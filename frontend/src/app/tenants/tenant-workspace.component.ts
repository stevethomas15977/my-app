import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { TenantApiService } from '../core/tenant-api.service';
import {
  Tenant,
  TenantDetail,
  TenantInvitation,
  TenantMember,
  TenantRole,
} from '../core/tenant.models';

@Component({
  selector: 'app-tenant-workspace',
  imports: [ReactiveFormsModule],
  templateUrl: './tenant-workspace.component.html',
  styleUrl: './tenant-workspace.component.css',
})
export class TenantWorkspaceComponent implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly tenantApi = inject(TenantApiService);

  readonly roles: TenantRole[] = ['TENANT_ADMIN', 'TENANT_USER', 'TENANT_READ_ONLY'];

  readonly tenants = signal<Tenant[]>([]);
  readonly selectedTenant = signal<Tenant | null>(null);
  readonly members = signal<TenantMember[]>([]);
  readonly invitations = signal<TenantInvitation[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  readonly pendingInvitations = computed(() =>
    this.invitations().filter((invitation) => invitation.status === 'PENDING'),
  );

  readonly tenantForm = this.formBuilder.nonNullable.group({
    tenant_name: ['', [Validators.required, Validators.minLength(2)]],
    admin_email: ['owner@example.com', [Validators.required, Validators.email]],
    display_name: ['Tenant Owner', [Validators.required]],
  });

  readonly inviteForm = this.formBuilder.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    role: ['TENANT_USER' as TenantRole, [Validators.required]],
  });

  readonly acceptInvitationForm = this.formBuilder.nonNullable.group({
    token: ['', [Validators.required]],
    display_name: ['Invited User', [Validators.required]],
  });

  ngOnInit(): void {
    this.loadTenants();
  }

  loadTenants(): void {
    this.loading.set(true);
    this.error.set(null);

    this.tenantApi.listTenants().subscribe({
      next: ({ tenants }) => {
        this.tenants.set(tenants);
        this.loading.set(false);

        if (tenants.length > 0 && !this.selectedTenant()) {
          this.selectTenant(tenants[0]);
        }
      },
      error: () => {
        this.loading.set(false);
        this.error.set('Tenant API is unavailable. Start the backend on port 8000.');
      },
    });
  }

  createTenant(): void {
    if (this.tenantForm.invalid) {
      this.tenantForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);

    this.tenantApi.createTenant(this.tenantForm.getRawValue()).subscribe({
      next: ({ tenant, invitation }) => {
        this.tenants.set([...this.tenants(), tenant]);
        this.selectedTenant.set(tenant);
        this.invitations.set([invitation]);
        this.members.set([]);
        this.loading.set(false);
        this.success.set('Tenant created. Accept the owner invitation to activate membership.');
      },
      error: ({ error }) => {
        this.loading.set(false);
        this.error.set(error?.error ?? 'Unable to create tenant.');
      },
    });
  }

  selectTenant(tenant: Tenant): void {
    this.loading.set(true);
    this.error.set(null);
    this.selectedTenant.set(tenant);

    this.tenantApi.getTenant(tenant.tenant_id).subscribe({
      next: (detail) => this.setTenantDetail(detail),
      error: ({ error }) => {
        this.loading.set(false);
        this.members.set([]);
        this.invitations.set([]);
        this.error.set(error?.error ?? 'Unable to load tenant detail.');
      },
    });
  }

  inviteUser(): void {
    const tenant = this.selectedTenant();
    if (!tenant) {
      this.error.set('Select a tenant first.');
      return;
    }
    if (this.inviteForm.invalid) {
      this.inviteForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);

    this.tenantApi.inviteUser(tenant.tenant_id, this.inviteForm.getRawValue()).subscribe({
      next: (invitation) => {
        this.invitations.set([invitation, ...this.invitations()]);
        this.inviteForm.reset({ email: '', role: 'TENANT_USER' });
        this.loading.set(false);
        this.success.set('Invitation created.');
      },
      error: ({ error }) => {
        this.loading.set(false);
        this.error.set(error?.error ?? 'Unable to create invitation.');
      },
    });
  }

  acceptInvitation(): void {
    if (this.acceptInvitationForm.invalid) {
      this.acceptInvitationForm.markAllAsTouched();
      return;
    }

    const { token, display_name } = this.acceptInvitationForm.getRawValue();
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);

    this.tenantApi.acceptInvitation(token, display_name).subscribe({
      next: (detail) => {
        this.setTenantDetail(detail);
        this.acceptInvitationForm.reset({ token: '', display_name });
        this.success.set('Invitation accepted.');
        this.loadTenants();
      },
      error: ({ error }) => {
        this.loading.set(false);
        this.error.set(error?.error ?? 'Unable to accept invitation.');
      },
    });
  }

  private setTenantDetail(detail: TenantDetail): void {
    this.selectedTenant.set(detail.tenant);
    this.members.set(detail.members);
    this.invitations.set(detail.invitations);
    this.loading.set(false);
  }
}
