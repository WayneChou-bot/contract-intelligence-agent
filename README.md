# 🔎 ClauseLens

> 🧠 **A modular contract-intelligence agent — one agent, many skills.**
> Built on **Google ADK 2.x + Gemini**. The agent owns reasoning and
> orchestration; every domain capability is a reusable, framework-agnostic
> **skill**. New capabilities (regulation lookup, RAG, …) plug in without
> touching the agent.

🧬 ClauseLens is the platform evolution of **ClauseGuard** (the Kaggle × Google
capstone, [repo](https://github.com/WayneChou-bot/contract-risk-agent)).
ClauseGuard was one focused contract-review agent — here it becomes the **first
skill** of a platform, and a single agent decides which skill to call.

![ClauseLens architecture](docs/clauselens_architecture.png)

## 🧩 Architecture — three layers

- 🟣 **Agent layer** (`app/agent.py`) — a Gemini `Agent` that understands intent,
  plans, and routes to the right skill. It can chain skills (e.g. translate a
  foreign contract, then review it) and never follows instructions hidden inside
  contract text.
- 🟦 **Skill layer** (`skills/`) — plain Python packages with **no dependency on
  the agent runtime**, so the same skills work under ADK today or any framework
  tomorrow.
- 🟡 **Foundation** — deterministic, unit-tested business logic (the security
  screen + risk engine from ClauseGuard) that gives hard guarantees the model
  can't bypass.

## 🛠️ Skills

| Skill | Tool | What it does | LLM? |
|---|---|---|---|
| 📄 Read document *(OCR)* | `read_document` | OCR a PDF / scan / image into text (Gemini multimodal); feeds the text to other skills | ✅ |
| 🛡️ Contract review *(ClauseGuard)* | `review_contract` | flag unfavorable clauses, redact PII, block prompt injection, route auto/human | ❌ deterministic |
| 📝 Summarize | `summarize_contract` | executive summary: risk count, top risks, recommendation | ❌ |
| ⚖️ Compare | `compare_contracts` | compare two contracts, say which is riskier and why | ❌ |
| 💡 Explain risk | `explain_risk` | plain-language "why it's risky + how to fix" per clause | ❌ |
| 🌐 Translate | `translate_contract` | translate a contract (Gemini-backed) | ✅ |
| 🧭 **Roadmap** | — | regulation lookup (RAG) · cross-template clause comparison · durable audit store · human-approval UI | — |

The agent **chains** skills: give it a file path and it calls `read_document`
(OCR) first, then `review_contract` on the extracted text.

## 🚀 Setup & run

```bash
# 1) install (uv recommended) and add your key
cp .env.example .env        # Windows: copy .env.example .env  → set GOOGLE_API_KEY

# 2) deterministic tests — no API key needed
uv run --with pytest pytest -q          # ✅ 39 passed

# 3) the agent in the ADK dev-ui (needs the Gemini key)
#    Windows: set GOOGLE_API_KEY=...   macOS/Linux: export GOOGLE_API_KEY=...
uv run adk web app --port 8080          # http://127.0.0.1:8080/dev-ui/?app=app
```

💬 In the dev-ui chat, just talk to it — the agent routes to the right skill:

```text
Read and review the contract in samples/contract_scan.pdf

Review this contract: This agreement renews automatically for one-year terms. The provider may terminate this agreement at any time at its sole discretion. Governed by the laws of Singapore.

Summarize it.

Explain the risks and how I should fix them.

Translate this contract to English: 本服務合約自動續約一年，乙方提前終止應付三倍違約金。

Compare these two contracts: A) <contract A text>  B) <contract B text>
```

📁 Sample contracts are in `samples/` — including `contract_scan.pdf`, a
**scanned-look PDF** for demoing the OCR → review chain.

> 🖥️ **Note on the UI.** The chat panel, the agent graph (root agent → tools), and
> the Events / Traces inspector are **Google ADK's built-in developer UI**
> (`adk web`) — not a custom frontend. ClauseLens provides the agent, the skills,
> and the deterministic business logic; ADK provides the runtime and the UI.

## 💡 Why this design

- ♻️ **Reusability** — a skill is decoupled from the agent and the framework. The
  same `contract_review` skill could be called from ADK, another agent SDK, or a
  plain FastAPI endpoint.
- 🧱 **Extensibility** — add a capability by adding a skill; the agent's reasoning
  doesn't change. Swap the domain (HR, finance, insurance) by swapping skills.
- ✅ **Trust by verification** — the security guarantees live in deterministic,
  unit-tested Python, not in a prompt. Trust comes from verification, not from
  hoping the model behaves.

## 🔒 Security (inherited from the review skill)

PII redaction (TW national ID, US SSN, cards, phones, emails — ZH & EN) and
prompt-injection detection run **before** any model call; injected documents are
escalated to a human with the model bypassed. See `skills/contract_review/`.

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE).
