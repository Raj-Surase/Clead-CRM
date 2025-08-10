import { getHeaders, handleApiError } from './authUtils';
import { Lead, LeadEngagementGroupResponse, LeadLocationGroupResponse, LeadsResponse, LeadStatisticsOverview } from './api';
import { authApi } from './api';

class LeadApi {
  private baseUrl = 'http://127.0.0.1:8000/leads';

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return handleApiError(async () => {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: { ...getHeaders(), ...options.headers },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }

      return response.json();
    });
  }

  async getLeads(params: Record<string, any> = {}): Promise<LeadsResponse> {
    const userId = await authApi.getUserId();
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
    return this.request<LeadsResponse>(`/${userId}?${queryParams.toString()}`);
  }

  async createLead(data: Partial<Lead>): Promise<Lead> {
    const userId = await authApi.getUserId();
    return this.request<Lead>('', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async getLead(id: number): Promise<Lead> {
    const userId = await authApi.getUserId();
    return this.request<Lead>(`/${userId}/${id}`);
  }

  async updateLead(id: number, data: Partial<Lead>): Promise<Lead> {
    const userId = await authApi.getUserId();
    return this.request<Lead>(`/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async deleteLead(id: number): Promise<{ message: string }> {
    const userId = await authApi.getUserId();
    return this.request<{ message: string }>(`/${userId}/${id}`, {
      method: 'DELETE',
    });
  }

  async getLeadStatisticsOverview(): Promise<LeadStatisticsOverview> {
    const userId = await authApi.getUserId();
    return this.request<LeadStatisticsOverview>(`/user/${userId}/statistics-overview`);
  }

  async groupLeadsByLocation(params: Record<string, any> = {}): Promise<LeadLocationGroupResponse> {
    const userId = await authApi.getUserId();
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
    return this.request<LeadLocationGroupResponse>(`/user/${userId}/group/location?${queryParams.toString()}`);
  }

  async groupLeadsByEngagement(params: Record<string, any> = {}): Promise<LeadEngagementGroupResponse> {
    const userId = await authApi.getUserId();
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });
    return this.request<LeadEngagementGroupResponse>(`/user/${userId}/group/engagement?${queryParams.toString()}`);
  }
}

export const leadApi = new LeadApi();