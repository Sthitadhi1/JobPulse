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
  checkAuthState();
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

  // Auth Screen Tabs
  if (tabLogin && tabSignup) {
    tabLogin.addEventListener('click', () => {
      tabLogin.classList.add('active');
      tabSignup.classList.remove('active');
      loginForm.classList.remove('hidden');
      signupForm.classList.add('hidden');
    });

    tabSignup.addEventListener('click', () => {
      tabSignup.classList.add('active');
      tabLogin.classList.remove('active');
      signupForm.classList.remove('hidden');
      loginForm.classList.add('hidden');
    });
  }

  if (forgotLink) {
    forgotLink.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('forgot-password-modal')?.classList.remove('hidden');
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

async function checkAuthState() {
  const authScreen = document.getElementById('auth-screen');
  const appWorkspace = document.getElementById('app-workspace');

  try {
    const res = await fetch(`${API_BASE}/auth/me`);
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        currentUser = data.user;
        updateHeaderUserUI(data.user);
        
        authScreen?.classList.add('hidden');
        appWorkspace?.classList.remove('hidden');

        // Render default landing view post-login: Dashboard Command Center
        switchTab('dashboard');
        return;
      }
    }
  } catch (err) {
    console.warn('Auth check warning:', err);
  }

  // Unauthenticated -> Show Auth Screen
  currentUser = null;
  authScreen?.classList.remove('hidden');
  appWorkspace?.classList.add('hidden');
}

function updateHeaderUserUI(user) {
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
}

async function handleLogout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    showToast('Logged out successfully.', 'info');
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    currentUser = null;
    document.getElementById('auth-screen')?.classList.remove('hidden');
    document.getElementById('app-workspace')?.classList.add('hidden');
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

  // Switch tab via links (e.g. data-switch-tab="resume-match")
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

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleResumeFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleResumeFileSelect(fileInput.files[0]);
      }
    });
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => {
      if (selectedResumeFile) {
        processResumeAnalysis(selectedResumeFile);
      } else {
        // Switch to resume match tab directly
        switchTab('resume-match');
      }
    });
  }
}

function handleResumeFileSelect(file) {
  selectedResumeFile = file;
  const badge = document.getElementById('dashboard-file-badge');
  if (badge) {
    badge.textContent = `📄 Selected File: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
    badge.classList.remove('hidden');
  }
}

async function loadDashboardOverview() {
  const greetingEl = document.getElementById('dashboard-user-greeting');
  const activeJobsEl = document.getElementById('dash-stat-active-jobs');
  const topMatchesEl = document.getElementById('dash-stat-top-matches');
  const applicationsEl = document.getElementById('dash-stat-applications');
  const bookmarkedEl = document.getElementById('dash-stat-bookmarked');

  const previewContainer = document.getElementById('dashboard-top-matches-preview-container');

  // Pipeline counts
  const pipeSaved = document.getElementById('dash-pipe-saved');
  const pipeApplied = document.getElementById('dash-pipe-applied');
  const pipeOa = document.getElementById('dash-pipe-oa');
  const pipeInterview = document.getElementById('dash-pipe-interview');
  const pipeOffer = document.getElementById('dash-pipe-offer');

  try {
    const res = await fetch(`${API_BASE}/dashboard/overview`);
    if (res.ok) {
      const data = await res.json();

      if (greetingEl && data.user_name) {
        const hour = new Date().getHours();
        const timeGreeting = hour < 12 ? 'Good morning' : (hour < 17 ? 'Good afternoon' : 'Good evening');
        greetingEl.textContent = `${timeGreeting}, ${data.user_name} 👋`;
      }

      if (data.overview) {
        if (activeJobsEl) activeJobsEl.textContent = (data.overview.active_jobs || 0).toLocaleString();
        if (topMatchesEl) topMatchesEl.textContent = (data.overview.top_matches || 0).toLocaleString();
        if (applicationsEl) applicationsEl.textContent = (data.overview.applications || 0).toLocaleString();
        if (bookmarkedEl) bookmarkedEl.textContent = (data.overview.bookmarked_jobs || 0).toLocaleString();
      }

      if (data.pipeline) {
        if (pipeSaved) pipeSaved.textContent = data.pipeline.saved || 0;
        if (pipeApplied) pipeApplied.textContent = data.pipeline.applied || 0;
        if (pipeOa) pipeOa.textContent = data.pipeline.oa_test || 0;
        if (pipeInterview) pipeInterview.textContent = data.pipeline.interview || 0;
        if (pipeOffer) pipeOffer.textContent = data.pipeline.offer || 0;
      }

      // Render Top Matches Preview
      if (previewContainer) {
        if (data.top_matches_preview && data.top_matches_preview.length > 0) {
          previewContainer.innerHTML = data.top_matches_preview.map(j => `
            <div class="top-match-item">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div class="company-avatar">${(j.company || 'C').charAt(0)}</div>
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
  showToast('Parsing resume & extracting skills...', 'info');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/ai/upload-resume`, {
      method: 'POST',
      body: formData
    });

    const result = await res.json();
    if (res.ok && result.success) {
      showToast(`Resume analyzed! Found ${result.total_recommendations} top matching jobs.`, 'success');
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
    const res = await fetch(`${API_BASE}/ai/recommendations`);
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
    const skillsList = profile.skills ? profile.skills.slice(0, 8).map(s => `<span class="tag">${escapeHtml(s)}</span>`).join(' ') : '';
    summaryEl.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="font-weight: 700; font-size: 16px;">👤 Profile: ${escapeHtml(profile.name || 'Candidate')}</div>
          <div class="text-xs text-muted mt-1">${escapeHtml(profile.degree || '')} • ${escapeHtml(profile.experience_level || 'Fresher')}</div>
          <div class="skills-row mt-2">${skillsList}</div>
        </div>
        <div class="badge badge-pulse" style="font-size: 12px; padding: 6px 12px;">
          🎯 ${recommendations ? recommendations.length : 0} Active Opportunities Matched
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
    ? j.matching_skills.slice(0, 5).map(s => `<span class="skill-tag-matched">✓ ${escapeHtml(s)}</span>`).join('')
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
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.role_alignment || 90}%;"></div></div>
            <span class="text-xs font-semibold">${b.role_alignment || 90}%</span>
          </div>
          <div class="score-progress-row">
            <span class="text-xs text-muted">Experience</span>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width: ${b.experience_match || 85}%;"></div></div>
            <span class="text-xs font-semibold">${b.experience_match || 85}%</span>
          </div>

          <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-color);">
            <div style="font-weight: 600; color: #10b981; font-size: 12px; margin-bottom: 2px;">Why you're a strong candidate:</div>
            <div class="text-xs text-secondary mb-2">${escapeHtml(j.why_matches || '')}</div>
            <div style="font-weight: 600; color: #f59e0b; font-size: 12px; margin-bottom: 2px;">Potential gap:</div>
            <div class="text-xs text-muted">${escapeHtml(j.potential_gap || '')}</div>
          </div>
        </div>
      </div>

      <div class="job-card-footer">
        <span class="posted-date">Source: ${escapeHtml(j.source || 'ATS')}</span>
        <div class="action-buttons">
          <button class="btn btn-sm btn-ghost" onclick="openJobDetailModal(${j.job_id || j.id})">Details</button>
          <button class="btn btn-sm btn-outline" onclick="trackJobInKanban(${j.job_id || j.id}, '${escapeJs(j.title)}', '${escapeJs(j.company)}')">Track</button>
          ${isClosed ? `
            <button class="btn btn-sm btn-disabled" disabled>Job Closed</button>
          ` : `
            <a href="${j.apply_url || j.job_url}" target="_blank" class="btn btn-sm btn-primary">Apply ↗</a>
          `}
        </div>
      </div>
    </div>
  `;
}

function toggleAccordion(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden');
}

/* ==========================================================================
   6. DISCOVER JOBS & FILTERS (CLOSED JOB BADGES)
   ========================================================================== */
function initSearchAndFilters() {
  const searchInput = document.getElementById('job-search-input');
  const searchBtn = document.getElementById('run-search-btn');

  const expSelect = document.getElementById('filter-exp');
  const remoteSelect = document.getElementById('filter-remote');
  const salarySelect = document.getElementById('filter-salary');
  const bookmarkedBtn = document.getElementById('bookmarked-only-btn');
  const chips = document.querySelectorAll('.salary-chip');

  if (searchBtn) {
    searchBtn.addEventListener('click', () => loadJobsFeed(true));
  }

  if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') loadJobsFeed(true);
    });
  }

  [expSelect, remoteSelect, salarySelect].forEach(select => {
    select?.addEventListener('change', () => loadJobsFeed(true));
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedSalaryMin = chip.getAttribute('data-min') || null;
      selectedSalaryMax = chip.getAttribute('data-max') || null;
      loadJobsFeed(true);
    });
  });

  if (bookmarkedBtn) {
    bookmarkedBtn.addEventListener('click', () => {
      isBookmarkedOnlyFilter = !isBookmarkedOnlyFilter;
      bookmarkedBtn.classList.toggle('btn-primary', isBookmarkedOnlyFilter);
      bookmarkedBtn.classList.toggle('btn-ghost', !isBookmarkedOnlyFilter);
      loadJobsFeed(true);
    });
  }
}

async function loadJobsFeed(reset = true) {
  const container = document.getElementById('jobs-container');
  const loadMoreBtn = document.getElementById('load-more-btn');
  const loadMoreSpinner = document.getElementById('load-more-spinner');

  if (!container) return;

  if (reset) {
    currentFeedPage = 1;
    currentJobs = [];
    container.innerHTML = '<div class="loading-skeleton">Searching live opportunities...</div>';
  }

  const q = document.getElementById('job-search-input')?.value.trim() || '';
  const exp = document.getElementById('filter-exp')?.value || '';
  const remote = document.getElementById('filter-remote')?.value || '';
  const minSal = selectedSalaryMin || document.getElementById('filter-salary')?.value || '';
  const maxSal = selectedSalaryMax || '';

  let url = `${API_BASE}/jobs/search?page=${currentFeedPage}&limit=30`;
  if (q) url += `&keyword=${encodeURIComponent(q)}`;
  if (exp) url += `&experience_level=${encodeURIComponent(exp)}`;
  if (remote) url += `&remote_type=${encodeURIComponent(remote)}`;
  if (minSal) url += `&salary_min=${encodeURIComponent(minSal)}`;
  if (maxSal) url += `&salary_max=${encodeURIComponent(maxSal)}`;
  if (isBookmarkedOnlyFilter) url += `&bookmarked_only=true`;

  isLoadingMoreFeed = true;
  if (loadMoreSpinner) loadMoreSpinner.classList.remove('hidden');

  try {
    const res = await fetch(url);
    const result = await res.json();

    if (result.success && result.data) {
      if (reset) {
        currentJobs = result.data;
      } else {
        currentJobs = currentJobs.concat(result.data);
      }

      totalFeedRecords = result.meta.total_records || currentJobs.length;
      totalFeedPages = result.meta.total_pages || 1;

      renderJobsGrid(container, currentJobs);

      const countBadge = document.getElementById('job-count-badge');
      if (countBadge) {
        countBadge.textContent = `Showing 1–${currentJobs.length} of ${totalFeedRecords} active jobs`;
      }

      if (loadMoreBtn) {
        if (currentFeedPage < totalFeedPages) {
          loadMoreBtn.classList.remove('hidden');
          loadMoreBtn.textContent = `📥 Load More Jobs (${totalFeedRecords - currentJobs.length} remaining)`;
        } else {
          loadMoreBtn.classList.add('hidden');
        }
      }
    }
  } catch (err) {
    if (reset) {
      container.innerHTML = `<div class="card card-padded text-muted">Error loading jobs feed: ${err.message}</div>`;
    }
  } finally {
    isLoadingMoreFeed = false;
    if (loadMoreSpinner) loadMoreSpinner.classList.add('hidden');
  }
}

function renderJobsGrid(container, jobs) {
  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<div class="card card-padded text-muted">No matching active jobs found. Try adjusting your search filters.</div>';
    return;
  }

  container.innerHTML = jobs.map(j => renderStandardJobCard(j)).join('');
}

function renderStandardJobCard(j) {
  const isClosed = j.status === 'CLOSED' || j.status === 'REMOVED';
  const statusBadgeClass = isClosed ? 'badge-status-closed' : (j.status === 'ACTIVE' ? 'badge-status-active' : 'badge-status-unknown');
  const statusLabel = isClosed ? '🔴 CLOSED' : (j.status === 'ACTIVE' ? '🟢 ACTIVE' : '🟡 UNVERIFIED');

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
        <span class="badge ${statusBadgeClass}">${statusLabel}</span>
        <span class="detail-item">📍 ${escapeHtml(j.location || 'India')}</span>
        <span class="detail-item">🌐 ${escapeHtml(j.remote_type || 'Hybrid')}</span>
        <span class="detail-item">💼 ${escapeHtml(j.experience_level || 'Fresher')}</span>
        ${j.salary_range ? `<span class="detail-item" style="color: #10b981;">💰 ${escapeHtml(j.salary_range)}</span>` : ''}
      </div>

      <div class="job-tags mt-2">
        ${(j.tags || []).slice(0, 4).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
      </div>

      <div class="job-card-footer">
        <span class="posted-date">Source: ${escapeHtml(j.source || 'ATS')}</span>
        <div class="action-buttons">
          <button class="btn btn-sm btn-ghost" onclick="openJobDetailModal(${j.id})">Details</button>
          <button class="btn btn-sm btn-outline" onclick="trackJobInKanban(${j.id}, '${escapeJs(j.title)}', '${escapeJs(j.company)}')">Track</button>
          ${isClosed ? `
            <button class="btn btn-sm btn-disabled" disabled>Job Closed</button>
          ` : `
            <a href="${j.url || j.job_url}" target="_blank" class="btn btn-sm btn-primary">Apply ↗</a>
          `}
        </div>
      </div>
    </div>
  `;
}

function initInfiniteScroll() {
  const contentArea = document.querySelector('.content-area');
  const loadMoreBtn = document.getElementById('load-more-btn');

  loadMoreBtn?.addEventListener('click', () => loadNextFeedPage());

  if (contentArea) {
    contentArea.addEventListener('scroll', () => {
      const activeTab = document.querySelector('.tab-pane.active');
      if (!activeTab || activeTab.id !== 'tab-jobs') return;

      const scrollPosition = contentArea.scrollTop + contentArea.clientHeight;
      const scrollThreshold = contentArea.scrollHeight - 300;

      if (scrollPosition >= scrollThreshold && !isLoadingMoreFeed && currentFeedPage < totalFeedPages) {
        loadNextFeedPage();
      }
    });
  }
}

async function loadNextFeedPage() {
  if (isLoadingMoreFeed || currentFeedPage >= totalFeedPages) return;
  currentFeedPage++;
  await loadJobsFeed(false);
}

/* ==========================================================================
   7. APPLICATION KANBAN WORKSPACE
   ========================================================================== */
function initApplicationWorkspaceEvents() {
  const addBtn = document.getElementById('add-custom-application-btn');
  const exportBtn = document.getElementById('export-applications-btn');
  const csvInput = document.getElementById('csv-file-input');

  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      window.open(`${API_BASE}/applications/export`, '_blank');
    });
  }

  if (csvInput) {
    csvInput.addEventListener('change', async () => {
      if (!csvInput.files || csvInput.files.length === 0) return;
      const formData = new FormData();
      formData.append('file', csvInput.files[0]);

      try {
        const res = await fetch(`${API_BASE}/applications/import`, {
          method: 'POST',
          body: formData
        });
        const result = await res.json();
        if (res.ok && result.success) {
          showToast(`Imported ${result.imported_count} applications!`, 'success');
          loadApplicationWorkspace();
        }
      } catch (err) {
        showToast('Error importing CSV: ' + err.message, 'error');
      }
    });
  }
}

async function loadApplicationWorkspace() {
  const container = document.getElementById('kanban-board-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading Application Kanban...</div>';

  try {
    const res = await fetch(`${API_BASE}/applications`);
    const result = await res.json();

    if (result.success && result.data) {
      renderKanbanBoard(container, result.data);
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading applications: ${err.message}</div>`;
  }
}

function renderKanbanBoard(container, applications) {
  const columns = ['Saved', 'Applied', 'OA / Test', 'Interview', 'Offer', 'Rejected'];
  
  const grouped = {};
  columns.forEach(col => grouped[col] = []);

  applications.forEach(app => {
    const status = app.status || 'Saved';
    if (grouped[status]) {
      grouped[status].push(app);
    } else {
      grouped['Saved'].push(app);
    }
  });

  container.innerHTML = columns.map(col => `
    <div class="kanban-column" data-column="${escapeHtml(col)}">
      <div class="kanban-header">
        <span class="kanban-title">${escapeHtml(col)}</span>
        <span class="badge badge-outline">${grouped[col].length}</span>
      </div>
      <div class="kanban-cards-wrapper" style="display: flex; flex-direction: column; gap: 10px; flex: 1;">
        ${grouped[col].length === 0 ? '<div class="text-xs text-muted" style="padding: 12px; text-align: center;">No items</div>' : ''}
        ${grouped[col].map(a => `
          <div class="kanban-card">
            <div style="font-weight: 700; font-size: 14px;">${escapeHtml(a.company)}</div>
            <div class="text-xs text-secondary">${escapeHtml(a.role)}</div>
            <div class="text-xs text-muted" style="display: flex; justify-content: space-between; margin-top: 4px;">
              <span>${a.applied_date ? new Date(a.applied_date).toLocaleDateString() : 'Tracked'}</span>
              <span class="badge badge-outline" style="font-size: 10px;">${escapeHtml(a.source || 'JobPulse')}</span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

async function trackJobInKanban(jobId, title, company) {
  try {
    const res = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: company,
        role: title,
        source: 'JobPulse Discovery',
        status: 'Applied'
      })
    });
    const result = await res.json();
    if (res.ok && result.success) {
      showToast(`Added ${company} — ${title} to Application Kanban!`, 'success');
      loadDashboardOverview();
    }
  } catch (err) {
    showToast('Error tracking job: ' + err.message, 'error');
  }
}

/* ==========================================================================
   8. BOOKMARKS & SAVED SEARCHES
   ========================================================================== */
async function toggleBookmark(jobId, btnElement) {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/bookmark`, { method: 'POST' });
    const result = await res.json();
    if (res.ok && result.success) {
      const isBookmarked = result.data.is_bookmarked;
      if (btnElement) {
        btnElement.classList.toggle('bookmarked', isBookmarked);
        btnElement.textContent = isBookmarked ? '★' : '☆';
      }
      showToast(isBookmarked ? 'Saved to Bookmarks!' : 'Removed from Bookmarks', 'info');
    }
  } catch (err) {
    showToast('Error toggling bookmark: ' + err.message, 'error');
  }
}

async function loadBookmarksFeed() {
  const container = document.getElementById('bookmarks-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading bookmarked opportunities...</div>';

  try {
    const res = await fetch(`${API_BASE}/jobs?bookmarked_only=true&limit=100`);
    const result = await res.json();
    if (result.success) {
      renderJobsGrid(container, result.data);
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading bookmarks: ${err.message}</div>`;
  }
}

async function loadSavedSearches() {
  const container = document.getElementById('searches-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-skeleton">Loading saved search rules...</div>';

  try {
    const res = await fetch(`${API_BASE}/search/saved`);
    const result = await res.json();

    if (result.success && result.data) {
      if (result.data.length === 0) {
        container.innerHTML = '<div class="card card-padded text-muted">No active search alert rules created yet.</div>';
        return;
      }

      container.innerHTML = `
        <table class="table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-size: 12px;">
              <th style="padding: 10px;">Rule Name</th>
              <th style="padding: 10px;">Keywords</th>
              <th style="padding: 10px;">Status</th>
              <th style="padding: 10px;">Telegram Recipient</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(s => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 13px;">
                <td style="padding: 12px; font-weight: 600;">${escapeHtml(s.name)}</td>
                <td style="padding: 12px; color: var(--accent-blue);">${escapeHtml(s.keywords || s.query || 'All Jobs')}</td>
                <td style="padding: 12px;"><span class="badge badge-pulse">${s.is_active ? 'ACTIVE' : 'PAUSED'}</span></td>
                <td style="padding: 12px; font-family: var(--font-mono);">${escapeHtml(s.telegram_chat_id || 'Default')}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading search rules: ${err.message}</div>`;
  }
}

/* ==========================================================================
   9. ANALYTICS & CONNECTORS
   ========================================================================== */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
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
    const res = await fetch(`${API_BASE}/admin/connectors`);
    const result = await res.json();

    if (result.success && result.data) {
      container.innerHTML = `
        <table class="table" style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-size: 12px;">
              <th style="padding: 10px;">Connector Name</th>
              <th style="padding: 10px;">Type</th>
              <th style="padding: 10px;">Status</th>
              <th style="padding: 10px;">Total Jobs</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(c => `
              <tr style="border-bottom: 1px solid var(--border-color); font-size: 13px;">
                <td style="padding: 12px; font-weight: 600;">${escapeHtml(c.name)}</td>
                <td style="padding: 12px;"><span class="badge badge-source-ats">${escapeHtml(c.source_type || 'ATS')}</span></td>
                <td style="padding: 12px;"><span class="badge badge-pulse">HEALTHY</span></td>
                <td style="padding: 12px; font-weight: 700;">${c.discovered_count || 0}</td>
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
  showToast('Triggering source synchronization across connectors...', 'info');
  try {
    const res = await fetch(`${API_BASE}/admin/connectors/sync`, { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      showToast('Synchronization cycle completed successfully!', 'success');
      loadDashboardOverview();
      loadJobsFeed(true);
    }
  } catch (err) {
    showToast('Sync error: ' + err.message, 'error');
  }
}

/* ==========================================================================
   10. ACCOUNT PROFILE & MODALS
   ========================================================================== */
function loadProfile() {
  if (currentUser) {
    document.getElementById('profile-name-field').value = currentUser.name || '';
    document.getElementById('profile-email-field').value = currentUser.email || '';
  }
}

function initModals() {
  document.getElementById('close-modal-btn')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.add('hidden');
  });

  document.getElementById('cancel-save-search')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.add('hidden');
  });

  document.getElementById('save-current-search-btn')?.addEventListener('click', () => {
    document.getElementById('save-search-modal')?.classList.remove('hidden');
  });

  document.getElementById('confirm-save-search')?.addEventListener('click', async () => {
    const name = document.getElementById('modal-search-name').value.trim();
    const query = document.getElementById('modal-search-query').value.trim();

    if (!name) {
      showToast('Alert rule name is required.', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/search/saved`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, query, keywords: query })
      });
      const result = await res.json();
      if (res.ok && result.success) {
        showToast('Saved search alert created!', 'success');
        document.getElementById('save-search-modal')?.classList.add('hidden');
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
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (res.ok) {
      const result = await res.json();
      const j = result.data;

      titleEl.textContent = `${j.company} — ${j.title}`;

      const isClosed = !j.is_active_opportunity;
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
   11. TELEGRAM VIEW & UTILS
   ========================================================================== */
function initTelegramView() {
  document.getElementById('generate-tg-token-btn')?.addEventListener('click', async () => {
    const display = document.getElementById('telegram-token-display');
    try {
      const res = await fetch(`${API_BASE}/notifications/telegram/token`, { method: 'POST' });
      const result = await res.json();
      if (result.success) {
        display.classList.remove('hidden');
        display.innerHTML = `<div class="alert alert-success">Your Token: <code>${result.token}</code><br>Send <code>/link ${result.token}</code> to our Telegram Bot.</div>`;
      }
    } catch (err) {
      showToast('Error generating token: ' + err.message, 'error');
    }
  });
}

function initSpotlightEffect() {
  document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.job-card, .bento-card, .kanban-card, .overview-card');
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
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000; display: flex; flex-direction: column; gap: 8px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#3b82f6');
  toast.style.cssText = `background: ${bg}; color: #fff; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.3); animation: fadeInUp 0.2s ease;`;
  toast.textContent = message;

  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
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

function escapeJs(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}
