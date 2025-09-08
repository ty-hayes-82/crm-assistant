## Development Roadmap (A2A‑Compliant CRM Agent → HubSpot)

- **environment**: Use conda env `adk` for all dev and runs.
- **default model**: `gemini-2.5-flash` across agents/workflows.
- **principle**: Each phase is independently completable and testable; phases build progressively.

### ✅ Phase 0 — Environment, smoke tests, and baselines (COMPLETED)
- **goal**: Confirm the repo runs, the core orchestrator works, and the A2A card scaffold loads.
- **scope**:
  - Verify `.env` and Private App token plumbing exists (no HubSpot write yet).
  - Exercise `create_crm_coordinator()` and `create_crm_a2a_agent()` locally.
  - Load the Agent Card builder in `crm_agent/a2a/__main__.py`.
- **how to test (PowerShell)**:
```powershell
conda activate adk
python -c "from crm_agent.coordinator import create_crm_coordinator; a=create_crm_coordinator(); print(type(a))"
python -c "from crm_agent.a2a.agent import create_crm_a2a_agent; a=create_crm_a2a_agent(); print(hasattr(a,'invoke'))"
python -c "from crm_agent.a2a.__main__ import build_agent_card; import json; print(json.dumps(build_agent_card(), indent=2))"
```
- **acceptance**:
  - ✅ Objects construct without errors; Agent Card prints valid JSON stub.

### ✅ Phase 1 — Discovery + quick lookup + data quality gate (offline) (COMPLETED)
- **goal**: Produce grounded company facts (no HubSpot writes), enforce provenance.
- **scope**:
  - Use `create_crm_quick_lookup_workflow()` and `create_crm_parallel_retrieval_workflow()` in `crm_agent/agents/workflows/crm_enrichment.py`.
  - Ensure `create_crm_data_quality_agent()` gating requires `source_urls` + `last_verified_at`.
  - Normalize output schema to match doc §1 properties and §2.5 provenance.
- **how to test**:
  - Feed 3–5 public course domains/names; verify JSON includes citations and timestamps.
  - Add a unit test to fail when any field lacks `source_urls` or `last_verified_at`.
- **acceptance**:
  - ✅ For each input, returns structured JSON with citations; DQ fails on missing provenance.
  - ✅ Unit tests in `tests/enrichment/test_provenance_gate.py` validate provenance enforcement.

### ✅ Phase 2 — HubSpot connectivity (direct script; safe dry run) (COMPLETED)
- **goal**: Prove HubSpot auth and payloads with an isolated script.
- **scope**:
  - Use `scripts/update_mansion_ridge_direct.py` as reference.
  - Add a `DRY_RUN` mode and a `HUBSPOT_TEST_PORTAL` guard.
  - Confirm read of Companies/Contacts and a no‑write dry run for create/update payloads.
- **how to test**:
```powershell
conda activate adk
$env:DRY_RUN="1"
python .\scripts\update_mansion_ridge_direct.py
```
- **acceptance**:
  - ✅ Auth succeeds; payloads validate; dry‑run logs the exact requests without mutating HubSpot.
  - ✅ HUBSPOT_TEST_PORTAL guard prevents writes to production portals.

### ✅ Phase 3 — HubSpot tools via ADK OpenAPI (replace placeholders) (COMPLETED)
- **goal**: Shift from ad‑hoc calls to generated tools; wire into `crm_updater`.
- **scope**:
  - In `crm_agent/core/factory.py`, add ADK `OpenApiTool` for HubSpot (Companies/Contacts/Associations/Emails/Tasks).
  - In `crm_agent/agents/specialized/crm_agents.py`, make `create_crm_updater()` call those tools.
  - Add idempotency key scaffolding for writes (per object + field set).
- **how to test**:
  - Run an "offline → approve → apply" loop: Phase 1 output feeds `crm_updater` in a sandbox portal.
  - Create a test Company with minimal props and associations; verify results in HubSpot.
- **acceptance**:
  - ✅ One command applies updates through OpenAPI tools; repeated run is idempotent.
  - ✅ `create_hubspot_openapi_tool()` factory creates OpenAPI tools for HubSpot CRM v3.
  - ✅ CRM updater agent wired with OpenAPI tools and idempotency key generation.

### Phase 4 — A2A wrapper consolidation + Agent Card expansion
- **goal**: Single canonical A2A entrypoint with richer, documented skills.
- **scope**:
  - Deprecate `crm_agent/a2a_wrapper.py`; update imports in callers to `crm_agent.a2a.agent.create_crm_a2a_agent`.
  - Expand `build_agent_card()` in `crm_agent/a2a/__main__.py` with skills:
    - `course.profile.extract`, `contact.roles.infer`, `hubspot.sync`, `lead.score.compute`, `outreach.generate`.
  - Document auth placeholders and versioning.
- **how to test**:
```powershell
conda activate adk
python -c "from crm_agent.a2a.__main__ import build_agent_card; import json; c=build_agent_card(); print(json.dumps(c,indent=2))"
```
- **acceptance**:
  - No references to legacy wrapper; Agent Card advertises expanded skills.

### Phase 5 — A2A HTTP server (JSON‑RPC + SSE) and lifecycle
- **goal**: Expose the CRM Agent via a real A2A server with task lifecycle.
- **scope**:
  - Add minimal HTTP server (JSON‑RPC 2.0) + SSE streaming; wire to `CRMAgentTaskManager` in `crm_agent/a2a/task_manager.py`.
  - Implement states: queued → running → completed/failed; map errors to A2A semantics.
  - Include request/response schemas that mirror Agent Card skill I/O.
- **how to test**:
  - Start the server; POST a JSON‑RPC request for `course.profile.extract`; stream SSE and validate final result matches Phase 1 schema.
- **acceptance**:
  - Requests complete with streaming updates; standardized lifecycle events emitted.

### Phase 6 — Lead scoring agent
- **goal**: Compute Fit/Intent and write `swoop_fit_score`, `swoop_intent_score`, `swoop_total_lead_score`.
- **scope**:
  - New `crm_agent/agents/specialized/lead_scoring_agent.py` with versioned JSON config (weights, rules).
  - Integrate into enrichment pipeline before updater.
  - Add toggle to seed HubSpot’s native/AI Scoring (no hard dependency).
- **how to test**:
  - Unit tests: deterministic inputs → expected scores.
  - E2E: pipeline writes scores into HubSpot via Phase 3 tools.
- **acceptance**:
  - Scores appear on Companies/Deals; re‑runs stable given same inputs.

### Phase 7 — Outreach personalizer agent
- **goal**: Generate grounded, role‑aware drafts and create Email/Task engagements.
- **scope**:
  - New `crm_agent/agents/specialized/outreach_personalizer_agent.py`.
  - Use facts and citations from Phase 1; role taxonomy from config; save Email draft + review Task via OpenAPI tools.
- **how to test**:
  - For a test Company + GM contact, generate draft; confirm Email engagement and Task in HubSpot with correct associations.
- **acceptance**:
  - Drafts include citation‑backed hooks; tasks routed with due dates; nothing sends automatically.

### Phase 8 — Role taxonomy, policy, and provenance enforcement
- **goal**: Make roles consistent, safe, and auditable.
- **scope**:
  - Centralize title→role synonyms in `crm_agent/configs/` and load at startup; emit `role_confidence`.
  - ADK policy callbacks: robots.txt, throttling, no paywall bypass, avoid email scraping; PII tagging.
  - “If role_confidence < threshold, open review task instead of write.”
- **how to test**:
  - Unit tests for title normalization.
  - Negative tests: restricted sites are skipped; low‑confidence opens review tasks.
- **acceptance**:
  - Role labels accurate; unsafe or low‑confidence paths diverted to human review.

### Phase 9 — Observability, idempotency, and session/state
- **goal**: Make it production‑ready and support reliable retries.
- **scope**:
  - Structured logging with `trace_id` and session/job IDs end‑to‑end.
  - Idempotency keys on all HubSpot writes; deterministic retries.
  - Replace in‑memory session with pluggable store (e.g., Redis) behind current interface.
  - Audit trail: before/after + evidence URLs for each applied change.
- **how to test**:
  - Simulate partial failures; verify retries don’t duplicate.
  - Restart mid‑task; confirm resume via session store.
- **acceptance**:
  - Traces link every tool call; repeated runs are safe; state survives process restarts.

### Phase 10 — HubSpot CRM UI Extension (card)
- **goal**: Surface facts, citations, roles, and scores inside HubSpot.
- **scope**:
  - Add `docs/hubspot_ui_extension/` scaffold; implement minimal card that reads from Company/Contact properties.
  - Display: course facts + source links + last verified, role chips, lead score, “Suggested opener” action.
- **how to test**:
  - Install extension in a sandbox portal; open a test Company; validate data renders correctly.
- **acceptance**:
  - Card loads quickly; shows expected properties with links and timestamps.

### Phase 11 — Remote A2A partner integrations (optional)
- **goal**: Consume external A2A agents (e.g., address/phone verification, event intel).
- **scope**:
  - Add `RemoteA2aAgent` abstraction; feature‑flagged usage in coordinator.
  - Extend Agent Card to include dependency declarations/versioning constraints.
- **how to test**:
  - Mock remote agent and a real one where available; verify fallbacks and error mapping to lifecycle.
- **acceptance**:
  - Remote calls degrade gracefully; provenance and policy still enforced.

### Notes on sequencing and cutlines
- **shipping points**: Value after Phase 3 (basic sync); major value after Phases 6–7 (lead scoring + outreach).
- **parallelization**: Phases 8–9 can run in parallel with Phase 10.

### Minimal per‑phase “done” checklist
- **conda**: `conda activate adk`.
- **model**: Use `gemini-2.5-flash` in new agents/workflows.
- **tests**: Add small, representative tests (unit or smoke) that run in CI.
- **docs**: Provide a short “how to run” snippet in each new module’s docstring or `docs/`.


