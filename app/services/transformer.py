import urllib.parse
import base64
import re

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
