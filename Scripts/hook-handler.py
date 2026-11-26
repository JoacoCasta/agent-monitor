#!/usr/bin/python3
import json
import os
import sys
import tempfile
import time

if os.name == "nt":
    import msvcrt
else:
    import fcntl

MONITOR_DIR = os.path.expanduser("~/.gemini/agent-monitor")
STATE_PATH = os.path.join(MONITOR_DIR, "state.json")
LOCK_PATH = os.path.join(MONITOR_DIR, "state.lock")
IDLE_PRUNE_SECONDS = 3600.0
VALID_PROVIDERS = ("antigravity", "codex", "claude", "copilot")


def acquire_lock(lock_file):
    if os.name == "nt":
        try:
            lock_file.seek(0)
            if os.path.getsize(LOCK_PATH) == 0:
                lock_file.write(" ")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        except Exception:
            pass
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)


def release_lock(lock_file):
    if os.name == "nt":
        try:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def atomic_replace(src, dst):
    last_err = None
    for _ in range(3):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_err = exc
            time.sleep(0.03)
    if last_err is not None:
        raise last_err


def is_root_path(path_str):
    s = path_str.strip()
    if s in ("/", "\\", ".", ""):
        return True
    if len(s) >= 2 and s[0].isalpha() and s[1] == ":":
        rest = s[2:].strip("/\\")
        if rest == "":
            return True
    return False


def basename_if_non_root(raw_path):
    if not isinstance(raw_path, str):
        return ""
    cleaned = raw_path.strip().rstrip("/\\")
    if not cleaned or is_root_path(cleaned):
        return ""
    norm = cleaned.replace("\\", "/")
    base = norm.rsplit("/", 1)[-1]
    return base


def parse_tool_args(raw_args):
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str) and raw_args.strip():
        try:
            parsed = json.loads(raw_args)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def extract_model_name(payload, existing):
    raw = payload.get("modelName")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    m = payload.get("model")
    if isinstance(m, str) and m.strip():
        return m.strip()
    if isinstance(m, dict):
        dn = m.get("display_name") or m.get("id")
        if isinstance(dn, str) and dn.strip():
            return dn.strip()
    return str(existing.get("modelName") or "")


def extract_workspace(payload, existing):
    ws_paths = payload.get("workspacePaths")
    if isinstance(ws_paths, list) and ws_paths:
        base = basename_if_non_root(str(ws_paths[0]))
        if base:
            return base
    ws = payload.get("workspace")
    if isinstance(ws, dict):
        cdir = ws.get("current_dir") or ws.get("project_dir")
        base = basename_if_non_root(cdir)
        if base:
            return base
    cwd = payload.get("cwd")
    base = basename_if_non_root(cwd)
    if base:
        return base
    prev = str(existing.get("workspace") or "")
    if prev in ("Sin workspace", "No workspace"):
        return ""
    return prev


def extract_session_id(payload):
    for key in ("conversationId", "session_id", "thread_id", "sessionId", "threadId"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "default"


def extract_tool_info(provider, payload):
    if provider == "antigravity":
        tc = payload.get("toolCall")
        if not isinstance(tc, dict):
            tc = {}
        name = str(tc.get("name") or "")
        args = parse_tool_args(tc.get("args"))
        return name, args
    name = str(payload.get("tool_name") or payload.get("toolName") or "")
    args = parse_tool_args(payload.get("tool_input") or payload.get("toolInput") or payload.get("toolArgs"))
    if not name and isinstance(payload.get("toolCall"), dict):
        tc = payload["toolCall"]
        name = str(tc.get("name") or "")
        args = parse_tool_args(tc.get("args"))
    return name, args


def update_state(provider, payload, event):
    if provider not in VALID_PROVIDERS:
        return

    raw_session_id = extract_session_id(payload)
    composite_id = "{}:{}".format(provider, raw_session_id)
    os.makedirs(MONITOR_DIR, exist_ok=True)
    now = time.time()

    with open(LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        acquire_lock(lock_file)
        try:
            state = {}
            if os.path.exists(STATE_PATH):
                try:
                    with open(STATE_PATH, "r", encoding="utf-8") as sf:
                        loaded = json.load(sf)
                        if isinstance(loaded, dict):
                            state = loaded
                except Exception:
                    state = {}

            sessions = state.get("sessions")
            if not isinstance(sessions, dict):
                sessions = {}

            last_turns = state.get("lastTurnCompletedByProvider")
            if not isinstance(last_turns, dict):
                last_turns = {}

            existing = sessions.get(composite_id)
            if not isinstance(existing, dict):
                existing = {}

            prev_status = existing.get("status", "idle")
            prev_changed_at = existing.get("statusChangedAt", now)
            model_name = extract_model_name(payload, existing)
            workspace = extract_workspace(payload, existing)

            status = prev_status
            detail = existing.get("detail", "Idle")
            detail_key = existing.get("detailKey", "idle")
            detail_arg = existing.get("detailArg", "")
            waiting_reason = existing.get("waitingReason", "")
            pending_feedback = bool(existing.get("pendingFeedback", False))
            remove_session = False

            if event == "SessionStart":
                status = "active"
                detail = "Starting session..."
                detail_key = "session_start"
                detail_arg = ""
                waiting_reason = ""
                pending_feedback = False
            elif event in ("PreInvocation", "UserPromptSubmit", "PreModelRequest"):
                status = "active"
                detail = "Thinking..."
                detail_key = "thinking"
                detail_arg = ""
                waiting_reason = ""
                pending_feedback = False
            elif event == "PermissionRequest":
                status = "waiting"
                waiting_reason = "permission"
                detail = "Waiting for permission"
                detail_key = "waiting_permission"
                detail_arg = ""
            elif event == "Elicitation":
                status = "waiting"
                waiting_reason = "elicitation"
                detail = "Waiting for confirmation"
                detail_key = "waiting_elicitation"
                detail_arg = ""
            elif event == "ElicitationResult":
                status = "active"
                waiting_reason = ""
                detail = "Processing response..."
                detail_key = "processing_answer"
                detail_arg = ""
            elif event == "Notification":
                notif_type = str(
                    payload.get("notification_type")
                    or payload.get("notificationType")
                    or ""
                )
                if notif_type == "permission_prompt":
                    status = "waiting"
                    waiting_reason = "permission"
                    detail = "Waiting for permission"
                    detail_key = "waiting_permission"
                    detail_arg = ""
                elif notif_type == "elicitation_dialog":
                    status = "waiting"
                    waiting_reason = "elicitation"
                    detail = "Waiting for confirmation"
                    detail_key = "waiting_elicitation"
                    detail_arg = ""
                else:
                    return
            elif event == "PreToolUse":
                name, args = extract_tool_info(provider, payload)
                if name in ("ask_question", "AskUserQuestion", "request_user_input", "ask_user"):
                    status = "waiting"
                    waiting_reason = "question"
                    detail = "Waiting for answer"
                    detail_key = "waiting_question"
                    detail_arg = ""
                elif name == "ask_permission":
                    status = "waiting"
                    waiting_reason = "permission"
                    detail = "Waiting for permission"
                    detail_key = "waiting_permission"
                    detail_arg = ""
                elif name == "notify_user" and args.get("BlockedOnUser") is True:
                    status = "waiting"
                    waiting_reason = "notify"
                    detail = "Waiting for approval"
                    detail_key = "waiting_approval"
                    detail_arg = ""
                elif (
                    provider == "antigravity"
                    and name in ("write_file", "edit_file")
                    and isinstance(args.get("ArtifactMetadata"), dict)
                    and args["ArtifactMetadata"].get("RequestFeedback") is True
                ):
                    pending_feedback = True
                    status = "active"
                    waiting_reason = ""
                    detail = "Preparing plan..."
                    detail_key = "preparing_plan"
                    detail_arg = ""
                else:
                    status = "active"
                    waiting_reason = ""
                    if name:
                        detail = "Running {}".format(name)
                        detail_key = "running_tool"
                        detail_arg = name
                    else:
                        detail = "Running tool"
                        detail_key = "running_tool_generic"
                        detail_arg = ""
            elif event in ("PostToolUse", "PostToolUseFailure"):
                name, _ = extract_tool_info(provider, payload)
                if (
                    name
                    in (
                        "ask_question",
                        "AskUserQuestion",
                        "request_user_input",
                        "ask_user",
                        "ask_permission",
                        "notify_user",
                    )
                    or prev_status == "waiting"
                ):
                    status = "active"
                    waiting_reason = ""
                    detail = "Processing response..."
                    detail_key = "processing_answer"
                    detail_arg = ""
                else:
                    status = "active"
                    waiting_reason = ""
                    detail = "Analyzing result..."
                    detail_key = "analyzing_result"
                    detail_arg = ""
            elif event in ("PostInvocation", "PostModelRequest"):
                pass
            elif event in ("Stop", "StopFailure", "Interrupt"):
                last_turns[provider] = now
                if provider == "antigravity":
                    fully_idle = payload.get("fullyIdle", True)
                    reason = str(payload.get("terminationReason") or "")
                    if fully_idle is False:
                        status = "active"
                        waiting_reason = ""
                        detail = "Background tasks running..."
                        detail_key = "background_tasks"
                        detail_arg = ""
                    elif pending_feedback and reason not in ("USER_CANCELED", "ERROR"):
                        status = "waiting"
                        waiting_reason = "plan_approval"
                        detail = "Waiting for plan approval"
                        detail_key = "waiting_plan_approval"
                        detail_arg = ""
                        pending_feedback = False
                    else:
                        status = "idle"
                        waiting_reason = ""
                        detail = "Idle"
                        detail_key = "idle"
                        detail_arg = ""
                        pending_feedback = False
                else:
                    status = "idle"
                    waiting_reason = ""
                    detail = "Idle"
                    detail_key = "idle"
                    detail_arg = ""
                    pending_feedback = False
            elif event == "SessionEnd":
                remove_session = True

            if remove_session:
                sessions.pop(composite_id, None)
            else:
                status_changed_at = (
                    now if (not existing or status != prev_status) else prev_changed_at
                )
                sessions[composite_id] = {
                    "id": composite_id,
                    "provider": provider,
                    "sessionId": raw_session_id,
                    "status": status,
                    "detail": detail,
                    "detailKey": detail_key,
                    "detailArg": detail_arg,
                    "waitingReason": waiting_reason,
                    "pendingFeedback": pending_feedback,
                    "modelName": model_name,
                    "workspace": workspace,
                    "updatedAt": now,
                    "statusChangedAt": status_changed_at,
                }

            pruned = {}
            for sid, sdata in sessions.items():
                if not isinstance(sdata, dict):
                    continue
                if sdata.get("status") == "idle":
                    updated = sdata.get("updatedAt", 0)
                    if isinstance(updated, (int, float)) and (now - updated) > IDLE_PRUNE_SECONDS:
                        continue
                pruned[sid] = sdata

            state["updatedAt"] = now
            state["lastTurnCompletedByProvider"] = last_turns
            state["sessions"] = pruned

            fd, tmp_path = tempfile.mkstemp(prefix=".state-", suffix=".json", dir=MONITOR_DIR)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tf:
                    json.dump(state, tf, ensure_ascii=False, indent=2)
                atomic_replace(tmp_path, STATE_PATH)
            except Exception:
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except Exception:
                    pass
        finally:
            release_lock(lock_file)


def emit_contract_response(provider, event):
    if provider == "antigravity":
        if event == "PreToolUse":
            sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")
        elif event == "Stop":
            sys.stdout.write(json.dumps({"decision": "stop"}) + "\n")
        else:
            sys.stdout.write("{}\n")
        sys.stdout.flush()


def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else ""
    fallback_event = sys.argv[2] if len(sys.argv) > 2 else ""
    event = fallback_event
    try:
        raw = sys.stdin.read()
        if raw and raw.strip():
            payload = json.loads(raw)
            if isinstance(payload, dict):
                event = str(
                    payload.get("hookEventName")
                    or payload.get("hook_event_name")
                    or fallback_event
                )
                if provider == "copilot":
                    copilot_event_map = {
                        "sessionStart": "SessionStart",
                        "userPromptSubmitted": "UserPromptSubmit",
                        "preToolUse": "PreToolUse",
                        "postToolUse": "PostToolUse",
                        "postToolUseFailure": "PostToolUseFailure",
                        "permissionRequest": "Notification",
                        "notification": "Notification",
                        "agentStop": "Stop",
                        "subagentStop": "Stop",
                        "sessionEnd": "SessionEnd",
                    }
                    raw_ev = event
                    event = copilot_event_map.get(event, event)
                    if raw_ev == "permissionRequest" and "notification_type" not in payload:
                        payload["notification_type"] = "permission_prompt"
                update_state(provider, payload, event)
    except Exception:
        pass
    finally:
        emit_contract_response(provider, event)


if __name__ == "__main__":
    main()
