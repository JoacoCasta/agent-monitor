import Foundation

enum AppLanguage: String, Codable, CaseIterable, Identifiable {
    case system
    case en
    case es
    case pt
    case fr
    case de
    case zhHans = "zh-Hans"
    case ja

    var id: String { rawValue }

    var resolvedCode: String {
        if self != .system {
            return rawValue
        }
        for preferred in Locale.preferredLanguages {
            let lower = preferred.lowercased()
            if lower.hasPrefix("es") { return "es" }
            if lower.hasPrefix("pt") { return "pt" }
            if lower.hasPrefix("fr") { return "fr" }
            if lower.hasPrefix("de") { return "de" }
            if lower.hasPrefix("zh") { return "zh-Hans" }
            if lower.hasPrefix("ja") { return "ja" }
            if lower.hasPrefix("en") { return "en" }
        }
        return "en"
    }

    var localeIdentifier: String {
        switch resolvedCode {
        case "es": return "es_ES"
        case "pt": return "pt_BR"
        case "fr": return "fr_FR"
        case "de": return "de_DE"
        case "zh-Hans": return "zh_CN"
        case "ja": return "ja_JP"
        default: return "en_US"
        }
    }

    func pickerLabel(systemAutoLabel: String) -> String {
        switch self {
        case .system: return systemAutoLabel
        case .en: return "English"
        case .es: return "Español"
        case .pt: return "Português"
        case .fr: return "Français"
        case .de: return "Deutsch"
        case .zhHans: return "简体中文"
        case .ja: return "日本語"
        }
    }
}

struct L10n {
    let language: AppLanguage
    let code: String
    let locale: Locale

    init(language: AppLanguage) {
        self.language = language
        let resolved = language.resolvedCode
        self.code = resolved
        self.locale = Locale(identifier: language.localeIdentifier)
    }

    private func tr(
        en: String,
        es: String,
        pt: String,
        fr: String,
        de: String,
        zh: String,
        ja: String
    ) -> String {
        switch code {
        case "es": return es
        case "pt": return pt
        case "fr": return fr
        case "de": return de
        case "zh-Hans": return zh
        case "ja": return ja
        default: return en
        }
    }

    // MARK: - General / Status

    var appTitle: String { "Agent Monitor" }

    func statusTitle(_ status: AgentStatus) -> String {
        switch status {
        case .waiting:
            return tr(
                en: "Waiting for response",
                es: "Esperando respuesta",
                pt: "Aguardando resposta",
                fr: "En attente de réponse",
                de: "Wartet auf Antwort",
                zh: "等待回复",
                ja: "応答待ち"
            )
        case .active:
            return tr(
                en: "Active",
                es: "Activo",
                pt: "Ativo",
                fr: "Actif",
                de: "Aktiv",
                zh: "运行中",
                ja: "稼働中"
            )
        case .idle:
            return tr(
                en: "Idle",
                es: "Inactivo",
                pt: "Inativo",
                fr: "Inactif",
                de: "Inaktiv",
                zh: "空闲",
                ja: "待機中"
            )
        }
    }

    var noWorkspace: String {
        tr(
            en: "No workspace",
            es: "Sin workspace",
            pt: "Sem workspace",
            fr: "Sans espace de travail",
            de: "Kein Arbeitsbereich",
            zh: "无工作区",
            ja: "ワークスペースなし"
        )
    }

    // MARK: - Onboarding

    var chooseAgentsTitle: String {
        tr(
            en: "Choose your agents",
            es: "Elige tus agentes",
            pt: "Escolha seus agentes",
            fr: "Choisissez vos agents",
            de: "Agenten auswählen",
            zh: "选择你的代理",
            ja: "エージェントを選択"
        )
    }

    var chooseAgentsSubtitle: String {
        tr(
            en: "Select the tools you want to monitor in your menu bar. You can change this anytime in Settings.",
            es: "Selecciona las herramientas que quieres monitorear en tu barra de menú. Podrás cambiarlo luego en Ajustes.",
            pt: "Selecione as ferramentas que deseja monitorar na barra de menus. Você pode alterar isso depois em Ajustes.",
            fr: "Sélectionnez les outils à suivre dans la barre des menus. Modifiable à tout moment dans les Réglages.",
            de: "Wähle die Tools aus, die in der Menüleiste überwacht werden sollen. Jederzeit in den Einstellungen änderbar.",
            zh: "选择要在菜单栏监控的工具，之后可随时在设置中修改。",
            ja: "メニューバーで監視するツールを選択してください。設定からいつでも変更できます。"
        )
    }

    var detectedBadge: String {
        tr(
            en: "Detected",
            es: "Detectado",
            pt: "Detectado",
            fr: "Détecté",
            de: "Erkannt",
            zh: "已检测到",
            ja: "検出済み"
        )
    }

    func onboardingSubtitle(for provider: AgentProvider) -> String {
        switch provider {
        case .antigravity:
            return tr(
                en: "5h/weekly quotas (Gemini & 3P) + live traffic light",
                es: "Cuotas 5h/semanal (Gemini y 3P) + semáforo en vivo",
                pt: "Cotas 5h/semanal (Gemini e 3P) + semáforo ao vivo",
                fr: "Quotas 5h/hebdo (Gemini & 3P) + statut en direct",
                de: "5h-/Wochenlimits (Gemini & 3P) + Live-Ampel",
                zh: "5小时/每周配额（Gemini 与 3P）+ 实时状态灯",
                ja: "5時間/週間クォータ（Gemini・3P）+ ライブ状態表示"
            )
        case .codex:
            return tr(
                en: "Codex account limits + live status via hooks",
                es: "Límites de cuenta Codex + semáforo vía hooks",
                pt: "Limites da conta Codex + semáforo via hooks",
                fr: "Limites du compte Codex + statut via hooks",
                de: "Codex-Kontolimits + Live-Status über Hooks",
                zh: "Codex 账户限额 + Hooks 实时状态",
                ja: "Codex アカウント制限 + Hooks ステータス"
            )
        case .claude:
            return tr(
                en: "5h/weekly limits via statusLine + live status via hooks",
                es: "Límites 5h/semanal vía statusLine + semáforo vía hooks",
                pt: "Limites 5h/semanal via statusLine + semáforo via hooks",
                fr: "Limites 5h/hebdo via statusLine + statut via hooks",
                de: "5h-/Wochenlimits via statusLine + Status via Hooks",
                zh: "通过 statusLine 获取 5小时/每周限额 + Hooks 状态",
                ja: "statusLine 経由の5時間/週間制限 + Hooks ステータス"
            )
        }
    }

    var codexTrustHint: String {
        tr(
            en: "• Codex: if prompted in CLI, approve hooks once with /hooks.",
            es: "• Codex: si aparece aviso en CLI, aprueba los hooks con /hooks.",
            pt: "• Codex: se aparecer aviso na CLI, aprove os hooks com /hooks.",
            fr: "• Codex : si demandé dans la CLI, approuvez les hooks via /hooks.",
            de: "• Codex: falls im CLI gefragt, Hooks einmal mit /hooks freigeben.",
            zh: "• Codex：如 CLI 提示，请运行 /hooks 授权一次。",
            ja: "• Codex：CLI で確認が出たら /hooks で一度承認してください。"
        )
    }

    var claudeStatusLineHint: String {
        tr(
            en: "• Claude Code: quotas update automatically when a session runs (statusLine).",
            es: "• Claude Code: sus cuotas se actualizan al iniciar una sesión (statusLine).",
            pt: "• Claude Code: as cotas atualizam ao iniciar uma sessão (statusLine).",
            fr: "• Claude Code : les quotas se mettent à jour dès qu'une session tourne (statusLine).",
            de: "• Claude Code: Quoten aktualisieren sich automatisch ab der ersten Sitzung (statusLine).",
            zh: "• Claude Code：运行会话后将通过 statusLine 自动更新配额。",
            ja: "• Claude Code：セッション実行時に statusLine 経由で自動更新されます。"
        )
    }

    var getStarted: String {
        tr(
            en: "Get Started",
            es: "Comenzar",
            pt: "Começar",
            fr: "Commencer",
            de: "Loslegen",
            zh: "开始使用",
            ja: "開始する"
        )
    }

    // MARK: - Settings

    var back: String {
        tr(
            en: "Back",
            es: "Volver",
            pt: "Voltar",
            fr: "Retour",
            de: "Zurück",
            zh: "返回",
            ja: "戻る"
        )
    }

    var settingsTitle: String {
        tr(
            en: "Settings",
            es: "Ajustes",
            pt: "Ajustes",
            fr: "Réglages",
            de: "Einstellungen",
            zh: "设置",
            ja: "設定"
        )
    }

    var done: String {
        tr(
            en: "Done",
            es: "Listo",
            pt: "Pronto",
            fr: "OK",
            de: "Fertig",
            zh: "完成",
            ja: "完了"
        )
    }

    var activeAgentsHeader: String {
        tr(
            en: "Active agents (minimum 1)",
            es: "Agentes activos (mínimo 1)",
            pt: "Agentes ativos (mínimo 1)",
            fr: "Agents actifs (minimum 1)",
            de: "Aktive Agenten (mind. 1)",
            zh: "启用的代理（至少 1 个）",
            ja: "有効なエージェント（最低1つ）"
        )
    }

    var languageLabel: String {
        tr(
            en: "Language",
            es: "Idioma",
            pt: "Idioma",
            fr: "Langue",
            de: "Sprache",
            zh: "语言",
            ja: "言語"
        )
    }

    var launchAtLogin: String {
        tr(
            en: "Start at login",
            es: "Iniciar al encender",
            pt: "Iniciar com o sistema",
            fr: "Lancer au démarrage",
            de: "Bei Anmeldung starten",
            zh: "开机自动启动",
            ja: "ログイン時に起動"
        )
    }

    var systemAutoLabel: String {
        tr(
            en: "Auto (macOS)",
            es: "Automático (macOS)",
            pt: "Automático (macOS)",
            fr: "Auto (macOS)",
            de: "Automatisch (macOS)",
            zh: "自动（macOS）",
            ja: "自動（macOS）"
        )
    }

    var hooksActive: String {
        tr(
            en: "Hooks active",
            es: "Hooks activos",
            pt: "Hooks ativos",
            fr: "Hooks actifs",
            de: "Hooks aktiv",
            zh: "Hooks 已启用",
            ja: "Hooks 有効"
        )
    }

    var hooksDisabled: String {
        tr(
            en: "Hooks disabled",
            es: "Hooks desactivados",
            pt: "Hooks desativados",
            fr: "Hooks désactivés",
            de: "Hooks deaktiviert",
            zh: "Hooks 已停用",
            ja: "Hooks 無効"
        )
    }

    var notDetected: String {
        tr(
            en: "· Not detected",
            es: "· No detectado",
            pt: "· Não detectado",
            fr: "· Non détecté",
            de: "· Nicht erkannt",
            zh: "· 未检测到",
            ja: "· 未検出"
        )
    }

    var checkingStatus: String {
        tr(
            en: "Checking status...",
            es: "Verificando estado...",
            pt: "Verificando status...",
            fr: "Vérification...",
            de: "Status wird geprüft...",
            zh: "正在检查状态...",
            ja: "状態を確認中..."
        )
    }

    var hooksAutoNote: String {
        tr(
            en: "Enabling or disabling an agent automatically connects or cleans up its hooks while preserving your existing settings.",
            es: "Al activar o desactivar un agente, sus hooks se conectan o limpian automáticamente preservando tus configuraciones previas.",
            pt: "Ao ativar ou desativar um agente, os hooks são configurados ou removidos automaticamente preservando suas configurações.",
            fr: "Activer ou désactiver un agent configure ou nettoie ses hooks automatiquement tout en préservant vos réglages existants.",
            de: "Beim Aktivieren oder Deaktivieren eines Agenten werden Hooks automatisch eingerichtet oder bereinigt, ohne vorhandene Einstellungen zu überschreiben.",
            zh: "启用或停用代理会自动配置或清理对应的 Hooks，同时保留你原有的配置。",
            ja: "エージェントを切り替えると既存設定を保持したまま Hooks が自動設定・解除されます。"
        )
    }

    var resyncHooks: String {
        tr(
            en: "Re-sync hooks",
            es: "Re-sincronizar hooks",
            pt: "Ressincronizar hooks",
            fr: "Resynchroniser les hooks",
            de: "Hooks neu synchronisieren",
            zh: "重新同步 Hooks",
            ja: "Hooks を再同期"
        )
    }

    var clearStates: String {
        tr(
            en: "Clear states",
            es: "Limpiar estados",
            pt: "Limpar estados",
            fr: "Effacer les états",
            de: "Status zurücksetzen",
            zh: "清除状态",
            ja: "状態をクリア"
        )
    }

    // MARK: - Dashboard & Cards

    var refreshAllHelp: String {
        tr(
            en: "Refresh all quotas now",
            es: "Refrescar cuotas ahora",
            pt: "Atualizar cotas agora",
            fr: "Actualiser les quotas maintenant",
            de: "Quoten jetzt aktualisieren",
            zh: "立即刷新所有配额",
            ja: "今すぐすべて更新"
        )
    }

    var settingsHelp: String {
        tr(
            en: "Select agents and settings",
            es: "Elegir agentes y ajustes",
            pt: "Escolher agentes e ajustes",
            fr: "Choisir les agents et réglages",
            de: "Agenten und Einstellungen wählen",
            zh: "选择代理与设置",
            ja: "エージェントと設定"
        )
    }

    var openButton: String {
        tr(
            en: "Open",
            es: "Abrir",
            pt: "Abrir",
            fr: "Ouvrir",
            de: "Öffnen",
            zh: "打开",
            ja: "開く"
        )
    }

    func openProviderHelp(_ name: String) -> String {
        tr(
            en: "Open or focus \(name)",
            es: "Abrir o enfocar \(name)",
            pt: "Abrir ou focar \(name)",
            fr: "Ouvrir ou afficher \(name)",
            de: "\(name) öffnen oder fokussieren",
            zh: "打开或聚焦 \(name)",
            ja: "\(name) を開く / 前面表示"
        )
    }

    func refreshProviderHelp(_ name: String) -> String {
        tr(
            en: "Refresh \(name)",
            es: "Refrescar \(name)",
            pt: "Atualizar \(name)",
            fr: "Actualiser \(name)",
            de: "\(name) aktualisieren",
            zh: "刷新 \(name)",
            ja: "\(name) を更新"
        )
    }

    var inUseBadge: String {
        tr(
            en: "In use",
            es: "En uso",
            pt: "Em uso",
            fr: "En cours",
            de: "Aktiv",
            zh: "使用中",
            ja: "使用中"
        )
    }

    var noQuotasReported: String {
        tr(
            en: "No quotas reported for your plan",
            es: "Sin cuotas reportadas para tu plan",
            pt: "Sem cotas reportadas para o seu plano",
            fr: "Aucun quota signalé pour votre offre",
            de: "Keine Limits für deinen Tarif gemeldet",
            zh: "当前套餐未返回配额信息",
            ja: "プランのクォータ情報がありません"
        )
    }

    var waitingClaudeSession: String {
        tr(
            en: "Waiting for first Claude Code session (auto-updates via statusLine)",
            es: "Esperando primera sesión de Claude Code (actualización automática vía statusLine)",
            pt: "Aguardando primeira sessão do Claude Code (atualiza via statusLine)",
            fr: "En attente d'une session Claude Code (mise à jour auto via statusLine)",
            de: "Warte auf erste Claude-Code-Sitzung (Auto-Update via statusLine)",
            zh: "等待首次 Claude Code 会话（通过 statusLine 自动更新）",
            ja: "最初の Claude Code セッション待機中（statusLine で自動更新）"
        )
    }

    var fetchingQuotas: String {
        tr(
            en: "Checking quotas...",
            es: "Consultando cuotas...",
            pt: "Consultando cotas...",
            fr: "Récupération des quotas...",
            de: "Quoten werden abgerufen...",
            zh: "正在查询配额...",
            ja: "クォータを取得中..."
        )
    }

    var updatingQuotas: String {
        tr(
            en: "Updating quotas...",
            es: "Actualizando cuotas...",
            pt: "Atualizando cotas...",
            fr: "Mise à jour des quotas...",
            de: "Aktualisiere Quoten...",
            zh: "正在更新配额...",
            ja: "クォータを更新中..."
        )
    }

    func updatedText(_ elapsed: String) -> String {
        tr(
            en: "Updated \(elapsed)",
            es: "Actualizado \(elapsed)",
            pt: "Atualizado \(elapsed)",
            fr: "Mis à jour \(elapsed)",
            de: "Aktualisiert \(elapsed)",
            zh: "更新于 \(elapsed)",
            ja: "更新: \(elapsed)"
        )
    }

    var ready: String {
        tr(
            en: "Ready",
            es: "Listo",
            pt: "Pronto",
            fr: "Prêt",
            de: "Bereit",
            zh: "就绪",
            ja: "準備完了"
        )
    }

    var dismissSessionHelp: String {
        tr(
            en: "Dismiss session",
            es: "Descartar conversación",
            pt: "Dispensar sessão",
            fr: "Masquer la session",
            de: "Sitzung ausblenden",
            zh: "关闭此会话",
            ja: "セッションを非表示"
        )
    }

    var quit: String {
        tr(
            en: "Quit",
            es: "Salir",
            pt: "Sair",
            fr: "Quitter",
            de: "Beenden",
            zh: "退出",
            ja: "終了"
        )
    }

    // MARK: - Context Menu

    var menuRefreshAll: String {
        tr(
            en: "Refresh all",
            es: "Refrescar todo",
            pt: "Atualizar tudo",
            fr: "Tout actualiser",
            de: "Alles aktualisieren",
            zh: "全部刷新",
            ja: "すべて更新"
        )
    }

    func menuOpenProvider(_ name: String) -> String {
        tr(
            en: "Open \(name)",
            es: "Abrir \(name)",
            pt: "Abrir \(name)",
            fr: "Ouvrir \(name)",
            de: "\(name) öffnen",
            zh: "打开 \(name)",
            ja: "\(name) を開く"
        )
    }

    var menuSettings: String {
        tr(
            en: "Settings...",
            es: "Ajustes...",
            pt: "Ajustes...",
            fr: "Réglages...",
            de: "Einstellungen...",
            zh: "设置...",
            ja: "設定..."
        )
    }

    // MARK: - Quota Groups & Windows

    var thirdPartyGroupTitle: String {
        tr(
            en: "3P Models (Claude / GPT)",
            es: "Modelos 3P (Claude / GPT)",
            pt: "Modelos 3P (Claude / GPT)",
            fr: "Modèles 3P (Claude / GPT)",
            de: "3P-Modelle (Claude / GPT)",
            zh: "第三方模型 (Claude / GPT)",
            ja: "3Pモデル (Claude / GPT)"
        )
    }

    func groupDisplayName(groupKey: String?, fallback: String) -> String {
        switch groupKey {
        case "gemini":
            return "Gemini"
        case "third_party":
            return thirdPartyGroupTitle
        case "codex":
            return "Codex"
        case "claude":
            return "Claude Code"
        default:
            if fallback.contains("3P") {
                return thirdPartyGroupTitle
            }
            return fallback
        }
    }

    func bucketLabel(for bucket: QuotaBucket) -> String {
        switch bucket.windowKind {
        case "5h":
            return tr(
                en: "5-hour window",
                es: "Ventana 5 horas",
                pt: "Janela de 5 horas",
                fr: "Fenêtre 5 heures",
                de: "5-Stunden-Fenster",
                zh: "5 小时窗口",
                ja: "5時間枠"
            )
        case "weekly":
            return tr(
                en: "Weekly limit",
                es: "Límite semanal",
                pt: "Limite semanal",
                fr: "Limite hebdomadaire",
                de: "Wochenlimit",
                zh: "每周限额",
                ja: "週間制限"
            )
        case "monthly":
            return tr(
                en: "Monthly limit",
                es: "Límite mensual",
                pt: "Limite mensal",
                fr: "Limite mensuelle",
                de: "Monatslimit",
                zh: "每月限额",
                ja: "月間制限"
            )
        case "spend":
            return tr(
                en: "Spend limit",
                es: "Límite de gasto",
                pt: "Limite de gastos",
                fr: "Limite de dépense",
                de: "Ausgabenlimit",
                zh: "消费限额",
                ja: "利用上限"
            )
        case "days":
            let d = bucket.windowAmount ?? 1
            return tr(
                en: "\(d)d window",
                es: "Ventana \(d)d",
                pt: "Janela \(d)d",
                fr: "Fenêtre \(d)j",
                de: "\(d)T-Fenster",
                zh: "\(d) 天窗口",
                ja: "\(d)日間枠"
            )
        case "hours":
            let h = bucket.windowAmount ?? 1
            return tr(
                en: "\(h)h window",
                es: "Ventana \(h)h",
                pt: "Janela \(h)h",
                fr: "Fenêtre \(h)h",
                de: "\(h)h-Fenster",
                zh: "\(h) 小时窗口",
                ja: "\(h)時間枠"
            )
        case "generic":
            return tr(
                en: "Window",
                es: "Ventana",
                pt: "Janela",
                fr: "Fenêtre",
                de: "Fenster",
                zh: "限额窗口",
                ja: "利用枠"
            )
        default:
            return bucket.label
        }
    }

    // MARK: - Session Details

    func sessionDetail(key: String?, arg: String?, fallback: String) -> String {
        switch key {
        case "session_start":
            return tr(
                en: "Starting session...",
                es: "Iniciando sesión...",
                pt: "Iniciando sessão...",
                fr: "Démarrage de la session...",
                de: "Sitzung wird gestartet...",
                zh: "正在启动会话...",
                ja: "セッション開始中..."
            )
        case "thinking":
            return tr(
                en: "Thinking...",
                es: "Pensando...",
                pt: "Pensando...",
                fr: "Réflexion...",
                de: "Denkt nach...",
                zh: "思考中...",
                ja: "思考中..."
            )
        case "waiting_permission":
            return tr(
                en: "Waiting for permission",
                es: "Esperando permiso",
                pt: "Aguardando permissão",
                fr: "En attente d'autorisation",
                de: "Wartet auf Erlaubnis",
                zh: "等待权限确认",
                ja: "許可待ち"
            )
        case "waiting_elicitation":
            return tr(
                en: "Waiting for confirmation",
                es: "Esperando confirmación",
                pt: "Aguardando confirmação",
                fr: "En attente de confirmation",
                de: "Wartet auf Bestätigung",
                zh: "等待确认",
                ja: "確認待ち"
            )
        case "waiting_question":
            return tr(
                en: "Waiting for answer",
                es: "Esperando respuesta",
                pt: "Aguardando resposta",
                fr: "En attente de réponse",
                de: "Wartet auf Antwort",
                zh: "等待回答",
                ja: "回答待ち"
            )
        case "waiting_approval":
            return tr(
                en: "Waiting for approval",
                es: "Esperando aprobación",
                pt: "Aguardando aprovação",
                fr: "En attente d'approbation",
                de: "Wartet auf Freigabe",
                zh: "等待批准",
                ja: "承認待ち"
            )
        case "waiting_plan_approval":
            return tr(
                en: "Waiting for plan approval",
                es: "Esperando aprobación del plan",
                pt: "Aguardando aprovação do plano",
                fr: "En attente d'approbation du plan",
                de: "Wartet auf Planfreigabe",
                zh: "等待计划批准",
                ja: "プラン承認待ち"
            )
        case "preparing_plan":
            return tr(
                en: "Preparing plan...",
                es: "Preparando plan...",
                pt: "Preparando plano...",
                fr: "Préparation du plan...",
                de: "Plan wird vorbereitet...",
                zh: "正在准备计划...",
                ja: "プラン準備中..."
            )
        case "running_tool":
            let tool = arg ?? ""
            if tool.isEmpty {
                return sessionDetail(key: "running_tool_generic", arg: nil, fallback: fallback)
            }
            return tr(
                en: "Running \(tool)",
                es: "Ejecutando \(tool)",
                pt: "Executando \(tool)",
                fr: "Exécution de \(tool)",
                de: "Führt \(tool) aus",
                zh: "正在运行 \(tool)",
                ja: "\(tool) を実行中"
            )
        case "running_tool_generic":
            return tr(
                en: "Running tool",
                es: "Ejecutando herramienta",
                pt: "Executando ferramenta",
                fr: "Exécution de l'outil",
                de: "Führt Tool aus",
                zh: "正在运行工具",
                ja: "ツールを実行中"
            )
        case "processing_answer":
            return tr(
                en: "Processing response...",
                es: "Procesando respuesta...",
                pt: "Processando resposta...",
                fr: "Traitement de la réponse...",
                de: "Antwort wird verarbeitet...",
                zh: "正在处理回复...",
                ja: "応答を処理中..."
            )
        case "analyzing_result":
            return tr(
                en: "Analyzing result...",
                es: "Analizando resultado...",
                pt: "Analisando resultado...",
                fr: "Analyse du résultat...",
                de: "Ergebnis wird analysiert...",
                zh: "正在分析结果...",
                ja: "結果を分析中..."
            )
        case "background_tasks":
            return tr(
                en: "Background tasks running...",
                es: "Tareas en segundo plano...",
                pt: "Tarefas em segundo plano...",
                fr: "Tâches en arrière-plan...",
                de: "Hintergrundaufgaben laufen...",
                zh: "后台任务运行中...",
                ja: "バックグラウンド処理中..."
            )
        case "idle":
            return statusTitle(.idle)
        default:
            return fallback
        }
    }

    // MARK: - Notifications

    func waitingNotificationTitle(provider: AgentProvider) -> String {
        tr(
            en: "\(provider.displayName) is waiting for your input",
            es: "\(provider.displayName) espera tu respuesta",
            pt: "\(provider.displayName) aguarda sua resposta",
            fr: "\(provider.displayName) attend votre réponse",
            de: "\(provider.displayName) wartet auf deine Antwort",
            zh: "\(provider.displayName) 正在等待你的回复",
            ja: "\(provider.displayName) が応答を待っています"
        )
    }

    func lowQuotaNotificationTitle(provider: AgentProvider) -> String {
        tr(
            en: "Low quota on \(provider.displayName)",
            es: "Cuota baja en \(provider.displayName)",
            pt: "Cota baixa em \(provider.displayName)",
            fr: "Quota faible sur \(provider.displayName)",
            de: "Niedriges Limit bei \(provider.displayName)",
            zh: "\(provider.displayName) 配额不足",
            ja: "\(provider.displayName) のクォータ残量低下"
        )
    }

    func lowQuotaNotificationBody(prefix: String, percent: Int, countdown: String) -> String {
        tr(
            en: "\(prefix): \(percent)% left (resets in \(countdown))",
            es: "\(prefix): \(percent)% restante (resetea en \(countdown))",
            pt: "\(prefix): \(percent)% restante (reinicia em \(countdown))",
            fr: "\(prefix) : \(percent)% restant (réinitialisation dans \(countdown))",
            de: "\(prefix): \(percent)% übrig (Reset in \(countdown))",
            zh: "\(prefix)：剩余 \(percent)%（\(countdown) 后重置）",
            ja: "\(prefix): 残り \(percent)%（\(countdown) 後にリセット）"
        )
    }

    // MARK: - Time & Countdowns

    var resetDoneLabel: String {
        tr(
            en: "Reset",
            es: "Reseteado",
            pt: "Reiniciado",
            fr: "Réinitialisé",
            de: "Zurückgesetzt",
            zh: "已重置",
            ja: "リセット済み"
        )
    }

    func resetsInText(_ countdown: String) -> String {
        if countdown == resetDoneLabel {
            return resetDoneLabel
        }
        return tr(
            en: "Resets in \(countdown)",
            es: "Resetea en \(countdown)",
            pt: "Reinicia em \(countdown)",
            fr: "Réinitialise dans \(countdown)",
            de: "Reset in \(countdown)",
            zh: "\(countdown) 后重置",
            ja: "\(countdown) 後にリセット"
        )
    }

    func formatCountdown(to targetDate: Date?, fallbackSeconds: Int, fetchedDate: Date?, now: Date) -> String {
        let remaining: TimeInterval
        if let target = targetDate {
            remaining = target.timeIntervalSince(now)
        } else if let fetched = fetchedDate {
            remaining = TimeInterval(fallbackSeconds) - now.timeIntervalSince(fetched)
        } else {
            remaining = TimeInterval(fallbackSeconds)
        }

        if remaining <= 0 {
            return resetDoneLabel
        }

        let totalSec = Int(remaining)
        let days = totalSec / 86400
        let hours = (totalSec % 86400) / 3600
        let minutes = (totalSec % 3600) / 60
        let seconds = totalSec % 60

        switch code {
        case "fr":
            if days > 0 { return "\(days)j \(hours)h" }
            if hours > 0 { return "\(hours)h \(minutes)m" }
            if minutes > 0 { return "\(minutes)m \(seconds)s" }
            return "< 1m"
        case "de":
            if days > 0 { return "\(days)T \(hours)Std" }
            if hours > 0 { return "\(hours)Std \(minutes)Min" }
            if minutes > 0 { return "\(minutes)Min \(seconds)Sek" }
            return "< 1Min"
        case "zh-Hans":
            if days > 0 { return "\(days)天\(hours)小时" }
            if hours > 0 { return "\(hours)小时\(minutes)分" }
            if minutes > 0 { return "\(minutes)分\(seconds)秒" }
            return "< 1分钟"
        case "ja":
            if days > 0 { return "\(days)日\(hours)時間" }
            if hours > 0 { return "\(hours)時間\(minutes)分" }
            if minutes > 0 { return "\(minutes)分\(seconds)秒" }
            return "1分未満"
        default:
            if days > 0 { return "\(days)d \(hours)h" }
            if hours > 0 { return "\(hours)h \(minutes)m" }
            if minutes > 0 { return "\(minutes)m \(seconds)s" }
            return "< 1m"
        }
    }

    func formatResetClock(date: Date?, isWeekly: Bool) -> String {
        guard let date = date else { return "" }
        let df = DateFormatter()
        df.locale = locale
        df.timeZone = TimeZone.current
        if !isWeekly {
            df.dateFormat = "HH:mm"
            return df.string(from: date)
        }
        switch code {
        case "zh-Hans":
            df.dateFormat = "M/d EEE HH:mm"
            return df.string(from: date)
        case "ja":
            df.dateFormat = "M/d(E) HH:mm"
            return df.string(from: date)
        case "en":
            df.dateFormat = "EEE, MMM d, HH:mm"
            return df.string(from: date)
        default:
            df.dateFormat = "EEE d MMM, HH:mm"
            let s = df.string(from: date)
            return s.prefix(1).uppercased() + s.dropFirst()
        }
    }

    func formatElapsed(since epoch: TimeInterval, now: Date) -> String {
        let delta = max(0, Int(now.timeIntervalSince1970 - epoch))
        let unitValue: String
        if delta < 60 {
            unitValue = "\(delta)\(secondUnit)"
        } else if delta < 3600 {
            unitValue = "\(delta / 60)\(minuteUnit)"
        } else if delta < 86400 {
            unitValue = "\(delta / 3600)\(hourUnit)"
        } else {
            unitValue = "\(delta / 86400)\(dayUnit)"
        }
        return tr(
            en: "\(unitValue) ago",
            es: "hace \(unitValue)",
            pt: "há \(unitValue)",
            fr: "il y a \(unitValue)",
            de: "vor \(unitValue)",
            zh: "\(unitValue)前",
            ja: "\(unitValue)前"
        )
    }

    private var secondUnit: String {
        switch code {
        case "de": return "s"
        case "zh-Hans": return "秒"
        case "ja": return "秒"
        default: return "s"
        }
    }

    private var minuteUnit: String {
        switch code {
        case "zh-Hans": return "分钟"
        case "ja": return "分"
        default: return "m"
        }
    }

    private var hourUnit: String {
        switch code {
        case "zh-Hans": return "小时"
        case "ja": return "時間"
        default: return "h"
        }
    }

    private var dayUnit: String {
        switch code {
        case "fr": return "j"
        case "de": return "T"
        case "zh-Hans": return "天"
        case "ja": return "日"
        default: return "d"
        }
    }
}
