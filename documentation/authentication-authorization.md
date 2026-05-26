# Multi-Tenant SaaS Architecture with Amazon Cognito

## Overview

This document outlines a recommended architecture for implementing a multi-tenant SaaS application using Amazon Cognito for authentication and a custom application database for tenant authorization and membership management.

The design goal is to:

- Provide secure tenant isolation
- Support scalable SaaS onboarding
- Enable delegated tenant administration
- Allow future enterprise enhancements
- Maintain clean separation of authentication vs authorization responsibilities

---

# Core Architecture Principles

## Authentication vs Authorization

A critical architectural decision is separating:

| Concern | Responsibility |
|---|---|
| Authentication | Amazon Cognito |
| Authorization | Application Database + Application Logic |

### Amazon Cognito Responsibilities

Cognito should manage:

- User authentication
- Password management
- MFA, when enabled
- Email verification
- OIDC/OAuth2 flows through the user pool app client
- JWT token issuance
- Hosted UI, when a Cognito domain is configured
- Federation (SAML/OIDC), when enterprise identity providers are added

### Application Responsibilities

The application should manage:

- Tenant creation
- Tenant membership
- Tenant roles
- Invitation lifecycle
- Subscription management
- Fine-grained authorization
- Audit logging
- Resource ownership

---

# Current Terraform MVP Alignment

The current Terraform implementation in `backend/terraform/cognito.tf` provisions the initial Cognito foundation:

- Cognito User Pool
- Cognito User Pool Client
- Email auto-verification
- Password policy
- Self-service user sign-up
- OAuth scopes for `email`, `openid`, and `profile`
- Local callback/logout URLs for development
- Optional `tenant_id` custom user attribute
- Cognito Identity Pool and IAM roles for authenticated/unauthenticated identities

This is enough to start authentication work, but it does not yet configure every capability described in the future architecture. In particular, the current Terraform does not yet configure:

- MFA
- Hosted UI domain
- SAML/OIDC enterprise identity providers
- Production callback/logout URLs
- Application database tables for tenants, memberships, roles, or invitations

The recommended implementation is therefore:

```text
Cognito authenticates the user.
The application database authorizes tenant access.
Terraform creates the Cognito identity foundation first.
Tenant membership and roles are implemented in the backend/application database next.
```

---

# Cognito Tenant Attribute Guidance

The Terraform currently defines a custom Cognito attribute:

```text
custom:tenant_id
```

Treat this attribute as optional metadata only. It should not be the source of truth for tenant authorization.

Reasons:

- A user may eventually belong to multiple tenants
- Tenant roles and status can change independently from the Cognito profile
- Authorization decisions should use fresh membership data from the application database
- Cognito custom attributes are less flexible than application-owned membership records

Acceptable uses for `custom:tenant_id`:

- Storing an initial tenant hint during onboarding
- Supporting a simple first-tenant MVP flow
- Helping the backend link a newly authenticated user to a pending tenant invitation

Do not use `custom:tenant_id` by itself to authorize API access. Every backend request should still validate the user against `UserProfile` and `TenantUser` records.

---

# Recommended High-Level Architecture

```text
+-------------------+
|   Web / SPA App   |
+-------------------+
          |
          v
+-------------------+
| Amazon Cognito    |
| User Pool         |
+-------------------+
          |
          v
+-------------------+
| API Layer         |
| FastAPI / Lambda  |
+-------------------+
          |
          v
+-------------------+
| Application DB    |
| Tenant Metadata   |
| Memberships       |
| Roles             |
+-------------------+
```

---

# Recommended Tenant Onboarding Flow

## Step 1 - Tenant Sign-Up

A company representative signs up and provides:

- Company/Tenant name
- Contact information
- Initial administrator email address

Example:

```text
Tenant Name: Acme HVAC Services
Administrator Email: admin@acmehvaс.com
```

---

## Step 2 - Create Tenant Record

The application creates:

- Tenant record
- Pending invitation for initial administrator

Example:

```text
Tenant Status = PENDING_ADMIN_ACCEPTANCE
```

---

## Step 3 - Send Administrator Invitation

The application sends an email invitation containing:

- Secure one-time token
- Expiration timestamp
- Invitation acceptance URL

Example:

```text
https://app.example.com/invite/accept?token=xyz
```

---

## Step 4 - Administrator Accepts Invitation

The invited administrator:

1. Accepts the invitation
2. Creates or signs into Cognito account
3. Application links Cognito identity to tenant membership

At this point:

```text
User becomes TENANT_OWNER
```

---

## Step 5 - Tenant Administration Portal

The tenant owner/admin can:

- Invite additional users
- Assign roles
- Disable users
- Manage tenant settings
- Configure identity federation later
- View billing/subscription information

---

## Step 6 - Additional User Invitation Flow

Tenant administrators invite colleagues via email.

The invited users:

1. Receive invitation
2. Create/login via Cognito
3. Are linked to tenant membership
4. Receive assigned role permissions

---

# Recommended Database Model

## Tenant Table

```text
Tenant
- tenant_id
- tenant_name
- status
- subscription_plan
- created_at
- updated_at
```

---

## UserProfile Table

Represents the authenticated user identity.

```text
UserProfile
- user_id
- cognito_sub
- email
- display_name
- created_at
```

Notes:

- `cognito_sub` is the unique immutable Cognito user identifier
- Avoid using email address as the primary identity key

---

## TenantUser Table

Represents tenant membership.

```text
TenantUser
- tenant_id
- user_id
- role
- status
- created_at
```

This design allows:

- One user to belong to multiple tenants
- Support for consultants/support staff
- Future partner organizations

---

## TenantInvitation Table

```text
TenantInvitation
- invitation_id
- tenant_id
- email
- role
- token_hash
- expires_at
- accepted_at
- invited_by_user_id
- status
```

Security recommendations:

- Store only hashed invitation tokens
- Use time-limited invitations
- Enforce one-time use
- Log invitation acceptance events

---

# Recommended Role Model

Start simple.

| Role | Description |
|---|---|
| PLATFORM_ADMIN | Internal SaaS administrators |
| TENANT_OWNER | Primary tenant administrator |
| TENANT_ADMIN | Tenant management privileges |
| TENANT_USER | Standard application user |
| TENANT_READ_ONLY | Optional read-only access |

---

# Multi-Tenant Isolation Strategy

## Recommended Initial Approach

Start with:

```text
Shared Database
Shared Schema
Tenant ID on every tenant-owned table
```

Every tenant-owned table should include:

```text
tenant_id
```

Example:

```text
Projects
- project_id
- tenant_id
- project_name
```

---

# Critical Security Rule

Never trust frontend tenant selection alone.

Every backend API request should validate:

```text
1. User is authenticated via Cognito
2. User exists in UserProfile
3. User is active in TenantUser
4. User role permits requested action
5. Resource belongs to same tenant
```

---

# Recommended Authorization Flow

## Authentication Flow

```text
Browser -> Cognito -> JWT Token
```

## Authorization Flow

```text
JWT -> API -> Application Authorization Layer -> Database Query
```

Example backend authorization logic:

```python
if not tenant_membership:
    raise Unauthorized()

if tenant_membership.role not in allowed_roles:
    raise Forbidden()
```

---

# Why Not Use Cognito Groups Alone?

Although Cognito Groups support RBAC-style authorization, using them as the sole tenant authorization system can become difficult at scale.

Challenges include:

- Complex tenant membership management
- Limited fine-grained authorization
- Difficult multi-tenant scaling
- Operational complexity for enterprise tenants

Recommendation:

```text
Use Cognito for identity.
Use application database for authorization.
```

---

# Future Enterprise Enhancements

The architecture should support future enhancements such as:

## Identity Federation

- Enterprise SAML integration
- OIDC integration
- Azure Entra ID
- Okta
- Google Workspace

---

## SCIM Provisioning

Automatic enterprise user provisioning.

---

## Enhanced Authorization

Potential future integration:

- Amazon Verified Permissions
- Cedar policy engine

---

## Stronger Tenant Isolation

Future enterprise tenants may require:

| Isolation Model | Use Case |
|---|---|
| Shared DB + Shared Schema | Standard SaaS |
| Shared DB + Separate Schema | Mid-tier enterprise |
| Separate Database Per Tenant | Government/regulated workloads |

---

# Recommended AWS Services

| Capability | AWS Service |
|---|---|
| Authentication | Amazon Cognito |
| API Layer | API Gateway / FastAPI / Lambda |
| Application Compute | ECS / EKS / Lambda |
| Relational Database | Aurora PostgreSQL |
| Vector Search | OpenSearch / pgvector |
| Audit Logging | CloudWatch + CloudTrail |
| Secrets | AWS Secrets Manager |
| Infrastructure as Code | Terraform |

---

# Recommended Initial MVP Scope

For the initial MVP:

## Include

- Cognito authentication
- Email invitations
- Tenant membership model
- Role-based authorization
- Shared database
- Tenant admin portal
- Audit logging

## Defer Until Later

- SCIM
- SAML federation
- Per-tenant databases
- Advanced policy engines
- Custom tenant domains
- Complex ABAC

---

# Final Recommendation

Recommended approach:

```text
Use Amazon Cognito for authentication.
Use the application database for tenant membership and authorization.
Implement tenant-aware backend authorization checks.
Start with shared database + tenant_id isolation.
Design for future enterprise federation and stronger isolation.
```

This architecture provides:

- Fast MVP development
- Secure tenant separation
- Enterprise scalability
- Operational simplicity
- Future extensibility
