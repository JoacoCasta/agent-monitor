import SwiftUI

struct PopoverView: View {
    @ObservedObject var store: StateStore
    var onFocusProvider: (AgentProvider) -> Void
    var onQuit: () -> Void

    private var t: L10n { store.l10n }

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
        .frame(width: 372)
    }

    // MARK: - Onboarding View

    private var onboardingView: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                HStack(alignment: .center, spacing: 8) {
                    Text(t.chooseAgentsTitle)
                        .font(.system(size: 15, weight: .semibold))

                    Spacer()

                    Menu {
                        ForEach(AppLanguage.allCases) { lang in
                            Button(action: { store.setLanguage(lang) }) {
                                if store.appLanguage == lang {
                                    Label(
                                        lang.pickerLabel(systemAutoLabel: t.systemAutoLabel),
                                        systemImage: "checkmark"
                                    )
                                } else {
                                    Text(lang.pickerLabel(systemAutoLabel: t.systemAutoLabel))
                                }
                            }
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "globe")
                                .font(.system(size: 11))
                            Text(store.appLanguage.resolvedCode.uppercased())
                                .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                        }
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.primary.opacity(0.06)))
                    }
                    .menuStyle(.borderlessButton)
                    .fixedSize()
                    .help(t.languageLabel)
                }

                Text(t.chooseAgentsSubtitle)
                    .font(.system(size: 11.5))
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            VStack(spacing: 8) {
                ForEach(AgentProvider.allCases) { provider in
                    let isSelected = store.onboardingSelection.contains(provider)
                    let status = store.hookStatuses[provider]
                    let isDetected = (status?.binaryFound == true) || (status?.appInstalled == true)

                    HStack(spacing: 10) {
                        Toggle(
                            "",
                            isOn: Binding(
                                get: { isSelected },
                                set: { newVal in
                                    store.toggleOnboardingProvider(provider, selected: newVal)
                                }
                            )
                        )
                        .labelsHidden()
                        .toggleStyle(.checkbox)

                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(provider.displayName)
                                    .font(.system(size: 12.5, weight: .semibold))
                                if isDetected {
                                    Text(t.detectedBadge)
                                        .font(.system(size: 9.5, weight: .semibold))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 1.5)
                                        .background(Capsule().fill(Color.green.opacity(0.16)))
                                        .foregroundStyle(.green)
                                }
                            }

                            Text(t.onboardingSubtitle(for: provider))
                                .font(.system(size: 10.5))
                                .foregroundStyle(.secondary)
                        }

                        Spacer()

                        Text(provider.shortTag)
                            .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background(RoundedRectangle(cornerRadius: 5).fill(Color.primary.opacity(0.06)))
                    }
                    .padding(10)
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
                    .contentShape(Rectangle())
                    .onTapGesture {
                        store.toggleOnboardingProvider(provider)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(t.codexTrustHint)
                Text(t.claudeStatusLineHint)
            }
            .font(.system(size: 10.5))
            .foregroundStyle(.secondary)

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
        }
        .padding(14)
    }

    // MARK: - Settings View

    private var settingsView: some View {
        VStack(alignment: .leading, spacing: 12) {
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
                } else {
                    Button(t.done) {
                        store.showingSettings = false
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }

            Divider()

            HStack {
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
                .frame(maxWidth: 185)
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

            VStack(spacing: 8) {
                ForEach(AgentProvider.allCases) { provider in
                    let isEnabled = store.enabledProviders.contains(provider)
                    let isOnlyOne = isEnabled && store.enabledProviders.count <= 1
                    let hookInfo = store.hookStatuses[provider]

                    HStack(spacing: 10) {
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(spacing: 6) {
                                Text(provider.displayName)
                                    .font(.system(size: 12.5, weight: .semibold))
                                Text(provider.shortTag)
                                    .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                    .foregroundStyle(.secondary)
                                    .padding(.horizontal, 4)
                                    .padding(.vertical, 1)
                                    .background(RoundedRectangle(cornerRadius: 4).fill(Color.primary.opacity(0.06)))
                            }

                            HStack(spacing: 6) {
                                if let info = hookInfo {
                                    Circle()
                                        .fill(info.hooksInstalled ? Color.green : Color.secondary.opacity(0.45))
                                        .frame(width: 6, height: 6)
                                    Text(info.hooksInstalled ? t.hooksActive : t.hooksDisabled)
                                        .font(.system(size: 10.5))
                                        .foregroundStyle(info.hooksInstalled ? .green : .secondary)

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
        }
        .padding(14)
    }

    // MARK: - Dashboard View

    private var dashboardView: some View {
        VStack(alignment: .leading, spacing: 10) {
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
            .padding(.horizontal, 14)
            .padding(.top, 12)

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
                            now: store.now,
                            t: t,
                            onFocus: { onFocusProvider(provider) },
                            onRefresh: { store.refreshQuota(for: provider, force: true) },
                            onDismissSession: { id in store.dismissSession(id: id) }
                        )
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 4)
            }
            .frame(maxHeight: 540)

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
            .padding(.horizontal, 14)
            .padding(.bottom, 12)
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
                    isActiveGroup: activeAntigravityGroupKey == AntigravityQuotaGroupKey.gemini,
                    buckets: geminiBuckets
                )
            }
            if !thirdPartyBuckets.isEmpty {
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
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.primary.opacity(0.10))
                    Capsule()
                        .fill(bucket.barColor)
                        .frame(
                            width: max(
                                4,
                                geo.size.width * CGFloat(max(0, min(1, bucket.remainingFraction)))
                            )
                        )
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
