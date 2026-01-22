from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    is_active: bool
    roles: List[str]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str
    roles: List[str] = []


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserRolesUpdate(BaseModel):
    roles: List[str]


class AuditLogOut(BaseModel):
    id: str
    request_id: str
    actor_user_id: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    payload_json: Dict[str, Any]
    created_at: datetime


Discipline = Literal[
    "System",
    "Mechanical",
    "Software",
    "Electronics",
    "Automation",
    "Optics",
    "Other",
]

RequirementType = Literal[
    "Functional",
    "Performance",
    "Safety",
    "Security",
    "Regulatory",
    "Interface",
    "Constraint",
]

WorkflowStatus = Literal["Draft", "Review", "Approved", "Rejected"]
ApprovalDecision = Literal["APPROVE", "REJECT"]
NotificationType = Literal["MENTION", "WORKFLOW", "APPROVAL"]
TraceEntityType = Literal["Requirement", "Test", "Design", "Standard"]
TraceLinkType = Literal["DERIVES", "SATISFIES", "VERIFIES", "REFERENCES"]
VerificationMethod = Literal["TEST", "ANALYSIS", "INSPECTION", "DEMONSTRATION"]
VerificationStatus = Literal["NOT_RUN", "PASS", "FAIL", "BLOCKED"]
EvidenceType = Literal["FILE", "LINK", "NOTE"]
EvidenceRelatedType = Literal["TestCase", "VerificationResult"]
ImportStatus = Literal["IN_PROGRESS", "COMPLETED", "FAILED"]


class RequirementCreate(BaseModel):
    title: Optional[str] = None
    text: str = Field(min_length=1)
    discipline: Discipline
    req_type_primary: RequirementType
    req_type_secondary: Optional[List[str]] = None
    is_explanation: bool = False
    status: WorkflowStatus = "Draft"
    owner_user_id: Optional[str] = None
    source: str = "manual"


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    discipline: Optional[Discipline] = None
    req_type_primary: Optional[RequirementType] = None
    req_type_secondary: Optional[List[str]] = None
    is_explanation: Optional[bool] = None
    owner_user_id: Optional[str] = None
    change_reason: Optional[str] = None


class RequirementOut(BaseModel):
    id: str
    req_code: str
    title: Optional[str]
    text: str
    discipline: str
    req_type_primary: str
    req_type_secondary: Optional[List[str]]
    is_explanation: bool
    status: str
    owner_user_id: str
    source: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class RequirementVersionOut(BaseModel):
    id: str
    requirement_id: str
    version_no: int
    snapshot_json: Dict[str, Any]
    changed_by_user_id: str
    change_reason: Optional[str]
    created_at: datetime


class StatusChangeRequest(BaseModel):
    to_status: WorkflowStatus
    reason: Optional[str] = None


class ApprovalRequest(BaseModel):
    decision: ApprovalDecision
    reason: Optional[str] = None
    reauth_password: Optional[str] = None


class ApprovalRecordOut(BaseModel):
    id: str
    requirement_id: str
    approver_user_id: str
    decision: str
    reason: Optional[str]
    signature_provider: str
    signature_metadata: Dict[str, Any]
    signed_at: datetime


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentUpdate(BaseModel):
    text: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: str
    requirement_id: str
    author_user_id: str
    text: str
    created_at: datetime
    edited_at: Optional[datetime]
    deleted_at: Optional[datetime]


class NotificationOut(BaseModel):
    id: str
    type: NotificationType
    title: str
    body: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    is_read: bool
    created_at: datetime


class LinkCreate(BaseModel):
    source_type: TraceEntityType
    source_id: str
    target_type: TraceEntityType
    target_id: str
    link_type: TraceLinkType


class LinkOut(BaseModel):
    id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    link_type: str
    created_by_user_id: str
    created_at: datetime
    deleted_at: Optional[datetime]


class RTMRow(BaseModel):
    req_code: Optional[str]
    requirement_title: Optional[str]
    discipline: Optional[str]
    req_type_primary: Optional[str]
    design_artifact_ids: List[str]
    test_case_ids: List[str]
    standard_clause_ids: List[str]
    suspect: bool
    coverage_status: str
    verification_status: VerificationStatus
    suspect_auto_cleared: bool


class ImpactItem(BaseModel):
    entity_type: str
    entity_id: str
    path: List[str]


class ImpactOut(BaseModel):
    requirement_id: str
    impacted: List[ImpactItem]


class OrphanItem(BaseModel):
    entity_type: TraceEntityType
    entity_id: str
    label: Optional[str] = None


class OrphanReport(BaseModel):
    tests: List[OrphanItem]
    designs: List[OrphanItem]
    standards: List[OrphanItem]


class TestCaseCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    verification_method: VerificationMethod
    owner_user_id: Optional[str] = None

    __test__ = False


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    verification_method: Optional[VerificationMethod] = None
    owner_user_id: Optional[str] = None

    __test__ = False


class TestCaseOut(BaseModel):
    id: str
    test_code: str
    title: str
    description: Optional[str]
    verification_method: str
    owner_user_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    __test__ = False


class VerificationResultCreate(BaseModel):
    test_case_id: str
    requirement_id: str
    baseline_id: Optional[str] = None
    status: VerificationStatus
    comment: Optional[str] = None


class VerificationResultOut(BaseModel):
    id: str
    test_case_id: str
    requirement_id: str
    baseline_id: Optional[str]
    status: str
    executed_by_user_id: str
    executed_at: datetime
    comment: Optional[str]


class EvidenceCreate(BaseModel):
    related_type: EvidenceRelatedType
    related_id: str
    evidence_type: EvidenceType
    uri_or_text: str = Field(min_length=1)
    checksum: Optional[str] = None


class EvidenceOut(BaseModel):
    id: str
    related_type: str
    related_id: str
    evidence_type: str
    uri_or_text: str
    checksum: Optional[str]
    uploaded_by_user_id: str
    created_at: datetime


class BaselineCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    requirement_ids: List[str] = Field(min_length=1)


class BaselineOut(BaseModel):
    id: str
    baseline_tag: str
    name: str
    description: Optional[str]
    created_by_user_id: str
    created_at: datetime


class BaselineItemOut(BaseModel):
    baseline_id: str
    requirement_id: str
    requirement_version_id: str
    version_no: int
    snapshot_json: Dict[str, Any]


class StandardCreate(BaseModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None


class StandardOut(BaseModel):
    id: str
    code: str
    title: str
    version: Optional[str]
    publication_year: Optional[int]
    publisher: Optional[str]
    created_at: datetime


class StandardClauseCreate(BaseModel):
    clause_code: str = Field(min_length=1)
    title: Optional[str] = None
    text: str = Field(min_length=1)


class StandardClauseOut(BaseModel):
    id: str
    standard_id: str
    clause_code: str
    title: Optional[str]
    text: str
    created_at: datetime


class ComplianceMappingCreate(BaseModel):
    requirement_id: str
    standard_clause_id: str
    compliance_status: str = Field(min_length=1)
    justification: Optional[str] = None


class ComplianceMappingOut(BaseModel):
    id: str
    requirement_id: str
    standard_clause_id: str
    compliance_status: str
    justification: Optional[str]
    created_by_user_id: str
    created_at: datetime


class ComplianceRow(BaseModel):
    baseline_id: Optional[str]
    standard_id: Optional[str]
    requirement_id: str
    req_code: Optional[str]
    requirement_title: Optional[str]
    standard_clause_id: str
    clause_code: str
    clause_title: Optional[str]
    compliance_status: str
    justification: Optional[str]


class ComplianceGapItem(BaseModel):
    requirement_id: str
    req_code: Optional[str]
    standard_clause_id: str
    clause_code: str
    compliance_status: Optional[str]


class ComplianceGapOut(BaseModel):
    missing_mappings: List[ComplianceGapItem]
    non_compliant: List[ComplianceGapItem]


class ComplianceReportOut(BaseModel):
    rows: List[ComplianceRow]
    gap_analysis: ComplianceGapOut

class ImportSessionOut(BaseModel):
    id: str
    file_name: str
    file_type: str
    uploaded_by_user_id: str
    uploaded_at: datetime
    status: ImportStatus


class ImportedClauseOut(BaseModel):
    id: str
    import_session_id: str
    raw_text: str
    location_ref: Optional[str]
    clause_index: int
    parsed_metadata: Dict[str, Any]
    created_at: datetime


class ClauseAcceptRequest(BaseModel):
    title: Optional[str] = None
    edited_text: Optional[str] = None
    discipline: Optional[Discipline] = None
    req_type_primary: Optional[RequirementType] = None
    req_type_secondary: Optional[List[str]] = None
    is_explanation: bool = False
    status: WorkflowStatus = "Draft"
    owner_user_id: Optional[str] = None


class RequirementSourceClause(BaseModel):
    source_reference_id: str
    import_session_id: str
    imported_clause_id: str
    file_name: str
    file_type: str
    clause_text: str
    location_ref: Optional[str]
    created_at: datetime


class RequirementSourceOut(BaseModel):
    requirement_id: str
    sources: List[RequirementSourceClause]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    enforce_regulatory_mapping: bool = False


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enforce_regulatory_mapping: Optional[bool] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    enforce_regulatory_mapping: bool
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime


class UnmappedRequirementItem(BaseModel):
    id: str
    req_code: str
    title: Optional[str]


class ComplianceValidationOut(BaseModel):
    valid: bool
    enforce_regulatory_mapping: bool
    unmapped_regulatory_requirements: List[UnmappedRequirementItem]
