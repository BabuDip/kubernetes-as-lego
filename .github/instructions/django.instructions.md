---
description: "Django backend conventions specific to QLess Cafe"
applyTo: "{config,qless_cafe}/**/*.py"
---

# Django Instructions

See `AGENTS.md`'s "Conventions that matter" and "Code layout" sections for
the full list — the rules below are the highest-risk ones to get wrong
while editing backend code, restated here so they surface path-scoped.

- **Server-trusted pricing** — never compute or trust a price/label from the
  request body. `qless_cafe/catalog/modifiers.py`'s `resolve_modifiers()` is
  the only place a modifier selection turns into a price; route all pricing
  logic through it instead of reimplementing it in a view or serializer.
- **Realtime events** — only `notify()` and `notify_managers()` in
  `qless_cafe/notifications/services.py` may call `group_send`. Call them
  from inside `transaction.on_commit()` so an event never fires for a
  rolled-back change.
- **New models get a UUID7 primary key**:
  `id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)`.
- **Pre-first-release migrations** — this project hasn't shipped yet: when a
  model changes, delete that app's existing migration file(s) and regenerate
  a single fresh `0001_initial` rather than accumulating `0002_*`, `0003_*`.
- **Manager = `is_staff=True`** on the standard `User` model — there is no
  separate Manager model/group; don't invent one.
- **Session auth only** — no JWT, no `django-allauth`. `GET /api/auth/csrf/`
  must be called before any unsafe request from the SPA.
- Views can hold orchestration logic (e.g. `qless_cafe/orders/api_views.py`'s
  status-transition state machine), but pricing, permission checks, and
  realtime notifications must go through the modules above, not be
  reimplemented inline.
- Leverage Django/DRF built-ins (`ModelSerializer`, `ViewSet` actions,
  `permissions` classes) before writing a custom equivalent.
- No i18n (`USE_I18N = False`) — don't add `gettext`/translation machinery.
