# Design Note — Customer Operations AI Pipeline

## 1. Production Failure Modes, Detection, and Mitigation

### 1.1 LLM/API failure

The ticket-triage pipeline depends on the Gemini API for classification and response generation. Production failures could include API timeouts, rate limits, quota exhaustion, authentication failures, or malformed model responses.

These failures should be detected through request timeouts, HTTP/API error handling, response validation, and structured application logs. The system should retry transient failures with exponential backoff and a bounded retry count. Rate-limit and quota errors should not be retried indefinitely. For persistent failures, the system should return a safe fallback classification or route the ticket for manual review rather than silently dropping the request.

### 1.2 Incorrect or inconsistent model classification

An LLM may classify an ambiguous ticket incorrectly, particularly when multiple categories or urgency levels appear plausible. This is important because urgency affects support prioritisation and responder-team routing.

The system should validate model output against the allowed category and urgency enums. Temperature should remain low for classification, and evaluation cases should cover ambiguous tickets. High-impact classifications such as P1 should also be eligible for human review. Evaluation results should be monitored over time so that degradation in classification quality can be detected.

### 1.3 Data inconsistency or missing customer data

Account and ticket data can be incomplete or contradictory. For example, an account may report open tickets while the retrieved ticket records contain fewer or no open tickets. Renewal dates and calculated metrics can also become inconsistent if source data is stale.

The pipeline should distinguish source data from calculated metrics, preserve missing values as unknown rather than inventing values, and explicitly surface contradictions in the account-health output. Data-quality checks should be logged and monitored so that upstream data problems can be corrected.

## 2. Latency vs Quality Trade-off

The highest-quality workflow would use an LLM for classification, knowledge-base reasoning, and response generation, but multiple sequential model calls increase latency and API cost.

For ticket triage, classification should be kept lightweight and deterministic where possible. Knowledge-base retrieval can be performed locally using the available corpus before invoking the LLM. The retrieved documents can then be supplied to the model instead of sending the entire knowledge base.

For production use, latency-sensitive operations could use a smaller/faster model for straightforward classification and reserve a stronger model for ambiguous or high-impact tickets. Caching can also reduce repeated retrieval and generation work for similar requests.

The goal is not simply minimum latency. A slightly slower response is justified when additional reasoning materially improves routing accuracy or prevents an incorrect P1/P2 classification. The appropriate balance should therefore depend on ticket urgency and operational impact.

## 3. Data Sensitivity and PII

The pipeline processes customer-support information that may contain sensitive business information and potentially personally identifiable information such as contact names, email addresses, or information included in ticket bodies.

Only the minimum data required for classification and account-health analysis should be sent to the model. Sensitive fields that are not required for the task should be excluded or redacted where possible.

API keys must never be committed to source control. Secrets should be provided through environment variables, with `.env` excluded through `.gitignore` and `.env.example` containing only a placeholder.

Production logging should also avoid recording complete ticket bodies, credentials, tokens, or unnecessary customer information. Access to customer data and generated account-health summaries should follow least-privilege principles, with appropriate retention and audit controls.

## 4. Scaling to 10× Volume

At 10× the current ticket volume, the main constraints would be LLM request throughput, API quotas, latency, and concurrent processing.

The current architecture separates data loading, knowledge-base retrieval, deterministic account-health calculations, and LLM-based reasoning. This separation provides a useful foundation for scaling.

Knowledge-base documents should be loaded and indexed once rather than rebuilding retrieval structures for every ticket. Retrieval can then operate against the reusable index. LLM calls should be bounded with concurrency limits, retries, and backoff so that traffic spikes do not overwhelm the API.

For larger deployments, ticket processing could be placed behind a queue and processed by horizontally scalable workers. Results could be persisted so that failed jobs can be retried without reprocessing successful tickets.

Account-health calculations are primarily deterministic and can be performed without an LLM, which keeps their cost and latency predictable. LLM usage should be reserved for the parts that benefit from language reasoning, while monitoring throughput, error rate, latency, token usage, and classification quality as volume increases.