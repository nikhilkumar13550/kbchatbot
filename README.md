{
  "fieldId": "reason_code",
  "description": "Withdrawal reason code",
  "dataType": "string",
  "extractionRules": "Mandatory. Extract the withdrawal reason code from Section 2, 'Withdrawal Reason and Year of Excess – Select one withdrawal reason'. Evaluate the selection status of EC, ED, and EA. EC represents Excess Contribution Withdrawal, ED represents Excess Deferral Withdrawal, and EA represents Excess Annual Addition Withdrawal. Count the selected options and unselected options. If the number of selected options is greater than 1, return 'EC'. If the number of unselected options is greater than 2, return 'EC'. Otherwise, if EC is selected, return 'EC'. If ED is selected, return 'ED'. If EA is selected, return 'EA'. Return only one value: 'EC', 'ED', or 'EA'."
}
