import os
import json

from dotenv import load_dotenv
from google import genai
from data_loader import load_tickets
from kb_loader import load_knowledge_base
from kb_retriever import search_knowledge_base
from google.genai import types

KB_MATCH_THRESHOLD = 0.10

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)


CATEGORY_DEFINITIONS = """
Bug:
Existing functionality is failing, broken, or behaving incorrectly.

Feature Request:
The customer wants functionality that does not currently exist.

How-To:
The customer is asking how to use an existing capability.

Performance:
Existing functionality is unusually slow, timing out, or degrading.

Billing:
The issue concerns charges, invoices, subscriptions, credits, pricing, or payments.

Integration:
The issue involves connecting to or communicating with another system, API, connector, or external service.

Onboarding:
The issue concerns initial setup, configuration, implementation, or getting started.

Data Loss:
Customer data is missing, deleted, corrupted, or otherwise lost.
"""


URGENCY_DEFINITIONS = """
P1:
Critical outage, severe data loss, security incident, or widespread
customer-impacting failure requiring immediate intervention.

P2:
High-impact issue affecting important functionality or a significant
customer workflow, especially when the ticket explicitly describes:
- production impact,
- repeated failures,
- timeouts,
- blocked or degraded workflows,
- significant user impact,
- service interruption,
- urgent operational impact.

P3:
Normal-impact issue, limited scope, workaround available, or non-critical
feature request.

For Billing issues specifically:
- A normal invoice, charge, payment, subscription, or billing question
  without evidence of substantial business impact is P3.
- Do not classify a normal billing discrepancy as P4 merely because it
  is informational or does not affect product functionality.
- Use P2 or P1 for billing issues only when the ticket explicitly
  provides evidence of significant or critical operational/business
  impact consistent with the P2/P1 definitions.

P4:
Low-priority question, minor request, cosmetic issue, or general
information where there is no meaningful customer-impacting problem.

IMPORTANT URGENCY RULE:
Choose urgency ONLY from evidence explicitly present in the ticket.
Do not infer severity merely because the customer uses words such as
"urgent", "critical", or "ASAP".

When a ticket explicitly describes a significant operational problem
such as production timeouts, repeated failures, blocked workflows,
or substantial customer impact, prefer P2 over P3 unless the evidence
clearly supports P1.

For ordinary billing issues with no explicit substantial impact,
prefer P3 over P4.
"""


def classify_ticket(subject, body):
    ticket_text = f"Subject: {subject}\n\nBody: {body}"

    prompt = f"""
You are a technical support ticket triage assistant.

Classify the ticket using ONLY the information contained in the ticket.

Do not invent facts.

{CATEGORY_DEFINITIONS}

{URGENCY_DEFINITIONS}

TICKET:
{ticket_text}

Return ONLY valid JSON with exactly these fields:

{{
  "product_area": "the product or module involved",
  "category": "Bug | Feature Request | How-To | Performance | Billing | Integration | Onboarding | Data Loss",
  "urgency": "P1 | P2 | P3 | P4",
  "reasoning": "brief explanation based only on evidence in the ticket"
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini returned invalid classification JSON: {response.text}"
        ) from e

    required_fields = {
        "product_area",
        "category",
        "urgency",
        "reasoning"
    }

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise RuntimeError(
            f"Gemini classification response is missing fields: {sorted(missing_fields)}"
        )
        
    valid_categories = {
        "Bug",
        "Feature Request",
        "How-To",
        "Performance",
        "Billing",
        "Integration",
        "Onboarding",
        "Data Loss"
    }

    valid_urgencies = {
        "P1",
        "P2",
        "P3",
        "P4"
    }

    if result["category"] not in valid_categories:
        raise RuntimeError(
            f"Invalid category returned by Gemini: {result['category']}"
        )

    if result["urgency"] not in valid_urgencies:
        raise RuntimeError(
            f"Invalid urgency returned by Gemini: {result['urgency']}"
        )

    return result

def evaluate_kb_match(ticket_text, kb_document):
    prompt = f"""
You are evaluating whether a support ticket matches a known issue
documented in an internal knowledge base.

Use ONLY the ticket and the supplied knowledge-base document.

Do not invent a solution that is not present in the document.

TICKET:
{ticket_text}

KNOWLEDGE-BASE DOCUMENT:
{kb_document}

Return ONLY valid JSON with exactly these fields:

{{
  "known_issue_match": true,
  "reason": "brief explanation of why the ticket does or does not match a documented issue",
  "relevant_section": "the relevant section heading, or empty string if there is no match"
}}

Set "known_issue_match" to true ONLY when the KB actually documents
the same issue, error, symptom, or directly applicable solution.
"""
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini returned invalid KB-match JSON: {response.text}"
        ) from e

    required_fields = {
        "known_issue_match",
        "reason",
        "relevant_section"
    }

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise RuntimeError(
            f"Gemini KB-match response is missing fields: {sorted(missing_fields)}"
        )

    if not isinstance(result["known_issue_match"], bool):
        raise RuntimeError(
            "Gemini KB-match response must use a boolean for known_issue_match"
        )

    return result

def recommend_responder_team(product_area, category):
    category = category.lower()
    product_area = product_area.lower()

    if category == "billing":
        return "Billing Support"

    if category == "integration":
        return "Integration Support"

    if category == "onboarding":
        return "Onboarding Support"

    if category == "data loss":
        return "Technical Support - Data Recovery"

    if category == "performance":
        return "Technical Support - Performance"

    if category == "feature request":
        return "Product Support"

    if category == "how-to":
        return "Technical Support"

    if category == "bug":
        return "Technical Support"

    return "Technical Support"

def generate_first_response(
    subject,
    body,
    classification,
    kb_match,
    kb_document
):
    if kb_match["known_issue_match"]:
        kb_context = kb_document
    else:
        kb_context = "No directly applicable known issue was found in the knowledge base."

    prompt = f"""
You are a technical support agent drafting the first response to a customer.

Use ONLY the ticket information and supplied knowledge-base information.

Do not invent product behavior, fixes, timelines, policies, or workarounds.

TICKET:
Subject: {subject}

Body:
{body}

TRIAGE:
{json.dumps(classification, indent=2)}

KNOWLEDGE-BASE MATCH:
{json.dumps(kb_match, indent=2)}

KNOWLEDGE-BASE CONTENT:
{kb_context}

Write a concise, professional first-response message.

Requirements:
- Acknowledge the customer's request or problem.
- Demonstrate that you understood the issue.
- If a documented KB solution exists, provide only that documented guidance.
- If no documented solution exists, do not pretend one exists.
- For a feature request, acknowledge the request and explain that it will be routed to the appropriate team.
- Never claim that a request was logged, created, escalated, or submitted unless the system actually performed that action.
- Do not promise a delivery date.
- Do not mention that you are an AI.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0
        )
    )

    first_response = response.text.strip()

    if not first_response:
        raise RuntimeError(
            "Gemini returned an empty first-response message"
        )

    return first_response

def triage_ticket(subject, body):
    documents = load_knowledge_base()

    ticket_text = (
        f"Subject: {subject}\n\n"
        f"Body: {body}"
    )

    classification = classify_ticket(
        subject,
        body
    )

    kb_results = search_knowledge_base(
        ticket_text,
        documents
    )

    top_kb = kb_results[0]

    if top_kb["score"] >= KB_MATCH_THRESHOLD:
        kb_document = top_kb["content"]

        kb_match = evaluate_kb_match(
            ticket_text,
            kb_document
        )
    else:
        kb_document = ""

        kb_match = {
            "known_issue_match": False,
            "reason": "No sufficiently relevant knowledge-base document was found.",
            "relevant_section": ""
        }

    responder_team = recommend_responder_team(
        classification["product_area"],
        classification["category"]
    )

    first_response = generate_first_response(
        subject,
        body,
        classification,
        kb_match,
        kb_document
    )

    return {
        "classification": {
            "product_area": classification["product_area"],
            "category": classification["category"],
            "urgency": classification["urgency"],
            "reasoning": classification["reasoning"]
        },
        "knowledge_base": {
            "retrieval_score": round(top_kb["score"], 4),
            "document": top_kb["path"],
            "known_issue_match": kb_match["known_issue_match"],
            "reason": kb_match["reason"],
            "relevant_section": kb_match["relevant_section"]
        },
        "responder_team": responder_team,
        "first_response": first_response
    }
    

if __name__ == "__main__":
    from data_loader import load_tickets

    tickets = load_tickets()
    sample = tickets[0]

    result = triage_ticket(
        sample["subject"],
        sample["body"]
    )

    print("COMPLETE TRIAGE RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=2))