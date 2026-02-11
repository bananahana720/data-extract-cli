# Local CI Reproduction Report

- Generated: 2026-02-11 20:00:19 UTC
- Repository: /home/andrewhana/projects/codex-fun/data-extraction-tool-main
- Profile: security
- Pass: 2
- Warn: 0
- Fail: 0

## security:secrets-scan [PASS]

- Command: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/.venv/bin/python scripts/scan_security.py --secrets-only --format json`
- Return code: `0`
- Duration: `0.49s`

```text
2026-02-11 15:00:18 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:18 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:18 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:18 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:18 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:18 [info     ] initialized_security_orchestrator project_root=/home/andrewhana/projects/codex-fun/data-extraction-tool-main
2026-02-11 15:00:18 [warning  ] gitleaks_not_installed
  Scanning for secrets... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
2026-02-11 15:00:19 [info     ] pattern_scan_completed         files_scanned=410
✓ No security issues found!

[green]Report saved to: /home/andrewhana/projects/codex-fun/data-extraction-tool-main/docs/security-reports/security_report_20260211_150019.json[/green]

[green]✓ Security scan completed successfully with no findings[/green]
```

## security:deps-scan [PASS]

- Command: `/home/andrewhana/projects/codex-fun/data-extraction-tool-main/.venv/bin/python scripts/scan_security.py --deps-only --format json`
- Return code: `0`
- Duration: `0.14s`

```text
2026-02-11 15:00:19 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:19 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:19 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:19 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:19 [info     ] loaded_scanignore              patterns=48
2026-02-11 15:00:19 [info     ] initialized_security_orchestrator project_root=/home/andrewhana/projects/codex-fun/data-extraction-tool-main
2026-02-11 15:00:19 [info     ] pip_audit_not_installed
✓ No security issues found!

[green]Report saved to: /home/andrewhana/projects/codex-fun/data-extraction-tool-main/docs/security-reports/security_report_20260211_150019.json[/green]

[green]✓ Security scan completed successfully with no findings[/green]
```
