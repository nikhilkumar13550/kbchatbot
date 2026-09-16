# Web Console (`/process`) — User Guide

The `/process` endpoint serves a browser-based console that lets you use the
doc-processing-service **without writing any code**.  It wraps the same
`POST /doc-processing/{ocr,classify,extract}` HTTP API that developers call
directly, but exposes it as a point-and-click form with built-in Entra ID SSO.

---

## Table of contents

1. [Access URLs](#access-urls)
2. [Onboarding / Access Control (ACL)](#onboarding--access-control-acl)
3. [Signing in (SSO)](#signing-in-sso)
4. [Using the OCR tab](#using-the-ocr-tab)
5. [Using the Classify tab](#using-the-classify-tab)
6. [Using the Data Extraction tab](#using-the-data-extraction-tab)
7. [Companion pages](#companion-pages)
8. [Troubleshooting](#troubleshooting)

---

## Access URLs

The console is available at:

```
https://{deploymentURL}/process
```

You can deep-link directly to a specific action:

| Action | URL |
|---|---|
| OCR | `https://{deploymentURL}/process?action=ocr` |
| Classify | `https://{deploymentURL}/process?action=classify` |
| Data Extraction | `https://{deploymentURL}/process?action=dataextraction` |

**Currently-known demo deployment (Canada `cac` region):**

```
https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/process
```

---

## Onboarding / Access Control (ACL)

The `/process` console (and the underlying `/doc-processing/*` API) is protected
by an Entra ID enterprise application.  Before you can sign in you must be added
to the ACL group for that app.

| Item | Value |
|---|---|
| ACL group | `app_prod_akka_proj_gwam_doc_proc-r` |
| Enterprise app name | **GFT-gaip-doc-proc-svc-PRD_SP** |
| Azure portal link | [Open in Azure portal](https://portal.azure.com/#view/Microsoft_AAD_IAM/ManagedAppMenuBlade/~/Users/objectId/de8844fb-2d07-4bb1-a21d-68b92e9d8be1/appId/fd755477-f7ed-470c-9980-0fa0928e7300) |
| Tenant ID | `5d3e2773-e07f-4432-a630-1a0f68a28a05` |
| App (client) ID | `fd755477-f7ed-470c-9980-0fa0928e7300` |

**How to request access:**

1. Contact your team lead or the doc-processing-service maintainers and ask to
   be added to the ACL group `app_prod_akka_proj_gwam_doc_proc-r`.
2. Once added, open the `/process` URL and click **Sign in** — Entra ID will
   issue you a token automatically.

> **Note for service accounts / SPNs:** If you need machine-to-machine access
> (curl, Postman, CI pipelines) rather than interactive SSO, follow the
> service-to-service onboarding steps in the root
> [README § Service-to-Service JWT Token Authentication](../README.md#service-to-service-jwt-token-authentication).

---

## Signing in (SSO)

1. Open any `/process` URL.
2. Click **Sign in** in the top-right header.
3. MSAL.js opens a popup targeting Entra ID.  Sign in with your Manulife
   credentials.
4. On success, the header shows your signed-in account and every subsequent API call
   automatically includes an `Authorization` header containing the bearer access token.

The page fetches its Entra configuration (`tenantId`, `clientId`, `scope`) from
`/auth-config.json` at load time — this is served by `AuthEndpoint` and is the
same config used by the `/ssotoken` helper page.

> **Redirect URIs:** The Entra app has `/process` and `/ssotoken` registered as
> Single-page Application (SPA) platform redirects.  No action is required from
> new users; this is informational only.

---

## Using the OCR tab

The **OCR** tab (or `/process?action=ocr`) lets you extract raw text from a PDF.

1. Upload a PDF using the file picker.
2. Optionally adjust quality-check and spam-check thresholds.
3. Click **Send**.  The console calls `POST /doc-processing/ocr` and displays
   the extracted text, quality score, and detected languages.

---

## Using the Classify tab

The **Classify** tab (or `/process?action=classify`) sorts a document into one
of your predefined categories.

1. Upload a PDF.
2. Define your categories (label + description) in the **Form** tab, or switch
   to the **JSON** tab to paste a raw category list.
3. Optionally set a minimum confidence threshold.
4. Click **Run**.  The console transparently runs OCR first (using the cached
   result if the same PDF was already processed) and then calls
   `POST /doc-processing/classify`.  Results show the matched category and
   confidence score.

---

## Using the Data Extraction tab

The **Data Extraction** tab (or `/process?action=dataextraction`) pulls
structured field values out of a document.

### Step-by-step walkthrough

1. **Open the tab** — navigate to `/process?action=dataextraction` or click the
   **Data Extraction** tab in the console header.

2. **Upload a PDF** — use the file picker to select the document you want to
   process.

3. **Define schema fields** — use either input mode:

   - **Form tab** — click **Add field** and fill in:

     | Field | Required | Notes |
     |---|---|---|
     | `fieldId` | ✅ | Unique identifier returned in the response |
     | `description` | ✅ | Natural-language instruction for the LLM |
     | `dataType` | optional | e.g. `string`, `number`, `date` |
     | `extractionRules` | optional | Additional constraints or formatting rules |

   - **JSON tab** — paste a JSON array directly, for example:

     ```json
     [
       {
         "fieldId": "invoice_number",
         "description": "The invoice number printed at the top of the document",
         "dataType": "string"
       },
       {
         "fieldId": "total_amount",
         "description": "The total amount due including taxes",
         "dataType": "number"
       }
     ]
     ```

4. **Click Run** — the console:
   - Runs `POST /doc-processing/ocr` behind the scenes (or reuses a cached
     result for the same PDF) to obtain the document text.
   - Pipes that text into `POST /doc-processing/extract` together with your
     schema.

5. **Read the response** — the response contains one entry per schema field:

   ```json
   {
     "extracted": [
       {
         "fieldId": "invoice_number",
         "values": [
           {
             "value": "INV-2024-00123",
             "locations": [
               "Page 1: top-right header text - Page position ratio Height/Width [0.05, 0.72]"
             ]
           }
         ],
         "confidence": 0.97
       }
     ]
   }
   ```

   - `locations` — each string follows the pattern
     `Page N: <description> - Page position ratio Height/Width [v, h]` where
     `v` and `h` are fractional coordinates (0 = top/left, 1 = bottom/right).
   - `confidence` — a 0–1 score indicating how certain the model is.

---

## Companion pages

| Page | URL | Purpose |
|---|---|---|
| **SSO Token helper** | `/ssotoken` | Interactive Entra ID sign-in that displays the resulting JWT bearer token — useful for calling the API from `curl`, Postman, or Bruno without a full client setup. |
| **Access log browser** | `/admin` | Browse recent API request logs.  Requires the same SSO sign-in as `/process`. |
| **Swagger UI** | `/openapi.html` | Human-readable rendering of the OpenAPI specification for the HTTP API. |

**Canada `cac` demo links:**

```
https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/ssotoken
https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/admin
https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/openapi.html
```

---

## Troubleshooting

### "Sign-in failed" / popup closes without signing in

The most common cause is that your account has **not yet been added** to the
ACL group `app_prod_akka_proj_gwam_doc_proc-r`.

**Steps to resolve:**

1. Ask your team lead or a doc-processing-service maintainer to add your
   Manulife user account to the group `app_prod_akka_proj_gwam_doc_proc-r` on
   the **GFT-gaip-doc-proc-svc-PRD_SP** enterprise application.
2. Wait a few minutes for the group membership to propagate.
3. Close the browser tab, reopen `/process`, and try **Sign in** again.

### Verifying you can obtain a token

Use the `/ssotoken` helper page — it performs the same MSAL (Microsoft Authentication Library)
sign-in flow and displays the raw JWT if successful.  If the token page also fails, the issue
is almost certainly the ACL group membership.

### API calls return 401 after signing in

The console asks MSAL for a current access token before every request, so expired tokens
are renewed automatically. If a 401 persists, sign out and back in, then verify that the token
has the expected audience and `Users` role; otherwise ask a maintainer to check your ACL assignment.

