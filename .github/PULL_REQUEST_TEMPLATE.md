## Summary
Briefly describe the changes in this PR and link any related issue (e.g., `Fixes #123`).

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation / translations
- [ ] Build / CI / packaging

## Platforms Tested
- [ ] macOS (`./build.sh` & `codesign --verify --deep --strict`)
- [ ] Windows (PySide6 tray & `py_compile`)
- [ ] Linux (PySide6 tray, `--status-json`, `py_compile`)

## Checklist
- [ ] Ran `python3 -m unittest discover -s tests -v` and all tests pass.
- [ ] Verified no `@State`, `@Observable`, or SwiftUI macros were introduced in `Sources/*.swift`.
- [ ] Preserved `--status-json` schema compatibility (`tag`, `displayName`, `status`, `percent`, `activeSessions`, `quota`).
- [ ] Updated `README.md` and `README.es.md` in sync (if user-facing behavior changed).
- [ ] Verified no personal emails, usernames, or private paths appear in code or screenshots.
