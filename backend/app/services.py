from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from app.models import (
    InvitationStatus,
    MembershipStatus,
    Tenant,
    TenantInvitation,
    TenantRole,
    TenantStatus,
    TenantUser,
    UserProfile,
    new_id,
    now_iso,
)
from app.repository import InMemoryTenantRepository


ADMIN_ROLES = {TenantRole.PLATFORM_ADMIN, TenantRole.TENANT_OWNER, TenantRole.TENANT_ADMIN}


class AuthorizationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class TenantService:
    def __init__(self, repository: InMemoryTenantRepository) -> None:
        self.repository = repository

    def ensure_user(self, cognito_sub: str, email: str, display_name: str | None = None) -> UserProfile:
        user = self.repository.get_user_by_cognito_sub(cognito_sub)
        if user:
            return user

        return self.repository.save_user(
            UserProfile(
                user_id=new_id("usr"),
                cognito_sub=cognito_sub,
                email=email,
                display_name=display_name or email,
            )
        )

    def create_tenant(
        self,
        tenant_name: str,
        admin_email: str,
        actor_cognito_sub: str,
        actor_display_name: str | None = None,
    ) -> dict:
        if not tenant_name.strip():
            raise ValidationError("tenant_name is required")
        if not admin_email.strip():
            raise ValidationError("admin_email is required")

        actor = self.ensure_user(actor_cognito_sub, admin_email, actor_display_name)
        tenant = self.repository.save_tenant(
            Tenant(
                tenant_id=new_id("ten"),
                tenant_name=tenant_name.strip(),
                status=TenantStatus.PENDING_ADMIN_ACCEPTANCE,
            )
        )
        invitation = self._create_invitation(
            tenant_id=tenant.tenant_id,
            email=admin_email,
            role=TenantRole.TENANT_OWNER,
            invited_by_user_id=actor.user_id,
        )

        return {
            "tenant": asdict(tenant),
            "invitation": asdict(invitation),
        }

    def list_tenants_for_user(self, cognito_sub: str, email: str) -> list[dict]:
        user = self.ensure_user(cognito_sub, email)
        memberships = self.repository.list_user_memberships(user.user_id)
        tenant_ids = {membership.tenant_id for membership in memberships}
        tenants = [
            tenant
            for tenant in self.repository.list_tenants()
            if tenant.tenant_id in tenant_ids
        ]
        return [asdict(tenant) for tenant in tenants]

    def get_tenant_detail(self, tenant_id: str, cognito_sub: str, email: str) -> dict:
        tenant = self._tenant_or_raise(tenant_id)
        user = self.ensure_user(cognito_sub, email)
        membership = self._membership_or_raise(tenant_id, user.user_id)

        return {
            "tenant": asdict(tenant),
            "current_membership": asdict(membership),
            "members": self.list_members(tenant_id, cognito_sub, email),
            "invitations": self.list_invitations(tenant_id, cognito_sub, email),
        }

    def invite_user(
        self,
        tenant_id: str,
        invitee_email: str,
        role: TenantRole,
        actor_cognito_sub: str,
        actor_email: str,
    ) -> dict:
        actor = self.ensure_user(actor_cognito_sub, actor_email)
        self._require_admin(tenant_id, actor.user_id)
        self._tenant_or_raise(tenant_id)

        invitation = self._create_invitation(
            tenant_id=tenant_id,
            email=invitee_email,
            role=role,
            invited_by_user_id=actor.user_id,
        )
        return asdict(invitation)

    def accept_invitation(
        self,
        token: str,
        cognito_sub: str,
        email: str,
        display_name: str | None = None,
    ) -> dict:
        invitation = self.repository.get_invitation_by_token(token)
        if invitation is None:
            raise NotFoundError("Invitation was not found")
        if invitation.status != InvitationStatus.PENDING:
            raise ValidationError("Invitation is no longer pending")

        expires_at = datetime.fromisoformat(invitation.expires_at)
        if expires_at < datetime.now(UTC):
            invitation.status = InvitationStatus.EXPIRED
            raise ValidationError("Invitation has expired")

        user = self.ensure_user(cognito_sub, email, display_name)
        membership = self.repository.save_membership(
            TenantUser(
                tenant_id=invitation.tenant_id,
                user_id=user.user_id,
                role=invitation.role,
                status=MembershipStatus.ACTIVE,
            )
        )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now_iso()

        tenant = self._tenant_or_raise(invitation.tenant_id)
        if tenant.status == TenantStatus.PENDING_ADMIN_ACCEPTANCE:
            tenant.status = TenantStatus.ACTIVE
            tenant.updated_at = now_iso()

        return {
            "tenant": asdict(tenant),
            "current_membership": asdict(membership),
            "members": self.list_members(tenant.tenant_id, cognito_sub, email),
            "invitations": self.list_invitations(tenant.tenant_id, cognito_sub, email),
        }

    def list_members(self, tenant_id: str, cognito_sub: str, email: str) -> list[dict]:
        user = self.ensure_user(cognito_sub, email)
        self._membership_or_raise(tenant_id, user.user_id)
        rows = []

        for membership in self.repository.list_memberships(tenant_id):
            profile = self.repository.get_user(membership.user_id)
            rows.append(
                {
                    **asdict(membership),
                    "email": profile.email if profile else "",
                    "display_name": profile.display_name if profile else "",
                }
            )

        return rows

    def list_invitations(self, tenant_id: str, cognito_sub: str, email: str) -> list[dict]:
        user = self.ensure_user(cognito_sub, email)
        self._require_admin(tenant_id, user.user_id)
        return [asdict(invitation) for invitation in self.repository.list_invitations(tenant_id)]

    def _create_invitation(
        self,
        tenant_id: str,
        email: str,
        role: TenantRole,
        invited_by_user_id: str,
    ) -> TenantInvitation:
        if not email.strip():
            raise ValidationError("email is required")

        expires_at = datetime.now(UTC) + timedelta(days=7)
        return self.repository.save_invitation(
            TenantInvitation(
                invitation_id=new_id("inv"),
                tenant_id=tenant_id,
                email=email.strip().lower(),
                role=role,
                token=token_urlsafe(24),
                expires_at=expires_at.isoformat(),
                invited_by_user_id=invited_by_user_id,
            )
        )

    def _tenant_or_raise(self, tenant_id: str) -> Tenant:
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant was not found")
        return tenant

    def _membership_or_raise(self, tenant_id: str, user_id: str) -> TenantUser:
        membership = self.repository.get_membership(tenant_id, user_id)
        if membership is None or membership.status != MembershipStatus.ACTIVE:
            raise AuthorizationError("Active tenant membership is required")
        return membership

    def _require_admin(self, tenant_id: str, user_id: str) -> TenantUser:
        membership = self._membership_or_raise(tenant_id, user_id)
        if membership.role not in ADMIN_ROLES:
            raise AuthorizationError("Tenant admin role is required")
        return membership
