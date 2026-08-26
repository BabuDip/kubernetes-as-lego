---
description: "Python coding conventions and guidelines"
applyTo: "**/*.py"
---

# Python Instructions

- Follow PEP 8; ruff enforces an 88-character line length and a wide rule
  set including `DTZ` (see `pyproject.toml`'s `[tool.ruff]`) — don't disable
  rules to work around a violation, fix the code instead.
- Use clear names, small functions, and explicit edge-case handling.
- Datetimes must be timezone-aware (`USE_TZ = True`, enforced by ruff's
  `DTZ` rules) — never use naive `datetime.now()`/`datetime.utcnow()`.
- Add type hints for new non-framework-specific functions/classes; mypy runs
  with `django-stubs`/`djangorestframework-stubs` (see `pyproject.toml`'s
  `[tool.mypy]`) and must stay clean — run it exactly as documented in
  `AGENTS.md`'s "Checks to run before considering backend work done"
  (`docker compose -f docker-compose.yaml run --rm django mypy qless_cafe`).
- Prefer concise comments only where intent, edge cases, or an external
  dependency's behavior need explaining — see the header-comment style
  already used across `qless_cafe/` (e.g. `qless_cafe/catalog/modifiers.py`).
- Add or update pytest coverage for behavior changes — see
  `.github/instructions/tests.instructions.md`.
- Keep functions focused and cohesive; avoid decomposition that adds call
  depth without a clarity benefit.
