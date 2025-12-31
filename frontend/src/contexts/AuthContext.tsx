'use client';

import React, { createContext, useContext, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthContextType,
  LoginResponse,
} from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider Component
 * Manages authentication state and provides auth methods to children
 *
 * Features:
 * - Auto-fetch current user on mount if token exists
 * - TanStack Query for user data caching
 * - localStorage token management
 * - Automatic 401 redirect (handled in api.ts interceptor)
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch current user data
  const {
    data: user = null,
    isLoading,
    error,
  } = useQuery<User | null>({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) return null;

      try {
        const response = await authAPI.me();
        return response.data;
      } catch (error) {
        // Token invalid or expired
        localStorage.removeItem('auth_token');
        return null;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await authAPI.login(credentials);
      return response.data as LoginResponse;
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
      router.push('/');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await authAPI.register(data);
      return response.data as LoginResponse;
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth', 'user'] });
      router.push('/');
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      try {
        await authAPI.logout();
      } catch (error) {
        // Ignore errors during logout
      }
    },
    onSuccess: () => {
      localStorage.removeItem('auth_token');
      queryClient.setQueryData(['auth', 'user'], null);
      queryClient.clear();
      router.push('/login');
    },
  });

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      await loginMutation.mutateAsync(credentials);
    },
    [loginMutation]
  );

  const register = useCallback(
    async (data: RegisterData) => {
      await registerMutation.mutateAsync(data);
    },
    [registerMutation]
  );

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth Hook
 * Access authentication state and methods
 *
 * @throws Error if used outside AuthProvider
 * @returns AuthContextType
 *
 * @example
 * const { user, isAuthenticated, login, logout } = useAuth();
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
