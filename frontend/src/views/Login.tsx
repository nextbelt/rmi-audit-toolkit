import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';
import { supabase, ALLOWED_DOMAIN, isAllowedEmail } from '../api/supabase';
import { Input, Button } from '../components';

type Mode = 'login' | 'signup' | 'reset_request' | 'update_password';

export const Login: React.FC = () => {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { login, signup, requestPasswordReset, updatePassword, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  // When the user returns from a password-reset email, Supabase emits
  // PASSWORD_RECOVERY — switch to the "set new password" screen.
  useEffect(() => {
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') {
        setMode('update_password');
        setNotice('Choose a new password to finish resetting your account.');
      }
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const switchMode = (m: Mode) => {
    clearError();
    setNotice(null);
    setMode(m);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch {
      /* error is in the store */
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);
    try {
      const { needsConfirmation } = await signup(email, password);
      if (needsConfirmation) {
        setNotice('Account created — check your email to confirm, then sign in.');
        setMode('login');
      } else {
        navigate('/dashboard');
      }
    } catch {
      /* error is in the store */
    }
  };

  const handleResetRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setBusy(true);
    setNotice(null);
    try {
      await requestPasswordReset(email);
      setNotice(`If ${email} has an account, a reset link is on its way. Open it to set a new password.`);
    } catch (err: any) {
      setNotice(err?.message || 'Could not send the reset email. Try again.');
    } finally {
      setBusy(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setBusy(true);
    try {
      await updatePassword(password);
      setNotice('Password updated. Redirecting…');
      setTimeout(() => navigate('/dashboard'), 600);
    } catch (err: any) {
      setNotice(err?.message || 'Could not update password.');
    } finally {
      setBusy(false);
    }
  };

  const domainOk = !email || isAllowedEmail(email);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)', padding: 24 }}>
      <div className="card" style={{ maxWidth: 460, width: '100%', padding: 36, boxShadow: '0 18px 60px rgba(27, 31, 29, 0.10)' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div className="brand-mark" style={{ width: 44, height: 44, fontSize: 15, margin: '0 auto 16px' }}>RMI</div>
          <h1 className="serif" style={{ fontSize: 36, margin: 0, color: 'var(--ink)' }}><em>RMI</em> Audit Toolkit</h1>
          <p className="mono" style={{ color: 'var(--muted)', fontSize: 11, marginTop: 8, letterSpacing: '0.06em' }}>by NextBelt LLC</p>
        </div>

        {notice && (
          <div style={{ padding: 12, background: 'var(--accent-soft)', border: '1px solid rgba(14, 110, 98, 0.30)', borderRadius: 8, color: 'var(--accent)', fontSize: 12.5, marginBottom: 16 }}>
            {notice}
          </div>
        )}
        {error && (
          <div role="alert" style={{ padding: '12px 14px', background: 'rgba(194, 83, 60, 0.06)', border: '1px solid rgba(194, 83, 60, 0.30)', borderRadius: 8, color: 'var(--danger)', fontSize: 12.5, marginBottom: 16 }}>
            {error}
          </div>
        )}

        {(mode === 'login' || mode === 'signup') && (
          <form onSubmit={mode === 'login' ? handleLogin : handleSignup}>
            <h2 className="serif" style={{ fontSize: 22, marginBottom: 14, color: 'var(--ink)' }}>
              {mode === 'login' ? 'Sign in' : 'Create your account'}
            </h2>
            <Input
              label="Work email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              placeholder={`you@${ALLOWED_DOMAIN}`}
              error={!domainOk ? `Use your @${ALLOWED_DOMAIN} email` : undefined}
            />
            <div style={{ position: 'relative' }}>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                minLength={mode === 'signup' ? 8 : undefined}
              />
              <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}
                style={{ position: 'absolute', right: 12, top: 34, background: 'transparent', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--muted)', padding: 4, fontFamily: 'inherit' }}>
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            <Button type="submit" fullWidth loading={busy} disabled={!domainOk} size="lg">
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </Button>

            <div className="row" style={{ justifyContent: 'space-between', marginTop: 16 }}>
              <button type="button" onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}
                style={{ background: 'transparent', border: 'none', color: 'var(--accent)', fontSize: 12.5, cursor: 'pointer', fontFamily: 'inherit' }}>
                {mode === 'login' ? 'Create an account' : 'Have an account? Sign in'}
              </button>
              {mode === 'login' && (
                <button type="button" onClick={() => switchMode('reset_request')}
                  style={{ background: 'transparent', border: 'none', color: 'var(--accent)', fontSize: 12.5, cursor: 'pointer', fontFamily: 'inherit' }}>
                  Forgot password?
                </button>
              )}
            </div>
            <p style={{ color: 'var(--muted-2)', fontSize: 11, marginTop: 14, textAlign: 'center' }}>
              Access is limited to @{ALLOWED_DOMAIN} accounts.
            </p>
          </form>
        )}

        {mode === 'reset_request' && (
          <form onSubmit={handleResetRequest}>
            <h2 className="serif" style={{ fontSize: 22, marginBottom: 10, color: 'var(--ink)' }}>Reset password</h2>
            <p style={{ color: 'var(--muted)', fontSize: 12.5, marginBottom: 20 }}>
              Enter your email and we'll send a link to set a new password.
            </p>
            <Input label="Work email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder={`you@${ALLOWED_DOMAIN}`} />
            <div style={{ display: 'flex', gap: 12 }}>
              <Button type="submit" fullWidth loading={busy}>Send reset link</Button>
              <Button type="button" variant="outline" fullWidth onClick={() => switchMode('login')}>Back</Button>
            </div>
          </form>
        )}

        {mode === 'update_password' && (
          <form onSubmit={handleUpdatePassword}>
            <h2 className="serif" style={{ fontSize: 22, marginBottom: 10, color: 'var(--ink)' }}>Set a new password</h2>
            <Input label="New password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required minLength={8} />
            <Button type="submit" fullWidth loading={busy}>Update password</Button>
          </form>
        )}
      </div>
    </div>
  );
};
