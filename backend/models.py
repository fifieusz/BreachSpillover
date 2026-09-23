from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class EmployeeSummary(BaseModel):
    id: int
    full_name: str
    corporate_email: str
    job_title: str
    department: str
    vip_level: str
    creds_count: int = 0
    direct_leaks_count: int = 0
    address_count: int = 0
    relatives_count: int = 0

class VectorDetail(BaseModel):
    score: int
    max: int
    label: str
    triggered: bool
    details: str

class RemediationItem(BaseModel):
    vector: str
    priority: str
    title: str
    description: str

class SpilloverScoreResponse(BaseModel):
    score: int
    level: str
    color: str
    badge_class: str
    vectors: Dict[str, VectorDetail]
    remediations: List[RemediationItem]

class SearchResponse(BaseModel):
    employee: Dict[str, Any]
    spillover_score: SpilloverScoreResponse
    leaks: List[Dict[str, Any]]
    credentials: List[Dict[str, Any]]
    pivots: List[Dict[str, Any]]
    physical_footprints: List[Dict[str, Any]]
    relatives: List[Dict[str, Any]]
    graph: Dict[str, Any]
    audit_mode: bool = False
    scenario: Optional[str] = "full"

class GlobalStats(BaseModel):
    total_employees: int
    total_leaks: int
    stealer_leaks: int
    total_compromised_credentials: int
    corporate_pattern_matches: int
    exposed_physical_addresses: int
    exposed_family_members: int
