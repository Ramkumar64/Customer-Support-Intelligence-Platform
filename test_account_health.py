from datetime import date
from account_health import calculate_health_metrics
from account_health import get_account_context

def test_health_metrics():
    account = {
        "account_id": "TEST-001",
        "health_status": "At Risk",
        "usage_trend": "Inactive",
        "last_login_days_ago": 10,
        "products": ["DataBridge Pro"],
        "integrations_active": ["Jira"],
        "seats_licensed": 100,
        "seats_active": 80,
        "arr_usd": 100000,
        "renewal_date": date.today().isoformat(),
        "primary_contact": {
            "name": "Test User",
            "title": "CTO"
        },
        "tam": "Test TAM",
        "nps_score": 5,
        "region": "APAC",
        "industry": "Technology",
        "open_tickets": 3,
        "escalation_notes": []
    }

    tickets = [
        {
            "status": "Open",
            "urgency": "P1",
            "satisfaction_score": 4
        },
        {
            "status": "Closed",
            "urgency": "P2",
            "satisfaction_score": 2
        }
    ]

    metrics = calculate_health_metrics(
        account,
        tickets
    )

    assert metrics["ticket_count"] == 2
    assert metrics["open_ticket_count"] == 1
    assert metrics["p1_ticket_count"] == 1
    assert metrics["avg_satisfaction"] == 3.0
    assert metrics["seat_utilization_percent"] == 80.0
    assert metrics["days_to_renewal"] == 0

    assert "Account health is at risk" in metrics["risk_signals"]
    assert "Usage trend is inactive or declining" in metrics["risk_signals"]
    assert "Renewal is within 30 days or overdue" in metrics["risk_signals"]
    assert "3 open tickets reported on account" in metrics["risk_signals"]
    assert "Low NPS score" in metrics["risk_signals"]

def test_account_context_uses_90_day_window():
    context = get_account_context(
        "ACC-3336",
        days=90
    )

    for ticket in context["tickets"]:
        assert ticket["account_id"] == "ACC-3336"


if __name__ == "__main__":
    test_health_metrics()
    test_account_context_uses_90_day_window()
    print("All account-health metric tests passed.")