import { getHeaders, handleApiError, AuthResponse, getToken } from './authUtils';

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login: string;
  full_name: string;
  is_onboarding_complete: boolean;
}

export class Profile {
  first_name: string;
  last_name: string;
  phone: string;
  timezone: string;

  constructor(data: Partial<Profile> = {}) {
    this.first_name = data.first_name || '';
    this.last_name = data.last_name || '';
    this.phone = data.phone;
    this.timezone = data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  }
}

export class Company {
  company_name: string;
  company_size: string;
  industry: string;
  website?: string;

  constructor(data: Partial<Company> = {}) {
    this.company_name = data.company_name || '';
    this.company_size = data.company_size || '';
    this.industry = data.industry || '';
    this.website = data.website;
  }
}

export interface OnboardingStatus {
  is_complete: boolean;
  steps_completed: {
    email_verified: boolean;
    personal_info: boolean;
    company_info: boolean;
  };
  next_step: string;
}

const API_BASE_URL = 'http://127.0.0.1:8000';

// Module-level cache for user id
let cachedUserId: string | null = null;

class AuthAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requireAuth: boolean = true
  ): Promise<T> {
    const headers = requireAuth ? getHeaders() : { 'Content-Type': 'application/json' };
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: { ...headers, ...options.headers },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  async register(email: string, password: string, confirm_password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, confirm_password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const data = await handleApiError(() =>
      this.request<AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }, false)
    );
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }

  async logout() {
    const refresh_token = localStorage.getItem('refresh_token');
    const access_token = localStorage.getItem('access_token');
    if (!refresh_token || !access_token) return;

    await handleApiError(() =>
      this.request('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token, access_token }),
      }, true)
    );

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    cachedUserId = null; // Invalidate user id cache on logout
  }

  async getCurrentUser(): Promise<User> {
    return handleApiError(() => this.request<User>('/auth/me'));
  }

  async forgotPassword(email: string) {
    return handleApiError(() =>
      this.request('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }, false)
    );
  }

  async resetPassword(token: string, new_password: string, confirm_password: string) {
    return handleApiError(() =>
      this.request('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password, confirm_password }),
      }, false)
    );
  }

  async getProfile() {
    return handleApiError(() => this.request('/auth/user/profile'));
  }

  async updateProfile(data: any) {
    return handleApiError(() =>
      this.request('/auth/user/profile', {
        method: 'PUT',
        body: JSON.stringify(data),
      })
    );
  }

  async getCompany() {
    return handleApiError(() => this.request('/auth/user/company'));
  }

  async updateCompany(data: any) {
    return handleApiError(() =>
      this.request('/auth/user/company', {
        method: 'PUT',
        body: JSON.stringify(data),
      })
    );
  }

  async getOnboardingStatus() {
    return handleApiError(() => this.request('/auth/onboarding/status'));
  }

  async updatePersonalInfo(data: any) {
    return handleApiError(() =>
      this.request('/auth/onboarding/personal', {
        method: 'PUT',
        body: JSON.stringify(data),
      })
    );
  }

  async updateCompanyInfo(data: any) {
    return handleApiError(() =>
      this.request('/auth/onboarding/company', {
        method: 'PUT',
        body: JSON.stringify(data),
      })
    );
  }

  async completeOnboarding() {
    return handleApiError(() =>
      this.request('/auth/onboarding/complete', {
        method: 'POST',
      })
    );
  }

  isAuthenticated(): boolean {
    return !!getToken();
  }

  async getUserId(): Promise<string> {
    if (cachedUserId) {
      return cachedUserId;
    }
    const user = await this.getCurrentUser();
    cachedUserId = user.id;
    return user.id;
  }

  async refreshToken(): Promise<void> {
    const refresh_token = localStorage.getItem('refresh_token');
    if (!refresh_token) {
      throw new Error('No refresh token found');
    }
  
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token }),
    });
  
    if (!response.ok) {
      cachedUserId = null; // Invalidate user id cache if refresh fails
      throw new Error('Failed to refresh token');
    }
  
    const data: AuthResponse = await response.json();
    localStorage.setItem('access_token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }
  }
  
}

export const authApi = new AuthAPI();