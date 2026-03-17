import urllib.parse
import base64

class TransformerService:
    @staticmethod
    def decode_data(data: str, decode_type: str) -> str:
        try:
            if decode_type == 'url':
                return urllib.parse.unquote(data)
            elif decode_type == 'base64':
                return base64.b64decode(data).decode('utf-8')
            return "Unsupported type"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def count_bytes(text: str, encoding: str) -> int:
        try:
            return len(text.encode(encoding))
        except Exception:
            return 0
