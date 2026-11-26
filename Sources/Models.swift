import AppKit
import Foundation
import SwiftUI

enum AgentProvider: String, Codable, CaseIterable, Identifiable {
    case antigravity
    case codex
    case claude
    case copilot

    var id: String { rawValue }

    var shortTag: String {
        switch self {
        case .antigravity: return "AG"
        case .codex: return "CX"
        case .claude: return "CC"
        case .copilot: return "CP"
        }
    }

    var displayName: String {
        switch self {
        case .antigravity: return "Antigravity"
        case .codex: return "ChatGPT (Codex)"
        case .claude: return "Claude Code"
        case .copilot: return "GitHub Copilot"
        }
    }

    var bundleId: String {
        switch self {
        case .antigravity: return "com.google.antigravity"
        case .codex: return "com.openai.codex"
        case .claude: return "com.anthropic.claudefordesktop"
        case .copilot: return "com.github.githubapp"
        }
    }

    var appPath: String {
        switch self {
        case .antigravity: return "/Applications/Antigravity.app"
        case .codex: return "/Applications/ChatGPT.app"
        case .claude: return "/Applications/Claude.app"
        case .copilot: return "/Applications/GitHub Copilot.app"
        }
    }

    var supportsBackgroundPoll: Bool {
        switch self {
        case .antigravity, .codex, .copilot: return true
        case .claude: return false
        }
    }

    static func sortedCanonical(_ list: [AgentProvider]) -> [AgentProvider] {
        let set = Set(list)
        return allCases.filter { set.contains($0) }
    }
}

enum AgentStatus: String, Codable, CaseIterable {
    case waiting
    case active
    case idle

    var priority: Int {
        switch self {
        case .waiting: return 3
        case .active: return 2
        case .idle: return 1
        }
    }

    var swiftUIColor: Color {
        switch self {
        case .waiting: return Color(red: 1.0, green: 0.78, blue: 0.0)
        case .active: return Color(red: 1.0, green: 0.23, blue: 0.19)
        case .idle: return Color(red: 0.20, green: 0.78, blue: 0.35)
        }
    }

    var nsColor: NSColor {
        switch self {
        case .waiting: return NSColor(srgbRed: 1.0, green: 0.80, blue: 0.0, alpha: 1.0)
        case .active: return NSColor(srgbRed: 1.0, green: 0.231, blue: 0.188, alpha: 1.0)
        case .idle: return NSColor(srgbRed: 0.204, green: 0.780, blue: 0.349, alpha: 1.0)
        }
    }
}

struct SessionState: Codable, Identifiable, Equatable {
    var id: String
    var provider: AgentProvider
    var sessionId: String
    var status: AgentStatus
    var detail: String
    var detailKey: String?
    var detailArg: String?
    var waitingReason: String
    var pendingFeedback: Bool
    var modelName: String
    var workspace: String
    var updatedAt: TimeInterval
    var statusChangedAt: TimeInterval

    var shortModelName: String {
        guard !modelName.isEmpty else { return "" }
        return modelName
            .replacingOccurrences(of: "-", with: " ")
            .split(separator: " ")
            .map { part in
                let s = String(part)
                let lower = s.lowercased()
                if lower == "gpt" || lower == "oss" {
                    return s.uppercased()
                }
                if lower == "xhigh" {
                    return "XHigh"
                }
                return s.prefix(1).uppercased() + s.dropFirst()
            }
            .joined(separator: " ")
    }
}

struct MonitorStateFile: Codable {
    var updatedAt: TimeInterval?
    var lastTurnCompletedByProvider: [String: TimeInterval]?
    var sessions: [String: SessionState]?
}

struct QuotaBucket: Codable, Identifiable, Equatable {
    var id: String
    var group: String
    var groupKey: String?
    var label: String
    var windowKind: String?
    var windowAmount: Int?
    var isWeekly: Bool
    var remainingFraction: Double
    var resetTime: String
    var resetInSeconds: Int
    var disabled: Bool?
    var usedRequests: Int?
    var entitlementRequests: Int?

    var remainingPercent: Int {
        let pct = Int((remainingFraction * 100.0).rounded())
        return max(0, min(100, pct))
    }

    var isLow: Bool {
        remainingPercent < 20
    }

    var barColor: Color {
        if remainingPercent < 20 {
            return Color(red: 1.0, green: 0.23, blue: 0.19)
        } else if remainingPercent <= 50 {
            return Color(red: 1.0, green: 0.62, blue: 0.04)
        } else {
            return Color(red: 0.20, green: 0.78, blue: 0.35)
        }
    }

    var resetDate: Date? {
        guard !resetTime.isEmpty else { return nil }
        if let d = DateFormatting.isoWithFractional.date(from: resetTime) {
            return d
        }
        return DateFormatting.isoBasic.date(from: resetTime)
    }
}

struct QuotaSnapshot: Codable, Equatable {
    var provider: AgentProvider
    var fetchedAt: String
    var planType: String
    var buckets: [QuotaBucket]

    var activeBuckets: [QuotaBucket] {
        buckets.filter { $0.disabled != true }
    }

    func lowestPercent(inGroupKey targetKey: String? = nil) -> Int? {
        let filtered = activeBuckets.filter { bucket in
            guard let targetKey = targetKey else { return true }
            if let gk = bucket.groupKey {
                return gk == targetKey
            }
            if targetKey == AntigravityQuotaGroupKey.thirdParty {
                return bucket.group.contains("3P") || bucket.id.contains("3p")
            }
            return !bucket.group.contains("3P") && !bucket.id.contains("3p")
        }
        return filtered.map { $0.remainingPercent }.min()
    }
}

struct UserPreferences: Codable, Equatable {
    var enabledProviders: [AgentProvider]
    var hasCompletedOnboarding: Bool
    var language: AppLanguage?
    var showAntigravity3PModels: Bool?
}

struct ProviderHookStatus: Codable, Equatable {
    var hooksInstalled: Bool
    var binaryFound: Bool
    var appInstalled: Bool
}

enum AntigravityQuotaGroupKey {
    static let gemini = "gemini"
    static let thirdParty = "third_party"

    static func from(modelName: String) -> String {
        let lower = modelName.lowercased()
        let markers = ["claude", "gpt", "o1", "o3", "o4", "3p", "opus", "sonnet", "haiku"]
        if markers.contains(where: { lower.contains($0) }) {
            return thirdParty
        }
        return gemini
    }
}

enum DateFormatting {
    static let isoWithFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    static let isoBasic: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()
}
