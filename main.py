import argparse
import json

from data_loader import load_tickets
from triage import triage_ticket
from account_health import summarize_account


def run_triage():
    tickets = load_tickets()

    if not tickets:
        raise RuntimeError("No tickets found in dataset")

    ticket = tickets[0]

    result = triage_ticket(
        ticket["subject"],
        ticket["body"]
    )

    print("TASK 1 — TICKET TRIAGE")
    print("=" * 70)
    print(json.dumps(result, indent=2))


def run_account_health(account_id):
    result = summarize_account(account_id)

    print("TASK 2 — ACCOUNT HEALTH")
    print("=" * 70)

    print("\nCALCULATED METRICS")
    print("-" * 70)
    print(json.dumps(result["metrics"], indent=2))

    print("\nEXECUTIVE BRIEF")
    print("-" * 70)
    print(result["summary"])


def main():
    parser = argparse.ArgumentParser(
        description="Customer Operations AI Pipeline"
    )

    parser.add_argument(
        "--task",
        choices=["triage", "health"],
        required=True,
        help="Task to execute"
    )

    parser.add_argument(
        "--account-id",
        default="ACC-3336",
        help="Account ID for health analysis"
    )

    args = parser.parse_args()

    if args.task == "triage":
        run_triage()
    elif args.task == "health":
        run_account_health(args.account_id)


if __name__ == "__main__":
    main()