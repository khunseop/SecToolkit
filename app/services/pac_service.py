import pacparser
import requests
from urllib.parse import urlparse

class PacService:
    @staticmethod
    def test_pac(pac_url: str, target_url: str) -> dict:
        try:
            # 1. Fetch PAC file content
            response = requests.get(pac_url, timeout=5)
            response.raise_for_status()
            pac_text = response.text
            
            # 2. Extract host from target URL
            parsed_target = urlparse(target_url)
            host = parsed_target.hostname
            if not host:
                return {"error": "Invalid target URL: No hostname found."}
            
            # 3. Initialize pacparser and find proxy
            # Note: pacparser.init() and cleanup() are managed within this context
            # to prevent state issues between requests.
            pacparser.init()
            try:
                pacparser.parse_pac_string(pac_text)
                proxy = pacparser.find_proxy(target_url, host)
                return {
                    "pac_url": pac_url,
                    "target_url": target_url,
                    "result": proxy,
                    "pac_preview": pac_text[:300] + "..." if len(pac_text) > 300 else pac_text
                }
            finally:
                pacparser.cleanup()
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch PAC file: {str(e)}"}
        except Exception as e:
            return {"error": f"PAC parsing error: {str(e)}"}
