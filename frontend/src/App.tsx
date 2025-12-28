import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './api/store';
import {
  Login,
  Dashboard,
  InterviewInterface,
  ObservationChecklist,
  AssessmentDetail,
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
    <div>
      {/* Header */}
      <header style={{
        background: 'rgba(250, 250, 248, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #E5E4E0',
        padding: '16px 0',
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
            <h1 style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              margin: 0,
              color: '#1A1A1A',
              letterSpacing: '-0.02em',
            }}>
              RMI Audit Toolkit
            </h1>
            <span style={{
              fontSize: '0.75rem',
              color: '#8A8A8A',
              fontFamily: "'IBM Plex Mono', monospace",
            }}>
              by NextBelt LLC
            </span>
          </div>

          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#1A1A1A' }}>
                  {user.full_name}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#8A8A8A' }}>
                  {user.role}
                </div>
              </div>
              <button
                onClick={logout}
                style={{
                  padding: '8px 16px',
                  background: 'transparent',
                  border: '1px solid #D1D0CC',
                  borderRadius: '4px',
                  color: '#5C5C5C',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontFamily: "'Space Grotesk', sans-serif",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#0D4F4F';
                  e.currentTarget.style.color = '#0D4F4F';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#D1D0CC';
                  e.currentTarget.style.color = '#5C5C5C';
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
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />

        {/* Protected Routes with Layout */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/assessment/:assessmentId"
          element={
            <ProtectedRoute>
              <Layout>
                <AssessmentDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/assessment/:assessmentId/interview"
          element={
            <ProtectedRoute>
              <Layout>
                <InterviewInterface />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/assessment/:assessmentId/observations"
          element={
            <ProtectedRoute>
              <Layout>
                <ObservationChecklist />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Default Route */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
