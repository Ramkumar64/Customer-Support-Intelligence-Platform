from triage import recommend_responder_team


def test_feature_request():
    team = recommend_responder_team(
        "DataBridge Pro Data Ingestion",
        "Feature Request"
    )

    assert team == "Product Support"


def test_billing():
    team = recommend_responder_team(
        "Billing",
        "Billing"
    )

    assert team == "Billing Support"


def test_integration():
    team = recommend_responder_team(
        "DataBridge Pro",
        "Integration"
    )

    assert team == "Integration Support"


def test_data_loss():
    team = recommend_responder_team(
        "DataBridge Pro",
        "Data Loss"
    )

    assert team == "Technical Support - Data Recovery"


if __name__ == "__main__":
    test_feature_request()
    test_billing()
    test_integration()
    test_data_loss()

    print("All responder-team tests passed.")