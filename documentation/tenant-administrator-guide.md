# Tenant Administrator Guide

This guide explains how tenant administrators use the current Tenant Admin UI for the HVAC Proposal and Submittal Automation application.

The current implementation is an MVP foundation. It supports tenant onboarding, invitation acceptance, member viewing, and user invitations. Authentication is still simulated locally, and tenant data is currently stored in memory by the backend.

## Accessing the Tenant Admin UI

Start the backend API:

```bash
python3 backend/main.py
```

Start the frontend:

```bash
cd frontend
npm start
```

Open the application:

```text
http://localhost:4200/
```

## Tenant Onboarding

Use the **Tenant Onboarding** panel to create a new tenant.

Required fields:

- **Tenant name**: The company or customer organization name.
- **Owner email**: The initial tenant owner email address.
- **Owner display name**: The display name for the initial tenant owner.

When the tenant is created, the system also creates a pending invitation for the initial owner. The tenant starts in:

```text
PENDING_ADMIN_ACCEPTANCE
```

The tenant becomes active after the owner invitation is accepted.

## Accepting an Invitation

Use the **Accept Invitation** panel to activate a tenant membership.

Required fields:

- **Invitation token**: The token shown in the Invitations table.
- **Display name**: The name for the accepting user.

After a valid owner invitation is accepted:

- The user becomes a tenant member.
- The user receives the `TENANT_OWNER` role.
- The tenant status changes to `ACTIVE`.

In the current local MVP, invitation tokens are visible in the UI so the onboarding flow can be tested without email delivery. In production, invitation tokens should be sent by email and should not be exposed in an administrator table.

## Viewing Tenants

The tenant list appears in the left sidebar.

Select a tenant to view:

- Tenant status
- Active members
- Pending and accepted invitations
- Available tenant administration actions

Only tenants associated with the current authenticated user should be visible. In the current local MVP, the authenticated user is simulated by request headers.

## Viewing Members

The **Members** panel lists accepted tenant users.

Each row includes:

- Display name
- Email
- Role
- Status

The backend authorization model treats the application database as the source of truth for tenant membership and roles. Cognito authenticates the user, but tenant access is checked against tenant membership records.

## Inviting Users

Use the **Invite User** panel to invite another user to the selected tenant.

Required fields:

- **Email**: The invited user's email address.
- **Role**: The role the user should receive after accepting the invitation.

Available tenant roles:

| Role | Purpose |
|---|---|
| `TENANT_ADMIN` | Can manage tenant users and settings. |
| `TENANT_USER` | Standard application user. |
| `TENANT_READ_ONLY` | Read-only access. |

The current UI exposes tenant-level roles only. `PLATFORM_ADMIN` is reserved for internal SaaS administrators, and `TENANT_OWNER` is assigned through the initial owner invitation flow.

## Invitation Statuses

Invitations can have these statuses:

| Status | Meaning |
|---|---|
| `PENDING` | The invitation has been created but not accepted. |
| `ACCEPTED` | The invited user accepted the invitation. |
| `EXPIRED` | The invitation was not accepted before expiration. |
| `REVOKED` | The invitation was cancelled by an administrator. |

The current backend creates invitations with a seven-day expiration window.

## Current MVP Limitations

The current UI is meant to validate the tenant administration workflow. It is not production-ready yet.

Current limitations:

- Tenant data is stored in memory and resets when the backend restarts.
- Authentication is simulated with local request headers.
- Invitation tokens are visible in the UI for testing.
- Invitation emails are not sent yet.
- User disabling and role editing are not implemented yet.
- Audit logging is not implemented yet.
- Cognito JWT verification is not wired into the backend yet.

## Production Behavior Target

The production tenant administration flow should work like this:

```text
User signs in with Cognito.
Backend verifies the Cognito JWT.
Backend resolves UserProfile from cognito_sub.
Backend checks TenantUser membership and role.
Tenant admin creates an invitation.
System sends a time-limited invitation email.
Invited user signs in and accepts the invitation.
Backend creates or updates tenant membership.
```

This matches the authentication and authorization architecture in [authentication-authorization.md](authentication-authorization.md).
