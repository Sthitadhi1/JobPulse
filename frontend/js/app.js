const API_BASE = '/api/v1';

let currentJobs = [];
let isBookmarkedOnlyFilter = false;

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initCommandPalette();
  initSearchAndFilters();
  initModals();
  initTelegramView();
  
  // Initial data load
  loadJobsFeed();
  loadAnalytics();
});

/* THEME TOGGLE */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  const htmlEl = document.documentElement;

  toggleBtn.addEventListener('click', () => {
    const currentTheme = htmlEl.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    htmlEl.setAttribute('data-theme', newTheme);
    toggleBtn.textContent = newTheme === 'dark' ? '🌙' : '☀️';
  });
}

/* NAVIGATION & TAB SWITCHING */
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tabTarget = item.getAttribute('data-tab');

      navItems.forEach(n => n.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      item.classList.add('active');
      const targetPane = document.getElementById(`tab-${tabTarget}`);
      if (targetPane) targetPane.classList.add('active');

      // Load tab-specific data
      if (tabTarget === 'jobs') loadJobsFeed();
      if (tabTarget === 'searches') loadSavedSearches();
      if (tabTarget === 'bookmarks') loadBookmarksFeed();
      if (tabTarget === 'analytics') loadAnalytics();
      if (tabTarget === 'connectors') loadConnectorHealth();
    });
  });

  // Sync button in header & connector panel
  document.getElementById('sync-now-btn')?.addEventListener('click', triggerManualSync);
  document.getElementById('trigger-sync-panel-btn')?.addEventListener('click', triggerManualSync);
}

/* JOBS FEED & API FETCHING */
async function loadJobsFeed() {
  const container = document.getElementById('jobs-container');
  const q = document.getElementById('job-search-input').value.trim();
  const exp = document.getElementById('filter-exp').value;
  const remote = document.getElementById('filter-remote').value;
  const minSal = document.getElementById('filter-salary').value;

  let url = `${API_BASE}/jobs?limit=50&india_or_remote_only=true`;
  if (q) url += `&q=${encodeURIComponent(q)}`;
  if (exp) url += `&experience_level=${encodeURIComponent(exp)}`;
  if (remote) url += `&remote_type=${encodeURIComponent(remote)}`;
  if (minSal) url += `&min_salary_lpa=${encodeURIComponent(minSal)}`;
  if (isBookmarkedOnlyFilter) url += `&bookmarked_only=true`;

  container.innerHTML = '<div class="loading-skeleton">Loading live discovery feed...</div>';

  try {
    const res = await fetch(url);
    const result = await res.json();

    if (result.success && result.data) {
      currentJobs = result.data;
      renderJobsGrid(container, currentJobs);
      document.getElementById('job-count-badge').textContent = `${result.meta.total_records} jobs found`;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading jobs feed: ${err.message}</div>`;
  }
}

function renderJobsGrid(container, jobs) {
  if (!jobs || jobs.length === 0) {
    container.innerHTML = `
      <div class="card card-padded text-center">
        <h3>No matching jobs found</h3>
        <p class="text-muted">Try adjusting your Boolean keywords, salary, or experience level filters.</p>
      </div>`;
    return;
  }

  container.innerHTML = jobs.map(job => `
    <div class="job-card" data-id="${job.id}">
      <div>
        <div class="job-card-header">
          <span class="job-company">${escapeHtml(job.company)}</span>
          <button class="btn btn-sm btn-ghost bookmark-btn" onclick="toggleBookmark(${job.id})">
            ${job.is_bookmarked ? '⭐ Bookmarked' : '☆ Bookmark'}
          </button>
        </div>
        <h3 class="job-title">${escapeHtml(job.title)}</h3>
        <p class="text-muted text-sm mt-1">📍 ${escapeHtml(job.location)}</p>

        <div class="job-meta-pills mt-3">
          <span class="pill pill-salary">${job.salary_range || 'Disclosed'}</span>
          <span class="pill pill-exp">${job.experience_level}</span>
          <span class="pill">${job.remote_type}</span>
          <span class="pill">${job.employment_type}</span>
        </div>
      </div>

      <div>
        <p class="text-sm text-muted line-clamp-2 mt-2">${escapeHtml(job.description || '')}</p>
        <div class="job-card-footer mt-3">
          <span class="source-tag">Source: ${job.source}</span>
          <div class="btn-actions">
            <a href="${job.url}" target="_blank" class="btn btn-sm btn-primary">Apply Official Site ↗</a>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

/* BOOKMARKS TOGGLE */
async function toggleBookmark(jobId) {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/bookmark`, { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      loadJobsFeed();
    }
  } catch (err) {
    console.error('Bookmark error:', err);
  }
}

async function loadBookmarksFeed() {
  isBookmarkedOnlyFilter = true;
  const container = document.getElementById('bookmarks-container');
  container.innerHTML = '<div class="loading-skeleton">Loading bookmarks...</div>';

  try {
    const res = await fetch(`${API_BASE}/jobs?bookmarked_only=true`);
    const result = await res.json();
    if (result.success) {
      renderJobsGrid(container, result.data);
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded">Error loading bookmarks.</div>`;
  } finally {
    isBookmarkedOnlyFilter = false;
  }
}

/* SAVED SEARCHES */
async function loadSavedSearches() {
  const container = document.getElementById('searches-container');
  container.innerHTML = '<div class="loading-skeleton">Loading saved search rules...</div>';

  try {
    const res = await fetch(`${API_BASE}/search/saved`);
    const result = await res.json();

    if (result.success && result.data) {
      if (result.data.length === 0) {
        container.innerHTML = `<div class="card card-padded text-muted">No saved search alerts created yet. Create one to receive automatic Telegram notifications!</div>`;
        return;
      }

      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Alert Name</th>
              <th>Keywords / Query</th>
              <th>Location</th>
              <th>Min Salary</th>
              <th>Exp Level</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(s => `
              <tr>
                <td><strong>${escapeHtml(s.name)}</strong></td>
                <td><code>${escapeHtml(s.query || s.keywords || 'All')}</code></td>
                <td>${s.location || 'Any'}</td>
                <td>${s.min_salary_lpa ? '₹' + s.min_salary_lpa + ' LPA' : 'Any'}</td>
                <td>${s.experience_level || 'All'}</td>
                <td>
                  <span class="badge ${s.is_active ? 'badge-pulse' : ''}">
                    ${s.is_active ? 'ACTIVE' : 'PAUSED'}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-outline" onclick="toggleSearchRule(${s.id})">
                    ${s.is_active ? 'Pause' : 'Activate'}
                  </button>
                  <button class="btn btn-sm btn-ghost" onclick="deleteSearchRule(${s.id})">Delete</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded">Failed to load saved searches.</div>`;
  }
}

async function toggleSearchRule(id) {
  await fetch(`${API_BASE}/search/saved/${id}/toggle`, { method: 'PATCH' });
  loadSavedSearches();
}

async function deleteSearchRule(id) {
  if (confirm('Delete this saved search alert?')) {
    await fetch(`${API_BASE}/search/saved/${id}`, { method: 'DELETE' });
    loadSavedSearches();
  }
}

/* ANALYTICS */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    const result = await res.json();

    if (result.success && result.data) {
      const d = result.data;
      document.getElementById('stat-jobs-today').textContent = d.jobs_discovered_today || 0;
      document.getElementById('stat-searches').textContent = d.active_saved_searches || 0;
      document.getElementById('stat-notifs').textContent = d.notifications_sent || 0;
      document.getElementById('stat-companies').textContent = d.companies_tracked || 0;

      const topList = document.getElementById('top-companies-list');
      if (topList && d.top_hiring_companies) {
        topList.innerHTML = d.top_hiring_companies.map(c => `
          <li style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color)">
            <span>🏢 ${escapeHtml(c.company)}</span>
            <strong>${c.count} active roles</strong>
          </li>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Analytics error:', err);
  }
}

/* CONNECTOR HEALTH & SYNC */
async function loadConnectorHealth() {
  const container = document.getElementById('connectors-container');
  container.innerHTML = '<div class="loading-skeleton">Loading connector diagnostics...</div>';

  try {
    const res = await fetch(`${API_BASE}/admin/connectors`);
    const result = await res.json();

    if (result.success && result.data) {
      container.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Connector Name</th>
              <th>Source Type</th>
              <th>Status</th>
              <th>Jobs Last Run</th>
              <th>Total Indexed</th>
              <th>Avg Runtime</th>
              <th>Last Run</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(c => `
              <tr>
                <td><strong>${escapeHtml(c.name)}</strong></td>
                <td>${c.source_type}</td>
                <td><span class="badge badge-pulse">${c.status}</span></td>
                <td>${c.jobs_found_last_run}</td>
                <td>${c.total_jobs_indexed}</td>
                <td>${c.average_runtime_ms} ms</td>
                <td>${c.last_run ? new Date(c.last_run).toLocaleTimeString() : 'Never'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded">Failed to load connectors health.</div>`;
  }
}

async function triggerManualSync() {
  const syncBtn = document.getElementById('sync-now-btn');
  if (syncBtn) syncBtn.textContent = '🔄 Syncing...';

  try {
    const res = await fetch(`${API_BASE}/admin/connectors/sync`, { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      loadJobsFeed();
      loadAnalytics();
      alert(`Sync Complete! Discovered ${result.data.new_unique_jobs_added} new roles across connectors.`);
    }
  } catch (err) {
    alert('Sync error: ' + err.message);
  } finally {
    if (syncBtn) syncBtn.textContent = '🔄 Sync Sources';
  }
}

/* TELEGRAM TEST VIEW */
function initTelegramView() {
  const btn = document.getElementById('send-telegram-test-btn');
  const chatInput = document.getElementById('telegram-chat-id-input');
  const resultAlert = document.getElementById('telegram-test-result');

  btn.addEventListener('click', async () => {
    const chatId = chatInput.value.trim();
    if (!chatId) return;

    btn.textContent = 'Sending...';
    try {
      const res = await fetch(`${API_BASE}/notifications/telegram/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId })
      });
      const result = await res.json();
      resultAlert.classList.remove('hidden');
      resultAlert.textContent = result.message + ' (Check backend terminal for simulated dispatch logs).';
    } catch (err) {
      resultAlert.classList.remove('hidden');
      resultAlert.textContent = 'Dispatch failed: ' + err.message;
    } finally {
      btn.textContent = '⚡ Send Test Alert';
    }
  });
}

/* SEARCH & FILTERS CONTROLS */
function initSearchAndFilters() {
  document.getElementById('run-search-btn').addEventListener('click', () => loadJobsFeed());
  document.getElementById('filter-exp').addEventListener('change', () => loadJobsFeed());
  document.getElementById('filter-remote').addEventListener('change', () => loadJobsFeed());
  document.getElementById('filter-salary').addEventListener('change', () => loadJobsFeed());
  
  document.getElementById('bookmarked-only-btn').addEventListener('click', () => {
    isBookmarkedOnlyFilter = !isBookmarkedOnlyFilter;
    const btn = document.getElementById('bookmarked-only-btn');
    btn.classList.toggle('btn-primary', isBookmarkedOnlyFilter);
    loadJobsFeed();
  });
}

/* MODALS & COMMAND PALETTE */
function initModals() {
  const modal = document.getElementById('save-search-modal');
  const openBtn = document.getElementById('save-current-search-btn');
  const openModalBtn = document.getElementById('create-search-modal-btn');
  const closeBtn = document.getElementById('close-modal-btn');
  const cancelBtn = document.getElementById('cancel-save-search');
  const confirmBtn = document.getElementById('confirm-save-search');

  const closeModal = () => modal.classList.add('hidden');
  const openModal = () => {
    const currentQ = document.getElementById('job-search-input').value;
    document.getElementById('modal-search-name').value = currentQ ? `Alert: ${currentQ}` : 'New SDE Alert';
    document.getElementById('modal-search-query').value = currentQ || 'Software Engineer';
    modal.classList.remove('hidden');
  };

  openBtn?.addEventListener('click', openModal);
  openModalBtn?.addEventListener('click', openModal);
  closeBtn?.addEventListener('click', closeModal);
  cancelBtn?.addEventListener('click', closeModal);

  confirmBtn.addEventListener('click', async () => {
    const name = document.getElementById('modal-search-name').value;
    const query = document.getElementById('modal-search-query').value;
    const loc = document.getElementById('modal-search-location').value;
    const sal = document.getElementById('modal-search-salary').value;

    if (!name) return alert('Please enter an alert name.');

    try {
      const res = await fetch(`${API_BASE}/search/saved`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          query: query,
          location: loc,
          min_salary_lpa: sal ? parseFloat(sal) : null,
          experience_level: "Fresh Graduate"
        })
      });
      const result = await res.json();
      if (result.success) {
        closeModal();
        alert('Saved search alert created successfully!');
      }
    } catch (err) {
      alert('Error saving search rule: ' + err.message);
    }
  });
}

function initCommandPalette() {
  const modal = document.getElementById('cmd-k-modal');
  const triggerBtn = document.getElementById('cmd-k-btn');
  const input = document.getElementById('cmd-k-input');

  const toggleCmdK = () => modal.classList.toggle('hidden');

  triggerBtn.addEventListener('click', toggleCmdK);

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleCmdK();
    }
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      modal.classList.add('hidden');
    }
  });

  document.querySelectorAll('.cmd-k-item').forEach(item => {
    item.addEventListener('click', () => {
      const action = item.getAttribute('data-action');
      modal.classList.add('hidden');

      if (action === 'search-sde') {
        document.getElementById('job-search-input').value = 'Software Engineer';
        loadJobsFeed();
      } else if (action === 'search-ai') {
        document.getElementById('job-search-input').value = 'AI OR ML';
        loadJobsFeed();
      } else if (action === 'search-remote') {
        document.getElementById('filter-remote').value = 'Remote';
        loadJobsFeed();
      } else if (action === 'open-searches') {
        document.querySelector('[data-tab="searches"]').click();
      } else if (action === 'sync-now') {
        triggerManualSync();
      }
    });
  });
}

/* UTILS */
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
}
