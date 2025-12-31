'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import Alert from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const { login, isLoading, error: authError } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError('');

    // Client-side validation
    if (!email || !password) {
      setLocalError('Please fill in all fields');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLocalError('Please enter a valid email address');
      return;
    }

    try {
      await login({ email, password });
    } catch (err) {
      // Error is already set by useAuth hook
      console.error('Login error:', err);
    }
  };

  const displayError = localError || authError;

  return (
    <Card className="shadow-xl">
      <CardHeader>
        <CardTitle className="text-2xl text-center">
          Sign In
        </CardTitle>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {displayError && (
            <Alert variant="error">
              {displayError}
            </Alert>
          )}

          <Input
            type="email"
            label="Email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading}
            autoComplete="email"
            required
          />

          <Input
            type="password"
            label="Password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            autoComplete="current-password"
            required
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>

          <div className="text-center text-sm">
            <span className="text-gray-400">Don't have an account? </span>
            <Link
              href="/register"
              className="text-primary-500 hover:text-primary-400 font-medium transition-colors"
            >
              Sign up
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
