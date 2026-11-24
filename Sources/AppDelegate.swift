import AppKit
import Combine
import SwiftUI
import UserNotifications

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate, NSPopoverDelegate {
    private struct StatusBarRenderItem: Equatable {
        let provider: AgentProvider
        let status: AgentStatus
        let percent: Int?
        let isLow: Bool
    }

    private struct StatusBarRenderKey: Equatable {
        let items: [StatusBarRenderItem]
        let language: AppLanguage
        let isDarkMenuBar: Bool
    }

    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var hostingController: NSHostingController<PopoverView>!
    private var store: StateStore!
    private var cancellables: Set<AnyCancellable> = []
    private var lastStatusBarKey: StatusBarRenderKey?
    private var statusDotCache: [AgentStatus: NSImage] = [:]

    deinit {
        DistributedNotificationCenter.default().removeObserver(self)
        NSWorkspace.shared.notificationCenter.removeObserver(self)
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        if Bundle.main.bundleIdentifier != nil {
            let center = UNUserNotificationCenter.current()
            center.delegate = self
            center.requestAuthorization(options: [.alert, .sound]) { _, _ in }
        }

        store = StateStore()

        let popoverView = PopoverView(
            store: store,
            onFocusProvider: { [weak self] provider in
                self?.focusProvider(provider)
            },
            onQuit: {
                NSApp.terminate(nil)
            }
        )

        hostingController = NSHostingController(rootView: popoverView)
        if #available(macOS 13.0, *) {
            hostingController.sizingOptions = []
        }

        popover = NSPopover()
        popover.behavior = .transient
        popover.animates = false
        popover.delegate = self
        popover.contentViewController = hostingController
        syncPopoverSize()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.autosaveName = "AgentMonitorStatusItem"
        if let button = statusItem.button {
            button.target = self
            button.action = #selector(handleStatusItemClick(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }

        DistributedNotificationCenter.default().addObserver(
            self,
            selector: #selector(handleAppearanceOrSpaceChange),
            name: NSNotification.Name("AppleInterfaceThemeChangedNotification"),
            object: nil
        )
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(handleAppearanceOrSpaceChange),
            name: NSWorkspace.activeSpaceDidChangeNotification,
            object: nil
        )

        bindStoreToStatusBar()
        updateStatusItemAppearance()

        if !store.hasCompletedOnboarding {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { [weak self] in
                guard let self = self, !self.popover.isShown else { return }
                self.openPopover()
            }
        }
    }

    private func syncPopoverSize() {
        let targetSize = NSSize(width: 380, height: store.preferredPopoverHeight)
        if hostingController.preferredContentSize != targetSize {
            hostingController.preferredContentSize = targetSize
        }
        if popover.contentSize != targetSize {
            popover.contentSize = targetSize
        }
    }

    private func bindStoreToStatusBar() {
        store.$enabledProviders
            .combineLatest(store.$statusByProvider, store.$quotasByProvider, store.$sessionsByProvider)
            .combineLatest(store.$appLanguage)
            .receive(on: RunLoop.main)
            .sink { [weak self] _, _ in
                self?.updateStatusItemAppearance()
                self?.syncPopoverSize()
            }
            .store(in: &cancellables)

        store.$showingSettings
            .combineLatest(store.$hasCompletedOnboarding, store.$showAntigravity3PModels)
            .receive(on: RunLoop.main)
            .sink { [weak self] _, _, _ in
                self?.updateStatusItemAppearance()
                self?.syncPopoverSize()
            }
            .store(in: &cancellables)
    }

    @objc private func handleAppearanceOrSpaceChange() {
        updateStatusItemAppearance()
    }

    func popoverWillShow(_ notification: Notification) {
        store.setPopoverVisible(true)
        updateStatusItemAppearance()
    }

    func popoverDidClose(_ notification: Notification) {
        store.setPopoverVisible(false)
    }

    private func updateStatusItemAppearance() {
        guard let button = statusItem.button else { return }

        let match = button.effectiveAppearance.bestMatch(from: [.darkAqua, .vibrantDark, .aqua, .vibrantLight])
        let isDarkMenuBar = (match == .darkAqua || match == .vibrantDark)

        let renderItems = store.enabledProviders.map { provider in
            StatusBarRenderItem(
                provider: provider,
                status: store.status(for: provider),
                percent: store.menuBarPercent(for: provider),
                isLow: store.isMenuBarLow(for: provider)
            )
        }
        let renderKey = StatusBarRenderKey(
            items: renderItems,
            language: store.appLanguage,
            isDarkMenuBar: isDarkMenuBar
        )
        if renderKey == lastStatusBarKey {
            return
        }
        lastStatusBarKey = renderKey

        let t = store.l10n
        let result = NSMutableAttributedString()
        let pctFont = NSFont.monospacedDigitSystemFont(ofSize: 12.0, weight: .medium)
        let logoSize: CGFloat = 14.5
        let logoYOffset = round((pctFont.capHeight - logoSize) / 2.0)
        let dotDiameter: CGFloat = 8.5
        let dotYOffset = round((pctFont.capHeight - dotDiameter) / 2.0)
        var tooltipParts: [String] = []

        for (index, item) in renderItems.enumerated() {
            let provider = item.provider
            if index > 0 {
                result.append(
                    NSAttributedString(
                        string: "   ",
                        attributes: [.font: pctFont]
                    )
                )
            }

            let status = item.status
            let pct = item.percent
            let isLow = item.isLow

            let logoAttachment = NSTextAttachment()
            logoAttachment.image = ProviderLogoRenderer.menuBarImage(
                for: provider,
                size: logoSize,
                isDark: isDarkMenuBar
            )
            logoAttachment.bounds = NSRect(x: 0, y: logoYOffset, width: logoSize, height: logoSize)
            result.append(NSAttributedString(attachment: logoAttachment))

            result.append(
                NSAttributedString(
                    string: "\u{2009}",
                    attributes: [.font: pctFont]
                )
            )

            let attachment = NSTextAttachment()
            attachment.image = statusDotImage(for: status, size: dotDiameter)
            attachment.bounds = NSRect(x: 0, y: dotYOffset, width: dotDiameter, height: dotDiameter)
            result.append(NSAttributedString(attachment: attachment))

            let pctText = pct.map { " \($0)%" } ?? " --"
            let pctColor: NSColor = isLow ? .systemRed : .labelColor
            result.append(
                NSAttributedString(
                    string: pctText,
                    attributes: [
                        .font: pctFont,
                        .foregroundColor: pctColor,
                    ]
                )
            )

            let tipPct = pct.map { "\($0)%" } ?? "--"
            tooltipParts.append("\(provider.displayName): \(t.statusTitle(status)) (\(tipPct))")
        }

        button.image = nil
        button.attributedTitle = result
        button.toolTip = tooltipParts.joined(separator: "\n")
    }

    private func statusDotImage(for status: AgentStatus, size dotSize: CGFloat) -> NSImage {
        if let cached = statusDotCache[status] {
            return cached
        }
        let scale: CGFloat = 2.0
        let pixelSize = max(2, Int((dotSize * scale).rounded()))
        guard let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: pixelSize,
            pixelsHigh: pixelSize,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .deviceRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ) else {
            return NSImage(size: NSSize(width: dotSize, height: dotSize))
        }

        // Set point size BEFORE creating NSGraphicsContext so the CTM uses 2x Retina scale
        rep.size = NSSize(width: dotSize, height: dotSize)
        guard let nsCtx = NSGraphicsContext(bitmapImageRep: rep) else {
            return NSImage(size: NSSize(width: dotSize, height: dotSize))
        }
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = nsCtx
        let dotRect = NSRect(origin: .zero, size: NSSize(width: dotSize, height: dotSize)).insetBy(dx: 0.5, dy: 0.5)
        let path = NSBezierPath(ovalIn: dotRect)
        status.nsColor.setFill()
        path.fill()
        NSColor.black.withAlphaComponent(0.22).setStroke()
        path.lineWidth = 0.75
        path.stroke()
        NSGraphicsContext.restoreGraphicsState()

        let image = NSImage(size: NSSize(width: dotSize, height: dotSize))
        image.addRepresentation(rep)
        image.isTemplate = false
        statusDotCache[status] = image
        return image
    }

    @objc private func handleStatusItemClick(_ sender: AnyObject?) {
        guard let event = NSApp.currentEvent else {
            togglePopover()
            return
        }

        if event.type == .rightMouseUp || event.modifierFlags.contains(.control) {
            showContextMenu()
        } else {
            togglePopover()
        }
    }

    private func togglePopover() {
        if popover.isShown {
            popover.performClose(nil)
        } else {
            openPopover()
        }
    }

    private func openPopover() {
        guard let button = statusItem.button else { return }
        syncPopoverSize()
        NSApp.activate(ignoringOtherApps: true)
        popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        popover.contentViewController?.view.window?.makeKey()
    }

    private func showContextMenu() {
        if popover.isShown {
            popover.performClose(nil)
        }
        let t = store.l10n
        let menu = NSMenu()

        let refreshItem = NSMenuItem(
            title: t.menuRefreshAll,
            action: #selector(menuRefreshAll),
            keyEquivalent: "r"
        )
        refreshItem.target = self
        menu.addItem(refreshItem)

        for provider in store.enabledProviders {
            let item = NSMenuItem(
                title: t.menuOpenProvider(provider.displayName),
                action: #selector(menuOpenProvider(_:)),
                keyEquivalent: ""
            )
            item.target = self
            item.representedObject = provider.rawValue
            menu.addItem(item)
        }

        menu.addItem(NSMenuItem.separator())

        let settingsItem = NSMenuItem(
            title: t.menuSettings,
            action: #selector(menuOpenSettings),
            keyEquivalent: ","
        )
        settingsItem.target = self
        menu.addItem(settingsItem)

        let clearItem = NSMenuItem(
            title: t.clearStates,
            action: #selector(menuClearSessions),
            keyEquivalent: ""
        )
        clearItem.target = self
        menu.addItem(clearItem)

        menu.addItem(NSMenuItem.separator())

        let quitItem = NSMenuItem(title: t.quit, action: #selector(menuQuit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem.menu = menu
        statusItem.button?.performClick(nil)
        statusItem.menu = nil
    }

    @objc private func menuRefreshAll() {
        store.refreshAllEnabledQuotas(force: true)
    }

    @objc private func menuOpenProvider(_ sender: NSMenuItem) {
        guard let raw = sender.representedObject as? String,
              let provider = AgentProvider(rawValue: raw)
        else { return }
        focusProvider(provider)
    }

    @objc private func menuOpenSettings() {
        if store.hasCompletedOnboarding {
            store.refreshHookStatuses()
            store.showingSettings = true
        }
        openPopover()
    }

    @objc private func menuClearSessions() {
        store.clearAllSessions()
    }

    @objc private func menuQuit() {
        NSApp.terminate(nil)
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !popover.isShown {
            openPopover()
        }
        return true
    }

    func focusProvider(_ provider: AgentProvider) {
        if popover.isShown {
            popover.performClose(nil)
        }
        if let app = NSRunningApplication.runningApplications(withBundleIdentifier: provider.bundleId).first {
            app.activate(options: [.activateAllWindows])
            return
        }
        let appURL = URL(fileURLWithPath: provider.appPath)
        if FileManager.default.fileExists(atPath: appURL.path) {
            let config = NSWorkspace.OpenConfiguration()
            config.activates = true
            NSWorkspace.shared.openApplication(at: appURL, configuration: config, completionHandler: nil)
            return
        }
        if let term = NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.Terminal").first {
            term.activate(options: [.activateAllWindows])
        }
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let rawProvider = response.notification.request.content.userInfo["provider"] as? String
        Task { @MainActor [weak self] in
            if let raw = rawProvider, let prov = AgentProvider(rawValue: raw) {
                self?.focusProvider(prov)
            } else if let first = self?.store.enabledProviders.first {
                self?.focusProvider(first)
            }
        }
        completionHandler()
    }
}
