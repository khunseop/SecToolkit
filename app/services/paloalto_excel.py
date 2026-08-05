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

# rule_name을 비워두면 바로 위 행과 같은 정책으로 취급되어, 이 행의 source/destination/service 등
# 다중값 필드 값이 콤마로 이어붙여진다 (정책 하나를 여러 행에 걸쳐 입력하는 원본 포맷 지원용 예시)
EXAMPLE_CONTINUATION_ROW = {
    "source": "10.0.1.0/24",
}

_TRUE_VALUES = {"true", "yes", "y", "1"}

# 여러 행에 걸쳐 입력된 값을 콤마로 이어붙일 수 있는 다중값 필드
LIST_FIELDS = ["from_zone", "source", "source_user", "to_zone", "destination", "service", "application"]

# 엑셀에 컬럼 자체가 없거나 셀이 비어 있을 때 저장된 기본값으로 채울 필드 (그리드의 "기본값"과 동일)
DEFAULT_FILLABLE_FIELDS = [
    "vsys", "disabled", "rule_action", "from_zone", "source", "source_user",
    "to_zone", "destination", "service", "application", "description",
    "log_end", "log_setting",
]

_excel_lock = threading.Lock()


def build_template_bytes() -> bytes:
    headers = [header for header, _ in COLUMN_FIELD_MAP]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "policies"
    ws.append(headers)
    ws.append([EXAMPLE_ROW.get(header, "") for header in headers])
    ws.append([EXAMPLE_CONTINUATION_ROW.get(header, "") for header in headers])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def rows_from_sheet_values(values: list) -> list:
    """Pure conversion of a 2D sheet value grid (header row + data rows) into
    dicts keyed by PolicyRuleRequest field names. No xlwings/openpyxl dependency,
    so this is unit-testable without Excel.

    rule_name이 빈 행은 바로 위의 정책이 이어지는 행("continuation row")으로 취급해서,
    그 행에 값이 있는 다중값 필드(source/destination/service 등)만 콤마로 이어붙이고
    별도 행으로 만들지 않는다. 정책 하나를 여러 행에 걸쳐 입력하는 원본 엑셀 포맷을
    그대로 업로드할 수 있게 하기 위함이다."""
    if not values or len(values) < 2:
        return []

    header_row = [str(cell).strip() if cell is not None else "" for cell in values[0]]
    header_to_field = dict(COLUMN_FIELD_MAP)
    field_by_col = [header_to_field.get(header) for header in header_row]

    rows = []
    current = None
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
            elif field_name == "rule_action":
                # PAN-OS는 소문자만 허용하므로 "Allow"/"Deny"처럼 대문자로 입력해도 정규화한다
                row_dict[field_name] = "" if cell_value is None else str(cell_value).strip().lower()
            else:
                row_dict[field_name] = "" if cell_value is None else str(cell_value).strip()

        if not row_dict.get("rule_name", "").strip() and current is not None:
            for field in LIST_FIELDS:
                value = row_dict.get(field, "")
                if not isinstance(value, str) or not value.strip():
                    continue
                existing = current.get(field, "")
                current[field] = f"{existing},{value.strip()}" if existing else value.strip()
            continue

        current = row_dict
        rows.append(current)

    return rows


def apply_defaults(rows: list, defaults: dict) -> list:
    """엑셀에 컬럼이 아예 없거나 셀이 비어 있는 필드를 저장된 기본값(그리드의 "1행 값을
    기본값으로 저장"과 동일한 값)으로 채운다. 값이 이미 채워진 필드(연속 행 병합 결과 포함)는
    건드리지 않는다. 작업유형(action)이 비어 있으면 "set"으로 취급한다."""
    filled_rows = []
    for row in rows:
        filled = dict(row)
        if not str(filled.get("action") or "").strip():
            filled["action"] = "set"
        for field in DEFAULT_FILLABLE_FIELDS:
            value = filled.get(field)
            is_blank = value is None or (isinstance(value, str) and not value.strip())
            if is_blank and field in defaults:
                filled[field] = defaults[field]
        filled_rows.append(filled)
    return filled_rows


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
