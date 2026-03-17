import urllib.parse
import base64

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
    def count_bytes(text: str, encoding: str) -> int:
        try:
            return len(text.encode(encoding))
        except Exception:
            return 0
