import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './api/store';
import {
  Login,
  UserManagement,
  DashboardV2,
  AssessmentV2Detail,
} from './views';
import './styles/global.css';

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Layout Component with Header
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuthStore();

  return (
    <div style={{ minHeight: '100vh', background: '#FAFAFA' }}>
      {/* Header */}
      <header style={{
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid #E5E5E5',
        padding: '12px 0',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <a href="/dashboard" style={{ textDecoration: 'none', color: 'inherit' }}>
              <h1 style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                margin: 0,
                color: '#1A1A1A',
                letterSpacing: '-0.02em',
              }}>
                RMI Audit Toolkit
              </h1>
            </a>
            <span style={{
              fontSize: '0.7rem',
              color: '#999999',
              fontFamily: "'IBM Plex Mono', monospace",
              letterSpacing: '0.04em',
            }}>
              by NextBelt LLC
            </span>
          </div>

          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
              <nav style={{ display: 'flex', gap: '20px' }}>
                <a 
                  href="/dashboard" 
                  style={{
                    fontSize: '0.8125rem',
                    fontWeight: 500,
                    color: '#666666',
                    textDecoration: 'none',
                    transition: 'color 0.15s ease',
                    letterSpacing: '0.02em',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#0F6F6F'}
                  onMouseLeave={(e) => e.currentTarget.style.color = '#666666'}
                >
                  Assessments
                </a>
                {user.role === 'admin' && (
                  <a 
                    href="/users" 
                    style={{
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                      color: '#666666',
                      textDecoration: 'none',
                      transition: 'color 0.15s ease',
                      letterSpacing: '0.02em',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = '#0F6F6F'}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#666666'}
                  >
                    Users
                  </a>
                )}
              </nav>
              <div style={{
                height: '24px',
                width: '1px',
                background: '#E5E5E5',
              }} />
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8125rem', fontWeight: 500, color: '#333333' }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: '0.6875rem', color: '#999999', fontFamily: "'IBM Plex Mono', monospace" }}>
                  {user.role}
                </div>
              </div>
              <button
                onClick={logout}
                style={{
                  padding: '6px 14px',
                  background: '#F5F5F5',
                  border: '1px solid #E5E5E5',
                  borderRadius: '4px',
                  color: '#666666',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#0F6F6F';
                  e.currentTarget.style.color = '#0F6F6F';
                  e.currentTarget.style.background = 'rgba(15, 111, 111, 0.04)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#E5E5E5';
                  e.currentTarget.style.color = '#666666';
                  e.currentTarget.style.background = '#F5F5F5';
                }}
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main style={{ minHeight: 'calc(100vh - 73px)' }}>
        {children}
      </main>
    </div>
  );
};

function App() {
  const { fetchCurrentUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchCurrentUser();
    }
  }, [isAuthenticated]);

  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />

        {/* Protected Routes with Layout */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardV2 />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/assessment/:assessmentId"
          element={
            <ProtectedRoute>
              <Layout>
                <AssessmentV2Detail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout>
                <UserManagement />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Legacy v2 paths redirect to new paths */}
        <Route path="/v2" element={<Navigate to="/dashboard" replace />} />
        <Route path="/v2/assessment/:assessmentId" element={<Navigate to="/assessment/:assessmentId" replace />} />

        {/* Default Route */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
