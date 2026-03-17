import json

class AnalyzerService:
    @staticmethod
    def convert_network_unit(value: float, from_unit: str) -> dict:
        """
        Mbps to MB/s and vice versa.
        1 Byte = 8 bits
        """
        try:
            if from_unit == 'mbps':
                # Mbps -> MB/s: divide by 8
                return {"mbps": value, "mbs": round(value / 8, 2)}
            elif from_unit == 'mbs':
                # MB/s -> Mbps: multiply by 8
                return {"mbps": round(value * 8, 2), "mbs": value}
            return {"error": "Unsupported unit"}
        except Exception as e:
            return {"error": str(e)}

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
        """
        Extracts key headers from HAR entries.
        """
        extracted = []
        try:
            entries = har_data.get('log', {}).get('entries', [])
            target_headers = ['Authorization', 'Cookie', 'X-Forwarded-For', 'User-Agent', 'Content-Type']
            
            for entry in entries:
                request = entry.get('request', {})
                url = request.get('url')
                method = request.get('method')
                headers = request.get('headers', [])
                
                header_map = {h['name']: h['value'] for h in headers}
                found_headers = {name: header_map.get(name, '-') for name in target_headers}
                
                extracted.append({
                    "method": method,
                    "url": url,
                    "headers": found_headers
                })
            return extracted
        except Exception:
            return []
