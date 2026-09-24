{
INPUTS: {
String to Deserialize: "{"status":"succeeded","createdDateTime":"2026-09-24T09:51:51Z","lastUpdatedDateTime":"2026-09-24T09:51:54Z","analyzeResult":{"apiVersion":"2024-11-30","modelId":"IA-Classification-v11","stringIndexType":"utf16CodeUnit","content":"","pages":[{"pageNumber":1,"angle":0,"width":8.5,"height":11,"unit":"inch","words":[],"lines":[],"spans":[]},{"pageNumber":2,"angle":0,"width":8.5,"height":11,"unit":"inch","words":[],"lines":[],"spans":[]}],"documents":[{"docType":"1111","boundingRegions":[{"pageNumber":1,"polygon":[0,0,8.5,0,8.5,11,0,11]}],"confidence":0.008,"spans":[]},{"docType":"1111","boundingRegions":[{"pageNumber":2,"polygon":[0,0,8.5,0,8.5,11,0,11]}],"confidence":0.083,"spans":[]}],"contentFormat":"text"}}"
},
OUTPUTS: [
{
path: "Done",
data: {
Output: {
analyzeResult: {
apiVersion: "2024-11-30",
contentFormat: "text",
documents: [
{
docType: "1111",
spans: [],
confidence: 0.008,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 1
}
]
},
{
docType: "1111",
spans: [],
confidence: 0.083,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 2
}
]
}
],
pages: [
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 1
},
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 2
}
],
content: "",
stringIndexType: "utf16CodeUnit",
modelId: "IA-Classification-v11"
},
lastUpdatedDateTime: "2026-09-24T09:51:54Z",
status: "succeeded",
createdDateTime: "2026-09-24T09:51:51Z"
}
}
}
]
}






{
INPUTS: {
ExtractionResultDeserialized: {
analyzeResult: {
apiVersion: "2024-11-30",
contentFormat: "text",
documents: [
{
docType: "1111",
spans: [],
confidence: 0.008,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 1
}
]
},
{
docType: "1111",
spans: [],
confidence: 0.083,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 2
}
]
}
],
pages: [
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 1
},
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 2
}
],
content: "",
stringIndexType: "utf16CodeUnit",
modelId: "IA-Classification-v11"
},
lastUpdatedDateTime: "2026-09-24T09:51:54Z",
status: "succeeded",
createdDateTime: "2026-09-24T09:51:51Z"
},
Error1: "Document is not of specified type",
JobLogList: [
{
ExtractionStatus: null,
ExtractedFields: null,
InstanceID: "2026-09-24-04.49.59.746840T01",
FirstNameConfidence: null,
DocumentName: null,
ExceptionDetails: null,
DocumentType: "pdf",
WorkflowName: "IndexingAgentFlow_v02",
UpdatedAt: "2026-09-24T05:51:49.7859706-04:00",
Status: "Started",
SSNConfidence: null,
ProcessingTime: null,
ObjectID: "2026-09-24-04.50.33.276840O01",
CreatedAt: "2026-09-24T05:51:49.785901-04:00",
ContractNumberConfidence: null,
ClassificationType: null,
ClassificationConfidence: null,
AvgExtractionConfidence: null,
LogType: "SYSTEM",
LogPoint: "Document Classification",
LastNameConfidence: null,
JobID: "id_BgdE1h3XswhOUr/n+/Hy5aS9JVwYpY61hUvDh3Ei3CQ=",
PageCount: null,
LogID: "27868736-19f2-4c71-89e6-b8803fb420b1"
},
{
ExtractionStatus: "Running",
ExtractedFields: null,
InstanceID: "2026-09-24-04.49.59.746840T01",
FirstNameConfidence: null,
DocumentName: null,
ExceptionDetails: null,
DocumentType: null,
WorkflowName: "Get Extraction Result and deserialize",
UpdatedAt: "2026-09-24T05:52:01.2903327-04:00",
Status: "Retry 1",
SSNConfidence: null,
ProcessingTime: null,
ObjectID: null,
CreatedAt: "2026-09-24T05:52:01.2899954-04:00",
ContractNumberConfidence: null,
ClassificationType: null,
ClassificationConfidence: null,
AvgExtractionConfidence: null,
LogType: "Service",
LogPoint: "Azure Doc Intel Classification Result API",
LastNameConfidence: null,
JobID: "id_BgdE1h3XswhOUr/n+/Hy5aS9JVwYpY61hUvDh3Ei3CQ=",
PageCount: null,
LogID: "9557e29a-b063-4bac-8049-13e0b6815fcc"
}
]
},
OUTPUTS: [
{
path: "Exception",
data: {
ExtractionResultDeserialized: {
analyzeResult: {
apiVersion: "2024-11-30",
contentFormat: "text",
documents: [
{
docType: "1111",
spans: [],
confidence: 0.008,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 1
}
]
},
{
docType: "1111",
spans: [],
confidence: 0.083,
boundingRegions: [
{
polygon: [
0,
0,
8.5,
0,
8.5,
11,
0,
11
],
pageNumber: 2
}
]
}
],
pages: [
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 1
},
{
spans: [],
lines: [],
words: [],
unit: "inch",
height: 11,
width: 8.5,
angle: 0,
pageNumber: 2
}
],
content: "",
stringIndexType: "utf16CodeUnit",
modelId: "IA-Classification-v11"
},
lastUpdatedDateTime: "2026-09-24T09:51:54Z",
status: "succeeded",
createdDateTime: "2026-09-24T09:51:51Z"
},
Error1: "Document is not of specified type",
JobLogList: [
{
ExtractionStatus: null,
ExtractedFields: null,
InstanceID: "2026-09-24-04.49.59.746840T01",
FirstNameConfidence: null,
DocumentName: null,
ExceptionDetails: null,
DocumentType: "pdf",
WorkflowName: "IndexingAgentFlow_v02",
UpdatedAt: "2026-09-24T05:51:49.7859706-04:00",
Status: "Started",
SSNConfidence: null,
ProcessingTime: null,
ObjectID: "2026-09-24-04.50.33.276840O01",
CreatedAt: "2026-09-24T05:51:49.785901-04:00",
ContractNumberConfidence: null,
ClassificationType: null,
ClassificationConfidence: null,
AvgExtractionConfidence: null,
LogType: "SYSTEM",
LogPoint: "Document Classification",
LastNameConfidence: null,
JobID: "id_BgdE1h3XswhOUr/n+/Hy5aS9JVwYpY61hUvDh3Ei3CQ=",
PageCount: null,
LogID: "27868736-19f2-4c71-89e6-b8803fb420b1"
},
{
ExtractionStatus: "Running",
ExtractedFields: null,
InstanceID: "2026-09-24-04.49.59.746840T01",
FirstNameConfidence: null,
DocumentName: null,
ExceptionDetails: null,
DocumentType: null,
WorkflowName: "Get Extraction Result and deserialize",
UpdatedAt: "2026-09-24T05:52:01.2903327-04:00",
Status: "Retry 1",
SSNConfidence: null,
ProcessingTime: null,
ObjectID: null,
CreatedAt: "2026-09-24T05:52:01.2899954-04:00",
ContractNumberConfidence: null,
ClassificationType: null,
ClassificationConfidence: null,
AvgExtractionConfidence: null,
LogType: "Service",
LogPoint: "Azure Doc Intel Classification Result API",
LastNameConfidence: null,
JobID: "id_BgdE1h3XswhOUr/n+/Hy5aS9JVwYpY61hUvDh3Ei3CQ=",
PageCount: null,
LogID: "9557e29a-b063-4bac-8049-13e0b6815fcc"
}
]
}
}
]
}
