import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/store';

type IconProps = { size?: number };

const Icon = {
  Home: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2h-4v-7h-6v7H5a2 2 0 0 1-2-2z" />
    </svg>
  ),
  Doc: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="14" y2="17" />
    </svg>
  ),
  Target: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  ),
  Download: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  ),
  Users: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  Edit: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z" />
    </svg>
  ),
  Settings: ({ size = 16 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.36.16.66.43.86.78.2.36.31.77.31 1.22 0 .45-.11.86-.31 1.22-.2.35-.5.62-.86.78z" />
    </svg>
  ),
  MoreH: ({ size = 14 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <circle cx="5" cy="12" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="19" cy="12" r="2" />
    </svg>
  ),
  Collapse: ({ size = 14 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <line x1="9" y1="4" x2="9" y2="20" />
    </svg>
  ),
  ChevronRight: ({ size = 14 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
};

type SubItem = { k: string; label: string; to: string };
type NavItem = {
  k: string;
  label: string;
  to: string;
  icon: React.ComponentType<IconProps>;
  badge?: string;
  count?: number | null;
  children?: SubItem[];
  matchPrefix?: string[];
  adminOnly?: boolean;
};
type NavSection = { section: string; items: NavItem[] };

const SECTIONS: NavSection[] = [
  {
    section: 'WORKSPACE',
    items: [
      { k: 'home', label: 'Home', to: '/home', icon: Icon.Home },
    ],
  },
  {
    section: 'ASSESSMENTS',
    items: [
      {
        k: 'assessments',
        label: 'Assessments',
        to: '/dashboard',
        icon: Icon.Doc,
        matchPrefix: ['/dashboard', '/assessment'],
        children: [
          { k: 'all',         label: 'All assessments',  to: '/dashboard' },
          { k: 'draft',       label: 'Drafts',           to: '/dashboard?status=DRAFT' },
          { k: 'in_progress', label: 'In Progress',      to: '/dashboard?status=IN_PROGRESS' },
          { k: 'scored',      label: 'Scored',           to: '/dashboard?status=COMPLETED' },
          { k: 'finalized',   label: 'Finalized',        to: '/dashboard?status=FINALIZED' },
        ],
      },
    ],
  },
  {
    section: 'INSIGHTS',
    items: [
      { k: 'benchmarks', label: 'Benchmarks', to: '/benchmarks', icon: Icon.Target },
      { k: 'reports',    label: 'Reports',    to: '/reports',    icon: Icon.Download },
    ],
  },
  {
    section: 'ADMIN',
    items: [
      { k: 'users',    label: 'Users',     to: '/users',    icon: Icon.Users,    adminOnly: true },
      { k: 'audit',    label: 'Audit log', to: '/audit',    icon: Icon.Edit,     adminOnly: true },
      { k: 'settings', label: 'Settings',  to: '/settings', icon: Icon.Settings },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (c: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const isAdmin = user?.role === 'admin';
  const path = location.pathname;
  const search = location.search;

  const isItemActive = (it: NavItem) => {
    const prefixes = it.matchPrefix ?? [it.to];
    return prefixes.some((p) => path === p || path.startsWith(p + '/') || path.startsWith(p));
  };

  const isSubActive = (sub: SubItem) => {
    const [subPath, subQuery] = sub.to.split('?');
    if (subPath !== path) return false;
    if (!subQuery) {
      // "All" sub-item: active when on /dashboard with no ?status= filter
      return !search.includes('status=');
    }
    return search.includes(subQuery);
  };

  const initials = (user?.full_name || 'NB')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <aside className="rail">
      <div className="rail-head">
        <div className="brand-mark">RMI</div>
        <div className="rail-brand-stack">
          <span className="rail-brand-name">RMI Toolkit</span>
          <span className="rail-brand-by">by NextBelt</span>
        </div>
        <button
          className="rail-toggle"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <Icon.ChevronRight size={14} /> : <Icon.Collapse size={14} />}
        </button>
      </div>

      <div className="rail-scroll">
        {SECTIONS.map((sec) => {
          const visibleItems = sec.items.filter((it) => !it.adminOnly || isAdmin);
          if (visibleItems.length === 0) return null;
          return (
            <div className="rail-section" key={sec.section}>
              <div className="rail-section-label">{sec.section}</div>
              {visibleItems.map((it) => {
                const active = isItemActive(it);
                const IconC = it.icon;
                return (
                  <React.Fragment key={it.k}>
                    <Link to={it.to} className={`rail-item ${active ? 'active' : ''}`}>
                      <IconC size={16} />
                      <span className="ri-label">{it.label}</span>
                      {it.badge && <span className="ri-badge">{it.badge}</span>}
                      {it.count != null && !it.badge && <span className="ri-count">{it.count}</span>}
                    </Link>
                    {active && it.children?.map((c) => (
                      <Link
                        key={c.k}
                        to={c.to}
                        className={`rail-subitem ${isSubActive(c) ? 'active' : ''}`}
                      >
                        {c.label}
                      </Link>
                    ))}
                  </React.Fragment>
                );
              })}
            </div>
          );
        })}
      </div>

      <div className="rail-foot">
        <div className="avatar" style={{ width: 30, height: 30, fontSize: 11.5 }}>{initials}</div>
        <div className="rail-foot-stack">
          <div className="rail-foot-name">{user?.full_name || 'NextBelt Admin'}</div>
          <div className="rail-foot-role">{user?.role || 'admin'} · NextBelt LLC</div>
        </div>
        <button
          className="rail-foot-more"
          onClick={() => {
            logout();
            navigate('/login');
          }}
          title="Sign out"
        >
          <Icon.MoreH size={14} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
