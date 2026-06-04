import re

from pydantic import BaseModel, Field, field_validator

from app.api.schemas.auth import EMAIL_PATTERN


ROLE_PATTERN = re.compile(r"^(admin|member|viewer)$")


class OrganizationResponse(BaseModel):
    id: str
    name: str
    current_user_role: str


class UpdateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class OrganizationMemberResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None = None
    role: str
    created_at: str


class OrganizationMembersResponse(BaseModel):
    members: list[OrganizationMemberResponse]


class InviteMemberRequest(BaseModel):
    email: str = Field(..., max_length=320)
    role: str = Field(default="member")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email address")
        return normalized

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not ROLE_PATTERN.fullmatch(normalized):
            raise ValueError("role must be admin, member, or viewer")
        return normalized


class UpdateMemberRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not ROLE_PATTERN.fullmatch(normalized):
            raise ValueError("role must be admin, member, or viewer")
        return normalized


class InvitationResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    invited_by_user_id: str
    status: str
    created_at: str


class InvitationsResponse(BaseModel):
    invitations: list[InvitationResponse]
