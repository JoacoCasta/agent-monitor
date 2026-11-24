#!/usr/bin/python3
import ctypes
import datetime
import locale
import os
import sys

SUPPORTED_LANGUAGES = ("system", "en", "es", "pt", "fr", "de", "zh-Hans", "ja")

NATIVE_NAMES = {
    "en": "English",
    "es": "Español",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
    "zh-Hans": "简体中文",
    "ja": "日本語",
}


def detect_os_language_code():
    candidates = []
    if sys.platform == "win32":
        try:
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            win_loc = locale.windows_locale.get(lang_id, "")
            if win_loc:
                candidates.append(win_loc)
        except Exception:
            pass
    for env_key in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(env_key, "")
        if val:
            candidates.append(val)
    try:
        loc = locale.getlocale()[0]
        if loc:
            candidates.append(loc)
    except Exception:
        pass

    for raw in candidates:
        lower = raw.lower().replace("_", "-")
        if lower.startswith("es"):
            return "es"
        if lower.startswith("pt"):
            return "pt"
        if lower.startswith("fr"):
            return "fr"
        if lower.startswith("de"):
            return "de"
        if lower.startswith("zh"):
            return "zh-Hans"
        if lower.startswith("ja"):
            return "ja"
        if lower.startswith("en"):
            return "en"
    return "en"


def resolve_language_code(language_pref):
    if language_pref and language_pref != "system" and language_pref in NATIVE_NAMES:
        return language_pref
    return detect_os_language_code()


class L10n:
    def __init__(self, language_pref="system"):
        self.language = language_pref if language_pref in SUPPORTED_LANGUAGES else "system"
        self.code = resolve_language_code(self.language)

    def _tr(self, en, es, pt, fr, de, zh, ja):
        mapping = {
            "en": en,
            "es": es,
            "pt": pt,
            "fr": fr,
            "de": de,
            "zh-Hans": zh,
            "ja": ja,
        }
        return mapping.get(self.code, en)

    def picker_label(self, lang_code):
        if lang_code == "system":
            return self.system_auto_label
        return NATIVE_NAMES.get(lang_code, lang_code)

    @property
    def app_title(self):
        return "Agent Monitor"

    def status_title(self, status):
        if status == "waiting":
            return self._tr(
                en="Waiting for response",
                es="Esperando respuesta",
                pt="Aguardando resposta",
                fr="En attente de réponse",
                de="Wartet auf Antwort",
                zh="等待回复",
                ja="応答待ち",
            )
        if status == "active":
            return self._tr(
                en="Active",
                es="Activo",
                pt="Ativo",
                fr="Actif",
                de="Aktiv",
                zh="运行中",
                ja="稼働中",
            )
        return self._tr(
            en="Idle",
            es="Inactivo",
            pt="Inativo",
            fr="Inactif",
            de="Inaktiv",
            zh="空闲",
            ja="待機中",
        )

    @property
    def no_workspace(self):
        return self._tr(
            en="No workspace",
            es="Sin workspace",
            pt="Sem workspace",
            fr="Sans espace de travail",
            de="Kein Arbeitsbereich",
            zh="无工作区",
            ja="ワークスペースなし",
        )

    @property
    def choose_agents_title(self):
        return self._tr(
            en="Choose your agents",
            es="Elige tus agentes",
            pt="Escolha seus agentes",
            fr="Choisissez vos agents",
            de="Agenten auswählen",
            zh="选择你的代理",
            ja="エージェントを選択",
        )

    @property
    def choose_agents_subtitle(self):
        return self._tr(
            en="Select the tools you want to monitor in your system tray. You can change this anytime in Settings.",
            es="Selecciona las herramientas que quieres monitorear en tu bandeja del sistema. Podrás cambiarlo luego en Ajustes.",
            pt="Selecione as ferramentas que deseja monitorar na bandeja do sistema. Você pode alterar isso depois em Ajustes.",
            fr="Sélectionnez les outils à suivre dans la zone de notification. Modifiable à tout moment dans les Réglages.",
            de="Wähle die Tools aus, die im Infobereich überwacht werden sollen. Jederzeit in den Einstellungen änderbar.",
            zh="选择要在系统托盘监控的工具，之后可随时在设置中修改。",
            ja="システムトレイで監視するツールを選択してください。設定からいつでも変更できます。",
        )

    @property
    def detected_badge(self):
        return self._tr(
            en="Detected",
            es="Detectado",
            pt="Detectado",
            fr="Détecté",
            de="Erkannt",
            zh="已检测到",
            ja="検出済み",
        )

    def onboarding_subtitle(self, provider):
        if provider == "antigravity":
            return self._tr(
                en="5h/weekly quotas (Gemini & 3P) + live traffic light",
                es="Cuotas 5h/semanal (Gemini y 3P) + semáforo en vivo",
                pt="Cotas 5h/semanal (Gemini e 3P) + semáforo ao vivo",
                fr="Quotas 5h/hebdo (Gemini & 3P) + statut en direct",
                de="5h-/Wochenlimits (Gemini & 3P) + Live-Ampel",
                zh="5小时/每周配额（Gemini 与 3P）+ 实时状态灯",
                ja="5時間/週間クォータ（Gemini・3P）+ ライブ状態表示",
            )
        if provider == "codex":
            return self._tr(
                en="Codex account limits + live status via hooks",
                es="Límites de cuenta Codex + semáforo vía hooks",
                pt="Limites da conta Codex + semáforo via hooks",
                fr="Limites du compte Codex + statut via hooks",
                de="Codex-Kontolimits + Live-Status über Hooks",
                zh="Codex 账户限额 + Hooks 实时状态",
                ja="Codex アカウント制限 + Hooks ステータス",
            )
        return self._tr(
            en="5h/weekly limits via statusLine + live status via hooks",
            es="Límites 5h/semanal vía statusLine + semáforo vía hooks",
            pt="Limites 5h/semanal via statusLine + semáforo via hooks",
            fr="Limites 5h/hebdo via statusLine + statut via hooks",
            de="5h-/Wochenlimits via statusLine + Status via Hooks",
            zh="通过 statusLine 获取 5小时/每周限额 + Hooks 状态",
            ja="statusLine 経由の5時間/週間制限 + Hooks ステータス",
        )

    @property
    def codex_trust_hint(self):
        return self._tr(
            en="• Codex: if prompted in CLI, approve hooks once with /hooks.",
            es="• Codex: si aparece aviso en CLI, aprueba los hooks con /hooks.",
            pt="• Codex: se aparecer aviso na CLI, aprove os hooks com /hooks.",
            fr="• Codex : si demandé dans la CLI, approuvez les hooks via /hooks.",
            de="• Codex: falls im CLI gefragt, Hooks einmal mit /hooks freigeben.",
            zh="• Codex：如 CLI 提示，请运行 /hooks 授权一次。",
            ja="• Codex：CLI で確認が出たら /hooks で一度承認してください。",
        )

    @property
    def claude_statusline_hint(self):
        return self._tr(
            en="• Claude Code: quotas update automatically when a session runs (statusLine).",
            es="• Claude Code: sus cuotas se actualizan al iniciar una sesión (statusLine).",
            pt="• Claude Code: as cotas atualizam ao iniciar uma sessão (statusLine).",
            fr="• Claude Code : les quotas se mettent à jour dès qu'une session tourne (statusLine).",
            de="• Claude Code: Quoten aktualisieren sich automatisch ab der ersten Sitzung (statusLine).",
            zh="• Claude Code：运行会话后将通过 statusLine 自动更新配额。",
            ja="• Claude Code：セッション実行時に statusLine 経由で自動更新されます。",
        )

    @property
    def get_started(self):
        return self._tr(
            en="Get Started",
            es="Comenzar",
            pt="Começar",
            fr="Commencer",
            de="Loslegen",
            zh="开始使用",
            ja="開始する",
        )

    @property
    def back(self):
        return self._tr(
            en="Back",
            es="Volver",
            pt="Voltar",
            fr="Retour",
            de="Zurück",
            zh="返回",
            ja="戻る",
        )

    @property
    def settings_title(self):
        return self._tr(
            en="Settings",
            es="Ajustes",
            pt="Ajustes",
            fr="Réglages",
            de="Einstellungen",
            zh="设置",
            ja="設定",
        )

    @property
    def done(self):
        return self._tr(
            en="Done",
            es="Listo",
            pt="Pronto",
            fr="OK",
            de="Fertig",
            zh="完成",
            ja="完了",
        )

    @property
    def active_agents_header(self):
        return self._tr(
            en="Active agents (minimum 1)",
            es="Agentes activos (mínimo 1)",
            pt="Agentes ativos (mínimo 1)",
            fr="Agents actifs (minimum 1)",
            de="Aktive Agenten (mind. 1)",
            zh="启用的代理（至少 1 个）",
            ja="有効なエージェント（最低1つ）",
        )

    @property
    def language_label(self):
        return self._tr(
            en="Language",
            es="Idioma",
            pt="Idioma",
            fr="Langue",
            de="Sprache",
            zh="语言",
            ja="言語",
        )

    @property
    def launch_at_login(self):
        return self._tr(
            en="Start at login",
            es="Iniciar al encender",
            pt="Iniciar com o sistema",
            fr="Lancer au démarrage",
            de="Bei Anmeldung starten",
            zh="开机自动启动",
            ja="ログイン時に起動",
        )

    @property
    def system_auto_label(self):
        return self._tr(
            en="Auto (OS)",
            es="Automático (Sistema)",
            pt="Automático (Sistema)",
            fr="Auto (Système)",
            de="Automatisch (System)",
            zh="自动（系统）",
            ja="自動（システム）",
        )

    @property
    def hooks_active(self):
        return self._tr(
            en="Hooks active",
            es="Hooks activos",
            pt="Hooks ativos",
            fr="Hooks actifs",
            de="Hooks aktiv",
            zh="Hooks 已启用",
            ja="Hooks 有効",
        )

    @property
    def hooks_disabled(self):
        return self._tr(
            en="Hooks disabled",
            es="Hooks desactivados",
            pt="Hooks desativados",
            fr="Hooks désactivés",
            de="Hooks deaktiviert",
            zh="Hooks 已停用",
            ja="Hooks 無効",
        )

    @property
    def not_detected(self):
        return self._tr(
            en="· Not detected",
            es="· No detectado",
            pt="· Não detectado",
            fr="· Non détecté",
            de="· Nicht erkannt",
            zh="· 未检测到",
            ja="· 未検出",
        )

    @property
    def checking_status(self):
        return self._tr(
            en="Checking status...",
            es="Verificando estado...",
            pt="Verificando status...",
            fr="Vérification...",
            de="Status wird geprüft...",
            zh="正在检查状态...",
            ja="状態を確認中...",
        )

    @property
    def hooks_auto_note(self):
        return self._tr(
            en="Enabling or disabling an agent automatically connects or cleans up its hooks while preserving your existing settings.",
            es="Al activar o desactivar un agente, sus hooks se conectan o limpian automáticamente preservando tus configuraciones previas.",
            pt="Ao ativar ou desativar um agente, os hooks são configurados ou removidos automaticamente preservando suas configurações.",
            fr="Activer ou désactiver un agent configure ou nettoie ses hooks automatiquement tout en préservant vos réglages existants.",
            de="Beim Aktivieren oder Deaktivieren eines Agenten werden Hooks automatisch eingerichtet oder bereinigt, ohne vorhandene Einstellungen zu überschreiben.",
            zh="启用或停用代理会自动配置或清理对应的 Hooks，同时保留你原有的配置。",
            ja="エージェントを切り替えると既存設定を保持したまま Hooks が自動設定・解除されます。",
        )

    @property
    def resync_hooks(self):
        return self._tr(
            en="Re-sync hooks",
            es="Re-sincronizar hooks",
            pt="Ressincronizar hooks",
            fr="Resynchroniser les hooks",
            de="Hooks neu synchronisieren",
            zh="重新同步 Hooks",
            ja="Hooks を再同期",
        )

    @property
    def clear_states(self):
        return self._tr(
            en="Clear states",
            es="Limpiar estados",
            pt="Limpar estados",
            fr="Effacer les états",
            de="Status zurücksetzen",
            zh="清除状态",
            ja="状態をクリア",
        )

    @property
    def refresh_all_help(self):
        return self._tr(
            en="Refresh all quotas now",
            es="Refrescar cuotas ahora",
            pt="Atualizar cotas agora",
            fr="Actualiser les quotas maintenant",
            de="Quoten jetzt aktualisieren",
            zh="立即刷新所有配额",
            ja="今すぐすべて更新",
        )

    @property
    def settings_help(self):
        return self._tr(
            en="Select agents and settings",
            es="Elegir agentes y ajustes",
            pt="Escolher agentes e ajustes",
            fr="Choisir les agents et réglages",
            de="Agenten und Einstellungen wählen",
            zh="选择代理与设置",
            ja="エージェントと設定",
        )

    @property
    def open_button(self):
        return self._tr(
            en="Open",
            es="Abrir",
            pt="Abrir",
            fr="Ouvrir",
            de="Öffnen",
            zh="打开",
            ja="開く",
        )

    def open_provider_help(self, name):
        return self._tr(
            en="Open or focus {}".format(name),
            es="Abrir o enfocar {}".format(name),
            pt="Abrir ou focar {}".format(name),
            fr="Ouvrir ou afficher {}".format(name),
            de="{} öffnen oder fokussieren".format(name),
            zh="打开或聚焦 {}".format(name),
            ja="{} を開く / 前面表示".format(name),
        )

    def refresh_provider_help(self, name):
        return self._tr(
            en="Refresh {}".format(name),
            es="Refrescar {}".format(name),
            pt="Atualizar {}".format(name),
            fr="Actualiser {}".format(name),
            de="{} aktualisieren".format(name),
            zh="刷新 {}".format(name),
            ja="{} を更新".format(name),
        )

    @property
    def in_use_badge(self):
        return self._tr(
            en="In use",
            es="En uso",
            pt="Em uso",
            fr="En cours",
            de="Aktiv",
            zh="使用中",
            ja="使用中",
        )

    @property
    def no_quotas_reported(self):
        return self._tr(
            en="No quotas reported for your plan",
            es="Sin cuotas reportadas para tu plan",
            pt="Sem cotas reportadas para o seu plano",
            fr="Aucun quota signalé pour votre offre",
            de="Keine Limits für deinen Tarif gemeldet",
            zh="当前套餐未返回配额信息",
            ja="プランのクォータ情報がありません",
        )

    @property
    def waiting_claude_session(self):
        return self._tr(
            en="Waiting for first Claude Code session (auto-updates via statusLine)",
            es="Esperando primera sesión de Claude Code (actualización automática vía statusLine)",
            pt="Aguardando primeira sessão do Claude Code (atualiza via statusLine)",
            fr="En attente d'une session Claude Code (mise à jour auto via statusLine)",
            de="Warte auf erste Claude-Code-Sitzung (Auto-Update via statusLine)",
            zh="等待首次 Claude Code 会话（通过 statusLine 自动更新）",
            ja="最初の Claude Code セッション待機中（statusLine で自動更新）",
        )

    @property
    def fetching_quotas(self):
        return self._tr(
            en="Checking quotas...",
            es="Consultando cuotas...",
            pt="Consultando cotas...",
            fr="Récupération des quotas...",
            de="Quoten werden abgerufen...",
            zh="正在查询配额...",
            ja="クォータを取得中...",
        )

    @property
    def updating_quotas(self):
        return self._tr(
            en="Updating quotas...",
            es="Actualizando cuotas...",
            pt="Atualizando cotas...",
            fr="Mise à jour des quotas...",
            de="Aktualisiere Quoten...",
            zh="正在更新配额...",
            ja="クォータを更新中...",
        )

    def updated_text(self, elapsed):
        return self._tr(
            en="Updated {}".format(elapsed),
            es="Actualizado {}".format(elapsed),
            pt="Atualizado {}".format(elapsed),
            fr="Mis à jour {}".format(elapsed),
            de="Aktualisiert {}".format(elapsed),
            zh="更新于 {}".format(elapsed),
            ja="更新: {}".format(elapsed),
        )

    @property
    def ready(self):
        return self._tr(
            en="Ready",
            es="Listo",
            pt="Pronto",
            fr="Prêt",
            de="Bereit",
            zh="就绪",
            ja="準備完了",
        )

    @property
    def dismiss_session_help(self):
        return self._tr(
            en="Dismiss session",
            es="Descartar conversación",
            pt="Dispensar sessão",
            fr="Masquer la session",
            de="Sitzung ausblenden",
            zh="关闭此会话",
            ja="セッションを非表示",
        )

    @property
    def quit(self):
        return self._tr(
            en="Quit",
            es="Salir",
            pt="Sair",
            fr="Quitter",
            de="Beenden",
            zh="退出",
            ja="終了",
        )

    @property
    def menu_refresh_all(self):
        return self._tr(
            en="Refresh all",
            es="Refrescar todo",
            pt="Atualizar tudo",
            fr="Tout actualiser",
            de="Alles aktualisieren",
            zh="全部刷新",
            ja="すべて更新",
        )

    def menu_open_provider(self, name):
        return self._tr(
            en="Open {}".format(name),
            es="Abrir {}".format(name),
            pt="Abrir {}".format(name),
            fr="Ouvrir {}".format(name),
            de="{} öffnen".format(name),
            zh="打开 {}".format(name),
            ja="{} を開く".format(name),
        )

    @property
    def menu_settings(self):
        return self._tr(
            en="Settings...",
            es="Ajustes...",
            pt="Ajustes...",
            fr="Réglages...",
            de="Einstellungen...",
            zh="设置...",
            ja="設定...",
        )

    @property
    def third_party_group_title(self):
        return self._tr(
            en="3P Models (Claude / GPT)",
            es="Modelos 3P (Claude / GPT)",
            pt="Modelos 3P (Claude / GPT)",
            fr="Modèles 3P (Claude / GPT)",
            de="3P-Modelle (Claude / GPT)",
            zh="第三方模型 (Claude / GPT)",
            ja="3Pモデル (Claude / GPT)",
        )

    def group_display_name(self, group_key, fallback):
        if group_key == "gemini":
            return "Gemini"
        if group_key == "third_party":
            return self.third_party_group_title
        if group_key == "codex":
            return "Codex"
        if group_key == "claude":
            return "Claude Code"
        if fallback and "3P" in fallback:
            return self.third_party_group_title
        return fallback

    def bucket_label(self, bucket):
        wk = bucket.get("windowKind")
        amt = bucket.get("windowAmount") or 1
        if wk == "5h":
            return self._tr(
                en="5-hour window",
                es="Ventana 5 horas",
                pt="Janela de 5 horas",
                fr="Fenêtre 5 heures",
                de="5-Stunden-Fenster",
                zh="5 小时窗口",
                ja="5時間枠",
            )
        if wk == "weekly":
            return self._tr(
                en="Weekly limit",
                es="Límite semanal",
                pt="Limite semanal",
                fr="Limite hebdomadaire",
                de="Wochenlimit",
                zh="每周限额",
                ja="週間制限",
            )
        if wk == "monthly":
            return self._tr(
                en="Monthly limit",
                es="Límite mensual",
                pt="Limite mensal",
                fr="Limite mensuelle",
                de="Monatslimit",
                zh="每月限额",
                ja="月間制限",
            )
        if wk == "spend":
            return self._tr(
                en="Spend limit",
                es="Límite de gasto",
                pt="Limite de gastos",
                fr="Limite de dépense",
                de="Ausgabenlimit",
                zh="消费限额",
                ja="利用上限",
            )
        if wk == "days":
            return self._tr(
                en="{}d window".format(amt),
                es="Ventana {}d".format(amt),
                pt="Janela {}d".format(amt),
                fr="Fenêtre {}j".format(amt),
                de="{}T-Fenster".format(amt),
                zh="{} 天窗口".format(amt),
                ja="{}日間枠".format(amt),
            )
        if wk == "hours":
            return self._tr(
                en="{}h window".format(amt),
                es="Ventana {}h".format(amt),
                pt="Janela {}h".format(amt),
                fr="Fenêtre {}h".format(amt),
                de="{}h-Fenster".format(amt),
                zh="{} 小时窗口".format(amt),
                ja="{}時間枠".format(amt),
            )
        if wk == "generic":
            return self._tr(
                en="Window",
                es="Ventana",
                pt="Janela",
                fr="Fenêtre",
                de="Fenster",
                zh="限额窗口",
                ja="利用枠",
            )
        return str(bucket.get("label") or "")

    def session_detail(self, key, arg, fallback):
        if key == "session_start":
            return self._tr(
                en="Starting session...",
                es="Iniciando sesión...",
                pt="Iniciando sessão...",
                fr="Démarrage de la session...",
                de="Sitzung wird gestartet...",
                zh="正在启动会话...",
                ja="セッション開始中...",
            )
        if key == "thinking":
            return self._tr(
                en="Thinking...",
                es="Pensando...",
                pt="Pensando...",
                fr="Réflexion...",
                de="Denkt nach...",
                zh="思考中...",
                ja="思考中...",
            )
        if key == "waiting_permission":
            return self._tr(
                en="Waiting for permission",
                es="Esperando permiso",
                pt="Aguardando permissão",
                fr="En attente d'autorisation",
                de="Wartet auf Erlaubnis",
                zh="等待权限确认",
                ja="許可待ち",
            )
        if key == "waiting_elicitation":
            return self._tr(
                en="Waiting for confirmation",
                es="Esperando confirmación",
                pt="Aguardando confirmação",
                fr="En attente de confirmation",
                de="Wartet auf Bestätigung",
                zh="等待确认",
                ja="確認待ち",
            )
        if key == "waiting_question":
            return self._tr(
                en="Waiting for answer",
                es="Esperando respuesta",
                pt="Aguardando resposta",
                fr="En attente de réponse",
                de="Wartet auf Antwort",
                zh="等待回答",
                ja="回答待ち",
            )
        if key == "waiting_approval":
            return self._tr(
                en="Waiting for approval",
                es="Esperando aprobación",
                pt="Aguardando aprovação",
                fr="En attente d'approbation",
                de="Wartet auf Freigabe",
                zh="等待批准",
                ja="承認待ち",
            )
        if key == "waiting_plan_approval":
            return self._tr(
                en="Waiting for plan approval",
                es="Esperando aprobación del plan",
                pt="Aguardando aprovação do plano",
                fr="En attente d'approbation du plan",
                de="Wartet auf Planfreigabe",
                zh="等待计划批准",
                ja="プラン承認待ち",
            )
        if key == "preparing_plan":
            return self._tr(
                en="Preparing plan...",
                es="Preparando plan...",
                pt="Preparando plano...",
                fr="Préparation du plan...",
                de="Plan wird vorbereitet...",
                zh="正在准备计划...",
                ja="プラン準備中...",
            )
        if key == "running_tool":
            tool = arg or ""
            if not tool:
                return self.session_detail("running_tool_generic", None, fallback)
            return self._tr(
                en="Running {}".format(tool),
                es="Ejecutando {}".format(tool),
                pt="Executando {}".format(tool),
                fr="Exécution de {}".format(tool),
                de="Führt {} aus".format(tool),
                zh="正在运行 {}".format(tool),
                ja="{} を実行中".format(tool),
            )
        if key == "running_tool_generic":
            return self._tr(
                en="Running tool",
                es="Ejecutando herramienta",
                pt="Executando ferramenta",
                fr="Exécution de l'outil",
                de="Führt Tool aus",
                zh="正在运行工具",
                ja="ツールを実行中",
            )
        if key == "processing_answer":
            return self._tr(
                en="Processing response...",
                es="Procesando respuesta...",
                pt="Processando resposta...",
                fr="Traitement de la réponse...",
                de="Antwort wird verarbeitet...",
                zh="正在处理回复...",
                ja="応答を処理中...",
            )
        if key == "analyzing_result":
            return self._tr(
                en="Analyzing result...",
                es="Analizando resultado...",
                pt="Analisando resultado...",
                fr="Analyse du résultat...",
                de="Ergebnis wird analysiert...",
                zh="正在分析结果...",
                ja="結果を分析中...",
            )
        if key == "background_tasks":
            return self._tr(
                en="Background tasks running...",
                es="Tareas en segundo plano...",
                pt="Tarefas em segundo plano...",
                fr="Tâches en arrière-plan...",
                de="Hintergrundaufgaben laufen...",
                zh="后台任务运行中...",
                ja="バックグラウンド処理中...",
            )
        if key == "idle":
            return self.status_title("idle")
        return fallback

    def waiting_notification_title(self, display_name):
        return self._tr(
            en="{} is waiting for your input".format(display_name),
            es="{} espera tu respuesta".format(display_name),
            pt="{} aguarda sua resposta".format(display_name),
            fr="{} attend votre réponse".format(display_name),
            de="{} wartet auf deine Antwort".format(display_name),
            zh="{} 正在等待你的回复".format(display_name),
            ja="{} が応答を待っています".format(display_name),
        )

    def low_quota_notification_title(self, display_name):
        return self._tr(
            en="Low quota on {}".format(display_name),
            es="Cuota baja en {}".format(display_name),
            pt="Cota baixa em {}".format(display_name),
            fr="Quota faible sur {}".format(display_name),
            de="Niedriges Limit bei {}".format(display_name),
            zh="{} 配额不足".format(display_name),
            ja="{} のクォータ残量低下".format(display_name),
        )

    def low_quota_notification_body(self, prefix, percent, countdown):
        return self._tr(
            en="{}: {}% left (resets in {})".format(prefix, percent, countdown),
            es="{}: {}% restante (resetea en {})".format(prefix, percent, countdown),
            pt="{}: {}% restante (reinicia em {})".format(prefix, percent, countdown),
            fr="{} : {}% restant (réinitialisation dans {})".format(prefix, percent, countdown),
            de="{}: {}% übrig (Reset in {})".format(prefix, percent, countdown),
            zh="{}：剩余 {}%（{} 后重置）".format(prefix, percent, countdown),
            ja="{}: 残り {}%（{} 後にリセット）".format(prefix, percent, countdown),
        )

    @property
    def reset_done_label(self):
        return self._tr(
            en="Reset",
            es="Reseteado",
            pt="Reiniciado",
            fr="Réinitialisé",
            de="Zurückgesetzt",
            zh="已重置",
            ja="リセット済み",
        )

    def resets_in_text(self, countdown):
        if countdown == self.reset_done_label:
            return self.reset_done_label
        return self._tr(
            en="Resets in {}".format(countdown),
            es="Resetea en {}".format(countdown),
            pt="Reinicia em {}".format(countdown),
            fr="Réinitialise dans {}".format(countdown),
            de="Reset in {}".format(countdown),
            zh="{} 后重置".format(countdown),
            ja="{} 後にリセット".format(countdown),
        )

    def format_countdown(self, reset_dt, fallback_seconds, fetched_dt, now_dt):
        if reset_dt is not None:
            remaining = (reset_dt - now_dt).total_seconds()
        elif fetched_dt is not None:
            remaining = float(fallback_seconds) - (now_dt - fetched_dt).total_seconds()
        else:
            remaining = float(fallback_seconds)

        if remaining <= 0:
            return self.reset_done_label

        total_sec = int(remaining)
        days = total_sec // 86400
        hours = (total_sec % 86400) // 3600
        minutes = (total_sec % 3600) // 60
        seconds = total_sec % 60

        if self.code == "fr":
            if days > 0:
                return "{}j {}h".format(days, hours)
            if hours > 0:
                return "{}h {}m".format(hours, minutes)
            if minutes > 0:
                return "{}m {}s".format(minutes, seconds)
            return "< 1m"
        if self.code == "de":
            if days > 0:
                return "{}T {}Std".format(days, hours)
            if hours > 0:
                return "{}Std {}Min".format(hours, minutes)
            if minutes > 0:
                return "{}Min {}Sek".format(minutes, seconds)
            return "< 1Min"
        if self.code == "zh-Hans":
            if days > 0:
                return "{}天{}小时".format(days, hours)
            if hours > 0:
                return "{}小时{}分".format(hours, minutes)
            if minutes > 0:
                return "{}分{}秒".format(minutes, seconds)
            return "< 1分钟"
        if self.code == "ja":
            if days > 0:
                return "{}日{}時間".format(days, hours)
            if hours > 0:
                return "{}時間{}分".format(hours, minutes)
            if minutes > 0:
                return "{}分{}秒".format(minutes, seconds)
            return "1分未満"

        if days > 0:
            return "{}d {}h".format(days, hours)
        if hours > 0:
            return "{}h {}m".format(hours, minutes)
        if minutes > 0:
            return "{}m {}s".format(minutes, seconds)
        return "< 1m"

    def format_reset_clock(self, reset_dt, is_weekly):
        if reset_dt is None:
            return ""
        local_dt = reset_dt.astimezone()
        if not is_weekly:
            return local_dt.strftime("%H:%M")

        weekday_names = {
            "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "es": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
            "pt": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
            "fr": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
            "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            "zh-Hans": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
            "ja": ["月", "火", "水", "木", "金", "土", "日"],
        }
        month_names = {
            "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
            "pt": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
            "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
            "de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."],
        }

        wd = weekday_names.get(self.code, weekday_names["en"])[local_dt.weekday()]
        hhmm = local_dt.strftime("%H:%M")

        if self.code == "zh-Hans":
            return "{}/{} {} {}".format(local_dt.month, local_dt.day, wd, hhmm)
        if self.code == "ja":
            return "{}/{}({}) {}".format(local_dt.month, local_dt.day, wd, hhmm)
        mon = month_names.get(self.code, month_names["en"])[local_dt.month - 1]
        if self.code == "en":
            return "{}, {} {}, {}".format(wd, mon, local_dt.day, hhmm)
        return "{} {} {}, {}".format(wd, local_dt.day, mon, hhmm)

    def format_elapsed(self, epoch_sec, now_epoch):
        delta = max(0, int(now_epoch - float(epoch_sec)))
        if delta < 60:
            unit_val = "{}{}".format(delta, "秒" if self.code in ("zh-Hans", "ja") else "s")
        elif delta < 3600:
            mins = delta // 60
            unit = "分钟" if self.code == "zh-Hans" else ("分" if self.code == "ja" else "m")
            unit_val = "{}{}".format(mins, unit)
        elif delta < 86400:
            hours = delta // 3600
            unit = "小时" if self.code == "zh-Hans" else ("時間" if self.code == "ja" else "h")
            unit_val = "{}{}".format(hours, unit)
        else:
            days = delta // 86400
            if self.code == "fr":
                unit = "j"
            elif self.code == "de":
                unit = "T"
            elif self.code == "zh-Hans":
                unit = "天"
            elif self.code == "ja":
                unit = "日"
            else:
                unit = "d"
            unit_val = "{}{}".format(days, unit)

        return self._tr(
            en="{} ago".format(unit_val),
            es="hace {}".format(unit_val),
            pt="há {}".format(unit_val),
            fr="il y a {}".format(unit_val),
            de="vor {}".format(unit_val),
            zh="{}前".format(unit_val),
            ja="{}前".format(unit_val),
        )
