import json

class AnalyzerService:
    # 단위 변환을 위한 기준 값 (Base Unit: Data-Byte, Speed-bps, Time-Second)
    CONVERSION_MAP = {
        "data": {
            "Byte": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4,
            "bit": 1/8,
            "Kbit": 1000/8,
            "Mbit": 1000**2/8,
            "Gbit": 1000**3/8
        },
        "speed": {
            "bps": 1,
            "Kbps": 1000,
            "Mbps": 1000**2,
            "Gbps": 1000**3,
            "B/s": 8,
            "KB/s": 8 * 1024,
            "MB/s": 8 * 1024**2,
            "GB/s": 8 * 1024**3
        },
        "time": {
            "Second": 1,
            "Minute": 60,
            "Hour": 3600,
            "Day": 86400,
            "Week": 604800
        }
    }

    @staticmethod
    def convert_units(category: str, value: float, from_unit: str, to_unit: str) -> float:
        try:
            cat_map = AnalyzerService.CONVERSION_MAP.get(category)
            if not cat_map: return 0.0
            
            # 기준 단위(Base)로 변환 후 대상 단위로 변환
            base_value = value * cat_map[from_unit]
            result = base_value / cat_map[to_unit]
            
            return round(result, 6)
        except Exception:
            return 0.0

    @staticmethod
    def beautify_json(data: str) -> dict:
        try:
            parsed = json.loads(data)
            return {"formatted": json.dumps(parsed, indent=4, ensure_ascii=False)}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def extract_har_headers(har_data: dict) -> list:
        extracted = []
        try:
            entries = har_data.get('log', {}).get('entries', [])
            target_headers = ['Authorization', 'Cookie', 'X-Forwarded-For', 'User-Agent', 'Content-Type']
            for entry in entries:
                request = entry.get('request', {})
                header_map = {h['name']: h['value'] for h in request.get('headers', [])}
                extracted.append({
                    "method": request.get('method'),
                    "url": request.get('url'),
                    "headers": {name: header_map.get(name, '-') for name in target_headers}
                })
            return extracted
        except Exception: return []
