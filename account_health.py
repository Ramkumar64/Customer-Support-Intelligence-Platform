import json
import os
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import types

from data_loader import load_accounts, load_tickets


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)


def get_account_context(account_id, days=90):
    accounts = load_accounts()
    tickets = load_tickets()

    account = accounts.get(account_id)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    account_tickets = [
        ticket
        for ticket in tickets
        if (
            ticket["account_id"] == account_id
            and datetime.fromisoformat(
                ticket["created_at"].replace("Z", "+00:00")
            ) > cutoff
        )
    ]

    return {
        "account": account,
        "tickets": account_tickets,
    }


def calculate_health_metrics(account, tickets):
    if account is None:
        return {
            "ticket_count": len(tickets),
            "open_ticket_count": sum(
                1
                for ticket in tickets
                if ticket["status"].lower()
                not in {"closed", "resolved"}
            ),
            "p1_ticket_count": sum(
                1
                for ticket in tickets
                if ticket["urgency"] == "P1"
            ),
            "avg_satisfaction": None,
        }

    satisfaction_scores = [
        ticket["satisfaction_score"]
        for ticket in tickets
        if ticket["satisfaction_score"] is not None
    ]

    renewal_date = date.fromisoformat(account["renewal_date"])
    days_to_renewal = (renewal_date - date.today()).days

    seat_utilization = (
        round(
            account["seats_active"]
            / account["seats_licensed"]
            * 100,
            2,
        )
        if account["seats_licensed"] > 0
        else None
    )

    risk_signals = []

    if account["health_status"].lower() in {"at risk", "red"}:
        risk_signals.append("Account health is at risk")

    if account["usage_trend"].lower() in {
        "inactive",
        "declining",
    }:
        risk_signals.append(
            "Usage trend is inactive or declining"
        )

    if days_to_renewal <= 30:
        risk_signals.append(
            "Renewal is within 30 days or overdue"
        )

    if account["open_tickets"] > 0:
        risk_signals.append(
            f"{account['open_tickets']} open tickets reported on account"
        )

    if (
        account["nps_score"] is not None
        and account["nps_score"] < 7
    ):
        risk_signals.append("Low NPS score")

    return {
        "ticket_count": len(tickets),
        "open_ticket_count": sum(
            1
            for ticket in tickets
            if ticket["status"].lower()
            not in {"closed", "resolved"}
        ),
        "p1_ticket_count": sum(
            1
            for ticket in tickets
            if ticket["urgency"] == "P1"
        ),
        "avg_satisfaction": (
            round(
                sum(satisfaction_scores)
                / len(satisfaction_scores),
                2,
            )
            if satisfaction_scores
            else None
        ),
        "account_health_status": account["health_status"],
        "usage_trend": account["usage_trend"],
        "last_login_days_ago": account["last_login_days_ago"],
        "products": account["products"],
        "integrations_active": account["integrations_active"],
        "seats_licensed": account["seats_licensed"],
        "seats_active": account["seats_active"],
        "seat_utilization_percent": seat_utilization,
        "arr_usd": account["arr_usd"],
        "renewal_date": account["renewal_date"],
        "days_to_renewal": days_to_renewal,
        "primary_contact": account["primary_contact"],
        "tam": account["tam"],
        "nps_score": account["nps_score"],
        "region": account["region"],
        "industry": account["industry"],
        "risk_signals": risk_signals,
        "escalation_notes": account["escalation_notes"],
    }


def build_ticket_evidence(tickets):
    evidence = []

    churn_keywords = {
        "churn",
        "competitor",
        "competing",
        "switching",
        "replace",
        "alternative",
        "cancel",
        "cancellation",
        "renewal",
    }

    escalation_keywords = {
        "escalat",
        "executive",
        "urgent",
        "critical",
        "p1",
        "blocked",
        "outage",
        "data loss",
        "lost data",
    }

    for ticket in tickets:
        text = (
            f"{ticket.get('subject', '')} "
            f"{ticket.get('body', '')}"
        )

        text_lower = text.lower()

        churn_match = any(
            keyword in text_lower
            for keyword in churn_keywords
        )

        escalation_match = (
            ticket.get("urgency") == "P1"
            or any(
                keyword in text_lower
                for keyword in escalation_keywords
            )
        )

        if churn_match or escalation_match:
            reasons = []

            if churn_match:
                reasons.append("churn-risk signal")

            if escalation_match:
                reasons.append("escalation signal")

            evidence.append(
                {
                    "ticket_id": ticket.get("ticket_id"),
                    "subject": ticket.get("subject"),
                    "status": ticket.get("status"),
                    "urgency": ticket.get("urgency"),
                    "reason": ", ".join(reasons),
                    "quote": ticket.get("body", "").strip(),
                }
            )

    return evidence


def generate_health_summary(account, metrics, tickets):
    prompt = f"""
You are a Technical Account Manager preparing an executive account-health brief.

Use ONLY the supplied account data, calculated metrics, and ticket data.

Do not invent facts, dates, numbers, risks, customer commitments, or actions.

Every factual statement must be directly supported by the supplied data.

IMPORTANT:
- Account-level values and ticket-derived values may differ.
- If they differ, explicitly acknowledge the discrepancy.
- Do not infer causality.
- Do not claim an action has already been taken.
- Recommendations must be clearly presented as recommendations.
- Only flag churn risk or escalation signals when the supplied ticket data
  provides evidence.
- Every churn-risk or escalation flag MUST include a short DIRECT QUOTE from
  the relevant ticket body or subject.
- Do not create or paraphrase a quote.
- If there are no supported churn or escalation signals, say "None identified."

ACCOUNT:
{json.dumps(account, indent=2)}

CALCULATED METRICS:
{json.dumps(metrics, indent=2)}

RECENT TICKETS:
{json.dumps(tickets, indent=2)}

Write a concise executive brief with exactly these sections:

EXECUTIVE SUMMARY
Write exactly 3 to 5 complete sentences in ONE paragraph.
Do NOT use bullets, numbered lists, subheadings, labels, or line breaks
inside this section.
The paragraph should summarize the account's current health, usage,
support/customer signals, renewal position, and the most important
evidence-based concern where applicable.

OPEN RISKS & FLAGGED ISSUES
- List the most important evidence-based risks and flagged issues.
- Clearly distinguish account-level signals from ticket-derived signals.
- If account-level data conflicts with calculated ticket metrics,
  explicitly describe the discrepancy.
- Do not invent risks.

RECOMMENDED TALKING POINTS
- Provide practical next actions for the TAM.
- Recommendations must be based on the supplied evidence.
- Do not claim that any action has already been taken.

DATA QUALITY NOTES
- Mention important missing or contradictory data.
- If there are no important issues, write "None".

IMPORTANT FORMAT RULE:
The EXECUTIVE SUMMARY MUST contain exactly 3–5 sentences
and MUST be a single paragraph.

Keep the entire brief concise and executive-friendly.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="text/plain",
            temperature=0
        )
    )

    summary = response.text.strip()

    if not summary:
        raise RuntimeError(
            "Gemini returned an empty account-health summary"
        )

    required_sections = [
        "EXECUTIVE SUMMARY",
        "OPEN RISKS & FLAGGED ISSUES",
        "RECOMMENDED TALKING POINTS"
    ]

    missing_sections = [
        section
        for section in required_sections
        if section not in summary
    ]

    if missing_sections:
        raise RuntimeError(
            "Gemini account-health summary is missing required sections: "
            f"{missing_sections}"
        )

    return summary

def summarize_account(account_id):
    context = get_account_context(account_id)

    if context["account"] is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    metrics = calculate_health_metrics(
        context["account"],
        context["tickets"],
    )

    summary = generate_health_summary(
        context["account"],
        metrics,
        context["tickets"]
    )

    return {
        "account_id": account_id,
        "account": context["account"],
        "tickets": context["tickets"],
        "metrics": metrics,
        "summary": summary,
    }


if __name__ == "__main__":
    account_id = "ACC-3336"

    result = summarize_account(account_id)

    print("ACCOUNT HEALTH SUMMARY")
    print("=" * 70)
    print(result["summary"])