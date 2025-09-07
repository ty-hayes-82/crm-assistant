## A2A-Compliant CRM Agent Framework Strategy (HubSpot + ADK)

### 0) What “A2A‑compliant with ADK” means
Being A2A‑compliant with ADK means your local sub‑agents do fast, in‑process tasks (e.g., parsing and normalization), while remote agents are exposed and consumed over the Agent‑to‑Agent protocol using an Agent Card that advertises capabilities, schemas, and auth. Remote calls use JSON‑RPC/gRPC/HTTP, support streaming updates, and follow standardized task lifecycle and error semantics. ADK provides first‑class primitives to decide when to keep logic as a local sub‑agent versus when to expose it remotely, and it includes simple providers for both running services (A2AServer) and consuming others (RemoteA2aAgent), so agents can interoperate cleanly with policy, observability, and versioning built in.

---

## 1) Target CRM model in HubSpot

### Core objects & properties

- **Company = Golf course / country club**
  - **Key properties (customs in bold)**: name, domain, website, phone, address, **swoop_course_type** (resort/private/muni), **swoop_holes** (9/18/27), **swoop_par**, **swoop_course_rating**, **swoop_slope**, **swoop_booking_engine** (TeeSheet/Booking URL), **swoop_management_company**, **swoop_amenities** (range, lessons, dining, events), **swoop_unique_hook** (copy‑ready highlight), **swoop_site_last_verified_at**, **swoop_source_urls** (JSON array). Manage these as Company properties via the CRM Objects API.

- **Contacts**
  - email, firstname, lastname, phone, jobtitle, **swoop_role_taxonomy** (GM, Director of Golf, Head Pro, Superintendent, Membership Director, F&B, Owner/Board), **swoop_decision_tier** (D1 decision‑maker / D2 influencer / D3 champion), **swoop_personalization_snippet**, **swoop_verified_from** (URL), **swoop_last_verified_at**.

- **Associations & labels (important!)**
  - Use Association Labels between Contact↔Company (e.g., GM, Head Pro, Superintendent) and Contact↔Deal (e.g., Decision Maker, Economic Buyer, Champion). This makes roles reportable and first‑class.

- **Deals (contracts)**
  - close_date, amount, **swoop_contract_type** (new/renewal/expansion), **swoop_renewal_date**, **swoop_risk_flag** (R/A/G), **swoop_fit_score**, **swoop_intent_score**, **swoop_total_lead_score**.

- **(Optional) Custom objects**
  - If you outgrow company properties, HubSpot supports objectTypeId‑based endpoints with the same CRUD pattern for custom objects (e.g., a distinct Course object linked to a parent Company).

### HubSpot integration surfaces

- **Auth**: Private App token (or OAuth) with granular scopes (contacts/companies/deals/associations/emails/tasks read/write).
- **CRM UI Extensions**: Show a “Course Intelligence” card on Company/Contact records (facts + citations + suggested outreach).

---

## 2) The Agent Team (ADK)

### 2.1 Root Orchestrator (local ADK workflow agent)
- Coordinates the pipeline; maintains session state (job id, object ids, provenance). Delegates tasks to sub‑agents or remote A2A agents.
- Uses ADK callbacks for guardrails (e.g., block scraping behind paywalls; enforce robots.txt).

### 2.2 Web Discovery Agent (local + Search Grounding)
- Finds the official course site and relevant pages (About, Staff, Membership, Events).
- Uses Google Search Grounding; stores groundingMetadata (citations) on each extracted field.

### 2.3 Site Reader & Extractor (local + function tools)
- Fetches pages (respect robots.txt), extracts structured data from HTML (JSON‑LD, Microdata). Prioritize schema.org/GolfCourse when present, then fall back to LLM extraction.
- Outputs a typed JSON payload aligned to your HubSpot property schema.

### 2.4 Contact & Role Inference Agent (local)
- Parses “Staff/Team” pages and press releases to extract names/titles/emails where public; never guess emails.
- Normalizes titles to the Swoop role taxonomy; assigns Decision Tier based on patterns/heuristics.
- Associates contacts to the company using Association Labels.

### 2.5 Data Quality & Provenance Agent (local)
- Cross‑checks claims; dedupes by domain/address; enforces “must have URL + last_verified_at”.
- Writes a field‑level source_urls array; persists grounding metadata returned by ADK grounding.

### 2.6 HubSpot Sync Agent (local, via ADK OpenAPI tool)
- Uses HubSpot’s OpenAPI to autogenerate tools for Companies, Contacts, Associations, Emails, Tasks.
- Creates/updates Companies & Contacts, sets custom props, creates association labels, and logs emails/tasks.

### 2.7 Lead Scoring Agent (local)
- Computes Fit and Intent into **swoop_total_lead_score**; can seed HubSpot’s AI Scoring or native scoring properties.

### 2.8 Personalized Outreach Agent (local, LLM)
- Generates email drafts and call notes tailored to course highlights and contact roles.
- Saves drafts as Email engagements and creates Tasks for reps to review/send.

### 2.9 Optional Remote A2A Agents (vendor/partner integrations)
- Data Enrichment Agent (A2A): external verification of addresses/phones; exposed via Agent Card; consumed via RemoteA2aAgent.
- Event Intelligence Agent (A2A): pulls tournament/event data for personalization hooks.

---

## 3) End‑to‑End Flow

1. **Seed**: Company domain or name/state.
2. **Discovery**: Search Grounding finds the official site; Site Reader fetches About/Staff/Membership pages; Extractor composes structured fields, with citations.
3. **Contacts & Roles**: Extract names/titles/emails (if public); map to taxonomy; add Association Labels.
4. **Quality Gate**: Confidence thresholds; provenance checks; normalization.
5. **HubSpot Sync**: Upsert Company/Contacts; apply props/labels; log notes; attach source URLs; create tasks for low‑confidence items.
6. **Lead Scoring**: Write **swoop_fit_score**, **swoop_intent_score**, **swoop_total_lead_score**; optionally configure HubSpot’s AI or rule‑based scores.
7. **Outreach**: Draft personalized emails and talking points; save as Email engagements and Tasks.
8. **UI Extension**: On a Company/Contact record, show a “Course Intelligence” card (facts + links + opener).

---

## 4) A2A compliance notes (design checklist)

- **Expose internal services** as an A2A Server with an Agent Card describing skills, methods, and auth; **Consume external agents** with RemoteA2aAgent.
- **Transports**: JSON‑RPC 2.0 over HTTPS; SSE streaming for long tasks; handle task lifecycle (queued → running → completed/failed) with standardized errors.
- **Security**: OAuth/mTLS per Agent Card; never embed secrets in the card; enforce scope‑limited tokens.
- **Interoperability**: Keep requests/outputs to typed data parts (facts with URLs and timestamps) so clients map them to HubSpot properties.

### Mini Agent Card sketch (JSON)
```json
{
  "protocolVersion": "0.3.0",
  "name": "Swoop Course Intel",
  "skills": [
    {
      "id": "course.profile.extract",
      "inputSchema": {
        "type": "object",
        "properties": {"domain": {"type": "string"}}
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "companyProps": {"type": "object"},
          "contacts": {"type": "array"},
          "citations": {"type": "array"}
        }
      }
    }
  ],
  "endpoints": {"jsonrpc": "https://intel.swoopgolf.com/a2a/jsonrpc"},
  "auth": {"type": "oauth2", "scopes": ["profile.read", "course.read"]}
}
```

---

## 5) Lead scoring design (fit + intent; written back to HubSpot)

### Fit (0–100) – candidate signals
- Facility size & type (holes, par)
- Management company
- Amenities
- Booking engine
- Location density/competition
- Event hosting
- Seasonality

### Intent (0–100) – candidate signals
- Email/meeting/website engagement already in HubSpot
- Page views of Membership/Events/Leagues
- Replies; task completions

### Rollup
- Total = weighted blend → write to **swoop_total_lead_score**. Keep master rules/config in HubSpot’s native Scoring (and/or AI Scoring) so RevOps can tune without redeploying agents.

---

## 6) Personalized outreach (role‑aware, grounded)

- The Outreach Agent builds a first‑line hook from **swoop_unique_hook** and citations.
- Tone switches by role (GM vs Superintendent vs Head Pro).
- Deliverables: Email engagement drafts + Tasks (due dates, owners). Optional: log WhatsApp/LinkedIn/SMS via Communications APIs.

---

## 7) HubSpot integration details (using ADK OpenAPI tools)

- **Companies**: upsert by domain or fuzzy name+address.
- **Contacts**: upsert by email (preferred); avoid duplicates.
- **Associations**: create Contact↔Company with labels for roles.
- **Emails**: create email engagements with subject/body as drafts; associate to Contact/Company.
- **Tasks**: create review/send tasks; set priority/queue if applicable.
- **Imports API (optional)** for bulk backfills.
- Because HubSpot publishes OpenAPI specs, you can import them into ADK’s OpenAPI tool to auto‑generate callable tools for the above endpoints, keeping auth via Private App or OAuth.

---

## 8) UI inside HubSpot (sales‑friendly)

- CRM UI Extension card on Company/Contact records that shows:
  - Key course facts (holes/par/amenities/management co/booking link) with source links & last verified timestamp.
  - Assigned role and decision tier per associated contacts (chips).
  - Lead score breakdown (fit/intent).
  - “Suggested opener” button to insert the draft outreach into a Timeline Email.

---

## 9) Guardrails, safety & observability

- **Website ethics**: obey robots.txt, throttle requests, never bypass paywalls, avoid scraping obfuscated emails; capture only business‑relevant data made public by the club.
- **Provenance**: store source_urls/last_verified_at; show citations (ADK grounding supplies this).
- **Policy hooks**: ADK callbacks for policy enforcement and PII filtering; log all tool calls.
- **Observability**: ADK logging + tracing integration for end‑to‑end task traces.

---

## 10) Implementation skeletons (illustrative)

### A) ADK Search‑grounded discovery agent (Python)
```python
from google.adk.agents import Agent
from google.adk.tools import google_search

discovery = Agent(
    name="discovery",
    model="gemini-2.5-flash",
    instruction=(
      "Given a golf course name and region, find the official site and "
      "important pages (About, Staff, Membership, Events). Use Google Search. "
      "Return JSON with urls + short summaries and include grounding metadata."
    ),
    tools=[google_search]
)
```

### B) HubSpot tools via OpenAPI in ADK
```python
from google.adk.tools import OpenApiTool

hubspot = OpenApiTool(
  spec_url="https://api.hubspot.com/api-catalog-public/v1/apis",  # or a merged spec
  auth={"type":"bearer", "token_env":"HUBSPOT_TOKEN"}
)

# Example calls: /crm/v3/objects/companies, /contacts, /associations, /emails, /tasks
```

### C) Create an email engagement draft (associate to a contact id)
```text
Endpoint: POST /crm/v3/objects/emails (subject/body, timestamp, associations)
```

### D) Create a task for rep review
```text
Endpoint: POST /crm/v3/objects/tasks (due date, body, owner, association to contact/company)
```

---

## 11) Role taxonomy (starter)

- **Decision makers**: General Manager, Director of Golf, Owner/Board, COO (management co)
- **Influencers/Champions**: Head Golf Professional, Superintendent, Membership Director, F&B Director, Events/Leagues Manager
- Mapped as Association Labels so they’re reportable in HubSpot.

---

## 12) Data extraction cues (to make profiles “enticing”)

- Prefer structured hints on site: schema.org/GolfCourse JSON‑LD (holes/par/amenities/price range), then page text.
- Capture hooks like: host of tournaments, renovated practice facility, Top 100 course, new TrackMan range, junior/ladies programs, wedding venue.

---

## 13) What success looks like (ops checklist)

- 90% of target courses have a Company profile in HubSpot with verified source URLs.
- ≥1 validated role label per Account (GM/Director of Golf prioritized).
- Lead score present on Companies/Deals; pipeline views filtered by score deciles.
- Outreach drafts auto‑logged as Emails + Tasks; reps customize and send.
- UI Extension card live on Company/Contact, showing facts + citations + opener.

---

## Notes & References (key, load‑bearing)

- ADK A2A overview & when to use A2A vs sub‑agents; exposing/consuming remote agents.
- A2A Protocol spec (Agent Card, transports, compliance).
- ADK grounding with Google Search / Vertex AI Search.
- ADK Tools & OpenAPI tools (generate tools from OpenAPI).
- HubSpot APIs: Companies, Contacts, Associations (labels), Emails (engagements), Tasks, Imports; Private apps/OAuth; UI Extensions.
- Lead Scoring (native & AI).
- Schema.org GolfCourse for structured cues.

---

## 14) Current codebase mapping (this repo)

This section maps concrete modules in this repository to the strategy’s agents, orchestrators, and A2A components.

### Orchestrators
- **Root Orchestrator (2.1)** → `crm_agent/coordinator.py`
  - Factory: `create_crm_coordinator()` returns an `LlmAgent` that routes to specialized sub‑agents and workflows (HubSpot‑first routing, clarification, enrichment workflows).
  - Also exposes `create_crm_simple_agent()` for basic operations.

- **Program‑level Orchestrator (project management layer)** → `project_manager_agent/`
  - `project_manager_agent/coordinator.py` → `ProjectManagerAgent` orchestrates complex CRM tasks, toolizes execution, and expects immediate action.
  - `project_manager_agent/interactive_coordinator.py` → `InteractiveProjectManagerAgent` adds chat/UX for live orchestration.
  - `project_manager_agent/hubspot_coordinator.py` → `HubSpotProjectManagerAgent` demonstrates end‑to‑end HubSpot updates (mocked wire‑up; production uses MCP/OpenAPI tools).
  - These orchestrators call the CRM Orchestrator via the A2A wrapper (see A2A section below).

### A2A compliance & adapters
- **A2A Agent Wrapper** → `crm_agent/a2a/agent.py`
  - Class: `CRMA2AAgent` with `async invoke(query, session_id)` and factory `create_crm_a2a_agent()`; runs the CRM coordinator via ADK `Runner`, streams updates, yields final content.
- **A2A Task Bridge** → `crm_agent/a2a/task_manager.py`
  - Class: `CRMAgentTaskManager(AgentExecutor)` bridging an A2A server’s `execute()` to the CRM agent, emitting lifecycle updates.
- **Agent Card scaffold** → `crm_agent/a2a/__main__.py`
  - Function: `build_agent_card()` builds an A2A Agent Card (skills, capabilities, transport, auth placeholders).
- **Alternative wrapper (legacy)** → `crm_agent/a2a_wrapper.py`
  - Class: `CRMAgentA2AWrapper` with `invoke(...)`. Prefer `crm_agent/a2a/agent.py` going forward to avoid duplication.
- **Consumer usage** → `project_manager_agent/coordinator.py`
  - Uses `from crm_agent.a2a_wrapper import create_crm_a2a_agent` in `execute_crm_task_direct(...)` to call CRM over the A2A pattern. Update to `crm_agent.a2a.agent.create_crm_a2a_agent` when convenient for single‑source A2A.

### Agents and workflows (strategy §§2.2–2.6)
- **Web Discovery + Site Reader & Extractor (2.2–2.3)**
  - `crm_agent/agents/workflows/crm_enrichment.py`
    - `create_crm_parallel_retrieval_workflow()` runs `web_retriever`, `linkedin_retriever`, `company_data_retriever`, `email_verifier` in parallel.
  - `crm_agent/agents/specialized/crm_agents.py`
    - Factories: `create_crm_query_builder`, `create_crm_web_retriever`, `create_crm_linkedin_retriever`, `create_crm_company_data_retriever`, etc.

- **Contact & Role Inference (2.4)**
  - `crm_agent/agents/specialized/contact_intelligence_agent.py` (contact analysis)
  - `crm_agent/agents/specialized/field_mapping_agent.py` (map fields/roles to HubSpot properties)
  - `crm_agent/agents/specialized/crm_agents.py` → `create_crm_entity_resolver()` (entity matching)

- **Data Quality & Provenance (2.5)**
  - `crm_agent/agents/specialized/crm_agents.py` → `create_crm_data_quality_agent()`
  - Workflows: `create_crm_data_quality_workflow()` in `crm_agent/agents/workflows/crm_enrichment.py`

- **HubSpot Sync (2.6)**
  - `crm_agent/agents/specialized/crm_agents.py` → `create_crm_updater()` (applies approved updates; uses HubSpot tools)
  - `crm_agent/core/factory.py` registers `crm_updater` with `tools: ["hubspot_tools"]` (MCP/OpenAPI integration point)
  - Example script: `scripts/update_mansion_ridge_direct.py` shows direct `crm/v3` calls (reference for expected payloads)

### Enrichment pipelines
- `crm_agent/agents/workflows/crm_enrichment.py`
  - `create_crm_enrichment_pipeline()` implements the 8‑step pipeline (gap detection → query planning → parallel retrieval → synthesis → entity matching → proposal → human approval → apply updates)
  - `create_crm_quick_lookup_workflow()` for fast summaries
  - `create_crm_parallel_retrieval_workflow()` for concurrent fetches

### Lead Scoring and Outreach (strategy §§2.7–2.8, §5, §6)
- **Lead Scoring Agent**: not present yet. Recommended add: `crm_agent/agents/specialized/lead_scoring_agent.py` that computes `swoop_fit_score`, `swoop_intent_score`, `swoop_total_lead_score`, with write‑back via `crm_updater`.
- **Outreach Agent**: not present yet. Recommended add: `crm_agent/agents/specialized/outreach_personalizer_agent.py` to generate grounded email drafts and create HubSpot Email/Task engagements via tools.

### UI Extension (strategy §8)
- Not in repo yet. Add a `docs/hubspot_ui_extension/` with the card schema and a small server stub when ready.

### Environment and models
- Use conda env `adk` for development and package management.
- Default LLM model across agents: `gemini-2.5-flash` (already configured in orchestrators and agents).

### Quick run pointers
- CRM Orchestrator (local): use `create_crm_coordinator()` from `crm_agent/coordinator.py`.
- A2A CRM Agent (remote‑style): use `create_crm_a2a_agent()` from `crm_agent/a2a/agent.py`.
- Project Manager Orchestrators: instantiate classes in `project_manager_agent/` to coordinate multi‑agent goals and call CRM via A2A wrapper.



## 15) Strategic improvements for crm_agent

These improvements align the current `crm_agent/` implementation with this strategy and make it production‑ready for A2A and HubSpot.

### A) A2A transport, lifecycle, and card
- Implement an actual A2A HTTP server (JSON‑RPC 2.0 + SSE) and wire it to `CRMAgentTaskManager` in `crm_agent/a2a/task_manager.py`.
- Expand the Agent Card (`crm_agent/a2a/__main__.py`) to advertise skills aligned to this doc:
  - `course.profile.extract`, `contact.roles.infer`, `hubspot.sync`, `lead.score.compute`, `outreach.generate`.
- Enforce standardized task lifecycle (queued → running → completed/failed) with error semantics mapped to A2A `TaskState`.
- Add OAuth2/mTLS configuration; remove any secrets from the card.

### B) Consolidate A2A wrappers
- Deprecate `crm_agent/a2a_wrapper.py` and standardize on `crm_agent/a2a/agent.py`.
- Update `project_manager_agent/coordinator.py` to import `create_crm_a2a_agent` from `crm_agent.a2a.agent` for a single, canonical A2A entrypoint.

### C) Grounding, provenance, and policy
- Use ADK Google Search Grounding in the web discovery/retriever, attaching citations (URLs, snippets, timestamps) to each extracted fact.
- Enforce “must have source_urls + last_verified_at” in the Data Quality Agent before HubSpot writes; serialize an evidence pack per field.
- Add ADK policy callbacks: obey robots.txt, throttle, avoid paywall bypass and obfuscated email scraping; add PII tags to gate operations.

### D) HubSpot tools via OpenAPI (replace placeholders)
- Add an `OpenApiTool` configuration for HubSpot in `crm_agent/core/factory.py` (spec URL/env, auth via `HUBSPOT_TOKEN`).
- Generate typed tools for Companies/Contacts/Associations/Emails/Tasks; retire generic `hubspot_tools` placeholders.
- Add optional Imports API support for bulk backfills.

### E) Lead scoring agent (new)
- Create `crm_agent/agents/specialized/lead_scoring_agent.py` implementing Fit + Intent and writing `swoop_fit_score`, `swoop_intent_score`, `swoop_total_lead_score`.
- Back scores with a versioned, externalized JSON config and expose a knob to seed HubSpot’s native/AI Scoring.

### F) Outreach personalizer agent (new)
- Create `crm_agent/agents/specialized/outreach_personalizer_agent.py` to generate grounded, role‑aware drafts.
- Use HubSpot Email/Tasks tools to save drafts and create review tasks.

### G) Role taxonomy and normalization
- Centralize title→role mapping and synonyms in `crm_agent/configs/` and load at startup.
- Emit `role_confidence`; when < threshold, open a review task rather than writing directly.

### H) Observability and idempotency
- Add structured logging with `trace_id` and session/job IDs across agents; emit metrics (latency, tokens, API counts).
- Use idempotency keys and deterministic retries for all HubSpot writes; store an audit trail (before/after, evidence URLs).

### I) Session and state
- Swap `InMemorySessionService` for a pluggable session store (e.g., Redis) while keeping the interface.
- Persist session state fields: job id, object ids, evidence, thresholds used, and routing decisions.

### J) Refactors and quality
- Break up `field_enrichment_manager_agent.py` into focused modules (extraction, validation, application) to simplify maintenance and testing.
- Add validation schemas (Pydantic/JSON Schema) for agent inputs/outputs to enforce the contract‑first approach.

### K) Remote A2A agent consumption (optional)
- Add a `RemoteA2aAgent` consumer abstraction to call vendor services (e.g., address/phone verification, event intelligence). Surface them in the coordinator behind feature flags.
