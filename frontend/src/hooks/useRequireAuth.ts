'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

/**
 * useRequireAuth Hook
 * Redirects to /login if user is not authenticated
 *
 * Features:
 * - Automatic redirect on mount if not authenticated
 * - Waits for loading state to complete before redirecting
 * - Returns auth state for conditional rendering
 *
 * @returns {{ isAuthenticated: boolean, isLoading: boolean }}
 *
 * @example
 * function ProtectedPage() {
 *   const { isAuthenticated, isLoading } = useRequireAuth();
 *
 *   if (isLoading) return <LoadingSpinner />;
 *   if (!isAuthenticated) return null; // Will redirect
 *
 *   return <div>Protected content</div>;
 * }
 */
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading };
}
