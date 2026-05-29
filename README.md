# Power BI Governance Agent

An agentic AI app that audits a Power BI tenant for governance and lineage issues using Claude and the Power BI REST / Scanner APIs.

Built with Python, Streamlit, and the Anthropic API. Runs against mock Power BI data — swap the mock functions for real API calls to connect to a live tenant.

---

## Features

### Phase 1 — Governance Scan
- Flag stale workspaces (90+ days inactive)
- Flag orphaned workspaces (no assigned users)
- Flag empty workspaces (no datasets or reports)
- Flag stale datasets (90+ days since last refresh)
- Gateway and datasource audit

### Phase 2 — Scanner API (Lineage & Impact)
Full 4-step async Scanner API flow:
1. `GetModifiedWorkspaces` — which workspaces need scanning
2. `PostWorkspaceInfo` — submit scan, receive a `scanId`
3. `GetScanStatus` — poll until `Succeeded`
4. `GetScanResult` — pull metadata (datasource lineage, sensitivity labels, endorsement)

Derived tools built on the scan result:
- **Lineage** — full upstream/downstream chain for any dataset
- **Impact analysis** — what reports and datasets break if a datasource changes
- **Sensitivity label audit** — datasets and reports missing a label
- **Endorsement audit** — uncertified / unendorsed datasets

---

## How the agent works

```
You → task description
        ↓
    Claude reads task + available tools
        ↓
    Claude calls tools in the order it decides
        ↓
    Results appended to message history
        ↓
    ... repeats until Claude has enough data ...
        ↓
    Claude writes the governance report
        ↓
    You ← structured report with recommendations
```

Claude controls the sequence — you don't specify which tools to call or in what order.

---

## Project structure

```
.
├── app.py                 # Streamlit UI
├── agent.py               # Agentic loop (Claude + tool routing + token tracking)
├── tools.py               # Phase 1 governance tool schemas and handlers
├── scanner_tools.py       # Phase 2 Scanner API tool schemas and handlers
├── mock_powerbi_data.py   # Mock Power BI REST API responses
└── mock_scanner_api.py    # Mock Scanner API responses (8 workspaces)
```

---

## Setup

**Prerequisites:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com)

```bash
git clone https://github.com/swapnil-hoderkar/powerbi-governance-agent.git
cd powerbi-governance-agent

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install anthropic streamlit
```

---

## Running

```bash
streamlit run app.py
```

Open http://localhost:8501, enter your Anthropic API key, choose a scan mode and preset, then click **RUN SCAN**.

Token usage (input, output, total) is displayed after each run.

---

## Moving to production

Each mock function has a comment showing the real Power BI REST endpoint it maps to. To connect to a live tenant:

1. Obtain an Azure AD access token with `Tenant.Read.All` / `Dataset.Read.All` scopes
2. Replace the body of each function in `mock_powerbi_data.py` and `mock_scanner_api.py` with a `requests.get` / `requests.post` call to the documented endpoint
3. Pass the bearer token in the `Authorization` header
4. The agent logic in `agent.py` does not change — only the data source does

---

## Governance rules

Rules are encoded in the system prompt in `agent.py`. Current defaults:

| Rule | Threshold |
|---|---|
| Stale workspace | No activity for 90+ days |
| Orphaned workspace | No assigned users |
| Empty workspace | No datasets or reports |
| Stale dataset | Not refreshed for 90+ days |

Edit the `SYSTEM_PROMPT` string in `agent.py` to add or adjust rules without touching any other code.
