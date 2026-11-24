#!/usr/bin/python3
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import threading
import time

# Ensure sibling imports work whether run directly, via symlink, or frozen
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from core import (
    PROVIDER_META,
    PROVIDERS,
    MonitorCore,
    focus_provider_app,
    is_launch_at_login_enabled,
    parse_iso_datetime,
    resolve_python_executable,
    resolve_scripts_dir,
    set_launch_at_login,
)
from i18n import SUPPORTED_LANGUAGES, L10n


PROVIDER_LOGO_PATHS = {
    "antigravity": (
        "M21.345 22.1123C22.6291 23.0755 24.5553 22.4335 22.7895 20.6677"
        "C17.4927 15.5313 18.6162 1.4061 12.0352 1.4061C5.4541 1.4061 6.5777 15.5313 1.2808 20.6677"
        "C-0.6454 22.5939 1.4413 23.0755 2.7254 22.1123C7.7013 18.7416 7.3803 12.8026 12.0352 12.8026"
        "C16.69 12.8026 16.369 18.7416 21.345 22.1123Z"
    ),
    "codex": (
        "M22.2819 9.8211C22.8248 8.1862 22.6369 6.3967 21.7662 4.9103"
        "C20.4571 2.6316 17.826 1.4595 15.2564 2.0103C13.8083 0.3995 11.6112 -0.3168 9.492 0.1311"
        "C7.3728 0.5789 5.6533 2.1229 4.9807 4.1818C3.2928 4.5279 1.836 5.5847 0.983 7.0818"
        "C-0.3404 9.3568 -0.0401 12.2267 1.7257 14.1784C1.1808 15.8125 1.367 17.6022 2.2367 19.0891"
        "C3.5475 21.3686 6.1803 22.5406 8.7513 21.9892C9.8948 23.277 11.5377 24.0097 13.2599 24"
        "C15.8937 24.0024 18.2271 22.3021 19.0317 19.7942C20.7194 19.4475 22.176 18.3908 23.0294 16.8941"
        "C24.3368 14.6231 24.0351 11.7688 22.2819 9.8212ZM13.2599 22.4292"
        "C12.2086 22.4309 11.1903 22.0624 10.3835 21.3884L10.5254 21.308L15.3037 18.5498"
        "C15.5456 18.4079 15.6949 18.149 15.6964 17.8685L15.6964 11.1316L17.7164 12.3002"
        "C17.7367 12.3105 17.7508 12.3298 17.7544 12.3522L17.7544 17.9348"
        "C17.7491 20.4148 15.7399 22.424 13.2599 22.4292ZM3.5992 18.3038"
        "C3.072 17.3934 2.8827 16.3263 3.0646 15.2901L3.2066 15.3753L7.9896 18.1335"
        "C8.2306 18.2749 8.5292 18.2749 8.7702 18.1335L14.613 14.765L14.613 17.0974"
        "C14.6119 17.1219 14.5997 17.1445 14.5798 17.1589L9.74 19.9502"
        "C7.5893 21.1891 4.8416 20.4525 3.5992 18.3038ZM2.3408 7.8956"
        "C2.8717 6.9794 3.7096 6.2805 4.7063 5.9228L4.7063 11.6C4.7026 11.8793 4.8513 12.1386 5.0942 12.2765"
        "L10.9086 15.6308L8.8885 16.7993C8.8663 16.8111 8.8397 16.8111 8.8175 16.7993L3.9872 14.0128"
        "C1.8408 12.7686 1.1047 10.023 2.3408 7.872ZM18.9371 11.7514L13.1038 8.364L15.1192 7.2"
        "C15.1414 7.1882 15.168 7.1882 15.1902 7.2L20.0205 9.9913"
        "C21.5281 10.8612 22.3979 12.5234 22.2531 14.258C22.1083 15.9926 20.975 17.4876 19.344 18.0955"
        "L19.344 12.4183C19.3355 12.1397 19.1808 11.8863 18.937 11.7513ZM20.9478 8.7283L20.8058 8.6431"
        "L16.0323 5.8613C15.7898 5.719 15.4894 5.719 15.2469 5.8613L9.409 9.2297L9.409 6.8974"
        "C9.4065 6.8732 9.4174 6.8496 9.4374 6.8359L14.2677 4.0493"
        "C15.779 3.1787 17.6573 3.2599 19.0877 4.2578C20.5182 5.2556 21.2431 6.9903 20.9479 8.7093Z"
        "M8.3065 12.863L6.2865 11.6992C6.266 11.6869 6.2521 11.6661 6.2485 11.6425L6.2485 6.0742"
        "C6.2508 4.3304 7.2605 2.7449 8.8397 2.0054C10.419 1.2659 12.2833 1.5056 13.6242 2.6205"
        "L13.4822 2.701L8.704 5.459C8.4621 5.6009 8.3128 5.8598 8.3113 6.1403ZM9.4041 10.4976"
        "L12.0061 8.9978L14.613 10.4976L14.613 13.497L12.0156 14.9967L9.4089 13.497Z"
    ),
    "claude": (
        "M4.7144 15.9555L9.4318 13.3084L9.5108 13.0777L9.4318 12.9502L9.2011 12.9502L8.4118 12.9016"
        "L5.7162 12.8287L3.3787 12.7316L1.1141 12.6102L0.5434 12.4887L0.0091 11.7845L0.0637 11.4323"
        "L0.5434 11.1105L1.2294 11.1713L2.7473 11.2745L5.024 11.4323L6.6754 11.5295L9.1222 11.7845"
        "L9.5108 11.7845L9.5654 11.6266L9.4318 11.5295L9.3286 11.4323L6.973 9.8356L4.423 8.1477"
        "L3.0874 7.1763L2.3649 6.6845L2.0006 6.2231L1.8428 5.2153L2.4985 4.4928L3.3788 4.5535"
        "L3.6034 4.6142L4.4959 5.3002L6.4023 6.7756L8.8916 8.6092L9.2559 8.9127L9.4016 8.8095"
        "L9.4198 8.7367L9.2558 8.4634L7.9019 6.0167L6.4569 3.5274L5.8134 2.4954L5.6434 1.876"
        "C5.5827 1.621 5.5402 1.4086 5.5402 1.1475L6.287 0.1335L6.6997 0L7.6954 0.1336L8.1144 0.4978"
        "L8.7336 1.9125L9.7354 4.1407L11.2897 7.1703L11.745 8.0688L11.9879 8.9006L12.0789 9.1556"
        "L12.2368 9.1556L12.2368 9.0099L12.3643 7.3039L12.6011 5.2092L12.8318 2.5135L12.9107 1.7546"
        "L13.2871 0.8439L14.0339 0.3521L14.6167 0.6314L15.0964 1.3174L15.0296 1.7607L14.7443 3.6124"
        "L14.1857 6.5145L13.8214 8.4574L14.0339 8.4574L14.2768 8.2145L15.2603 6.9092L16.9117 4.8449"
        "L17.6403 4.0253L18.4903 3.1207L19.0367 2.6896L20.0688 2.6896L20.8278 3.8189L20.4878 4.9846"
        "L19.4253 6.3324L18.5449 7.4738L17.2821 9.1738L16.4928 10.5338L16.5657 10.6431L16.7539 10.6248"
        "L19.6074 10.0178L21.1495 9.7384L22.9891 9.4227L23.8209 9.8113L23.9119 10.2059L23.5841 11.0134"
        "L21.6171 11.4991L19.3099 11.9605L15.8735 12.7741L15.831 12.8045L15.8796 12.8652L17.4278 13.0109"
        "L18.0896 13.0473L19.7106 13.0473L22.7281 13.272L23.5173 13.794L23.9909 14.4316L23.9119 14.9173"
        "L22.6977 15.5366L21.0584 15.148L17.2334 14.2373L15.9221 13.9094L15.7399 13.9094L15.7399 14.0187"
        "L16.8328 15.0873L18.8363 16.8965L21.3438 19.2279L21.4713 19.8047L21.1495 20.2601L20.8095 20.2115"
        "L18.6056 18.554L17.7556 17.8072L15.831 16.1862L15.7035 16.1862L15.7035 16.3562L16.1467 17.0058"
        "L18.4903 20.5272L18.6117 21.6079L18.4417 21.96L17.8346 22.1725L17.1667 22.0511L15.7946 20.1265"
        "L14.38 17.959L13.2386 16.0162L13.0989 16.0952L12.4249 23.3504L12.1093 23.7207L11.3807 24"
        "L10.7736 23.5386L10.4518 22.7918L10.7736 21.3165L11.1622 19.3919L11.4779 17.8619L11.7632 15.9615"
        "L11.9332 15.3301L11.9211 15.2876L11.7814 15.3058L10.3486 17.273L8.169 20.2176L6.4447 22.0632"
        "L6.0319 22.2272L5.3155 21.8568L5.3822 21.195L5.783 20.6061L8.169 17.5704L9.6079 15.6884"
        "L10.5369 14.6016L10.5307 14.4437L10.4761 14.4437L4.1376 18.5601L3.0083 18.7058L2.5226 18.2504"
        "L2.5834 17.5037L2.8141 17.2608L4.7205 15.9494Z"
    ),
}

_SVG_TOKEN_RE = re.compile(r"[MLCZ]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


def parse_svg_path_commands(d_str):
    """Parse an SVG path string containing absolute M/L/C/Z commands."""
    tokens = _SVG_TOKEN_RE.findall(d_str or "")
    commands = []
    idx = 0
    current_cmd = None
    while idx < len(tokens):
        tok = tokens[idx]
        if tok in ("M", "L", "C", "Z"):
            current_cmd = tok
            idx += 1
            if current_cmd == "Z":
                commands.append(("Z", ()))
                continue
        if current_cmd == "M":
            x, y = float(tokens[idx]), float(tokens[idx + 1])
            commands.append(("M", (x, y)))
            idx += 2
            current_cmd = "L"
        elif current_cmd == "L":
            x, y = float(tokens[idx]), float(tokens[idx + 1])
            commands.append(("L", (x, y)))
            idx += 2
        elif current_cmd == "C":
            vals = tuple(float(tokens[idx + j]) for j in range(6))
            commands.append(("C", vals))
            idx += 6
        else:
            raise ValueError("Unsupported SVG path command: {!r}".format(tok))
    return commands


def no_window_kwargs():
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
    return {}


def run_script_capture(script_name, args):
    scripts_dir = resolve_scripts_dir()
    script_path = os.path.join(scripts_dir, script_name)
    py_exe = resolve_python_executable()
    env = os.environ.copy()
    env.setdefault("HOME", os.path.expanduser("~"))
    env["AGENT_MONITOR_PYTHON"] = py_exe
    proc = subprocess.run(
        [py_exe, script_path] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=25,
        **no_window_kwargs()
    )
    if proc.returncode != 0:
        raw_err = (proc.stderr or "").strip()
        msg = raw_err or "Script failed ({})".format(proc.returncode)
        try:
            obj = json.loads(raw_err)
            if isinstance(obj, dict) and obj.get("error"):
                msg = str(obj["error"])
        except Exception:
            pass
        raise RuntimeError(msg)
    return json.loads((proc.stdout or "").strip())


def main_gui():
    from PySide6.QtCore import (
        QFileSystemWatcher,
        QObject,
        QPoint,
        QRect,
        Qt,
        QTimer,
        Signal,
    )
    from PySide6.QtGui import (
        QAction,
        QColor,
        QCursor,
        QGuiApplication,
        QIcon,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMenu,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )

    STATUS_COLORS = {
        "waiting": QColor(255, 204, 0),
        "active": QColor(255, 59, 48),
        "idle": QColor(52, 199, 89),
    }

    def bar_hex_color(pct):
        if pct < 20:
            return "#FF3B30"
        if pct <= 50:
            return "#FF9F0A"
        return "#34C759"

    def status_hex_color(status):
        if status == "waiting":
            return "#FFCC00"
        if status == "active":
            return "#FF3B30"
        return "#34C759"

    def build_provider_path(provider):
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        d_str = PROVIDER_LOGO_PATHS.get(provider, "")
        for cmd, args in parse_svg_path_commands(d_str):
            if cmd == "M":
                path.moveTo(args[0], args[1])
            elif cmd == "L":
                path.lineTo(args[0], args[1])
            elif cmd == "C":
                path.cubicTo(*args)
            elif cmd == "Z":
                path.closeSubpath()
        return path

    def make_provider_logo_pixmap(provider, size, color_hex):
        dpr = 2.0
        px_size = int(round(size * dpr))
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(Qt.transparent)
        pixmap.setDevicePixelRatio(dpr)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        scale = size / 24.0
        painter.scale(scale, scale)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color_hex))
        painter.drawPath(build_provider_path(provider))
        painter.end()
        return pixmap

    class WorkerBridge(QObject):
        quota_fetched = Signal(str, object)
        quota_failed = Signal(str, str)
        hooks_updated = Signal(object)
        hooks_failed = Signal(str)

    class MonitorApp(QObject):
        def __init__(self, qt_app):
            super().__init__()
            self.qt_app = qt_app
            self.core = MonitorCore()
            self.bridge = WorkerBridge()
            self.bridge.quota_fetched.connect(self._on_quota_fetched)
            self.bridge.quota_failed.connect(self._on_quota_failed)
            self.bridge.hooks_updated.connect(self._on_hooks_updated)
            self.bridge.hooks_failed.connect(self._on_hooks_failed)

            self.fetching_providers = set()
            self.is_syncing_hooks = False
            self.showing_settings = False
            self.onboarding_selection = set(self.core.enabled_providers)
            self.has_edited_onboarding = False
            self.last_refresh_attempt = {}
            self.debounce_timers = {}
            self.last_notified_provider = None

            self.tray = QSystemTrayIcon(self)
            self.tray.activated.connect(self._on_tray_activated)
            self.tray.messageClicked.connect(self._on_notification_clicked)

            self.popup = QFrame(None, Qt.Popup | Qt.FramelessWindowHint)
            self.popup.setObjectName("MonitorPopup")
            self.popup.setFixedWidth(382)
            self._apply_theme_styles()

            self.root_layout = QVBoxLayout(self.popup)
            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.root_layout.setSpacing(0)

            self.watcher = QFileSystemWatcher([self.core.monitor_dir], self)
            self.watcher.directoryChanged.connect(self._on_dir_changed)

            self.tick_timer = QTimer(self)
            self.tick_timer.setInterval(1000)
            self.tick_timer.timeout.connect(self._on_tick)
            self.tick_timer.start()

            self._update_tray_visuals()
            self._rebuild_context_menu()
            self.tray.show()

            self._refresh_hook_statuses()
            self.refresh_all_enabled_quotas(force=True)

            if not self.core.has_completed_onboarding:
                QTimer.singleShot(800, self._open_popup_initial)

        @property
        def t(self):
            return L10n(self.core.app_language)

        def _is_dark_theme(self):
            pal = self.qt_app.palette()
            return pal.window().color().lightness() < 128

        def _apply_theme_styles(self):
            dark = self._is_dark_theme()
            if dark:
                bg = "#1E1E20"
                border = "#3A3A3F"
                card_bg = "#28282C"
                subcard_bg = "#222226"
                text_primary = "#F2F2F7"
                text_secondary = "#A1A1AA"
                btn_bg = "#323237"
                btn_hover = "#3E3E45"
                accent = "#0A84FF"
            else:
                bg = "#F7F7F9"
                border = "#D1D1D6"
                card_bg = "#FFFFFF"
                subcard_bg = "#F2F2F7"
                text_primary = "#1C1C1E"
                text_secondary = "#6E6E73"
                btn_bg = "#E5E5EA"
                btn_hover = "#D8D8DF"
                accent = "#007AFF"

            self._theme = {
                "bg": bg,
                "border": border,
                "card_bg": card_bg,
                "subcard_bg": subcard_bg,
                "text_primary": text_primary,
                "text_secondary": text_secondary,
                "btn_bg": btn_bg,
                "btn_hover": btn_hover,
                "accent": accent,
            }

            self.popup.setStyleSheet(
                """
                #MonitorPopup {{
                    background-color: {bg};
                    border: 1px solid {border};
                    border-radius: 12px;
                }}
                QLabel {{
                    color: {text_primary};
                    background: transparent;
                }}
                QPushButton {{
                    background-color: {btn_bg};
                    color: {text_primary};
                    border: none;
                    border-radius: 6px;
                    padding: 4px 9px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {btn_hover};
                }}
                QPushButton#PrimaryBtn {{
                    background-color: {accent};
                    color: #FFFFFF;
                    font-weight: 600;
                    padding: 5px 12px;
                }}
                QPushButton#PlainBtn {{
                    background: transparent;
                    color: {text_secondary};
                    padding: 2px 6px;
                }}
                QPushButton#PlainBtn:hover {{
                    color: {text_primary};
                    background: transparent;
                }}
                QComboBox {{
                    background-color: {btn_bg};
                    color: {text_primary};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 3px 8px;
                    font-size: 11px;
                }}
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
                """.format(**self._theme)
            )

        def _make_tray_icon(self):
            enabled = self.core.enabled_providers
            size = 64
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)

            count = len(enabled)
            if count == 1:
                centers = [(32, 32)]
                radius = 20
            elif count == 2:
                centers = [(19, 32), (45, 32)]
                radius = 11
            else:
                centers = [(32, 17), (17, 44), (47, 44)]
                radius = 10

            any_low = False
            for idx, prov in enumerate(enabled[:3]):
                cx, cy = centers[idx]
                status = self.core.status_by_provider.get(prov, "idle")
                color = STATUS_COLORS.get(status, STATUS_COLORS["idle"])
                pct = self.core.menu_bar_percent(prov)
                if pct is not None and pct < 20:
                    any_low = True

                painter.setPen(QPen(QColor(0, 0, 0, 140), 3))
                painter.setBrush(color)
                painter.drawEllipse(QPoint(cx, cy), radius, radius)

            if any_low:
                painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
                painter.setBrush(QColor(255, 59, 48))
                painter.drawEllipse(QPoint(54, 10), 7, 7)

            painter.end()
            return QIcon(pixmap)

        def _update_tray_visuals(self):
            self.tray.setIcon(self._make_tray_icon())
            t = self.t
            lines = []
            for prov in self.core.enabled_providers:
                meta = PROVIDER_META[prov]
                st = self.core.status_by_provider.get(prov, "idle")
                pct = self.core.menu_bar_percent(prov)
                pct_str = "{}%".format(pct) if pct is not None else "--"
                lines.append("{}: {} ({})".format(meta["display_name"], t.status_title(st), pct_str))
            self.tray.setToolTip("\n".join(lines))

        def _rebuild_context_menu(self):
            t = self.t
            menu = QMenu()

            act_refresh = QAction(t.menu_refresh_all, menu)
            act_refresh.triggered.connect(lambda: self.refresh_all_enabled_quotas(force=True))
            menu.addAction(act_refresh)

            for prov in self.core.enabled_providers:
                name = PROVIDER_META[prov]["display_name"]
                act = QAction(t.menu_open_provider(name), menu)
                act.triggered.connect(lambda _=False, p=prov: focus_provider_app(p))
                menu.addAction(act)

            menu.addSeparator()

            act_settings = QAction(t.menu_settings, menu)
            act_settings.triggered.connect(self._open_settings_from_menu)
            menu.addAction(act_settings)

            act_clear = QAction(t.clear_states, menu)
            act_clear.triggered.connect(self._clear_all_sessions)
            menu.addAction(act_clear)

            menu.addSeparator()

            act_quit = QAction(t.quit, menu)
            act_quit.triggered.connect(self.qt_app.quit)
            menu.addAction(act_quit)

            self.context_menu = menu
            self.tray.setContextMenu(menu)

        def _open_popup_initial(self):
            if not self.core.has_completed_onboarding and not self.popup.isVisible():
                self._show_popup()

        def _on_tray_activated(self, reason):
            if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
                if self.popup.isVisible():
                    self.popup.hide()
                else:
                    self._show_popup()

        def _show_popup(self):
            self._apply_theme_styles()
            self._render_popup_contents()
            self.popup.adjustSize()

            geom = self.tray.geometry()
            anchor = geom.center() if geom.isValid() and not geom.isNull() else QCursor.pos()
            screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
            avail = screen.availableGeometry() if screen else QRect(0, 0, 1280, 800)

            w = self.popup.width()
            h = self.popup.height()
            x = max(avail.left() + 8, min(anchor.x() - w // 2, avail.right() - w - 8))
            if anchor.y() > avail.center().y():
                y = max(avail.top() + 8, anchor.y() - h - 14)
            else:
                y = min(avail.bottom() - h - 8, anchor.y() + 14)

            self.popup.move(x, y)
            self.popup.show()
            self.popup.raise_()
            self.popup.activateWindow()

        def _open_settings_from_menu(self):
            if self.core.has_completed_onboarding:
                self._refresh_hook_statuses()
                self.showing_settings = True
            self._show_popup()

        # --- Background Workers ---

        def _refresh_hook_statuses(self):
            def worker():
                try:
                    res = run_script_capture("configure-hooks.py", ["status"])
                    self.bridge.hooks_updated.emit(res)
                except Exception as exc:
                    self.bridge.hooks_failed.emit(str(exc))

            threading.Thread(target=worker, daemon=True).start()

        def _sync_hooks(self, args):
            self.is_syncing_hooks = True
            if self.popup.isVisible():
                self._render_popup_contents()

            def worker():
                try:
                    res = run_script_capture("configure-hooks.py", args)
                    self.bridge.hooks_updated.emit(res)
                except Exception as exc:
                    self.bridge.hooks_failed.emit(str(exc))

            threading.Thread(target=worker, daemon=True).start()

        def _on_hooks_updated(self, result):
            self.is_syncing_hooks = False
            if isinstance(result, dict):
                self.core.hook_statuses = result
                if not self.core.has_completed_onboarding and not self.has_edited_onboarding:
                    detected = {
                        p
                        for p in PROVIDERS
                        if (result.get(p, {}).get("binaryFound") or result.get(p, {}).get("appInstalled"))
                    }
                    if detected:
                        self.onboarding_selection = detected
            if self.popup.isVisible():
                self._render_popup_contents()

        def _on_hooks_failed(self, err):
            self.is_syncing_hooks = False
            if self.popup.isVisible():
                self._render_popup_contents()

        def refresh_all_enabled_quotas(self, force=False):
            for prov in self.core.enabled_providers:
                if prov == "claude":
                    if self.core.load_claude_quota():
                        self._check_low_quota_alerts(self.core.quotas_by_provider["claude"])
                else:
                    self.refresh_quota(prov, force=force)
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        def refresh_quota(self, provider, force=False):
            if provider not in self.core.enabled_providers:
                return
            if not PROVIDER_META[provider]["supports_poll"]:
                if provider == "claude":
                    self.core.load_claude_quota()
                return
            if provider in self.fetching_providers:
                return
            now_ts = time.time()
            last_ts = self.last_refresh_attempt.get(provider, 0.0)
            if not force and (now_ts - last_ts) < 5.0:
                return
            self.last_refresh_attempt[provider] = now_ts
            self.fetching_providers.add(provider)
            if self.popup.isVisible():
                self._render_popup_contents()

            def worker():
                try:
                    snap = run_script_capture("fetch-quota.py", ["--provider", provider])
                    self.bridge.quota_fetched.emit(provider, snap)
                except Exception as exc:
                    self.bridge.quota_failed.emit(provider, str(exc))

            threading.Thread(target=worker, daemon=True).start()

        def _on_quota_fetched(self, provider, snapshot):
            self.fetching_providers.discard(provider)
            if isinstance(snapshot, dict):
                self.core.quotas_by_provider[provider] = snapshot
                self.core.last_updated_by_provider[provider] = time.time()
                self.core.quota_errors.pop(provider, None)
                self._check_low_quota_alerts(snapshot)
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        def _on_quota_failed(self, provider, err_msg):
            self.fetching_providers.discard(provider)
            self.core.quota_errors[provider] = err_msg
            if self.popup.isVisible():
                self._render_popup_contents()

        # --- Watchers, Timers & Notifications ---

        def _on_dir_changed(self, _path):
            now_ts = time.time()
            completed = self.core.load_state(now_epoch=now_ts)
            if self.core.load_claude_quota():
                self._check_low_quota_alerts(self.core.quotas_by_provider["claude"])
            self._check_waiting_alerts(now_ts)
            for prov in completed:
                self._schedule_debounced_refresh(prov)
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        def _schedule_debounced_refresh(self, provider):
            old = self.debounce_timers.get(provider)
            if old is not None:
                old.stop()
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(1500)
            timer.timeout.connect(lambda p=provider: self.refresh_quota(p, force=False))
            self.debounce_timers[provider] = timer
            timer.start()

        def _on_tick(self):
            now_ts = time.time()
            self.core.recompute_derived(now_ts)
            for prov in self.core.enabled_providers:
                if PROVIDER_META[prov]["supports_poll"]:
                    last_ts = self.last_refresh_attempt.get(prov, 0.0)
                    if (now_ts - last_ts) >= 300.0:
                        self.refresh_quota(prov, force=True)
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        def _check_waiting_alerts(self, now_ts):
            t = self.t
            for prov, s in self.core.collect_waiting_notifications(now_ts):
                ws = s.get("workspace") or t.no_workspace
                detail = t.session_detail(s.get("detailKey"), s.get("detailArg"), s.get("detail", ""))
                self.last_notified_provider = prov
                self.tray.showMessage(
                    t.waiting_notification_title(PROVIDER_META[prov]["display_name"]),
                    "{} · {}".format(ws, detail),
                    QSystemTrayIcon.Information,
                    6000,
                )

        def _check_low_quota_alerts(self, snapshot):
            t = self.t
            fetched_dt = parse_iso_datetime(snapshot.get("fetchedAt"))
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            for prov, bucket, pct in self.core.collect_low_quota_notifications(snapshot):
                reset_dt = parse_iso_datetime(bucket.get("resetTime"))
                countdown = t.format_countdown(
                    reset_dt, int(bucket.get("resetInSeconds") or 0), fetched_dt, now_dt
                )
                group_title = t.group_display_name(bucket.get("groupKey"), bucket.get("group", ""))
                label_title = t.bucket_label(bucket)
                disp = PROVIDER_META[prov]["display_name"]
                prefix = (
                    "{} · {}".format(group_title, label_title)
                    if group_title not in (disp, "Codex")
                    else label_title
                )
                self.last_notified_provider = prov
                self.tray.showMessage(
                    t.low_quota_notification_title(disp),
                    t.low_quota_notification_body(prefix, pct, countdown),
                    QSystemTrayIcon.Warning,
                    6000,
                )

        def _on_notification_clicked(self):
            prov = self.last_notified_provider or (
                self.core.enabled_providers[0] if self.core.enabled_providers else "antigravity"
            )
            focus_provider_app(prov)

        # --- Actions ---

        def _toggle_onboarding_provider(self, prov, checked=None):
            self.has_edited_onboarding = True
            should_select = (not (prov in self.onboarding_selection)) if checked is None else bool(checked)
            if should_select:
                self.onboarding_selection.add(prov)
            elif len(self.onboarding_selection) > 1:
                self.onboarding_selection.discard(prov)
            self._render_popup_contents()

        def _complete_onboarding(self):
            self.core.complete_onboarding(list(self.onboarding_selection))
            self._sync_hooks(["sync", ",".join(self.core.enabled_providers)])
            self._rebuild_context_menu()
            self._update_tray_visuals()
            self.refresh_all_enabled_quotas(force=True)
            self._render_popup_contents()

        def _set_provider_enabled(self, prov, enabled):
            if not self.core.set_provider_enabled(prov, enabled):
                self._render_popup_contents()
                return
            action = "enable" if enabled else "disable"
            self._sync_hooks([action, prov])
            self._rebuild_context_menu()
            self._update_tray_visuals()
            if enabled:
                if prov == "claude":
                    self.core.load_claude_quota()
                else:
                    self.refresh_quota(prov, force=True)
            self._render_popup_contents()

        def _set_language(self, lang_code):
            self.core.set_language(lang_code)
            self._rebuild_context_menu()
            self._update_tray_visuals()
            self._render_popup_contents()

        def _set_launch_at_login(self, enabled):
            set_launch_at_login(bool(enabled))
            self._render_popup_contents()

        def _clear_all_sessions(self):
            self.core.clear_all_sessions()
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        def _dismiss_session(self, sid):
            self.core.dismiss_session(sid)
            self._update_tray_visuals()
            if self.popup.isVisible():
                self._render_popup_contents()

        # --- Rendering ---

        def _clear_layout(self, layout):
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
                sub = item.layout()
                if sub is not None:
                    self._clear_layout(sub)

        def _render_popup_contents(self):
            self._clear_layout(self.root_layout)
            if not self.core.has_completed_onboarding:
                self.root_layout.addWidget(self._build_onboarding_widget())
            elif self.showing_settings:
                self.root_layout.addWidget(self._build_settings_widget())
            else:
                self.root_layout.addWidget(self._build_dashboard_widget())
            self.popup.adjustSize()

        def _make_card_frame(self, bg_color, border_color=None):
            frame = QFrame()
            b = border_color or self._theme["border"]
            frame.setStyleSheet(
                "QFrame {{ background-color: {}; border: 1px solid {}; border-radius: 10px; }}".format(
                    bg_color, b
                )
            )
            return frame

        def _build_onboarding_widget(self):
            t = self.t
            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(14, 14, 14, 14)
            lay.setSpacing(10)

            top_row = QHBoxLayout()
            title = QLabel(t.choose_agents_title)
            title.setStyleSheet("font-size: 14px; font-weight: 700; border: none;")
            top_row.addWidget(title)
            top_row.addStretch()

            lang_combo = QComboBox()
            for lc in SUPPORTED_LANGUAGES:
                lang_combo.addItem(t.picker_label(lc), lc)
            lang_combo.setCurrentIndex(max(0, SUPPORTED_LANGUAGES.index(self.core.app_language)))
            lang_combo.currentIndexChanged.connect(
                lambda idx: self._set_language(lang_combo.itemData(idx))
            )
            top_row.addWidget(lang_combo)
            lay.addLayout(top_row)

            sub = QLabel(t.choose_agents_subtitle)
            sub.setWordWrap(True)
            sub.setStyleSheet("font-size: 11px; color: {}; border: none;".format(self._theme["text_secondary"]))
            lay.addWidget(sub)

            for prov in PROVIDERS:
                meta = PROVIDER_META[prov]
                selected = prov in self.onboarding_selection
                st = self.core.hook_statuses.get(prov, {})
                detected = bool(st.get("binaryFound") or st.get("appInstalled"))
                border = self._theme["accent"] if selected else self._theme["border"]
                card = self._make_card_frame(self._theme["card_bg"], border)
                clay = QHBoxLayout(card)
                clay.setContentsMargins(10, 8, 10, 8)
                clay.setSpacing(8)

                cb = QCheckBox()
                cb.setChecked(selected)
                cb.toggled.connect(lambda checked, p=prov: self._toggle_onboarding_provider(p, checked))
                clay.addWidget(cb)

                info_col = QVBoxLayout()
                info_col.setSpacing(2)
                name_row = QHBoxLayout()
                name_row.setSpacing(6)
                nl = QLabel(meta["display_name"])
                nl.setStyleSheet("font-size: 12px; font-weight: 600; border: none;")
                name_row.addWidget(nl)
                if detected:
                    badge = QLabel(t.detected_badge)
                    badge.setStyleSheet(
                        "font-size: 9px; font-weight: 700; color: #34C759; "
                        "background-color: rgba(52,199,89,0.18); border-radius: 6px; padding: 1px 6px; border: none;"
                    )
                    name_row.addWidget(badge)
                name_row.addStretch()
                info_col.addLayout(name_row)

                sl = QLabel(t.onboarding_subtitle(prov))
                sl.setWordWrap(True)
                sl.setStyleSheet("font-size: 10px; color: {}; border: none;".format(self._theme["text_secondary"]))
                info_col.addWidget(sl)
                clay.addLayout(info_col, 1)

                logo_lbl = QLabel()
                logo_lbl.setPixmap(make_provider_logo_pixmap(prov, 16, self._theme["text_primary"]))
                logo_lbl.setStyleSheet(
                    "background-color: {}; border-radius: 6px; padding: 5px; border: none;".format(
                        self._theme["btn_bg"]
                    )
                )
                clay.addWidget(logo_lbl)
                lay.addWidget(card)

            hints = QLabel("{}\n{}".format(t.codex_trust_hint, t.claude_statusline_hint))
            hints.setWordWrap(True)
            hints.setStyleSheet("font-size: 10px; color: {}; border: none;".format(self._theme["text_secondary"]))
            lay.addWidget(hints)

            btn_row = QHBoxLayout()
            q_btn = QPushButton(t.quit)
            q_btn.setObjectName("PlainBtn")
            q_btn.clicked.connect(self.qt_app.quit)
            btn_row.addWidget(q_btn)
            btn_row.addStretch()

            start_btn = QPushButton(t.get_started)
            start_btn.setObjectName("PrimaryBtn")
            start_btn.clicked.connect(self._complete_onboarding)
            btn_row.addWidget(start_btn)
            lay.addLayout(btn_row)

            return container

        def _build_settings_widget(self):
            t = self.t
            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(10)

            top_row = QHBoxLayout()
            back_btn = QPushButton("‹ " + t.back)
            back_btn.setObjectName("PlainBtn")
            back_btn.clicked.connect(lambda: self._exit_settings())
            top_row.addWidget(back_btn)
            top_row.addStretch()

            hdr = QLabel(t.settings_title)
            hdr.setStyleSheet("font-size: 13px; font-weight: 700; border: none;")
            top_row.addWidget(hdr)
            top_row.addStretch()

            done_btn = QPushButton(t.done)
            done_btn.setObjectName("PrimaryBtn")
            done_btn.clicked.connect(lambda: self._exit_settings())
            top_row.addWidget(done_btn)
            lay.addLayout(top_row)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setMaximumHeight(440)

            body = QWidget()
            body.setStyleSheet("background: transparent;")
            blay = QVBoxLayout(body)
            blay.setContentsMargins(0, 0, 0, 0)
            blay.setSpacing(8)

            # Language card
            lang_card = self._make_card_frame(self._theme["card_bg"])
            llay = QHBoxLayout(lang_card)
            llay.setContentsMargins(10, 7, 10, 7)
            llbl = QLabel("🌐 " + t.language_label)
            llbl.setStyleSheet("font-size: 11.5px; font-weight: 600; border: none;")
            llay.addWidget(llbl)
            llay.addStretch()

            lang_combo = QComboBox()
            for lc in SUPPORTED_LANGUAGES:
                lang_combo.addItem(t.picker_label(lc), lc)
            lang_combo.setCurrentIndex(max(0, SUPPORTED_LANGUAGES.index(self.core.app_language)))
            lang_combo.currentIndexChanged.connect(
                lambda idx: self._set_language(lang_combo.itemData(idx))
            )
            llay.addWidget(lang_combo)
            blay.addWidget(lang_card)

            # Start at login card
            auto_card = self._make_card_frame(self._theme["card_bg"])
            alay = QHBoxLayout(auto_card)
            alay.setContentsMargins(10, 7, 10, 7)
            albl = QLabel("⏻ " + t.launch_at_login)
            albl.setStyleSheet("font-size: 11.5px; font-weight: 600; border: none;")
            alay.addWidget(albl)
            alay.addStretch()

            auto_cb = QCheckBox()
            auto_cb.setChecked(is_launch_at_login_enabled())
            auto_cb.toggled.connect(lambda checked: self._set_launch_at_login(checked))
            alay.addWidget(auto_cb)
            blay.addWidget(auto_card)

            ahdr = QLabel(t.active_agents_header)
            ahdr.setStyleSheet("font-size: 11px; font-weight: 600; color: {}; border: none;".format(self._theme["text_secondary"]))
            blay.addWidget(ahdr)

            for prov in PROVIDERS:
                meta = PROVIDER_META[prov]
                enabled = prov in self.core.enabled_providers
                only_one = enabled and len(self.core.enabled_providers) <= 1
                info = self.core.hook_statuses.get(prov)

                card = self._make_card_frame(self._theme["card_bg"])
                clay = QHBoxLayout(card)
                clay.setContentsMargins(10, 8, 10, 8)
                clay.setSpacing(8)

                col = QVBoxLayout()
                col.setSpacing(2)
                row1 = QHBoxLayout()
                row1.setSpacing(6)
                logo_lbl = QLabel()
                logo_lbl.setPixmap(make_provider_logo_pixmap(prov, 13, self._theme["text_primary"]))
                logo_lbl.setStyleSheet("border: none;")
                row1.addWidget(logo_lbl)
                nl = QLabel(meta["display_name"])
                nl.setStyleSheet("font-size: 12px; font-weight: 600; border: none;")
                row1.addWidget(nl)
                row1.addStretch()
                col.addLayout(row1)

                if info is not None:
                    active = bool(info.get("hooksInstalled"))
                    dot_color = "#34C759" if active else self._theme["text_secondary"]
                    htext = t.hooks_active if active else t.hooks_disabled
                    if not info.get("binaryFound") and not info.get("appInstalled"):
                        htext += " " + t.not_detected
                    hl = QLabel("● " + htext)
                    hl.setStyleSheet("font-size: 10px; color: {}; border: none;".format(dot_color))
                else:
                    hl = QLabel(t.checking_status)
                    hl.setStyleSheet("font-size: 10px; color: {}; border: none;".format(self._theme["text_secondary"]))
                col.addWidget(hl)
                clay.addLayout(col, 1)

                cb = QCheckBox()
                cb.setChecked(enabled)
                cb.setEnabled(not only_one)
                cb.toggled.connect(lambda checked, p=prov: self._set_provider_enabled(p, checked))
                clay.addWidget(cb)
                blay.addWidget(card)

            note = QLabel(t.hooks_auto_note)
            note.setWordWrap(True)
            note.setStyleSheet("font-size: 10px; color: {}; border: none;".format(self._theme["text_secondary"]))
            blay.addWidget(note)
            blay.addStretch()

            scroll.setWidget(body)
            lay.addWidget(scroll)

            foot = QHBoxLayout()
            resync_btn = QPushButton(t.resync_hooks)
            resync_btn.setEnabled(not self.is_syncing_hooks)
            resync_btn.clicked.connect(
                lambda: self._sync_hooks(["sync", ",".join(self.core.enabled_providers)])
            )
            foot.addWidget(resync_btn)
            foot.addStretch()

            clear_btn = QPushButton(t.clear_states)
            clear_btn.setObjectName("PlainBtn")
            clear_btn.clicked.connect(self._clear_all_sessions)
            foot.addWidget(clear_btn)
            lay.addLayout(foot)

            return container

        def _exit_settings(self):
            self.showing_settings = False
            self._render_popup_contents()

        def _build_dashboard_widget(self):
            t = self.t
            now_ts = time.time()
            now_dt = datetime.datetime.now(datetime.timezone.utc)

            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(10)

            # Header
            hdr_row = QHBoxLayout()
            title = QLabel(t.app_title)
            title.setStyleSheet("font-size: 13.5px; font-weight: 700; border: none;")
            hdr_row.addWidget(title)
            hdr_row.addStretch()

            ref_btn = QPushButton("↻")
            ref_btn.setToolTip(t.refresh_all_help)
            ref_btn.clicked.connect(lambda: self.refresh_all_enabled_quotas(force=True))
            hdr_row.addWidget(ref_btn)

            gear_btn = QPushButton("⚙")
            gear_btn.setToolTip(t.settings_help)
            gear_btn.clicked.connect(self._open_settings_inline)
            hdr_row.addWidget(gear_btn)
            lay.addLayout(hdr_row)

            # Scrollable Cards
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setMaximumHeight(540)

            cards_holder = QWidget()
            cards_holder.setStyleSheet("background: transparent;")
            cards_lay = QVBoxLayout(cards_holder)
            cards_lay.setContentsMargins(0, 0, 0, 0)
            cards_lay.setSpacing(10)

            for prov in self.core.enabled_providers:
                cards_lay.addWidget(self._build_provider_card(prov, now_ts, now_dt))

            cards_lay.addStretch()
            scroll.setWidget(cards_holder)
            lay.addWidget(scroll)

            # Footer
            foot = QHBoxLayout()
            if self.fetching_providers:
                status_txt = t.updating_quotas
            else:
                updated_epochs = [
                    self.core.last_updated_by_provider[p]
                    for p in self.core.enabled_providers
                    if p in self.core.last_updated_by_provider
                ]
                if updated_epochs:
                    status_txt = t.updated_text(t.format_elapsed(max(updated_epochs), now_ts))
                else:
                    status_txt = t.ready
            flbl = QLabel(status_txt)
            flbl.setStyleSheet("font-size: 10.5px; color: {}; border: none;".format(self._theme["text_secondary"]))
            foot.addWidget(flbl)
            foot.addStretch()

            s_btn = QPushButton(t.settings_title)
            s_btn.setObjectName("PlainBtn")
            s_btn.clicked.connect(self._open_settings_inline)
            foot.addWidget(s_btn)

            q_btn = QPushButton(t.quit)
            q_btn.setObjectName("PlainBtn")
            q_btn.clicked.connect(self.qt_app.quit)
            foot.addWidget(q_btn)
            lay.addLayout(foot)

            return container

        def _open_settings_inline(self):
            self._refresh_hook_statuses()
            self.showing_settings = True
            self._render_popup_contents()

        def _build_provider_card(self, prov, now_ts, now_dt):
            t = self.t
            meta = PROVIDER_META[prov]
            status = self.core.status_by_provider.get(prov, "idle")
            sessions = self.core.non_idle_sessions(prov, now_ts)
            snapshot = self.core.quotas_by_provider.get(prov)
            is_fetching = prov in self.fetching_providers
            err_msg = self.core.quota_errors.get(prov)

            border = "#FFCC00" if status == "waiting" else self._theme["border"]
            card = self._make_card_frame(self._theme["card_bg"], border)
            clay = QVBoxLayout(card)
            clay.setContentsMargins(11, 10, 11, 10)
            clay.setSpacing(8)

            # Card Header
            hrow = QHBoxLayout()
            hrow.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet("font-size: 13px; color: {}; border: none;".format(status_hex_color(status)))
            hrow.addWidget(dot)

            title_col = QVBoxLayout()
            title_col.setSpacing(1)
            nrow = QHBoxLayout()
            nrow.setSpacing(6)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(make_provider_logo_pixmap(prov, 13, self._theme["text_primary"]))
            logo_lbl.setStyleSheet("border: none;")
            nrow.addWidget(logo_lbl)
            pname = QLabel(meta["display_name"])
            pname.setStyleSheet("font-size: 12px; font-weight: 700; border: none;")
            nrow.addWidget(pname)

            if snapshot and snapshot.get("planType"):
                pl = QLabel(str(snapshot["planType"]))
                pl.setStyleSheet(
                    "font-size: 9px; font-weight: 600; color: {}; background-color: {}; border-radius: 5px; padding: 1px 5px; border: none;".format(
                        self._theme["text_secondary"], self._theme["btn_bg"]
                    )
                )
                nrow.addWidget(pl)
            nrow.addStretch()
            title_col.addLayout(nrow)

            st_lbl = QLabel(t.status_title(status))
            st_color = "#FF9F0A" if status == "waiting" else self._theme["text_secondary"]
            st_lbl.setStyleSheet("font-size: 10px; color: {}; border: none;".format(st_color))
            title_col.addWidget(st_lbl)
            hrow.addLayout(title_col, 1)

            if meta["supports_poll"]:
                rbtn = QPushButton("↻" if not is_fetching else "…")
                rbtn.setEnabled(not is_fetching)
                rbtn.setToolTip(t.refresh_provider_help(meta["display_name"]))
                rbtn.clicked.connect(lambda _=False, p=prov: self.refresh_quota(p, force=True))
                hrow.addWidget(rbtn)

            obtn = QPushButton(t.open_button)
            obtn.setToolTip(t.open_provider_help(meta["display_name"]))
            obtn.clicked.connect(lambda _=False, p=prov: focus_provider_app(p))
            hrow.addWidget(obtn)
            clay.addLayout(hrow)

            # Active / Waiting Sessions
            for s in sessions:
                clay.addWidget(self._build_session_row(s, now_ts))

            # Error notice
            if err_msg:
                elbl = QLabel("⚠ " + err_msg)
                elbl.setWordWrap(True)
                elbl.setStyleSheet(
                    "font-size: 10px; color: #FF9F0A; background-color: rgba(255,159,10,0.12); "
                    "border-radius: 6px; padding: 5px 7px; border: none;"
                )
                clay.addWidget(elbl)

            # Quotas
            if snapshot:
                fetched_dt = parse_iso_datetime(snapshot.get("fetchedAt"))
                buckets = [b for b in (snapshot.get("buckets") or []) if b.get("disabled") is not True]
                if not buckets:
                    nl = QLabel(t.no_quotas_reported)
                    nl.setStyleSheet("font-size: 10.5px; color: {}; border: none;".format(self._theme["text_secondary"]))
                    clay.addWidget(nl)
                elif prov == "antigravity":
                    active_gk = self.core.active_antigravity_group_key(now_ts)
                    gem = [
                        b for b in buckets
                        if b.get("groupKey") == "gemini" or (b.get("groupKey") is None and "3P" not in str(b.get("group", "")) and "3p" not in str(b.get("id", "")))
                    ]
                    tp = [
                        b for b in buckets
                        if b.get("groupKey") == "third_party" or (b.get("groupKey") is None and ("3P" in str(b.get("group", "")) or "3p" in str(b.get("id", ""))))
                    ]
                    if gem:
                        clay.addWidget(self._build_subgroup("Gemini", active_gk == "gemini", gem, fetched_dt, now_dt))
                    if tp:
                        clay.addWidget(self._build_subgroup(t.third_party_group_title, active_gk == "third_party", tp, fetched_dt, now_dt))
                else:
                    for b in buckets:
                        clay.addWidget(self._build_quota_row(b, fetched_dt, now_dt))
            elif prov == "claude":
                wl = QLabel(t.waiting_claude_session)
                wl.setWordWrap(True)
                wl.setStyleSheet("font-size: 10.5px; color: {}; border: none;".format(self._theme["text_secondary"]))
                clay.addWidget(wl)
            elif is_fetching:
                fl = QLabel(t.fetching_quotas)
                fl.setStyleSheet("font-size: 10.5px; color: {}; border: none;".format(self._theme["text_secondary"]))
                clay.addWidget(fl)

            return card

        def _build_session_row(self, session, now_ts):
            t = self.t
            row = self._make_card_frame(self._theme["subcard_bg"], "transparent")
            rlay = QHBoxLayout(row)
            rlay.setContentsMargins(7, 5, 7, 5)
            rlay.setSpacing(6)

            s_status = session.get("status", "idle")
            dot = QLabel("●")
            dot.setStyleSheet("font-size: 9px; color: {}; border: none;".format(status_hex_color(s_status)))
            rlay.addWidget(dot)

            col = QVBoxLayout()
            col.setSpacing(1)
            ws = session.get("workspace") or t.no_workspace
            model = session.get("modelName") or ""
            top_txt = "{} · {}".format(ws, model) if model else ws
            tl = QLabel(top_txt)
            tl.setStyleSheet("font-size: 11px; font-weight: 600; border: none;")
            col.addWidget(tl)

            detail = t.session_detail(
                session.get("detailKey"),
                session.get("detailArg"),
                session.get("detail", ""),
            )
            elapsed = t.format_elapsed(float(session.get("updatedAt") or now_ts), now_ts)
            dl = QLabel("{} · {}".format(detail, elapsed))
            dcolor = "#FF9F0A" if s_status == "waiting" else self._theme["text_secondary"]
            dl.setStyleSheet("font-size: 10px; color: {}; border: none;".format(dcolor))
            col.addWidget(dl)
            rlay.addLayout(col, 1)

            xbtn = QPushButton("×")
            xbtn.setObjectName("PlainBtn")
            xbtn.setToolTip(t.dismiss_session_help)
            sid = session.get("id", "")
            xbtn.clicked.connect(lambda _=False, i=sid: self._dismiss_session(i))
            rlay.addWidget(xbtn)
            return row

        def _build_subgroup(self, title, is_active, buckets, fetched_dt, now_dt):
            t = self.t
            box = self._make_card_frame(self._theme["subcard_bg"], "transparent")
            blay = QVBoxLayout(box)
            blay.setContentsMargins(8, 7, 8, 7)
            blay.setSpacing(6)

            top = QHBoxLayout()
            tl = QLabel(title)
            tl.setStyleSheet("font-size: 10.5px; font-weight: 700; color: {}; border: none;".format(self._theme["text_secondary"]))
            top.addWidget(tl)
            top.addStretch()
            if is_active:
                badge = QLabel(t.in_use_badge)
                badge.setStyleSheet(
                    "font-size: 9px; font-weight: 700; color: {}; background-color: rgba(10,132,255,0.16); "
                    "border-radius: 5px; padding: 1px 5px; border: none;".format(self._theme["accent"])
                )
                top.addWidget(badge)
            blay.addLayout(top)

            for b in buckets:
                blay.addWidget(self._build_quota_row(b, fetched_dt, now_dt))
            return box

        def _build_quota_row(self, bucket, fetched_dt, now_dt):
            t = self.t
            w = QWidget()
            w.setStyleSheet("background: transparent; border: none;")
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(3)

            frac = max(0.0, min(1.0, float(bucket.get("remainingFraction", 0.0))))
            pct = max(0, min(100, int(round(frac * 100.0))))
            is_low = pct < 20

            r1 = QHBoxLayout()
            lbl = QLabel(t.bucket_label(bucket))
            lbl.setStyleSheet("font-size: 10.5px; border: none;")
            r1.addWidget(lbl)
            r1.addStretch()
            pct_txt = ("⚠ {}%".format(pct)) if is_low else "{}%".format(pct)
            plbl = QLabel(pct_txt)
            pcolor = "#FF3B30" if is_low else self._theme["text_primary"]
            plbl.setStyleSheet("font-size: 11px; font-weight: 700; color: {}; border: none;".format(pcolor))
            r1.addWidget(plbl)
            v.addLayout(r1)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(
                "QProgressBar {{ background-color: {}; border-radius: 3px; border: none; }}"
                "QProgressBar::chunk {{ background-color: {}; border-radius: 3px; }}".format(
                    self._theme["btn_bg"], bar_hex_color(pct)
                )
            )
            v.addWidget(bar)

            reset_dt = parse_iso_datetime(bucket.get("resetTime"))
            countdown = t.format_countdown(
                reset_dt, int(bucket.get("resetInSeconds") or 0), fetched_dt, now_dt
            )
            sub_txt = t.resets_in_text(countdown)
            if countdown != t.reset_done_label:
                clk = t.format_reset_clock(reset_dt, bool(bucket.get("isWeekly")))
                if clk:
                    sub_txt += " · " + clk
            slbl = QLabel(sub_txt)
            slbl.setStyleSheet("font-size: 9.5px; color: {}; border: none;".format(self._theme["text_secondary"]))
            v.addWidget(slbl)
            return w

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Agent Monitor")
    _monitor = MonitorApp(app)
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status-json",
        action="store_true",
        help="Print current monitor status as JSON and exit",
    )
    args, _ = parser.parse_known_args()

    if args.status_json:
        core = MonitorCore()
        sys.stdout.write(json.dumps(core.build_status_json()) + "\n")
        sys.stdout.flush()
        return

    main_gui()


if __name__ == "__main__":
    main()
