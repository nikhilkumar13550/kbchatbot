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
},
{
  "fieldId": "reason_code",
  "description": "Loan request reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the loan request reason code from Section 4, 'Type of Loan Request – Select ONE only'. If option A – New Loan Request is selected, return 'Loan Issue'. If option B – Refinance Existing Loan is selected, return 'Loan Consolidation'. If the selection mark is unclear but an amount is populated under B – Refinance Existing Loan (BloanAmount), return 'Loan Consolidation'. Return only one of these exact values: 'Loan Issue' or 'Loan Consolidation'. Do not return the option letter A or B."
}






{
  "fieldId": "reason_code",
  "description": "Withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from Section 2, 'Withdrawal Reason and Year of Excess – Select one withdrawal reason'. Evaluate the selection status of EC, ED, and EA. EC represents Excess Contribution Withdrawal, ED represents Excess Deferral Withdrawal, and EA represents Excess Annual Addition Withdrawal. Count the selected options and unselected options. If the number of selected options is greater than 1, return 'EC'. If the number of unselected options is greater than 2, return 'EC'. Otherwise, if EC is selected, return 'EC'. If ED is selected, return 'ED'. If EA is selected, return 'EA'. Return only one value: 'EC', 'ED', or 'EA'."
}
