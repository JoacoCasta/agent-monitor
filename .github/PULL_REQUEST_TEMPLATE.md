## Summary
Briefly describe the changes in this PR and link any related issue (e.g., `Fixes #123`).

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation / translations
- [ ] Build / CI / packaging

## Verification on macOS
- [ ] `./build.sh` compiles cleanly and `codesign --verify --deep --strict /Applications/AgentMonitor.app` passes.
- [ ] Universal (`arm64` + `x86_64`) build verified if build/workflow files changed.
- [ ] `python3 -m py_compile Scripts/*.py` and `python3 -m unittest discover -s tests -v` pass.
- [ ] `bash -n build.sh install.sh uninstall.sh` passes.

## Checklist
- [ ] Verified no `@State`, `@Observable`, or SwiftUI macros were introduced in `Sources/*.swift`.
- [ ] Updated `README.md` and `README.es.md` in sync (if user-facing behavior changed).
- [ ] Verified no personal emails, usernames, or private paths appear in code or screenshots.
