import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../lib/authApi';

interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login: string;
  full_name: string;
  is_onboarding_complete: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    try {
      if (authApi.isAuthenticated()) {
        try {
          // Try to get user with current access token
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (error: any) {
          // If error is due to expired token, try to refresh
          if (error?.response?.status === 401 || error?.message?.toLowerCase().includes('token')) {
            // Try to refresh token
            try {
              await authApi.refreshToken();
              // Retry getting user
              const userData = await authApi.getCurrentUser();
              setUser(userData);
            } catch (refreshError) {
              // Refresh failed, log out
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              setUser(null);
            }
          } else {
            throw error;
          }
        }
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    await authApi.login(email, password);
    await refreshUser(); // Update user state after login
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};