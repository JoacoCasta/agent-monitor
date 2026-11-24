import SwiftUI

struct PopoverView: View {
    @ObservedObject var store: StateStore
    var onFocusProvider: (AgentProvider) -> Void
    var onQuit: () -> Void

    private var t: L10n { store.l10n }

    private var readableGreen: Color {
        Color(
            nsColor: NSColor(name: nil) { appearance in
                let isDark = appearance.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
                return isDark
                    ? NSColor.systemGreen
                    : NSColor(srgbRed: 0.08, green: 0.50, blue: 0.20, alpha: 1.0)
            }
        )
    }

    var body: some View {
        Group {
            if !store.hasCompletedOnboarding {
                onboardingView
            } else if store.showingSettings {
                settingsView
            } else {
                dashboardView
            }
        }
        .frame(width: 380)
        .frame(maxHeight: .infinity, alignment: .top)
        .background(Color(nsColor: .windowBackgroundColor).opacity(0.86))
    }

    // MARK: - Onboarding View

    private var onboardingView: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Text(t.chooseAgentsTitle)
                    .font(.system(size: 14, weight: .semibold))
                    .lineLimit(1)

                Spacer()

                Picker(
                    "",
                    selection: Binding(
                        get: { store.appLanguage },
                        set: { store.setLanguage($0) }
                    )
                ) {
                    ForEach(AppLanguage.allCases) { lang in
                        Text(lang.pickerLabel(systemAutoLabel: t.systemAutoLabel))
                            .tag(lang)
                    }
                }
                .labelsHidden()
                .pickerStyle(.menu)
                .controlSize(.small)
                .fixedSize()
                .help(t.languageLabel)
            }
            .padding(.horizontal, 18)
            .padding(.top, 2)
            .frame(height: 46)

            Divider()

            ScrollView(.vertical, showsIndicators: true) {
                VStack(alignment: .leading, spacing: 10) {
                    Text(t.chooseAgentsSubtitle)
                        .font(.system(size: 11.5))
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)

                    VStack(spacing: 8) {
                        ForEach(AgentProvider.allCases) { provider in
                            let isSelected = store.onboardingSelection.contains(provider)
                            let status = store.hookStatuses[provider]
                            let isDetected = (status?.binaryFound == true) || (status?.appInstalled == true)

                            Button(action: {
                                store.toggleOnboardingProvider(provider)
                            }) {
                                HStack(spacing: 10) {
                                    Image(systemName: isSelected ? "checkmark.square.fill" : "square")
                                        .font(.system(size: 15))
                                        .foregroundStyle(isSelected ? Color.accentColor : .secondary)

                                    VStack(alignment: .leading, spacing: 2) {
                                        HStack(spacing: 6) {
                                            Text(provider.displayName)
                                                .font(.system(size: 12.5, weight: .semibold))
                                                .foregroundStyle(.primary)
                                            if isDetected {
                                                Text(t.detectedBadge)
                                                    .font(.system(size: 9.5, weight: .semibold))
                                                    .padding(.horizontal, 5)
                                                    .padding(.vertical, 1.5)
                                                    .background(Capsule().fill(Color.green.opacity(0.16)))
                                                    .foregroundStyle(readableGreen)
                                            }
                                        }

                                        Text(t.onboardingSubtitle(for: provider))
                                            .font(.system(size: 10.5))
                                            .foregroundStyle(.secondary)
                                            .fixedSize(horizontal: false, vertical: true)
                                    }

                                    Spacer(minLength: 4)

                                    ProviderLogoView(provider: provider, size: 15)
                                        .foregroundStyle(.primary)
                                        .frame(width: 28, height: 28)
                                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.primary.opacity(0.06)))
                                }
                                .padding(10)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(
                                    RoundedRectangle(cornerRadius: 10)
                                        .fill(Color.primary.opacity(isSelected ? 0.06 : 0.03))
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 10)
                                                .strokeBorder(
                                                    isSelected ? Color.accentColor.opacity(0.35) : Color.primary.opacity(0.08),
                                                    lineWidth: 1
                                                )
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    VStack(alignment: .leading, spacing: 3) {
                        Text(t.codexTrustHint)
                        Text(t.claudeStatusLineHint)
                    }
                    .font(.system(size: 10.5))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            HStack {
                Button(t.quit) {
                    onQuit()
                }
                .buttonStyle(.plain)
                .font(.system(size: 11.5))
                .foregroundStyle(.secondary)

                Spacer()

                Button(t.getStarted) {
                    store.completeOnboarding(selected: Array(store.onboardingSelection))
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.regular)
                .disabled(store.onboardingSelection.isEmpty)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 2)
            .frame(height: 44)
        }
    }

    // MARK: - Settings View

    private var settingsView: some View {
        VStack(spacing: 0) {
            HStack {
                Button(action: { store.showingSettings = false }) {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 11, weight: .semibold))
                        Text(t.back)
                            .font(.system(size: 12, weight: .medium))
                    }
                }
                .buttonStyle(.borderless)

                Spacer()

                Text(t.settingsTitle)
                    .font(.system(size: 13.5, weight: .semibold))

                Spacer()

                if store.isSyncingHooks {
                    ProgressView()
                        .controlSize(.small)
                        .frame(width: 48, alignment: .trailing)
                } else {
                    Button(t.done) {
                        store.showingSettings = false
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
            .padding(.horizontal, 18)
            .padding(.top, 2)
            .frame(height: 46)

            Divider()

            ScrollView(.vertical, showsIndicators: true) {
                VStack(alignment: .leading, spacing: 10) {
                    // Language card
                    HStack(spacing: 8) {
                        Label(t.languageLabel, systemImage: "globe")
                            .font(.system(size: 12, weight: .medium))
                        Spacer()
                        Picker(
                            "",
                            selection: Binding(
                                get: { store.appLanguage },
                                set: { store.setLanguage($0) }
                            )
                        ) {
                            ForEach(AppLanguage.allCases) { lang in
                                Text(lang.pickerLabel(systemAutoLabel: t.systemAutoLabel))
                                    .tag(lang)
                            }
                        }
                        .labelsHidden()
                        .pickerStyle(.menu)
                        .controlSize(.small)
                        .fixedSize()
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.primary.opacity(0.045))
                    )

                    // Start at login card
                    HStack(spacing: 8) {
                        Label(t.launchAtLogin, systemImage: "power")
                            .font(.system(size: 12, weight: .medium))
                        Spacer()
                        Toggle(
                            "",
                            isOn: Binding(
                                get: { store.launchAtLogin },
                                set: { store.setLaunchAtLogin($0) }
                            )
                        )
                        .labelsHidden()
                        .toggleStyle(.switch)
                        .controlSize(.small)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill(Color.primary.opacity(0.045))
                    )

                    Text(t.activeAgentsHeader)
                        .font(.system(size: 11.5, weight: .semibold))
                        .foregroundStyle(.secondary)
                        .padding(.top, 2)

                    VStack(spacing: 8) {
                        ForEach(AgentProvider.allCases) { provider in
                            let isEnabled = store.enabledProviders.contains(provider)
                            let isOnlyOne = isEnabled && store.enabledProviders.count <= 1
                            let hookInfo = store.hookStatuses[provider]

                            VStack(spacing: 8) {
                                HStack(spacing: 10) {
                                    VStack(alignment: .leading, spacing: 3) {
                                        HStack(spacing: 6) {
                                            ProviderLogoView(provider: provider, size: 14)
                                                .foregroundStyle(.primary)
                                            Text(provider.displayName)
                                                .font(.system(size: 12.5, weight: .semibold))
                                        }

                                        HStack(spacing: 6) {
                                            if let info = hookInfo {
                                                Circle()
                                                    .fill(info.hooksInstalled ? readableGreen : Color.secondary.opacity(0.45))
                                                    .frame(width: 6, height: 6)
                                                Text(info.hooksInstalled ? t.hooksActive : t.hooksDisabled)
                                                    .font(.system(size: 10.5))
                                                    .foregroundStyle(info.hooksInstalled ? readableGreen : .secondary)

                                                if !info.binaryFound && !info.appInstalled {
                                                    Text(t.notDetected)
                                                        .font(.system(size: 10.5))
                                                        .foregroundStyle(.orange)
                                                }
                                            } else {
                                                Text(t.checkingStatus)
                                                    .font(.system(size: 10.5))
                                                    .foregroundStyle(.secondary)
                                            }
                                        }
                                    }

                                    Spacer()

                                    Toggle(
                                        "",
                                        isOn: Binding(
                                            get: { isEnabled },
                                            set: { newValue in
                                                store.setProvider(provider, enabled: newValue)
                                            }
                                        )
                                    )
                                    .labelsHidden()
                                    .toggleStyle(.switch)
                                    .controlSize(.small)
                                    .disabled(isOnlyOne)
                                }

                                if provider == .antigravity && isEnabled {
                                    Divider()

                                    HStack(spacing: 8) {
                                        Text(t.showThirdPartyModels)
                                            .font(.system(size: 11))
                                            .foregroundStyle(.secondary)

                                        Spacer()

                                        Toggle(
                                            "",
                                            isOn: Binding(
                                                get: { store.showAntigravity3PModels },
                                                set: { store.setShowAntigravity3PModels($0) }
                                            )
                                        )
                                        .labelsHidden()
                                        .toggleStyle(.switch)
                                        .controlSize(.mini)
                                    }
                                    .padding(.leading, 20)
                                }
                            }
                            .padding(10)
                            .background(
                                RoundedRectangle(cornerRadius: 10)
                                    .fill(Color.primary.opacity(0.045))
                            )
                        }
                    }

                    Text(t.hooksAutoNote)
                        .font(.system(size: 10.5))
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            HStack {
                Button(action: { store.resyncHooks() }) {
                    Label(t.resyncHooks, systemImage: "arrow.triangle.2.circlepath")
                        .font(.system(size: 11))
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .disabled(store.isSyncingHooks)

                Spacer()

                Button(t.clearStates) {
                    store.clearAllSessions()
                }
                .buttonStyle(.plain)
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 2)
            .frame(height: 44)
        }
    }

    // MARK: - Dashboard View

    private var dashboardView: some View {
        VStack(spacing: 0) {
            HStack(spacing: 8) {
                Text(t.appTitle)
                    .font(.system(size: 13.5, weight: .semibold))

                Spacer()

                Button(action: { store.refreshAllEnabledQuotas(force: true) }) {
                    if store.isFetchingAnyQuota {
                        ProgressView()
                            .controlSize(.small)
                            .frame(width: 24, height: 24)
                    } else {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12, weight: .medium))
                            .frame(width: 24, height: 24)
                    }
                }
                .buttonStyle(.borderless)
                .help(t.refreshAllHelp)

                Button(action: {
                    store.refreshHookStatuses()
                    store.showingSettings = true
                }) {
                    Image(systemName: "gearshape")
                        .font(.system(size: 12.5, weight: .medium))
                        .frame(width: 24, height: 24)
                }
                .buttonStyle(.borderless)
                .help(t.settingsHelp)
            }
            .padding(.horizontal, 18)
            .padding(.top, 2)
            .frame(height: 46)

            Divider()

            ScrollView(.vertical, showsIndicators: true) {
                VStack(spacing: 10) {
                    ForEach(store.enabledProviders) { provider in
                        ProviderCardView(
                            provider: provider,
                            status: store.status(for: provider),
                            sessions: store.nonIdleSessions(for: provider),
                            snapshot: store.quotasByProvider[provider],
                            isFetching: store.fetchingProviders.contains(provider),
                            errorMessage: store.quotaErrors[provider],
                            activeAntigravityGroupKey: store.activeAntigravityGroupKey,
                            showThirdPartyModels: store.showAntigravity3PModels,
                            now: store.now,
                            t: t,
                            onFocus: { onFocusProvider(provider) },
                            onRefresh: { store.refreshQuota(for: provider, force: true) },
                            onDismissSession: { id in store.dismissSession(id: id) }
                        )
                    }
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            HStack {
                if store.isFetchingAnyQuota {
                    Text(t.updatingQuotas)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                } else if let updated = store.latestQuotaUpdate {
                    Text(t.updatedText(t.formatElapsed(since: updated.timeIntervalSince1970, now: store.now)))
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                } else {
                    Text(t.ready)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button(t.settingsTitle) {
                    store.refreshHookStatuses()
                    store.showingSettings = true
                }
                .buttonStyle(.plain)
                .font(.system(size: 11.5))
                .foregroundStyle(.secondary)

                Button(t.quit) {
                    onQuit()
                }
                .buttonStyle(.plain)
                .font(.system(size: 11.5))
                .foregroundStyle(.secondary)
                .padding(.leading, 8)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 2)
            .frame(height: 44)
        }
    }
}

// MARK: - Provider Card

private struct ProviderCardView: View {
    let provider: AgentProvider
    let status: AgentStatus
    let sessions: [SessionState]
    let snapshot: QuotaSnapshot?
    let isFetching: Bool
    let errorMessage: String?
    let activeAntigravityGroupKey: String
    let showThirdPartyModels: Bool
    let now: Date
    let t: L10n
    let onFocus: () -> Void
    let onRefresh: () -> Void
    let onDismissSession: (String) -> Void

    private var fetchedDate: Date? {
        guard let str = snapshot?.fetchedAt else { return nil }
        return DateFormatting.isoBasic.date(from: str)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 9) {
            HStack(spacing: 8) {
                ZStack {
                    if status != .idle {
                        Circle()
                            .fill(status.swiftUIColor.opacity(0.28))
                            .frame(width: 18, height: 18)
                    }
                    Circle()
                        .fill(status.swiftUIColor)
                        .frame(width: 10, height: 10)
                        .overlay(
                            Circle()
                                .strokeBorder(Color.primary.opacity(0.15), lineWidth: 0.75)
                        )
                }
                .frame(width: 18, height: 18)

                VStack(alignment: .leading, spacing: 1) {
                    HStack(spacing: 6) {
                        ProviderLogoView(provider: provider, size: 14)
                            .foregroundStyle(.primary)
                        Text(provider.displayName)
                            .font(.system(size: 12.5, weight: .semibold))

                        if let plan = snapshot?.planType, !plan.isEmpty {
                            Text(plan)
                                .font(.system(size: 9.5, weight: .semibold))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(Capsule().fill(Color.primary.opacity(0.08)))
                                .foregroundStyle(.secondary)
                        }
                    }

                    Text(t.statusTitle(status))
                        .font(.system(size: 10.5))
                        .foregroundStyle(status == .waiting ? Color.orange : .secondary)
                }

                Spacer()

                HStack(spacing: 4) {
                    if provider.supportsBackgroundPoll {
                        Button(action: onRefresh) {
                            if isFetching {
                                ProgressView()
                                    .controlSize(.mini)
                                    .frame(width: 20, height: 20)
                            } else {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 10.5, weight: .medium))
                                    .frame(width: 20, height: 20)
                            }
                        }
                        .buttonStyle(.borderless)
                        .disabled(isFetching)
                        .help(t.refreshProviderHelp(provider.displayName))
                    }

                    Button(action: onFocus) {
                        HStack(spacing: 3) {
                            Image(systemName: "macwindow")
                                .font(.system(size: 10.5))
                            Text(t.openButton)
                                .font(.system(size: 10.5, weight: .medium))
                        }
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(RoundedRectangle(cornerRadius: 5).fill(Color.primary.opacity(0.07)))
                    }
                    .buttonStyle(.plain)
                    .help(t.openProviderHelp(provider.displayName))
                }
            }

            if !sessions.isEmpty {
                VStack(spacing: 5) {
                    ForEach(sessions) { session in
                        SessionRowView(
                            session: session,
                            now: now,
                            t: t,
                            onDismiss: { onDismissSession(session.id) }
                        )
                    }
                }
            }

            if let errorMessage = errorMessage {
                HStack(spacing: 5) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 10))
                        .foregroundStyle(.orange)
                    Text(errorMessage)
                        .font(.system(size: 10.5))
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
                .padding(6)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 6).fill(Color.orange.opacity(0.10)))
            }

            if let snapshot = snapshot {
                let buckets = snapshot.activeBuckets
                if buckets.isEmpty {
                    Text(t.noQuotasReported)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                } else if provider == .antigravity {
                    antigravityGroupsView(buckets: buckets)
                } else {
                    VStack(spacing: 8) {
                        ForEach(buckets) { bucket in
                            QuotaRowView(
                                bucket: bucket,
                                fetchedDate: fetchedDate,
                                now: now,
                                t: t
                            )
                        }
                    }
                }
            } else if provider == .claude {
                Text(t.waitingClaudeSession)
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            } else if isFetching {
                HStack(spacing: 6) {
                    ProgressView()
                        .controlSize(.small)
                    Text(t.fetchingQuotas)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .padding(11)
        .background(
            RoundedRectangle(cornerRadius: 11)
                .fill(Color.primary.opacity(0.045))
                .overlay(
                    RoundedRectangle(cornerRadius: 11)
                        .strokeBorder(
                            status == .waiting
                                ? Color.yellow.opacity(0.45)
                                : Color.primary.opacity(0.08),
                            lineWidth: 1
                        )
                )
        )
    }

    @ViewBuilder
    private func antigravityGroupsView(buckets: [QuotaBucket]) -> some View {
        let geminiBuckets = buckets.filter {
            ($0.groupKey == AntigravityQuotaGroupKey.gemini)
                || ($0.groupKey == nil && !$0.group.contains("3P") && !$0.id.contains("3p"))
        }
        let thirdPartyBuckets = buckets.filter {
            ($0.groupKey == AntigravityQuotaGroupKey.thirdParty)
                || ($0.groupKey == nil && ($0.group.contains("3P") || $0.id.contains("3p")))
        }

        VStack(alignment: .leading, spacing: 8) {
            if !geminiBuckets.isEmpty {
                subGroupBlock(
                    title: "Gemini",
                    isActiveGroup: showThirdPartyModels && (activeAntigravityGroupKey == AntigravityQuotaGroupKey.gemini),
                    buckets: geminiBuckets
                )
            }
            if showThirdPartyModels && !thirdPartyBuckets.isEmpty {
                subGroupBlock(
                    title: t.thirdPartyGroupTitle,
                    isActiveGroup: activeAntigravityGroupKey == AntigravityQuotaGroupKey.thirdParty,
                    buckets: thirdPartyBuckets
                )
            }
        }
    }

    private func subGroupBlock(title: String, isActiveGroup: Bool, buckets: [QuotaBucket]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                if isActiveGroup {
                    Text(t.inUseBadge)
                        .font(.system(size: 9.5, weight: .semibold))
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1.5)
                        .background(Capsule().fill(Color.accentColor.opacity(0.15)))
                        .foregroundStyle(Color.accentColor)
                }
            }

            ForEach(buckets) { bucket in
                QuotaRowView(bucket: bucket, fetchedDate: fetchedDate, now: now, t: t)
            }
        }
        .padding(8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.primary.opacity(0.035))
        )
    }
}

private struct SessionRowView: View {
    let session: SessionState
    let now: Date
    let t: L10n
    let onDismiss: () -> Void

    var body: some View {
        let ws = session.workspace.isEmpty ? t.noWorkspace : session.workspace
        let detailText = t.sessionDetail(
            key: session.detailKey,
            arg: session.detailArg,
            fallback: session.detail
        )

        HStack(alignment: .top, spacing: 7) {
            Circle()
                .fill(session.status.swiftUIColor)
                .frame(width: 7, height: 7)
                .padding(.top, 4)

            VStack(alignment: .leading, spacing: 1.5) {
                HStack(spacing: 4) {
                    Text(ws)
                        .font(.system(size: 11.5, weight: .semibold))
                        .lineLimit(1)

                    if !session.shortModelName.isEmpty {
                        Text("· \(session.shortModelName)")
                            .font(.system(size: 10.5))
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }

                HStack(spacing: 4) {
                    Text(detailText)
                        .font(.system(size: 10.5))
                        .foregroundStyle(session.status == .waiting ? Color.orange : .secondary)
                        .lineLimit(1)

                    Text("· \(t.formatElapsed(since: session.updatedAt, now: now))")
                        .font(.system(size: 10))
                        .foregroundStyle(.tertiary)
                }
            }

            Spacer(minLength: 4)

            Button(action: onDismiss) {
                Image(systemName: "xmark")
                    .font(.system(size: 9, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .frame(width: 16, height: 16)
            }
            .buttonStyle(.borderless)
            .help(t.dismissSessionHelp)
        }
        .padding(.horizontal, 7)
        .padding(.vertical, 5)
        .background(
            RoundedRectangle(cornerRadius: 7)
                .fill(Color.primary.opacity(0.05))
        )
    }
}

private struct QuotaRowView: View {
    let bucket: QuotaBucket
    let fetchedDate: Date?
    let now: Date
    let t: L10n

    var body: some View {
        let pct = bucket.remainingPercent
        let countdown = t.formatCountdown(
            to: bucket.resetDate,
            fallbackSeconds: bucket.resetInSeconds,
            fetchedDate: fetchedDate,
            now: now
        )
        let resetClock = t.formatResetClock(date: bucket.resetDate, isWeekly: bucket.isWeekly)

        VStack(alignment: .leading, spacing: 3.5) {
            HStack {
                Text(t.bucketLabel(for: bucket))
                    .font(.system(size: 11))
                    .foregroundStyle(.primary)

                Spacer()

                HStack(spacing: 3.5) {
                    if bucket.isLow {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 9.5))
                            .foregroundStyle(.red)
                    }
                    Text("\(pct)%")
                        .font(.system(size: 11.5, weight: .semibold).monospacedDigit())
                        .foregroundStyle(bucket.isLow ? Color.red : .primary)
                }
            }

            GeometryReader { geo in
                let totalWidth = max(0, geo.size.width)
                let clampedFrac = CGFloat(max(0, min(1, bucket.remainingFraction)))
                let fillWidth: CGFloat = pct == 0 ? 0 : min(totalWidth, max(4, totalWidth * clampedFrac))

                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.primary.opacity(0.10))
                    if fillWidth > 0 {
                        Capsule()
                            .fill(bucket.barColor)
                            .frame(width: fillWidth)
                    }
                }
            }
            .frame(height: 5.5)

            HStack(spacing: 4) {
                Text(t.resetsInText(countdown))
                    .font(.system(size: 10).monospacedDigit())
                    .foregroundStyle(.secondary)
                if !resetClock.isEmpty && countdown != t.resetDoneLabel {
                    Text("· \(resetClock)")
                        .font(.system(size: 10))
                        .foregroundStyle(.tertiary)
                }
                Spacer()
            }
        }
    }
}
