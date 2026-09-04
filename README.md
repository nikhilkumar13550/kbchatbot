Execution Steps (In Order)
1  HTTP Request Trigger
2  APIM validates, authenticates, applies policies, and forwards the request
3.1  Receive request
3.2  Read case from Dataverse
3.3  Run early-exit checks
3.4  Classify case and identify missing fields
3.5  Search Provider Registry API
3.6  Route to Agent 1, Agent 2, or escalate
3.7  Call selected agent through APIM
3.8  Retry and validate response
3.9  Apply guardrails
3.10  Update case and write audit
3.11  Return HTTP response
