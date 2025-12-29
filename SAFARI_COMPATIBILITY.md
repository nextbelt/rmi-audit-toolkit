# Safari Compatibility Troubleshooting Guide

## Changes Made for Safari Compatibility

### Backend (main.py)
- ✅ Added `expose_headers=["*"]` to CORS middleware
- ✅ Added `max_age=3600` to cache preflight requests
- ✅ Already has `allow_credentials=True`

### Frontend (client.ts)
- ✅ Added `withCredentials: true` to axios config
- ✅ Added 30-second timeout

---

## Common Safari Issues & Solutions

### Issue 1: "Cannot Access Site" or Blank Page
**Likely Cause:** Safari's Intelligent Tracking Prevention (ITP) blocking cookies/localStorage

**Solutions:**
1. **Tell your partner to:**
   - Open Safari → Preferences → Privacy
   - **Uncheck** "Prevent cross-site tracking" (temporarily)
   - Refresh the page

2. **Or use Private Browsing mode** (ironically, sometimes works better):
   - File → New Private Window
   - Try accessing the site

### Issue 2: "Mixed Content" Error
**Likely Cause:** Frontend is HTTPS but trying to connect to HTTP backend

**Check:**
- Is the frontend URL `https://...`?
- Is the backend URL `http://...` (not https)?

**Solution:**
Ensure `VITE_API_URL` environment variable points to HTTPS backend:
```bash
# On Railway, set this environment variable:
VITE_API_URL=https://rmi-audit-toolkit-backend-production.up.railway.app
```

### Issue 3: CORS Error in Safari Console
**Symptoms:** Console shows: `Cross-origin request blocked` or `No 'Access-Control-Allow-Origin' header`

**Check:**
1. Open Safari → Develop → Show JavaScript Console (Cmd+Option+C)
2. Look for red CORS errors

**Solution:**
Already fixed in code, but verify Railway deployment has latest code:
```bash
git add .
git commit -m "Add Safari compatibility fixes"
git push
```

### Issue 4: LocalStorage Not Working
**Symptoms:** Login works but immediately logs out, or token not saved

**Safari Restrictions:**
- Safari blocks localStorage in iframes
- Safari blocks localStorage in Private Browsing for some sites

**Solution:**
1. Ensure user is NOT in Private Browsing mode
2. Tell them to go to Safari → Preferences → Privacy → **Uncheck** "Block all cookies"

### Issue 5: "Not Secure" Warning on HTTPS
**Symptoms:** Safari shows warning about certificate

**Solution:**
Railway provides valid SSL certificates. If seeing this:
1. Check the URL is exactly: `https://rmi-audit-toolkit-frontend-production.up.railway.app`
2. Not a redirect or shortened link

---

## Diagnostic Questions to Ask Your Partner

1. **What exact error message do you see?**
   - Blank white screen?
   - "Cannot connect to server"?
   - "This site is not secure"?
   - Page loads but can't login?

2. **Can you open Safari Developer Tools?**
   - Safari → Preferences → Advanced → ✓ "Show Develop menu in menu bar"
   - Develop → Show JavaScript Console
   - **Send screenshot of any red errors**

3. **What URL are they using?**
   - The production Railway URL?
   - A custom domain?
   - A shortened link (bit.ly, etc.)?

4. **Safari Version?**
   - Safari → About Safari
   - **Needs Safari 14+ for full compatibility**

5. **Have they tried another browser?**
   - Does it work in Chrome/Firefox on the same device?
   - If yes → Safari-specific issue
   - If no → Network/deployment issue

---

## Quick Fix Checklist (Send to Partner)

**Try these in order:**

### Step 1: Clear Safari Cache
1. Safari → Preferences → Privacy → Manage Website Data → Remove All
2. Safari → History → Clear History → "all history"
3. Quit Safari completely
4. Reopen and try again

### Step 2: Disable Tracking Prevention (Temporarily)
1. Safari → Preferences → Privacy
2. **Uncheck** "Prevent cross-site tracking"
3. **Uncheck** "Block all cookies"
4. Refresh page

### Step 3: Try Private Window
1. File → New Private Window (Cmd+Shift+N)
2. Try accessing the site
3. (Sometimes Private mode bypasses cache issues)

### Step 4: Update Safari
1. System Preferences → Software Update
2. Install any pending macOS/Safari updates
3. Restart Mac

### Step 5: Try Different Network
1. Switch from WiFi to mobile hotspot (or vice versa)
2. Corporate networks sometimes block certain domains

---

## If Still Not Working

### Check Railway Deployment Status

1. **Backend Health Check:**
   ```
   https://rmi-audit-toolkit-backend-production.up.railway.app/
   ```
   Should return: `{"message": "RMI Audit Toolkit API", "status": "online"}`

2. **Frontend Build Status:**
   - Login to Railway dashboard
   - Check if latest deployment succeeded
   - Look for build errors

### Environment Variables on Railway

**Frontend needs:**
```
VITE_API_URL=https://rmi-audit-toolkit-backend-production.up.railway.app
```

**Backend needs:**
```
CORS_ORIGINS=https://rmi-audit-toolkit-frontend-production.up.railway.app
DATABASE_URL=<your-database-url>
SECRET_KEY=<your-secret-key>
```

---

## Known Safari Quirks

### iOS Safari Specific
- **Back Button:** Sometimes caches old state → Hard refresh needed
- **Home Screen App:** If added to home screen, localStorage might not persist
- **Low Power Mode:** Can disable some JavaScript features

### macOS Safari Specific
- **Content Blockers:** Extensions like AdBlock can break API calls
  - Safari → Preferences → Extensions → Disable all
- **Reader Mode:** Can interfere with dynamic content
- **Intelligent Tracking Prevention:** Most common issue

---

## Test in Safari (For You)

Open Safari on Mac/iPhone and try:
1. Navigate to production URL
2. Open Console (Cmd+Option+C)
3. Try to login
4. Look for errors

**Expected Console Output (Normal):**
```
[No errors should appear]
```

**Problem Console Output:**
```
❌ Cross-origin request blocked
❌ Failed to load resource
❌ localStorage is not available
```

---

## Contact Info to Collect

If partner still can't access, get:
- [ ] Screenshot of error
- [ ] Screenshot of Safari console
- [ ] Safari version
- [ ] macOS version (if Mac) or iOS version (if iPhone/iPad)
- [ ] Exact URL they're using
- [ ] Does it work on Chrome on same device?

---

## Fallback: Temporary Public Share

If Safari continues to be problematic and it's urgent, you could:

1. **Use Ngrok** to create temporary public URL from your local machine:
   ```bash
   ngrok http 3001
   ```
   Gives URL like: `https://abc123.ngrok.io`

2. **Send them that URL** for immediate access
   (Not permanent, just for demo/testing)

---

**Most Common Fix:** 90% of Safari issues are fixed by:
1. Disable "Prevent cross-site tracking"
2. Clear cache
3. Hard refresh (Cmd+Shift+R)
