---
description: Create a structured implementation plan with context exploration
argument-hint: [what you want to do]
allowed-tools: Write, Read, Glob, Grep, Task, Bash
---

# Plan Command

Create keyword-focused implementation plan for Odoo tesote.com API Connector.

## User's Goal
$ARGUMENTS

## Process

### 1. Parse Input
- Extract feature/bug description
- Identify affected components (models, adapters, webhooks, etc.)

### 2. Explore Codebase
Use Task tool (subagent_type=Explore, thoroughness="very thorough"):
- Existing patterns: models, components (adapter, binder, mapper, importer), webhooks
- Similar implementations to reference
- Testing patterns (pytest, responses library, mocked Odoo)
- Connector architecture (OCA connector framework)
- i18n patterns (English/Spanish)
- API v2 integration patterns

### 3. Create Plan Structure
- Generate concise title (max 10 words)
- Create: `.debugging/plans/[plan-title]/`

### 4. Generate Planning Documents

Create files in plan directory:

**summary.md** (1-2 sentences)
```markdown
What this accomplishes and why needed for tesote.com Odoo connector.
```

**TODO.md** (actionable checklist)
```markdown
# TODO: [Plan Title]

**Branch**: feature/[branch-name]

## Setup
- [ ] Review patterns: `file.py:line`
- [ ] Check dependencies in pyproject.toml
- [ ] Verify Odoo 18.0 compatibility

## Implementation
- [ ] Model changes: `models/tesote_*.py` (fields, methods, @api decorators)
- [ ] Component updates: `components/adapter.py`, `binder.py`, `mapper.py`, `importer.py`
- [ ] Webhook handling: `models/tesote_webhook_*.py`, `controllers/webhook_controller.py`
- [ ] Backend logic: `models/tesote_backend.py` (sync orchestration)
- [ ] Views/UI: `views/tesote_*.xml` (forms, trees, actions, menus)
- [ ] Security: `security/ir.model.access.csv` (access rights)
- [ ] i18n: `i18n/tesote_connector.pot`, `i18n/en_US.po`, `i18n/es.po`
- [ ] Error tracking: Update Sentry integration if needed

## Testing
- [ ] Unit tests: `tests/test_*.py` (mock Odoo dependencies)
- [ ] API mocking: Use `responses` library for HTTP calls
- [ ] Test coverage: All new code paths
- [ ] Run: `uv run pytest -v`
- [ ] Verify: All 112+ tests still pass

## Quality
- [ ] Tests pass: `uv run pytest`
- [ ] Linting: `uv run ruff check --fix .`
- [ ] Formatting: `uv run black .`
- [ ] Import sorting: `uv run isort .`
- [ ] Pre-commit hooks: `uv run pre-commit run --all-files`
- [ ] SOLID principles applied

## Git & PR
- [ ] Branch: `git checkout -b [18.0|branch-name]`
- [ ] Commit + push + create PR
- [ ] Verify working branch (18.0)

## Notes
- Key considerations, dependencies, risks
- API v2 compatibility requirements
- Cursor management for sync
- Webhook security (HMAC verification)
```

**index.md** (comprehensive reference)
```markdown
# Plan: [Title]

## Overview
1-2 sentences: what/why for tesote.com Odoo connector

## Example Files (Patterns)
- Models: `models/tesote_backend.py`, `models/tesote_account.py`, `models/tesote_transaction.py`
- Components: `components/adapter.py`, `components/binder.py`, `components/mapper.py`
- Webhooks: `models/tesote_webhook_config.py`, `controllers/webhook_controller.py`
- Views: `views/tesote_backend_view.xml`, `views/tesote_account_view.xml`
- Tests: `tests/test_adapter*.py`, `tests/test_webhook*.py`, `tests/test_models.py`
- Security: `security/ir.model.access.csv`
- i18n: `i18n/en_US.po`, `i18n/es.po`
- Error tracking: `utils/sentry_config.py`

## Key Files to Modify
- `path/to/file.py:123` - What/why
- List models, components, views, tests, i18n

## Architecture Context
- Odoo 18.0 OCA connector framework
- tesote.com API v2.0.0 integration
- Singleton backend pattern (only one configuration)
- Cursor-based incremental sync
- Component architecture: adapter, binder, mapper, importer
- Webhook real-time updates with HMAC-SHA256 verification
- Rate limiting: 200/500/1000 req/min (Standard/Premium/Enterprise)
- Multi-language: English/Spanish
- Testing: pytest with mocked Odoo dependencies

## Implementation Strategy
1. **Models**: Add/modify Odoo models with proper decorators (@api.model, @api.depends)
2. **Components**: Update adapter/binder/mapper/importer logic
3. **API Integration**: Implement v2 endpoint calls with proper error handling
4. **Webhooks**: Handle event processing with signature verification
5. **Views**: Create/update XML views (forms, trees, actions, menus)
6. **Security**: Define access rights in CSV
7. **i18n**: Add translations for all user-facing strings
8. **Error Tracking**: Integrate Sentry for production monitoring
9. **Tests**: Write comprehensive unit tests with mocked dependencies

## Key Decisions
- API v2 vs v1 (always use v2)
- Sync strategy: cursor-based incremental
- Transaction state handling: pending → completed (36h aging)
- Webhook vs polling for updates
- Singleton backend enforcement
- Error tracking with Sentry

## Dependencies
- Odoo 18.0 (odoo.models, odoo.fields, odoo.api)
- Python 3.10+
- requests library for API calls
- OCA connector framework patterns
- pytest, responses (for testing)
- ruff, black, isort (for linting/formatting)

## Testing Strategy
- Unit tests with mocked Odoo dependencies (conftest.py)
- Mock HTTP calls with `responses` library
- Test all sync scenarios: added, modified, removed
- Test webhook event processing
- Test error handling and rate limiting
- Coverage: All components and models
- Run: `uv run pytest -v`

## SOLID Principles
- SRP: Single responsibility per component/model
- Open/Closed: Extend via inheritance (tesote_binding.py base)
- Liskov: Proper inheritance hierarchy
- Interface Segregation: Clean component interfaces
- Dependency Inversion: Depend on abstractions

## API v2 Key Points
- Sync endpoint: `POST /api/v2/transactions/sync`
- Cursor management: Always store `next_cursor`
- Transaction states: `pending` → `completed`
- Sync arrays: Process removed → modified → added
- Rate limits: 200/500/1000 req/min
- Webhooks: Real-time notifications

## References
- [TODO](./TODO.md), [Summary](./summary.md)
- [CLAUDE.md](../../CLAUDE.md)
- [docs/SENTRY_USAGE.md](../../docs/SENTRY_USAGE.md)
```

**plan-[aspect].md** (optional, only if complex)

Create focused files for specific aspects:
- `plan-models.md` - Model changes, fields, methods
- `plan-components.md` - Adapter/binder/mapper/importer logic
- `plan-webhooks.md` - Webhook handling and processing
- `plan-views.md` - XML views and UI
- `plan-api.md` - API v2 integration details
- `plan-testing.md` - Test strategy and coverage
- `plan-i18n.md` - Translation requirements

Each file:
- Focus on ONE aspect
- Keyword references + links to examples (not code blocks)
- Link to patterns with `file:line` format
- Link back to index.md

### 5. Cross-Reference
Link all files together with relative paths

### 6. Make Agent-Friendly
Use clear `file:line` format, bullet points, short sentences, cross-links

## Output Format
```
✓ Created plan: .debugging/plans/[plan-title]/

Files: summary.md, index.md, TODO.md, plan-*.md

Branch: feature/[name] or 18.0
Working Branch: 18.0

Next: /implement [plan-name]
```

## Guidelines

**Concise + comprehensive:**
- summary.md: 1-2 sentences
- index.md: what/why/where
- TODO.md: checklist + file references
- Use `file:line` format

**Link to patterns:**
- ✅ "Follow `components/adapter.py:123` but [difference]"
- ❌ Don't include code blocks

**Scannable:**
- Bullet points, short sentences, file references, cross-links

**Odoo connector context:**
- OCA connector framework patterns
- Component architecture (adapter, binder, mapper, importer)
- API v2 integration with cursor management
- Webhook security with HMAC verification
- Multi-language support (en/es)
- pytest with mocked Odoo dependencies
- SOLID principles

**Key requirements:**
- Odoo 18.0 compatibility
- API v2 only (no v1 code)
- Singleton backend pattern
- Cursor-based sync
- Comprehensive tests with mocked dependencies
- Follow CLAUDE.md guidelines
