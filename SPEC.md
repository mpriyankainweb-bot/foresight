1. Product
Foresight is an AI deploy-safety agent for payments and fintech engineering teams. Its tagline is: Hindsight remembers. Foresight prevents.
Before a risky change ships, Foresight reads the change and compares it against the team's full incident history, kept in Hindsight memory. It answers: "Should we ship this, and if not, why?" When an incident does happen, it recalls what fixed similar incidents, what failed, and which fixes only held temporarily.
Why memory is the core: Without memory the agent gives generic advice like "add tests and use canary." With memory it says "You changed the payment retry timeout. The same class of change caused double-debits on Aug 12 and Sep 3. Rollback fixed it in 38 minutes, but the config drift returned 9 days later. Ship only with a canary and an idempotency-key check."
2. Persona and demo story
Persona: Arjun, backend engineer at PayNest, a fictional UPI and card payments company handling 2M transactions a day.
Friday, 5:40 PM. Arjun opens a PR that lowers the gateway retry timeout from 30s to 8s.
Foresight shows risk 87/100, HOLD, with cited past incidents, a canary plan, and a rollback plan.
Arjun ships anyway with the canary. Foresight catches the success-rate dip early. The outcome is retained. The next similar change is judged with even higher confidence.
Dashboard shows the learning curve: risk-prediction accuracy up and mean time to resolve (MTTR) down as memory grows.
A Memory OFF / ON toggle re-runs the same check without memory (generic answer) and with memory (specific, cited answer).
3. Tech stack (do not substitute)
Backend: Python 3.11, FastAPI, Pydantic v2, SQLModel with SQLite (structured records only), httpx, tenacity for retries, pytest.
Memory: Hindsight (Hindsight Cloud) via the official Python SDK. Verify the exact package name, client class, and method signatures against https://hindsight.vectorize.io/ and https://github.com/vectorize-io/hindsight before coding. Do not guess the API. If the SDK differs from this spec, follow the docs and note it in the README.
LLM: Groq API, primary model openai/gpt-oss-120b, fallback openai/gpt-oss-20b. Wrap all calls in a resilient client (see section 6).
Frontend: Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, Recharts, Lucide icons, TanStack Query.
Integrations: REST API with API-key auth, a CLI (foresight check), a GitHub Action, and an optional Slack webhook.
Deploy targets: Vercel for the frontend, Render or Railway for the backend, plus a docker-compose.yml for local runs.
4. Hindsight memory design (the star of the project)
Use one memory bank per organization, for example foresight-paynest. Configure the bank with a clear background and a retain mission such as: "Remember deploys, incidents, root causes, fixes attempted, whether each fix worked, whether it held, and the engineering context around them. Prioritize causal links between changes and outages."
What gets retained (via retain):
Incident postmortems. Full text with metadata: service, severity, root cause class, detection time, resolution time, blast radius.
Fix attempts. Each attempt with outcome: worked, failed, or temporary, and how long it held.
Deploy records. Change summary, files touched, config keys touched, and the outcome afterward (clean, degraded, incident).
Engineer feedback. "Was this warning useful?" and "Was this fix helpful?"
Every Foresight verdict and what actually happened next (this is how the agent learns its own accuracy).
Use tags for service, environment, and incident id, and use context labels so recall can filter.
How memory is used:
recall before every deploy check: query with the change description and touched config keys. Return the raw memories to the UI as citations.
reflect to produce the risk brief, with the bank disposition set to cautious and evidence-driven.
After every incident and deploy outcome, retain the result so the next verdict improves.
Build a "Memory Inspector" in the UI showing exactly which memories were recalled for each verdict.
The bank must never be a hidden implementation detail. Judges must see it working.
5. Backend API
All routes under /api/v1. All accept and return JSON. Require an X-API-Key header except /health and demo-mode routes.
POST /deploys/check: input {service, title, description, diff (optional), config_changes[], environment, author}. Output {risk_score 0-100, verdict SHIP|CANARY|HOLD, summary, reasons[], similar_incidents[{id, title, date, similarity_reason, fix_that_worked, fix_that_failed, held_for_days}], canary_plan, rollback_plan, memory_citations[], memory_used: bool, check_id}.
POST /deploys/{check_id}/outcome: input {outcome: clean|degraded|incident, notes}. Retains the outcome.
POST /ask: input {question}. Output streams memory citations and answer synthesized from Hindsight recall + LLM reasoning (no hardcoded rules).
POST /incidents: create an incident from alerts and logs. Returns ranked fix suggestions from memory.
POST /incidents/{id}/fix-attempts: log a fix attempt with outcome.
POST /incidents/{id}/resolve: close the incident, generate a postmortem draft, and retain it.
GET /memory/search?q=: proxies Hindsight recall for the Memory Inspector.
GET /analytics/learning-curve: series of prediction accuracy and MTTR over time.
POST /demo/replay: replays the seeded incident timeline into memory step by step for the demo.
POST /demo/reset: clears demo state.
GET /health.
Error handling: return structured errors {error: {code, message}}. Handle Hindsight downtime by degrading gracefully (verdict marked memory_used: false with a visible banner), never crashing.
6. LLM layer requirements
One LLMClient class with: primary model, fallback model, retry with exponential backoff (tenacity), timeout, and rate-limit handling.
Function-calling and JSON-output errors are common on these models. Always request strict JSON, validate with Pydantic, and on failure retry once with a repair prompt, then fall back to the second model, then return a safe degraded response.
Never trust model output. Clamp risk_score, validate enums, and drop citations that do not map to real recalled memories (no hallucinated incidents).
Log token usage and latency per call.
7. Frontend: design and UX (must feel premium)
Visual language: dark, calm, serious, "mission control for deploys." Supports a light/dark theme toggle with a polished light palette, defaulting to the system preference.
Colors (Dark): background #0B0D12, surface #12151C, border #1F2430, primary #7C5CFF, danger #FF4D6D, warning #FFB020, success #2DD4A0, text #E6E8EE, muted #8A90A2.
Colors (Light): background #F8FAFC, surface #FFFFFF, border #E2E8F0, primary #6366F1, danger #EF4444, warning #F59E0B, success #10B981, text #0F172A, muted #64748B.
Fonts: Inter for UI, JetBrains Mono for code and logs. Generous spacing, 12-16px rounded corners, subtle glow on primary elements, soft gradients only in hero areas.
Motion: Framer Motion for the risk gauge sweep, staggered card entrance, and smooth drawer transitions. Respect prefers-reduced-motion.
Fully responsive down to a tablet, keyboard accessible, visible focus states, WCAG AA contrast.
Pages:
Landing (/): hero with the tagline, a 20-second looping demo animation, "Try the live demo" button, three value cards (Prevent, Recall, Learn), and an integration snippet.
Deploy Check (/check): the main screen. Left: form with change title, service, description, diff textarea, config changes, plus a "Load example" dropdown. Right: results with an animated risk gauge, verdict badge, reasons, similar past incidents as expandable cards (with "fix that worked" in green and "fix that failed" in red), canary plan, rollback plan, and copy buttons. Include the Memory OFF / ON toggle at the top.
Memory Inspector: a right-side drawer available on every screen showing recalled memories for the current verdict, with entity chips, dates, and relevance.
Incident Mode (/incident): paste alerts or logs, get ranked fixes from memory, log fix attempts, one-click resolve with postmortem draft.
Learning Curve (/insights): Recharts line charts of MTTR and prediction accuracy over time, memory growth counter, top recurring root causes, and a "fixes that only held temporarily" list.
Ask Foresight (/ask): chat UI for asking questions about past deploys, outages, and temporary fixes. Each answer is generated from Hindsight recall + LLM reasoning, displays memory citations, and streams the response. Features suggested prompt chips: "What broke last time we changed retry timeouts?", "Which fixes only held temporarily?".
Integrate (/integrate): API key generator, cURL and Python and JS snippets, GitHub Action YAML, CLI usage, all with copy buttons.
Demo Control (/demo): Replay button that plays the seeded timeline with a progress bar and live memory counter, plus a reset button.
Every screen needs proper loading skeletons, empty states with helpful copy, and clear error states. No lorem ipsum anywhere.
8. Data
20 incidents for PayNest across 12 months, each with: title, date, service, severity, root cause class, alert text, realistic error logs, Slack war-room excerpts, fix attempts (including failures and temporary fixes), resolution time, and a recurrence link where applicable.
40 past deploys with outcomes, including the ones that caused incidents.
Root causes must be based on real public postmortems (retry storms, bad config pushes, expired certificates, connection pool exhaustion, idempotency failures, DB failover issues, rate-limit misconfig). Source inspiration: https://github.com/danluu/post-mortems . Do not copy text verbatim. Adapt patterns into the fictional PayNest setting.
Plant a recurring pattern across three incidents (retry timeout changes causing double-debits) so the demo climax is genuine.
Provide a scripts/generate_seed.py that can regenerate the data using the LLM, and commit the generated JSON as well.
Clearly mark data as synthetic and pattern-based in the README.
9. Integrations
REST: documented with OpenAPI at /docs.
CLI: pip install -e cli/ gives foresight check --service payments-gateway --title "..." --diff ./change.diff, exit code 0 for SHIP, 1 for CANARY, 2 for HOLD.
GitHub Action: .github/actions/foresight that runs on pull requests, posts a comment with the verdict and citations, and can fail the check on HOLD.
Slack (stretch): incoming webhook posting verdicts.
10. Quality bar
Clean architecture: routers/, services/, memory/, llm/, models/, seed/.
Type hints everywhere, ruff and mypy config, ESLint and Prettier for the frontend.
Tests: pytest for the verdict logic, LLM output repair, and the memory client (mocked), plus one end-to-end test of the demo replay.
Edge cases: empty diff, huge diff (truncate safely), Hindsight unavailable, Groq rate limit, malformed model output, duplicate retains, concurrent replay clicks.
Security: keys only from environment variables, .env.example provided, input size limits, CORS restricted.
README: problem, architecture diagram (Mermaid), a dedicated "How Hindsight memory is used" section with the exact retain, recall, and reflect calls and the before/after comparison, setup steps, demo script, and screenshots.
11. Definition of done
A judge can open the app, click "Run demo replay," watch memory grow, run the Friday-5:40 deploy check, see a cited HOLD verdict, flip Memory OFF to see the generic answer, and view the learning curve. All within 90 seconds, with no errors.
