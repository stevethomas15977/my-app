# HVAC Proposal and Submittal Automation

HVAC Proposal and Submittal Automation is a SaaS application for water-side HVAC manufacturer sales representatives. The product is intended to automate the proposal-through-submittal workflow by extracting project requirements from bid documents, supporting model selection, and generating review-ready proposal or submittal packages.

The initial MVP focuses on proposal-stage automation for one water-side equipment category. Submittal generation and deeper compliance workflows are planned for later pilot phases.

## Problem

Commercial HVAC equipment proposals and submittals are built from information scattered across construction documents:

- Mechanical schedules and M-sheets
- General notes and keynotes
- Written specifications and project manuals
- Manufacturer catalog data
- Proprietary manufacturer selection software

Manufacturer reps manually read these documents, select compliant equipment, and assemble proposal or submittal packages. This work is high-volume, detail-heavy, and expensive to perform manually.

## Product Direction

The product is organized around three functional layers:

| Layer | Purpose |
|---|---|
| Qualification | Screen bid opportunities, identify applicable equipment scope, and confirm whether the rep should pursue the bid. |
| Spec Matching / Model Selection | Extract equipment requirements and compare model recommendations against manufacturer catalog data and the rep's selection-program output. |
| Output Generation | Produce proposal or submittal documents from selected models, project metadata, and supporting documentation. |

The v0.1 MVP targets the proposal stage first because proposals happen on every pursued bid, while submittals only happen after award.

## MVP Scope

Planned v0.1 scope:

- Proposal-stage workflow only
- One initial water-side equipment category
- PDF bid document ingestion
- Applicable-equipment screening
- Requirement extraction from schedules, notes, and specifications
- Tool-path model recommendation against customer-provided catalog data
- Human-path selection-program output capture for comparison
- Baseline proposal document generation
- Multi-tenant architecture from the start
- Audit logging for LLM calls, user decisions, document versions, and model-selection comparisons
- AWS-hosted web application
- SSO-ready authentication

Explicitly deferred from v0.1:

- Submittal-specific workflows
- Multi-equipment-category support
- Direct manufacturer selection-program integration
- Procore, Bluebeam, BIM, Revit, or ACC integrations
- Mobile apps
- CMMC Level 2 certification

## Architecture Principles

The project follows these working defaults:

- LLMs perform extraction and generation; deterministic code performs matching and compliance checks.
- Structured data is the source of truth between pipeline stages.
- Every claim should cite its source document, page, and supporting span.
- Trust-critical outputs require human verification.
- Tenant data must be logically isolated from the first commit.
- Audit logs are a product feature, not just operational telemetry.
- Compliance and selection rules should live in versioned policy files where possible.

## Authentication and Authorization

Authentication uses Amazon Cognito. Authorization is expected to live in the application database and backend logic.

Current Terraform provisions the Cognito foundation:

- Cognito User Pool
- Cognito User Pool Client
- Email verification
- Password policy
- OAuth scopes for `email`, `openid`, and `profile`
- Optional `custom:tenant_id` metadata for onboarding support

Tenant membership, roles, invitations, and fine-grained authorization should be implemented in the application database rather than relying on Cognito groups or a single Cognito tenant attribute.

See [documentation/authentication-authorization.md](documentation/authentication-authorization.md) for the detailed recommendation.

## Repository Structure

```text
.
|-- backend/
|   |-- main.py
|   |-- pyproject.toml
|   `-- terraform/
|       |-- cognito.tf
|       |-- output.tf
|       |-- provider.tf
|       `-- envs/
|           |-- dev/backend.hcl
|           `-- prod/backend.hcl
|-- documentation/
|   |-- HVAC_Proposal_Submittal_v0.3_Scope.docx
|   `-- authentication-authorization.md
|-- frontend/
|   |-- angular.json
|   |-- package.json
|   `-- src/
`-- .github/workflows/
    `-- terraform.yaml
```

## Current Implementation State

This repository is in an early foundation stage.

Implemented:

- Angular frontend scaffold
- Python backend scaffold
- Terraform root for AWS infrastructure
- Cognito User Pool and User Pool Client Terraform
- Environment-specific Terraform backend configuration
- Manual GitHub Actions workflow for Terraform deployment
- Authentication and authorization architecture notes

Not yet implemented:

- Bid document ingestion
- Requirement extraction pipeline
- Catalog ingestion
- Model matching engine
- Proposal generation
- Tenant database model
- Audit logging pipeline
- Application API endpoints

## Local Development

### Frontend

```bash
cd frontend
npm install
npm start
```

The Angular dev server normally runs at:

```text
http://localhost:4200
```

### Backend

The backend currently contains a minimal Python scaffold.

```bash
cd backend
uv sync
uv run python main.py
```

## Terraform

Terraform is rooted at:

```text
backend/terraform
```

Initialize against the dev backend:

```bash
cd backend/terraform
terraform init -backend-config=envs/dev/backend.hcl
terraform plan
```

Initialize against the prod backend:

```bash
cd backend/terraform
terraform init -reconfigure -backend-config=envs/prod/backend.hcl
terraform plan
```

The backend `.hcl` files configure where Terraform state is stored. Runtime infrastructure settings should go in Terraform variables and `.tfvars` files when they are needed.

## GitHub Actions

Infrastructure can be deployed manually through:

```text
.github/workflows/terraform.yaml
```

The workflow accepts an environment choice (`dev` or `prod`), configures AWS credentials from GitHub secrets, runs `terraform init`, then runs `terraform plan` and `terraform apply`.

Expected repository variables and secrets:

- `AWS_DEFAULT_REGION`
- `DEV_AWS_ACCESS_KEY_ID`
- `DEV_AWS_SECRET_ACCESS_KEY`
- `PROD_AWS_ACCESS_KEY_ID`
- `PROD_AWS_SECRET_ACCESS_KEY`

## Source Documents

The product scope is based on:

```text
documentation/HVAC_Proposal_Submittal_v0.3_Scope.docx
```

That document is the living product/technical scope. This README summarizes the repo and current implementation direction.
