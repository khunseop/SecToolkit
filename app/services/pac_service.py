import pacparser
import requests
import difflib
import bisect
from urllib.parse import urlparse

class PacService:
    @staticmethod
    def _ensure_schema(url: str) -> str:
        if not url: return url
        if not url.startswith(('http://', 'https://')):
            return 'http://' + url
        return url

    @staticmethod
    def _validate_pac(pac_text: str, target_url: str, host: str) -> dict:
        """Helper to validate PAC syntax and get proxy result using standard pacparser."""
        import socket
        resolved_ips = []
        try:
            # Fetch all associated IP addresses (IPv4 & IPv6)
            addr_info = socket.getaddrinfo(host, None)
            resolved_ips = list(set([info[4][0] for info in addr_info]))
        except:
            pass

        pacparser.init()
        try:
            pacparser.parse_pac_string(pac_text)
            proxy = pacparser.find_proxy(target_url, host)
            return {
                "valid": True, 
                "proxy": proxy, 
                "resolved_ips": resolved_ips,
                "error": None
            }
        except Exception as e:
            return {
                "valid": False,
                "proxy": None,
                "resolved_ips": resolved_ips,
                "error": str(e)
            }
        finally:
            pacparser.cleanup()
    @staticmethod
    def _fetch_pac(url: str) -> str:
        """Fetch PAC with encoding fallback (UTF-8 -> EUC-KR) and detailed error handling."""
        try:
            # Set a reasonable timeout for both connection and read
            response = requests.get(url, timeout=(3.05, 10))
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise Exception(f"PAC fetch timed out: Connection to {url} took too long.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"PAC fetch failed: Could not connect to {url}. Check if the server is up.")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 404:
                raise Exception(f"PAC fetch failed: File not found (404) at {url}.")
            elif status_code == 403:
                raise Exception(f"PAC fetch failed: Permission denied (403) for {url}.")
            else:
                raise Exception(f"PAC fetch failed: HTTP Error {status_code} for {url}.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"PAC fetch failed: An unexpected error occurred: {str(e)}")
        
        # Try decoding with UTF-8, then fallback to EUC-KR
        try:
            return response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return response.content.decode('euc-kr')
            except UnicodeDecodeError:
                # Last resort: use requests default behavior which might use ISO-8859-1
                return response.text

    @staticmethod
    def test_pac(pac_url: str, target_url: str, client_ip: str = None) -> dict:
        try:
            if not pac_url:
                return {"error": "PAC URL is required."}
            if not target_url:
                return {"error": "Target URL is required."}

            pac_url = PacService._ensure_schema(pac_url)
            target_url = PacService._ensure_schema(target_url)
            
            try:
                pac_text = PacService._fetch_pac(pac_url)
            except Exception as fe:
                return {"error": str(fe)}
            
            parsed_target = urlparse(target_url)
            host = parsed_target.hostname
            if not host: 
                return {"error": f"Invalid target URL: '{target_url}'. Hostname could not be parsed."}
            
            val = PacService._validate_pac(pac_text, target_url, host)
            if not val["valid"]: 
                return {"error": f"PAC Syntax/Execution Error: {val['error']}"}
            
            return {
                "pac_url": pac_url,
                "target_url": target_url,
                "resolved_ips": val["resolved_ips"],
                "client_ip": client_ip,
                "result": val["proxy"],
                "pac_preview": pac_text
            }
        except Exception as e:
            return {"error": f"Internal Error: {str(e)}"}

    @staticmethod
    def diff_pac(prod_url: str, test_url: str, sample_url: str, client_ip: str = None) -> dict:
        try:
            if not prod_url or not test_url or not sample_url:
                return {"error": "Production PAC URL, Test PAC URL, and Sample Target URL are all required."}

            prod_url = PacService._ensure_schema(prod_url)
            test_url = PacService._ensure_schema(test_url)
            sample_url = PacService._ensure_schema(sample_url)

            # 1. Fetch both files with encoding handling
            try:
                prod_text = PacService._fetch_pac(prod_url)
            except Exception as e:
                return {"error": f"Failed to fetch Production PAC: {str(e)}"}
            
            try:
                test_text = PacService._fetch_pac(test_url)
            except Exception as e:
                return {"error": f"Failed to fetch Test PAC: {str(e)}"}
            
            # 2. Validate & Test Sample URL
            parsed_sample = urlparse(sample_url)
            host = parsed_sample.hostname or "localhost"
            
            prod_val = PacService._validate_pac(prod_text, sample_url, host)
            test_val = PacService._validate_pac(test_text, sample_url, host)
            
            # 3. Compute Text Diff
            raw_diff = list(difflib.ndiff(prod_text.splitlines(), test_text.splitlines()))
            # Filter only changes (+ or -)
            changes_only = [line for line in raw_diff if line.startswith(('-', '+'))]
            
            return {
                "sample_url": sample_url,
                "client_ip": client_ip,
                "resolved_ips": list(set(prod_val["resolved_ips"] + test_val["resolved_ips"])),
                "prod_status": {
                    "valid": prod_val["valid"], 
                    "proxy": prod_val["proxy"], 
                    "error": prod_val["error"]
                },
                "test_status": {
                    "valid": test_val["valid"], 
                    "proxy": test_val["proxy"], 
                    "error": test_val["error"]
                },
                "diff_result": raw_diff,
                "changes_only": changes_only
            }
        except Exception as e:
            return {"error": f"Internal Error during comparison: {str(e)}"}
