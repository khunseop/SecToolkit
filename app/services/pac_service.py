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
    def _find_matching_rule(pac_text: str, target_url: str, host: str) -> dict:
        """Find the exact matching line by instrumenting the PAC file with fallback."""
        import re
        
        # 1. Get original result first as fallback in case instrumentation fails
        fallback_res = {"proxy": "DIRECT", "matched_rule": "Default (Matched but line tracking failed)", "line": None}
        pacparser.init()
        try:
            pacparser.parse_pac_string(pac_text)
            fallback_res["proxy"] = pacparser.find_proxy(target_url, host)
        except Exception as e:
            return {"proxy": "ERROR", "matched_rule": "Syntax Error", "line": None, "error": str(e)}
        finally:
            pacparser.cleanup()

        # 2. Try instrumentation to find the exact line
        try:
            helper = "function __trace_ret(v, l) { if (typeof v !== 'string') return v; return v + '; [[MATCH_L' + l + ']]'; }\n"
            line_offsets = [0]
            for m in re.finditer(r'\n', pac_text):
                line_offsets.append(m.end())
            
            def get_line_num(offset):
                return bisect.bisect_right(line_offsets, offset)

            last_pos = 0
            instrumented_parts = [helper]
            
            # Regex to find 'return ... ;' or 'return ...' but not inside comments. 
            # Semicolon is optional at the end.
            for m in re.finditer(r'\breturn\s+([^;/\n{}]+)(;?)', pac_text):
                # Check if it's in a comment (crude check)
                preceding_text = pac_text[last_pos:m.start()]
                if '//' in preceding_text.splitlines()[-1] if preceding_text.splitlines() else False:
                    instrumented_parts.append(pac_text[last_pos:m.end()])
                    last_pos = m.end()
                    continue
                    
                line_num = get_line_num(m.start())
                val_expr = m.group(1).strip()
                semicolon = m.group(2)
                
                instrumented_parts.append(pac_text[last_pos:m.start()])
                instrumented_parts.append(f"return __trace_ret({val_expr}, {line_num}){semicolon}")
                last_pos = m.end()
                
            instrumented_parts.append(pac_text[last_pos:])
            instrumented_pac = "".join(instrumented_parts)
            
            pacparser.init()
            try:
                pacparser.parse_pac_string(instrumented_pac)
                full_result = pacparser.find_proxy(target_url, host)
                
                # Extract line number marker from result (e.g., "DIRECT; [[MATCH_L45]]")
                line_match = re.search(r'\[\[MATCH_L(\d+)\]\]', full_result)
                
                if line_match:
                    line_num = int(line_match.group(1))
                    line_idx = line_num - 1
                    clean_result = full_result.replace(f"; [[MATCH_L{line_match.group(1)}]]", "").strip()
                    
                    # Create snippet from ORIGINAL pac_text
                    lines = pac_text.splitlines()
                    start = max(0, line_idx - 1)
                    end = min(len(lines), line_idx + 2)
                    snippet_lines = []
                    for i in range(start, end):
                        prefix = ">> " if i == line_idx else "   "
                        snippet_lines.append(f"{prefix}L{i+1}: {lines[i].strip()}")
                    
                    return {
                        "proxy": clean_result,
                        "matched_rule": "\n".join(snippet_lines),
                        "line": line_num
                    }
            finally:
                pacparser.cleanup()
        except:
            # If instrumentation logic fails (e.g. regex corruption), use fallback
            pass
            
        return fallback_res

    @staticmethod
    def _validate_pac(pac_text: str, target_url: str, host: str) -> dict:
        """Helper to validate PAC syntax and get proxy result."""
        import socket
        resolved_ip = None
        try:
            resolved_ip = socket.gethostbyname(host)
        except:
            pass

        # Use the new instrumentation method to get exact match
        match_info = PacService._find_matching_rule(pac_text, target_url, host)
        
        if match_info["proxy"] == "ERROR":
            return {
                "valid": False,
                "proxy": None,
                "matched_rule": None,
                "resolved_ip": resolved_ip,
                "error": match_info.get("error", "Unknown Syntax Error")
            }

        return {
            "valid": True, 
            "proxy": match_info["proxy"], 
            "matched_rule": match_info["matched_rule"], 
            "resolved_ip": resolved_ip,
            "error": None
        }

    @staticmethod
    def _fetch_pac(url: str) -> str:
        """Fetch PAC with encoding fallback (UTF-8 -> EUC-KR)."""
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        # Try decoding with UTF-8, then fallback to EUC-KR
        try:
            return response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return response.content.decode('euc-kr')
            except UnicodeDecodeError:
                # Last resort: use requests default behavior
                return response.text

    @staticmethod
    def test_pac(pac_url: str, target_url: str) -> dict:
        try:
            pac_url = PacService._ensure_schema(pac_url)
            target_url = PacService._ensure_schema(target_url)
            
            pac_text = PacService._fetch_pac(pac_url)
            
            parsed_target = urlparse(target_url)
            host = parsed_target.hostname
            if not host: return {"error": "Invalid target URL."}
            
            val = PacService._validate_pac(pac_text, target_url, host)
            if not val["valid"]: return {"error": f"PAC syntax error: {val['error']}"}
            
            return {
                "pac_url": pac_url,
                "target_url": target_url,
                "resolved_ip": val["resolved_ip"],
                "result": val["proxy"],
                "matched_rule": val["matched_rule"],
                "pac_preview": pac_text
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def diff_pac(prod_url: str, test_url: str, sample_url: str) -> dict:
        try:
            prod_url = PacService._ensure_schema(prod_url)
            test_url = PacService._ensure_schema(test_url)
            sample_url = PacService._ensure_schema(sample_url)

            # 1. Fetch both files with encoding handling
            prod_text = PacService._fetch_pac(prod_url)
            test_text = PacService._fetch_pac(test_url)
            
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
                "resolved_ip": prod_val["resolved_ip"] or test_val["resolved_ip"],
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
                "diff_result": raw_diff,
                "changes_only": changes_only
            }
        except Exception as e:
            return {"error": str(e)}
