(venv) PS C:\IGP> python pyer_tracker.py
2026-10-29 12:28:24  INFO      ======================================================================
2026-10-29 12:28:24  INFO      IGP PYER Tracker — Script started
2026-10-29 12:28:24  INFO      Mailbox : IGP Administration - PYERs/JHancock/Manulife
2026-10-29 12:28:24  INFO      Tracker : C:\IGP\PYER_Tracker.xlsx
2026-10-29 12:28:24  INFO      ======================================================================
2026-10-29 12:28:24  INFO      Run type: INCREMENTAL UPDATE
2026-10-29 12:28:24  INFO      Connecting to Outlook...
2026-10-29 12:28:25  INFO      Found mailbox: IGP Administration - PYERs/JHancock/Manulife
2026-10-29 12:28:25  INFO      --- Processing folder: Inbox ---
2026-10-29 12:28:32  INFO      Folder 'Inbox': 3 email(s) found
Traceback (most recent call last):
  File "C:\IGP\pyer_tracker.py", line 494, in <module>
    run()
    ~~~^^
  File "C:\IGP\pyer_tracker.py", line 461, in run
    append_rows_to_sheet(
    ~~~~~~~~~~~~~~~~~~~~^
        TRACKER_PATH,
        ^^^^^^^^^^^^^
    ...<2 lines>...
        cfg["header_color"]
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\IGP\pyer_tracker.py", line 406, in append_rows_to_sheet
    wb.save(path)
    ~~~~~~~^^^^^^
  File "C:\IGP\venv\Lib\site-packages\openpyxl\workbook\workbook.py", line 386, in save
    save_workbook(self, filename)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\IGP\venv\Lib\site-packages\openpyxl\writer\excel.py", line 291, in save_workbook
    archive = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
  File "C:\Users\kumnikh\AppData\Local\Python\pythoncore-3.15-64\Lib\zipfile\__init__.py", line 1487, in __init__
    self.fp = io.open(file, filemode)
              ~~~~~~~^^^^^^^^^^^^^^^^
PermissionError: [Errno 13] Permission denied: 'C:\\IGP\\PYER_Tracker.xlsx'
