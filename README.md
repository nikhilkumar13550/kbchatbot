To confirm that it is IP whitelising issue can you please help me test this spn connection via eother channer , I have documentation for that. Skip to content  manulife-innersource  doc-processing-service Repository navigation Code  Issues28 (28)  Pull requests2 (2) From Akka serviceIf your service uses Akka, you can use the doc-processing-service-client directly. See doc-processing-service-client for usage instructions.HTTP clienthttps://{deploymentURL}/doc-processing/{endpoint-path}HTTP:POST /doc-processing/ocrPOST /doc-processing/classifyPOST /doc-processing/extractGET /health — unauthenticated liveness check returning { "status": "UP" }The specifications of the HTTP API are exported with OpenAPI: openapi.yaml for full specification of the endpoints.https://{deploymentURL}/openapi.html for a human-friendly (SwaggerUI) rendering of the OpenAPI specs. For Canada cac region: https://proud-dawn-5395.az-manulife-canada-crt-cac.agents.akka.manulife.io/openapi.html For API calls to /doc-processing/* (and /mcp), a JWT must be present in the HTTP Authorization header: Authorization: Bearer <your_jwt_token_here>GET /health does not require authentication and is intended for load balancers, liveness probes, and uptime monitoring.Service-to-Service JWT Token AuthenticationYour service needs to obtain a JWT and include it as a Bearer token in the Authorization header of HTTP and MCP API calls.# Constant Manulife Tenant
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
  | jq -r '.access_token'The resulting token must have these properties:aud: fd755477-f7ed-470c-9980-0fa0928e7300iss: https://login.microsoftonline.com/5d3e2773-e07f-4432-a630-1a0f68a28a05/v2.0roles: ["Users"]Granting access to your serviceBefore your service can obtain a valid token with the Users role, your Azure SPN must be authorized on the doc-processing-service app registration. This is a one-time setup:Add API permission on your SPN's App Registration: In the Azure portal, open your SPN's App Registration page → API permissions → Add a permission. Under the APIs my organization uses tab, search for GFT-gaip-doc-proc-svc-PRD_SP and select the Users permission. The status will appear as Not granted for Manulife.Submit a SNOW request to get the permission approved: Create a Single-Sign On Services (Global) SNOW request:
Once processed, your SPN is added to the Users and groups list on the GFT-gaip-doc-proc-svc-PRD_SP Enterprise Application, and the permission status changes to Granted for Manulife.Select Modify Azure AD service principalWrite: "Please grant GFT-gaip-doc-proc-svc-PRD_SP for manulife to {YOUR_CLIENT_SPN}. Please see attached screenshot."Attach a screenshot of the API permissions page (from step 1), highlighting the Not granted for Manulife status.Verify: Tokens issued to your SPN will now contain "roles": ["Users"].I HAVE THE USERS PERMISSION Agents  Actions  Projects  Wiki  Security and quality  Insights  Settings AnnouncementPosted to manulife-innersource on May 19, 2026A gentle reminder: As per earlier discussion and agreement in our stand-up calls, any repo found in Innersource by EOD Nov 30, 2026 will be archived between Dec 1st and 5th. Reason: We need to start collecting proof that Innersource is empty, upload them in Archer and close CAP-40277 on Dec 15th with Risk Team's approval.FilestT.devcontainer.github.mvndevops doc-processing-service-api doc-processing-service-client src  README.md  pom.xml doc-processing-servicedocs.env.example.gitguardian.yml.gitignore.snykCODEOWNERS README.md adaloom.jsoncpom.xmldoc-processing-service/doc-processing-service-client/ Make PDF Field Optional For Classify and Extract Endpoints ( #143) a8b6013 · last weekdoc-processing-service/doc-processing-service-client/NameLast commit messageLast commit date .. src Make PDF Field Optional For Classify and Extract Endpoints ( #143 ) last weekREADME.md Make PDF Field Optional For Classify and Extract Endpoints ( #143)last weekpom.xml Fix snyk sca scans ( #158)2 weeks agoREADME.mddoc-processing-service-clientHTTP client implementation of the DocProcessingApi (defined in the doc-processing-service-api module).Built on global-ai-libraries:rest-http-connector library. Acquires and automatically renews a JWT from Azure Entra.PrerequisitesBefore using this client, your Azure SPN must be granted the Users role on the doc-processing-service app registration. See Granting access to your service in the root README for the one-time setup steps.UsageFirst, add the Client as dependency:<dependency>
  <groupId>com.manulife.global.ai</groupId>
  <artifactId>doc-processing-service-client</artifactId>
  <version>0.1.2-SNAPSHOT</version>
</dependency>Then set-up the client in your Akka application.import akka.javasdk.http.HttpClientProvider;
import com.manulife.ai.gwam.docprocessing.client.DocProcessingHttpClient;
import com.manulife.ai.gwam.docprocessing.client.auth.AzureEntraJwtProvider;
import com.manulife.ai.gwam.docprocessing.client.auth.AzureEntraJwtProviderConfig;
import com.manulife.ai.gwam.docprocessing.client.auth.JwtTokenProvider;
import com.manulife.global.ai.connector.http.rest.RestHttpConnector;
import java.io.InputStream;
import java.util.function.Supplier;


// First, create a RestHttpConnector pointed to the doc-processing-service instance
// See https://github.com/manulife-innersource/global-ai-platform-libraries/tree/build/rest-http-connector#quick-start for the different ways to configure a RestHttpConnector
// In that example, we assume a Multi-Service configuration of the RestHttpConnector
/*
# application.conf
rest.http {
  doc-processing {
    base-url = "https://{doc-processing-host}"
  }
}
*/
Config config = ConfigFactory.load(); // Config from Akka Bootstrap
RestHttpConnector connector =
    RestHttpConnector.createForService(config, httpClientProvider, "doc-processing");
// Second, you need an Azure Entra ID JWT token provider, which is used to acquire and renew the JWT used in the HTTP calls.
/*
# application.conf
azure.auth {
  tenant-id = ${AZURE_TENANT_ID}
  client-id = ${AZURE_CLIENT_ID}
  client-secret = ${AZURE_CLIENT_SECRET}
}
doc-processing-client {
  entra-id = ${DOC_PROC_ENTRA_ID}
}
*/
JwtTokenProvider tokenProvider = new AzureEntraJwtProvider(
    new AzureEntraJwtProviderConfig(
        config.getString("azure.auth.tenant-id"),
        config.getString("azure.auth.client-id"),
        config.getString("azure.auth.client-secret"),
        config.getString("doc-processing-client.entra-id")
    )
);

// Creation
DocProcessingHttpClient client = new DocProcessingHttpClient(connector, tokenProvider);

// Usage, example with a PDF from local file, but input can be anything that supplies an InputStream.
Supplier<InputStream> pdfFile = () -> Files.newInputStream(Path.of("/path/to/document.pdf"));
OcrResponse response = client.performOcr(request, pdfFile);

// classify / extract accept an optional PDF. Pass a supplier for multimodal
// (image-aware) processing, or pass null to run in text-only mode — the client
// will omit the pdfFile multipart part entirely.

// Multimodal: pass a PDF supplier
ClassifyResponse classified = client.classify(classifyRequest, pdfFile);

// Text-only: pass null — no pdfFile part is sent
ClassifyResponse textOnly = client.classify(classifyRequest, null);

// Same pattern for extract:
ExtractResponse extracted     = client.extract(extractRequest, pdfFile);
ExtractResponse extractedText = client.extract(extractRequest, null);In text-only mode the service still returns a well-formed response — for extract, every value's locations array comes back empty, since locations are derived from the rendered page images rather than from the OCR text.Token lifecycleAzureEntraJwtProvider fetches a JWT lazily on the first API call, caches it in memory, decodes the exp claim, and renews the token automatically once it has expired (a small safety skew is applied so the token is refreshed slightly before its real expiry). 
