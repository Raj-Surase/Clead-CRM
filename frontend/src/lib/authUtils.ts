import { authApi } from './authApi';

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: any;
}

export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const getHeaders = (): Record<string, string> => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export const refreshToken = async (): Promise<boolean> => {
  const refresh_token = localStorage.getItem('refresh_token');
  if (!refresh_token) {
    return false;
  }

  try {
    const response = await fetch('http://127.0.0.2:8000/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token }),
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data: AuthResponse = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return true;
  } catch (error) {
    console.error('Token refresh error:', error);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Optionally redirect to login page
    window.location.href = '/login';
    return false;
  }
};

export const handleApiError = async <T>(
  request: () => Promise<T>,
  retryCount: number = 1
): Promise<T> => {
  try {
    return await request();
  } catch (error: any) {
    if (error.message.includes('401') && retryCount > 0) {
      const refreshed = await refreshToken();
      if (refreshed) {
        return await request(); // Retry the request with the new token
      }
    }
    throw error;
  }
};