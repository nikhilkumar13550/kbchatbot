# =============================================================================
# IGP Automation — Captive Receipt Tracker
# =============================================================================
# Mailbox : IGP OAR Payments/JHancock/Manulife
#
# Logic:
#   For every captive group subfolder (5048 BASF, 5156 Bayer, etc.) under
#   "2. Captives", scan for PAIRS of emails:
#
#   ORIGINAL  — subject starts with "Payment Received :"
#   REPLY     — subject starts with "RE:" or "FW:" followed by the same
#               "Payment Received : …" text
#
#   Only pairs (original + at least one admin reply) are written to the tracker.
#   Unpaired originals are SKIPPED (admin hasn't confirmed yet).
#
# Output : Captive_Receipt_Tracker.xlsx
#   Sheet 1 — "All Receipts"  : combined view of every matched pair
#   Sheet 2+ — one sheet per captive group
#
# 39-column AP template (fields 1-39) with auto-extracted values where
# possible; manual-fill columns left blank and highlighted in yellow.
#
# Incremental: state file tracks the newest email date per group so
# subsequent runs pick up only new pairs.
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

MAILBOX_NAME   = os.getenv("OAR_MAILBOX_NAME",              "IGP OAR Payments/JHancock/Manulife")
TRACKER_PATH   = os.getenv("CAPTIVE_RECEIPT_TRACKER_PATH",  r"C:\IGP\Captive_Receipt_Tracker.xlsx")
LOG_FOLDER     = os.getenv("CAPTIVE_LOG_FOLDER",            r"C:\IGP\Logs")
STATE_FILE     = os.getenv("CAPTIVE_RECEIPT_STATE_FILE",    r"C:\IGP\captive_receipt_state.json")

CAPTIVES_PARENT = "2. Captives"
FIRST_RUN_LIMIT = 50          # scan this many emails per group on first run

# Keywords that identify an original "Payment Received" email
PAYMENT_RECEIVED_KEYWORD = "payment received"

# Prefixes on admin reply subjects
REPLY_PREFIXES = ("re:", "fw:", "fwd:")

# Colours
COLOR_SUMMARY  = "00422D"   # Manulife dark green
COLOR_GROUP    = "1F3864"   # dark navy
COLOR_MANUAL   = "FFFDE7"   # light yellow  — manual-fill cells
COLOR_AUTO     = "FFFFFF"   # white          — auto-filled cells
COLOR_AUTO_ALT = "F5F5F5"   # light grey     — alternate row

# -----------------------------------------------------------------------------
# 39-COLUMN AP TEMPLATE
# Each entry: (column_header, auto_fill_key_or_None)
# auto_fill_key maps to a key in the extracted data dict; None = manual fill
# -----------------------------------------------------------------------------
COLUMNS = [
    # col  Header                          auto-fill key
    ( 1,  "Seq No.",                       "seq_no"),
    ( 2,  "Enter AP Process Level",        None),
    ( 3,  "Enter Cash Code",               None),
    ( 4,  "Cash Code Currency",            "currency"),
    ( 5,  "Bank Amount",                   "bank_amount"),
    ( 6,  "Bank Currency",                 "currency"),
    ( 7,  "AP Company",                    "ap_company"),
    ( 8,  "Transaction Date (YYYY/MM/DD)", "transaction_date"),
    ( 9,  "Description",                   "description"),
    (10,  "Approval Cost Center",          None),
    (11,  "Approval Category",             None),
    (12,  "Payee Name",                    "payee_name"),
    (13,  "Payee Country Code",            None),
    (14,  "Payee Address Line 1",          None),
    (15,  "Payee Address Line 2",          None),
    (16,  "Payee City",                    None),
    (17,  "Payee State/Province",          None),
    (18,  "Payee Postal Code",             None),
    (19,  "Bank Identification",           "bank_id"),
    (20,  "Bank Name",                     "bank_name"),
    (21,  "Bank Account Number",           None),
    (22,  "Bank Account Type",             None),
    (23,  "Cross Border/ SWIFT Number type", None),
    (24,  "Cross/ SWIFT Number",           "swift_number"),
    (25,  "Priority Code",                 None),
    (26,  "Cash Ledger Charge Code",       None),
    (27,  "Payee Bank Country Code",       None),
    (28,  "Payee Bank Address Line 1",     None),
    (29,  "Payee Bank Address Line 2",     None),
    (30,  "Payee Bank City",               None),
    (31,  "Payee Bank State/Province",     None),
    (32,  "Payee Bank Postal Code",        None),
    (33,  "Remittance Comment",            "remittance_comment"),
    (34,  "Distribution Amount",           None),
    (35,  "Distribution Accounting Unit",  None),
    (36,  "Distribution Account",          None),
    (37,  "CONTRACT",                      None),
    (38,  "MISC1",                         "misc1"),
    (39,  "CERT",                          None),
]

# Extra metadata columns appended AFTER the 39 AP columns (for reference)
META_COLUMNS = [
    "Captive Group",
    "Original Subject",
    "Admin Reply From",
    "Admin Reply Date",
    "Admin Reply Body",
    "Attachment(s)",
    "Tracked At",
]

ALL_HEADERS = [c[1] for c in COLUMNS] + META_COLUMNS

# Which column indices (1-based) are manual fill
MANUAL_COL_INDICES = {c[0] for c in COLUMNS if c[2] is None}

# Column widths — 39 AP cols + 7 meta
COLUMN_WIDTHS = [
     8,  18,  18,  14,  14,  14,  14,  22,  48,   # 1-9
    20,  20,  28,  16,  28,  28,  20,  20,  16,   # 10-18
    20,  34,  22,  18,  28,  22,  14,  22,  20,   # 19-27
    28,  28,  20,  20,  16,  48,  18,  26,  22,   # 28-36
    16,  22,  12,                                  # 37-39
    # meta
    24,  54,  28,  20,  54,  40,  18,
]

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
log_file = Path(LOG_FOLDER) / f"Captive_Receipt_Log_{datetime.now().strftime('%Y-%m-%d')}.txt"

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
# STATE
# =============================================================================

def load_state() -> dict:
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    log.info(f"State saved → {STATE_FILE}")


# =============================================================================
# OUTLOOK
# =============================================================================

def get_mailbox_root():
    log.info("Connecting to Outlook…")
    try:
        outlook   = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
    except Exception as e:
        log.error(f"Cannot connect to Outlook: {e}")
        raise

    for folder in namespace.Folders:
        if MAILBOX_NAME.lower() in folder.Name.lower():
            log.info(f"Found mailbox: {folder.Name}")
            return folder

    raise ValueError(f"Mailbox '{MAILBOX_NAME}' not found in Outlook sidebar.")


def find_child_folder(parent, name: str):
    try:
        for f in parent.Folders:
            if f.Name.lower() == name.lower():
                return f
    except Exception:
        pass
    return None


def get_captives_subfolders(root) -> list:
    captives = find_child_folder(root, CAPTIVES_PARENT)
    if not captives:
        log.warning(f"Could not find '{CAPTIVES_PARENT}'")
        return []
    result = []
    try:
        for sf in captives.Folders:
            result.append((sf.Name, sf))
    except Exception as e:
        log.error(f"Error listing captive subfolders: {e}")
    log.info(f"Found {len(result)} captive group(s)")
    for n, _ in result:
        log.info(f"  → {n}")
    return result


# =============================================================================
# SUBJECT HELPERS
# =============================================================================

def _strip_reply_prefix(subject: str) -> str:
    """Remove RE:/FW:/FWD: (and stacked ones) from the front of a subject."""
    s = subject.strip()
    while True:
        lower = s.lower()
        stripped = False
        for prefix in REPLY_PREFIXES:
            if lower.startswith(prefix):
                s = s[len(prefix):].strip()
                stripped = True
                break
        if not stripped:
            break
    return s


def _is_payment_received(subject: str) -> bool:
    """True if the bare subject (after stripping RE/FW) contains 'Payment Received'."""
    bare = _strip_reply_prefix(subject)
    return PAYMENT_RECEIVED_KEYWORD in bare.lower()


def _is_reply_to(reply_subject: str, original_subject: str) -> bool:
    """
    True if reply_subject is a RE:/FW: of original_subject.
    Both subjects are compared after stripping reply prefixes.
    """
    bare_reply    = _strip_reply_prefix(reply_subject).lower().strip()
    bare_original = _strip_reply_prefix(original_subject).lower().strip()
    return bare_reply == bare_original


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def _extract_from_subject(subject: str) -> dict:
    """
    Parse: "Payment Received : <Payee Name> <CURRENCY> <AMOUNT>"
    e.g.  "Payment Received : Unum Poland USD 45,524.51"
    """
    bare = _strip_reply_prefix(subject).strip()

    # Remove "Payment Received :" prefix (case-insensitive)
    remainder = re.sub(r"(?i)^payment\s+received\s*:\s*", "", bare).strip()

    # Extract currency (3-letter code) and amount (digits + commas + dot)
    # Pattern: <payee name> <CURRENCY> <amount>
    m = re.search(
        r"^(.*?)\s+([A-Z]{3})\s+([\d,]+(?:\.\d+)?)\s*$",
        remainder
    )
    if m:
        payee_name  = m.group(1).strip()
        currency    = m.group(2).upper()
        bank_amount = m.group(3).replace(",", "")   # numeric string, no commas
    else:
        # Fallback: everything before the last token pair
        payee_name  = remainder
        currency    = ""
        bank_amount = ""

    return {
        "payee_name" : payee_name,
        "currency"   : currency,
        "bank_amount": bank_amount,
    }


def _extract_from_body(body: str) -> dict:
    """
    Extract AP Company, Transaction Date, wire description, bank name,
    bank ID (SWIFT/BIC), and DETAILS line from the email body table.

    The table in the original email looks like (spaces/newlines vary):
        US004  7/6/2026  45,524.51  DESCRIPTION ... TYPE:FX IN DATE:070626 ...
                                    BK:BANK HANDLOWY W WARSZAWIE S. ID:CITIPLPXINS
                                    DETAILS:RECKITT 5741-49 Q3 Q4 ...
    """
    result = {
        "ap_company"      : "",
        "transaction_date": "",
        "description"     : "",
        "bank_id"         : "",
        "bank_name"       : "",
        "swift_number"    : "",
        "remittance_comment": "",
    }

    # ── AP Company: US followed by digits (e.g. US0045, US004 5) ─────────────
    ap_match = re.search(r"\b(US\s*\d{3,6})\b", body)
    if ap_match:
        result["ap_company"] = ap_match.group(1).replace(" ", "")

    # ── Transaction Date: M/D/YYYY or MM/DD/YYYY ─────────────────────────────
    date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", body)
    if date_match:
        try:
            dt = datetime.strptime(date_match.group(1), "%m/%d/%Y")
            result["transaction_date"] = dt.strftime("%Y/%m/%d")
        except ValueError:
            result["transaction_date"] = date_match.group(1)

    # ── Wire description: everything from DESCRIPTION to end of that block ───
    desc_match = re.search(
        r"(DESCRIPTION\s+INDIVIDUAL.*?)(?=\n\n|\Z)", body,
        re.DOTALL | re.IGNORECASE
    )
    if desc_match:
        result["description"] = " ".join(desc_match.group(1).split())

    # ── Bank Identification (SWIFT BIC after ID:) ────────────────────────────
    id_match = re.search(r"\bID:([A-Z0-9]{8,11})\b", body)
    if id_match:
        result["bank_id"]      = id_match.group(1)
        result["swift_number"] = id_match.group(1)

    # ── Bank Name (after BK:) ─────────────────────────────────────────────────
    bk_match = re.search(r"\bBK:([^\.]+(?:\.[^\.]+)?)\.", body)
    if bk_match:
        result["bank_name"] = bk_match.group(1).strip()

    # ── DETAILS / Remittance Comment ──────────────────────────────────────────
    det_match = re.search(r"DETAILS:(.+?)(?=\n\n|\Z)", body, re.DOTALL)
    if det_match:
        result["remittance_comment"] = " ".join(det_match.group(1).split())

    return result


def _extract_reply_info(reply_email) -> dict:
    """Extract admin name, date, body summary, and attachment list from reply."""
    info = {
        "admin_name"  : "",
        "admin_date"  : "",
        "reply_body"  : "",
        "attachments" : "",
    }
    try:
        info["admin_name"] = reply_email.SenderName or ""
        rd = reply_email.ReceivedTime
        if rd:
            naive = rd.replace(tzinfo=None)
            info["admin_date"] = naive.strftime("%Y-%m-%d %H:%M")

        # Body — take only the first meaningful paragraph (before the quoted original)
        body = reply_email.Body or ""
        # Split on common quoted-email separators
        for separator in ["-----Original Message-----", "From: IGP OAR", "________________________________"]:
            if separator in body:
                body = body[:body.index(separator)]
        info["reply_body"] = " ".join(body.strip().split())[:500]

        # Attachments
        att_names = []
        try:
            for att in reply_email.Attachments:
                att_names.append(att.FileName)
        except Exception:
            pass
        info["attachments"] = "; ".join(att_names)

    except Exception as e:
        log.warning(f"Error extracting reply info: {e}")

    return info


# =============================================================================
# PAIR MATCHING — the core logic
# =============================================================================

def collect_pairs_from_folder(group_name: str, com_folder, last_seen_dt, is_first_run: bool) -> list:
    """
    Scan the folder for Payment Received pairs:
    1. Collect all "Payment Received" originals
    2. Find matching RE:/FW: replies
    3. Return only matched pairs as a list of dicts

    Returns list of extracted row dicts, each representing one matched pair.
    """
    pairs = []

    try:
        items = com_folder.Items
        items.Sort("[ReceivedTime]", True)   # newest first
    except Exception as e:
        log.error(f"Cannot read '{group_name}': {e}")
        return pairs

    # ── Load all relevant emails into memory ──────────────────────────────────
    originals = {}   # key = bare_subject_lower → list of email dicts
    replies   = {}   # key = bare_subject_lower → list of email dicts

    count = 0
    for email in items:
        try:
            if email.Class != 43:
                continue

            received_dt    = email.ReceivedTime
            received_naive = received_dt.replace(tzinfo=None) if received_dt else None

            # Incremental cutoff
            if not is_first_run and last_seen_dt and received_naive:
                if received_naive <= last_seen_dt:
                    break

            subject = email.Subject or ""
            bare    = _strip_reply_prefix(subject).lower().strip()

            if not _is_payment_received(subject):
                continue   # not a "Payment Received" thread at all

            is_reply = any(
                subject.strip().lower().startswith(p) for p in REPLY_PREFIXES
            )

            record = {
                "subject"       : subject,
                "bare_subject"  : bare,
                "received_naive": received_naive,
                "com_email"     : email,   # keep COM object for data extraction
            }

            if is_reply:
                replies.setdefault(bare, []).append(record)
            else:
                originals.setdefault(bare, []).append(record)

            count += 1
            if is_first_run and count >= FIRST_RUN_LIMIT:
                break

        except Exception as e:
            log.warning(f"Error reading email in '{group_name}': {e}")
            continue

    log.info(f"'{group_name}': {len(originals)} original(s), {len(replies)} reply thread(s) found")

    # ── Match originals to replies ────────────────────────────────────────────
    matched = 0
    skipped_no_reply = 0

    for bare_subj, orig_list in originals.items():
        if bare_subj not in replies:
            skipped_no_reply += len(orig_list)
            log.debug(f"  No reply found for: '{bare_subj}' — skipping")
            continue

        reply_list = replies[bare_subj]

        for orig in orig_list:
            # Pick the most recent reply for this original
            best_reply = sorted(
                reply_list,
                key=lambda r: r["received_naive"] or datetime.min,
                reverse=True
            )[0]

            try:
                orig_email  = orig["com_email"]
                reply_email = best_reply["com_email"]

                # Extract from original
                subj_data   = _extract_from_subject(orig["subject"])
                body_data   = _extract_from_body(orig_email.Body or "")
                reply_info  = _extract_reply_info(reply_email)

                # MISC1 = admin reply body summary (what the payment relates to)
                misc1 = reply_info["reply_body"]

                row = {
                    "seq_no"            : "",       # filled during write (auto-increment)
                    "currency"          : subj_data["currency"],
                    "bank_amount"       : subj_data["bank_amount"],
                    "ap_company"        : body_data["ap_company"],
                    "transaction_date"  : body_data["transaction_date"],
                    "description"       : body_data["description"],
                    "payee_name"        : subj_data["payee_name"],
                    "bank_id"           : body_data["bank_id"],
                    "bank_name"         : body_data["bank_name"],
                    "swift_number"      : body_data["swift_number"],
                    "remittance_comment": body_data["remittance_comment"],
                    "misc1"             : misc1,
                    # meta
                    "captive_group"     : group_name,
                    "original_subject"  : orig["subject"],
                    "admin_reply_from"  : reply_info["admin_name"],
                    "admin_reply_date"  : reply_info["admin_date"],
                    "admin_reply_body"  : reply_info["reply_body"],
                    "attachments"       : reply_info["attachments"],
                    "tracked_at"        : datetime.now().strftime("%Y-%m-%d %H:%M"),
                    # for state tracking
                    "_received_dt"      : orig["received_naive"],
                }
                pairs.append(row)
                matched += 1

            except Exception as e:
                log.warning(f"Error building pair for '{bare_subj}': {e}")
                continue

    log.info(f"'{group_name}': {matched} matched pair(s), {skipped_no_reply} skipped (no admin reply yet)")
    return pairs


# =============================================================================
# EXCEL
# =============================================================================

def _safe_sheet_name(name: str) -> str:
    for ch in r'\/*?:[]\x00':
        name = name.replace(ch, "-")
    return name[:31]


def create_sheet_header(ws, header_color: str):
    hfill  = PatternFill("solid", fgColor=header_color)
    hfont  = Font(color="FFFFFF", bold=True, size=9)
    halign = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin   = Side(style="thin", color="DDDDDD")
    brd    = Border(left=thin, right=thin, bottom=thin)

    for col_idx, header in enumerate(ALL_HEADERS, start=1):
        cell            = ws.cell(row=1, column=col_idx, value=header)
        cell.fill       = hfill
        cell.font       = hfont
        cell.alignment  = halign
        cell.border     = brd

    # Manual-fill AP columns → gold text header
    for col_num in MANUAL_COL_INDICES:
        cell      = ws.cell(row=1, column=col_num)
        cell.fill = PatternFill("solid", fgColor="4A4A4A")
        cell.font = Font(color="FFD700", bold=True, size=9)

    for i, w in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.row_dimensions[1].height = 36
    ws.freeze_panes = "A2"


def _build_row_values(row: dict, seq: int) -> list:
    """Build the ordered list of values matching ALL_HEADERS."""
    row["seq_no"] = seq
    auto_fill_map = {c[2]: c[0] for c in COLUMNS if c[2]}   # key → col_number

    values = []
    for _, header, key in COLUMNS:
        if key:
            values.append(row.get(key, ""))
        else:
            values.append("")   # manual fill — blank

    # Meta columns
    values.append(row.get("captive_group",    ""))
    values.append(row.get("original_subject", ""))
    values.append(row.get("admin_reply_from", ""))
    values.append(row.get("admin_reply_date", ""))
    values.append(row.get("admin_reply_body", ""))
    values.append(row.get("attachments",      ""))
    values.append(row.get("tracked_at",       ""))
    return values


def append_row_to_sheet(ws, row: dict, seq: int):
    """Append one matched-pair row to a worksheet."""
    thin     = Side(style="thin", color="DDDDDD")
    brd      = Border(left=thin, right=thin, bottom=thin)
    wrap     = Alignment(vertical="top", wrap_text=False)
    auto_fill= PatternFill("solid", fgColor=COLOR_AUTO)
    alt_fill = PatternFill("solid", fgColor=COLOR_AUTO_ALT)
    manual_f = PatternFill("solid", fgColor=COLOR_MANUAL)

    values   = _build_row_values(row, seq)
    row_idx  = ws.max_row + 1
    is_alt   = (row_idx % 2 == 0)
    base     = alt_fill if is_alt else auto_fill

    num_ap_cols = len(COLUMNS)

    for col_idx, val in enumerate(values, start=1):
        cell            = ws.cell(row=row_idx, column=col_idx, value=val)
        cell.border     = brd
        cell.alignment  = wrap
        if col_idx <= num_ap_cols and col_idx in MANUAL_COL_INDICES:
            cell.fill = manual_f
        else:
            cell.fill = base


def safe_save(wb, path: str):
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
            "\n\n  ╔═══════════════════════════════════════════════════════════════╗\n"
            "  ║  Captive_Receipt_Tracker.xlsx is currently open in Excel.      ║\n"
            "  ║  Please close it and run the script again.                     ║\n"
            "  ╚═══════════════════════════════════════════════════════════════╝\n"
        )


def subject_key(row: dict) -> str:
    """Dedup key — same original subject = same payment."""
    return row.get("original_subject", "").lower().strip()


def already_in_sheet(ws, row: dict) -> bool:
    """Check if this pair is already tracked (by original subject in col 41 = 'Original Subject')."""
    orig_subj = subject_key(row)
    # Original Subject is at index 40 (0-based) = column 41
    orig_col = len(COLUMNS) + 2   # col 1 = Seq, +39 AP cols, +1 Captive Group, +1 Original Subject
    for r in ws.iter_rows(min_row=2, min_col=orig_col, max_col=orig_col, values_only=True):
        if r[0] and r[0].lower().strip() == orig_subj:
            return True
    return False


def get_or_create_sheet(wb, name: str, color: str):
    if name in wb.sheetnames:
        return wb[name]
    ws = wb.create_sheet(name)
    create_sheet_header(ws, color)
    return ws


def ensure_tracker_exists(path: str):
    if Path(path).exists():
        return
    log.info(f"Creating new tracker: {path}")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("All Receipts")
    create_sheet_header(ws, COLOR_SUMMARY)
    safe_save(wb, path)
    log.info("Tracker created.")


# =============================================================================
# MAIN
# =============================================================================

def run():
    log.info("=" * 70)
    log.info("IGP Captive Receipt Tracker — starting run")
    log.info("=" * 70)

    state        = load_state()
    is_first_run = len(state) == 0
    log.info("FIRST RUN" if is_first_run else "INCREMENTAL RUN")

    root            = get_mailbox_root()
    captive_groups  = get_captives_subfolders(root)

    if not captive_groups:
        log.error("No captive groups found — aborting.")
        return

    all_pairs  = []   # combined for "All Receipts" sheet
    group_data = {}   # group_name → list of pair dicts
    new_state  = {}

    for group_name, com_folder in captive_groups:
        state_key     = f"receipt::{group_name}"
        last_seen_str = state.get(state_key)
        last_seen_dt  = None

        if last_seen_str:
            try:
                from dateutil import parser as dp
                last_seen_dt = dp.parse(last_seen_str)
            except Exception:
                last_seen_dt = None

        pairs = collect_pairs_from_folder(
            group_name, com_folder, last_seen_dt, is_first_run
        )

        group_data[group_name] = pairs
        all_pairs.extend(pairs)

        # Update state
        valid_dts = [p["_received_dt"] for p in pairs if p.get("_received_dt")]
        if valid_dts:
            most_recent = max(valid_dts)
            new_state[state_key] = most_recent.strftime("%Y-%m-%d %H:%M:%S")
        elif last_seen_str:
            new_state[state_key] = last_seen_str

    # ── Open / create tracker ─────────────────────────────────────────────────
    Path(TRACKER_PATH).parent.mkdir(parents=True, exist_ok=True)
    ensure_tracker_exists(TRACKER_PATH)
    wb = openpyxl.load_workbook(TRACKER_PATH)

    # ── All Receipts (summary) sheet ──────────────────────────────────────────
    ws_all  = get_or_create_sheet(wb, "All Receipts", COLOR_SUMMARY)
    seq_all = ws_all.max_row   # continues from last run's sequence

    new_all = 0
    for pair in all_pairs:
        if not already_in_sheet(ws_all, pair):
            seq_all += 1
            append_row_to_sheet(ws_all, pair, seq_all)
            new_all += 1

    log.info(f"All Receipts sheet: {new_all} new row(s)")

    # ── Per-group sheets ──────────────────────────────────────────────────────
    total_new = 0
    for group_name, pairs in group_data.items():
        if not pairs:
            continue
        sheet_name = _safe_sheet_name(group_name)
        ws_grp     = get_or_create_sheet(wb, sheet_name, COLOR_GROUP)
        seq_grp    = ws_grp.max_row

        new_grp = 0
        for pair in pairs:
            if not already_in_sheet(ws_grp, pair):
                seq_grp += 1
                append_row_to_sheet(ws_grp, pair, seq_grp)
                new_grp += 1

        if new_grp:
            log.info(f"  Sheet '{sheet_name}': {new_grp} new row(s)")
        total_new += new_grp

    # ── Save ──────────────────────────────────────────────────────────────────
    safe_save(wb, TRACKER_PATH)
    log.info(f"Tracker saved → {TRACKER_PATH}")

    if new_state:
        save_state(new_state)

    log.info("=" * 70)
    log.info(f"Done. All Receipts: {new_all} new | Per-group total: {total_new}")
    log.info("=" * 70)


if __name__ == "__main__":
    run()
