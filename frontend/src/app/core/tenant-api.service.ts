import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import {
  CreateInvitationRequest,
  CreateTenantRequest,
  CreateTenantResponse,
  Tenant,
  TenantDetail,
  TenantInvitation,
} from './tenant.models';

interface TenantListResponse {
  tenants: Tenant[];
}

interface InvitationListResponse {
  invitations: TenantInvitation[];
}

@Injectable({ providedIn: 'root' })
export class TenantApiService {
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  readonly activeTenantId = signal<string | null>(null);

  constructor(private readonly http: HttpClient) {}

  listTenants(): Observable<TenantListResponse> {
    return this.http.get<TenantListResponse>(`${this.apiBaseUrl}/tenants`, {
      headers: this.headers(),
    });
  }

  createTenant(request: CreateTenantRequest): Observable<CreateTenantResponse> {
    return this.http.post<CreateTenantResponse>(`${this.apiBaseUrl}/tenants`, request, {
      headers: this.headers(),
    });
  }

  getTenant(tenantId: string): Observable<TenantDetail> {
    return this.http.get<TenantDetail>(`${this.apiBaseUrl}/tenants/${tenantId}`, {
      headers: this.headers(),
    });
  }

  inviteUser(tenantId: string, request: CreateInvitationRequest): Observable<TenantInvitation> {
    return this.http.post<TenantInvitation>(
      `${this.apiBaseUrl}/tenants/${tenantId}/invitations`,
      request,
      { headers: this.headers() },
    );
  }

  listInvitations(tenantId: string): Observable<InvitationListResponse> {
    return this.http.get<InvitationListResponse>(
      `${this.apiBaseUrl}/tenants/${tenantId}/invitations`,
      { headers: this.headers() },
    );
  }

  acceptInvitation(token: string, displayName: string): Observable<TenantDetail> {
    return this.http
      .post<TenantDetail>(
        `${this.apiBaseUrl}/invitations/accept`,
        { token, display_name: displayName },
        { headers: this.headers() },
      )
      .pipe(tap((response) => this.activeTenantId.set(response.tenant.tenant_id)));
  }

  private headers(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Cognito-Sub': 'local-cognito-sub',
      'X-User-Email': 'owner@example.com',
    });
  }
}
