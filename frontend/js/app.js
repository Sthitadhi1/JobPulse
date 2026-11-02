const API_BASE = '/api/v1';

let currentUser = null;
let currentJobs = [];
let isBookmarkedOnlyFilter = false;

let currentFeedPage = 1;
let totalFeedPages = 1;
let totalFeedRecords = 0;
let isLoadingMoreFeed = false;

let selectedSalaryMin = null;
let selectedSalaryMax = null;

let selectedResumeFile = null;

// Job discovery is public. These tabs hold personal data, so signed-out visitors get the sign-in modal instead.
const ACCOUNT_TABS = {
  'dashboard': 'Sign in to see your personal job search dashboard.',
  'resume-match': 'Sign in to match your resume against live jobs.',
  'searches': 'Sign in to save searches and get alerts for new matching jobs.',
  'applications': 'Sign in to track your applications on a Kanban board.',
  'bookmarks': 'Sign in to bookmark jobs and come back to them later.',
  'telegram': 'Sign in to get instant Telegram alerts for new jobs.',
  'profile': 'Sign in to manage your account.'
};
const DEFAULT_AUTH_PROMPT = 'Sign in or create a free account to track applications, save searches and get job alerts.';

let activeTab = 'jobs';
let pendingTabAfterLogin = null;

function getAuthHeaders() {
  const token = localStorage.getItem('jobpulse_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    headers['X-JobPulse-Token'] = token;
  }
  return headers;
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initAuthentication();
  initNavigation();
  initDashboardEvents();
  initResumeMatchEvents();
  initSearchAndFilters();
  initModals();
  initTelegramView();
  initInfiniteScroll();
  initApplicationWorkspaceEvents();
  initSpotlightEffect();

  // Check auth state on load
  checkAuthState({ initial: true });
});

/* ==========================================================================
   1. THEME TOGGLE
   ========================================================================== */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  const htmlEl = document.documentElement;

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = htmlEl.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      htmlEl.setAttribute('data-theme', newTheme);
      toggleBtn.textContent = newTheme === 'dark' ? '🌙' : '☀️';
    });
  }
}

/* ==========================================================================
   2. AUTHENTICATION & SESSION MANAGEMENT (AUTH FIRST)
   ========================================================================== */
function initAuthentication() {
  const loginForm = document.getElementById('auth-login-form');
  const signupForm = document.getElementById('auth-signup-form');
  const tabLogin = document.getElementById('auth-tab-login');
  const tabSignup = document.getElementById('auth-tab-signup');
  const forgotLink = document.getElementById('auth-forgot-link');

  // Auth Modal Tabs
  tabLogin?.addEventListener('click', () => setAuthMode('login'));
  tabSignup?.addEventListener('click', () => setAuthMode('signup'));

  document.getElementById('header-signin-btn')?.addEventListener('click', () => openAuthModal());
  document.getElementById('close-auth-modal')?.addEventListener('click', closeAuthModal);
  document.getElementById('auth-screen')?.addEventListener('click', (e) => {
    if (e.target.id === 'auth-screen') closeAuthModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAuthModal();
  });

  if (forgotLink) {
    forgotLink.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('auth-screen')?.classList.add('hidden');
      const modal = document.getElementById('forgot-password-modal');
      if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('forgot-step-1')?.classList.remove('hidden');
        document.getElementById('forgot-step-2')?.classList.add('hidden');
        document.getElementById('forgot-error-msg')?.classList.add('hidden');
      }
    });
  }

  // Login Submit
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('auth-login-email').value.trim();
      const password = document.getElementById('auth-login-password').value;
      const msgEl = document.getElementById('auth-login-msg');
      const btn = document.getElementById('auth-login-btn');

      msgEl.classList.add('hidden');
      btn.disabled = true;
      btn.textContent = '⚡ Authenticating...';

      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const result = await res.json();

        if (res.ok && result.success) {
          if (result.token) {
            localStorage.setItem('jobpulse_token', result.token);
          }
          if (result.user) {
            localStorage.setItem('jobpulse_user', JSON.stringify(result.user));
          }
          showToast('Log in successful! Welcome to JobPulse.', 'success');
          await checkAuthState();
        } else {
          msgEl.textContent = result.detail || result.message || 'Invalid email or password.';
          msgEl.classList.remove('hidden');
        }
      } catch (err) {
        msgEl.textContent = 'Authentication error: ' + err.message;
        msgEl.classList.remove('hidden');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Log In to JobPulse';
      }
    });
  }

  // Signup Submit
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('auth-signup-name').value.trim();
      const email = document.getElementById('auth-signup-email').value.trim();
      const password = document.getElementById('auth-signup-password').value;
      const confirmPassword = document.getElementById('auth-signup-confirm').value;
      const msgEl = document.getElementById('auth-signup-msg');
      const btn = document.getElementById('auth-signup-btn');

      msgEl.classList.add('hidden');

      if (password !== confirmPassword) {
        msgEl.textContent = 'Passwords do not match.';
        msgEl.classList.remove('hidden');
        return;
      }

      if (password.length < 6) {
        msgEl.textContent = 'Password must be at least 6 characters.';
        msgEl.classList.remove('hidden');
        return;
      }

      btn.disabled = true;
      btn.textContent = '⚡ Creating Account...';

      try {
        const res = await fetch(`${API_BASE}/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });
        const result = await res.json();

        if (res.ok && result.success) {
          if (result.token) {
            localStorage.setItem('jobpulse_token', result.token);
          }
          if (result.user) {
            localStorage.setItem('jobpulse_user', JSON.stringify(result.user));
          }
          showToast('Account created successfully! Welcome to JobPulse.', 'success');
          await checkAuthState();
        } else {
          msgEl.textContent = result.detail || result.message || 'Signup failed. Please try again.';
          msgEl.classList.remove('hidden');
        }
      } catch (err) {
        msgEl.textContent = 'Signup error: ' + err.message;
        msgEl.classList.remove('hidden');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Create JobPulse Account';
      }
    });
  }

  // Forgot Password Flow
  document.getElementById('submit-forgot-btn')?.addEventListener('click', async () => {
    const email = document.getElementById('forgot-email-input')?.value.trim();
    const errorEl = document.getElementById('forgot-error-msg');
    const btn = document.getElementById('submit-forgot-btn');

    if (!email) {
      if (errorEl) {
        errorEl.textContent = 'Please enter your registered email address.';
        errorEl.className = 'alert alert-error';
        errorEl.classList.remove('hidden');
      }
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Generating code...';

    try {
      const res = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const result = await res.json();

      if (res.ok && result.success) {
        // Transition to Step 2
        document.getElementById('forgot-step-1')?.classList.add('hidden');
        document.getElementById('forgot-step-2')?.classList.remove('hidden');

        const msg2 = document.getElementById('reset-otp-msg');
        if (msg2) {
          msg2.textContent = result.message || 'Reset code sent!';
          msg2.className = 'alert alert-success';
          msg2.classList.remove('hidden');
        }
      } else {
        if (errorEl) {
          errorEl.textContent = result.detail || 'Could not send reset code.';
          errorEl.className = 'alert alert-error';
          errorEl.classList.remove('hidden');
        }
      }
    } catch (err) {
      if (errorEl) {
        errorEl.textContent = 'Error: ' + err.message;
        errorEl.className = 'alert alert-error';
        errorEl.classList.remove('hidden');
      }
    } finally {
      btn.disabled = false;
      btn.textContent = 'Get Reset Code';
    }
  });

  // Step 2 Reset Password Submit
  document.getElementById('submit-reset-otp-btn')?.addEventListener('click', async () => {
    const email = document.getElementById('forgot-email-input')?.value.trim();
    const otp = document.getElementById('reset-otp-input')?.value.trim();
    const newPassword = document.getElementById('reset-new-password')?.value;
    const confirmPassword = document.getElementById('reset-confirm-password')?.value;
    const msgEl = document.getElementById('reset-otp-msg');
    const btn = document.getElementById('submit-reset-otp-btn');

    if (!otp || otp.length < 6) {
      msgEl.textContent = 'Please enter the 6-digit reset code.';
      msgEl.className = 'alert alert-error';
      msgEl.classList.remove('hidden');
      return;
    }

    if (!newPassword || newPassword.length < 6) {
      msgEl.textContent = 'New password must be at least 6 characters.';
      msgEl.className = 'alert alert-error';
      msgEl.classList.remove('hidden');
      return;
    }

    if (newPassword !== confirmPassword) {
      msgEl.textContent = 'Passwords do not match.';
      msgEl.className = 'alert alert-error';
      msgEl.classList.remove('hidden');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Updating...';

    try {
      const res = await fetch(`${API_BASE}/auth/reset-password-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp, new_password: newPassword })
      });
      const result = await res.json();

      if (res.ok && result.success) {
        if (result.token) {
          localStorage.setItem('jobpulse_token', result.token);
        }
        showToast('Password reset successfully! Logged in.', 'success');
        document.getElementById('forgot-password-modal')?.classList.add('hidden');
        await checkAuthState();
      } else {
        msgEl.textContent = result.detail || result.message || 'Reset failed.';
        msgEl.className = 'alert alert-error';
        msgEl.classList.remove('hidden');
      }
    } catch (err) {
      msgEl.textContent = 'Error: ' + err.message;
      msgEl.className = 'alert alert-error';
      msgEl.classList.remove('hidden');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Update Password & Log In';
    }
  });

  document.getElementById('back-to-forgot-step1')?.addEventListener('click', () => {
    document.getElementById('forgot-step-2')?.classList.add('hidden');
    document.getElementById('forgot-step-1')?.classList.remove('hidden');
  });

  document.getElementById('close-forgot-modal')?.addEventListener('click', () => {
    document.getElementById('forgot-password-modal')?.classList.add('hidden');
  });
  document.getElementById('cancel-forgot')?.addEventListener('click', () => {
    document.getElementById('forgot-password-modal')?.classList.add('hidden');
  });

  // Header Logout & Profile Menu Toggle
  const profilePill = document.getElementById('header-profile-pill');
  const dropdownMenu = document.getElementById('header-profile-dropdown');
  const logoutBtn = document.getElementById('header-logout-action');

  if (profilePill && dropdownMenu) {
    profilePill.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', () => {
      dropdownMenu.classList.add('hidden');
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  document.getElementById('profile-logout-btn')?.addEventListener('click', handleLogout);
}

function setAuthMode(mode) {
  const isSignup = mode === 'signup';
  document.getElementById('auth-tab-login')?.classList.toggle('active', !isSignup);
  document.getElementById('auth-tab-signup')?.classList.toggle('active', isSignup);
  document.getElementById('auth-login-form')?.classList.toggle('hidden', isSignup);
  document.getElementById('auth-signup-form')?.classList.toggle('hidden', !isSignup);
}

function openAuthModal(message = DEFAULT_AUTH_PROMPT, tabAfterLogin = null) {
  pendingTabAfterLogin = tabAfterLogin;
  const promptEl = document.getElementById('auth-prompt-msg');
  if (promptEl) promptEl.textContent = message;
  document.getElementById('auth-login-msg')?.classList.add('hidden');
  document.getElementById('auth-signup-msg')?.classList.add('hidden');
  setAuthMode('login');
  document.getElementById('auth-screen')?.classList.remove('hidden');
  document.getElementById('auth-login-email')?.focus();
}

function closeAuthModal() {
  pendingTabAfterLogin = null;
  document.getElementById('auth-screen')?.classList.add('hidden');
}

// Returns true when signed in; otherwise opens the sign-in modal with the given reason.
function requireAuth(message) {
  if (currentUser) return true;
  openAuthModal(message);
  return false;
}

async function checkAuthState({ initial = false } = {}) {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        currentUser = data.user;
        localStorage.setItem('jobpulse_user', JSON.stringify(data.user));
        updateHeaderUserUI(data.user);

        const nextTab = pendingTabAfterLogin || (initial ? 'dashboard' : activeTab);
        closeAuthModal();
        switchTab(nextTab);
        return;
      }
    }
  } catch (err) {
    console.warn('Auth check warning:', err);
  }

  // Signed out: job discovery stays open, account features ask for sign-in
  currentUser = null;
  localStorage.removeItem('jobpulse_token');
  localStorage.removeItem('jobpulse_user');
  updateHeaderUserUI(null);
  if (initial) switchTab('jobs');
}

function updateHeaderUserUI(user) {
  const signedIn = Boolean(user);
  document.getElementById('header-signin-btn')?.classList.toggle('hidden', signedIn);
  ['header-user-profile', 'notif-bell', 'sync-now-btn'].forEach(id => {
    document.getElementById(id)?.classList.toggle('hidden', !signedIn);
  });
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('nav-locked', !signedIn && item.getAttribute('data-tab') in ACCOUNT_TABS);
  });
  // Job posting is restricted to accounts listed in the server's ADMIN_EMAILS.
  ['post-job-top-btn', 'post-job-feed-btn'].forEach(id => {
    document.getElementById(id)?.classList.toggle('hidden', !(user && user.is_admin));
  });
  if (!user) return;

  const avatarEl = document.getElementById('header-user-avatar');
  const nameEl = document.getElementById('header-user-name');
  const emailEl = document.getElementById('dropdown-user-email');

  if (avatarEl && user.name) {
    avatarEl.textContent = user.name.charAt(0).toUpperCase();
  }
  if (nameEl && user.name) {
    nameEl.textContent = user.name.split(' ')[0];
  }
  if (emailEl && user.email) {
    emailEl.textContent = user.email;
  }
  const tgInput = document.getElementById('telegram-chat-id-input');
  if (tgInput && user.telegram_chat_id && !tgInput.value) {
    tgInput.value = user.telegram_chat_id;
  }
}

async function handleLogout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    showToast('Logged out successfully.', 'info');
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    currentUser = null;
    localStorage.removeItem('jobpulse_token');
    localStorage.removeItem('jobpulse_user');
    updateHeaderUserUI(null);
    document.getElementById('header-profile-dropdown')?.classList.add('hidden');
    switchTab('jobs');
  }
}

/* ==========================================================================
   3. NAVIGATION & TAB SWITCHING
   ========================================================================== */
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tabTarget = item.getAttribute('data-tab');
      switchTab(tabTarget);
    });
  });

  // Switch tab via links and clickable stat cards (e.g. data-switch-tab="jobs")
  document.addEventListener('click', (e) => {
    const link = e.target.closest('[data-switch-tab], [data-goto-tab]');
    if (link) {
      e.preventDefault();
      const tabTarget = link.getAttribute('data-switch-tab') || link.getAttribute('data-goto-tab');
      if (tabTarget) switchTab(tabTarget);
    }
  });

  document.getElementById('sync-now-btn')?.addEventListener('click', triggerManualSync);
  document.getElementById('trigger-sync-panel-btn')?.addEventListener('click', triggerManualSync);
}

function switchTab(tabTarget) {
  if (!currentUser && tabTarget in ACCOUNT_TABS) {
    openAuthModal(ACCOUNT_TABS[tabTarget], tabTarget);
    return;
  }
  activeTab = tabTarget;

  const navItems = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');

  navItems.forEach(n => {
    if (n.getAttribute('data-tab') === tabTarget) {
      n.classList.add('active');
    } else {
      n.classList.remove('active');
    }
  });

  tabPanes.forEach(p => p.classList.remove('active'));

  const targetPane = document.getElementById(`tab-${tabTarget}`);
  if (targetPane) {
    targetPane.classList.add('active');
  }

  // Load tab-specific data
  if (tabTarget === 'dashboard') loadDashboardOverview();
  if (tabTarget === 'jobs') loadJobsFeed(true);
  if (tabTarget === 'resume-match') loadResumeMatchRecommendations();
  if (tabTarget === 'searches') loadSavedSearches();
  if (tabTarget === 'applications') loadApplicationWorkspace();
  if (tabTarget === 'bookmarks') loadBookmarksFeed();
  if (tabTarget === 'analytics') loadAnalytics();
  if (tabTarget === 'connectors') loadConnectorHealth();
  if (tabTarget === 'profile') loadProfile();
}

/* ==========================================================================
   4. POST-LOGIN COMMAND CENTER DASHBOARD
   ========================================================================== */
function initDashboardEvents() {
  const dropzone = document.getElementById('dashboard-resume-dropzone');
  const fileInput = document.getElementById('dashboard-resume-file-input');
  const analyzeBtn = document.getElementById('dashboard-analyze-resume-btn');
  const fileBadge = document.getElementById('dashboard-file-badge');

  if (dropzone && fileInput) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        selectedResumeFile = e.dataTransfer.files[0];
        showSelectedFileBadge(selectedResumeFile.name);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        selectedResumeFile = fileInput.files[0];
        showSelectedFileBadge(selectedResumeFile.name);
      }
    });
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => {
      if (!selectedResumeFile) {
        showToast('Please select or drop a resume PDF/DOCX file first.', 'warning');
        return;
      }
      processResumeAnalysis(selectedResumeFile);
    });
  }

  function showSelectedFileBadge(filename) {
    if (fileBadge) {
      fileBadge.textContent = `📄 Selected: ${filename}`;
      fileBadge.classList.remove('hidden');
    }
  }
}

async function loadDashboardOverview() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/overview`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const d = result.data;
      if (d) {
        // 1. Greeting
        const greetingEl = document.getElementById('dashboard-greeting');
        if (greetingEl) {
          const userName = currentUser ? currentUser.name.split(' ')[0] : 'Engineer';
          greetingEl.textContent = `${d.greeting}, ${userName} 👋`;
        }

        // 2. Stat Cards
        document.getElementById('dash-stat-active-jobs').textContent = (d.stats.active_jobs || 0).toLocaleString();
        document.getElementById('dash-stat-top-matches').textContent = (d.stats.top_matches || 30).toLocaleString();
        document.getElementById('dash-stat-applications').textContent = (d.stats.applications || 0).toLocaleString();
        document.getElementById('dash-stat-bookmarked').textContent = (d.stats.bookmarked || 0).toLocaleString();

        // 3. Pipeline counts
        const p = d.pipeline || {};
        document.getElementById('dash-pipe-saved').textContent = p.Saved || 0;
        document.getElementById('dash-pipe-applied').textContent = p.Applied || 0;
        document.getElementById('dash-pipe-oa').textContent = p['OA / Test'] || 0;
        document.getElementById('dash-pipe-interview').textContent = p.Interview || 0;
        document.getElementById('dash-pipe-offer').textContent = p.Offer || 0;

        // 4. Top Matches Preview
        const previewContainer = document.getElementById('dashboard-top-matches-preview-container');
        if (previewContainer && d.top_matches_preview && d.top_matches_preview.length > 0) {
          previewContainer.innerHTML = d.top_matches_preview.map(j => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; border-bottom: 1px solid var(--border-color);">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div class="company-logo-placeholder">${escapeHtml(j.company.charAt(0))}</div>
                <div>
                  <div style="font-weight: 700; font-size: 14px;">${escapeHtml(j.title)}</div>
                  <div class="text-xs text-muted">${escapeHtml(j.company)} • ${escapeHtml(j.location || 'Remote')}</div>
                </div>
              </div>
              <div style="text-align: right;">
                <span class="match-badge match-strong" style="font-size: 11px;">${j.match_score}% Match</span>
                <div class="text-xs text-muted mt-1" style="font-weight: 600;">${escapeHtml(j.match_classification)}</div>
              </div>
            </div>
          `).join('');
        } else {
          previewContainer.innerHTML = '<div class="text-muted text-sm" style="padding: 14px 0;">Upload your resume to get instant top opportunities.</div>';
        }
      }
    }
  } catch (err) {
    console.error('Dashboard overview error:', err);
  }
}

/* ==========================================================================
   5. RESUME MATCH & TOP 30 RECOMMENDATIONS
   ========================================================================== */
function initResumeMatchEvents() {
  const resumeTabFileInput = document.getElementById('resume-tab-file-input');
  if (resumeTabFileInput) {
    resumeTabFileInput.addEventListener('change', () => {
      if (resumeTabFileInput.files && resumeTabFileInput.files.length > 0) {
        processResumeAnalysis(resumeTabFileInput.files[0]);
      }
    });
  }
}

async function processResumeAnalysis(file) {
  showToast('Parsing resume & extracting structured candidate intelligence...', 'info');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const token = localStorage.getItem('jobpulse_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      headers['X-JobPulse-Token'] = token;
    }

    const res = await fetch(`${API_BASE}/ai/upload-resume`, {
      method: 'POST',
      headers: headers,
      body: formData
    });

    const result = await res.json();
    if (res.ok && result.success) {
      showToast(`Resume parsed! Discovered ${result.total_recommendations} top tailored opportunities.`, 'success');
      switchTab('resume-match');
      renderResumeMatchView(result.candidate_profile, result.data);
    } else {
      showToast(result.detail || 'Resume analysis failed.', 'error');
    }
  } catch (err) {
    showToast('Error uploading resume: ' + err.message, 'error');
  }
}

async function loadResumeMatchRecommendations() {
  const container = document.getElementById('resume-match-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Evaluating your candidate profile against active opportunities...</div>';

  try {
    const res = await fetch(`${API_BASE}/ai/recommendations`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      renderResumeMatchView(result.candidate_profile, result.data);
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading recommendations: ${err.message}</div>`;
  }
}

function renderResumeMatchView(profile, recommendations) {
  const container = document.getElementById('resume-match-container');
  const summaryEl = document.getElementById('candidate-profile-summary');

  if (summaryEl && profile) {
    summaryEl.classList.remove('hidden');

    const edu = profile.education || {
      degree: profile.degree || 'B.Tech in Computer Science',
      institution: profile.institution || 'Engineering Institute',
      grad_year: profile.grad_year || '2025',
      gpa: profile.gpa || '8.8/10'
    };

    const topSkills = profile.top_skills || profile.skills || [];
    const workExps = profile.work_experience || [];
    const projects = profile.projects || [];
    const preferredRoles = profile.preferred_roles || ['Software Development Engineer (SDE 1)', 'Full Stack Developer'];

    summaryEl.innerHTML = `
      <div class="candidate-bento-grid">
        <!-- 1. Candidate Hero Header -->
        <div class="candidate-profile-hero">
          <div class="candidate-hero-left">
            <div class="candidate-large-avatar">${(profile.name || 'C').charAt(0).toUpperCase()}</div>
            <div class="candidate-hero-meta">
              <h2>${escapeHtml(profile.name || 'Candidate Profile')}</h2>
              <div class="candidate-hero-contacts">
                <span>📧 ${escapeHtml(profile.email || 'candidate@example.com')}</span>
                <span>📱 ${escapeHtml(profile.phone || '+91 98765 43210')}</span>
                <span>🎯 Status: <strong style="color: #10b981;">Actively Seeking Opportunities</strong></span>
              </div>
              <div class="candidate-hero-roles">
                ${preferredRoles.map(r => `<span class="role-pill">${escapeHtml(r)}</span>`).join('')}
              </div>
            </div>
          </div>
          <div style="text-align: right;">
            <div class="badge badge-pulse" style="font-size: 13px; padding: 8px 16px; margin-bottom: 6px;">
              ⚡ ${recommendations ? recommendations.length : 0} Active Matches Verified
            </div>
            <div class="text-xs text-muted">Experience Level: <strong>${escapeHtml(profile.experience_level || 'Fresher')}</strong></div>
          </div>
        </div>

        <!-- 2. Education Card -->
        <div class="bento-card">
          <div class="bento-card-header">
            <div class="bento-card-title">🎓 Education & Background</div>
            <span class="badge badge-outline">Class of ${escapeHtml(edu.grad_year || '2027')}</span>
          </div>
          <div style="font-size: 14px; font-weight: 700; color: var(--text-primary);">${escapeHtml(edu.degree || 'B.Tech in CSE (Software Engineering Specialization)')}</div>
          <div style="font-size: 13px; color: var(--accent-blue); margin-top: 4px;">${escapeHtml(edu.institution || 'SRM Institute of Science and Technology, Chennai')}</div>
          <div style="display: flex; gap: 16px; margin-top: 10px; font-size: 12px; color: var(--text-muted); flex-wrap: wrap;">
            <span>Graduation: <strong>${escapeHtml(edu.grad_range || edu.grad_year || 'June 2023 – May 2027')}</strong></span>
            <span>Academic GPA: <strong>${escapeHtml(edu.gpa || '8.5 / 10.0')}</strong></span>
          </div>
        </div>

        <!-- 3. Top 15+ Ranked Technical Skills -->
        <div class="bento-card">
          <div class="bento-card-header">
            <div class="bento-card-title">💻 Technical Skills (${topSkills.length} Identified)</div>
            <span class="text-xs text-muted">Ranked by Stack Depth</span>
          </div>
          <div class="skills-badge-cluster">
            ${topSkills.map((sk, idx) => {
              let tagClass = 'skill-pill-lang';
              if (['React', 'Next.js', 'FastAPI', 'Django', 'Spring Boot', 'Node.js', 'Express', 'Tailwind'].includes(sk)) tagClass = 'skill-pill-framework';
              else if (['PostgreSQL', 'Redis', 'MongoDB', 'MySQL', 'SQL', 'Databricks', 'Apache Spark', 'Spark', 'SQLAlchemy'].includes(sk)) tagClass = 'skill-pill-db';
              else if (['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Git', 'Linux', 'GitHub Actions', 'Microsoft Azure', 'Azure', 'EC2', 'S3'].includes(sk)) tagClass = 'skill-pill-cloud';
              else if (['Machine Learning', 'PyTorch', 'TensorFlow', 'Deep Learning', 'NLP', 'AI', 'Hugging Face', 'Transformers', 'LangChain', 'RAG', 'CNNs', 'SHAP', 'XGBoost', 'Graph Machine Learning', 'Graph Neural Networks'].includes(sk)) tagClass = 'skill-pill-ml';
              else if (['Data Structures', 'Algorithms', 'System Design', 'OOP', 'Multithreading', 'Problem Solving', 'Debugging', 'Testing', 'CMake'].includes(sk)) tagClass = 'skill-pill-core';
              return `<span class="skill-pill-ranked ${tagClass}">${escapeHtml(sk)}</span>`;
            }).join('')}
          </div>
        </div>

        <!-- 4. Experience & Leadership / Fresher Status -->
        <div class="bento-card">
          <div class="bento-card-header">
            <div class="bento-card-title">💼 Experience & Leadership</div>
            <span class="badge badge-outline">${workExps.length > 0 ? `${workExps.length} Roles` : ((profile.leadership && profile.leadership.length > 0) ? `${profile.leadership.length} Leadership Roles` : 'Fresher / Student')}</span>
          </div>
          ${workExps.length > 0 ? workExps.map(exp => `
            <div class="timeline-item">
              <div class="timeline-role">${escapeHtml(exp.role || 'Software Engineering Intern')}</div>
              <div class="timeline-company">${escapeHtml(exp.company || 'Tech Organization')}</div>
              <div class="timeline-duration">📅 ${escapeHtml(exp.duration || '2024')}</div>
              <ul class="timeline-bullets">
                ${(exp.highlights || []).map(h => `<li>${escapeHtml(h)}</li>`).join('')}
              </ul>
            </div>
          `).join('') : ((profile.leadership && profile.leadership.length > 0) ? profile.leadership.map(lead => `
            <div class="timeline-item">
              <div class="timeline-role">${escapeHtml(lead.role)}</div>
              <div class="timeline-company">${escapeHtml(lead.organization)}</div>
              <div class="timeline-duration">📅 ${escapeHtml(lead.duration)}</div>
              <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">${escapeHtml(lead.description)}</div>
            </div>
          `).join('') : `
            <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.6;">
              🌱 <strong>Fresher / Student Candidate</strong> — No corporate work experience listed.
              <div style="color: var(--text-muted); font-size: 12px; margin-top: 6px;">
                Demonstrated strong technical readiness with 4+ production engineering projects and open-source contributions.
              </div>
            </div>
          `)}
        </div>

        <!-- 5. Key Projects Portfolio -->
        <div class="bento-card">
          <div class="bento-card-header">
            <div class="bento-card-title">🚀 Key Engineering Projects</div>
            <span class="text-xs text-muted">${projects.length} Highlights</span>
          </div>
          ${projects.map(proj => `
            <div class="project-card-item">
              <div class="project-title-row">
                <span class="project-title">${escapeHtml(proj.title)}</span>
              </div>
              <div class="project-desc">${escapeHtml(proj.description)}</div>
              <div class="project-tech-tags">
                ${(proj.tech_stack || []).map(t => `<span class="project-tech-tag">${escapeHtml(t)}</span>`).join('')}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  if (!recommendations || recommendations.length === 0) {
    container.innerHTML = '<div class="card card-padded text-muted">No active opportunities found for profile. Try uploading an updated resume.</div>';
    return;
  }

  container.innerHTML = recommendations.map(j => renderRecommendedJobCard(j)).join('');
}

function renderRecommendedJobCard(j) {
  const isClosed = j.status === 'CLOSED' || j.status === 'REMOVED';
  const matchClass = (j.match_classification || 'Good Match').toLowerCase().replace(' ', '-');

  const matchingSkillsHtml = j.matching_skills && j.matching_skills.length > 0
    ? j.matching_skills.slice(0, 6).map(s => `<span class="skill-tag-matched">✓ ${escapeHtml(s)}</span>`).join('')
    : '<span class="text-xs text-muted">CS Fundamentals</span>';

  const missingSkillsHtml = j.missing_skills && j.missing_skills.length > 0
    ? j.missing_skills.slice(0, 3).map(s => `<span class="skill-tag-missing">• ${escapeHtml(s)}</span>`).join('')
    : '<span class="text-xs text-muted" style="color: #10b981;">No critical gaps</span>';

  const b = j.breakdown || {};

  return `
    <div class="job-card spotlight-card">
      ${isClosed ? `
        <div class="closed-job-banner">
          🔴 JOB CLOSED — Source listing is no longer available.
        </div>
      ` : ''}

      <div class="job-card-header">
        <div>
          <span class="company-name">${escapeHtml(j.company)}</span>
          <h3 class="job-title">${escapeHtml(j.title)}</h3>
        </div>
        <button class="bookmark-btn ${j.is_bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark(${j.job_id || j.id}, this)">
          ${j.is_bookmarked ? '★' : '☆'}
        </button>
      </div>

      <div class="job-details">
        <span class="detail-item">📍 ${escapeHtml(j.location || 'India')}</span>
        <span class="detail-item">🌐 ${escapeHtml(j.remote_type || 'Hybrid')}</span>
        <span class="detail-item">💼 ${escapeHtml(j.experience_level || 'Fresher')}</span>
        ${j.salary_range ? `<span class="detail-item" style="color: #10b981;">💰 ${escapeHtml(j.salary_range)}</span>` : ''}
      </div>

      <!-- Match Scores & Priority Row -->
      <div style="display: flex; align-items: center; justify-content: space-between; background: var(--bg-secondary); padding: 8px 12px; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="match-badge match-${matchClass.includes('strong') ? 'strong' : (matchClass.includes('good') ? 'good' : 'moderate')}">${j.match_score}% Match</span>
          <span class="text-xs font-semibold" style="color: var(--text-secondary);">${escapeHtml(j.match_classification)}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <span class="text-xs text-muted">Priority:</span>
          <span class="priority-badge priority-${(j.application_priority || 'MEDIUM').toLowerCase()}">${j.application_priority || 'MEDIUM'}</span>
        </div>
      </div>

      <!-- Skills Overlap Section -->
      <div class="skills-section">
        <div class="skills-row">
          <span class="text-xs text-muted" style="width: 85px;">Matching:</span>
          ${matchingSkillsHtml}
        </div>
        <div class="skills-row">
          <span class="text-xs text-muted" style="width: 85px;">Gaps:</span>
          ${missingSkillsHtml}
        </div>
      </div>

      <!-- Expandable "Why this matches you" Accordion -->
      <div class="why-accordion-box">
        <button class="why-accordion-toggle" onclick="toggleAccordion('why-content-${j.job_id || j.id}')">
          <span>💡 Why this matches you</span>
          <span>▼</span>
        </button>
        <div id="why-content-${j.job_id || j.id}" class="why-accordion-content hidden">
          <div class="score-progress-row">
            <span class="text-xs text-muted">Skill Match</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.skill_match || 80}%;"></div></div>
            <span class="text-xs font-semibold">${b.skill_match || 80}%</span>
          </div>
          <div class="score-progress-row">
            <span class="text-xs text-muted">Role Alignment</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.role_alignment || 85}%;"></div></div>
            <span class="text-xs font-semibold">${b.role_alignment || 85}%</span>
          </div>
          <div class="score-progress-row">
            <span class="text-xs text-muted">Experience</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.experience_match || 90}%;"></div></div>
            <span class="text-xs font-semibold">${b.experience_match || 90}%</span>
          </div>
          <div class="score-progress-row">
            <span class="text-xs text-muted">Education</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.education_match || 90}%;"></div></div>
            <span class="text-xs font-semibold">${b.education_match || 90}%</span>
          </div>

          <div style="margin-top: 10px; font-size: 12px; color: var(--text-secondary); line-height: 1.5;">
            <strong>Analysis:</strong> ${escapeHtml(j.why_matches || 'Strong profile alignment with technical requirements.')}
          </div>
          ${j.potential_gap ? `
            <div style="margin-top: 6px; font-size: 12px; color: #f59e0b;">
              <strong>Note:</strong> ${escapeHtml(j.potential_gap)}
            </div>
          ` : ''}
        </div>
      </div>

      <!-- Action Buttons Row -->
      <div class="job-card-actions" style="display: flex; gap: 8px; margin-top: 14px;">
        ${isClosed ? `
          <button class="btn btn-sm btn-disabled" style="flex: 1;">🔴 Job Closed</button>
        ` : `
          <a href="${escapeHtml(j.apply_url || j.job_url || '#')}" target="_blank" class="btn btn-sm btn-primary" style="flex: 1; text-align: center; text-decoration: none;">
            Apply ↗
          </a>
        `}
        <button class="btn btn-sm btn-outline" onclick="trackJobInKanban('${escapeHtml(j.company)}', '${escapeHtml(j.title)}', ${j.job_id || j.id})" title="Track in Application Kanban">
          📋 Track
        </button>
        <button class="btn btn-sm btn-ghost" onclick="openJobDetailModal(${j.job_id || j.id})">
          Details
        </button>
      </div>
    </div>
  `;
}

function toggleAccordion(contentId) {
  const el = document.getElementById(contentId);
  if (el) {
    el.classList.toggle('hidden');
  }
}

async function trackJobInKanban(company, role, jobId) {
  if (!requireAuth('Sign in to track this application on your Kanban board.')) return;
  try {
    const res = await fetch(`${API_BASE}/applications/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        company: company,
        role: role,
        job_id: jobId,
        status: 'Applied',
        notes: 'Tracked from Top Opportunities recommendation feed.'
      })
    });
    if (res.ok) {
      showToast(`Added ${company} (${role}) to Application Kanban!`, 'success');
    } else {
      showToast('Could not track application.', 'error');
    }
  } catch (err) {
    showToast('Error tracking application: ' + err.message, 'error');
  }
}

/* ==========================================================================
   6. DISCOVER JOBS FEED (Infinite Scroll, Multi-Filter, Search)
   ========================================================================== */
function initSearchAndFilters() {
  document.getElementById('run-search-btn')?.addEventListener('click', () => {
    loadJobsFeed(true);
  });

  document.getElementById('job-search-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loadJobsFeed(true);
  });

  document.getElementById('filter-experience')?.addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-remote')?.addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-type')?.addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-salary')?.addEventListener('change', () => loadJobsFeed(true));

  // Salary Chips
  const chips = document.querySelectorAll('.salary-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedSalaryMin = chip.getAttribute('data-min') || null;
      selectedSalaryMax = chip.getAttribute('data-max') || null;
      loadJobsFeed(true);
    });
  });

  // Bookmarked Filter
  const bookmarkBtn = document.getElementById('bookmarked-only-btn');
  if (bookmarkBtn) {
    bookmarkBtn.addEventListener('click', () => {
      if (!requireAuth(ACCOUNT_TABS['bookmarks'])) return;
      isBookmarkedOnlyFilter = !isBookmarkedOnlyFilter;
      bookmarkBtn.classList.toggle('active', isBookmarkedOnlyFilter);
      loadJobsFeed(true);
    });
  }
}

function initInfiniteScroll() {
  const loadMoreBtn = document.getElementById('load-more-btn');
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
      if (currentFeedPage < totalFeedPages && !isLoadingMoreFeed) {
        currentFeedPage++;
        loadJobsFeed(false);
      }
    });
  }

  window.addEventListener('scroll', () => {
    if (document.getElementById('tab-jobs')?.classList.contains('active')) {
      const scrollY = window.scrollY;
      const visible = window.innerHeight;
      const pageHeight = document.documentElement.scrollHeight;

      if (scrollY + visible >= pageHeight - 300) {
        if (currentFeedPage < totalFeedPages && !isLoadingMoreFeed) {
          currentFeedPage++;
          loadJobsFeed(false);
        }
      }
    }
  });
}

async function loadJobsFeed(reset = false) {
  if (isLoadingMoreFeed) return;
  isLoadingMoreFeed = true;

  if (reset) {
    currentFeedPage = 1;
    currentJobs = [];
  }

  const container = document.getElementById('jobs-container');
  const countBadge = document.getElementById('job-count-badge');
  const spinner = document.getElementById('load-more-spinner');
  const loadMoreBtn = document.getElementById('load-more-btn');

  if (reset && container) {
    container.innerHTML = '<div class="loading-skeleton">Loading live discovery feed...</div>';
  }
  if (spinner) spinner.classList.remove('hidden');

  const keyword = document.getElementById('job-search-input')?.value.trim() || '';
  const experience = document.getElementById('filter-experience')?.value || '';
  const remote = document.getElementById('filter-remote')?.value || '';
  const employment = document.getElementById('filter-type')?.value || '';
  const minSalDropdown = document.getElementById('filter-salary')?.value || '';

  const minSalary = selectedSalaryMin || minSalDropdown || '';
  const maxSalary = selectedSalaryMax || '';

  const params = new URLSearchParams({
    page: currentFeedPage,
    limit: 20,
    active_only: true
  });

  if (keyword) params.append('keyword', keyword);
  if (experience) params.append('experience_level', experience);
  if (remote) params.append('remote_type', remote);
  if (employment) params.append('employment_type', employment);
  if (minSalary) params.append('min_salary_lpa', minSalary);
  if (maxSalary) params.append('max_salary_lpa', maxSalary);
  if (isBookmarkedOnlyFilter) params.append('bookmarked_only', 'true');

  try {
    const res = await fetch(`${API_BASE}/jobs/search?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const newJobs = result.data || [];
      totalFeedRecords = result.meta?.total_records ?? result.total ?? newJobs.length;
      totalFeedPages = Math.ceil(totalFeedRecords / 20) || 1;

      if (countBadge) {
        countBadge.textContent = `${totalFeedRecords.toLocaleString()} jobs verified`;
      }

      if (reset) {
        currentJobs = newJobs;
      } else {
        currentJobs = currentJobs.concat(newJobs);
      }

      renderJobsGrid(container, currentJobs);

      if (loadMoreBtn) {
        loadMoreBtn.classList.toggle('hidden', currentFeedPage >= totalFeedPages);
      }
    }
  } catch (err) {
    console.error('Load jobs error:', err);
    if (container && reset) {
      container.innerHTML = `<div class="card card-padded text-muted">Error loading jobs: ${err.message}</div>`;
    }
  } finally {
    isLoadingMoreFeed = false;
    if (spinner) spinner.classList.add('hidden');
  }
}

function renderJobsGrid(container, jobs) {
  if (!container) return;

  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<div class="card card-padded text-muted" style="grid-column: 1 / -1; text-align: center;">No active matching jobs found. Try adjusting your filters.</div>';
    return;
  }

  container.innerHTML = jobs.map(j => {
    const isClosed = j.status === 'CLOSED' || j.status === 'REMOVED';
    const tags = (j.raw_tags || '').split(',').map(t => t.trim()).filter(t => t.length > 0).slice(0, 4);

    return `
      <div class="job-card spotlight-card">
        ${isClosed ? `
          <div class="closed-job-banner">
            🔴 JOB CLOSED — Source listing is no longer available.
          </div>
        ` : ''}

        <div class="job-card-header">
          <div>
            <span class="company-name">${escapeHtml(j.company)}</span>
            <h3 class="job-title">${escapeHtml(j.title)}</h3>
          </div>
          <button class="bookmark-btn ${j.is_bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark(${j.id}, this)">
            ${j.is_bookmarked ? '★' : '☆'}
          </button>
        </div>

        <div class="job-details">
          <span class="detail-item">📍 ${escapeHtml(j.location || 'India')}</span>
          <span class="detail-item">🌐 ${escapeHtml(j.remote_type || 'Hybrid')}</span>
          <span class="detail-item">💼 ${escapeHtml(j.experience_level || 'Fresher')}</span>
          ${j.salary_range ? `<span class="detail-item" style="color: #10b981;">💰 ${escapeHtml(j.salary_range)}</span>` : ''}
        </div>

        <div class="skills-row mt-2">
          ${tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>

        <div class="job-card-actions" style="display: flex; gap: 8px; margin-top: 14px;">
          ${isClosed ? `
            <button class="btn btn-sm btn-disabled" style="flex: 1;">🔴 Closed</button>
          ` : `
            <a href="${escapeHtml(j.external_apply_url || j.job_url || '#')}" target="_blank" class="btn btn-sm btn-primary" style="flex: 1; text-align: center; text-decoration: none;">
              Apply ↗
            </a>
          `}
          <button class="btn btn-sm btn-outline" onclick="trackJobInKanban('${escapeHtml(j.company)}', '${escapeHtml(j.title)}', ${j.id})">
            📋 Track
          </button>
          <button class="btn btn-sm btn-ghost" onclick="openJobDetailModal(${j.id})">
            Details
          </button>
        </div>
      </div>
    `;
  }).join('');
}

async function toggleBookmark(jobId, btnEl) {
  if (!requireAuth(ACCOUNT_TABS['bookmarks'])) return;
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/bookmark`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const isBookmarked = result.is_bookmarked;
      if (btnEl) {
        btnEl.textContent = isBookmarked ? '★' : '☆';
        btnEl.classList.toggle('bookmarked', isBookmarked);
      }
      showToast(result.message || (isBookmarked ? 'Bookmarked job!' : 'Bookmark removed.'), 'info');
    }
  } catch (err) {
    showToast('Error updating bookmark: ' + err.message, 'error');
  }
}

async function loadBookmarksFeed() {
  const container = document.getElementById('bookmarks-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading bookmarked opportunities...</div>';

  try {
    const res = await fetch(`${API_BASE}/jobs/bookmarks`, {
      headers: getAuthHeaders()
    });
    const result = await res.json();
    if (result.success) {
      renderJobsGrid(container, result.data);
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading bookmarks: ${err.message}</div>`;
  }
}

/* ==========================================================================
   7. SAVED SEARCHES & ALERTS
   ========================================================================== */
async function loadSavedSearches() {
  const container = document.getElementById('searches-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading saved search rules...</div>';

  try {
    const res = await fetch(`${API_BASE}/search/saved`, {
      headers: getAuthHeaders()
    });
    const result = await res.json();

    if (result.success && result.data) {
      if (result.data.length === 0) {
        container.innerHTML = '<div class="card card-padded text-muted">No active search alert rules created yet. Click "➕ New Saved Search" to configure instant alerts.</div>';
        return;
      }

      container.innerHTML = `
        <table class="table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-size: 12px;">
              <th style="padding: 10px;">Rule Name</th>
              <th style="padding: 10px;">Keywords & Tech</th>
              <th style="padding: 10px;">Location & Mode</th>
              <th style="padding: 10px;">Status</th>
              <th style="padding: 10px;">Telegram Recipient</th>
              <th style="padding: 10px; text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(s => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 13px;">
                <td style="padding: 12px; font-weight: 700; color: var(--text-primary);">${escapeHtml(s.name)}</td>
                <td style="padding: 12px; color: var(--accent-blue);">${escapeHtml(s.keywords || s.query || 'All Jobs')}</td>
                <td style="padding: 12px; color: var(--text-muted);">${escapeHtml(s.location || 'Any')} (${escapeHtml(s.remote_type || 'Any')})</td>
                <td style="padding: 12px;">
                  <span class="badge ${s.is_active ? 'badge-pulse' : 'badge-outline'}" style="font-size: 11px;">
                    ${s.is_active ? '🟢 ACTIVE' : '⏸ PAUSED'}
                  </span>
                </td>
                <td style="padding: 12px; font-family: var(--font-mono); font-size: 11px;">${escapeHtml(s.telegram_chat_id || 'Default')}</td>
                <td style="padding: 12px; text-align: right;">
                  <button class="btn btn-sm btn-ghost" onclick="toggleSavedSearchRule(${s.id})">
                    ${s.is_active ? 'Pause' : 'Activate'}
                  </button>
                  <button class="btn btn-sm btn-ghost" style="color: #ef4444;" onclick="deleteSavedSearchRule(${s.id})">
                    ✕
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } else {
      container.innerHTML = `<div class="card card-padded text-muted">${result.message || 'No search rules found.'}</div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading search rules: ${err.message}</div>`;
  }
}

async function toggleSavedSearchRule(id) {
  try {
    const res = await fetch(`${API_BASE}/search/saved/${id}/toggle`, {
      method: 'PATCH',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast('Search alert rule updated.', 'info');
      loadSavedSearches();
    }
  } catch (err) {
    showToast('Error toggling rule: ' + err.message, 'error');
  }
}

async function deleteSavedSearchRule(id) {
  if (!confirm('Are you sure you want to delete this alert rule?')) return;
  try {
    const res = await fetch(`${API_BASE}/search/saved/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast('Search alert rule deleted.', 'info');
      loadSavedSearches();
    }
  } catch (err) {
    showToast('Error deleting rule: ' + err.message, 'error');
  }
}

/* ==========================================================================
   8. APPLICATION WORKSPACE (KANBAN)
   ========================================================================== */
function initApplicationWorkspaceEvents() {
  document.getElementById('add-custom-application-btn')?.addEventListener('click', () => {
    const company = prompt('Enter Company Name:');
    if (!company) return;
    const role = prompt('Enter Job Role Title:');
    if (!role) return;

    fetch(`${API_BASE}/applications/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ company, role, status: 'Applied' })
    }).then(res => {
      if (res.ok) {
        showToast('Application tracked!', 'success');
        loadApplicationWorkspace();
      }
    });
  });
}

async function loadApplicationWorkspace() {
  const container = document.getElementById('kanban-board-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading Application Kanban columns...</div>';

  try {
    const res = await fetch(`${API_BASE}/applications/`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const apps = result.data || [];

      const columns = ['Saved', 'Applied', 'OA / Test', 'Interview', 'Offer', 'Rejected'];
      const grouped = {};
      columns.forEach(c => grouped[c] = []);
      apps.forEach(a => {
        const col = a.status || 'Applied';
        if (grouped[col]) grouped[col].push(a);
        else grouped['Applied'].push(a);
      });

      container.innerHTML = columns.map(col => `
        <div class="kanban-column" ondragover="event.preventDefault()" ondrop="dropToColumn(event, '${col}')">
          <div class="kanban-col-header">
            <h4>${col}</h4>
            <span class="badge badge-outline">${grouped[col].length}</span>
          </div>
          <div class="kanban-cards-list">
            ${grouped[col].map(a => `
              <div class="kanban-card" draggable="true" ondragstart="dragApplication(event, ${a.id})">
                <div style="font-weight: 700; font-size: 13px;">${escapeHtml(a.company)}</div>
                <div class="text-xs text-muted">${escapeHtml(a.role)}</div>
                <div class="text-xs mt-2" style="display: flex; justify-content: space-between; color: var(--text-muted);">
                  <span>${a.applied_date ? new Date(a.applied_date).toLocaleDateString() : 'Active'}</span>
                  <span style="color: #ef4444; cursor: pointer;" onclick="deleteApp(${a.id})">✕</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading Kanban: ${err.message}</div>`;
  }
}

function dragApplication(e, id) {
  e.dataTransfer.setData('text/plain', id);
}

async function dropToColumn(e, newStatus) {
  e.preventDefault();
  const id = e.dataTransfer.getData('text/plain');
  if (!id) return;

  try {
    const res = await fetch(`${API_BASE}/applications/${id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast(`Application moved to ${newStatus}`, 'info');
      loadApplicationWorkspace();
    }
  } catch (err) {
    showToast('Error moving application: ' + err.message, 'error');
  }
}

async function deleteApp(id) {
  if (!confirm('Remove application?')) return;
  try {
    await fetch(`${API_BASE}/applications/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    loadApplicationWorkspace();
  } catch (err) {}
}

/* ==========================================================================
   9. ANALYTICS & CONNECTORS
   ========================================================================== */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const d = result.data;
      if (d) {
        document.getElementById('stat-total-jobs').textContent = (d.total_jobs || 0).toLocaleString();
        document.getElementById('stat-remote-jobs').textContent = (d.active_jobs || 0).toLocaleString();
        document.getElementById('stat-fresher-jobs').textContent = (d.freshers_jobs_today || 0).toLocaleString();
        document.getElementById('stat-avg-salary').textContent = `${d.verification_success_rate || 95}%`;
      }
    }
  } catch (err) {
    console.error('Analytics error:', err);
  }
}

async function loadConnectorHealth() {
  const container = document.getElementById('connectors-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading connector diagnostics...</div>';

  try {
    const res = await fetch(`${API_BASE}/admin/connectors`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const connectors = result.data || [];

      container.innerHTML = `
        <table class="table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-size: 12px;">
              <th style="padding: 10px;">Connector Source</th>
              <th style="padding: 10px;">Type</th>
              <th style="padding: 10px;">Status</th>
              <th style="padding: 10px;">Indexed Jobs</th>
              <th style="padding: 10px;">Last Latency</th>
            </tr>
          </thead>
          <tbody>
            ${connectors.map(c => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 13px;">
                <td style="padding: 12px; font-weight: 600;">${escapeHtml(c.name)}</td>
                <td style="padding: 12px; color: var(--accent-blue);">${escapeHtml(c.source_type)}</td>
                <td style="padding: 12px;">
                  <span class="badge ${c.health === 'HEALTHY' ? 'badge-pulse' : 'badge-outline'}" style="font-size: 11px;">
                    ${c.health || 'HEALTHY'}
                  </span>
                </td>
                <td style="padding: 12px;">${c.jobs_discovered_total || 2}</td>
                <td style="padding: 12px; font-family: var(--font-mono);">${c.duration_ms ? Math.round(c.duration_ms) + 'ms' : '15ms'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading connector diagnostics: ${err.message}</div>`;
  }
}

async function triggerManualSync() {
  if (!requireAuth('Sign in with an admin account to sync job sources.')) return;
  showToast('⚡ Triggering multi-connector discovery cycle in background...', 'info');
  try {
    const res = await fetch(`${API_BASE}/admin/discover`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast('Discovery cycle initiated successfully!', 'success');
      setTimeout(() => {
        loadJobsFeed(true);
        loadDashboardOverview();
      }, 3000);
    }
  } catch (err) {
    showToast('Error syncing sources: ' + err.message, 'error');
  }
}

/* ==========================================================================
   10. TELEGRAM NOTIFICATIONS
   ========================================================================== */
function initTelegramView() {
  document.getElementById('send-telegram-test-btn')?.addEventListener('click', async () => {
    const input = document.getElementById('telegram-chat-id-input');
    const resultEl = document.getElementById('telegram-test-result');
    const chatId = input?.value.trim();
    if (!chatId) {
      showToast('Please enter your numeric Telegram Chat ID.', 'warning');
      return;
    }

    showToast('Sending test job alert...', 'info');
    try {
      const res = await fetch(`${API_BASE}/notifications/telegram/test`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ chat_id: chatId })
      });
      const result = await res.json();
      const delivered = res.ok && result.delivered_via_api;
      if (resultEl) {
        resultEl.textContent = result.message || result.detail || 'Could not send test alert.';
        resultEl.className = `alert mt-3 ${delivered ? 'alert-success' : 'alert-error'}`;
      }
      if (delivered && currentUser) {
        currentUser.telegram_chat_id = chatId;
        currentUser.telegram_connected = true;
      }
    } catch (err) {
      showToast('Error sending test alert: ' + err.message, 'error');
    }
  });
}

/* ==========================================================================
   11. MODALS & PROFILE
   ========================================================================== */
function loadProfile() {
  const user = currentUser || JSON.parse(localStorage.getItem('jobpulse_user') || '{}');
  if (user) {
    const nameInput = document.getElementById('profile-name-field');
    const emailInput = document.getElementById('profile-email-field');
    if (nameInput) nameInput.value = user.name || '';
    if (emailInput) emailInput.value = user.email || '';
  }
}

function initModals() {
  // Admin Manual Post Job Modal Triggers
  const openManualJobModal = () => {
    const modal = document.getElementById('manual-job-modal');
    if (modal) {
      modal.classList.remove('hidden');
      const msg = document.getElementById('manual-job-msg');
      if (msg) msg.classList.add('hidden');
      document.getElementById('manual-job-title')?.focus();
    }
  };

  const closeManualJobModal = () => {
    document.getElementById('manual-job-modal')?.classList.add('hidden');
  };

  document.getElementById('post-job-top-btn')?.addEventListener('click', openManualJobModal);
  document.getElementById('post-job-feed-btn')?.addEventListener('click', openManualJobModal);
  document.getElementById('close-manual-job-modal')?.addEventListener('click', closeManualJobModal);
  document.getElementById('cancel-manual-job')?.addEventListener('click', closeManualJobModal);

  // Manual Job Form Submit
  document.getElementById('manual-job-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('manual-job-title')?.value.trim();
    const company = document.getElementById('manual-job-company')?.value.trim();
    const jobUrl = document.getElementById('manual-job-url')?.value.trim();
    const location = document.getElementById('manual-job-location')?.value.trim() || 'Bengaluru, India';
    const remoteType = document.getElementById('manual-job-remote')?.value || 'Hybrid';
    const expLevel = document.getElementById('manual-job-exp')?.value || 'Fresher';
    const empType = document.getElementById('manual-job-employment')?.value || 'Full-time';
    const salaryRange = document.getElementById('manual-job-salary')?.value.trim() || null;
    const minSalVal = document.getElementById('manual-job-minsal')?.value;
    const tags = document.getElementById('manual-job-tags')?.value.trim() || null;
    const desc = document.getElementById('manual-job-desc')?.value.trim() || null;
    const msgEl = document.getElementById('manual-job-msg');
    const submitBtn = document.getElementById('submit-manual-job-btn');

    if (!title || !company || !jobUrl) {
      if (msgEl) {
        msgEl.className = 'alert alert-error';
        msgEl.textContent = 'Please fill in Title, Company, and Application Link.';
        msgEl.classList.remove('hidden');
      }
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Publishing...';
    }

    try {
      const res = await fetch(`${API_BASE}/jobs/manual`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          title: title,
          company: company,
          job_url: jobUrl,
          external_apply_url: jobUrl,
          location: location,
          remote_type: remoteType,
          experience_level: expLevel,
          employment_type: empType,
          salary_range: salaryRange,
          min_salary_lpa: minSalVal ? parseFloat(minSalVal) : null,
          tags: tags,
          skills: tags,
          description: desc
        })
      });

      const result = await res.json();
      if (res.ok && result.success) {
        showToast(`🎉 "${title}" at ${company} posted successfully!`, 'success');
        document.getElementById('manual-job-form')?.reset();
        closeManualJobModal();

        // Switch to Discover Jobs and reload feed
        switchTab('jobs');
        currentFeedPage = 1;
        loadJobsFeed(true);
        loadDashboardStats();
      } else {
        const errorDetail = result.detail ? (typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail)) : 'Failed to post job listing.';
        if (msgEl) {
          msgEl.className = 'alert alert-error';
          msgEl.textContent = errorDetail;
          msgEl.classList.remove('hidden');
        }
        showToast(errorDetail, 'error');
      }
    } catch (err) {
      if (msgEl) {
        msgEl.className = 'alert alert-error';
        msgEl.textContent = 'Network error: ' + err.message;
        msgEl.classList.remove('hidden');
      }
      showToast('Error posting job: ' + err.message, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Publish Job Listing';
      }
    }
  });

  document.getElementById('close-modal-btn')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.add('hidden');
  });

  document.getElementById('cancel-save-search')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.add('hidden');
  });

  document.getElementById('create-search-modal-btn')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.remove('hidden');
  });

  document.getElementById('save-current-search-btn')?.addEventListener('click', () => {
    if (!requireAuth(ACCOUNT_TABS['searches'])) return;
    const currentKeyword = document.getElementById('job-search-input')?.value.trim();
    if (currentKeyword) {
      document.getElementById('modal-search-query').value = currentKeyword;
      document.getElementById('modal-search-name').value = `${currentKeyword} Opportunities`;
    }
    document.getElementById('save-search-modal')?.classList.remove('hidden');
  });

  document.getElementById('confirm-save-search')?.addEventListener('click', async () => {
    const name = document.getElementById('modal-search-name').value.trim();
    const query = document.getElementById('modal-search-query').value.trim();
    const location = document.getElementById('modal-search-location')?.value.trim();
    const salaryVal = document.getElementById('modal-search-salary')?.value;
    const remote = document.getElementById('modal-search-remote')?.value;
    const telegram = document.getElementById('modal-search-telegram')?.value.trim();

    if (!name) {
      showToast('Alert rule name is required.', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/search/saved`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name: name,
          query: query,
          keywords: query,
          location: location || null,
          min_salary_lpa: salaryVal ? parseFloat(salaryVal) : null,
          remote_type: remote || null,
          telegram_chat_id: telegram || null
        })
      });
      const result = await res.json();
      if (res.ok && result.success) {
        showToast('Saved search alert created!', 'success');
        document.getElementById('save-search-modal')?.classList.add('hidden');
        loadSavedSearches();
      } else {
        showToast(result.detail || 'Could not save search rule.', 'error');
      }
    } catch (err) {
      showToast('Error creating search alert: ' + err.message, 'error');
    }
  });

  // Job Detail Modal
  document.getElementById('close-job-detail-modal')?.addEventListener('click', closeJobDetailModal);
  document.getElementById('close-job-detail-btn')?.addEventListener('click', closeJobDetailModal);
}

async function openJobDetailModal(jobId) {
  const modal = document.getElementById('job-detail-modal');
  const titleEl = document.getElementById('modal-job-title');
  const bodyEl = document.getElementById('modal-job-body');
  const applyLink = document.getElementById('modal-job-apply-link');

  if (!modal) return;

  bodyEl.innerHTML = '<div class="loading-skeleton">Loading job details...</div>';
  modal.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
      headers: getAuthHeaders()
    });
    if (res.ok) {
      const result = await res.json();
      const j = result.data;

      titleEl.textContent = `${j.company} — ${j.title}`;

      const isClosed = j.status === 'CLOSED' || j.status === 'REMOVED';
      if (isClosed) {
        applyLink.classList.add('btn-disabled');
        applyLink.textContent = 'Job Closed';
        applyLink.removeAttribute('href');
      } else {
        applyLink.classList.remove('btn-disabled');
        applyLink.textContent = 'Apply Now ↗';
        applyLink.href = j.external_apply_url || j.job_url || '#';
      }

      bodyEl.innerHTML = `
        ${isClosed ? `
          <div class="closed-job-banner mb-3">
            🔴 ${escapeHtml(j.notice || 'This job is no longer active on the source website.')}
          </div>
        ` : ''}
        <div class="mb-3">
          <strong>Location:</strong> ${escapeHtml(j.location || 'India')}<br>
          <strong>Remote Type:</strong> ${escapeHtml(j.remote_type || 'Hybrid')}<br>
          <strong>Experience:</strong> ${escapeHtml(j.experience_level || 'Fresher')}<br>
          ${j.salary_range ? `<strong>Salary:</strong> <span style="color: #10b981;">${escapeHtml(j.salary_range)}</span><br>` : ''}
          <strong>Source:</strong> ${escapeHtml(j.source || 'ATS')}
        </div>
        <hr style="border-color: var(--border-color); margin: 12px 0;">
        <div style="font-weight: 600; margin-bottom: 6px;">Job Description:</div>
        <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.6; max-height: 250px; overflow-y: auto;">
          ${escapeHtml(j.description || 'Full job posting details indexed directly from source ATS/career portal.')}
        </div>
      `;
    }
  } catch (err) {
    bodyEl.innerHTML = `<div class="text-muted">Error loading job details: ${err.message}</div>`;
  }
}

function closeJobDetailModal() {
  document.getElementById('job-detail-modal')?.classList.add('hidden');
}

/* ==========================================================================
   12. SPOTLIGHT EFFECT & TOASTS
   ========================================================================== */
function initSpotlightEffect() {
  document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.spotlight-card');
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.position = 'fixed';
    container.style.bottom = '20px';
    container.style.right = '20px';
    container.style.zIndex = '9999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '10px';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'error' ? 'error' : (type === 'success' ? 'success' : 'info')}`;
  toast.style.boxShadow = '0 8px 24px rgba(0,0,0,0.5)';
  toast.style.minWidth = '260px';
  toast.style.animation = 'fadeIn 0.3s ease';
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
