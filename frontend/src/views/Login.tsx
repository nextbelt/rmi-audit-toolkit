import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';
import { authAPI } from '../api/client';
import { Input, Button } from '../components';

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
      /* Error already in store */
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
      if (r.debug_token) setDebugToken(r.debug_token);
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

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg)',
        padding: 24,
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: 460,
          width: '100%',
          padding: 36,
          boxShadow: '0 18px 60px rgba(27, 31, 29, 0.10)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div
            className="brand-mark"
            style={{ width: 44, height: 44, fontSize: 15, margin: '0 auto 16px' }}
          >
            RMI
          </div>
          <h1
            className="serif"
            style={{ fontSize: 36, margin: 0, color: 'var(--ink)' }}
          >
            <em>RMI</em> Audit Toolkit
          </h1>
          <p
            className="mono"
            style={{ color: 'var(--muted)', fontSize: 11, marginTop: 8, letterSpacing: '0.06em' }}
          >
            by NextBelt LLC
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
                  top: 34,
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 12,
                  color: 'var(--muted)',
                  padding: 4,
                  fontFamily: 'inherit',
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            {error && (
              <div
                style={{
                  padding: '12px 14px',
                  background: 'rgba(194, 83, 60, 0.06)',
                  border: '1px solid rgba(194, 83, 60, 0.30)',
                  borderRadius: 8,
                  color: 'var(--danger)',
                  fontSize: 12.5,
                  marginBottom: 16,
                }}
              >
                {error}
              </div>
            )}

            {resetStatus && (
              <div
                style={{
                  padding: 12,
                  background: 'var(--accent-soft)',
                  border: '1px solid rgba(14, 110, 98, 0.30)',
                  borderRadius: 8,
                  color: 'var(--accent)',
                  fontSize: 12.5,
                  marginBottom: 16,
                }}
              >
                {resetStatus}
              </div>
            )}

            <Button type="submit" fullWidth loading={isLoading} disabled={isLoading} size="lg">
              Sign In
            </Button>

            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                type="button"
                onClick={() => {
                  setMode('reset_request');
                  setResetStatus(null);
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--accent)',
                  fontSize: 12.5,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                Forgot Password?
              </button>
            </div>
          </form>
        )}

        {mode === 'reset_request' && (
          <form onSubmit={handleResetRequest}>
            <h2 className="serif" style={{ fontSize: 24, marginBottom: 10, color: 'var(--ink)' }}>
              Reset Password
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: 12.5, marginBottom: 22 }}>
              Enter your email. We will issue a reset token; an administrator can hand it to you,
              or it will be in the server log.
            </p>

            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            {resetStatus && (
              <div style={{ marginBottom: 16, fontSize: 12.5, color: 'var(--muted)' }}>
                {resetStatus}
              </div>
            )}

            <div style={{ display: 'flex', gap: 12 }}>
              <Button type="submit" fullWidth>
                Request Token
              </Button>
              <Button type="button" variant="outline" fullWidth onClick={() => setMode('login')}>
                Cancel
              </Button>
            </div>
          </form>
        )}

        {mode === 'reset_confirm' && (
          <form onSubmit={handleResetConfirm}>
            <h2 className="serif" style={{ fontSize: 24, marginBottom: 10, color: 'var(--ink)' }}>
              Set New Password
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: 12.5, marginBottom: 16 }}>
              {resetStatus || 'Paste the reset token and choose a new password (minimum 12 characters).'}
            </p>

            {debugToken && (
              <div
                className="mono"
                style={{
                  padding: 12,
                  background: 'var(--accent-soft)',
                  border: '1px solid rgba(14, 110, 98, 0.30)',
                  borderRadius: 8,
                  marginBottom: 16,
                  fontSize: 11.5,
                  wordBreak: 'break-all',
                  color: 'var(--accent)',
                }}
              >
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
              <Button type="submit" fullWidth>
                Update Password
              </Button>
              <Button type="button" variant="outline" fullWidth onClick={() => setMode('login')}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
