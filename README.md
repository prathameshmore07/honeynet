<div align="center">

# 🍯 HoneyNet

### **An AI-powered adaptive honeynet that builds a unique fake company around each attacker in real time.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Build-Passing-36B37E?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/prathameshmore07/honeynet/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20Local-white?style=flat-square&logo=ollama&logoColor=black)](https://ollama.ai/)
[![Apple Silicon](https://img.shields.io/badge/Hardware-M4%20Tuned-8892A0?style=flat-square&logo=apple&logoColor=white)](https://apple.com)

<br/>

<!-- ============================================================================== -->
<!-- DEMO GIF HERE                                                                  -->
<!-- Replace the placeholder below with the launch recording GIF/video (demo.gif)  -->
<!-- ============================================================================== -->
<p align="center">
  <img src="https://raw.githubusercontent.com/prathameshmore07/honeynet/main/public/demo_preview.png" alt="HoneyNet Forensics SOC Dashboard Demo" width="880px" style="border-radius: 8px; border: 1px solid #222730; box-shadow: 0 8px 24px rgba(0,0,0,0.6);" onerror="this.src='https://via.placeholder.com/880x480/14171C/4A9EFF?text=HoneyNet+Forensics+SOC+Dashboard+Preview'" />
</p>

</div>

---

## ⚡ Why HoneyNet?

Traditional honeypots rely on static fake filesystems. Experienced attackers immediately spot the lack of authentic developer secrets, company payroll records, or database backups and disconnect within seconds.

**HoneyNet** watches incoming SSH commands, infers adversary tactical intent in real time, and dynamically deploys **authentic, formatted fake assets** matching that intent.

```
Attacker: "ls -la /home/phil"
HoneyNet: [Instant Regex Match: Intent = Finance]
HoneyNet: [Faker Engine -> Seeds "Apex Holdings Ltd." (Tax ID: 88-1928371, Domain: apexholdings.io)]
HoneyNet: [openpyxl Engine -> Drops genuine binary Payroll_2026_Confidential.xlsx with 8 executive salaries]
Attacker: "cat Payroll_2026_Confidential.xlsx" -> Attacker stays engaged; SOC gathers forensic attribution.
```

---

## 📊 Comparison: HoneyNet vs. Traditional Deception

| Feature / Capability | Traditional Honeypot (Cowrie Alone) | Commercial Cyber Deception | **HoneyNet (AI Adaptive)** |
| :--- | :--- | :--- | :--- |
| **Adaptiveness** | ❌ None (Static filesystem) | ⚠️ Rule-based static decoys | ✅ **Real-Time Dynamic Deception** |
| **Asset Personalization** | ❌ Generic placeholder files | ⚠️ Manual template configuration | ✅ **Unique Fake Company per Attacker** |
| **Spreadsheet Realism** | ❌ Plain text / Fake shell errors | ⚠️ Mock CSV templates | ✅ **Genuine Binary Excel (`.xlsx`) via openpyxl** |
| **AI Inference Latency** | ❌ No AI integration | ⚠️ Cloud API calls (5–10s lag) | ✅ **$< 1\text{ms}$ Baseline + $\le 2\text{s}$ Async Ollama** |
| **Cost & Privacy** | 🟢 Free (Self-hosted) | 🔴 $20k–$100k+/year (Enterprise) | 🟢 **100% Free & Self-Hosted (No Cloud Billing)** |
| **Resource Efficiency** | 🟢 Low memory | 🔴 High VM overhead | 🟢 **$< 3\text{GB}$ Docker RAM (M4 Apple Silicon Tuned)** |

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph HostLayer ["1. Host Environment (MacBook Air M4 / Linux)"]
        NativeOllama["Native Ollama AI (:11434)<br>Model: qwen2.5:3b (< 2s hard timeout)"]
        NextJS["Next.js 16 SOC Forensics Dashboard (:3000)<br>React Flow + TanStack Query + Zod"]
    end

    subgraph DockerContainment ["2. Containment Sandbox (< 3GB RAM Total)"]
        Cowrie["Cowrie SSH Honeypot Container<br>Port :2222 | mem_limit: 512m"]
        CowrieLog["cowrie_logs/cowrie.json"]
        
        MongoDB[("MongoDB 7.0 Document Engine<br>Port :27017 | mem_limit: 1g<br>Single Embedded Document Schema")]
        
        subgraph FastAPIBackend ["3. FastAPI Real-Time Deception Engine (mem_limit: 1g)"]
            Tailer["Log Ingestion Tailer (Motor Async)"]
            RegexEngine["Tier 1: Instant Heuristic Regex (< 1ms)"]
            IdSeeder["Company Identity Seeder (Faker)"]
            AssetEngine["Real Asset Generator (openpyxl / xlsx)"]
            Profiler["Adversary Profiler & Risk Engine"]
            WSManager["WebSocket Telemetry Broadcaster (:8000)"]
        end

        Cowrie --> CowrieLog
        CowrieLog --> Tailer
        Tailer --> RegexEngine
        Tailer -.->|Async 2s Timeout| NativeOllama
        Tailer --> IdSeeder --> AssetEngine --> Cowrie
        Tailer --> Profiler --> MongoDB
        MongoDB --> WSManager --> NextJS
    end
```

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Clone the repository
git clone https://github.com/prathameshmore07/honeynet.git && cd honeynet

# 2. Launch the unified platform (FastAPI + Next.js + Cowrie)
chmod +x start.sh && ./start.sh

# 3. In another terminal, trigger a realistic attack simulation
python3 honeypot_sim.py --scenario finance
```

* 📊 **Forensics Lab SOC Dashboard:** [http://localhost:3000](http://localhost:3000)
* 🔌 **FastAPI Telemetry Backend:** [http://localhost:8000](http://localhost:8000) (Swagger Docs: `/docs`)
* 🍯 **Cowrie SSH Honeypot:** `ssh root@localhost -p 2222`

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Honeypot Ingress** | ![Cowrie](https://img.shields.io/badge/Cowrie-SSH%2FTelnet-3776AB?style=flat-square) | Low-to-medium interaction SSH daemon in container sandbox |
| **Backend & WS** | ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white) | Asynchronous API & WebSocket event broadcaster |
| **Database** | ![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white) | Single-collection embedded-document persistence with Motor |
| **Local AI Engine** | ![Ollama](https://img.shields.io/badge/Ollama-Qwen2.5%203B-white?style=flat-square&logo=ollama&logoColor=black) | Metal/MLX accelerated local LLM for intent attribution |
| **Asset Synthesis** | ![openpyxl](https://img.shields.io/badge/openpyxl-Binary%20Excel-217346?style=flat-square) ![Faker](https://img.shields.io/badge/Faker-Identity%20Seeder-FF6F00?style=flat-square) | Formatted `.xlsx` workbooks and corporate employee identity generation |
| **SOC Dashboard** | ![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=nextdotjs&logoColor=white) ![Tailwind](https://img.shields.io/badge/Tailwind-v4-38B2AC?style=flat-square&logo=tailwindcss&logoColor=white) | Forensics Lab UI (`#0B0D10` palette, `IBM Plex Mono`) |
| **Attack Graph** | ![React Flow](https://img.shields.io/badge/@xyflow/react-12-FF0072?style=flat-square) | Interactive lateral movement & pivot topology canvas |

---

## 🗺️ Roadmap & Future Milestones

The following capabilities are planned for upcoming releases:

- [ ] **Multi-Hop Web Application Decoys:** Lightweight simulated web applications (e.g. simulated internal GitLab issue tracker and HR salary lookup portal).
- [ ] **RDP Graphical Honeypot Decoys:** Low-interaction Windows RDP decoy nodes with fake desktop icons and simulated browser histories.
- [ ] **Automated Payload Detonation Sandbox:** Safe, isolated micro-VM sandboxing for dropped ELF/script binaries with MITRE behavioral tagging.
- [ ] **STIX 2.1 Threat Intel Export:** Automated packaging of session attack graphs into standard STIX 2.1 intelligence bundles for SIEM ingestion.

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](file:///Users/prathamesh/Desktop/x/CONTRIBUTING.md) for local development guidelines and [Good First Issues](file:///Users/prathamesh/Desktop/x/CONTRIBUTING.md#good-first-issues--starter-tasks).

---

## 📄 License

This project is licensed under the [MIT License](file:///Users/prathamesh/Desktop/x/LICENSE).
