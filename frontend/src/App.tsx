import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from './api/store';
import { Sidebar } from './components';
import {
  Login,
  UserManagement,
  DashboardV2,
  AssessmentV2Detail,
  Home,
  Reports,
  Benchmarks,
  AuditLog,
  Settings,
} from './views';
import './styles/global.css';

// ── Protected route wrapper ────────────────────────────────────────────────
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

// ── Slim breadcrumb top bar ────────────────────────────────────────────────
type Crumb = { label: string; to?: string };

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Drafts',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Scored',
  FINALIZED: 'Finalized',
};

function crumbsForPath(pathname: string, search: string): Crumb[] {
  if (pathname === '/' || pathname === '/home') {
    return [{ label: 'Home' }];
  }
  if (pathname.startsWith('/dashboard')) {
    const status = new URLSearchParams(search).get('status') || '';
    const sublabel = STATUS_LABELS[status.toUpperCase()];
    return sublabel
      ? [{ label: 'Assessments', to: '/dashboard' }, { label: sublabel }]
      : [{ label: 'Assessments' }];
  }
  if (pathname.startsWith('/assessment/')) {
    return [
      { label: 'Assessments', to: '/dashboard' },
      { label: 'Detail' },
    ];
  }
  if (pathname.startsWith('/benchmarks')) return [{ label: 'Insights' }, { label: 'Benchmarks' }];
  if (pathname.startsWith('/reports'))    return [{ label: 'Insights' }, { label: 'Reports' }];
  if (pathname.startsWith('/users'))      return [{ label: 'Admin' }, { label: 'Users' }];
  if (pathname.startsWith('/audit'))      return [{ label: 'Admin' }, { label: 'Audit log' }];
  if (pathname.startsWith('/settings'))   return [{ label: 'Admin' }, { label: 'Settings' }];
  return [{ label: 'Workspace' }];
}

const Chevron: React.FC = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const TopBar: React.FC = () => {
  const location = useLocation();
  const crumbs = crumbsForPath(location.pathname, location.search);

  return (
    <header className="topbar">
      <div className="crumb">
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {c.to ? <Link to={c.to}>{c.label}</Link> : (i === crumbs.length - 1 ? <b>{c.label}</b> : <span>{c.label}</span>)}
            {i < crumbs.length - 1 && <Chevron />}
          </React.Fragment>
        ))}
      </div>
    </header>
  );
};

// ── Shell layout (sidebar + main column) ───────────────────────────────────
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('rmi.sidebar.collapsed') === '1';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('rmi.sidebar.collapsed', collapsed ? '1' : '0');
    } catch {
      /* ignore */
    }
  }, [collapsed]);

  return (
    <div className="app-shell" data-rail={collapsed ? 'collapsed' : 'expanded'}>
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="main-col">
        <TopBar />
        <main style={{ flex: 1 }}>{children}</main>
      </div>
    </div>
  );
};

// ── Wrap a page in the protected shell ─────────────────────────────────────
const Page: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute>
    <Layout>{children}</Layout>
  </ProtectedRoute>
);

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
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Workspace */}
        <Route path="/home"      element={<Page><Home /></Page>} />

        {/* Assessments */}
        <Route path="/dashboard" element={<Page><DashboardV2 /></Page>} />
        <Route path="/assessment/:assessmentId" element={<Page><AssessmentV2Detail /></Page>} />

        {/* Insights */}
        <Route path="/benchmarks" element={<Page><Benchmarks /></Page>} />
        <Route path="/reports"    element={<Page><Reports /></Page>} />

        {/* Admin */}
        <Route path="/users"    element={<Page><UserManagement /></Page>} />
        <Route path="/audit"    element={<Page><AuditLog /></Page>} />
        <Route path="/settings" element={<Page><Settings /></Page>} />

        {/* Legacy v2 redirects */}
        <Route path="/v2" element={<Navigate to="/dashboard" replace />} />
        <Route path="/v2/assessment/:assessmentId" element={<Navigate to="/assessment/:assessmentId" replace />} />

        {/* Default */}
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
