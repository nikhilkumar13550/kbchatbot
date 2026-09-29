{
  "documentId": "doc-ocr-1",
  "schema": [
    {
      "fieldId": "last_name",
      "description": "Participant last name",
      "dataType": "string",
      "extractionRules": "Participant last name. If name has a comma, use text before the comma as last name. If no comma,Mandatory. use first word as last name. Return only last name."
      
    },
    {
      "fieldId": "first_name",
      "description": "Participant first name",
      "dataType": "string",
      "extractionRules": "Participant first name. If name has a comma, use text after the comma as first name. If no comma, Mandatory. use second word as first name. Return only first name."
    },
    {
      "fieldId": "contract_number",
      "description": "Participant Contract Number",
      "dataType": "string",                                    
      "extractionRules": "Extract the participant contract number from the form it can go from 4 to 6 digit number"
    },
    {
      "fieldId": "ssn",
      "description": "Participant ssn",
      "dataType": "string",
      "extractionRules": "Mandatory. Extract participant Social Security Number from participant header area. Priority labels: SSN, Social Security Number, Participant Social Security Number, Full SSN Required, form field SSN. Accept XXX-XX-XXXX or XXXXXXXXX. Return 9 digits only"
    }
  ],
  "ocrText": "{{ocr-text-output}}"
}
