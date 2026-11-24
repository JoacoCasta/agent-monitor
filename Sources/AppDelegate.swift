import AppKit
import Combine
import SwiftUI
import UserNotifications

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate {
    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var hostingController: NSHostingController<PopoverView>!
    private var store: StateStore!
    private var cancellables: Set<AnyCancellable> = []

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
        popover.contentViewController = hostingController
        syncPopoverSize()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.target = self
            button.action = #selector(handleStatusItemClick(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }

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
        if popover.contentSize != targetSize {
            popover.contentSize = targetSize
        }
        hostingController.view.frame = NSRect(origin: .zero, size: targetSize)
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
            .combineLatest(store.$hasCompletedOnboarding)
            .receive(on: RunLoop.main)
            .sink { [weak self] _, _ in
                self?.syncPopoverSize()
            }
            .store(in: &cancellables)
    }

    private func updateStatusItemAppearance() {
        guard let button = statusItem.button else { return }

        let t = store.l10n
        let result = NSMutableAttributedString()
        let tagFont = NSFont.systemFont(ofSize: 11.5, weight: .semibold)
        let pctFont = NSFont.monospacedDigitSystemFont(ofSize: 12.0, weight: .medium)
        let dotDiameter: CGFloat = 8.0
        let dotYOffset = floor((pctFont.capHeight - dotDiameter) / 2.0)
        var tooltipParts: [String] = []

        for (index, provider) in store.enabledProviders.enumerated() {
            if index > 0 {
                result.append(
                    NSAttributedString(
                        string: "  ",
                        attributes: [.font: pctFont]
                    )
                )
            }

            let status = store.status(for: provider)
            let pct = store.menuBarPercent(for: provider)
            let isLow = store.isMenuBarLow(for: provider)

            result.append(
                NSAttributedString(
                    string: "\(provider.shortTag) ",
                    attributes: [
                        .font: tagFont,
                        .foregroundColor: NSColor.secondaryLabelColor,
                    ]
                )
            )

            let attachment = NSTextAttachment()
            attachment.image = makeStatusDotImage(color: status.nsColor, size: dotDiameter)
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

    private func makeStatusDotImage(color: NSColor, size dotSize: CGFloat) -> NSImage {
        let size = NSSize(width: dotSize, height: dotSize)
        let image = NSImage(size: size, flipped: false) { rect in
            let dotRect = rect.insetBy(dx: 0.5, dy: 0.5)
            let path = NSBezierPath(ovalIn: dotRect)
            color.setFill()
            path.fill()

            NSColor.black.withAlphaComponent(0.22).setStroke()
            path.lineWidth = 0.75
            path.stroke()
            return true
        }
        image.isTemplate = false
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
