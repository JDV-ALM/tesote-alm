---
description: Address and resolve CodeRabbit PR comments end-to-end using tstc CLI
argument-hint: <pr-url-or-number>
allowed-tools: Write, Read, Edit, Glob, Grep, Bash, Task, TodoWrite, AskUserQuestion
---

# Fix CodeRabbit PR Comments

Extract → Categorize → Implement → Test → Commit → Resolve

## PR
$ARGUMENTS

## Workflow

### 1. Extract
```bash
tstc pr:comments <pr_number> --username=coderabbitai[bot]
cat .debugging/prs/<pr_number>/00_overview.md
cat .debugging/prs/<pr_number>/03_ai_prompts_simple.md
```

### 2. Categorize
- **Major**: Security, bugs, breaking changes
- **Design**: Architecture, patterns
- **Minor**: Style, nitpicks

Use TodoWrite to track.

### 3. Verify & Decide (BE OBJECTIVE)
**DO NOT** blindly accept suggestions. For each comment:
1. Check docs (Odoo, Python, tesote.com API, pytest)
2. Verify claim applies to our context/version (Odoo 18.0, Python 3.10+, API v2)
3. Test the suggestion
4. Decide: Implement if TRUE, Disagree if FALSE

### 4. Implement
For each prompt in `03_ai_prompts_simple.md`:
1. Verify objectively
2. Implement OR prepare disagreement with evidence
3. Mark complete

### 5. Test & Lint
```bash
uv run pytest -v
uv run ruff check --fix .
uv run black .
uv run isort .
uv run pre-commit run --all-files
```

### 6. Commit
```bash
git add .
git commit -m "$(cat <<'EOF'
fix: Address CodeRabbit comments [PR #<pr>]

- <changes>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push
```

### 7. Resolve with Evidence

**Reply to Individual Comments**:
```bash
# Reply to a specific comment
tstc pr:comments:reply <comment_id> \
  --pr=<pr_number> \
  --message="Fixed in commit <sha>. Verified with Odoo 18.0 docs."

# Show comment details
tstc pr:comments:show <comment_id> --pr=<pr_number>

# Resolve comment thread
tstc pr:comments:resolve <comment_id> --pr=<pr_number>
```

**Examples**:
- ✅ "Fixed in commit abc123. Verified with Odoo 18.0 API docs - @api.depends required for computed fields."
- ✅ "Implemented. pytest docs confirm responses library is best practice for HTTP mocking."
- ❌ "Not applicable. Per tesote.com API v2 docs, cursor must be stored after each sync. See: https://api.tesote.com/docs/v2"
- ❌ "Already handled in components/adapter.py:142 via rate limit backoff"

**Batch Process Comments**:
```bash
# Get all comment IDs from overview
grep -o 'comment_id: [0-9]*' .debugging/prs/<pr_number>/00_overview.md

# Reply and resolve each
for comment_id in $(cat comment_ids.txt); do
  tstc pr:comments:reply $comment_id \
    --pr=<pr_number> \
    --message="Addressed in commit <sha>"
  tstc pr:comments:resolve $comment_id --pr=<pr_number>
done
```

## Rules
1. **BE OBJECTIVE** - Verify claims, check docs, test suggestions
2. **COMMIT FIRST** - Push before resolving
3. **PROVIDE EVIDENCE** - Link sources in responses (Odoo docs, Python docs, API docs)
4. **DISAGREE WHEN WRONG** - Help CodeRabbit learn with facts
5. **TEST ALL** - Full suite must pass (112+ tests)
6. **LINT** - All checks must be clean (ruff, black, isort, pre-commit)

## Context-Specific Checks
- **Odoo 18.0**: Verify decorator usage (@api.model, @api.depends, @api.model_create_multi)
- **API v2**: Confirm cursor management, rate limiting, error handling
- **Webhooks**: Verify HMAC-SHA256 signature verification
- **Testing**: Ensure mocked Odoo dependencies, HTTP mocking with responses
- **i18n**: Check _() function usage for translations

## Output
```
🔍 PR #<n>: <count> comments (<major> major, <design> design, <minor> minor)
📁 .debugging/prs/<n>/

✅ Implemented <count> fixes
✅ Tests pass (112+ tests) • Lint clean
🔀 Committed & pushed
✅ Resolved <count> threads
⚠️  Disagreed <count> threads
```

## Troubleshooting
- No comments: Check `tstc status`, verify auth
- Failed resolve: Verify PR is open, check GitHub token
- tstc command not found: Verify tstc is installed and in PATH
- HTTP 422: PR may be closed or merged
