

````markdown
# Customer Operations AI Pipeline

An AI-assisted customer operations pipeline for enterprise support teams.

The project combines deterministic business logic, local knowledge-base
retrieval, and Gemini-powered reasoning to support two core workflows:

1. **Intelligent Ticket Triage**
2. **TAM Account Health Analysis**

It also includes an evaluation harness and production design documentation.

The project uses the synthetic datasets provided for the
**US Delivery Internship Technical Task Round**.

---

## Overview

Customer-support operations typically require two types of work:

- understanding and routing incoming support tickets
- identifying account-level risks and preparing useful information for
  Technical Account Managers (TAMs)

This project automates both workflows while keeping important business
calculations deterministic and auditable.

### Architecture

```text
                         Customer Operations AI Pipeline
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
          Task 1: Ticket Triage                  Task 2: Account Health
                 │                                         │
          Ticket subject/body                    Account + ticket history
                 │                                         │
                 ▼                                         ▼
        Gemini classification                    Deterministic metrics
                 │                                         │
                 ▼                                         ▼
       Knowledge-base retrieval                  Risk-signal detection
                 │                                         │
                 ▼                                         ▼
        Known-issue analysis                       Gemini summary
                 │                                         │
                 ▼                                         ▼
       Responder-team routing                    TAM executive brief
                 │
                 ▼
          First-response draft
````

---

## Features

### Ticket Triage

For each support ticket, the pipeline determines:

* Product area
* Category
* Urgency
* Reasoning
* Relevant knowledge-base document
* Known-issue match
* Recommended responder team
* Draft first response

Supported categories:

* Bug
* Feature Request
* How-To
* Performance
* Billing
* Integration
* Onboarding
* Data Loss

Urgency levels:

* **P1** — Critical
* **P2** — High impact
* **P3** — Normal / moderate impact
* **P4** — Low priority

### Account Health

The account-health workflow combines account information with the
customer's recent support history.

It calculates:

* Ticket volume
* Open tickets
* P1 tickets
* Average satisfaction
* Seat utilisation
* Days to renewal
* Usage trend
* NPS
* Account health
* Risk signals
* Escalation notes

It then uses Gemini to turn the grounded metrics into a concise
TAM-oriented executive summary.

### Knowledge-Base Retrieval

Knowledge-base retrieval is performed locally rather than asking the LLM
to search the entire corpus.

The retrieval pipeline uses:

* TF-IDF vectorisation
* Cosine similarity
* Product-aware matching
* Ranked document selection

This reduces unnecessary LLM usage and keeps retrieval deterministic.

### Evaluation

The repository contains automated evaluation cases covering:

* Normal ticket triage
* Account-health calculations
* Ambiguous tickets
* Conflicting account signals
* Account/ticket discrepancies
* Executive account-health output

---

## Project Structure

```text
customer-ops-ai-pipeline/
│
├── data/
│   ├── tickets.json
│   └── accounts.json
│
├── knowledge-base/
│   ├── products/
│   ├── troubleshooting/
│   ├── billing/
│   └── onboarding/
│
├── account_health.py
├── data_loader.py
├── evaluation.py
├── kb_loader.py
├── kb_retriever.py
├── main.py
├── triage.py
│
├── test_account_health.py
├── test_triage_rules.py
│
├── DATA_SCHEMA.md
├── DESIGN_NOTE.md
├── eval_report.md
├── requirements.txt
├── .env.example
└── .gitignore
```

### Module Responsibilities

| File                     | Responsibility                                                      |
| ------------------------ | ------------------------------------------------------------------- |
| `main.py`                | CLI entry point                                                     |
| `triage.py`              | Ticket classification, KB matching, routing and response generation |
| `account_health.py`      | Account context, deterministic metrics and health summary           |
| `data_loader.py`         | Loads tickets and account data                                      |
| `kb_loader.py`           | Loads knowledge-base documents                                      |
| `kb_retriever.py`        | TF-IDF and cosine-similarity retrieval                              |
| `evaluation.py`          | Automated evaluation harness                                        |
| `test_triage_rules.py`   | Responder-team rule tests                                           |
| `test_account_health.py` | Account-health metric tests                                         |
| `DATA_SCHEMA.md`         | Dataset schema documentation                                        |
| `DESIGN_NOTE.md`         | Production architecture and failure-mode analysis                   |
| `eval_report.md`         | Evaluation results                                                  |

---

# Getting Started

## Requirements

* Python 3.10+
* Gemini API key
* Internet connection for Gemini API calls

## 1. Clone or open the project

Open the project directory:

```powershell
cd customer-ops-ai-pipeline
```

## 2. Create a virtual environment

```powershell
python -m venv venv
```

Activate it in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## 4. Configure Gemini

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

`.env.example` is provided as a safe template.

The actual `.env` file is excluded from Git through `.gitignore`.

---

# Running the Application

The project uses `main.py` as its command-line entry point.

## View available commands

```powershell
python main.py --help
```

Expected interface:

```text
usage: main.py [-h] --task {triage,health} [--account-id ACCOUNT_ID]
```

---

## Task 1 — Ticket Triage

Run:

```powershell
python main.py --task triage
```

The pipeline:

```text
Ticket
  │
  ▼
Gemini classification
  │
  ├── Product area
  ├── Category
  ├── Urgency
  └── Reasoning
  │
  ▼
Knowledge-base retrieval
  │
  ▼
Known-issue evaluation
  │
  ▼
Responder-team recommendation
  │
  ▼
First-response generation
```

The classification is constrained to the supported category and urgency
values.

The model is also instructed to base urgency on evidence contained in the
ticket rather than simply trusting words such as "urgent" or "critical".

---

## Task 2 — Account Health

Run:

```powershell
python main.py --task health --account-id ACC-3336
```

The workflow is:

```text
Account
   +
Recent ticket history
   │
   ▼
Deterministic metric calculation
   │
   ├── Ticket metrics
   ├── Support metrics
   ├── Seat utilisation
   ├── Renewal timing
   └── Risk signals
   │
   ▼
Gemini
   │
   ▼
Executive TAM summary
```

The account-health calculations are performed locally in Python so that
important business metrics remain reproducible.

The LLM is used for summarisation rather than for calculating the
underlying metrics.

---

# Knowledge-Base Retrieval

The knowledge base is stored under:

```text
knowledge-base/
```

Documents are loaded by `kb_loader.py`.

Retrieval is implemented in `kb_retriever.py`.

The retrieval process is:

1. Load the Markdown documents.
2. Convert documents into TF-IDF vectors.
3. Convert the ticket into a query vector.
4. Calculate cosine similarity.
5. Apply product-specific matching where appropriate.
6. Rank the documents.
7. Select the most relevant document.

This provides a lightweight local retrieval layer without requiring an
external vector database.

---

# Data

The project uses two supplied synthetic datasets.

### Tickets

```text
data/tickets.json
```

Contains 500 synthetic support tickets.

### Accounts

```text
data/accounts.json
```

Contains 50 synthetic customer accounts.

All supplied data is synthetic.

The complete schema is documented in:

```text
DATA_SCHEMA.md
```

The implementation also handles the intentionally imperfect dataset,
including ticket/account mismatches and ambiguous tickets.

---

# Testing

The repository contains both deterministic unit tests and an
LLM-dependent evaluation harness.

## Triage rule tests

```powershell
python test_triage_rules.py
```

Expected:

```text
All responder-team tests passed.
```

## Account-health tests

```powershell
python test_account_health.py
```

Expected:

```text
All account-health metric tests passed.
```

## Python compilation

```powershell
python -m py_compile data_loader.py kb_loader.py kb_retriever.py triage.py account_health.py evaluation.py main.py
```

No output indicates successful compilation.

## Dependency validation

```powershell
python -m pip check
```

Expected:

```text
No broken requirements found.
```

---

# Evaluation

Run the complete evaluation harness with:

```powershell
python evaluation.py
```

The evaluation covers:

* 5 normal triage cases
* 5 account-health metric cases
* 2 adversarial triage cases
* 2 adversarial account-health cases
* Task 2 executive-brief validation

A successful development run achieved:

```text
Overall score: 1.00
Passed: 14/14
Overall pass rate: 100.00%
Evaluation errors: 0
```

Evaluation results are documented in:

```text
eval_report.md
```

### API quota

The evaluation requires Gemini API requests.

During development, some runs encountered Gemini Free Tier quota
limitations (`429 RESOURCE_EXHAUSTED`) and temporary service
availability errors (`503 UNAVAILABLE`).

These errors are external API limitations and are reported separately
by the evaluation harness.

---

# Design Decisions

## Deterministic business logic

Business-critical account metrics are calculated locally rather than
delegated to the LLM.

This makes values such as:

* ticket counts
* seat utilisation
* renewal timing
* satisfaction averages

reproducible and testable.

## LLM usage

Gemini is used where language reasoning provides the most value:

* ticket classification
* knowledge-grounded reasoning
* first-response generation
* executive account-health summarisation

## Grounding

Prompts explicitly instruct the model to:

* use only supplied data
* avoid inventing facts
* acknowledge missing information
* distinguish calculated values from source values
* surface contradictory data

---

# Security

API credentials are loaded from environment variables.

Never commit:

```text
.env
```

The repository provides:

```text
.env.example
```

with a placeholder value.

The `.gitignore` also excludes:

```text
.env
venv/
__pycache__/
*.pyc
```

---

# Production Considerations

Production failure modes and scaling considerations are documented in:

```text
DESIGN_NOTE.md
```

The design note covers:

* LLM/API failures
* Rate limits and quota exhaustion
* Invalid model responses
* Classification errors
* Missing or contradictory customer data
* Latency versus quality
* PII and data sensitivity
* Scaling to 10× volume
* Retry and backoff strategies
* Human review for high-impact classifications

---

# Verification

Before submission, run:

```powershell
python -m py_compile data_loader.py kb_loader.py kb_retriever.py triage.py account_health.py evaluation.py main.py
```

```powershell
python test_triage_rules.py
```

```powershell
python test_account_health.py
```

```powershell
python -m pip check
```

```powershell
python main.py --help
```

Finally, when Gemini API quota is available:

```powershell
python evaluation.py
```

---

# Limitations

* Ticket triage depends on Gemini API availability.
* Free-tier Gemini quotas can limit evaluation runs.
* The current knowledge-base retriever is a lightweight TF-IDF system
  rather than a production vector database.
* The supplied datasets are synthetic and therefore do not represent
  production customer data.
* The CLI is currently the primary interface.

---

# Documentation

Additional project documentation:

* [`DATA_SCHEMA.md`](DATA_SCHEMA.md) — dataset schema
* [`DESIGN_NOTE.md`](DESIGN_NOTE.md) — production design considerations
* [`eval_report.md`](eval_report.md) — evaluation results

---

