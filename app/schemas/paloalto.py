from pydantic import BaseModel
from typing import List, Optional

class PolicyRuleRequest(BaseModel):
    action: str  # create | modify | delete | move
    vsys: Optional[str] = ""
    rule_name: str
    disabled: Optional[bool] = False
    rule_action: Optional[str] = "allow"
    from_zone: Optional[str] = ""
    source: Optional[str] = ""
    source_user: Optional[str] = ""
    to_zone: Optional[str] = ""
    destination: Optional[str] = ""
    service: Optional[str] = ""
    application: Optional[str] = ""
    description: Optional[str] = ""
    log_end: Optional[str] = ""  # "", "yes", "no"
    log_setting: Optional[str] = ""
    move_position: Optional[str] = ""  # top | bottom | before | after
    anchor_rule: Optional[str] = ""

class BulkGenerateRequest(BaseModel):
    rows: List[PolicyRuleRequest]

class PolicyDefaults(BaseModel):
    vsys: Optional[str] = ""
    disabled: Optional[bool] = False
    rule_action: Optional[str] = "allow"
    from_zone: Optional[str] = ""
    source: Optional[str] = ""
    source_user: Optional[str] = ""
    to_zone: Optional[str] = ""
    destination: Optional[str] = ""
    service: Optional[str] = ""
    application: Optional[str] = ""
    description: Optional[str] = ""
    log_end: Optional[str] = ""
    log_setting: Optional[str] = ""
