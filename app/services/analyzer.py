import json
import subprocess
import platform

class AnalyzerService:
    @staticmethod
    def get_system_proxy_settings() -> dict:
        """Extracts system-wide proxy settings. Currently optimized for macOS."""
        system = platform.system()
        try:
            if system == "Darwin":
                # Use scutil on macOS to get detailed proxy settings
                result = subprocess.run(['scutil', '--proxy'], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"raw": result.stdout, "system": system}
            elif system == "Windows":
                # Basic environment proxy for Windows
                import urllib.request
                return {"raw": str(urllib.request.getproxies()), "system": system}
            
            return {"raw": "System proxy detection not supported for this OS.", "system": system}
        except Exception as e:
            return {"error": str(e), "system": system}

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
    def convert_units(category: str, value: float, from_unit: str, to_unit: str) -> dict:
        try:
            cat_map = AnalyzerService.CONVERSION_MAP.get(category)
            if not cat_map: return {"result": 0.0, "formula": ""}
            
            # 변환 결과 계산
            base_value = value * cat_map[from_unit]
            result = round(base_value / cat_map[to_unit], 6)
            
            # 공식 문자열 생성 (1 단위 기준)
            ratio = cat_map[from_unit] / cat_map[to_unit]
            # 소수점이 너무 길면 정리
            if ratio >= 1:
                ratio_str = f"{ratio:g}"
            else:
                ratio_str = f"{ratio:.10g}"
                
            formula = f"1 {from_unit} = {ratio_str} {to_unit}"
            
            return {"result": result, "formula": formula}
        except Exception:
            return {"result": 0.0, "formula": ""}

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
