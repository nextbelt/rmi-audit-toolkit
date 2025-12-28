import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';
import { Input, Button, Card } from '../components';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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

        <form onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@nextbelt.com"
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

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
            fullWidth={true}
            loading={isLoading}
            disabled={isLoading}
          >
            Sign In
          </Button>
        </form>

        <div style={{
          marginTop: '24px',
          padding: '16px',
          background: '#F2F1EE',
          borderRadius: '4px',
          fontSize: '0.75rem',
          color: '#5C5C5C',
        }}>
          <strong>Demo Credentials:</strong><br />
          Email: admin@nextbelt.com<br />
          Password: admin123
        </div>
      </Card>
    </div>
  );
};
