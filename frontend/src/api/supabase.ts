import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!url || !anonKey) {
  // Surfaced loudly in dev; in prod these come from the build env.
  // eslint-disable-next-line no-console
  console.error('Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY');
}

export const supabase = createClient(url, anonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/** App access is restricted to this email domain (also enforced server-side). */
export const ALLOWED_DOMAIN = 'next-belt.com';

export const isAllowedEmail = (email: string): boolean =>
  email.trim().toLowerCase().endsWith('@' + ALLOWED_DOMAIN);
