# 📚 Documentation Sync Rules (MANDATORY)

> **CRITICAL**: These rules are NON-NEGOTIABLE. All code changes MUST follow this protocol.

---

## 🚨 The Golden Rule

**BEFORE changing ANY frontend/backend functionality:**
1. ✅ READ relevant `design/` specs (UI work)
2. ✅ READ relevant `docs/ai-guide/` documents
3. ✅ UNDERSTAND existing patterns

**AFTER changing ANY functionality:**
1. ✅ UPDATE `docs/ai-guide/` to reflect changes
2. ✅ VERIFY docs match implementation
3. ✅ ENSURE examples are current

---

## Why This Matters

❌ **Without this rule:**
- Documentation becomes stale and unreliable
- Developers make wrong assumptions from outdated docs
- Inconsistent implementations proliferate
- Tech debt accumulates exponentially
- Knowledge is lost when contributors leave

✅ **With this rule:**
- Documentation is always accurate source of truth
- Consistent patterns across entire codebase
- New contributors onboard quickly
- Less time wasted debugging confusion
- Codebase remains maintainable long-term

---

## Quick Reference Tables

### Design Specs (consult BEFORE UI changes)

| Change Type | Read This First |
|-------------|-----------------|
| Coin cards, grid layout | `design/CoinStack Frontpage + Grid Design.md` |
| Coin detail page | `design/CoinStack Individual Coin Page Design.md` |
| Table/list views | `design/CoinStack Coin Table Design.md` |
| Dashboard/stats | `design/CoinStack Statistics Dashboard Design.md` |
| Colors, badges, tokens | `design/CoinStack Design System v3.0.md` |

### Developer Guides (consult BEFORE any changes)

| Change Type | Read This First |
|-------------|-----------------|
| Backend logic | `docs/ai-guide/03-BACKEND-MODULES.md`, `08-CODING-PATTERNS.md` |
| Domain entities | `docs/ai-guide/04-DOMAIN-ENTITIES.md`, `05-DATA-MODEL.md` |
| Frontend components | `docs/ai-guide/04-FRONTEND-MODULES.md`, `11-FRONTEND-COMPONENTS.md` |
| UI/Design | `docs/ai-guide/10-DESIGN-SYSTEM.md`, `11-FRONTEND-COMPONENTS.md` |
| API endpoints | `docs/ai-guide/07-API-REFERENCE.md`, `06-DATA-FLOWS.md` |
| Database schema | `docs/ai-guide/05-DATA-MODEL.md`, `09-TASK-RECIPES.md` |

### Documentation Updates (update AFTER changes)

| Change Made | Update This |
|-------------|-------------|
| New/modified API endpoint | `docs/ai-guide/07-API-REFERENCE.md` |
| Database field added | `docs/ai-guide/05-DATA-MODEL.md` |
| New backend module | `docs/ai-guide/03-BACKEND-MODULES.md` |
| New domain entity | `docs/ai-guide/04-DOMAIN-ENTITIES.md` |
| New/modified component | `docs/ai-guide/11-FRONTEND-COMPONENTS.md` |
| Design token change | `docs/ai-guide/10-DESIGN-SYSTEM.md` + `design/` specs |
| New hook or store | `docs/ai-guide/04-FRONTEND-MODULES.md` |
| Data flow change | `docs/ai-guide/06-DATA-FLOWS.md` |
| New pattern | `docs/ai-guide/08-CODING-PATTERNS.md` |

---

## Pre-Commit Checklist

Before committing ANY code, verify:

- [ ] I consulted relevant `design/` specs (for UI work)
- [ ] I consulted relevant `docs/ai-guide/` documents
- [ ] I understood existing patterns before coding
- [ ] My implementation follows documented conventions
- [ ] I identified ALL documentation that needs updating
- [ ] I updated `docs/ai-guide/` to reflect changes
- [ ] Documentation examples match current implementation
- [ ] Future developers can rely on docs as accurate

**If ANY checkbox is unchecked → DO NOT commit.**

---

## Example: Correct Workflow

```
📋 Task: Add "provenance_notes" field to Coin entity

📖 CONSULTED BEFORE:
- docs/ai-guide/05-DATA-MODEL.md → Current Coin schema
- docs/ai-guide/04-DOMAIN-ENTITIES.md → Entity patterns
- docs/ai-guide/09-TASK-RECIPES.md → Field addition recipe

🔨 IMPLEMENTED:
- Added field to domain entity (src/domain/coin.py)
- Added field to ORM model (src/infrastructure/persistence/orm.py)
- Updated repository mappings
- Added to API schema (Pydantic models)
- Added to frontend form (CoinForm.tsx)

✏️ UPDATED AFTER:
- docs/ai-guide/05-DATA-MODEL.md → Added provenance_notes to schema
- docs/ai-guide/07-API-REFERENCE.md → Updated API request/response
- docs/ai-guide/11-FRONTEND-COMPONENTS.md → Updated CoinForm props
- ✅ VERIFIED: All docs match implementation

✅ Commit created with all code + doc updates
```

---

## Example: Incorrect Workflow (DO NOT DO)

```
📋 Task: Add new API endpoint

❌ Skip reading existing patterns (assume I know them)
❌ Implement with different response format
❌ Skip updating 07-API-REFERENCE.md ("I'll do it later")

⏰ 3 months later:
- Another developer needs similar endpoint
- Checks docs → not documented
- Implements DIFFERENT pattern
- Now TWO inconsistent approaches exist
- Tech debt grows, team confused

⚠️ This is EXACTLY what we're preventing!
```

---

## Enforcement

This rule is enforced at multiple levels:

1. **Cursor IDE rule** (`.cursor/rules/developer-guide.mdc`) - Always applies
2. **Critical rules doc** (`docs/ai-guide/08-CRITICAL-RULES.md`) - Validation checklist
3. **AI guide README** (`docs/ai-guide/README.md`) - Top-level visibility
4. **This document** (`DOCUMENTATION_RULES.md`) - Quick reference

**Consequences of violation:**
- Pull requests blocked until docs updated
- Loss of trust in documentation
- Increased maintenance burden
- Tech debt accumulation

---

## For AI Assistants

When making changes, you MUST:

1. **State what you consulted:**
   ```
   📖 CONSULTED BEFORE:
   - design/[file] - [what I learned]
   - docs/ai-guide/[file] - [relevant patterns]
   ```

2. **Make changes following documented patterns**

3. **Update documentation:**
   ```
   ✏️ UPDATED AFTER:
   - docs/ai-guide/[file] - [what changed]
   - ✅ VERIFIED: Docs match implementation
   ```

**This is not optional. This is mandatory for every change.**

---

## Related Documentation

- **Cursor rule**: `.cursor/rules/developer-guide.mdc`
- **Critical rules**: `docs/ai-guide/08-CRITICAL-RULES.md`
- **AI guide index**: `docs/ai-guide/README.md`
- **Design specs**: `design/` folder

---

**Last Updated**: January 25, 2026

**Enforcement Level**: ZERO TOLERANCE - All code changes must include documentation updates.
