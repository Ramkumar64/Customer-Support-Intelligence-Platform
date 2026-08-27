````markdown
# Evaluation Report

## Summary

The Customer Operations AI Pipeline was evaluated across ticket triage and account-health analysis, including adversarial cases designed to test ambiguous inputs and conflicting account signals.

The evaluation harness currently contains **15 checks**:

- 5 normal triage cases
- 5 account-health metric cases
- 1 Task 2 executive-brief validation
- 2 adversarial triage cases
- 2 adversarial account-health cases

A previous complete evaluation run achieved:

- **Overall score:** 1.00
- **Passed:** 14/14
- **Overall pass rate:** 100%
- **Evaluation errors:** 0

The 14/14 result was obtained before the additional Task 2 executive-brief validation was added to the evaluation harness.

## Score Breakdown

| Evaluation Area | Result |
|---|---:|
| Triage | 5/5 passed in the latest run |
| Account Health | 5/5 passed in the latest run |
| Adversarial Triage | Previously 2/2 passed |
| Adversarial Account Health | 2/2 passed in the latest run |
| Task 2 Executive Brief | Previously passed |

## Triage Evaluation

Five normal ticket cases are evaluated:

1. Feature request
2. Billing issue
3. How-to question
4. Performance issue
5. Data loss

The latest evaluation run passed all five normal triage cases.

The Billing evaluation initially returned `P4` instead of the expected `P3`. The urgency guidance was subsequently refined so that ordinary billing and invoice issues without evidence of substantial business impact are treated as P3. The Billing case then passed.

Two adversarial triage cases are also evaluated:

- Ambiguous feature request
- Performance vs integration ambiguity

Both cases passed in the previous complete 14/14 evaluation run.

## Account Health Evaluation

Five deterministic account-health cases are evaluated:

1. At-risk account
2. Healthy account
3. Zero-ticket account
4. Seat utilization
5. Renewal calculation

All five cases passed in the latest evaluation run.

The account-health implementation is also tested against:

- Conflicting health signals
- Account-level ticket discrepancies

Both adversarial account-health cases passed in the latest evaluation run.

## Task 2 Executive Brief

The evaluation harness includes a dedicated smoke test for the LLM-generated account-health executive brief.

The test verifies that the generated brief is non-empty and contains the required sections:

1. `EXECUTIVE SUMMARY`
2. `OPEN RISKS & FLAGGED ISSUES`
3. `RECOMMENDED TALKING POINTS`

This validation passed in a previous successful evaluation run.

The check uses one live Gemini request rather than generating a summary for every deterministic account-health test, reducing unnecessary API usage.

## Scoring Method

Each evaluation case receives a score between 0 and 1.

For triage cases, the score is based on:

- Category correctness
- Urgency correctness

For account-health cases, each expected metric is checked against the calculated metric.

The Task 2 executive-brief smoke test checks the presence of the required sections and verifies that the generated summary is non-empty.

A case is marked **PASS** when all required checks pass.

API or execution failures are reported separately as **ERROR** rather than being treated as successful cases.

## API / Infrastructure Notes

The Gemini API is required for LLM-based ticket classification and executive-summary generation.

During development, some evaluation runs were affected by Gemini Free Tier quota exhaustion (`429 RESOURCE_EXHAUSTED`) and temporary model availability errors (`503 UNAVAILABLE`).

These errors occurred while making live API requests and do not represent deterministic failures in the local calculation or routing logic.

The latest quota-limited run still demonstrated:

- Normal triage: **5/5 passed**
- Account-health metrics: **5/5 passed**
- Adversarial account health: **2/2 passed**
- Billing classification: **passed after the urgency-rule refinement**

The previously completed 14/14 run provides the last complete zero-error evaluation result before the Task 2 executive-brief smoke test was added.

## Local Deterministic Tests

The project also contains focused local tests that do not require Gemini API calls.

### Triage responder-team tests

```text
python test_triage_rules.py
````

Result:

```text
All responder-team tests passed.
```

### Account-health metric tests

```text
python test_account_health.py
```

Result:

```text
All account-health metric tests passed.
```

### Python compilation check

```text
python -m py_compile data_loader.py kb_loader.py kb_retriever.py triage.py account_health.py evaluation.py main.py
```

Result:

```text
No compilation errors.
```

### Dependency check

```text
python -m pip check
```

Result:

```text
No broken requirements found.
```

## Conclusion

The mandatory Task 1 and Task 2 functionality has been implemented and validated with both deterministic tests and live Gemini-based evaluation cases.

The evaluation harness includes normal and adversarial scenarios and separates API/infrastructure errors from application-level failures.

The project also includes a production design note covering failure modes, latency versus quality, data sensitivity and PII, and scaling to higher ticket volume.

```
```
