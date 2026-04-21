from pydantic import BaseModel
from typing import List

class PacRequest(BaseModel):
    pac_url: str
    target_url: str

class PacDiffRequest(BaseModel):
    prod_url: str
    test_url: str
    sample_url: str

class PacGroupsRequest(BaseModel):
    groups: List
