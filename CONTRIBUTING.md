# Contributing to HoneyNet

Thank you for your interest in contributing to **HoneyNet**! We welcome contributions from cybersecurity researchers, backend engineers, frontend developers, and AI/ML enthusiasts.

---

## 🧭 Code of Conduct & Development Philosophy

1. **Safety First**: HoneyNet generates 100% synthetic decoy honeytokens. Never commit real credentials, production API keys, or live enterprise identities.
2. **Deterministic & Realistic**: Fake assets must be consistent across files within a session (same company name, matching corporate domain, authentic employee rosters).
3. **High-Performance & Low-Latency**: The honeypot response must never block on slow AI calls. Rule-based regex baselines must respond in $< 1\text{ms}$; AI enrichment is bounded by strict timeouts.
4. **Code Quality**:
   - Backend: Python 3.10+, strict Pydantic v2 schemas, type annotations, and structured JSON logs.
   - Frontend: Next.js 16 (App Router), TypeScript strict mode (no `any`), TanStack Query, and Zod validation.

---

## 🛠️ Local Development Setup

### 1. Fork & Clone Repository
```bash
git clone https://github.com/<your-username>/honeynet.git
cd honeynet
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend test verification
python -c "from backend.db import init_db; init_db(); print('Database OK')"
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running the Full Stack
```bash
# Run one-click launcher from project root
./start.sh
```

---

## 🎯 Good First Issues / Starter Tasks

Looking for an easy place to start? Here are well-scoped tasks ready for contribution:

* [ ] **Issue #1: Add Azure Cloud Decoy Artifacts (`backend/asset_generator.py`)**
  * *Scope*: Add Azure CLI profile generators (`~/.azure/azureProfile.json`) and Azure Blob storage decoy outputs (`az storage blob list`) matching the seeded company domain.
  * *Labels*: `good first issue`, `enhancement`, `deception`

* [ ] **Issue #2: Frontend Dark Theme / Accent Color Switcher (`frontend/`)**
  * *Scope*: Add a user toggle in the SOC top header to switch between "Clinical Forensics" (default `#0B0D10` / `#4A9EFF`) and "High-Contrast Monokai" theme palettes.
  * *Labels*: `good first issue`, `frontend`, `ui`

* [ ] **Issue #3: Export Forensic Timeline to JSON / STIX 2.1 Format (`backend/main.py`)**
  * *Scope*: Add an endpoint `GET /api/sessions/{session_id}/export` that packages session commands, MITRE ATT&CK techniques, and generated assets into a standard STIX 2.1 JSON bundle.
  * *Labels*: `good first issue`, `threat-intel`, `backend`

---

## 🔄 Pull Request Workflow

1. Create a feature branch: `git checkout -b feat/my-new-deception-template`
2. Commit your changes: `git commit -m "feat: add Azure CLI canary generator"`
3. Push to your fork: `git push origin feat/my-new-deception-template`
4. Open a Pull Request on GitHub describing your changes and testing steps.
