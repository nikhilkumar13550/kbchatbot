# =============================================================================
# IGP Automation — PYER Email Tracker
# =============================================================================
# Mailbox : IGP Administration - PYERs/JHancock/Manulife
#
# What this script tracks:
#   1. INBOX          — Unread emails not yet moved (PENDING action)
#   2. PYERs received in 2026  — Emails moved here by the team (RECEIVED)
#   3. Correspondence — Emails moved here by the team (CORRESPONDENCE)
#   4. Deleted PYERs  — Emails moved here by the team (DELETED)
#
# First run  : picks up last 10 emails from each folder
# Every run after : picks up only NEW emails added since last run
# Output     : OAR_PYER_Tracker.xlsx with 4 separate sheets, one per folder
# =============================================================================

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

import win32com.client
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
load_dotenv()

MAILBOX_NAME = os.getenv("PYER_MAILBOX_NAME", "IGP Administration - PYERs/JHancock/Manulife")
TRACKER_PATH = os.getenv("PYER_TRACKER_PATH", r"C:\IGP\PYER_Tracker.xlsx")
LOG_FOLDER   = os.getenv("PYER_LOG_FOLDER",   r"C:\IGP\Logs")

# State file — stores the last-processed email date per folder
# so subsequent runs only pick up NEW emails
STATE_FILE   = os.getenv("PYER_STATE_FILE",   r"C:\IGP\pyer_tracker_state.json")

# On first run, how many emails to pull from each folder (most recent first)
FIRST_RUN_LIMIT = 10

# Folders to monitor inside the mailbox
FOLDER_CONFIG = {
    "Inbox": {
        "sheet"      : "Pending (Inbox)",
        "status"     : "PENDING",
        "header_color": "C00000",   # red
        "description": "Unread emails in Inbox — not yet moved by team"
    },
    "PYERs received in 2026": {
        "sheet"      : "PYERs Received 2026",
        "status"     : "RECEIVED",
        "header_color": "375623",   # dark green
        "description": "Emails moved to PYERs received in 2026"
    },
    "Correspondence": {
        "sheet"      : "Correspondence",
        "status"     : "CORRESPONDENCE",
        "header_color": "1F3864",   # dark navy
        "description": "Emails moved to Correspondence"
    },
    "Deleted PYERs": {
        "sheet"      : "Deleted PYERs",
        "status"     : "DELETED",
        "header_color": "595959",   # dark grey
        "description": "Emails moved to Deleted PYERs"
    },
}

# Columns in each sheet
COLUMNS = [
    "Tracked At",
    "Received Date",
    "From (Name)",
    "From (Email)",
    "Subject",
    "NP / Client Name",
    "PYER Reference",
    "Folder",
    "Status",
    "Notes",
]

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
log_file = Path(LOG_FOLDER) / f"PYER_Tracker_Log_{datetime.now().strftime('%Y-%m-%d')}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# =============================================================================
# STATE MANAGEMENT
# Tracks the most recent email date seen per folder so that
# subsequent runs only pick up emails NEWER than the last run.
# =============================================================================

def load_state() -> dict:
    """Load the last-seen timestamps from the state file."""
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}   # empty = first run


def save_state(state: dict):
    """Save the latest timestamps to the state file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    log.info(f"State saved to: {STATE_FILE}")


# =============================================================================
# OUTLOOK CONNECTION
# =============================================================================

def get_mailbox_root():
    """Connect to Outlook and return the root of the PYER shared mailbox."""
    log.info("Connecting to Outlook...")
    try:
        outlook   = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
    except Exception as e:
        log.error(f"Cannot connect to Outlook. Is Outlook open? Error: {e}")
        raise

    for folder in namespace.Folders:
        if MAILBOX_NAME.lower() in folder.Name.lower():
            log.info(f"Found mailbox: {folder.Name}")
            return folder

    raise ValueError(
        f"Mailbox '{MAILBOX_NAME}' not found in Outlook. "
        f"Ensure it is visible in the Outlook sidebar."
    )


def get_folder(root, folder_name: str):
    """
    Return a subfolder by name from the mailbox root.
    Searches recursively through all nested subfolders.

    Folder structure in this mailbox:
      Inbox
        └── PYERs received in 2026
              ├── Correspondence      ← nested inside PYERs received in 2026
              └── Deleted PYERs      ← nested inside PYERs received in 2026
    """
    try:
        if folder_name.lower() == "inbox":
            return root.Folders["Inbox"]
        else:
            # Recursively search all folders and subfolders
            return _find_folder_recursive(root, folder_name)
    except Exception as e:
        log.warning(f"Could not find folder '{folder_name}': {e}")
    return None


def _find_folder_recursive(parent, target_name: str):
    """
    Walk all subfolders recursively and return the first one
    whose name matches target_name (case-insensitive).
    Returns None if not found.
    """
    try:
        for folder in parent.Folders:
            if folder.Name.lower() == target_name.lower():
                return folder
            # Recurse into this folder's subfolders
            found = _find_folder_recursive(folder, target_name)
            if found:
                return found
    except Exception:
        pass
    return None


# =============================================================================
# EMAIL EXTRACTION
# =============================================================================

def extract_pyer_info(subject: str, body: str) -> dict:
    """
    Try to extract NP/client name and PYER reference number
    from the email subject and body.
    These are best-effort — will be blank if not found.
    """
    # PYER reference — looks like PYER-2026-001 or IGP/PYER/2026/001
    ref_match = re.search(
        r"(PYER[\-/]\d{4}[\-/]\d+|IGP[\-/]PYER[\-/]\d{4}[\-/]\d+)",
        subject + " " + body[:500], re.IGNORECASE
    )
    pyer_ref = ref_match.group(1).upper() if ref_match else ""

    # NP / client name — often in square brackets or after "from" in subject
    np_match = re.search(r"\[([A-Z][A-Za-z\s&]+)\]", subject)
    np_name  = np_match.group(1).strip() if np_match else ""

    return {
        "pyer_ref": pyer_ref,
        "np_name" : np_name,
    }


def read_emails_from_folder(folder, folder_name: str, last_seen_dt, is_first_run: bool) -> list:
    """
    Read emails from an Outlook folder and return a list of dicts.

    Inbox     : reads only UNREAD emails (pending action)
    Other folders: reads emails newer than last_seen_dt,
                   or last FIRST_RUN_LIMIT emails on first run
    """
    results = []

    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)   # newest first
    except Exception as e:
        log.error(f"Cannot read items from '{folder_name}': {e}")
        return results

    count = 0

    for email in items:
        try:
            # Only process mail items (not meeting requests etc.)
            if email.Class != 43:   # 43 = olMail
                continue

            received_dt = email.ReceivedTime

            # ── INBOX: only unread emails ────────────────────────────────────
            if folder_name.lower() == "inbox":
                if not email.UnRead:
                    continue

            # ── OTHER FOLDERS: first run = last N; subsequent = only new ─────
            else:
                if is_first_run:
                    if count >= FIRST_RUN_LIMIT:
                        break
                else:
                    if last_seen_dt and received_dt <= last_seen_dt:
                        break   # emails are sorted newest first, so we can stop

            subject      = email.Subject             or ""
            body         = email.Body                or ""
            sender_name  = email.SenderName          or ""
            sender_email = email.SenderEmailAddress  or ""
            received_str = received_dt.strftime("%Y-%m-%d %H:%M") if received_dt else ""

            pyer_info = extract_pyer_info(subject, body)

            results.append({
                "tracked_at"   : datetime.now().strftime("%Y-%m-%d %H:%M"),
                "received_date": received_str,
                "sender_name"  : sender_name,
                "sender_email" : sender_email,
                "subject"      : subject,
                "np_name"      : pyer_info["np_name"],
                "pyer_ref"     : pyer_info["pyer_ref"],
                "folder"       : folder_name,
                "status"       : FOLDER_CONFIG[folder_name]["status"],
                "notes"        : "",
                "_received_dt" : received_dt,   # used for state update, not written to sheet
            })

            count += 1

        except Exception as e:
            log.warning(f"Skipping one email in '{folder_name}': {e}")
            continue

    log.info(f"Folder '{folder_name}': {len(results)} email(s) found")
    return results


# =============================================================================
# EXCEL TRACKER
# =============================================================================

def create_sheet_header(ws, header_color: str):
    """Write and style the header row for one sheet."""
    header_fill  = PatternFill("solid", fgColor=header_color)
    header_font  = Font(color="FFFFFF", bold=True, size=10)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin         = Side(style="thin", color="DDDDDD")
    border       = Border(left=thin, right=thin, bottom=thin)

    for col_idx, col_name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill      = header_fill
        cell.font      = header_font
        cell.alignment = header_align
        cell.border    = border

    # Column widths
    widths = [18, 18, 22, 32, 50, 22, 18, 22, 16, 24]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"


def ensure_tracker_exists(path: str):
    """Create the tracker Excel file with 4 sheets if it does not exist."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists():
        return

    log.info(f"Creating new tracker: {path}")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)   # remove default blank sheet

    for folder_name, cfg in FOLDER_CONFIG.items():
        ws = wb.create_sheet(title=cfg["sheet"])
        create_sheet_header(ws, cfg["header_color"])
        # Add description in cell A2 as a guide (light italic)
        ws["A2"].value     = f"← {cfg['description']}"
        ws["A2"].font      = Font(italic=True, color="888888", size=9)
        ws["A2"].alignment = Alignment(vertical="center")

    wb.save(path)
    log.info("Tracker created successfully.")


def append_rows_to_sheet(path: str, sheet_name: str, rows: list, header_color: str):
    """Append extracted email rows to the correct sheet in the tracker."""
    if not rows:
        return

    wb = openpyxl.load_workbook(path)

    if sheet_name not in wb.sheetnames:
        ws = wb.create_sheet(title=sheet_name)
        create_sheet_header(ws, header_color)
    else:
        ws = wb[sheet_name]

    # Find next empty row (skip header + any description row)
    next_row = ws.max_row + 1
    if next_row == 2 and ws["A2"].value and ws["A2"].value.startswith("←"):
        next_row = 3   # skip the description hint row on first data write

    # Status colour map
    status_colors = {
        "PENDING"       : "FCE4D6",   # light orange
        "RECEIVED"      : "E2EFDA",   # light green
        "CORRESPONDENCE": "DEEAF1",   # light blue
        "DELETED"       : "EDEDED",   # light grey
    }

    for row_data in rows:
        # Alternating row shading
        row_fill = (
            PatternFill("solid", fgColor="F9F9F9")
            if next_row % 2 == 0
            else PatternFill("solid", fgColor="FFFFFF")
        )

        values = [
            row_data["tracked_at"],
            row_data["received_date"],
            row_data["sender_name"],
            row_data["sender_email"],
            row_data["subject"],
            row_data["np_name"],
            row_data["pyer_ref"],
            row_data["folder"],
            row_data["status"],
            row_data["notes"],
        ]

        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=next_row, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="center", wrap_text=(col_idx == 5))
            cell.fill      = row_fill

            # Highlight Status column
            if col_idx == 9:
                status_color = status_colors.get(str(value), "FFFFFF")
                cell.fill = PatternFill("solid", fgColor=status_color)
                cell.font = Font(bold=True, size=9)

        ws.row_dimensions[next_row].height = 18
        next_row += 1

    wb.save(path)
    log.info(f"Sheet '{sheet_name}': {len(rows)} row(s) written.")


# =============================================================================
# MAIN
# =============================================================================

def run():
    log.info("=" * 70)
    log.info("IGP PYER Tracker — Script started")
    log.info(f"Mailbox : {MAILBOX_NAME}")
    log.info(f"Tracker : {TRACKER_PATH}")
    log.info("=" * 70)

    # ── Load state (know what was last seen per folder) ───────────────────────
    state        = load_state()
    is_first_run = len(state) == 0
    log.info(f"Run type: {'FIRST RUN' if is_first_run else 'INCREMENTAL UPDATE'}")

    # ── Create tracker if missing ─────────────────────────────────────────────
    ensure_tracker_exists(TRACKER_PATH)

    # ── Connect to mailbox ────────────────────────────────────────────────────
    mailbox_root = get_mailbox_root()

    new_state = {}
    total_processed = 0

    # ── Process each folder ───────────────────────────────────────────────────
    for folder_name, cfg in FOLDER_CONFIG.items():
        log.info(f"--- Processing folder: {folder_name} ---")

        folder = get_folder(mailbox_root, folder_name)
        if folder is None:
            log.warning(f"Folder '{folder_name}' not found — skipping.")
            continue

        # Get last seen datetime for this folder
        last_seen_str = state.get(folder_name)
        last_seen_dt  = None
        if last_seen_str:
            try:
                from dateutil import parser as dtparser
                last_seen_dt = dtparser.parse(last_seen_str)
            except Exception:
                last_seen_dt = None

        # Read emails
        emails = read_emails_from_folder(
            folder, folder_name, last_seen_dt, is_first_run
        )

        if emails:
            # Write to tracker
            append_rows_to_sheet(
                TRACKER_PATH,
                cfg["sheet"],
                emails,
                cfg["header_color"]
            )

            # Update state with the most recent email seen in this folder
            most_recent_dt = max(e["_received_dt"] for e in emails)
            new_state[folder_name] = most_recent_dt.strftime("%Y-%m-%d %H:%M:%S")
            total_processed += len(emails)
        else:
            # Keep previous state for this folder
            if folder_name in state:
                new_state[folder_name] = state[folder_name]

    # ── Save updated state ────────────────────────────────────────────────────
    if new_state:
        save_state(new_state)

    # ── Summary ───────────────────────────────────────────────────────────────
    log.info("-" * 70)
    log.info(f"Done. Total emails tracked this run: {total_processed}")
    log.info(f"Tracker saved at : {TRACKER_PATH}")
    log.info(f"Log saved at     : {log_file}")
    log.info("=" * 70)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run()
