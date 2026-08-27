from datetime import date
import re

from data_loader import load_accounts
from triage import classify_ticket
from account_health import (
    calculate_health_metrics,
    get_account_context,
    generate_health_summary,
)


def expected_days_to_renewal(account):
    renewal_date = date.fromisoformat(account["renewal_date"])
    return (renewal_date - date.today()).days


# =========================================================
# TASK 1 — TRIAGE EVALUATION
# =========================================================

def evaluate_triage_case(name, subject, body, expected):
    try:
        classification = classify_ticket(subject, body)

        checks = {
            "category": (
                classification.get("category")
                == expected["category"]
            ),
            "urgency": (
                classification.get("urgency")
                == expected["urgency"]
            ),
        }

        passed = all(checks.values())
        score = sum(checks.values()) / len(checks)

        return {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "score": score,
            "checks": checks,
            "expected": expected,
            "actual": {
                "category": classification.get("category"),
                "urgency": classification.get("urgency"),
            },
        }

    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "passed": False,
            "score": None,
            "checks": {},
            "expected": expected,
            "actual": None,
            "error": str(e),
        }


# =========================================================
# TASK 2 — ACCOUNT HEALTH METRIC EVALUATION
# =========================================================

def evaluate_health_case(name, account_id, expected):
    try:
        context = get_account_context(account_id)

        if context["account"] is None:
            return {
                "name": name,
                "status": "ERROR",
                "passed": False,
                "score": None,
                "checks": {
                    "account_exists": False
                },
                "expected": expected,
                "actual": None,
                "error": f"Account not found: {account_id}",
            }

        metrics = calculate_health_metrics(
            context["account"],
            context["tickets"],
        )

        checks = {}

        for field, expected_value in expected.items():
            checks[field] = (
                metrics.get(field) == expected_value
            )

        score = (
            sum(checks.values()) / len(checks)
            if checks
            else 0.0
        )

        passed = all(checks.values())

        return {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "score": score,
            "checks": checks,
            "expected": expected,
            "actual": {
                field: metrics.get(field)
                for field in expected
            },
        }

    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "passed": False,
            "score": None,
            "checks": {},
            "expected": expected,
            "actual": None,
            "error": str(e),
        }


# =========================================================
# TASK 2 — EXECUTIVE BRIEF EVALUATION
# =========================================================

def count_sentences(text):
    """
    Count simple sentence boundaries for validation.

    This is intentionally lightweight because the evaluation
    only needs to verify the required 3–5 sentence range.
    """

    sentences = re.findall(
        r"(?<!\b[A-Z])[.!?](?:\s|$)",
        text.strip(),
    )

    return len(sentences)


def extract_section(summary, heading, next_heading=None):
    """
    Extract text belonging to one required section.
    """

    start = summary.find(heading)

    if start == -1:
        return ""

    start += len(heading)

    if next_heading:
        end = summary.find(next_heading, start)

        if end != -1:
            return summary[start:end].strip()

    return summary[start:].strip()


def evaluate_health_summary_format():
    """
    One live Gemini smoke test for the Task 2 executive brief.

    This test validates the assignment-required structure and
    the 3–5 sentence executive-summary requirement.

    It is intentionally run once so deterministic metric tests
    do not consume Gemini quota.
    """

    account_id = "ACC-3336"

    try:
        context = get_account_context(account_id)

        if context["account"] is None:
            return {
                "name": "Task 2 executive brief",
                "status": "ERROR",
                "passed": False,
                "score": None,
                "checks": {},
                "expected": None,
                "actual": None,
                "error": f"Account not found: {account_id}",
            }

        metrics = calculate_health_metrics(
            context["account"],
            context["tickets"],
        )

        summary = generate_health_summary(
            context["account"],
            metrics,
            context["tickets"],
        )

        required_sections = [
            "EXECUTIVE SUMMARY",
            "OPEN RISKS & FLAGGED ISSUES",
            "RECOMMENDED TALKING POINTS",
        ]

        checks = {
            section: section in summary
            for section in required_sections
        }

        checks["non_empty"] = bool(summary.strip())

        executive_summary = extract_section(
            summary,
            "EXECUTIVE SUMMARY",
            "OPEN RISKS & FLAGGED ISSUES",
        )

        sentence_count = count_sentences(executive_summary)

        checks["executive_summary_3_to_5_sentences"] = (
            3 <= sentence_count <= 5
        )

        passed = all(checks.values())

        return {
            "name": "Task 2 executive brief",
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "score": (
                sum(checks.values()) / len(checks)
            ),
            "checks": checks,
            "expected": {
                "required_sections": required_sections,
                "executive_summary_sentences": "3-5",
            },
            "actual": {
                "summary_length": len(summary),
                "executive_summary_sentence_count": sentence_count,
                "summary_preview": summary[:500],
            },
        }

    except Exception as e:
        return {
            "name": "Task 2 executive brief",
            "status": "ERROR",
            "passed": False,
            "score": None,
            "checks": {},
            "expected": {
                "required_sections": [
                    "EXECUTIVE SUMMARY",
                    "OPEN RISKS & FLAGGED ISSUES",
                    "RECOMMENDED TALKING POINTS",
                ],
                "executive_summary_sentences": "3-5",
            },
            "actual": None,
            "error": str(e),
        }


# =========================================================
# EVALUATION CASES
# =========================================================

def run_evaluation():

    # =====================================================
    # TASK 1 — NORMAL TRIAGE CASES
    # =====================================================

    triage_cases = [
        {
            "name": "Feature request",
            "subject": "Request bulk archive",
            "body": (
                "We need the ability to select multiple entries "
                "and archive them at once."
            ),
            "expected": {
                "category": "Feature Request",
                "urgency": "P3",
            },
        },
        {
            "name": "Billing issue",
            "subject": "Unexpected invoice charge",
            "body": (
                "Our latest invoice contains an unexpected charge "
                "that we need help understanding."
            ),
            "expected": {
                "category": "Billing",
                "urgency": "P3",
            },
        },
        {
            "name": "How-to question",
            "subject": "How do I configure the integration?",
            "body": (
                "Please explain how to configure the existing "
                "integration."
            ),
            "expected": {
                "category": "How-To",
                "urgency": "P4",
            },
        },
        {
            "name": "Performance issue",
            "subject": "Pipeline is extremely slow",
            "body": (
                "The ingestion pipeline has become extremely slow "
                "and is timing out."
            ),
            "expected": {
                "category": "Performance",
                "urgency": "P2",
            },
        },
        {
            "name": "Data loss",
            "subject": "Customer data disappeared",
            "body": (
                "Several customer records are missing and appear "
                "to have been deleted."
            ),
            "expected": {
                "category": "Data Loss",
                "urgency": "P1",
            },
        },
    ]

    # =====================================================
    # TASK 1 — ADVERSARIAL CASES
    # =====================================================

    adversarial_triage_cases = [
        {
            "name": "Ambiguous feature request",
            "subject": "Archive operation is difficult",
            "body": (
                "We currently archive entries one by one. "
                "We would like to select multiple entries and "
                "archive them together."
            ),
            "expected": {
                "category": "Feature Request",
                "urgency": "P3",
            },
        },
        {
            "name": "Performance vs integration ambiguity",
            "subject": "External API requests are timing out",
            "body": (
                "Our DataBridge pipeline is timing out when "
                "communicating with an external source API. "
                "The source system appears to be throttling "
                "requests."
            ),
            "expected": {
                "category": "Integration",
                "urgency": "P2",
            },
        },
    ]

    # =====================================================
    # TASK 2 — NORMAL ACCOUNT HEALTH CASES
    # =====================================================

    accounts = load_accounts()

    health_cases = [
        {
            "name": "At-risk account",
            "account_id": "ACC-3336",
            "expected": {
                "account_health_status": "At Risk",
                "usage_trend": "Inactive",
            },
        },
        {
            "name": "Healthy account",
            "account_id": "ACC-3033",
            "expected": {
                "account_health_status": "Healthy",
                "usage_trend": "Increasing",
            },
        },
        {
            "name": "Zero-ticket account",
            "account_id": "ACC-3033",
            "expected": {
                "ticket_count": 0,
                "open_ticket_count": 0,
            },
        },
        {
            "name": "Seat utilization",
            "account_id": "ACC-3033",
            "expected": {
                "seat_utilization_percent": 88.18,
            },
        },
        {
            "name": "Renewal calculation",
            "account_id": "ACC-3336",
            "expected": {
                "days_to_renewal": expected_days_to_renewal(
                    accounts["ACC-3336"]
                ),
            },
        },
    ]

    # =====================================================
    # TASK 2 — ADVERSARIAL CASES
    # =====================================================

    adversarial_health_cases = [
        {
            "name": "Conflicting health signals",
            "account_id": "ACC-3336",
            "expected": {
                "account_health_status": "At Risk",
                "usage_trend": "Inactive",
            },
        },
        {
            "name": "Account-level ticket discrepancy",
            "account_id": "ACC-3033",
            "expected": {
                "ticket_count": 0,
                "open_ticket_count": 0,
            },
        },
    ]

    # =====================================================
    # RUN NORMAL TRIAGE
    # =====================================================

    triage_results = []

    for case in triage_cases:
        triage_results.append(
            evaluate_triage_case(
                case["name"],
                case["subject"],
                case["body"],
                case["expected"],
            )
        )

    # =====================================================
    # RUN ADVERSARIAL TRIAGE
    # =====================================================

    adversarial_triage_results = []

    for case in adversarial_triage_cases:
        adversarial_triage_results.append(
            evaluate_triage_case(
                case["name"],
                case["subject"],
                case["body"],
                case["expected"],
            )
        )

    # =====================================================
    # RUN NORMAL ACCOUNT HEALTH
    # =====================================================

    health_results = []

    for case in health_cases:
        health_results.append(
            evaluate_health_case(
                case["name"],
                case["account_id"],
                case["expected"],
            )
        )

    # =====================================================
    # RUN ADVERSARIAL ACCOUNT HEALTH
    # =====================================================

    adversarial_health_results = []

    for case in adversarial_health_cases:
        adversarial_health_results.append(
            evaluate_health_case(
                case["name"],
                case["account_id"],
                case["expected"],
            )
        )

    # =====================================================
    # TASK 2 EXECUTIVE BRIEF
    # =====================================================

    health_summary_result = evaluate_health_summary_format()

    return {
        "triage": triage_results,
        "account_health": health_results,
        "executive_brief": health_summary_result,
        "adversarial_triage": adversarial_triage_results,
        "adversarial_health": adversarial_health_results,
    }


# =========================================================
# SCORING
# =========================================================

def calculate_score(results):
    valid_results = [
        result
        for result in results
        if result["status"] in {"PASS", "FAIL"}
    ]

    if not valid_results:
        return None

    return (
        sum(result["score"] for result in valid_results)
        / len(valid_results)
    )


def calculate_pass_rate(results):
    valid_results = [
        result
        for result in results
        if result["status"] in {"PASS", "FAIL"}
    ]

    if not valid_results:
        return None

    passed = sum(
        1
        for result in valid_results
        if result["status"] == "PASS"
    )

    return passed / len(valid_results)


# =========================================================
# RESULT PRINTING
# =========================================================

def print_results(title, results):
    print(f"\n{title}")
    print("-" * 70)

    for result in results:
        status = result["status"]

        if result["score"] is None:
            score_text = "N/A"
        else:
            score_text = f"{result['score']:.2f}"

        print(
            f"{status} | "
            f"{result['name']} | "
            f"score={score_text}"
        )

        if status == "FAIL":
            print(
                f"       Expected: {result['expected']}"
            )
            print(
                f"       Actual:   {result['actual']}"
            )

        elif status == "ERROR":
            print(
                f"       Error: {result['error']}"
            )


def print_report(results):

    normal_triage = results["triage"]
    normal_health = results["account_health"]
    executive_brief = results["executive_brief"]

    adversarial_triage = results["adversarial_triage"]
    adversarial_health = results["adversarial_health"]

    all_results = (
        normal_triage
        + normal_health
        + [executive_brief]
        + adversarial_triage
        + adversarial_health
    )

    valid_results = [
        result
        for result in all_results
        if result["status"] in {"PASS", "FAIL"}
    ]

    error_results = [
        result
        for result in all_results
        if result["status"] == "ERROR"
    ]

    passed = sum(
        1
        for result in valid_results
        if result["status"] == "PASS"
    )

    overall_score = calculate_score(all_results)
    overall_pass_rate = calculate_pass_rate(all_results)

    print("EVALUATION REPORT")
    print("=" * 70)

    if overall_score is None:
        print("Overall score: N/A")
    else:
        print(
            f"Overall score: {overall_score:.2f}"
        )

    print(
        f"Passed: {passed}/{len(valid_results)}"
    )

    if overall_pass_rate is None:
        print("Overall pass rate: N/A")
    else:
        print(
            f"Overall pass rate: "
            f"{overall_pass_rate:.2%}"
        )

    print(
        f"Evaluation errors: "
        f"{len(error_results)}"
    )

    scores = {
        "Triage": normal_triage,
        "Account health": normal_health,
        "Executive brief": [executive_brief],
        "Adversarial triage": adversarial_triage,
        "Adversarial health": adversarial_health,
    }

    print("\nSCORES")
    print("-" * 70)

    for name, group in scores.items():
        score = calculate_score(group)
        pass_rate = calculate_pass_rate(group)

        if score is None:
            score_text = "N/A"
        else:
            score_text = f"{score:.2f}"

        if pass_rate is None:
            pass_text = "N/A"
        else:
            pass_text = f"{pass_rate:.2%}"

        print(
            f"{name}: "
            f"score={score_text}, "
            f"pass_rate={pass_text}"
        )

    print_results(
        "TRIAGE",
        normal_triage,
    )

    print_results(
        "ACCOUNT HEALTH",
        normal_health,
    )

    print_results(
        "TASK 2 EXECUTIVE BRIEF",
        [executive_brief],
    )

    print_results(
        "ADVERSARIAL TRIAGE",
        adversarial_triage,
    )

    print_results(
        "ADVERSARIAL ACCOUNT HEALTH",
        adversarial_health,
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    results = run_evaluation()
    print_report(results)