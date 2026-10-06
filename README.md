{
  "fieldId": "reason_code",
  "description": "Contract termination withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from the Contract Termination Withdrawal section containing the options ID – Taking payout due to Plan Termination, TE – Previously terminated from the company – assets left in Plan, and RE – Previously retired from the company – assets left in Plan. A right/check mark indicates that the option is selected. A cross mark indicates that the option is not selected. If exactly one option has a right/check mark, return the corresponding reason code: ID if only ID is selected, TE if only TE is selected, or RE if only RE is selected. If more than one option has a right/check mark, return 'TE'. If none of the three options has a right/check mark, return 'TE'. Return only one of these exact values: 'ID', 'TE', or 'RE'."
}
