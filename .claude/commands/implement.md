---
description: Find and implement a plan from .debugging/plans/
argument-hint: [keyword or fuzzy search]
allowed-tools: Read, Write, Edit, Glob, Grep, Task, Bash, TodoWrite, AskUserQuestion
---

# Implement Command

Find and implement plan using TDD + SOLID for Odoo tesote.com API Connector.

## Query
$ARGUMENTS

## Process

### 1. Find Plans
Search `.debugging/plans/` for matches:
- Directory names
- summary.md content
- index.md content

Multiple matches → AskUserQuestion with plan titles + summaries
No matches → Suggest `/plan` first
One match → Proceed

### 2. Load Plan Context
Read ALL files in `.debugging/plans/[plan-title]/`:
- summary.md (quick context)
- index.md (architecture/patterns)
- TODO.md (implementation steps)
- plan-*.md (specific aspects: database, services, activeadmin, app, i18n, testing)

Get context for: architecture, patterns, files, testing, SOLID, namespaces, i18n

### 3. Create Todo List
Use TodoWrite with all phases/steps from TODO.md (exact wording)
Set first unchecked as `in_progress`

### 4. Setup
1. `git status` - clean working directory
2. `git checkout -b feature/[name]` OR stay on `18.0` if working on main branch
3. Verify current branch is appropriate (18.0 is the main development branch)

### 5. Implement (TDD + SOLID)
For each TODO.md step:

1. **Mark in_progress** (TodoWrite)

2. **Reference context**: index.md, plan-*.md, CLAUDE.md

3. **TDD cycle**:
   - **RED**: Write failing test (`tests/test_*.py`)
   - **GREEN**: Implement minimal code (models, components, webhooks, views)
   - **REFACTOR**: Apply SOLID (SRP, Open/Closed, DIP)

4. **SOLID principles** (apply, don't explain):
   - Components = business logic (SRP)
   - Models = data + Odoo framework methods
   - Adapter = API communication only
   - Binder/Mapper/Importer = specific responsibilities
   - Inject dependencies (DIP)

5. **Odoo connector patterns**:
   - Models: @api.model, @api.depends decorators
   - Components: adapter, binder, mapper, importer
   - API v2: cursor-based sync with proper error handling
   - Webhooks: HMAC-SHA256 signature verification
   - i18n: _() function for translations (en/es)
   - Error tracking: Sentry integration

6. **Run tests**: `uv run pytest tests/test_specific.py -v`

7. **Update TODO.md**: `- [ ]` → `- [x]` (Edit tool)

8. **Mark completed** (TodoWrite)

9. **Next step**

### 6. Quality Checks
After all steps:

1. **Tests**: `uv run pytest -v` - all pass (green), comprehensive coverage
2. **Linting**: `uv run ruff check --fix .` - all pass
3. **Formatting**: `uv run black .` - consistent style
4. **Import sorting**: `uv run isort .` - organized imports
5. **Pre-commit**: `uv run pre-commit run --all-files` - all hooks pass
6. **Fix issues**: test failures, lint errors, warnings
7. **Verify**: SOLID, no security issues, API v2 compatibility, i18n complete

### 7. Create PR
Once quality checks pass:

1. `git add .`
2. `git commit -m "$(cat <<'EOF'
Add [feature]

- Implemented [changes]
- Added comprehensive tests
- SOLID principles
- API v2 compatible

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"`
3. `git push -u origin [branch-name]` (or just `git push` if on 18.0)
4. `gh pr create --title "Title" --body "$(cat <<'EOF'
## Summary
- What/why/changes

## Test plan
- [ ] Tests pass (`uv run pytest -v`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Formatting passes (`uv run black --check .`)
- [ ] Pre-commit hooks pass (`uv run pre-commit run --all-files`)
- [ ] Manually tested in Odoo 18.0
- [ ] Verified i18n (en/es)
- [ ] API v2 compatibility verified

## References
- Plan: `.debugging/plans/[name]/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"`

### 8. Reference Plan Files
Continuously reference: index.md, plan-models.md, plan-components.md, plan-webhooks.md, plan-api.md, plan-testing.md, plan-i18n.md, CLAUDE.md

### 9. Handle Blockers
- Document in TODO.md "## Blockers"
- Keep step unchecked
- AskUserQuestion for guidance
- DO NOT mark complete if blocked

### 10. Completion Summary
When done:
- Verify: TODO.md all checked, tests pass, linting passes, PR created
- Summarize: what/files/tests/SOLID/PR link

## Example Output
```
🔍 Found: .debugging/plans/add-webhook-retry/
📖 Loaded: summary.md, index.md, TODO.md, plan-*.md
✅ Ready: TDD + SOLID

Setup
✓ Git clean
✓ Branch: 18.0

Phase 1: Models [1/4]
✓ TDD Red → Green → Refactor
✓ Tests pass: uv run pytest tests/test_webhook_retry.py -v
✓ TODO.md [x]

[Continue...]

Quality
✓ Tests pass (112+ tests) ✓ Linting pass ✓ SOLID ✓

PR
✓ Committed + pushed
✓ Created: https://github.com/tesote/tesote-odoo-api-connector/pull/123

🎉 Complete! 10 steps. Tests ✓ Linting ✓ PR ✓
```

## Key Notes

**Context**
- Read ALL plan files first
- Reference plan-*.md for guidance
- Follow Odoo connector patterns (index.md, CLAUDE.md)
- Component architecture: adapter, binder, mapper, importer
- Verify i18n: _() function for both en/es

**Workflow**
- Feature branch OR 18.0 main branch
- TDD: Red → Green → Refactor
- SOLID: Apply (don't explain) - SRP, Open/Closed, Liskov, Interface Segregation, DIP
- Update TODO.md immediately
- Sync TodoWrite

**Odoo Connector Patterns**
- Models: Odoo models with @api decorators (models/tesote_*.py)
- Components: adapter (API), binder (ID mapping), mapper (transformation), importer (sync)
- API v2: cursor-based sync, proper error handling
- Webhooks: HMAC-SHA256 verification, event processing
- Views: XML forms/trees/actions/menus
- i18n: _() function, .po files (en_US, es)
- Error tracking: Sentry integration

**Testing**
- pytest: comprehensive coverage
- responses library: mock HTTP calls
- conftest.py: mocked Odoo dependencies
- Test patterns: models, components, webhooks, sync
- Run before commit: `uv run pytest -v`

**Quality**
- Tests pass (`uv run pytest -v`)
- Linting passes (`uv run ruff check --fix .`)
- Formatting passes (`uv run black .`)
- Import sorting (`uv run isort .`)
- Pre-commit hooks (`uv run pre-commit run --all-files`)
- SOLID principles
- No security issues (XSS, injection, etc.)
- API v2 compatibility
- Follow TODO.md order

**Blockers**
- Document in TODO.md "## Blockers"
- Keep unchecked
- AskUserQuestion
- DO NOT mark complete

## No Plans
If no matches: `No plans found. Use: /plan [describe] first`

## Multiple Matches
AskUserQuestion with plan titles + summaries, let user select

## Checklist
Every implementation:
- [ ] Models with proper @api decorators
- [ ] Components (adapter/binder/mapper/importer) as needed
- [ ] API v2 compatibility with cursor management
- [ ] Webhook security (HMAC verification)
- [ ] Views (XML forms/trees/actions)
- [ ] i18n (_() function, en/es translations)
- [ ] Tests with mocked Odoo
- [ ] Mock HTTP with responses library
- [ ] SOLID (SRP, DIP, etc.)
- [ ] `uv run pytest -v` pass
- [ ] `uv run ruff check .` pass
- [ ] `uv run black .` + `uv run isort .` pass
- [ ] PR created
- [ ] Follow CLAUDE.md
