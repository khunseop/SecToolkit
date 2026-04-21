from pydantic import BaseModel

class ConvertRequest(BaseModel):
    category: str
    value: float
    from_unit: str
    to_unit: str

class JsonRequest(BaseModel):
    data: str
