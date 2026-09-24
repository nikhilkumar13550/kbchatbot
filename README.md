Usage
Online webpage
GET /process exposes a browser-based console to use the service without any programming required. It supports OCR, Document Classification, and Data Extraction via a point-and-click form with built-in Entra ID SSO.

Deep-links to specific actions:

https://{deploymentURL}/process?action=ocr
https://{deploymentURL}/process?action=classify
https://{deploymentURL}/process?action=dataextraction
Demo (url below is for the Create environment deployment):

https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/process
Companion pages: /ssotoken (get a JWT for curl/Postman) · /admin (access-log browser)

Onboarding / Access
Sign-in via SSO requires membership in the Entra ID ACL group app_prod_akka_proj_gwam_doc_proc-r on the enterprise application GFT-gaip-doc-proc-svc-PRD_SP. Contact your team lead or a service maintainer to request access.

📖 Full walkthrough: docs/web-ui.md

From Akka service
If your service uses Akka, you can use the doc-processing-service-client directly. See doc-processing-service-client for usage instructions.

HTTP client
https://{deploymentURL}/doc-processing/{endpoint-path}

HTTP:

POST /doc-processing/ocr
POST /doc-processing/classify
POST /doc-processing/extract
GET /health — unauthenticated liveness check returning { "status": "UP" }
The specifications of the HTTP API are exported with OpenAPI:

openapi.yaml for full specification of the endpoints.

https://{deploymentURL}/openapi.html for a human-friendly (SwaggerUI) rendering of the OpenAPI specs. For Canada cac region: https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/openapi.html

For API calls to /doc-processing/* (and /mcp), a JWT must be present in the HTTP Authorization header: Authorization: Bearer <your_jwt_token_here>

GET /health does not require authentication and is intended for load balancers, liveness probes, and uptime monitoring.

Service-to-Service JWT Token Authentication
Your service needs to obtain a JWT and include it as a Bearer token in the Authorization header of HTTP and MCP API calls.

# Constant Manulife Tenant
export AZURE_TENANT_ID=5d3e2773-e07f-4432-a630-1a0f68a28a05
# Constant doc-processing-service App ID
export ENTRA_APPLICATION_ID=fd755477-f7ed-470c-9980-0fa0928e7300

# Your Azure service credentials
export AZURE_CLIENT_ID=<...>
export AZURE_CLIENT_SECRET=<...>

curl -s -X POST \
  "https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=${AZURE_CLIENT_ID}" \
  -d "client_secret=${AZURE_CLIENT_SECRET}" \
  -d "scope=api://${ENTRA_APPLICATION_ID}/.default" \
  | jq -r '.access_token'
The resulting token must have these properties:

aud: fd755477-f7ed-470c-9980-0fa0928e7300
iss: https://login.microsoftonline.com/5d3e2773-e07f-4432-a630-1a0f68a28a05/v2.0
roles: ["Users"]
Granting access to your service
Before your service can obtain a valid token with the Users role, your Azure SPN must be authorized on the doc-processing-service app registration. This is a one-time setup:

Add API permission on your SPN's App Registration: In the Azure portal, open your SPN's App Registration page → API permissions → Add a permission. Under the APIs my organization uses tab, search for GFT-gaip-doc-proc-svc-PRD_SP and select the Users permission. The status will appear as Not granted for Manulife.

Submit a SNOW request to get the permission approved: Create a Single-Sign On Services (Global) SNOW request:

Select Modify Azure AD service principal
Write: "Please grant GFT-gaip-doc-proc-svc-PRD_SP for manulife to {YOUR_CLIENT_SPN}. Please see attached screenshot."
Attach a screenshot of the API permissions page (from step 1), highlighting the Not granted for Manulife status.
Once processed, your SPN is added to the Users and groups list on the GFT-gaip-doc-proc-svc-PRD_SP Enterprise Application, and the permission status changes to Granted for Manulife.

Verify: Tokens issued to your SPN will now contain "roles": ["Users"].

MCP
The capabilities are exposed as MCP tools on /mcp path. Following the MCP protocol, the tools are inspectable. For example with MCP-inspector:

npx @modelcontextprotocol/inspector

mcp-inspector.png

Bruno
