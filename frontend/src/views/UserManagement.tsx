import React, { useEffect, useState } from 'react';
import { Button, Input, Modal } from '../components';
import api from '../api/client';

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

const PlusIcon: React.FC = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const UsersIcon: React.FC<{ size?: number }> = ({ size = 13 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);

const ChevronRightIcon: React.FC<{ size?: number }> = ({ size = 11 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const ROLE_META: Record<string, { cls: string; label: string }> = {
  admin:   { cls: 'accent', label: 'Admin' },
  auditor: { cls: 'ok',     label: 'Auditor' },
  client:  { cls: 'muted',  label: 'Client' },
};

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'auditor',
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
    setFormError(null);
    try {
      await api.post('/register', formData);
      setShowCreateModal(false);
      setFormData({ email: '', password: '', full_name: '', role: 'auditor' });
      loadUsers();
    } catch (error: any) {
      const msg = error?.response?.data?.detail || 'Failed to create user';
      setFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
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
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="pg-head">
        <div>
          <div className="pg-crumb">
            <UsersIcon /> <span>NextBelt Admin</span> <ChevronRightIcon /> <span className="crumb-cur">Users</span>
          </div>
          <h1 className="pg-title">
            <em>User</em> Management
          </h1>
          <div className="pg-sub">
            <span>Manage user access and permissions</span>
          </div>
        </div>
        <button className="btn primary lg" onClick={() => setShowCreateModal(true)}>
          <PlusIcon /> Create User
        </button>
      </div>

      <section className="table-card">
        <div className="table-head">
          <div>
            <h3>All users</h3>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>
              {users.length} {users.length === 1 ? 'user' : 'users'}
            </div>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.6fr) 130px 130px 120px 110px',
            gap: 14,
            padding: '10px 22px',
            borderBottom: '1px solid var(--line-2)',
            color: 'var(--muted)',
            fontSize: 10.5,
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            fontWeight: 600,
          }}
        >
          <span>Name & email</span>
          <span>Role</span>
          <span>Status</span>
          <span>Created</span>
          <span style={{ textAlign: 'right' }}>Action</span>
        </div>

        {users.map((user) => {
          const role = ROLE_META[user.role] || { cls: 'muted', label: user.role };
          return (
            <div
              key={user.id}
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 1.6fr) 130px 130px 120px 110px',
                gap: 14,
                padding: '14px 22px',
                borderBottom: '1px solid var(--line-2)',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--ink)' }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 3 }}>
                  {user.email}
                </div>
              </div>
              <div>
                <span className={`chip ${role.cls}`}>{role.label}</span>
              </div>
              <div>
                <span className={`chip ${user.is_active ? 'ok' : 'danger'}`}>
                  <span className="dot" />
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="mono" style={{ fontSize: 11.5, color: 'var(--muted)' }}>
                {new Date(user.created_at).toLocaleDateString()}
              </div>
              <div style={{ textAlign: 'right' }}>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggleActive(user.id, user.is_active)}
                >
                  {user.is_active ? 'Disable' : 'Enable'}
                </Button>
              </div>
            </div>
          );
        })}
      </section>

      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setFormError(null);
        }}
        title="Create New User"
      >
        <form onSubmit={handleCreateUser}>
          {formError && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                background: 'rgba(194, 83, 60, 0.08)',
                border: '1px solid rgba(194, 83, 60, 0.30)',
                color: 'var(--danger)',
                fontSize: 12.5,
                marginBottom: 12,
              }}
            >
              {formError}
            </div>
          )}
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="user@example.com"
            required
          />
          <Input
            label="Full Name"
            type="text"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            placeholder="Jane Doe"
            required
          />
          <Input
            label="Password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            placeholder="Minimum 8 characters"
            required
          />

          <div className="field">
            <label className="field-label">Role</label>
            <select
              className="field-input"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="auditor">Auditor</option>
              <option value="admin">Admin</option>
              <option value="client">Client</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Create User</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
