import json

import streamlit as st

from data_loader import load_accounts, load_tickets
from triage import triage_ticket
from account_health import summarize_account


st.set_page_config(
    page_title="Customer Operations AI",
    page_icon="🎫",
    layout="wide",
)


# =========================================================
# PAGE HEADER
# =========================================================

st.title("Customer Operations AI Pipeline")
st.caption(
    "AI-assisted ticket triage and TAM account-health analysis"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Workflow")

task = st.sidebar.radio(
    "Select a workflow",
    [
        "Ticket Triage",
        "Account Health",
    ],
)


# =========================================================
# TASK 1 — TICKET TRIAGE
# =========================================================

if task == "Ticket Triage":

    st.header("🎫 Ticket Triage")
    st.write(
        "Classify a support ticket, identify urgency, "
        "find relevant knowledge-base guidance, and generate "
        "a recommended first response."
    )

    tickets = load_tickets()

    if not tickets:
        st.error("No tickets found in the dataset.")
        st.stop()

    ticket_options = {
        f"{ticket['ticket_id']} — {ticket['subject']}": ticket
        for ticket in tickets
    }

    selected_label = st.selectbox(
        "Select a support ticket",
        list(ticket_options.keys()),
    )

    ticket = ticket_options[selected_label]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ticket Details")

        st.text_input(
            "Ticket ID",
            value=ticket["ticket_id"],
            disabled=True,
        )

        st.text_input(
            "Company",
            value=ticket["company"],
            disabled=True,
        )

        st.text_input(
            "Subject",
            value=ticket["subject"],
            disabled=True,
        )

    with col2:
        st.subheader("Ticket Content")

        st.text_area(
            "Ticket body",
            value=ticket["body"],
            height=180,
            disabled=True,
        )

    if st.button(
        "Run Ticket Triage",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner("Analyzing ticket..."):

            try:
                result = triage_ticket(
                    ticket["subject"],
                    ticket["body"],
                )

            except Exception as e:
                st.error(
                    "Ticket triage failed. "
                    "Please check the Gemini API configuration "
                    "and quota."
                )
                st.exception(e)
                st.stop()

        st.success("Ticket triage completed.")

        st.subheader("Classification")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Category",
                result["classification"]["category"],
            )

        with c2:
            st.metric(
                "Urgency",
                result["classification"]["urgency"],
            )

        with c3:
            st.metric(
                "Responder Team",
                result["responder_team"],
            )

        st.subheader("Reasoning")

        st.write(
            result["classification"]["reasoning"]
        )

        st.subheader("Knowledge Base")

        kb = result["knowledge_base"]

        kb1, kb2 = st.columns(2)

        with kb1:
            st.metric(
                "Retrieval Score",
                kb["retrieval_score"],
            )

        with kb2:
            st.write(
                f"**Document:** `{kb['document']}`"
            )

        st.write(
            f"**Known Issue Match:** "
            f"{kb['known_issue_match']}"
        )

        st.write(
            f"**Reason:** {kb['reason']}"
        )

        if kb.get("relevant_section"):
            with st.expander(
                "Relevant Knowledge-Base Section"
            ):
                st.write(kb["relevant_section"])

        st.subheader("Recommended First Response")

        st.info(
            result["first_response"]
        )

        with st.expander("Raw JSON Result"):
            st.json(result)


# =========================================================
# TASK 2 — ACCOUNT HEALTH
# =========================================================

else:

    st.header("🏢 Account Health")
    st.write(
        "Review customer account health, calculated support "
        "metrics, risk signals, data-quality issues, and "
        "the executive TAM brief."
    )

    accounts = load_accounts()

    if not accounts:
        st.error("No accounts found in the dataset.")
        st.stop()

    account_options = {
        f"{account_id} — {account['company']}": account_id
        for account_id, account in accounts.items()
    }

    selected_account_label = st.selectbox(
        "Select customer account",
        list(account_options.keys()),
    )

    account_id = account_options[
        selected_account_label
    ]

    account = accounts[account_id]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Plan",
            account["plan_tier"],
        )

    with col2:
        st.metric(
            "ARR",
            f"${account['arr_usd']:,}",
        )

    with col3:
        st.metric(
            "Health",
            account["health_status"],
        )

    with col4:
        st.metric(
            "Usage Trend",
            account["usage_trend"],
        )

    st.divider()

    if st.button(
        "Generate Account Health Brief",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Calculating account health and generating executive brief..."
        ):

            try:
                result = summarize_account(account_id)

            except Exception as e:
                st.error(
                    "Account-health analysis failed. "
                    "Please check the Gemini API configuration "
                    "and quota."
                )
                st.exception(e)
                st.stop()

        st.success("Account-health analysis completed.")

        metrics = result["metrics"]

        st.subheader("Key Metrics")

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.metric(
                "Recent Tickets",
                metrics["ticket_count"],
            )

        with m2:
            st.metric(
                "Open Tickets",
                metrics["open_ticket_count"],
            )

        with m3:
            st.metric(
                "P1 Tickets",
                metrics["p1_ticket_count"],
            )

        with m4:
            utilization = metrics[
                "seat_utilization_percent"
            ]

            st.metric(
                "Seat Utilization",
                (
                    f"{utilization:.2f}%"
                    if utilization is not None
                    else "N/A"
                ),
            )

        m5, m6, m7, m8 = st.columns(4)

        with m5:
            st.metric(
                "Days to Renewal",
                metrics["days_to_renewal"],
            )

        with m6:
            nps = metrics["nps_score"]

            st.metric(
                "NPS",
                nps if nps is not None else "N/A",
            )

        with m7:
            st.metric(
                "Active Seats",
                metrics["seats_active"],
            )

        with m8:
            st.metric(
                "Licensed Seats",
                metrics["seats_licensed"],
            )

        st.subheader("Executive Brief")

        st.markdown(
            result["summary"]
        )

        st.subheader("Risk Signals")

        risk_signals = metrics.get(
            "risk_signals",
            [],
        )

        if risk_signals:

            for risk in risk_signals:
                st.warning(risk)

        else:
            st.success(
                "No calculated risk signals identified."
            )

        st.subheader("Escalation Notes")

        escalation_notes = metrics.get(
            "escalation_notes",
            [],
        )

        if escalation_notes:

            for note in escalation_notes:
                st.info(note)

        else:
            st.write("None")

        st.subheader("Customer Context")

        context_col1, context_col2 = st.columns(2)

        with context_col1:
            st.write(
                f"**TAM:** {metrics['tam']}"
            )

            st.write(
                f"**Primary Contact:** "
                f"{metrics['primary_contact']['name']} "
                f"({metrics['primary_contact']['title']})"
            )

            st.write(
                f"**Region:** {metrics['region']}"
            )

            st.write(
                f"**Industry:** {metrics['industry']}"
            )

        with context_col2:
            st.write(
                f"**Products:** "
                f"{', '.join(metrics['products'])}"
            )

            st.write(
                f"**Integrations:** "
                f"{', '.join(metrics['integrations_active'])}"
            )

            st.write(
                f"**Renewal Date:** "
                f"{metrics['renewal_date']}"
            )

            st.write(
                f"**Last Login:** "
                f"{metrics['last_login_days_ago']} days ago"
            )

        with st.expander("Raw Metrics JSON"):
            st.json(metrics)

        with st.expander("Raw Account JSON"):
            st.json(result["account"])