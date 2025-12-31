'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import Alert from '@/components/ui/Alert';
import { useAuth } from '@/hooks/useAuth';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState('');

  const { register, isLoading, error: authError } = useAuth();

  const validateForm = (): boolean => {
    // Check if all fields are filled
    if (!email || !username || !password || !confirmPassword) {
      setLocalError('Please fill in all fields');
      return false;
    }

    // Validate email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setLocalError('Please enter a valid email address');
      return false;
    }

    // Validate username length
    if (username.length < 3) {
      setLocalError('Username must be at least 3 characters long');
      return false;
    }

    // Validate username format (alphanumeric and underscores only)
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setLocalError('Username can only contain letters, numbers, and underscores');
      return false;
    }

    // Validate password length
    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters long');
      return false;
    }

    // Check if passwords match
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalError('');

    if (!validateForm()) {
      return;
    }

    try {
      await register({ email, username, password });
    } catch (err) {
      // Error is already set by useAuth hook
      console.error('Registration error:', err);
    }
  };

  const displayError = localError || authError;

  return (
    <Card className="shadow-xl">
      <CardHeader>
        <CardTitle className="text-2xl text-center">
          Create Account
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
            type="text"
            label="Username"
            placeholder="Choose a username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            autoComplete="username"
            required
          />

          <Input
            type="password"
            label="Password"
            placeholder="Create a password (min. 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            autoComplete="new-password"
            required
          />

          <Input
            type="password"
            label="Confirm Password"
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isLoading}
            autoComplete="new-password"
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
            {isLoading ? 'Creating account...' : 'Create Account'}
          </Button>

          <div className="text-center text-sm">
            <span className="text-gray-400">Already have an account? </span>
            <Link
              href="/login"
              className="text-primary-500 hover:text-primary-400 font-medium transition-colors"
            >
              Sign in
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
