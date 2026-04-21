from pydantic import BaseModel
from typing import List, Optional

class ConvertRequest(BaseModel):
    category: str
    value: float
    from_unit: str
    to_unit: str

class JsonRequest(BaseModel):
    data: str

class DnsLookupRequest(BaseModel):
    host: str

class DnsLookupResponse(BaseModel):
    host: str
    ips: List[str]
    reverse_name: str = "-"
    error: Optional[str] = None
