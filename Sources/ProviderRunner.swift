import Foundation

final class ProviderRunner {
    private let fetchQueue = DispatchQueue(
        label: "com.agentmonitor.app.fetch",
        qos: .utility,
        attributes: .concurrent
    )
    private let configQueue = DispatchQueue(
        label: "com.agentmonitor.app.hooks",
        qos: .userInitiated
    )

    private let lock = NSLock()
    private var inFlightFetches: Set<AgentProvider> = []

    private let fetchScriptPath: String = {
        NSString(string: "~/.gemini/agent-monitor/fetch-quota.py").expandingTildeInPath
    }()

    private let configureScriptPath: String = {
        NSString(string: "~/.gemini/agent-monitor/configure-hooks.py").expandingTildeInPath
    }()

    func fetchQuota(
        provider: AgentProvider,
        completion: @escaping (Result<QuotaSnapshot, Error>) -> Void
    ) {
        guard provider.supportsBackgroundPoll else { return }

        lock.lock()
        if inFlightFetches.contains(provider) {
            lock.unlock()
            return
        }
        inFlightFetches.insert(provider)
        lock.unlock()

        let script = fetchScriptPath
        fetchQueue.async { [weak self] in
            defer {
                if let self = self {
                    self.lock.lock()
                    self.inFlightFetches.remove(provider)
                    self.lock.unlock()
                }
            }

            let result = Self.runScript(
                scriptPath: script,
                arguments: ["--provider", provider.rawValue]
            )

            switch result {
            case .success(let data):
                do {
                    let snapshot = try JSONDecoder().decode(QuotaSnapshot.self, from: data)
                    DispatchQueue.main.async {
                        completion(.success(snapshot))
                    }
                } catch {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            case .failure(let error):
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
    }

    func configureHooks(
        arguments: [String],
        completion: @escaping (Result<[AgentProvider: ProviderHookStatus], Error>) -> Void
    ) {
        let script = configureScriptPath
        configQueue.async {
            let result = Self.runScript(scriptPath: script, arguments: arguments)
            switch result {
            case .success(let data):
                do {
                    let rawMap = try JSONDecoder().decode([String: ProviderHookStatus].self, from: data)
                    var typed: [AgentProvider: ProviderHookStatus] = [:]
                    for (k, v) in rawMap {
                        if let prov = AgentProvider(rawValue: k) {
                            typed[prov] = v
                        }
                    }
                    DispatchQueue.main.async {
                        completion(.success(typed))
                    }
                } catch {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            case .failure(let error):
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }
    }

    private static func runScript(scriptPath: String, arguments: [String]) -> Result<Data, Error> {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = [scriptPath] + arguments

        let home = FileManager.default.homeDirectoryForCurrentUser.path
        var env = ProcessInfo.processInfo.environment
        env["HOME"] = home
        env["PATH"] = "\(home)/.gemini/bin:\(home)/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        process.environment = env

        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = errPipe

        do {
            try process.run()
        } catch {
            return .failure(error)
        }

        let outData = outPipe.fileHandleForReading.readDataToEndOfFile()
        let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        guard process.terminationStatus == 0 else {
            let errText = String(data: errData, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? "Error ejecutando script"
            return .failure(
                NSError(
                    domain: "ProviderRunner",
                    code: Int(process.terminationStatus),
                    userInfo: [NSLocalizedDescriptionKey: Self.extractErrorMessage(from: errText)]
                )
            )
        }
        return .success(outData)
    }

    private static func extractErrorMessage(from raw: String) -> String {
        if let data = raw.data(using: .utf8),
           let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let msg = obj["error"] as? String,
           !msg.isEmpty
        {
            return msg
        }
        return raw.isEmpty ? "Error desconocido" : raw
    }
}
