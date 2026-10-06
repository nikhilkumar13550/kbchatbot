{
  "fieldId": "reason_code",
  "description": "Withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from Section 2, 'Withdrawal Reason and Year of Excess – Select one withdrawal reason'. Evaluate the selection status of EC (Excess Contribution Withdrawal), ED (Excess Deferral Withdrawal), and EA (Excess Annual Addition Withdrawal). If exactly one option is selected, return the corresponding reason code: if EC is selected, return 'EC'; if ED is selected, return 'ED'; if EA is selected, return 'EA'. If more than one option is selected, return 'EC'. If none of the three options is selected, return 'EC'. Return only one of these exact values: 'EC', 'ED', or 'EA'."
}
