import io
import os
import tempfile
import threading

import openpyxl

# Column header -> PolicyRuleRequest field name (order also defines template column order)
COLUMN_FIELD_MAP = [
    ("작업유형", "action"),
    ("vsys", "vsys"),
    ("rule_name", "rule_name"),
    ("disabled", "disabled"),
    ("action", "rule_action"),
    ("from", "from_zone"),
    ("source", "source"),
    ("source-user", "source_user"),
    ("to", "to_zone"),
    ("destination", "destination"),
    ("service", "service"),
    ("application", "application"),
    ("description", "description"),
    ("log-end", "log_end"),
    ("log-setting", "log_setting"),
    ("move_position", "move_position"),
    ("anchor_rule", "anchor_rule"),
]

EXAMPLE_ROW = {
    "작업유형": "set",
    "vsys": "vsys1",
    "rule_name": "ALLOW-WEB",
    "disabled": "FALSE",
    "action": "allow",
    "from": "trust",
    "source": "10.0.0.0/24",
    "source-user": "any",
    "to": "untrust",
    "destination": "any",
    "service": "application-default",
    "application": "ssl,web-browsing",
    "description": "example rule",
    "log-end": "yes",
    "log-setting": "default",
    "move_position": "",
    "anchor_rule": "",
}

_TRUE_VALUES = {"true", "yes", "y", "1"}

_excel_lock = threading.Lock()


def build_template_bytes() -> bytes:
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "policies"
    ws.append(headers)
    ws.append([EXAMPLE_ROW.get(header, "") for header in headers])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def rows_from_sheet_values(values: list) -> list:
    """Pure conversion of a 2D sheet value grid (header row + data rows) into
    dicts keyed by PolicyRuleRequest field names. No xlwings/openpyxl dependency,
    so this is unit-testable without Excel."""
    if not values or len(values) < 2:
        return []

    header_row = [str(cell).strip() if cell is not None else "" for cell in values[0]]
    header_to_field = dict(COLUMN_FIELD_MAP)
    field_by_col = [header_to_field.get(header) for header in header_row]

    rows = []
    for raw_row in values[1:]:
        if raw_row is None or all(cell is None or str(cell).strip() == "" for cell in raw_row):
            continue

        row_dict = {}
        for col_index, field_name in enumerate(field_by_col):
            if field_name is None or col_index >= len(raw_row):
                continue
            cell_value = raw_row[col_index]
            if field_name == "disabled":
                row_dict[field_name] = str(cell_value).strip().lower() in _TRUE_VALUES if cell_value is not None else False
            else:
                row_dict[field_name] = "" if cell_value is None else str(cell_value).strip()
        rows.append(row_dict)

    return rows


def parse_uploaded_excel(file_bytes: bytes) -> list:
    """Opens the uploaded (DRM-protected) xlsx via a real Excel instance using
    xlwings, since the corporate DRM only allows decryption through Excel itself."""
    import xlwings as xw

    fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_bytes)

        with _excel_lock:
            app = xw.App(visible=False, add_book=False)
            try:
                book = app.books.open(temp_path)
                try:
                    sheet = book.sheets[0]
                    values = sheet.used_range.value
                finally:
                    book.close()
            finally:
                app.quit()

        return rows_from_sheet_values(values)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
