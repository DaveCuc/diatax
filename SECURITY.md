# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues via GitHub's private vulnerability reporting, or email the maintainer directly. Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and aim to release a fix within 7 days for critical issues.

## Security Model

**Diatax** is a **local documentation generator and SAST auditing tool**. It runs locally on your machine and communicates with LLM APIs to generate documentation.

### Threat Surface & Mitigation

| Vector | Mitigation |
|--------|-----------|
| **Credential Leakage** | API Keys are strictly managed through the OS native `keyring` (Windows Credential Locker, macOS Keychain, Linux Secret Service). They are **never** saved in plaintext configuration files (`.diatax_config.json`). |
| **Fail-Secure Architecture** | If the OS keyring is unavailable or locked, the system aborts the configuration process rather than falling back to an insecure storage method. |
| **Prompt Injection (Jailbreak)** | Code is passed as a string literal to the LLMs. The `RiskAgent` includes specific heuristic checks to identify potential prompt injection payloads embedded within source code comments or strings. |
| **Malformed LLM Responses** | The JSON resilience layer in `LLMService` handles corrupted JSON payloads via regex extraction and provides an emergency auto-recovery fallback to prevent pipeline crashes. |
| **Path Traversal during Export** | `FileService.encontrar_raiz_proyecto` caps upward directory traversal at 10 levels to prevent scanning the entire filesystem. Export paths are bounded to `diatax_result/`. |
| **Arbitrary Code Execution** | Diatax reads files as plain text (`utf-8`) for analysis. It **does not** execute, `eval()`, or run the source code files it analyzes. |

### What Diatax does NOT do

- Does not run a network listener or open local ports.
- Does not collect or transmit telemetry, analytics, or usage data.
- Does not execute code from the source files it documents.
- Does not store API keys in environment files or plaintext JSON.

### Outbound Network Calls

- **LLM APIs:** Makes outbound HTTPS requests to the configured provider (Google Gemini, Groq, OpenAI, Anthropic) for code analysis and generation. 
- Diatax respects Rate Limits natively using an Exponential Backoff strategy to prevent API bans.