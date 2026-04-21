from pydantic import BaseModel

class TransformRequest(BaseModel):
    data: str
    action: str

class ByteCountRequest(BaseModel):
    text: str
    encoding: str
