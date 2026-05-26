export type TenantStatus = 'PENDING_ADMIN_ACCEPTANCE' | 'ACTIVE' | 'SUSPENDED';

export type TenantRole =
  | 'PLATFORM_ADMIN'
  | 'TENANT_OWNER'
  | 'TENANT_ADMIN'
  | 'TENANT_USER'
  | 'TENANT_READ_ONLY';

export type InvitationStatus = 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED';

export interface Tenant {
  tenant_id: string;
  tenant_name: string;
  status: TenantStatus;
  subscription_plan: string;
  created_at: string;
  updated_at: string;
}

export interface TenantMember {
  tenant_id: string;
  user_id: string;
  role: TenantRole;
  status: 'ACTIVE' | 'DISABLED';
  created_at: string;
  email: string;
  display_name: string;
}

export interface TenantInvitation {
  invitation_id: string;
  tenant_id: string;
  email: string;
  role: TenantRole;
  token: string;
  expires_at: string;
  invited_by_user_id: string;
  status: InvitationStatus;
  accepted_at?: string | null;
  created_at: string;
}

export interface TenantDetail {
  tenant: Tenant;
  current_membership: TenantMember;
  members: TenantMember[];
  invitations: TenantInvitation[];
}

export interface CreateTenantRequest {
  tenant_name: string;
  admin_email: string;
  display_name?: string;
}

export interface CreateTenantResponse {
  tenant: Tenant;
  invitation: TenantInvitation;
}

export interface CreateInvitationRequest {
  email: string;
  role: TenantRole;
}
