import Combine
import Foundation
import UserNotifications

@MainActor
final class StateStore: ObservableObject {
    @Published private(set) var enabledProviders: [AgentProvider] = AgentProvider.allCases
    @Published private(set) var hasCompletedOnboarding: Bool = false
    @Published var appLanguage: AppLanguage = .system
    @Published var launchAtLogin: Bool = LaunchAtLoginManager.isEnabled()
    @Published var showingSettings: Bool = false
    @Published var onboardingSelection: Set<AgentProvider> = Set(AgentProvider.allCases)

    var l10n: L10n {
        L10n(language: appLanguage)
    }

    var preferredPopoverHeight: CGFloat {
        if !hasCompletedOnboarding {
            return 480
        }
        if showingSettings {
            return 522
        }
        var bodyHeight: CGFloat = 20
        for provider in enabledProviders {
            let sessionCount = nonIdleSessions(for: provider).count
            let sessionHeight = CGFloat(sessionCount) * 48
            if provider == .antigravity {
                bodyHeight += 250 + sessionHeight
            } else {
                bodyHeight += 145 + sessionHeight
            }
        }
        if enabledProviders.count > 1 {
            bodyHeight += CGFloat(enabledProviders.count - 1) * 10
        }
        let total = 46 + 44 + bodyHeight
        return min(588, max(288, total))
    }

    @Published private(set) var sessionsByProvider: [AgentProvider: [SessionState]] = [:]
    @Published private(set) var statusByProvider: [AgentProvider: AgentStatus] = [:]
    @Published private(set) var quotasByProvider: [AgentProvider: QuotaSnapshot] = [:]
    @Published private(set) var fetchingProviders: Set<AgentProvider> = []
    @Published private(set) var quotaErrors: [AgentProvider: String] = [:]
    @Published private(set) var lastUpdatedByProvider: [AgentProvider: Date] = [:]
    @Published private(set) var hookStatuses: [AgentProvider: ProviderHookStatus] = [:]
    @Published private(set) var isSyncingHooks: Bool = false
    @Published private(set) var now: Date = Date()

    var activeAntigravityGroupKey: String {
        let list = sessionsByProvider[.antigravity] ?? []
        let current = now
        let nonIdle = list.compactMap { s -> (SessionState, AgentStatus)? in
            let eff = effectiveStatus(for: s, at: current)
            return eff == .idle ? nil : (s, eff)
        }
        if let prioritized = nonIdle
            .filter({ !$0.0.modelName.isEmpty })
            .sorted(by: { lhs, rhs in
                if lhs.1.priority != rhs.1.priority {
                    return lhs.1.priority > rhs.1.priority
                }
                return lhs.0.updatedAt > rhs.0.updatedAt
            })
            .first
        {
            return AntigravityQuotaGroupKey.from(modelName: prioritized.0.modelName)
        }
        if let recentIdle = list
            .filter({ !$0.modelName.isEmpty && (current.timeIntervalSince1970 - $0.updatedAt) <= 600 })
            .sorted(by: { $0.updatedAt > $1.updatedAt })
            .first
        {
            return AntigravityQuotaGroupKey.from(modelName: recentIdle.modelName)
        }
        return AntigravityQuotaGroupKey.gemini
    }

    var isFetchingAnyQuota: Bool {
        !fetchingProviders.isEmpty
    }

    var latestQuotaUpdate: Date? {
        enabledProviders.compactMap { lastUpdatedByProvider[$0] }.max()
    }

    func status(for provider: AgentProvider) -> AgentStatus {
        statusByProvider[provider] ?? .idle
    }

    func nonIdleSessions(for provider: AgentProvider) -> [SessionState] {
        (sessionsByProvider[provider] ?? []).filter {
            effectiveStatus(for: $0, at: now) != .idle
        }
    }

    func menuBarPercent(for provider: AgentProvider) -> Int? {
        guard let snapshot = quotasByProvider[provider] else { return nil }
        if provider == .antigravity {
            return snapshot.lowestPercent(inGroupKey: activeAntigravityGroupKey)
        }
        return snapshot.lowestPercent()
    }

    func isMenuBarLow(for provider: AgentProvider) -> Bool {
        guard let pct = menuBarPercent(for: provider) else { return false }
        return pct < 20
    }

    private let monitorDirPath: String
    private let stateFilePath: String
    private let lockFilePath: String
    private let claudeQuotaPath: String
    private let preferencesPath: String
    private let runner = ProviderRunner()

    private var dirFD: Int32 = -1
    private var dirSource: DispatchSourceFileSystemObject?
    private var tickTimer: Timer?
    private var debounceItems: [AgentProvider: DispatchWorkItem] = [:]

    private var allSessions: [SessionState] = []
    private var lastSeenTurnByProvider: [AgentProvider: TimeInterval] = [:]
    private var lastRefreshAttemptByProvider: [AgentProvider: Date] = [:]
    private var notifiedWaitingKeys: Set<String> = []
    private var notifiedLowQuotaKeys: Set<String> = []
    private var hasEditedOnboardingSelection: Bool = false

    private let activeStaleTimeout: TimeInterval = 15 * 60
    private let waitingStaleTimeout: TimeInterval = 2 * 3600
    private let periodicQuotaInterval: TimeInterval = 300
    private let turnDebounceInterval: TimeInterval = 5

    init() {
        let dir = NSString(string: "~/.gemini/agent-monitor").expandingTildeInPath
        self.monitorDirPath = dir
        self.stateFilePath = (dir as NSString).appendingPathComponent("state.json")
        self.lockFilePath = (dir as NSString).appendingPathComponent("state.lock")
        self.claudeQuotaPath = (dir as NSString).appendingPathComponent("claude-quota.json")
        self.preferencesPath = (dir as NSString).appendingPathComponent("preferences.json")

        try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        RuntimeSetup.ensureRuntimeScriptsInstalled()

        loadPreferences()
        loadState(triggerTurnRefresh: false)
        loadClaudeQuotaIfAvailable()
        startDirectoryWatcher()
        startTimers()
        refreshHookStatuses()
        refreshAllEnabledQuotas(force: true)
    }

    deinit {
        dirSource?.cancel()
        tickTimer?.invalidate()
        for item in debounceItems.values {
            item.cancel()
        }
    }

    // MARK: - Preferences & Hooks

    func completeOnboarding(selected: [AgentProvider]) {
        let clean = AgentProvider.sortedCanonical(selected)
        let finalSelection = clean.isEmpty ? [.antigravity] : clean
        enabledProviders = finalSelection
        hasCompletedOnboarding = true
        savePreferences()
        syncHooksToEnabledProviders()
        pruneDisabledProviderData()
        refreshAllEnabledQuotas(force: true)
    }

    func setProvider(_ provider: AgentProvider, enabled: Bool) {
        var current = Set(enabledProviders)
        if enabled {
            current.insert(provider)
        } else {
            if current.count <= 1 && current.contains(provider) {
                return
            }
            current.remove(provider)
        }

        enabledProviders = AgentProvider.sortedCanonical(Array(current))
        savePreferences()

        isSyncingHooks = true
        let action = enabled ? "enable" : "disable"
        runner.configureHooks(arguments: [action, provider.rawValue]) { [weak self] result in
            guard let self = self else { return }
            self.isSyncingHooks = false
            if case .success(let map) = result {
                self.hookStatuses = map
            }
        }

        if enabled {
            if provider == .claude {
                loadClaudeQuotaIfAvailable()
            } else {
                refreshQuota(for: provider, force: true)
            }
        } else {
            pruneDisabledProviderData()
        }
    }

    func resyncHooks() {
        syncHooksToEnabledProviders()
    }

    func toggleOnboardingProvider(_ provider: AgentProvider, selected: Bool? = nil) {
        hasEditedOnboardingSelection = true
        let shouldSelect = selected ?? !onboardingSelection.contains(provider)
        if shouldSelect {
            onboardingSelection.insert(provider)
        } else if onboardingSelection.count > 1 {
            onboardingSelection.remove(provider)
        }
    }

    func refreshHookStatuses() {
        runner.configureHooks(arguments: ["status"]) { [weak self] result in
            guard let self = self else { return }
            if case .success(let map) = result {
                self.hookStatuses = map
                if !self.hasCompletedOnboarding && !self.hasEditedOnboardingSelection {
                    var detected: Set<AgentProvider> = []
                    for prov in AgentProvider.allCases {
                        if let st = map[prov], st.binaryFound || st.appInstalled {
                            detected.insert(prov)
                        }
                    }
                    if !detected.isEmpty {
                        self.onboardingSelection = detected
                    }
                }
            }
        }
    }

    private func syncHooksToEnabledProviders() {
        isSyncingHooks = true
        let joined = enabledProviders.map { $0.rawValue }.joined(separator: ",")
        runner.configureHooks(arguments: ["sync", joined]) { [weak self] result in
            guard let self = self else { return }
            self.isSyncingHooks = false
            if case .success(let map) = result {
                self.hookStatuses = map
            }
        }
    }

    func setLanguage(_ lang: AppLanguage) {
        appLanguage = lang
        savePreferences()
    }

    func setLaunchAtLogin(_ enabled: Bool) {
        LaunchAtLoginManager.setEnabled(enabled)
        launchAtLogin = LaunchAtLoginManager.isEnabled()
    }

    private func loadPreferences() {
        guard FileManager.default.fileExists(atPath: preferencesPath),
              let data = try? Data(contentsOf: URL(fileURLWithPath: preferencesPath)),
              let prefs = try? JSONDecoder().decode(UserPreferences.self, from: data)
        else {
            self.enabledProviders = AgentProvider.allCases
            self.hasCompletedOnboarding = false
            self.appLanguage = .system
            return
        }
        let sorted = AgentProvider.sortedCanonical(prefs.enabledProviders)
        self.enabledProviders = sorted.isEmpty ? [.antigravity] : sorted
        self.hasCompletedOnboarding = prefs.hasCompletedOnboarding
        self.appLanguage = prefs.language ?? .system
    }

    private func savePreferences() {
        let prefs = UserPreferences(
            enabledProviders: enabledProviders,
            hasCompletedOnboarding: hasCompletedOnboarding,
            language: appLanguage
        )
        guard let encoded = try? JSONEncoder().encode(prefs) else { return }
        let tmpPath = (monitorDirPath as NSString).appendingPathComponent(".prefs-\(UUID().uuidString).json")
        let tmpURL = URL(fileURLWithPath: tmpPath)
        let targetURL = URL(fileURLWithPath: preferencesPath)
        do {
            try encoded.write(to: tmpURL, options: .atomic)
            _ = try FileManager.default.replaceItemAt(targetURL, withItemAt: tmpURL)
        } catch {
            try? FileManager.default.removeItem(at: tmpURL)
        }
    }

    private func pruneDisabledProviderData() {
        let enabledSet = Set(enabledProviders)
        for prov in AgentProvider.allCases where !enabledSet.contains(prov) {
            quotaErrors.removeValue(forKey: prov)
            fetchingProviders.remove(prov)
        }
        recomputeDerivedState(referenceDate: now)
    }

    // MARK: - Quotas

    func refreshAllEnabledQuotas(force: Bool = false) {
        for provider in enabledProviders {
            if provider == .claude {
                loadClaudeQuotaIfAvailable()
            } else {
                refreshQuota(for: provider, force: force)
            }
        }
    }

    func refreshQuota(for provider: AgentProvider, force: Bool = false) {
        guard enabledProviders.contains(provider) else { return }
        if !provider.supportsBackgroundPoll {
            if provider == .claude {
                loadClaudeQuotaIfAvailable()
            }
            return
        }
        if fetchingProviders.contains(provider) { return }

        let current = Date()
        let lastAttempt = lastRefreshAttemptByProvider[provider] ?? .distantPast
        if !force && current.timeIntervalSince(lastAttempt) < turnDebounceInterval {
            return
        }

        lastRefreshAttemptByProvider[provider] = current
        fetchingProviders.insert(provider)

        runner.fetchQuota(provider: provider) { [weak self] result in
            guard let self = self else { return }
            self.fetchingProviders.remove(provider)
            switch result {
            case .success(let snapshot):
                self.quotasByProvider[provider] = snapshot
                self.lastUpdatedByProvider[provider] = Date()
                self.quotaErrors.removeValue(forKey: provider)
                self.checkLowQuotaNotifications(snapshot: snapshot)
            case .failure(let error):
                self.quotaErrors[provider] = error.localizedDescription
            }
        }
    }

    private func loadClaudeQuotaIfAvailable() {
        guard enabledProviders.contains(.claude),
              FileManager.default.fileExists(atPath: claudeQuotaPath),
              let data = try? Data(contentsOf: URL(fileURLWithPath: claudeQuotaPath)),
              let snapshot = try? JSONDecoder().decode(QuotaSnapshot.self, from: data)
        else {
            return
        }
        quotasByProvider[.claude] = snapshot
        if let fetched = DateFormatting.isoBasic.date(from: snapshot.fetchedAt) {
            lastUpdatedByProvider[.claude] = fetched
        } else {
            lastUpdatedByProvider[.claude] = Date()
        }
        quotaErrors.removeValue(forKey: .claude)
        checkLowQuotaNotifications(snapshot: snapshot)
    }

    // MARK: - Sessions

    func dismissSession(id: String) {
        mutateStateFile { state in
            var map = state.sessions ?? [:]
            map.removeValue(forKey: id)
            state.sessions = map
            state.updatedAt = Date().timeIntervalSince1970
        }
        loadState(triggerTurnRefresh: false)
    }

    func clearAllSessions() {
        mutateStateFile { state in
            state.sessions = [:]
            state.updatedAt = Date().timeIntervalSince1970
        }
        loadState(triggerTurnRefresh: false)
    }

    // MARK: - Watchers & Timers

    private func startDirectoryWatcher() {
        let fd = open(monitorDirPath, O_EVTONLY)
        guard fd >= 0 else { return }
        self.dirFD = fd

        let source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fd,
            eventMask: [.write, .rename, .extend, .attrib],
            queue: DispatchQueue.main
        )
        source.setEventHandler { [weak self] in
            self?.loadState(triggerTurnRefresh: true)
            self?.loadClaudeQuotaIfAvailable()
        }
        source.setCancelHandler { [weak self] in
            if let fd = self?.dirFD, fd >= 0 {
                close(fd)
                self?.dirFD = -1
            }
        }
        source.resume()
        self.dirSource = source
    }

    private func startTimers() {
        tickTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                let current = Date()
                self.now = current
                self.recomputeDerivedState(referenceDate: current)

                for provider in self.enabledProviders where provider.supportsBackgroundPoll {
                    let lastAttempt = self.lastRefreshAttemptByProvider[provider] ?? .distantPast
                    if current.timeIntervalSince(lastAttempt) >= self.periodicQuotaInterval {
                        self.refreshQuota(for: provider, force: true)
                    }
                }
            }
        }
        if let tickTimer = tickTimer {
            RunLoop.main.add(tickTimer, forMode: .common)
        }
    }

    private func loadState(triggerTurnRefresh: Bool) {
        guard FileManager.default.fileExists(atPath: stateFilePath),
              let data = try? Data(contentsOf: URL(fileURLWithPath: stateFilePath)),
              let decoded = try? JSONDecoder().decode(MonitorStateFile.self, from: data)
        else {
            self.allSessions = []
            recomputeDerivedState(referenceDate: Date())
            return
        }

        let rawSessions = Array((decoded.sessions ?? [:]).values)
        self.allSessions = rawSessions.sorted { lhs, rhs in
            if lhs.status.priority != rhs.status.priority {
                return lhs.status.priority > rhs.status.priority
            }
            return lhs.updatedAt > rhs.updatedAt
        }

        let current = Date()
        recomputeDerivedState(referenceDate: current)
        checkWaitingNotifications(referenceDate: current)

        if let turnMap = decoded.lastTurnCompletedByProvider {
            for (rawProv, turnTS) in turnMap {
                guard let prov = AgentProvider(rawValue: rawProv) else { continue }
                let prev = lastSeenTurnByProvider[prov] ?? 0
                if turnTS > prev {
                    lastSeenTurnByProvider[prov] = turnTS
                    if triggerTurnRefresh && prev > 0 && enabledProviders.contains(prov) && prov.supportsBackgroundPoll {
                        scheduleDebouncedQuotaRefresh(for: prov)
                    }
                }
            }
        }
    }

    private func scheduleDebouncedQuotaRefresh(for provider: AgentProvider) {
        debounceItems[provider]?.cancel()
        let item = DispatchWorkItem { [weak self] in
            self?.refreshQuota(for: provider, force: false)
        }
        debounceItems[provider] = item
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5, execute: item)
    }

    private func effectiveStatus(for session: SessionState, at date: Date) -> AgentStatus {
        let age = date.timeIntervalSince1970 - session.updatedAt
        switch session.status {
        case .active:
            return age > activeStaleTimeout ? .idle : .active
        case .waiting:
            return age > waitingStaleTimeout ? .idle : .waiting
        case .idle:
            return .idle
        }
    }

    private func recomputeDerivedState(referenceDate: Date) {
        var grouped: [AgentProvider: [SessionState]] = [:]
        var statuses: [AgentProvider: AgentStatus] = [:]

        for provider in AgentProvider.allCases {
            let list = allSessions.filter { $0.provider == provider }
            grouped[provider] = list
            var best: AgentStatus = .idle
            for s in list {
                let eff = effectiveStatus(for: s, at: referenceDate)
                if eff.priority > best.priority {
                    best = eff
                }
            }
            statuses[provider] = best
        }

        sessionsByProvider = grouped
        statusByProvider = statuses
    }

    // MARK: - Notifications

    private func checkWaitingNotifications(referenceDate: Date) {
        let t = l10n
        let enabledSet = Set(enabledProviders)
        for session in allSessions where enabledSet.contains(session.provider) {
            if effectiveStatus(for: session, at: referenceDate) == .waiting {
                let key = "\(session.id)|\(session.waitingReason)|\(Int(session.statusChangedAt))"
                if !notifiedWaitingKeys.contains(key) {
                    notifiedWaitingKeys.insert(key)
                    let ws = session.workspace.isEmpty ? t.noWorkspace : session.workspace
                    let detail = t.sessionDetail(key: session.detailKey, arg: session.detailArg, fallback: session.detail)
                    sendNotification(
                        identifier: "waiting-\(key)",
                        title: t.waitingNotificationTitle(provider: session.provider),
                        body: "\(ws) · \(detail)",
                        provider: session.provider
                    )
                }
            }
        }
    }

    private func checkLowQuotaNotifications(snapshot: QuotaSnapshot) {
        guard enabledProviders.contains(snapshot.provider) else { return }
        let t = l10n
        let fetchedDate = DateFormatting.isoBasic.date(from: snapshot.fetchedAt) ?? Date()

        for bucket in snapshot.activeBuckets where bucket.isLow {
            let key = "\(snapshot.provider.rawValue)|\(bucket.id)|\(bucket.resetTime)"
            if !notifiedLowQuotaKeys.contains(key) {
                notifiedLowQuotaKeys.insert(key)
                let countdown = t.formatCountdown(
                    to: bucket.resetDate,
                    fallbackSeconds: bucket.resetInSeconds,
                    fetchedDate: fetchedDate,
                    now: Date()
                )
                let groupTitle = t.groupDisplayName(groupKey: bucket.groupKey, fallback: bucket.group)
                let labelTitle = t.bucketLabel(for: bucket)
                let prefix = (groupTitle != snapshot.provider.displayName && groupTitle != "Codex")
                    ? "\(groupTitle) · \(labelTitle)"
                    : labelTitle
                sendNotification(
                    identifier: "lowquota-\(snapshot.provider.rawValue)-\(bucket.id)",
                    title: t.lowQuotaNotificationTitle(provider: snapshot.provider),
                    body: t.lowQuotaNotificationBody(
                        prefix: prefix,
                        percent: bucket.remainingPercent,
                        countdown: countdown
                    ),
                    provider: snapshot.provider
                )
            }
        }
    }

    private func sendNotification(
        identifier: String,
        title: String,
        body: String,
        provider: AgentProvider
    ) {
        guard Bundle.main.bundleIdentifier != nil else { return }
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.userInfo = ["provider": provider.rawValue]

        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request, withCompletionHandler: nil)
    }

    private func mutateStateFile(_ mutator: (inout MonitorStateFile) -> Void) {
        let lockFD = open(lockFilePath, O_CREAT | O_RDWR, 0o644)
        if lockFD >= 0 {
            flock(lockFD, LOCK_EX)
        }
        defer {
            if lockFD >= 0 {
                flock(lockFD, LOCK_UN)
                close(lockFD)
            }
        }

        var state = MonitorStateFile(
            updatedAt: nil,
            lastTurnCompletedByProvider: nil,
            sessions: [:]
        )
        if let data = try? Data(contentsOf: URL(fileURLWithPath: stateFilePath)),
           let decoded = try? JSONDecoder().decode(MonitorStateFile.self, from: data)
        {
            state = decoded
        }

        mutator(&state)

        if let encoded = try? JSONEncoder().encode(state) {
            let tmpPath = (monitorDirPath as NSString).appendingPathComponent(".state-swift-\(UUID().uuidString).json")
            let tmpURL = URL(fileURLWithPath: tmpPath)
            let targetURL = URL(fileURLWithPath: stateFilePath)
            do {
                try encoded.write(to: tmpURL, options: .atomic)
                _ = try FileManager.default.replaceItemAt(targetURL, withItemAt: tmpURL)
            } catch {
                try? FileManager.default.removeItem(at: tmpURL)
            }
        }
    }
}
