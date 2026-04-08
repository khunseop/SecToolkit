import pacparser
import requests
import difflib
from urllib.parse import urlparse

class PacService:
    @staticmethod
    def _ensure_schema(url: str) -> str:
        if not url: return url
        if not url.startswith(('http://', 'https://')):
            return 'http://' + url
        return url

    @staticmethod
    def _find_matching_rule(pac_text: str, proxy_result: str) -> str:
        """Heuristic to find the matching rule line."""
        if not proxy_result or proxy_result == "DIRECT":
            return "DIRECT (No specific rule matched or default)"
        
        # Extract the proxy part if it's like "PROXY 1.2.3.4:80"
        parts = proxy_result.split(';')
        for part in parts:
            part = part.strip()
            if not part: continue
            
            # Simple heuristic: find the line containing the first proxy result
            # We skip 'PROXY' or 'SOCKS' to search for the host/port
            search_str = part.split(' ')[-1] if ' ' in part else part
            lines = pac_text.splitlines()
            for i, line in enumerate(lines):
                if search_str in line:
                    return f"L{i+1}: {line.strip()}"
        return proxy_result

    @staticmethod
    def _validate_pac(pac_text: str, target_url: str, host: str) -> dict:
        """Helper to validate PAC syntax and get proxy result."""
        pacparser.init()
        try:
            # Check syntax by attempting to parse
            pacparser.parse_pac_string(pac_text)
            proxy = pacparser.find_proxy(target_url, host)
            matched_rule = PacService._find_matching_rule(pac_text, proxy)
            return {"valid": True, "proxy": proxy, "matched_rule": matched_rule, "error": None}
        except Exception as e:
            return {"valid": False, "proxy": None, "matched_rule": None, "error": str(e)}
        finally:
            pacparser.cleanup()

    @staticmethod
    def test_pac(pac_url: str, target_url: str) -> dict:
        try:
            pac_url = PacService._ensure_schema(pac_url)
            target_url = PacService._ensure_schema(target_url)
            
            response = requests.get(pac_url, timeout=5)
            response.raise_for_status()
            pac_text = response.text
            
            parsed_target = urlparse(target_url)
            host = parsed_target.hostname
            if not host: return {"error": "Invalid target URL."}
            
            val = PacService._validate_pac(pac_text, target_url, host)
            if not val["valid"]: return {"error": f"PAC syntax error: {val['error']}"}
            
            return {
                "pac_url": pac_url,
                "target_url": target_url,
                "result": val["proxy"],
                "matched_rule": val["matched_rule"],
                "pac_preview": pac_text # Show full text now
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def diff_pac(prod_url: str, test_url: str, sample_url: str) -> dict:
        try:
            prod_url = PacService._ensure_schema(prod_url)
            test_url = PacService._ensure_schema(test_url)
            sample_url = PacService._ensure_schema(sample_url)

            # 1. Fetch both files
            r_prod = requests.get(prod_url, timeout=5)
            r_test = requests.get(test_url, timeout=5)
            r_prod.raise_for_status()
            r_test.raise_for_status()
            
            prod_text = r_prod.text
            test_text = r_test.text
            
            # 2. Validate & Test Sample URL
            parsed_sample = urlparse(sample_url)
            host = parsed_sample.hostname or "localhost"
            
            prod_val = PacService._validate_pac(prod_text, sample_url, host)
            test_val = PacService._validate_pac(test_text, sample_url, host)
            
            # 3. Compute Text Diff
            # ndiff returns a delta with prefixes: '  ' (unchanged), '+ ' (added), '- ' (removed)
            diff = list(difflib.ndiff(prod_text.splitlines(), test_text.splitlines()))
            
            return {
                "prod_status": {
                    "valid": prod_val["valid"], 
                    "proxy": prod_val["proxy"], 
                    "matched_rule": prod_val["matched_rule"],
                    "error": prod_val["error"]
                },
                "test_status": {
                    "valid": test_val["valid"], 
                    "proxy": test_val["proxy"], 
                    "matched_rule": test_val["matched_rule"],
                    "error": test_val["error"]
                },
                "diff_result": diff,
                "sample_url": sample_url
            }
        except Exception as e:
            return {"error": str(e)}
