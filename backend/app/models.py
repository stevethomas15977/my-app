from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class TenantStatus(StrEnum):
    PENDING_ADMIN_ACCEPTANCE = "PENDING_ADMIN_ACCEPTANCE"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class TenantRole(StrEnum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_OWNER = "TENANT_OWNER"
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_USER = "TENANT_USER"
    TENANT_READ_ONLY = "TENANT_READ_ONLY"


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass
class Tenant:
    tenant_id: str
    tenant_name: str
    status: TenantStatus
    subscription_plan: str = "MVP"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class UserProfile:
    user_id: str
    cognito_sub: str
    email: str
    display_name: str
    created_at: str = field(default_factory=now_iso)


@dataclass
class TenantUser:
    tenant_id: str
    user_id: str
    role: TenantRole
    status: MembershipStatus = MembershipStatus.ACTIVE
    created_at: str = field(default_factory=now_iso)


@dataclass
class TenantInvitation:
    invitation_id: str
    tenant_id: str
    email: str
    role: TenantRole
    token: str
    expires_at: str
    invited_by_user_id: str
    status: InvitationStatus = InvitationStatus.PENDING
    accepted_at: str | None = None
    created_at: str = field(default_factory=now_iso)
