{
  "fieldId": "reason_code",
  "description": "Withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from Section 2, 'Withdrawal Reason and Year of Excess – Select one withdrawal reason'. Evaluate the selection marks for EC (Excess Contribution Withdrawal), ED (Excess Deferral Withdrawal), and EA (Excess Annual Addition Withdrawal). A right/check mark indicates that the option is selected. A cross mark indicates that the option is not selected. If exactly one option has a right/check mark, return the corresponding reason code: EC for Excess Contribution Withdrawal, ED for Excess Deferral Withdrawal, or EA for Excess Annual Addition Withdrawal. If more than one option has a right/check mark, return 'EC'. If none of the three options has a right/check mark, return 'EC'. Return only one of these exact values: 'EC', 'ED', or 'EA'."
}
