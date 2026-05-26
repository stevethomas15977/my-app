from dataclasses import asdict

from app.models import Tenant, TenantInvitation, TenantUser, UserProfile


class InMemoryTenantRepository:
    def __init__(self) -> None:
        self.tenants: dict[str, Tenant] = {}
        self.users: dict[str, UserProfile] = {}
        self.users_by_cognito_sub: dict[str, str] = {}
        self.memberships: list[TenantUser] = []
        self.invitations: dict[str, TenantInvitation] = {}
        self.invitations_by_token: dict[str, str] = {}

    def save_tenant(self, tenant: Tenant) -> Tenant:
        self.tenants[tenant.tenant_id] = tenant
        return tenant

    def list_tenants(self) -> list[Tenant]:
        return sorted(self.tenants.values(), key=lambda tenant: tenant.created_at)

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.tenants.get(tenant_id)

    def save_user(self, user: UserProfile) -> UserProfile:
        self.users[user.user_id] = user
        self.users_by_cognito_sub[user.cognito_sub] = user.user_id
        return user

    def get_user_by_cognito_sub(self, cognito_sub: str) -> UserProfile | None:
        user_id = self.users_by_cognito_sub.get(cognito_sub)
        if user_id is None:
            return None
        return self.users[user_id]

    def get_user(self, user_id: str) -> UserProfile | None:
        return self.users.get(user_id)

    def save_membership(self, membership: TenantUser) -> TenantUser:
        existing = self.get_membership(membership.tenant_id, membership.user_id)
        if existing:
            existing.role = membership.role
            existing.status = membership.status
            return existing

        self.memberships.append(membership)
        return membership

    def get_membership(self, tenant_id: str, user_id: str) -> TenantUser | None:
        return next(
            (
                membership
                for membership in self.memberships
                if membership.tenant_id == tenant_id and membership.user_id == user_id
            ),
            None,
        )

    def list_memberships(self, tenant_id: str) -> list[TenantUser]:
        return [
            membership
            for membership in self.memberships
            if membership.tenant_id == tenant_id
        ]

    def list_user_memberships(self, user_id: str) -> list[TenantUser]:
        return [
            membership
            for membership in self.memberships
            if membership.user_id == user_id
        ]

    def save_invitation(self, invitation: TenantInvitation) -> TenantInvitation:
        self.invitations[invitation.invitation_id] = invitation
        self.invitations_by_token[invitation.token] = invitation.invitation_id
        return invitation

    def get_invitation_by_token(self, token: str) -> TenantInvitation | None:
        invitation_id = self.invitations_by_token.get(token)
        if invitation_id is None:
            return None
        return self.invitations[invitation_id]

    def list_invitations(self, tenant_id: str) -> list[TenantInvitation]:
        return [
            invitation
            for invitation in self.invitations.values()
            if invitation.tenant_id == tenant_id
        ]

    def dump(self, value: object) -> dict:
        return asdict(value)
