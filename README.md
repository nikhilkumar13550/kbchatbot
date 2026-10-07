{
  "fieldId": "reason_code",
  "description": "Withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from the withdrawal reason section containing the options TE – Termination date, RE – Retirement date, IR – Employee Money Transferred into Plan, DI – Disability, VC – Employee Voluntary Money, and PD – Early/Pre-Retirement. A right/check mark indicates that the option is selected. A cross mark indicates that the option is not selected. If exactly one option has a right/check mark, return the corresponding reason code: TE if only TE is selected, RE if only RE is selected, VC if only VC is selected, IR if only IR is selected, PD if only PD is selected, or DI if only DI is selected. If more than one option has a right/check mark, return 'TE'. If none of the six options has a right/check mark, return 'TE'. Return only one of these exact values: 'TE', 'RE', 'VC', 'IR', 'PD', or 'DI'."
}




{
  "fieldId": "reason_code",
  "description": "Forfeiture reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the reason code from Section 2, 'What is the Reason for the Forfeiture of Unvested Money?', containing the options TE – Termination date, RE – Retirement date, and DI – Disability. A right/check mark indicates that the option is selected. An empty option indicates that the option is not selected. A cross mark indicates that the option is not selected. If exactly one option has a right/check mark, return the corresponding reason code: TE if only TE is selected, RE if only RE is selected, or DI if only DI is selected. If more than one option has a right/check mark, return 'TE'. If none of the three options has a right/check mark, return 'TE'. Return only one of these exact values: 'TE', 'RE', or 'DI'."
}
