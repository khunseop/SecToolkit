import urllib.parse
import base64
import re
import ipaddress

class TransformerService:
    @staticmethod
    def url_transform(data: str, action: str) -> str:
        try:
            if action == 'encode':
                return urllib.parse.quote(data)
            else:
                return urllib.parse.unquote(data)
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def base64_transform(data: str, action: str) -> str:
        try:
            if action == 'encode':
                return base64.b64encode(data.encode('utf-8')).decode('utf-8')
            else:
                return base64.b64decode(data).decode('utf-8')
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def ip_to_sql_transform(raw_text: str) -> dict:
        input_lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
        final_patterns = set()

        for item in input_lines:
            try:
                networks = []
                if '-' in item:
                    # 1. IP Range 처리
                    start_ip, end_ip = [ip.strip() for ip in item.split('-')]
                    networks = list(ipaddress.summarize_address_range(
                        ipaddress.IPv4Address(start_ip), 
                        ipaddress.IPv4Address(end_ip)
                    ))
                else:
                    # 2. CIDR 처리
                    networks = [ipaddress.IPv4Network(item, strict=False)]

                for net in networks:
                    prefix = net.prefixlen
                    # 8, 16, 24비트 단위 케이스 (단, /32는 /24 패턴으로 취급하기 위해 제외)
                    if prefix in [8, 16, 24]:
                        octet_count = prefix // 8
                        parts = str(net.network_address).split('.')
                        final_patterns.add(".".join(parts[:octet_count]) + ".%")
                    else:
                        # 옥텟 단위가 아닐 경우 (예: /23, /22)
                        # 하위 24비트(/24) 단위 패턴들로 쪼개서 정확도 유지
                        if prefix < 24:
                            for sub_net in net.subnets(new_prefix=24):
                                parts = str(sub_net.network_address).split('.')
                                final_patterns.add(f"{parts[0]}.{parts[1]}.{parts[2]}.%")
                        else:
                            # /25 ~ /32는 LIKE로 표현 시 오탐 가능성이 커서 최소 /24 패턴으로 포함
                            parts = str(net.network_address).split('.')
                            final_patterns.add(f"{parts[0]}.{parts[1]}.{parts[2]}.%")
            except Exception:
                continue

        patterns = sorted(list(final_patterns))
        column_name = "ip_address"
        sql_where = " OR ".join([f"{column_name} LIKE '{p}'" for p in patterns])
        
        return {
            "patterns": patterns,
            "sql_where": f"WHERE {sql_where}" if sql_where else ""
        }

    @staticmethod
    def analyze_text(text: str, encoding: str) -> dict:
        try:
            byte_size = len(text.encode(encoding))
            char_count = len(text)
            
            # 문자 유형별 정규식 분석
            hangul = len(re.findall(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', text))
            english = len(re.findall(r'[a-zA-Z]', text))
            numbers = len(re.findall(r'[0-9]', text))
            whitespace = len(re.findall(r'\s', text))
            
            # 특수문자 = 전체 - (한글 + 영어 + 숫자 + 공백)
            special = char_count - (hangul + english + numbers + whitespace)
            
            return {
                "bytes": byte_size,
                "chars": char_count,
                "details": {
                    "한글": hangul,
                    "영어": english,
                    "숫자": numbers,
                    "공백": whitespace,
                    "특수문자": special
                }
            }
        except Exception:
            return {"bytes": 0, "chars": 0, "details": {}}
