import React, { useState, useEffect } from 'react';
import { Button, Card, Input } from '../components';
import api from '../api/client';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'auditor'
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/register', formData);
      alert('User created successfully!');
      setShowCreateModal(false);
      setFormData({ email: '', password: '', full_name: '', role: 'auditor' });
      loadUsers();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/users/${userId}`, { is_active: !currentStatus });
      loadUsers();
    } catch (error) {
      alert('Failed to update user status');
    }
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading users...</div>;
  }

  return (
    <div style={{ 
      padding: '40px 20px', 
      maxWidth: '1200px', 
      margin: '0 auto',
      fontFamily: "'Space Grotesk', sans-serif" 
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '32px' 
      }}>
        <div>
          <h1 style={{ 
            fontSize: '2rem', 
            fontWeight: 600, 
            color: '#1A1A1A',
            marginBottom: '8px' 
          }}>
            User Management
          </h1>
          <p style={{ color: '#666', fontSize: '1rem' }}>
            Manage user access and permissions
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          + Create User
        </Button>
      </div>

      <div style={{ display: 'grid', gap: '16px' }}>
        {users.map(user => (
          <Card key={user.id}>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 200px 150px 120px 100px',
              gap: '16px',
              alignItems: 'center' 
            }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#666' }}>
                  {user.email}
                </div>
              </div>
              
              <div>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '4px',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  background: user.role === 'admin' ? '#C65D3B' : 
                             user.role === 'auditor' ? '#0D4F4F' : '#666',
                  color: 'white'
                }}>
                  {user.role}
                </span>
              </div>

              <div style={{ fontSize: '0.875rem', color: '#666' }}>
                {new Date(user.created_at).toLocaleDateString()}
              </div>

              <div>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '4px',
                  fontSize: '0.875rem',
                  background: user.is_active ? '#22c55e' : '#ef4444',
                  color: 'white'
                }}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleToggleActive(user.id, user.is_active)}
              >
                {user.is_active ? 'Disable' : 'Enable'}
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <Card style={{ width: '100%', maxWidth: '500px', padding: '32px' }}>
            <h2 style={{ marginBottom: '24px', fontSize: '1.5rem' }}>Create New User</h2>
            
            <form onSubmit={handleCreateUser}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="user@example.com"
                  required
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Full Name
                </label>
                <Input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="John Doe"
                  required
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Password
                </label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Minimum 8 characters"
                  required
                />
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Role
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '2px solid #D1D0CC',
                    borderRadius: '4px',
                    fontSize: '1rem',
                    fontFamily: "'Space Grotesk', sans-serif"
                  }}
                >
                  <option value="auditor">Auditor</option>
                  <option value="admin">Admin</option>
                  <option value="client">Client</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <Button type="submit" fullWidth>
                  Create User
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  fullWidth
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
