import AppKit
import SwiftUI

enum ProviderLogoRenderer {
    static let viewBoxSize: CGFloat = 24.0

    // Exact official 24x24 paths synchronized 1:1 with assets/logos/{antigravity,codex,claude}.svg
    private static let antigravitySVGPath = "M21.345 22.1123C22.6291 23.0755 24.5553 22.4335 22.7895 20.6677C17.4927 15.5313 18.6162 1.4061 12.0352 1.4061C5.4541 1.4061 6.5777 15.5313 1.2808 20.6677C-0.6454 22.5939 1.4413 23.0755 2.7254 22.1123C7.7013 18.7416 7.3803 12.8026 12.0352 12.8026C16.69 12.8026 16.369 18.7416 21.345 22.1123Z"

    private static let codexSVGPath = "M22.2819 9.8211C22.8248 8.1862 22.6369 6.3967 21.7662 4.9103C20.4571 2.6316 17.826 1.4595 15.2564 2.0103C13.8083 0.3995 11.6112 -0.3168 9.492 0.1311C7.3728 0.5789 5.6533 2.1229 4.9807 4.1818C3.2928 4.5279 1.836 5.5847 0.983 7.0818C-0.3404 9.3568 -0.0401 12.2267 1.7257 14.1784C1.1808 15.8125 1.367 17.6022 2.2367 19.0891C3.5475 21.3686 6.1803 22.5406 8.7513 21.9892C9.8948 23.277 11.5377 24.0097 13.2599 24C15.8937 24.0024 18.2271 22.3021 19.0317 19.7942C20.7194 19.4475 22.176 18.3908 23.0294 16.8941C24.3368 14.6231 24.0351 11.7688 22.2819 9.8212ZM13.2599 22.4292C12.2086 22.4309 11.1903 22.0624 10.3835 21.3884L10.5254 21.308L15.3037 18.5498C15.5456 18.4079 15.6949 18.149 15.6964 17.8685L15.6964 11.1316L17.7164 12.3002C17.7367 12.3105 17.7508 12.3298 17.7544 12.3522L17.7544 17.9348C17.7491 20.4148 15.7399 22.424 13.2599 22.4292ZM3.5992 18.3038C3.072 17.3934 2.8827 16.3263 3.0646 15.2901L3.2066 15.3753L7.9896 18.1335C8.2306 18.2749 8.5292 18.2749 8.7702 18.1335L14.613 14.765L14.613 17.0974C14.6119 17.1219 14.5997 17.1445 14.5798 17.1589L9.74 19.9502C7.5893 21.1891 4.8416 20.4525 3.5992 18.3038ZM2.3408 7.8956C2.8717 6.9794 3.7096 6.2805 4.7063 5.9228L4.7063 11.6C4.7026 11.8793 4.8513 12.1386 5.0942 12.2765L10.9086 15.6308L8.8885 16.7993C8.8663 16.8111 8.8397 16.8111 8.8175 16.7993L3.9872 14.0128C1.8408 12.7686 1.1047 10.023 2.3408 7.872ZM18.9371 11.7514L13.1038 8.364L15.1192 7.2C15.1414 7.1882 15.168 7.1882 15.1902 7.2L20.0205 9.9913C21.5281 10.8612 22.3979 12.5234 22.2531 14.258C22.1083 15.9926 20.975 17.4876 19.344 18.0955L19.344 12.4183C19.3355 12.1397 19.1808 11.8863 18.937 11.7513ZM20.9478 8.7283L20.8058 8.6431L16.0323 5.8613C15.7898 5.719 15.4894 5.719 15.2469 5.8613L9.409 9.2297L9.409 6.8974C9.4065 6.8732 9.4174 6.8496 9.4374 6.8359L14.2677 4.0493C15.779 3.1787 17.6573 3.2599 19.0877 4.2578C20.5182 5.2556 21.2431 6.9903 20.9479 8.7093ZM8.3065 12.863L6.2865 11.6992C6.266 11.6869 6.2521 11.6661 6.2485 11.6425L6.2485 6.0742C6.2508 4.3304 7.2605 2.7449 8.8397 2.0054C10.419 1.2659 12.2833 1.5056 13.6242 2.6205L13.4822 2.701L8.704 5.459C8.4621 5.6009 8.3128 5.8598 8.3113 6.1403ZM9.4041 10.4976L12.0061 8.9978L14.613 10.4976L14.613 13.497L12.0156 14.9967L9.4089 13.497Z"

    private static let claudeSVGPath = "M4.7144 15.9555L9.4318 13.3084L9.5108 13.0777L9.4318 12.9502L9.2011 12.9502L8.4118 12.9016L5.7162 12.8287L3.3787 12.7316L1.1141 12.6102L0.5434 12.4887L0.0091 11.7845L0.0637 11.4323L0.5434 11.1105L1.2294 11.1713L2.7473 11.2745L5.024 11.4323L6.6754 11.5295L9.1222 11.7845L9.5108 11.7845L9.5654 11.6266L9.4318 11.5295L9.3286 11.4323L6.973 9.8356L4.423 8.1477L3.0874 7.1763L2.3649 6.6845L2.0006 6.2231L1.8428 5.2153L2.4985 4.4928L3.3788 4.5535L3.6034 4.6142L4.4959 5.3002L6.4023 6.7756L8.8916 8.6092L9.2559 8.9127L9.4016 8.8095L9.4198 8.7367L9.2558 8.4634L7.9019 6.0167L6.4569 3.5274L5.8134 2.4954L5.6434 1.876C5.5827 1.621 5.5402 1.4086 5.5402 1.1475L6.287 0.1335L6.6997 0L7.6954 0.1336L8.1144 0.4978L8.7336 1.9125L9.7354 4.1407L11.2897 7.1703L11.745 8.0688L11.9879 8.9006L12.0789 9.1556L12.2368 9.1556L12.2368 9.0099L12.3643 7.3039L12.6011 5.2092L12.8318 2.5135L12.9107 1.7546L13.2871 0.8439L14.0339 0.3521L14.6167 0.6314L15.0964 1.3174L15.0296 1.7607L14.7443 3.6124L14.1857 6.5145L13.8214 8.4574L14.0339 8.4574L14.2768 8.2145L15.2603 6.9092L16.9117 4.8449L17.6403 4.0253L18.4903 3.1207L19.0367 2.6896L20.0688 2.6896L20.8278 3.8189L20.4878 4.9846L19.4253 6.3324L18.5449 7.4738L17.2821 9.1738L16.4928 10.5338L16.5657 10.6431L16.7539 10.6248L19.6074 10.0178L21.1495 9.7384L22.9891 9.4227L23.8209 9.8113L23.9119 10.2059L23.5841 11.0134L21.6171 11.4991L19.3099 11.9605L15.8735 12.7741L15.831 12.8045L15.8796 12.8652L17.4278 13.0109L18.0896 13.0473L19.7106 13.0473L22.7281 13.272L23.5173 13.794L23.9909 14.4316L23.9119 14.9173L22.6977 15.5366L21.0584 15.148L17.2334 14.2373L15.9221 13.9094L15.7399 13.9094L15.7399 14.0187L16.8328 15.0873L18.8363 16.8965L21.3438 19.2279L21.4713 19.8047L21.1495 20.2601L20.8095 20.2115L18.6056 18.554L17.7556 17.8072L15.831 16.1862L15.7035 16.1862L15.7035 16.3562L16.1467 17.0058L18.4903 20.5272L18.6117 21.6079L18.4417 21.96L17.8346 22.1725L17.1667 22.0511L15.7946 20.1265L14.38 17.959L13.2386 16.0162L13.0989 16.0952L12.4249 23.3504L12.1093 23.7207L11.3807 24L10.7736 23.5386L10.4518 22.7918L10.7736 21.3165L11.1622 19.3919L11.4779 17.8619L11.7632 15.9615L11.9332 15.3301L11.9211 15.2876L11.7814 15.3058L10.3486 17.273L8.169 20.2176L6.4447 22.0632L6.0319 22.2272L5.3155 21.8568L5.3822 21.195L5.783 20.6061L8.169 17.5704L9.6079 15.6884L10.5369 14.6016L10.5307 14.4437L10.4761 14.4437L4.1376 18.5601L3.0083 18.7058L2.5226 18.2504L2.5834 17.5037L2.8141 17.2608L4.7205 15.9494Z"

    private static let cachedPaths: [AgentProvider: CGPath] = [
        .antigravity: parseSVGPath(antigravitySVGPath),
        .codex: parseSVGPath(codexSVGPath),
        .claude: parseSVGPath(claudeSVGPath),
    ]

    static func path(for provider: AgentProvider, in rect: CGRect) -> CGPath {
        let base = normalizedPath(for: provider)
        let scale = min(rect.width, rect.height) / viewBoxSize
        let dx = rect.midX - (viewBoxSize * scale) / 2.0
        let dy = rect.midY - (viewBoxSize * scale) / 2.0
        var transform = CGAffineTransform(translationX: dx, y: dy).scaledBy(x: scale, y: scale)
        return base.copy(using: &transform) ?? base
    }

    static func normalizedPath(for provider: AgentProvider) -> CGPath {
        cachedPaths[provider] ?? CGPath(rect: .zero, transform: nil)
    }

    static func menuBarImage(
        for provider: AgentProvider,
        size: CGFloat = 14.0,
        appearance: NSAppearance? = nil
    ) -> NSImage {
        let image = NSImage(size: NSSize(width: size, height: size), flipped: true) { rect in
            let targetAppearance = appearance ?? NSAppearance.currentDrawing()
            let match = targetAppearance.bestMatch(from: [.darkAqua, .vibrantDark, .aqua, .vibrantLight])
            let isDark = (match == .darkAqua || match == .vibrantDark)
            let resolvedColor = isDark ? NSColor.white : NSColor.black

            guard let ctx = NSGraphicsContext.current?.cgContext else { return false }
            ctx.saveGState()
            ctx.setFillColor(resolvedColor.cgColor)
            ctx.addPath(path(for: provider, in: rect.insetBy(dx: 0.25, dy: 0.25)))
            ctx.fillPath(using: .winding)
            ctx.restoreGState()
            return true
        }
        image.isTemplate = false
        return image
    }

    // MARK: - SVG Path Parser (M/L/C/Z)

    private static func parseSVGPath(_ d: String) -> CGPath {
        let path = CGMutablePath()
        var tokens: [String] = []
        var buffer = ""

        func flushBuffer() {
            if !buffer.isEmpty {
                tokens.append(buffer)
                buffer.removeAll(keepingCapacity: true)
            }
        }

        for ch in d {
            if ch == "M" || ch == "L" || ch == "C" || ch == "Z" {
                flushBuffer()
                tokens.append(String(ch))
            } else if ch == " " || ch == "," || ch == "\n" || ch == "\t" {
                flushBuffer()
            } else if ch == "-" && !buffer.isEmpty {
                flushBuffer()
                buffer.append(ch)
            } else {
                buffer.append(ch)
            }
        }
        flushBuffer()

        var idx = 0
        var currentCmd = "M"

        func nextNum() -> CGFloat? {
            guard idx < tokens.count, let v = Double(tokens[idx]) else { return nil }
            idx += 1
            return CGFloat(v)
        }

        while idx < tokens.count {
            let tok = tokens[idx]
            if tok == "M" || tok == "L" || tok == "C" || tok == "Z" {
                currentCmd = tok
                idx += 1
                if currentCmd == "Z" {
                    path.closeSubpath()
                    continue
                }
            }

            switch currentCmd {
            case "M":
                guard let x = nextNum(), let y = nextNum() else { break }
                path.move(to: CGPoint(x: x, y: y))
                currentCmd = "L"
            case "L":
                guard let x = nextNum(), let y = nextNum() else { break }
                path.addLine(to: CGPoint(x: x, y: y))
            case "C":
                guard let x1 = nextNum(), let y1 = nextNum(),
                      let x2 = nextNum(), let y2 = nextNum(),
                      let x = nextNum(), let y = nextNum() else { break }
                path.addCurve(
                    to: CGPoint(x: x, y: y),
                    control1: CGPoint(x: x1, y: y1),
                    control2: CGPoint(x: x2, y: y2)
                )
            default:
                idx += 1
            }
        }

        return path
    }
}

struct ProviderLogoView: View {
    let provider: AgentProvider
    var size: CGFloat = 14

    var body: some View {
        Canvas { context, canvasSize in
            let rect = CGRect(origin: .zero, size: canvasSize).insetBy(dx: 0.25, dy: 0.25)
            let path = Path(ProviderLogoRenderer.path(for: provider, in: rect))
            context.fill(path, with: .foreground, style: FillStyle(eoFill: false))
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)
    }
}
