<p align="center">
  <h1 align="center">Diatax</h1>
</p>



<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Architecture-Multi--Agent-purple" alt="Multi-Agent"/>
  <img src="https://img.shields.io/badge/Framework-Diátaxis-2ea44f" alt="Diataxis Framework"/>
  <img src="https://img.shields.io/badge/Security-Fail--Secure-red" alt="Fail-Secure"/>
</p>

Type `python -m diatax.main generar` in your terminal and it orchestrates a team of AI agents to map, understand, and document your entire project — outputting a beautiful, zero-dependency HTML dashboard based on the prestigious Diátaxis framework.

Works with local codebases and supports advanced static dependency graphs (like Graphify) for massive enterprise architectures.

```bash
python -m diatax.main generar .
```

That's it. You get a production-ready documentation site:

```
diatax_result/
├── index.html       open in any browser — elegant, zero-JS "Ink & Paper" aesthetic
├── style.css        fully customizable styling variables
├── assets/          auto-extracted local images referenced in your docs
├── reference.md     technical reference (functions, classes, APIs)
├── howto.md         step-by-step guides for specific tasks
├── tutorial.md      learning-oriented onboarding materials
└── explanation.md   deep-dive architectural concepts and decisions
```

For incremental updates when code changes, just run:

```bash
python -m diatax.main update .
```

---

## ⚡ Prerequisites

| Requirement | Minimum | Check | Install |
|---|---|---|---|
| Python | 3.10+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| Git (Optional) | any | `git --version` | Required for automatic root detection fallback |

---

## ⚙️ Install & Configure

> **Local Installation:** Diatax is designed to run locally on your machine to securely process your source code.

**Step 1 — Clone & Install dependencies:**

```bash
# Clone the repository
git clone https://github.com/DaveCuc/diatax.git
cd diatax

# Install dependencies
python -m pip install -r diatax/requirements.txt
```

**Step 2 — Configure your AI Provider:**

Diatax supports Google Gemini (2.x/3.x series), Groq (LLaMA 3.3), OpenAI, Anthropic, and more via LiteLLM.

```bash
python -m diatax.main config
```

*Security Note: Your API credentials are NEVER stored in plain text. Diatax uses OS-level Keyring integration (Windows Credential Locker, macOS Keychain) with a Fail-Secure policy.*

---

## 📝 Usage Guide

### 1. Full Documentation Generation
Enter your project folder and run the main command. Diatax features a Human-in-the-Loop (HITL) system allowing you to approve or reject agent drafts.
```bash
python -m diatax.main generar .
```
*Tip: Use `--auto` to skip interactive feedback pauses and run headless.*

### 2. Smart Incremental Updates
Only document what has changed to save API tokens and time. Diatax maintains a local `.diatax_cache.json` hash map.
```bash
python -m diatax.main update .
```

### 3. Deep Security Audit (SAST)
Launch the standalone `RiskAgent` to scan for vulnerabilities, hardcoded secrets, and bad practices.
```bash
python -m diatax.main audit .
```

### 🚀 Massive Enterprise Projects
For extensive codebases, it is highly recommended to generate a static dependency map first using tools like [Graphify](https://github.com/safishamsi/graphify). Diatax will automatically detect `graphify_result.json` in your root folder to provide deep systemic context to the documentation agents.

---

## 🤖 Internal Architecture

Diatax operates on a synchronous Multi-Agent pipeline:

### The Agents
- **Researcher:** The scout. Analyzes the technical structure, AST, and logical flow of the source code. Identifies knowledge gaps.
- **Writers (x4):** Specialists trained in the Diátaxis methodology. They draft Reference, How-To, Tutorial, and Explanation content.
- **Judges (x4):** The QA team. They evaluate Writer drafts against strict technical and stylistic standards.
- **RiskAgent (SAST):** The security auditor. Identifies security flaws and exposed secrets.
- **SiteWriter:** The static site generator. Assembles the Markdown into a Zero-JS HTML dashboard.

### Resilience & Security Layer
- **Keyring Integration:** API Keys are shielded in the OS vault.
- **Anti-Jailbreak:** Protection against prompt injection embedded in source code comments.
- **JSON Resilience:** Automatic regex-based recovery from corrupted AI JSON responses.
- **Circuit Breaker:** Adaptive rate-limiting and retry logic to guarantee pipeline completion.

---

## 📁 Export Results

The tool creates the `diatax_result/` folder in your project root:
- **index.html / style.css**: The portable interactive Dashboard.
- **assets/**: Automatic copy of local images detected in the code.
- **Markdowns**: Raw source files for integration with platforms like Docusaurus or MkDocs.
- **README Link**: Automatic injection of the documentation link into your `README.md`.

<!-- DOCUMENTOR_START -->
## 📚 Interactive Documentation
This project uses an autogenerated Diátaxis Dashboard. [View Full Web Documentation](./diatax_result/index.html)
<!-- DOCUMENTOR_END -->

---

## 🏆 Recommended Models

Diatax is heavily optimized for modern reasoning models:

| Provider | Model | Use Case |
|---|---|---|
| **Google** | `gemini-3.5-flash` | Maximum intelligence and stability (Recommended) |
| **Google** | `gemini-2.5-pro` | Deep reasoning for highly complex code |
| **Groq** | `llama-3.3-70b-versatile` | Extreme speed for rapid iteration |

---

## Privacy & Security

- **Code files** — processed locally. Sent only to your configured AI provider via secure HTTPS.
- **Credentials** — locked in your OS Keychain.
- No telemetry, no usage tracking, no analytics.
- Review our [Security Policy](SECURITY.md) for vulnerability reporting.

---
