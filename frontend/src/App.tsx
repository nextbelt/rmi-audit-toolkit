import React, { Suspense, lazy, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from './api/store';
import { Sidebar } from './components';
import { Login } from './views';
import './styles/global.css';

// Code-split the authenticated views so the login bundle stays tiny (the
// assessment detail + charts are large and only needed once signed in).
const UserManagement = lazy(() => import('./views/UserManagement').then((m) => ({ default: m.UserManagement })));
const DashboardV2 = lazy(() => import('./views/DashboardV2').then((m) => ({ default: m.DashboardV2 })));
const AssessmentV2Detail = lazy(() => import('./views/AssessmentV2Detail').then((m) => ({ default: m.AssessmentV2Detail })));
const Home = lazy(() => import('./views/Home').then((m) => ({ default: m.Home })));
const Reports = lazy(() => import('./views/Reports').then((m) => ({ default: m.Reports })));
const Benchmarks = lazy(() => import('./views/Benchmarks').then((m) => ({ default: m.Benchmarks })));
const AuditLog = lazy(() => import('./views/AuditLog').then((m) => ({ default: m.AuditLog })));
const Settings = lazy(() => import('./views/Settings').then((m) => ({ default: m.Settings })));

// ── Protected route wrapper ────────────────────────────────────────────────
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, initialized } = useAuthStore();
  if (!initialized) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <div className="spinner" />
      </div>
    );
  }
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
        <main style={{ flex: 1 }}>
          <Suspense
            fallback={
              <div style={{ display: 'grid', placeItems: 'center', padding: '60px' }}>
                <div className="spinner" />
              </div>
            }
          >
            {children}
          </Suspense>
        </main>
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
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

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
