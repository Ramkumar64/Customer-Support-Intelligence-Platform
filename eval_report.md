# Evaluation Report

## Summary

The Customer Support Intelligence Platform was evaluated across ticket
triage and account-health analysis, including adversarial cases designed
to test ambiguous inputs, conflicting signals, and data discrepancies.

The evaluation harness contains **15 checks**:

- 5 normal triage cases
- 5 account-health metric cases
- 2 adversarial triage cases
- 2 adversarial account-health cases
- 1 Task 2 executive-brief validation

The deterministic and adversarial test suites achieved full passing
results during development. The executive-brief validation also passed
successfully when Gemini API quota was available.

## Evaluation Coverage

| Evaluation Area | Cases | Result |
|---|---:|---:|
| Normal Triage | 5 | 5/5 passed |
| Account Health | 5 | 5/5 passed |
| Adversarial Triage | 2 | 2/2 passed |
| Adversarial Account Health | 2 | 2/2 passed |
| Task 2 Executive Brief | 1 | Passed |

## Triage Evaluation

Five normal ticket cases are evaluated:

1. Feature request
2. Billing issue
3. How-to question
4. Performance issue
5. Data loss

All five normal triage cases passed.

Two adversarial triage cases are also evaluated:

1. Ambiguous feature request
2. Performance vs integration ambiguity

Both adversarial cases passed.

## Account Health Evaluation

Five deterministic account-health cases are evaluated:

1. At-risk account
2. Healthy account
3. Zero-ticket account
4. Seat utilization
5. Renewal calculation

All five cases passed.

The account-health implementation is additionally tested against:

- Conflicting health signals
- Account-level ticket discrepancies

Both adversarial account-health cases passed.

These tests verify that the implementation preserves deterministic
business calculations and surfaces conflicting source data rather than
silently reconciling it.

## Task 2 Executive Brief

The evaluation harness includes a dedicated smoke test for the
LLM-generated account-health executive brief.

The test verifies that the generated brief:

- is non-empty
- contains `EXECUTIVE SUMMARY`
- contains `OPEN RISKS & FLAGGED ISSUES`
- contains `RECOMMENDED TALKING POINTS`

The executive-brief validation passed successfully during development.

The check intentionally makes only one live Gemini request rather than
generating a summary for every account-health metric test. This reduces
unnecessary API usage and keeps deterministic tests independent of the
LLM.

## Scoring Method

Each evaluation case receives a score between 0 and 1.

For triage cases, the score checks:

- Category correctness
- Urgency correctness

For account-health cases, expected calculated metrics are compared
directly with the implementation output.

The Task 2 executive-brief smoke test checks the required sections and
ensures that the generated summary is non-empty.

A case is marked **PASS** when all required checks pass.

API or execution failures are reported separately as **ERROR** rather
than being treated as application-level failures.

## API / Infrastructure Notes

The Gemini API is required for LLM-based ticket classification and
executive-summary generation.

During development, some evaluation runs were affected by Gemini Free
Tier quota exhaustion (`429 RESOURCE_EXHAUSTED`) and temporary model
availability errors (`503 UNAVAILABLE`).

These failures occurred while making live API requests and do not
represent failures in the deterministic calculation or responder-team
routing logic.

When Gemini quota was available, the LLM-dependent evaluation cases
passed successfully.

## Local Deterministic Tests

The project also contains focused tests that do not require Gemini API
calls.

### Triage Responder-Team Tests

```powershell
python test_triage_rules.py

Result:

All responder-team tests passed.
Account-Health Metric Tests
python test_account_health.py

Result:

All account-health metric tests passed.
Python Compilation Check
python -m py_compile data_loader.py kb_loader.py kb_retriever.py triage.py account_health.py evaluation.py main.py app.py

Result:

No compilation errors.
Dependency Check
python -m pip check

Result:

No broken requirements found.
Continuous Integration

GitHub Actions runs on pushes and pull requests.

The CI workflow:

installs project dependencies
compiles the Python modules
runs deterministic triage tests
runs deterministic account-health tests

The Gemini-dependent evaluation harness is intentionally not executed
as part of CI because it requires live API access and is subject to
external quota and availability limits.

Conclusion

The core Ticket Triage and Account Health workflows have been implemented
and validated using deterministic tests, adversarial scenarios, and
Gemini-based evaluation where live API access is available.

The evaluation design separates deterministic business logic from
LLM-dependent reasoning and reports API/infrastructure failures
separately from application-level test failures.