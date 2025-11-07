# ArcFlux (ArcPay Agentic Stack)

ArcFlux is a prototype agentic workflow for ArcPay. It combines language-native user interfaces with autonomous risk checks, scheduling, and execution so that a single command such as “Pay User Two 120 USDC every Friday” can be classified, risk-scored, verified, scheduled, and executed without manual follow-up. The repository is intentionally small, self-contained, and data-backed by JSON files so you can inspect and demo the end-to-end flow quickly.

## Architecture at a Glance
1. **Command understanding (agentic).** `IntentAgent` uses an LLM (or a lightweight heuristic fallback) to turn raw text/audio into a structured intent payload and routes it to the right downstream agent.
2. **Guardian gating (agentic + automation).** `GuardianAgent` calls the LLM for risk scoring, enriches the request with balance data, verifies the recipient, stores the assessment, and either asks for user confirmation or schedules the payment.
3. **Execution loop (automation).** `PaymentScheduler` polls approved/scheduled payments, runs balance checks, executes them via `ExecutionEngine`/`APIConnector`, and rotates recurring schedules.
4. **Observability + sync (automation).** `SyncValidator`, `NotificationService`, and JSON-backed repositories keep the ledger, risk store, and alerts in sync so the system can be audited or reset easily.

## Agentic vs. Automation Responsibilities
| Component | Type | Why it belongs there |
| --- | --- | --- |
| `intent_agent.py` | **Agentic** | Uses an LLM to classify user intent, extract entities (amount, recipient, schedule), and decide whether to hand off to the Guardian or Query agent. |
| `guardian_agent.py` | **Agentic** | Calls the LLM-based risk model, reasons about recipient trust, balance ratios, and confirmation state, then decides whether to approve, deny, or flag. |
| `query_agent.py` | **Agentic** | Answers natural-language status questions by fetching facts (balance, upcoming/previous payments, risk flags) and passing them to the LLM for narrative responses. |
| `model_loader.py` | **Agentic enabler** | Loads the preferred HuggingFace model or falls back to heuristics so other agents stay model-agnostic. |
| `payment_scheduler.py`, `execution_engine.py`, `balance_monitor.py`, `sync_validator.py`, `notification_service.py`, `api_connector.py` | **Automation** | Deterministic services that enforce policy, execute payments, monitor balances, call external APIs, and raise alerts without LLM involvement. |
| `config.py`, `data_store.py`, `data_access.py`, `schedule_utils.py`, JSON data files | **Shared infrastructure** | Provide configuration resolution, thread-safe persistence, repositories, and scheduling math that both agentic and automated layers rely on. |

## File-by-File Map
| Path | Layer | Purpose / Key Functions | Agentic vs Automation |
| --- | --- | --- | --- |
| `rest_api.py` | API surface | FastAPI app exposing `/v1/commands`, `/v1/scheduler/tick`, `/v1/system/validate`, and `/v1/payments/{id}` so external clients can drive the agents or automation loops. | Bridge (mix) |
| `intent_agent.py` | LLM agent | Converts text/audio to structured intents, autofills recipients and schedules, and routes to Guardian or Query agents. | Agentic |
| `guardian_agent.py` | LLM agent | Performs risk scoring, recipient verification, balance-aware feature building, confirmation handling, and payment scheduling. | Agentic |
| `query_agent.py` | LLM agent | Answers “what’s happening?” questions by summarizing payment/risk/balance facts via the shared LLM. | Agentic |
| `model_loader.py` | ML infra | Loads HuggingFace models (e.g., `Qwen/Qwen3-0.6B`) with graceful fallback to heuristics; exposes `BaseArcLLM` interface. | Agentic enabler |
| `api_connector.py` | Integrations | Simulated wrappers for Circle (payments/verification), balance feeds, and stock data; centralizes auth headers. | Automation |
| `balance_monitor.py` | Controls | Pulls balances, caches results, detects drops, and triggers user/admin notifications when funds are insufficient. | Automation |
| `execution_engine.py` | Controls | Translates scheduled payments into Circle API payloads and records success/error metadata. | Automation |
| `payment_scheduler.py` | Controls | Polls `payment_schedule.json`, decides when records are due, re-checks balances, executes payments, updates recurring runs, and raises failures. | Automation |
| `sync_validator.py` | Controls | Cross-checks the payment schedule with `risk_assessment_db.json` to make sure every executed/approved payment has a risk log entry. | Automation |
| `notification_service.py` | Communications | Sends email/SMS/push messages using providers configured in `system_config.json`; used by Guardian, Scheduler, and monitors. | Automation |
| `data_store.py` | Persistence | Thread-safe helper that guarantees atomic JSON reads/writes with file-level locks. | Shared |
| `data_access.py` | Persistence | Repository classes for users, payment schedules, and risk assessments built on `JSONDataStore`; exposes helper dataclass `User`. | Shared |
| `schedule_utils.py` | Utilities | Parses ISO timestamps, detects recurring schedules, and computes next run times for interval/monthly requests. | Shared |
| `config.py` | Utilities | Loads `system_config.json`, supports `env:` indirection, and hands out repo-relative data paths. | Shared |
| `demo_test.py` | Tooling | CLI demo that chains Intent → Guardian → Scheduler to showcase an entire flow every 5 seconds. Useful while no UI exists. | Mixed |
| `LICENSE` | Legal | MIT-style license for reuse. | — |
| `system_config.json` | Config data | Central knobs for models, notification providers, Circle credentials, scheduler cadence, and demo defaults. | Shared |
| `user_database.json` | Data | Example customers with contact details, linked accounts, preferences, and whitelisted recipients for risk checks. | Shared |
| `payment_schedule.json` | Data | Ledger of scheduled/approved/executed payments, updated by Guardian decisions and Scheduler ticks. | Automation state |
| `risk_assessment_db.json` | Data | Append-only log of each risk-scoring call, including raw request payloads, engineered features, model output, and verification results. | Audit layer |

## Data & Persistence Model
- All repositories (`UserRepository`, `PaymentScheduleRepository`, `RiskAssessmentRepository`) write to JSON files defined in `system_config.json.dataPaths`. This makes the prototype easy to reset or inspect but can be swapped with a database later.
- Each write is guarded by `JSONDataStore`’s locks, so you can safely run the API server and the scheduler in parallel without corrupting files.
- Risk assessments capture the exact inputs the Guardian agent saw, giving you traceability when `SyncValidator` later audits approvals.

## Running the Stack Locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn
# (Install optional extras such as transformers/torch if you want the HuggingFace model.)

# Start the API (serves agents + automation endpoints)
uvicorn rest_api:app --reload

# In another shell, trigger automation or health checks
curl -X POST http://localhost:8000/v1/scheduler/tick
curl -X POST http://localhost:8000/v1/system/validate
```

### Demo Run
```
python demo_test.py
```
The script issues a recurring “Pay user2 every 5 seconds” command, walks through Guardian confirmations, and lets `PaymentScheduler` execute a few cycles so you can watch `payment_schedule.json` evolve.

## Typical Flows
1. **User issues a natural-language command.** `/v1/commands` feeds it to `IntentAgent`, which emits `IntentResult`.
2. **Guardian decision.** Guardian checks the user & recipient, verifies balances, and records a risk assessment. It either asks for confirmation, approves (and stores the payment for the scheduler), or denies/flags and notifies an operator.
3. **Automation loop.** `PaymentScheduler.run_tick()` repeatedly checks for due approvals, re-validates balances, calls `ExecutionEngine`, and sends post-run notifications. Recurring jobs get a new `scheduledTimestamp` via `schedule_utils.next_run`.
4. **Transparency.** The same `/v1/commands` route can answer “What’s my balance?” because `IntentAgent` can route to `QueryAgent`, which assembles facts and asks the LLM to explain them naturally.
5. **Safety nets.** `SyncValidator` ensures every executed payment has a matching risk entry, while `BalanceMonitor.detect_drop` and `NotificationService` surface anomalies to end users or ops.

## Extending the Prototype
- **Swap data stores.** Replace `JSONDataStore` in `data_access.py` with a real database while keeping the repo APIs stable.
- **Plug real providers.** Implement Circle’s real endpoints inside `APIConnector` or point the notification service at your SendGrid/Twilio accounts via `system_config.json`.
- **Upgrade the model.** Change `models.shared.name` to another HuggingFace checkpoint (or OpenAI via a custom loader) and the agents will automatically gain those capabilities.
- **Add new agents.** Follow the `BaseArcLLM` pattern and wire the agent through `rest_api.py` to keep separation between agentic reasoning and automation loops.

With this README you can see which parts of ArcFlux rely on agentic reasoning versus deterministic automation, how the files work together, and how to run or extend the system.
