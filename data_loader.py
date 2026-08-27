import json
from datetime import datetime, timedelta, timezone

# ---- Function 1: Load all tickets from the JSON file ----
def load_tickets():
    with open("data/tickets.json", "r", encoding="utf-8") as f:
        tickets = json.load(f)
    return tickets  # returns a list of ticket dictionaries

# ---- Function 2: Load all accounts, keyed by account_id for instant lookup ----
def load_accounts():
    with open("data/accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)
    # Convert the list into a dictionary: {account_id: account_dict}
    # This means account_map["ACC-3847"] instantly gives you that account
    # instead of looping through all 50 every time.
    account_map = {a["account_id"]: a for a in accounts}
    return account_map

# ---- Function 3: Get one account's tickets from the last N days ----
# Instead of measuring from "today" (which would miss this historical
# dataset entirely), we measure from the most recent ticket date in the
# data itself. This makes the filter meaningful regardless of when you
# run the code.
def get_account_tickets(account_id, tickets, days=90):
    all_dates = [
        datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        for t in tickets
    ]
    reference_date = max(all_dates)  # the "most recent" point in this dataset
    cutoff = reference_date - timedelta(days=days)

    result = []
    for t in tickets:
        if t["account_id"] != account_id:
            continue
        ticket_date = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
        if ticket_date > cutoff:
            result.append(t)
    return result
# ---- Quick test block: only runs if you execute this file directly ----
if __name__ == "__main__":
    tickets = load_tickets()
    accounts = load_accounts()

    print(f"Loaded {len(tickets)} tickets")
    print(f"Loaded {len(accounts)} accounts")

    # Try it on the very first ticket's account_id, just to see it work
    sample_account_id = list(accounts.keys())[0]
    print(f"\nLooking up account: {sample_account_id}")
    account = accounts.get(sample_account_id)
    if account:
        print(f"Found account: {account['company']}, health: {account['health_status']}")
    else:
        print("This account_id has no matching account (this is expected sometimes)")

    recent = get_account_tickets(sample_account_id, tickets, days=90)
    print(f"\n{sample_account_id} has {len(recent)} tickets in the last 90 days")