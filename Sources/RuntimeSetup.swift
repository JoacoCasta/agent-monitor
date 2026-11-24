import Foundation

enum RuntimeSetup {
    private static let scriptNames = [
        "hook-handler.py",
        "fetch-quota.py",
        "claude-statusline.py",
        "configure-hooks.py",
    ]

    static var monitorDirectoryPath: String {
        NSString(string: "~/.gemini/agent-monitor").expandingTildeInPath
    }

    static func ensureRuntimeScriptsInstalled() {
        let fm = FileManager.default
        let destDir = monitorDirectoryPath
        try? fm.createDirectory(atPath: destDir, withIntermediateDirectories: true)

        guard let bundledScriptsDir = Bundle.main.resourceURL?.appendingPathComponent("Scripts").path,
              fm.fileExists(atPath: bundledScriptsDir)
        else {
            return
        }

        for name in scriptNames {
            let src = (bundledScriptsDir as NSString).appendingPathComponent(name)
            let dst = (destDir as NSString).appendingPathComponent(name)
            guard fm.fileExists(atPath: src),
                  let srcData = try? Data(contentsOf: URL(fileURLWithPath: src))
            else {
                continue
            }

            let needsCopy: Bool
            if fm.fileExists(atPath: dst),
               let dstData = try? Data(contentsOf: URL(fileURLWithPath: dst))
            {
                needsCopy = srcData != dstData
            } else {
                needsCopy = true
            }

            if needsCopy {
                let tmp = (destDir as NSString).appendingPathComponent(".\(name).tmp")
                do {
                    try srcData.write(to: URL(fileURLWithPath: tmp), options: .atomic)
                    try fm.setAttributes([.posixPermissions: 0o755], ofItemAtPath: tmp)
                    if fm.fileExists(atPath: dst) {
                        _ = try fm.replaceItemAt(URL(fileURLWithPath: dst), withItemAt: URL(fileURLWithPath: tmp))
                    } else {
                        try fm.moveItem(atPath: tmp, toPath: dst)
                    }
                    try? fm.setAttributes([.posixPermissions: 0o755], ofItemAtPath: dst)
                } catch {
                    try? fm.removeItem(atPath: tmp)
                }
            }
        }
    }
}

enum LaunchAtLoginManager {
    private static let label = "com.agentmonitor.app"

    private static var plistPath: String {
        NSString(string: "~/Library/LaunchAgents/\(label).plist").expandingTildeInPath
    }

    static func isEnabled() -> Bool {
        FileManager.default.fileExists(atPath: plistPath)
    }

    static func setEnabled(_ enabled: Bool) {
        let fm = FileManager.default
        let uid = getuid()

        if !enabled {
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: "/bin/launchctl")
            proc.arguments = ["bootout", "gui/\(uid)", plistPath]
            proc.standardOutput = Pipe()
            proc.standardError = Pipe()
            try? proc.run()
            proc.waitUntilExit()
            try? fm.removeItem(atPath: plistPath)
            return
        }

        let launchAgentsDir = (plistPath as NSString).deletingLastPathComponent
        try? fm.createDirectory(atPath: launchAgentsDir, withIntermediateDirectories: true)

        let home = fm.homeDirectoryForCurrentUser.path
        let exePath = Bundle.main.executablePath ?? "/Applications/AgentMonitor.app/Contents/MacOS/AgentMonitor"
        let logPath = (RuntimeSetup.monitorDirectoryPath as NSString).appendingPathComponent("app.log")
        let pathEnv = "\(home)/.gemini/bin:\(home)/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

        let plistDict: [String: Any] = [
            "Label": label,
            "ProgramArguments": [exePath],
            "EnvironmentVariables": [
                "HOME": home,
                "PATH": pathEnv,
            ],
            "RunAtLoad": true,
            "KeepAlive": false,
            "StandardOutPath": logPath,
            "StandardErrorPath": logPath,
        ]

        if let data = try? PropertyListSerialization.data(fromPropertyList: plistDict, format: .xml, options: 0) {
            try? data.write(to: URL(fileURLWithPath: plistPath), options: .atomic)
        }
    }
}
