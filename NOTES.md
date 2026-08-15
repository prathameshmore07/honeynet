# HoneyNet: Public Launch & Repository Operations Notes

This document contains manual checklist items, launch copy, and community distribution channels for the project author.

---

## 📌 1. GitHub Repository Settings

### Description One-Liner (Paste into Repository Settings):
> **AI-powered adaptive honeynet that infers attacker intent in real-time, builds a unique fake company around each adversary, and visualizes live attack paths in a SOC dashboard.**

### GitHub Topics to Add:
`honeypot`, `cybersecurity`, `ai`, `llm`, `mitre-attack`, `threat-intel`, `docker`, `deception-technology`, `threat-hunting`, `nextjs`, `fastapi`, `mongodb`, `ollama`

---

## 🔍 2. Naming Collision & Alternative Aliases

Before public launch, search for existing projects on GitHub:
* **Search Link**: [https://github.com/search?q=honeynet](https://github.com/search?q=honeynet)
* If the exact name `honeynet` is crowded or conflicts with the legacy Honeynet Project (1999), consider these strong alternatives:
  * `HoneyNet-AI` / `HoneyNet-Core`
  * `DeceptoNet` (Adaptive Cyber Deception Network)
  * `PhantomCorp` (AI Autonomous Deception Enterprise)
  * `CanaryNet` / `ForensicHoneynet`

---

## 🚀 3. Manual Launch Checklist & Show HN Post Draft

### Optimal Posting Day & Window:
* **Best Days**: Tuesday or Wednesday
* **Best Time Window**: 13:00 – 15:00 UTC (09:00 – 11:00 AM Eastern Time)

### ✍️ Hacker News: Show HN Post Draft

**Title:**
> Show HN: HoneyNet – An AI honeypot that builds a unique fake company around each attacker in real time

**Post Body:**
```text
Hey HN,

Traditional honeypots use static filesystems that attackers spot in seconds. Once they realize there are no real database connection strings or payroll sheets, they disconnect.

I built HoneyNet: an AI-driven adaptive honeynet that listens to attacker SSH commands, infers their tactical intent (hunting for payroll docs, developer secrets, or AWS keys), and dynamically generates authentic canary files to keep them engaged.

Key technical decisions & hurdles solved:
1. Sub-2s AI Latency: Attackers won't wait 10s for an LLM to respond mid-terminal session. We use a two-tier engine: a sub-millisecond regex matcher serves instant baseline deception, while native local Ollama (Qwen2.5) enriches metadata asynchronously with a strict 2s hard timeout.
2. Cross-File Identity Consistency: Fake files look fake if names don't match. We use Python Faker to generate one consistent corporate identity per session (same company name, domain, tax ID, and employee roster across .xlsx spreadsheets, .env files, and git commits).
3. Authentic Binary Excel (.xlsx): Attackers inspecting files find genuine binary Excel workbooks generated with openpyxl (with styled headers, formatted currency cells, and payroll formulas).
4. Forensics Lab SOC Dashboard: Built with Next.js 16 + React Flow to visualize lateral movement, live command feeds, MITRE ATT&CK heatmap, and risk scores.
5. 100% Free & Self-Hostable: Zero cloud APIs or external billing. Tuned for Apple Silicon (MacBook Air M4) and Linux servers with strict memory limits (< 3GB Docker RAM).

GitHub: https://github.com/prathameshmore07/honeynet

Would love your feedback on the architecture, deception realism, and threat attribution models!
```

---

## 🌐 4. Reddit & Community Distribution Subreddits

| Subreddit | Angle / Headline Focus |
| :--- | :--- |
| **r/netsec** | *Technical deep-dive*: "HoneyNet: Real-time intent classification and dynamic fake company generation for SSH honeypots" |
| **r/selfhosted** | *Self-hostable*: "I built a self-hosted AI honeypot with a live Next.js forensics dashboard (100% free, runs on Ollama & Docker)" |
| **r/homelab** | *Lab monitoring*: "Adding an adaptive AI honeypot to my homelab with live React Flow attack path tracking" |
| **r/LocalLLaMA** | *Local AI deployment*: "Using local Qwen2.5 3B via Ollama for real-time cybersecurity intent classification under a 2s budget" |
| **r/cybersecurity** | *Defensive deception*: "Using dynamic cyber deception to profile adversary TTPs and map MITRE ATT&CK techniques in real time" |

---

## 📑 5. Awesome-Lists Pull Requests

Submit pull requests to include HoneyNet in curated security repositories:
- [ ] **awesome-honeypots** (`paralax/awesome-honeypots`): Under *Deception / Adaptive Honeypots*
- [ ] **awesome-threat-intelligence** (`hslatman/awesome-threat-intelligence`): Under *Honeypots & Telemetry Collectors*
- [ ] **awesome-selfhosted** (`awesome-selfhosted/awesome-selfhosted`): Under *Communication / Security Tools*
