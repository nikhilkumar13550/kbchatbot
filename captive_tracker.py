# =============================================================================
# IGP Automation — Captive Payment Email Tracker
# =============================================================================
# Mailbox : IGP OAR Payments/JHancock/Manulife
#
# What this script tracks:
#   1. INBOX           — Unread emails in the OAR Payments inbox (PENDING)
#   2. 2. Captives     — All subfolders inside the "2. Captives" folder.
#                        Each subfolder (e.g. "5048 BASF", "5177 Sanofi-Aventis
#                        Payment", …) is treated as a separate captive group.
#                        UNREAD emails in each subfolder are tracked on first run.
#                        On subsequent runs, NEW emails added since last run are
#                        picked up automatically.
#
# Output : Captive_Tracker.xlsx
#   Sheet 1 — "Pending (Inbox)"    : unread Inbox emails
#   Sheet 2 — "Captives Summary"   : ALL captive group emails in one view
#   Sheet 3+ — one sheet per captive group (e.g. "5048 BASF", "5177 Sanofi")
#              Sheet names are trimmed to 31 chars (Excel limit).
#
# Editable columns (team fills these in manually in Excel):
#   • Assigned Person's Name
#   • Read/Unread
#   • Action Taken
# =============================================================================

import os
import re
import json
import logging
import shutil
import tempfile
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

MAILBOX_NAME  = os.getenv("OAR_MAILBOX_NAME",       "IGP OAR Payments/JHancock/Manulife")
TRACKER_PATH  = os.getenv("CAPTIVE_TRACKER_PATH",   r"C:\IGP\Captive_Tracker.xlsx")
LOG_FOLDER    = os.getenv("CAPTIVE_LOG_FOLDER",     r"C:\IGP\Logs")
STATE_FILE    = os.getenv("CAPTIVE_STATE_FILE",     r"C:\IGP\captive_tracker_state.json")

# Parent folder that contains all the captive sub-groups
CAPTIVES_PARENT = "2. Captives"

# On first run, how many recent emails to pull from each captive subfolder
FIRST_RUN_LIMIT = 10

# -----------------------------------------------------------------------------
# COLUMN DEFINITIONS  (same structure as PYER tracker)
# -----------------------------------------------------------------------------
COLUMNS = [
    "Tracked At",               # col 1  — set by script
    "Received Date",            # col 2  — set by script
    "From (Name)",              # col 3  — set by script
    "From (Email)",             # col 4  — set by script
    "Subject",                  # col 5  — set by script
    "Captive Group",            # col 6  — which subfolder (e.g. "5048 BASF")
    "Folder Path",              # col 7  — full path for reference
    "Status",                   # col 8  — PENDING / CAPTIVE / etc.
    "Notes",                    # col 9  — set by script (blank)
    "Assigned Person's Name",   # col 10 — EDITABLE by team
    "Read/Unread",              # col 11 — EDITABLE by team
    "Action Taken",             # col 12 — EDITABLE by team
]

COLUMN_WIDTHS = [18, 18, 24, 34, 54, 26, 30, 14, 24, 26, 14, 28]

# Header colours
COLOR_INBOX    = "C00000"   # red        — Inbox / Pending
COLOR_CAPTIVE  = "1F3864"   # dark navy  — individual captive sheets
COLOR_SUMMARY  = "00422D"   # Manulife dark green — summary sheet

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
log_file = Path(LOG_FOLDER) / f"Captive_Tracker_Log_{datetime.now().strftime('%Y-%m-%d')}.txt"

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
# =============================================================================

def load_state() -> dict:
    """Load last-seen timestamps from state file. Empty dict = first run."""
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    log.info(f"State saved → {STATE_FILE}")


# =============================================================================
# OUTLOOK CONNECTION
# =============================================================================

def get_mailbox_root():
    """Connect to Outlook and return the root of the OAR Payments mailbox."""
    log.info("Connecting to Outlook…")
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
        f"Make sure it is visible in the sidebar."
    )


def find_folder_by_name(parent, name: str):
    """Case-insensitive direct child folder lookup."""
    try:
        for f in parent.Folders:
            if f.Name.lower() == name.lower():
                return f
    except Exception:
        pass
    return None


def get_inbox(root):
    """Return the Inbox folder of the mailbox."""
    return find_folder_by_name(root, "Inbox")


def get_captives_subfolders(root) -> list:
    """
    Find the '2. Captives' parent folder and return a list of
    (subfolder_name, com_folder) tuples — one entry per captive group.
    """
    captives_folder = find_folder_by_name(root, CAPTIVES_PARENT)
    if not captives_folder:
        log.warning(f"Could not find '{CAPTIVES_PARENT}' under {MAILBOX_NAME}")
        return []

    result = []
    try:
        for subfolder in captives_folder.Folders:
            result.append((subfolder.Name, subfolder))
    except Exception as e:
        log.error(f"Error listing captive subfolders: {e}")

    log.info(f"Found {len(result)} captive group(s) under '{CAPTIVES_PARENT}'")
    for name, _ in result:
        log.info(f"  → {name}")
    return result


# =============================================================================
# EMAIL EXTRACTION
# =============================================================================

def read_inbox_unread(inbox_folder) -> list:
    """Read all UNREAD emails from the Inbox every run."""
    results = []
    if not inbox_folder:
        log.warning("Inbox folder not found, skipping.")
        return results

    try:
        items = inbox_folder.Items
        items.Sort("[ReceivedTime]", True)
    except Exception as e:
        log.error(f"Cannot read Inbox: {e}")
        return results

    for email in items:
        try:
            if email.Class != 43:
                continue
            if not email.UnRead:
                continue

            received_dt = email.ReceivedTime
            received_naive = received_dt.replace(tzinfo=None) if received_dt else None
            received_str   = received_naive.strftime("%Y-%m-%d %H:%M") if received_naive else ""

            results.append({
                "tracked_at"      : datetime.now().strftime("%Y-%m-%d %H:%M"),
                "received_date"   : received_str,
                "sender_name"     : email.SenderName         or "",
                "sender_email"    : email.SenderEmailAddress or "",
                "subject"         : email.Subject            or "",
                "captive_group"   : "Inbox",
                "folder_path"     : f"{MAILBOX_NAME} / Inbox",
                "status"          : "PENDING",
                "notes"           : "",
                "assigned_person" : "",
                "read_unread"     : "",
                "action_taken"    : "",
                "_received_dt"    : received_naive,
            })
        except Exception as e:
            log.warning(f"Skipping Inbox email: {e}")

    log.info(f"Inbox: {len(results)} unread email(s)")
    return results


def read_captive_subfolder(subfolder_name: str, com_folder, last_seen_dt, is_first_run: bool) -> list:
    """
    Read emails from one captive group subfolder.

    First run  → last FIRST_RUN_LIMIT emails (most recent)
    Later runs → only emails newer than last_seen_dt
    """
    results = []

    try:
        items = com_folder.Items
        items.Sort("[ReceivedTime]", True)   # newest first
    except Exception as e:
        log.error(f"Cannot read '{subfolder_name}': {e}")
        return results

    count = 0
    for email in items:
        try:
            if email.Class != 43:
                continue

            received_dt    = email.ReceivedTime
            received_naive = received_dt.replace(tzinfo=None) if received_dt else None

            if is_first_run:
                if count >= FIRST_RUN_LIMIT:
                    break
            else:
                if last_seen_dt and received_naive and received_naive <= last_seen_dt:
                    break   # sorted newest-first; everything older can be skipped

            received_str = received_naive.strftime("%Y-%m-%d %H:%M") if received_naive else ""

            results.append({
                "tracked_at"      : datetime.now().strftime("%Y-%m-%d %H:%M"),
                "received_date"   : received_str,
                "sender_name"     : email.SenderName         or "",
                "sender_email"    : email.SenderEmailAddress or "",
                "subject"         : email.Subject            or "",
                "captive_group"   : subfolder_name,
                "folder_path"     : f"{MAILBOX_NAME} / {CAPTIVES_PARENT} / {subfolder_name}",
                "status"          : "CAPTIVE",
                "notes"           : "",
                "assigned_person" : "",
                "read_unread"     : "",
                "action_taken"    : "",
                "_received_dt"    : received_naive,
            })
            count += 1

        except Exception as e:
            log.warning(f"Skipping email in '{subfolder_name}': {e}")
            continue

    log.info(f"Captive group '{subfolder_name}': {len(results)} email(s) found")
    return results


# =============================================================================
# EXCEL — HELPERS
# =============================================================================

def _safe_sheet_name(name: str) -> str:
    """Excel sheet names: max 31 chars, no special chars."""
    for ch in r'\/*?:[]\x00':
        name = name.replace(ch, "-")
    return name[:31]


def _header_fill(color: str):
    return PatternFill("solid", fgColor=color)


def _thin_border():
    s = Side(style="thin", color="DDDDDD")
    return Border(left=s, right=s, bottom=s)


def create_sheet_header(ws, header_color: str):
    """Write and style the header row."""
    hfill  = _header_fill(header_color)
    hfont  = Font(color="FFFFFF", bold=True, size=10)
    halign = Alignment(horizontal="center", vertical="center", wrap_text=True)
    brd    = _thin_border()

    for col_idx, col_name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill      = hfill
        cell.font      = hfont
        cell.alignment = halign
        cell.border    = brd

    # Editable columns (10, 11, 12) — gold text on dark header
    for editable_col in [10, 11, 12]:
        cell = ws.cell(row=1, column=editable_col)
        cell.fill = PatternFill("solid", fgColor="4A4A4A")
        cell.font = Font(color="FFD700", bold=True, size=10)

    for i, w in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"


def append_rows_to_sheet(ws, emails: list, row_tint: str = ""):
    """Append email rows to a worksheet, alternating row colours."""
    thin = _thin_border()
    wrap = Alignment(vertical="top", wrap_text=False)

    base_fill  = PatternFill("solid", fgColor="FFFFFF")
    alt_fill   = PatternFill("solid", fgColor="F5F5F5")
    tint_fill  = PatternFill("solid", fgColor=row_tint) if row_tint else None
    edit_tint  = PatternFill("solid", fgColor="FFFDE7")  # light yellow for editable cols

    for email in emails:
        row_idx = ws.max_row + 1
        is_odd  = (row_idx % 2 == 0)
        row_fill = tint_fill if tint_fill else (alt_fill if is_odd else base_fill)

        values = [
            email["tracked_at"],
            email["received_date"],
            email["sender_name"],
            email["sender_email"],
            email["subject"],
            email["captive_group"],
            email["folder_path"],
            email["status"],
            email["notes"],
            email["assigned_person"],   # col 10 — editable
            email["read_unread"],       # col 11 — editable
            email["action_taken"],      # col 12 — editable
        ]

        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = wrap
            cell.border    = thin
            # Editable columns get yellow tint
            cell.fill = edit_tint if col_idx >= 10 else row_fill


def safe_save(wb, path: str):
    """
    Save workbook via temp file → rename, so a file open in Excel
    doesn't cause a PermissionError on the main file.
    """
    path      = str(path)
    dir_name  = os.path.dirname(path) or "."
    base_name = os.path.basename(path)

    try:
        fd, tmp_path = tempfile.mkstemp(
            prefix=f"~{base_name}_tmp_", suffix=".xlsx", dir=dir_name)
        os.close(fd)
        wb.save(tmp_path)
    except Exception as e:
        try: os.remove(tmp_path)
        except: pass
        raise RuntimeError(f"Could not write tracker: {e}") from e

    try:
        shutil.move(tmp_path, path)
    except PermissionError:
        try: os.remove(tmp_path)
        except: pass
        raise PermissionError(
            "\n\n  ╔══════════════════════════════════════════════════════════╗\n"
            "  ║  Captive_Tracker.xlsx is currently open in Excel.         ║\n"
            "  ║  Please close it and run the script again.                ║\n"
            "  ╚══════════════════════════════════════════════════════════╝\n"
        )


# =============================================================================
# EXCEL — TRACKER BUILD / UPDATE
# =============================================================================

SUMMARY_SHEET  = "Captives Summary"
INBOX_SHEET    = "Pending (Inbox)"


def _migrate_existing_tracker(path: str):
    """
    If the tracker already exists but is missing the 3 editable columns,
    add them to every sheet automatically.
    """
    wb = openpyxl.load_workbook(path)
    changed = False
    for ws in wb.worksheets:
        current_headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
        expected = COLUMNS
        for idx, col_name in enumerate(expected, start=1):
            if idx > len(current_headers) or current_headers[idx - 1] != col_name:
                # Insert missing column
                ws.insert_cols(idx)
                cell = ws.cell(1, idx, value=col_name)
                cell.fill = PatternFill("solid", fgColor="4A4A4A")
                cell.font = Font(color="FFD700", bold=True, size=10)
                cell.alignment = Alignment(horizontal="center", vertical="center")
                ws.column_dimensions[get_column_letter(idx)].width = COLUMN_WIDTHS[idx - 1]
                changed = True
    if changed:
        safe_save(wb, path)
        log.info("Migrated existing tracker — added missing editable columns.")


def ensure_tracker_exists(path: str):
    """Create the tracker workbook if it doesn't exist yet."""
    if Path(path).exists():
        _migrate_existing_tracker(path)
        return

    log.info(f"Creating new tracker: {path}")
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Create Inbox sheet
    ws_inbox = wb.create_sheet(INBOX_SHEET)
    create_sheet_header(ws_inbox, COLOR_INBOX)

    # Create Summary sheet
    ws_summary = wb.create_sheet(SUMMARY_SHEET)
    create_sheet_header(ws_summary, COLOR_SUMMARY)

    safe_save(wb, path)
    log.info("Tracker created with Inbox + Summary sheets.")


def get_or_create_sheet(wb, sheet_name: str, header_color: str):
    """Return an existing sheet or create a new one with header."""
    if sheet_name in wb.sheetnames:
        return wb[sheet_name]
    ws = wb.create_sheet(sheet_name)
    create_sheet_header(ws, header_color)
    return ws


def subject_already_in_sheet(ws, subject: str, sender_email: str) -> bool:
    """
    Check if this exact email (same subject + sender) is already in the sheet.
    Prevents duplicates when re-running within the same day.
    """
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[4] == subject and row[3] == sender_email:
            return True
    return False


# =============================================================================
# MAIN
# =============================================================================

def run():
    log.info("=" * 60)
    log.info("IGP Captive Payment Tracker — starting run")
    log.info("=" * 60)

    state        = load_state()
    is_first_run = len(state) == 0
    if is_first_run:
        log.info("FIRST RUN — will pull last 10 emails from each captive group")
    else:
        log.info("INCREMENTAL RUN — will pull only new emails since last run")

    # ── Connect to Outlook ───────────────────────────────────────────────────
    root = get_mailbox_root()

    # ── Gather emails ────────────────────────────────────────────────────────
    inbox_folder    = get_inbox(root)
    captive_groups  = get_captives_subfolders(root)

    inbox_emails    = read_inbox_unread(inbox_folder)

    all_captive_emails = []   # combined for summary sheet
    per_group_emails   = {}   # key = subfolder name

    new_state = {}

    for group_name, com_folder in captive_groups:
        state_key    = f"captive::{group_name}"
        last_seen_str = state.get(state_key)
        last_seen_dt  = None

        if last_seen_str:
            try:
                from dateutil import parser as dateutil_parser
                last_seen_dt = dateutil_parser.parse(last_seen_str)
            except Exception:
                last_seen_dt = None

        emails = read_captive_subfolder(
            group_name, com_folder, last_seen_dt, is_first_run
        )

        per_group_emails[group_name] = emails
        all_captive_emails.extend(emails)

        # Update state — store the most recent datetime for this group
        if emails:
            most_recent = max(
                e["_received_dt"] for e in emails if e["_received_dt"]
            )
            new_state[state_key] = most_recent.strftime("%Y-%m-%d %H:%M:%S")
        elif last_seen_str:
            # No new emails; keep the previous timestamp
            new_state[state_key] = last_seen_str

    # ── Open / create tracker ────────────────────────────────────────────────
    Path(TRACKER_PATH).parent.mkdir(parents=True, exist_ok=True)
    ensure_tracker_exists(TRACKER_PATH)

    wb = openpyxl.load_workbook(TRACKER_PATH)

    # ── Inbox sheet ──────────────────────────────────────────────────────────
    ws_inbox = get_or_create_sheet(wb, INBOX_SHEET, COLOR_INBOX)
    new_inbox = 0
    for email in inbox_emails:
        if not subject_already_in_sheet(ws_inbox, email["subject"], email["sender_email"]):
            append_rows_to_sheet(ws_inbox, [email])
            new_inbox += 1
    log.info(f"Inbox sheet: {new_inbox} new row(s) added")

    # ── Summary sheet ────────────────────────────────────────────────────────
    ws_summary = get_or_create_sheet(wb, SUMMARY_SHEET, COLOR_SUMMARY)
    new_summary = 0
    for email in all_captive_emails:
        if not subject_already_in_sheet(ws_summary, email["subject"], email["sender_email"]):
            append_rows_to_sheet(ws_summary, [email])
            new_summary += 1
    log.info(f"Summary sheet: {new_summary} new row(s) added")

    # ── Per-group sheets ─────────────────────────────────────────────────────
    total_captive_new = 0
    for group_name, emails in per_group_emails.items():
        sheet_name = _safe_sheet_name(group_name)
        ws_group   = get_or_create_sheet(wb, sheet_name, COLOR_CAPTIVE)
        new_rows   = 0
        for email in emails:
            if not subject_already_in_sheet(ws_group, email["subject"], email["sender_email"]):
                append_rows_to_sheet(ws_group, [email])
                new_rows += 1
        if new_rows:
            log.info(f"  Sheet '{sheet_name}': {new_rows} new row(s)")
        total_captive_new += new_rows

    log.info(f"Total captive emails added this run: {total_captive_new}")

    # ── Save ─────────────────────────────────────────────────────────────────
    safe_save(wb, TRACKER_PATH)
    log.info(f"Tracker saved → {TRACKER_PATH}")

    # ── Persist state ─────────────────────────────────────────────────────────
    if new_state:
        save_state(new_state)

    log.info("=" * 60)
    log.info(f"Done. Inbox: {new_inbox} | Captive groups: {total_captive_new} | "
             f"Summary: {new_summary}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
