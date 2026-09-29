# Foresight 🛡️

[![Deployment Status](https://img.shields.io/badge/Deploy-Live%20on%20Render-200052?style=for-the-badge&logo=render&logoColor=white)](https://foresight-05ok.onrender.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15%20App%20Router-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Hindsight Memory](https://img.shields.io/badge/Memory-Hindsight%20Cloud-7C5CFF?style=for-the-badge)](https://hindsight.vectorize.io/)

> **Tagline:** *Hindsight remembers. Foresight prevents.*

**🚀 Live Application URL:** [https://foresight-05ok.onrender.com](https://foresight-05ok.onrender.com)

## 📖 About Foresight

Foresight is an intelligent **AI Deploy-Safety Agent** purpose-built for fintech, payments, and mission-critical engineering teams. Before a high-risk PR or configuration change ships to production, Foresight automatically inspects the diff against the organization's complete deploy history and incident postmortems stored in **Hindsight memory**.

### The Core Problem
Without long-term institutional memory, standard AI code review tools generate generic, repetitive advice such as *"ensure adequate unit test coverage and deploy via canary."*

### The Foresight Solution
With **Hindsight memory**, Foresight evaluates risk with exact historical precedents and evidence:

> 🚨 **Critical Risk Warning:** *"You are reducing the payment retry timeout from 30s to 8s. An identical retry timeout change triggered SEV-1 double-debit outages on Aug 12 (INC-2024-001) and Sep 3 (INC-2024-002). A quick rollback resolved the outage in 38 minutes, but configuration drift reintroduced the bug 9 days later. **Verdict: HOLD.** Ship only with mandatory idempotency key enforcement and a multi-stage canary rollout."*

---

## ✨ Key Features & Capabilities

- 🛡️ **Deploy Safety Evaluator (`/check`):** Analyzes proposed PR diffs, service context, and config changes to generate a 0–100 risk score, verdict badge (`SHIP`, `CANARY`, `HOLD`), canary plan, and rollback strategy.
- 🧠 **Hindsight Memory Bank:** Retains postmortems, temporary fixes, deploy logs, and resolution outcomes, establishing real causal links between code changes and outages.
- 🔄 **Memory OFF / ON Comparison:** Interactively compare generic LLM responses (Memory OFF) against evidence-backed, cited risk briefs (Memory ON).
- 💬 **Ask Foresight AI (`/ask`):** A conversational streaming intelligence interface powered by Hindsight recall to query past incidents, failed fixes, and root causes.
- 📈 **Learning Curve & Analytics (`/insights`):** Visualizes risk prediction accuracy growth and Mean Time to Resolve (MTTR) reductions as institutional memory expands over time.
- 🔍 **Memory Inspector:** Inspect raw recalled incident memories, relevance scores, and metadata citations directly inside the UI.
- 🚨 **Incident Resolution Engine (`/incident`):** Ranks historical fix strategies when active alerts fire, and drafts postmortems for one-click retention upon incident resolution.
- 🧰 **CLI & GitHub Action Guard:** Integrates seamlessly into CI/CD pipelines via `foresight check` CLI and `.github/actions/foresight` PR status checks.

---

## 🏗️ Architecture & Technical Design

```mermaid
graph TD
    subgraph Clients & Integrations
        A[Next.js 15 Frontend UI]
        B[Foresight CLI]
        C[GitHub Action PR Guard]
    end

    subgraph Backend Engine [FastAPI + SQLModel]
        D[API Router /api/v1]
        E[Deploy Safety Evaluator]
        F[Incident Resolution Engine]
        G[Analytics & Learning Curve]
    end

    subgraph Memory & Reasoning
        H[(Hindsight Cloud Bank)]
        I[Groq API: GPT-OSS-120B / GPT-OSS-20B]
    end

    A -->|HTTP / JSON| D
    B -->|HTTP / JSON| D
    C -->|HTTP / JSON| D

    D --> E
    D --> F
    D --> G

    E -->|retain & recall| H
    E -->|JSON reasoning| I
    F -->|retain postmortems| H
    G -->|aggregate metrics| D
```

### Tech Stack Breakdown
- **Backend Framework:** Python 3.11+, FastAPI, Pydantic v2, SQLModel (SQLite structured persistence), `httpx`, `tenacity`.
- **Memory Infrastructure:** [Hindsight Cloud](https://hindsight.vectorize.io/) via the official Python SDK (`hindsight-client`, installed for live deployments).
- **LLM Reasoning Engine:** Groq API featuring `openai/gpt-oss-120b` (Primary) and `openai/gpt-oss-20b` (Fallback) with strict JSON schema validation.
- **Frontend Stack:** Next.js 15 (App Router), TypeScript, Tailwind CSS, TanStack Query, Framer Motion, Recharts, Lucide Icons.
- **Deployment Platform:** Render single-service Docker Blueprint running the Next.js standalone frontend and FastAPI backend.

---

## 💡 How Hindsight Memory Works

Hindsight acts as the core memory engine behind Foresight. Each engineering organization operates a dedicated memory bank (e.g. `foresight-paynest`).

### Core Hindsight SDK Operations

1. **`retain` (Ingesting Incidents & Postmortems):**
   ```python
   hindsight.retain(
       bank_id="foresight-paynest",
       content="[INC-2024-001] Gateway timeout reduction from 30s to 8s caused downstream retry storm and double debits...",
       document_id="INC-2024-001",
       tags=["payments-gateway", "SEV-1", "retry_storm"],
       metadata={"service": "payments-gateway", "root_cause": "retry_storm"}
   )
   ```

2. **`recall` (Retrieving Relevant Precedents):**
   ```python
   memories = hindsight.recall(
       bank_id="foresight-paynest",
       query="payments-gateway retry timeout GATEWAY_RETRY_TIMEOUT_MS=8000",
       tags=["payments-gateway"]
   )
   ```

3. **`reflect` (Synthesizing Risk Verdicts):**
   Synthesizes evidence-driven verdicts backed by cited postmortems, failed fixes, and temporary workaround durations.

---

## 📊 Before & After: Memory OFF vs Memory ON

| Analysis Metric | Memory OFF (Generic LLM) | Memory ON (Hindsight + LLM) |
| --- | --- | --- |
| **Safety Verdict** | `CANARY` (Risk Score: 45/100) | `HOLD` (Risk Score: 87/100) |
| **Risk Summary** | "Retry timeout reduced. Ensure upstream service handles retries." | **CRITICAL RISK:** Lowering timeout to 8s matches identical changes that caused SEV-1 double-debit outages on Aug 12 & Sep 3. |
| **Past Precedents** | 0 Citations (No historical context). | Cited **INC-2024-001** & **INC-2024-002** with similarity reasons and fix outcomes. |
| **Actionable Guidance** | "Run standard unit tests." | "Rollback timeout to >=25s, enforce client idempotency keys, and deploy only via canary." |

---

## ⚡ Quickstart & Local Setup

### Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** 18.0 or higher & `npm`

### 1. Repository Setup
```bash
git clone https://github.com/your-username/foresight.git
cd foresight
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default offline configuration (`FORESIGHT_MODE=offline`) requires no external API keys and runs deterministically:
```env
FORESIGHT_MODE=offline
API_KEY=foresight-secret-key-123
HINDSIGHT_BANK_ID=foresight-paynest
```

### 3. Backend Setup
```bash
# Install backend package in editable mode with dev dependencies
pip install -e ".[dev]"

# Launch FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation available at: `http://localhost:8000/docs`.

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`.

---

## 🛠️ Integrations & CLI Usage

### Foresight CLI
Install the CLI tool locally:
```bash
pip install -e cli/
```

Run an automated deploy-safety check against a diff file:
```bash
foresight check \
  --service payments-gateway \
  --title "Lower gateway retry timeout from 30s to 8s" \
  --diff ./change.diff
```
*CLI Exit Codes:* `0` = `SHIP`, `1` = `CANARY`, `2` = `HOLD`.

### GitHub Action Integration
Add Foresight to your workflow (`.github/workflows/foresight.yml`):
```yaml
uses: ./.github/actions/foresight
with:
  api_key: ${{ secrets.FORESIGHT_API_KEY }}
  service: "payments-gateway"
  fail_on_hold: "true"
```

---

## 🎬 90-Second Product Walkthrough Script

1. **Seed Memory:** Navigate to `/demo` and click **"Run Demo Replay"** to populate 20 incident postmortems and 40 deploy records into Hindsight memory.
2. **Run Friday 5:40 PM Safety Check:** Go to `/check`, select the example *"Friday 5:40 PM: Gateway Retry Timeout Reduction"*, and click **"Run Safety Check"**.
3. **Inspect Verdict:** Review the `HOLD` verdict, 87/100 risk score, and real citations pointing to past SEV-1 double-debit incidents.
4. **Toggle Memory OFF:** Switch the **"Memory ON"** toggle at the top to **"Memory OFF"** and click **"Re-run Check"** to see how a generic LLM misses the critical incident history.
5. **Ask Foresight AI:** Head to `/ask` and click the chip *"What broke last time we changed retry timeouts?"* to watch real-time streaming answers powered by Hindsight recall.
6. **Analyze Learning Curve:** Visit `/insights` to view how prediction accuracy improves as team memory grows over time.

---

## 🐳 Docker & Production Deployment

### Docker Compose
Run both frontend and backend services locally:
```bash
docker compose up --build
```
- **Frontend UI:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`

### Live deployment on Render
The root `render.yaml` deploys the Next.js frontend and FastAPI backend together as one Docker web service. Production uses `FORESIGHT_MODE=live`, installs the optional Hindsight SDK, and proxies `/health` and `/api/*` to the local FastAPI process. In the Render service's **Environment** tab, set these exact names (case-sensitive):

| Variable | Value |
| --- | --- |
| `FORESIGHT_MODE` | `live` |
| `HINDSIGHT_API_KEY` | Active Hindsight Cloud API key (secret) |
| `HINDSIGHT_API_URL` | `https://api.hindsight.vectorize.io` |
| `HINDSIGHT_BANK_ID` | The bank containing the incident data; defaults to `foresight-paynest` |
| `GROQ_API_KEY` | Active Groq API key (secret) |
| `GROQ_PRIMARY_MODEL` | `openai/gpt-oss-120b` |
| `GROQ_FALLBACK_MODEL` | `openai/gpt-oss-20b` |

`HINDSIGHT_BASE_URL` is accepted as a legacy alias for `HINDSIGHT_API_URL`; prefer the latter and do not set conflicting URLs. `API_KEY` is the Foresight API's separate request-auth key, not either provider key.

If the frontend is deployed separately, its build environment needs `NEXT_PUBLIC_API_BASE_URL=https://<backend-service-host>` and (if the backend `API_KEY` differs from the public default) `NEXT_PUBLIC_API_KEY` equal to that request-auth key. These `NEXT_PUBLIC_*` values are bundled into browser code and are not provider secrets. Groq and Hindsight credentials belong only in the backend service environment.

The Render Blueprint declares the two provider keys with `sync: false`; enter them as secrets in the Render Environment tab rather than committing them. The health response reports which providers are configured and names missing keys without exposing values. Live provider request failures are returned/logged explicitly; deterministic seed data is used only for offline mode or when live credentials are genuinely absent.

The Blueprint uses Render's free service plan. Free services can sleep when idle, and the container filesystem is ephemeral, so SQLite/demo state may reset after a restart or redeploy. `data/seed/` contains synthetic example records; do not use those as production incident history.

---

## ⚖️ Synthetic Data & License

- **Data Disclaimer:** All incidents and deploys under `data/seed/` are synthetic and pattern-based, inspired by public postmortems adapted for the fictional **PayNest** payments platform.
- **License:** Open Source under the MIT License.
