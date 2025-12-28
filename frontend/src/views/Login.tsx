import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';
import { Input, Button, Card } from '../components';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetSent, setResetSent] = useState(false);
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      // Error handled by store
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Send email to nextbelt@next-belt.com with reset request
      const emailBody = `Password reset requested for: ${resetEmail}`;
      window.location.href = `mailto:nextbelt@next-belt.com?subject=RMI Audit Toolkit - Password Reset Request&body=${encodeURIComponent(emailBody)}`;
      setResetSent(true);
      setTimeout(() => {
        setShowForgotPassword(false);
        setResetSent(false);
        setResetEmail('');
      }, 3000);
    } catch (err) {
      console.error('Failed to send reset email');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#FAFAF8',
      padding: '24px',
    }}>
      <Card style={{ maxWidth: '450px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '8px', fontWeight: 600 }}>
            RMI Audit Toolkit
          </h1>
          <p style={{ color: '#5C5C5C', fontSize: '0.875rem', fontFamily: "'IBM Plex Mono', monospace" }}>
            NextBelt LLC
          </p>
        </div>

        {!showForgotPassword ? (
          <form onSubmit={handleSubmit}>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              autoComplete="email"
              required
            />

            <div style={{ position: 'relative' }}>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '38px',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '1.25rem',
                  color: '#5C5C5C',
                  padding: '4px',
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>

            {error && (
              <div style={{
                padding: '12px 16px',
                background: 'rgba(155, 44, 44, 0.1)',
                border: '1px solid #9B2C2C',
                borderRadius: '4px',
                color: '#9B2C2C',
                fontSize: '0.875rem',
                marginBottom: '24px',
              }}>
                {error}
              </div>
            )}

            <Button
              type="submit"
              fullWidth
              loading={isLoading}
              disabled={isLoading}
            >
              Sign In
            </Button>

            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                type="button"
                onClick={() => setShowForgotPassword(true)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#0D4F4F',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  fontFamily: "'Space Grotesk', sans-serif",
                }}
              >
                Forgot Password?
              </button>
            </div>
          </form>
        ) : (
          <div>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '16px' }}>Reset Password</h2>
            <p style={{ color: '#5C5C5C', fontSize: '0.875rem', marginBottom: '24px' }}>
              Enter your email address and we'll send you instructions to reset your password.
            </p>

            {resetSent ? (
              <div style={{
                padding: '16px',
                background: 'rgba(45, 106, 79, 0.1)',
                border: '1px solid #2D6A4F',
                borderRadius: '4px',
                color: '#2D6A4F',
                fontSize: '0.875rem',
                marginBottom: '24px',
              }}>
                ✓ Reset request sent! Check your email.
              </div>
            ) : (
              <form onSubmit={handleForgotPassword}>
                <Input
                  label="Email"
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                />

                <div style={{ display: 'flex', gap: '12px' }}>
                  <Button type="submit" fullWidth>
                    Send Reset Link
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    fullWidth
                    onClick={() => setShowForgotPassword(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
