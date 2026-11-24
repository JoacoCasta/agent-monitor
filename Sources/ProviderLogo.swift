import AppKit
import SwiftUI

enum ProviderLogoRenderer {
    static let viewBoxSize: CGFloat = 24.0

    static func path(for provider: AgentProvider, in rect: CGRect) -> CGPath {
        let base = normalizedPath(for: provider)
        let scale = min(rect.width, rect.height) / viewBoxSize
        let dx = rect.midX - (viewBoxSize * scale) / 2.0
        let dy = rect.midY - (viewBoxSize * scale) / 2.0
        var transform = CGAffineTransform(translationX: dx, y: dy).scaledBy(x: scale, y: scale)
        return base.copy(using: &transform) ?? base
    }

    static func normalizedPath(for provider: AgentProvider) -> CGPath {
        switch provider {
        case .antigravity:
            return antigravityPath()
        case .codex:
            return codexPath()
        case .claude:
            return claudePath()
        }
    }

    static func menuBarImage(
        for provider: AgentProvider,
        size: CGFloat = 13.5,
        appearance: NSAppearance? = nil
    ) -> NSImage {
        let image = NSImage(size: NSSize(width: size, height: size), flipped: true) { rect in
            let targetAppearance = appearance ?? NSAppearance.currentDrawing()
            var resolvedColor = NSColor.labelColor
            targetAppearance.performAsCurrentDrawingAppearance {
                if let srgb = NSColor.labelColor.usingColorSpace(.sRGB) {
                    resolvedColor = srgb
                } else {
                    resolvedColor = NSColor.labelColor
                }
            }

            guard let ctx = NSGraphicsContext.current?.cgContext else { return false }
            ctx.saveGState()
            ctx.setFillColor(resolvedColor.cgColor)
            ctx.addPath(path(for: provider, in: rect))
            ctx.fillPath()
            ctx.restoreGState()
            return true
        }
        image.isTemplate = false
        return image
    }

    // MARK: - Vector Paths (24x24 Y-down)

    private static func antigravityPath() -> CGPath {
        let p = CGMutablePath()
        // Smooth rounded upward arch ("A" silhouette matching Antigravity)
        p.move(to: CGPoint(x: 2.9, y: 20.3))
        p.addCurve(
            to: CGPoint(x: 12.0, y: 2.3),
            control1: CGPoint(x: 5.0, y: 13.8),
            control2: CGPoint(x: 8.6, y: 2.3)
        )
        p.addCurve(
            to: CGPoint(x: 21.1, y: 20.3),
            control1: CGPoint(x: 15.4, y: 2.3),
            control2: CGPoint(x: 19.0, y: 13.8)
        )
        p.addCurve(
            to: CGPoint(x: 17.3, y: 20.8),
            control1: CGPoint(x: 21.7, y: 21.7),
            control2: CGPoint(x: 18.9, y: 22.1)
        )
        p.addCurve(
            to: CGPoint(x: 12.0, y: 11.4),
            control1: CGPoint(x: 15.3, y: 17.2),
            control2: CGPoint(x: 13.9, y: 11.4)
        )
        p.addCurve(
            to: CGPoint(x: 6.7, y: 20.8),
            control1: CGPoint(x: 10.1, y: 11.4),
            control2: CGPoint(x: 8.7, y: 17.2)
        )
        p.addCurve(
            to: CGPoint(x: 2.9, y: 20.3),
            control1: CGPoint(x: 5.1, y: 22.1),
            control2: CGPoint(x: 2.3, y: 21.7)
        )
        p.closeSubpath()
        return p
    }

    private static func codexPath() -> CGPath {
        // Exact C1-tangent 6-petal interlocking hexagonal knot (OpenAI / Codex emblem)
        let strokePath = CGMutablePath()
        let cx: CGFloat = 12.0
        let cy: CGFloat = 12.0
        let lobeDist: CGFloat = 5.0
        let apothem: CGFloat = 2.55
        let lobeRadius: CGFloat = 0.5 * lobeDist + apothem
        let hexVertexR: CGFloat = apothem / (sqrt(3.0) / 2.0)

        for k in 0..<6 {
            let theta = CGFloat(k) * (.pi / 3.0) - (.pi / 2.0)
            let lobeCenter = CGPoint(
                x: cx + lobeDist * cos(theta),
                y: cy + lobeDist * sin(theta)
            )

            // Straight segment enters collinearly along hexagon edge (-150 deg) to T1,
            // wraps 240 deg C1-tangentially around lobeCenter, and exits to +90 deg vertex.
            let v1Angle = theta - (5.0 * .pi / 6.0)
            let vStart = CGPoint(
                x: cx + hexVertexR * cos(v1Angle),
                y: cy + hexVertexR * sin(v1Angle)
            )
            let vEndAngle = theta + (.pi / 2.0)
            let vEnd = CGPoint(
                x: cx + hexVertexR * cos(vEndAngle),
                y: cy + hexVertexR * sin(vEndAngle)
            )

            let arcStartAngle = theta - (2.0 * .pi / 3.0)
            let arcEndAngle = theta + (2.0 * .pi / 3.0)
            let t1 = CGPoint(
                x: lobeCenter.x + lobeRadius * cos(arcStartAngle),
                y: lobeCenter.y + lobeRadius * sin(arcStartAngle)
            )

            strokePath.move(to: vStart)
            strokePath.addLine(to: t1)
            strokePath.addArc(
                center: lobeCenter,
                radius: lobeRadius,
                startAngle: arcStartAngle,
                endAngle: arcEndAngle,
                clockwise: false
            )
            strokePath.addLine(to: vEnd)
        }

        return strokePath.copy(
            strokingWithWidth: 1.55,
            lineCap: .round,
            lineJoin: .round,
            miterLimit: 4.0
        )
    }

    private static func claudePath() -> CGPath {
        // Single continuous non-overlapping 12-ray starburst contour (Claude / Anthropic emblem)
        let p = CGMutablePath()
        let cx: CGFloat = 12.0
        let cy: CGFloat = 12.0
        let rayCount = 12
        let lengths: [CGFloat] = [
            10.4, 8.7, 10.1, 8.9, 10.5, 8.6,
            10.2, 9.0, 10.4, 8.7, 9.9, 9.1
        ]
        let valleyRadius: CGFloat = 3.1
        let baseHalfW: CGFloat = 0.88
        let tipRadius: CGFloat = 0.65

        for idx in 0..<rayCount {
            let step = (2.0 * .pi) / CGFloat(rayCount)
            let angle = CGFloat(idx) * step - (.pi / 2.0) + 0.08
            let prevValleyAngle = angle - step * 0.5
            let nextValleyAngle = angle + step * 0.5

            let ux = cos(angle)
            let uy = sin(angle)
            let px = -uy
            let py = ux

            let len = lengths[idx]
            let tipCenter = CGPoint(
                x: cx + (len - tipRadius) * ux,
                y: cy + (len - tipRadius) * uy
            )

            let vPrev = CGPoint(
                x: cx + valleyRadius * cos(prevValleyAngle),
                y: cy + valleyRadius * sin(prevValleyAngle)
            )
            let bLeft = CGPoint(
                x: cx + (valleyRadius + 0.25) * ux - baseHalfW * px,
                y: cy + (valleyRadius + 0.25) * uy - baseHalfW * py
            )
            let tLeft = CGPoint(
                x: tipCenter.x - tipRadius * px,
                y: tipCenter.y - tipRadius * py
            )
            let tRight = CGPoint(
                x: tipCenter.x + tipRadius * px,
                y: tipCenter.y + tipRadius * py
            )
            let bRight = CGPoint(
                x: cx + (valleyRadius + 0.25) * ux + baseHalfW * px,
                y: cy + (valleyRadius + 0.25) * uy + baseHalfW * py
            )
            let vNext = CGPoint(
                x: cx + valleyRadius * cos(nextValleyAngle),
                y: cy + valleyRadius * sin(nextValleyAngle)
            )

            if idx == 0 {
                p.move(to: vPrev)
            }
            p.addLine(to: bLeft)
            p.addLine(to: tLeft)
            p.addArc(
                center: tipCenter,
                radius: tipRadius,
                startAngle: angle - (.pi / 2.0),
                endAngle: angle + (.pi / 2.0),
                clockwise: false
            )
            p.addLine(to: tRight)
            p.addLine(to: bRight)
            p.addLine(to: vNext)
        }
        p.closeSubpath()
        return p
    }
}

struct ProviderLogoView: View {
    let provider: AgentProvider
    var size: CGFloat = 14

    var body: some View {
        Canvas { context, canvasSize in
            let rect = CGRect(origin: .zero, size: canvasSize)
            let path = Path(ProviderLogoRenderer.path(for: provider, in: rect))
            context.fill(path, with: .foreground)
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)
    }
}
