import json
import subprocess
import platform

class AnalyzerService:
    @staticmethod
    def get_system_dns_settings() -> dict:
        """Extracts system-wide DNS settings (DNS Servers)."""
        system = platform.system()
        try:
            if system == "Darwin":
                # macOS: use scutil --dns to find resolver[1] or primary resolvers
                result = subprocess.run(['scutil', '--dns'], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"raw": result.stdout, "system": system}
            elif system == "Windows":
                # Windows: Use PowerShell to get DNS server addresses for active interfaces
                ps_cmd = "Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.ServerAddresses -ne $null } | Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json"
                result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    try:
                        parsed = json.loads(result.stdout)
                        # Normalize single object to list
                        if isinstance(parsed, dict): parsed = [parsed]
                        
                        settings = {}
                        for item in parsed:
                            alias = item.get("InterfaceAlias", "Unknown")
                            addrs = item.get("ServerAddresses", [])
                            if addrs:
                                settings[alias] = ", ".join(addrs) if isinstance(addrs, list) else addrs
                        
                        return {
                            "raw": result.stdout,
                            "system": system,
                            "settings": settings
                        }
                    except:
                        pass
                # Fallback to ipconfig /all
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, encoding='cp949')
                return {"raw": result.stdout, "system": system, "settings": {}}
            
            return {"raw": f"DNS detection not supported for {system}.", "system": system, "settings": {}}
        except Exception as e:
            return {"error": str(e), "system": system, "settings": {}}

    @staticmethod
    def resolve_dns(host: str) -> dict:
        import socket
        try:
            # host가 URL 형태일 경우 hostname만 추출
            if "://" in host:
                from urllib.parse import urlparse
                host = urlparse(host).hostname or host
            
            # Fetch all associated IP addresses (IPv4 & IPv6)
            addr_info = socket.getaddrinfo(host, None)
            ips = list(set([info[4][0] for info in addr_info]))
            
            # reverse lookup (optional, for first IP)
            reverse_name = "-"
            if ips:
                try:
                    reverse_name = socket.gethostbyaddr(ips[0])[0]
                except: pass
                
            return {
                "host": host,
                "ips": ips,
                "reverse_name": reverse_name
            }
        except Exception as e:
            return {"error": str(e), "host": host, "ips": []}

    @staticmethod
    def get_system_proxy_settings() -> dict:
        """Extracts system-wide proxy settings. Optimized for macOS and Windows."""
        system = platform.system()
        try:
            if system == "Darwin":
                # Use scutil on macOS to get detailed proxy settings
                result = subprocess.run(['scutil', '--proxy'], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"raw": result.stdout, "system": system, "settings": {}} # macOS is complex, keep raw
            elif system == "Windows":
                # Detailed proxy settings from Windows Registry
                try:
                    import winreg
                    registry_path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
                        settings_dict = {}
                        # Mapping registry keys to user-friendly Windows UI labels
                        targets = [
                            ('ProxyEnable', 'Manual Proxy Server'),
                            ('ProxyServer', 'Proxy Server Address'),
                            ('ProxyOverride', 'Proxy Exceptions (Bypass)'),
                            ('AutoConfigURL', 'Use Setup Script (PAC)'),
                            ('AutoDetect', 'Automatically Detect Settings')
                        ]
                        for value_name, label in targets:
                            try:
                                val, _ = winreg.QueryValueEx(key, value_name)
                                # Convert 1/0 to ON/OFF for toggle-like settings
                                if value_name in ['ProxyEnable', 'AutoDetect']:
                                    val = "ON" if val == 1 else "OFF"
                                elif value_name == 'AutoConfigURL':
                                    # If AutoConfigURL exists, it means "Use setup script" is likely ON
                                    settings_dict['Setup Script Status'] = "ON"
                                    settings_dict['Script Address (PAC)'] = val
                                    continue
                                
                                settings_dict[label] = val
                            except FileNotFoundError:
                                if value_name == 'AutoConfigURL':
                                    settings_dict['Setup Script Status'] = "OFF"
                                continue
                        
                        return {
                            "raw": "\n".join([f"{k}: {v}" for k, v in settings_dict.items()]),
                            "system": system,
                            "settings": settings_dict
                        }
                except Exception as reg_err:
                    import urllib.request
                    return {"raw": f"Registry Error: {str(reg_err)}", "system": system, "settings": {}}
            
            return {"raw": f"Detection not supported for {system}.", "system": system, "settings": {}}
        except Exception as e:
            return {"error": str(e), "system": system, "settings": {}}

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
