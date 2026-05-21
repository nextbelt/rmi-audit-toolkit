import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';
import { authAPI } from '../api/client';
import { Input, Button, Card } from '../components';

type Mode = 'login' | 'reset_request' | 'reset_confirm';

export const Login: React.FC = () => {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [resetToken, setResetToken] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetStatus, setResetStatus] = useState<string | null>(null);
  const [debugToken, setDebugToken] = useState<string | null>(null);
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch {
      // Error already in store
    }
  };

  const handleResetRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetStatus(null);
    setDebugToken(null);
    try {
      const r = await authAPI.requestPasswordReset(email);
      setResetStatus(
        'If that email is registered, a password reset token has been issued. ' +
          'Check the system log (production) or paste the debug token below (development) to set a new password.',
      );
      if (r.debug_token) {
        setDebugToken(r.debug_token);
      }
      setMode('reset_confirm');
    } catch {
      setResetStatus('Could not start password reset. Try again.');
    }
  };

  const handleResetConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetStatus(null);
    try {
      await authAPI.confirmPasswordReset(resetToken, resetNewPassword);
      setResetStatus('Password updated. Sign in below with the new password.');
      setMode('login');
      setPassword('');
      setResetToken('');
      setResetNewPassword('');
      setDebugToken(null);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Token invalid or expired.';
      setResetStatus(detail);
    }
  };

  const box: React.CSSProperties = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#FAFAFA',
    padding: '24px',
  };

  return (
    <div style={box}>
      <Card style={{ maxWidth: 460, width: '100%', boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <h1 style={{ fontSize: '1.75rem', marginBottom: 8, fontWeight: 600, color: '#1A1A1A' }}>
            RMI Audit Toolkit
          </h1>
          <p style={{ color: '#666', fontSize: '0.8125rem', fontFamily: "'IBM Plex Mono', monospace", letterSpacing: '0.04em' }}>
            NextBelt LLC
          </p>
        </div>

        {mode === 'login' && (
          <form onSubmit={handleLogin}>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              placeholder="you@example.com"
            />

            <div style={{ position: 'relative' }}>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: 38,
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  color: '#666',
                  padding: 4,
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            {error && (
              <div style={{
                padding: '12px 16px',
                background: 'rgba(197, 48, 48, 0.06)',
                border: '1px solid rgba(197, 48, 48, 0.25)',
                borderRadius: 6,
                color: '#C53030',
                fontSize: '0.8125rem',
                marginBottom: 24,
              }}>
                {error}
              </div>
            )}

            {resetStatus && (
              <div style={{
                padding: 12,
                background: 'rgba(15, 111, 111, 0.06)',
                border: '1px solid rgba(15, 111, 111, 0.25)',
                borderRadius: 6,
                color: '#0F6F6F',
                fontSize: '0.8125rem',
                marginBottom: 16,
              }}>
                {resetStatus}
              </div>
            )}

            <Button type="submit" fullWidth loading={isLoading} disabled={isLoading}>
              Sign In
            </Button>

            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                type="button"
                onClick={() => { setMode('reset_request'); setResetStatus(null); }}
                style={{
                  background: 'transparent', border: 'none', color: '#0F6F6F',
                  fontSize: '0.8125rem', cursor: 'pointer',
                }}
              >
                Forgot Password?
              </button>
            </div>
          </form>
        )}

        {mode === 'reset_request' && (
          <form onSubmit={handleResetRequest}>
            <h2 style={{ fontSize: '1.125rem', marginBottom: 12, color: '#1A1A1A' }}>Reset Password</h2>
            <p style={{ color: '#666', fontSize: '0.8125rem', marginBottom: 24 }}>
              Enter your email. We will issue a reset token; an administrator can hand it to you, or it will be in the server log.
            </p>

            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            {resetStatus && (
              <div style={{ marginBottom: 16, fontSize: '0.8125rem', color: '#666' }}>{resetStatus}</div>
            )}

            <div style={{ display: 'flex', gap: 12 }}>
              <Button type="submit" fullWidth>Request Token</Button>
              <Button type="button" variant="outline" fullWidth onClick={() => setMode('login')}>Cancel</Button>
            </div>
          </form>
        )}

        {mode === 'reset_confirm' && (
          <form onSubmit={handleResetConfirm}>
            <h2 style={{ fontSize: '1.125rem', marginBottom: 12, color: '#1A1A1A' }}>Set New Password</h2>
            <p style={{ color: '#666', fontSize: '0.8125rem', marginBottom: 16 }}>
              {resetStatus || 'Paste the reset token and choose a new password (minimum 12 characters).'}
            </p>

            {debugToken && (
              <div style={{
                padding: 12,
                background: 'rgba(15, 111, 111, 0.06)',
                border: '1px solid rgba(15, 111, 111, 0.25)',
                borderRadius: 6,
                marginBottom: 16,
                fontSize: '0.75rem',
                fontFamily: "'IBM Plex Mono', monospace",
                wordBreak: 'break-all',
              }}>
                <strong>Dev-mode token:</strong> {debugToken}
              </div>
            )}

            <Input
              label="Reset Token"
              type="text"
              value={resetToken}
              onChange={(e) => setResetToken(e.target.value)}
              required
            />
            <Input
              label="New Password (min 12 characters)"
              type="password"
              value={resetNewPassword}
              onChange={(e) => setResetNewPassword(e.target.value)}
              required
            />

            <div style={{ display: 'flex', gap: 12 }}>
              <Button type="submit" fullWidth>Update Password</Button>
              <Button type="button" variant="outline" fullWidth onClick={() => setMode('login')}>Cancel</Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};
