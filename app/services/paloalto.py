import json
import os

class PaloAltoService:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    DEFAULTS_FILE = os.path.join(DATA_DIR, "paloalto_defaults.json")

    DEFAULT_VALUES = {
        "vsys": "",
        "disabled": False,
        "rule_action": "allow",
        "from_zone": "",
        "source": "",
        "source_user": "",
        "to_zone": "",
        "destination": "",
        "service": "",
        "application": "",
        "description": "",
        "log_end": "",
        "log_setting": "",
    }

    @staticmethod
    def _ensure_data_dir():
        if not os.path.exists(PaloAltoService.DATA_DIR):
            os.makedirs(PaloAltoService.DATA_DIR)
        if not os.path.exists(PaloAltoService.DEFAULTS_FILE):
            with open(PaloAltoService.DEFAULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(PaloAltoService.DEFAULT_VALUES, f)

    @staticmethod
    def get_defaults() -> dict:
        PaloAltoService._ensure_data_dir()
        try:
            with open(PaloAltoService.DEFAULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(PaloAltoService.DEFAULT_VALUES)

    @staticmethod
    def save_defaults(defaults: dict) -> bool:
        PaloAltoService._ensure_data_dir()
        try:
            with open(PaloAltoService.DEFAULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    @staticmethod
    def _quote_if_needed(value: str) -> str:
        if " " in value:
            return f'"{value}"'
        return value

    @staticmethod
    def _format_list_value(raw: str) -> str:
        items = [item.strip() for item in raw.replace(",", "\n").split("\n") if item.strip()]
        if not items:
            return ""
        quoted = [PaloAltoService._quote_if_needed(item) for item in items]
        if len(quoted) == 1:
            return quoted[0]
        return "[ " + " ".join(quoted) + " ]"

    @staticmethod
    def _rule_base(vsys: str) -> str:
        if vsys:
            return f'set vsys {vsys} rulebase security rules'
        return "set rulebase security rules"

    @staticmethod
    def _delete_move_base(vsys: str) -> str:
        if vsys:
            return f'vsys {vsys} rulebase security rules'
        return "rulebase security rules"

    LIST_FIELDS = [
        ("from_zone", "from"),
        ("source", "source"),
        ("source_user", "source-user"),
        ("to_zone", "to"),
        ("destination", "destination"),
        ("service", "service"),
        ("application", "application"),
    ]

    @staticmethod
    def generate_command(request) -> dict:
        action = request.action

        if not request.rule_name.strip():
            return {"error": "Rule name is required."}

        if action == "delete":
            base = f'delete {PaloAltoService._delete_move_base(request.vsys)} "{request.rule_name.strip()}"'

            set_fields = [
                (field_name, keyword)
                for field_name, keyword in PaloAltoService.LIST_FIELDS
                if (getattr(request, field_name) or "").strip()
            ]

            if not set_fields:
                return {"command": base}

            if len(set_fields) > 1:
                return {"error": "삭제 시 한 번에 하나의 필드만 지정할 수 있습니다."}

            field_name, keyword = set_fields[0]
            raw_value = getattr(request, field_name)
            items = [v.strip() for v in raw_value.replace(",", "\n").split("\n") if v.strip()]
            if len(items) != 1:
                return {"error": "삭제 시 값은 하나만 입력하세요."}

            return {"command": f'{base} {keyword} "{items[0]}"'}

        if action == "move":
            if request.move_position not in ("top", "bottom", "before", "after"):
                return {"error": "Move position must be one of top, bottom, before, after."}
            base = f'move {PaloAltoService._delete_move_base(request.vsys)} "{request.rule_name.strip()}" {request.move_position}'
            if request.move_position in ("before", "after"):
                if not request.anchor_rule.strip():
                    return {"error": "Anchor rule name is required for before/after move."}
                base += f' "{request.anchor_rule.strip()}"'
            return {"command": base}

        if action == "set":
            parts = [f'{PaloAltoService._rule_base(request.vsys)} "{request.rule_name.strip()}"']

            parts.append("disabled yes" if request.disabled else "disabled no")

            if request.rule_action:
                parts.append(f"action {request.rule_action}")

            for field_name, keyword in PaloAltoService.LIST_FIELDS:
                formatted = PaloAltoService._format_list_value(getattr(request, field_name) or "")
                if formatted:
                    parts.append(f"{keyword} {formatted}")

            if request.description and request.description.strip():
                parts.append(f'description "{request.description.strip()}"')

            if request.log_end in ("yes", "no"):
                parts.append(f"log-end {request.log_end}")

            if request.log_setting and request.log_setting.strip():
                parts.append(f'log-setting "{request.log_setting.strip()}"')

            return {"command": " ".join(parts)}

        return {"error": f"Unknown action: {action}"}

    @staticmethod
    def generate_bulk(requests: list) -> dict:
        results = []
        for index, request in enumerate(requests):
            outcome = PaloAltoService.generate_command(request)
            results.append({
                "row_index": index,
                "command": outcome.get("command"),
                "error": outcome.get("error"),
            })
        return {"results": results}

    @staticmethod
    def _object_base(vsys: str) -> str:
        if vsys:
            return f'set vsys {vsys} service'
        return "set service"

    @staticmethod
    def generate_service_command(request) -> dict:
        if not request.name.strip():
            return {"error": "Service 이름은 필수입니다."}

        protocol = request.protocol.strip().lower()
        if protocol not in ("tcp", "udp"):
            return {"error": "protocol은 tcp 또는 udp만 지원합니다."}

        port = request.port.strip()
        if not port:
            return {"error": "port는 필수입니다."}

        name = PaloAltoService._quote_if_needed(request.name.strip())
        command = f'{PaloAltoService._object_base(request.vsys)} {name} protocol {protocol} port {port}'
        return {"command": command}

    @staticmethod
    def generate_service_bulk(requests: list) -> dict:
        results = []
        for index, request in enumerate(requests):
            outcome = PaloAltoService.generate_service_command(request)
            results.append({
                "row_index": index,
                "command": outcome.get("command"),
                "error": outcome.get("error"),
            })
        return {"results": results}
