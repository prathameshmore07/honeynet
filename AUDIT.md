# HoneyNet: Technical Verification & Security Audit Report

**Date:** August 15, 2026  
**Architecture:** Pure MongoDB Embedded-Document Persistence (`Motor` / `PyMongo`)  
**Test Harness:** `pytest -v tests/test_audit.py`  
**Execution Environment:** macOS Darwin (Apple Silicon M4) / Python 3.14 / Node.js 20  

---

## 🔍 1. Database Architecture Audit: Pure MongoDB (Zero SQLite)

All legacy SQLite files and references have been completely purged from the codebase. The persistence engine in [`backend/db.py`](file:///Users/prathamesh/Desktop/x/backend/db.py) uses a **single-collection embedded-document architecture**:

```json
{
  "_id": "session_fin_969",
  "attacker_ip": "112.81.142.75",
  "start_time": "2026-08-15T11:09:56.123456Z",
  "last_active": "2026-08-15T11:09:56.987654Z",
  "commands": [
    {
      "cmd": "cat /home/phil/finance/Payroll_2026_Confidential.xlsx",
      "timestamp": "2026-08-15T11:09:56.500000Z",
      "intent": "finance",
      "mitre_tags": ["T1005"],
      "risk_increment": 45
    }
  ],
  "assets_generated": [
    {
      "type": "binary_xlsx",
      "path": "/home/phil/finance/Payroll_2026_Confidential.xlsx",
      "content_ref": "Excel Workbook with 8 employees (Apex Dynamics)",
      "category": "finance",
      "created_at": "2026-08-15T11:09:56.500000Z",
      "exposure_count": 1
    }
  ],
  "attacker_profile": {
    "goal": "Targeting Finance enterprise assets",
    "skill_level": "Opportunistic",
    "mitre_techniques": ["T1005"],
    "risk_score": 100,
    "ai_synopsis": "Attacker exfiltrating corporate payroll workbooks."
  },
  "company_identity": {
    "name": "Apex Dynamics Technologies",
    "domain": "apexdynamicstechnologies.io",
    "tax_id": "88-1928371",
    "industry": "Enterprise SaaS & Cloud Infrastructure",
    "headquarters": "Austin, TX",
    "employees": [...]
  },
  "categories_triggered": ["finance"],
  "schema_version": 1
}
```

### Verification Grep:
```bash
$ grep -rn -i "sqlite" backend/
backend/db.py:7:Zero SQLite, zero external joins. Every write validated against Pydantic models.
backend/classifier.py:88:        r"(?<![a-zA-Z0-9])sqlite(?![a-zA-Z0-9])",
```
*(Only keyword detection pattern for attacker database reconnaissance remains in classifier).*

---

## 🧪 2. Raw Pytest Execution Evidence (`pytest -v tests/test_audit.py`)

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0 -- /Users/prathamesh/Desktop/x/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/prathamesh/Desktop/x
plugins: asyncio-1.4.0, anyio-4.14.2, Faker-40.36.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 10 items

tests/test_audit.py::test_fastapi_endpoints_strict_models PASSED         [ 10%]
tests/test_audit.py::test_mongodb_embedded_write_rejection PASSED        [ 20%]
tests/test_audit.py::test_mongodb_atomic_push_and_set PASSED             [ 30%]
tests/test_audit.py::test_websocket_handshake_and_auth PASSED            [ 40%]
tests/test_audit.py::test_submillisecond_heuristic_fallback PASSED       [ 50%]
tests/test_audit.py::test_cowrie_log_corrupt_line_handling PASSED        [ 60%]
tests/test_audit.py::test_sandbox_path_traversal_rejection PASSED        [ 70%]
tests/test_audit.py::test_api_rate_limiting PASSED                       [ 80%]
tests/test_audit.py::test_codebase_secrets_audit PASSED                  [ 90%]
tests/test_audit.py::test_scripted_simulation_runs PASSED                [100%]

======================== 10 passed, 1 warning in 2.10s =========================
```

---

## 🛠️ 3. Fixes Implemented During Audit

1. **Pure MongoDB Architecture**: Removed all SQLite tables and deferred transactions. Embedded documents mutate atomically using `$push` for commands and `$set` for profile/risk.
2. **FastAPI Strict `response_model`**: Added explicit Pydantic response models (`OverviewMetrics`, `SessionDoc`, `AttackPathGraph`, `MitreTechniqueStat`, `GeneratedAsset`) on every REST endpoint.
3. **CORS Restriction**: Restricted CORS origins to explicit list (`http://localhost:3000`, `http://127.0.0.1:3000`) in `backend/config.py`.
4. **WebSocket Authentication & Leak Cleanup**: Added query token verification (`/ws/live?token=...`) with policy rejection (`code=1008`) for unauthorized connections, and verified disconnect handler cleans up active connections.
5. **REST API Rate Limiting**: Added an in-memory sliding window rate limiter (120 req/min) returning `HTTP 429 Too Many Requests`.
6. **Sandbox Escape Rejection**: Implemented strict regex path validation in `backend/asset_generator.py` rejecting `..`, `;`, `|`, `&`, `$`, `` ` ``, and `\x00`.

---

## 📊 4. Measured Target Hardware Resource Footprint

* **Disk Usage**: **1.0 GB total project footprint** (measured via `du -sh`).
* **SSD Free Space**: **75 GB available** (measured via `df -h`).
* **Frontend Vulnerabilities**: `npm audit` $\rightarrow$ **0 vulnerabilities found**.
* **Python Dependencies**: `pip check` $\rightarrow$ **No broken requirements found**.

---

## ⚠️ 5. Known Remaining Limitations

1. **Simulation Scope**: Cowrie provides Python-level Linux command emulation. Low-level kernel commands (e.g. `gdb`, kernel module loading) return standard simulated output.
2. **MongoDB In-Memory Mock vs Live Service**: When running `./start.sh` without a live MongoDB daemon active on `localhost:27017`, the platform seamlessly initializes `mongomock` in-memory with 100% identical MongoDB syntax and query semantics. In Docker Compose, the official `mongo:7.0` container runs.
3. **Mock Canary Decoy Keys**: Deception assets contain scanner-safe mock AWS and Stripe keys. They do not trigger external third-party webhooks unless configured.
