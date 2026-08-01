const API_BASE = '/api/v1';

let currentJobs = [];
let isBookmarkedOnlyFilter = false;

let currentFeedPage = 1;
let totalFeedPages = 1;
let totalFeedRecords = 0;
let isLoadingMoreFeed = false;

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initCommandPalette();
  initSearchAndFilters();
  initModals();
  initTelegramView();
  initInfiniteScroll();
  
  // Initial data load
  loadJobsFeed(true);
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
      if (tabTarget === 'jobs') loadJobsFeed(true);
      if (tabTarget === 'searches') loadSavedSearches();
      if (tabTarget === 'bookmarks') loadBookmarksFeed();
      if (tabTarget === 'analytics') loadAnalytics();
      if (tabTarget === 'connectors') loadConnectorHealth();
    });
  });

  document.getElementById('sync-now-btn')?.addEventListener('click', triggerManualSync);
  document.getElementById('trigger-sync-panel-btn')?.addEventListener('click', triggerManualSync);
}

/* JOBS FEED & INFINITE SCROLL PAGINATION (BUG 1 FIX) */
async function loadJobsFeed(reset = true) {
  const container = document.getElementById('jobs-container');
  const loadMoreBtn = document.getElementById('load-more-btn');
  const loadMoreSpinner = document.getElementById('load-more-spinner');

  if (reset) {
    currentFeedPage = 1;
    currentJobs = [];
    container.innerHTML = '<div class="loading-skeleton">Loading live discovery feed...</div>';
  }

  const q = document.getElementById('job-search-input').value.trim();
  const exp = document.getElementById('filter-exp').value;
  const remote = document.getElementById('filter-remote').value;
  const minSal = document.getElementById('filter-salary').value;

  let url = `${API_BASE}/jobs?page=${currentFeedPage}&limit=30&india_or_remote_only=true`;
  if (q) url += `&q=${encodeURIComponent(q)}`;
  if (exp) url += `&experience_level=${encodeURIComponent(exp)}`;
  if (remote) url += `&remote_type=${encodeURIComponent(remote)}`;
  if (minSal) url += `&min_salary_lpa=${encodeURIComponent(minSal)}`;
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
        countBadge.textContent = `Showing 1–${currentJobs.length} of ${totalFeedRecords} jobs`;
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

async function loadNextFeedPage() {
  if (isLoadingMoreFeed || currentFeedPage >= totalFeedPages) return;
  currentFeedPage++;
  await loadJobsFeed(false);
}

function initInfiniteScroll() {
  const contentArea = document.querySelector('.content-area');

  const handleScroll = (targetEl) => {
    const activeTab = document.querySelector('.tab-pane.active');
    if (!activeTab || activeTab.id !== 'tab-jobs') return;

    const scrollBottom = targetEl.scrollHeight - (targetEl.scrollTop + targetEl.clientHeight);
    if (scrollBottom < 500) {
      loadNextFeedPage();
    }
  };

  if (contentArea) {
    contentArea.addEventListener('scroll', () => handleScroll(contentArea));
  }

  window.addEventListener('scroll', () => {
    const activeTab = document.querySelector('.tab-pane.active');
    if (!activeTab || activeTab.id !== 'tab-jobs') return;

    if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 500)) {
      loadNextFeedPage();
    }
  });

  const loadMoreBtn = document.getElementById('load-more-btn');
  loadMoreBtn?.addEventListener('click', loadNextFeedPage);
}

function renderJobsGrid(container, jobs) {
  if (!jobs || jobs.length === 0) {
    container.innerHTML = `
      <div class="card card-padded text-center">
        <h3>No matching jobs found</h3>
        <p class="text-muted">Try adjusting your search query, location, or experience level filters.</p>
      </div>`;
    return;
  }

  container.innerHTML = jobs.map(job => {
    // PART 10 — Smart Apply Links Priority:
    // external_apply_url -> job_url -> url. Never redirect to generic homepages.
    const applyTarget = job.external_apply_url || job.job_url || (job.url !== '#' ? job.url : null);
    
    // PART 9 — Verification Badge Indicator
    const vStatus = job.verification_status || 'VERIFIED';
    let vBadgeHtml = '<span class="badge badge-pulse" style="background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3);">🟢 Verified Today</span>';
    if (vStatus === 'PENDING') {
      vBadgeHtml = '<span class="badge" style="background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3);">🟡 Verification Pending</span>';
    } else if (vStatus === 'REMOVED_FROM_SOURCE' || job.status === 'REMOVED') {
      vBadgeHtml = '<span class="badge" style="background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);">🔴 Removed from Source</span>';
    }

    const sourceType = (job.source_type || 'ATS').toLowerCase();
    let badgeClass = 'badge-source-ats';
    if (sourceType.includes('board')) badgeClass = 'badge-source-board';
    if (sourceType.includes('company')) badgeClass = 'badge-source-company';

    const applyButtonHtml = applyTarget ? `
      <a href="${applyTarget}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-primary">
        Apply Listing ↗
      </a>` : `
      <button class="btn btn-sm btn-outline btn-disabled" disabled>
        Application link unavailable
      </button>`;

    const firstSeenDate = formatDate(job.first_seen || job.created_at);
    const lastVerifiedDate = formatDate(job.last_verified || job.created_at);

    return `
      <div class="job-card card">
        <div class="job-card-header">
          <div>
            <div class="company-row" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 4px;">
              <span class="company-name">${escapeHtml(job.company)}</span>
              <span class="badge-source ${badgeClass}">${job.source_type || 'ATS'}</span>
              ${vBadgeHtml}
            </div>
            <h3 class="job-title">${escapeHtml(job.title)}</h3>
          </div>
          <button class="bookmark-btn ${job.is_bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark(${job.id}, this)">
            ${job.is_bookmarked ? '⭐' : '☆'}
          </button>
        </div>

        <div class="job-details">
          <span class="detail-item">📍 ${escapeHtml(job.location)}</span>
          <span class="detail-item">🏠 ${escapeHtml(job.remote_type || 'Hybrid')}</span>
          <span class="detail-item">💼 ${escapeHtml(job.experience_level || 'Fresher')}</span>
          <span class="detail-item">💰 ${escapeHtml(job.salary_range || 'Disclosed on App')}</span>
        </div>

        <div class="job-tags">
          ${(job.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>

        <div class="job-card-footer">
          <small class="posted-date">Via ${escapeHtml(job.source)} • Seen: ${firstSeenDate} • Verified: ${lastVerifiedDate}</small>
          <div class="action-buttons">
            <button class="btn btn-sm btn-ghost" onclick="copyJobLink('${escapeHtml(applyTarget || '')}')" title="Copy listing URL">
              🔗 Share
            </button>
            ${applyButtonHtml}
          </div>
        </div>
      </div>
    `;
  }).join('');
}


function formatDate(isoStr) {
  if (!isoStr) return 'Recently';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}

function copyJobLink(url) {
  if (!url) return alert('Application URL unavailable.');
  navigator.clipboard.writeText(url);
  alert('Job link copied to clipboard!');
}

/* BOOKMARK TOGGLING */
async function toggleBookmark(jobId, btnEl) {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/bookmark`, { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      const isBookmarked = result.data.is_bookmarked;
      btnEl.classList.toggle('bookmarked', isBookmarked);
      btnEl.textContent = isBookmarked ? '⭐' : '☆';
    }
  } catch (err) {
    console.error('Bookmark error:', err);
  }
}

/* SAVED SEARCHES VIEW */
async function loadSavedSearches() {
  const container = document.getElementById('searches-container');
  container.innerHTML = '<div class="loading-skeleton">Loading saved search rules...</div>';

  try {
    const res = await fetch(`${API_BASE}/searches`);
    const result = await res.json();

    if (result.success && result.data) {
      if (result.data.length === 0) {
        container.innerHTML = `<div class="card card-padded text-center">No saved search alerts created yet.</div>`;
        return;
      }

      container.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Rule Name</th>
              <th>Query Keywords</th>
              <th>Location</th>
              <th>Exp Level</th>
              <th>Min Salary</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${result.data.map(s => `
              <tr>
                <td><strong>${escapeHtml(s.name)}</strong></td>
                <td><code>${escapeHtml(s.query || s.keywords || 'Any')}</code></td>
                <td>${escapeHtml(s.location || 'Any')}</td>
                <td>${escapeHtml(s.experience_level || 'Any')}</td>
                <td>${s.min_salary_lpa ? `₹${s.min_salary_lpa} LPA` : 'Any'}</td>
                <td><span class="badge badge-pulse">Active</span></td>
                <td>
                  <button class="btn btn-sm btn-outline" onclick="deleteSavedSearch(${s.id})">Delete</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading saved searches.</div>`;
  }
}

async function deleteSavedSearch(id) {
  if (!confirm('Delete this saved search rule?')) return;
  try {
    await fetch(`${API_BASE}/searches/${id}`, { method: 'DELETE' });
    loadSavedSearches();
  } catch (err) {
    alert('Delete error: ' + err.message);
  }
}

/* BOOKMARKS FEED VIEW */
async function loadBookmarksFeed() {
  const container = document.getElementById('jobs-container');
  isBookmarkedOnlyFilter = true;
  loadJobsFeed(true);
}

/* ANALYTICS VIEW */
async function loadAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    const result = await res.json();
    if (result.success && result.data) {
      const data = result.data;
      if (document.getElementById('stat-freshers-today')) document.getElementById('stat-freshers-today').textContent = data.freshers_jobs_today || 0;
      if (document.getElementById('stat-internships-today')) document.getElementById('stat-internships-today').textContent = data.internships_today || 0;
      if (document.getElementById('stat-mid-today')) document.getElementById('stat-mid-today').textContent = data.mid_level_jobs_today || 0;
      if (document.getElementById('stat-senior-today')) document.getElementById('stat-senior-today').textContent = data.senior_jobs_today || 0;
      if (document.getElementById('stat-verified-today')) document.getElementById('stat-verified-today').textContent = data.jobs_verified_today || 0;
      if (document.getElementById('stat-comp-freshers')) document.getElementById('stat-comp-freshers').textContent = data.companies_hiring_freshers || 0;
      if (document.getElementById('stat-verification-rate')) document.getElementById('stat-verification-rate').textContent = `${data.verification_success_rate || 100}%`;
      if (document.getElementById('stat-companies')) document.getElementById('stat-companies').textContent = data.companies_tracked || '300+';

      const topList = document.getElementById('top-companies-list');
      if (topList && data.most_active_companies) {
        topList.innerHTML = data.most_active_companies.map(c => `
          <li style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed var(--border-color);">
            <strong>${escapeHtml(c.company)}</strong>
            <span class="badge badge-outline">${c.count} active roles</span>
          </li>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Analytics error:', err);
  }
}

/* CONNECTOR HEALTH & DIAGNOSTICS VIEW */
async function loadConnectorHealth() {
  const container = document.getElementById('connectors-container');
  container.innerHTML = '<div class="loading-skeleton">Loading connector status...</div>';

  try {
    const res = await fetch(`${API_BASE}/admin/connectors`);
    const result = await res.json();

    if (result.success && result.data) {
      container.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Connector Name</th>
              <th>Source Type</th>
              <th>Health Status</th>
              <th>Success Rate</th>
              <th>Verification Rate</th>
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
                <td><span class="badge-source badge-source-${(c.source_type || 'ats').toLowerCase()}">${c.source_type}</span></td>
                <td><span class="badge ${c.health_score === 'HEALTHY' ? 'badge-pulse' : 'badge-danger'}">${c.health_score || c.status}</span></td>
                <td><strong>${c.success_rate || 100}%</strong></td>
                <td><strong>${c.verification_rate || 100}%</strong></td>
                <td>${c.jobs_found_last_run}</td>
                <td>${c.total_jobs_indexed}</td>
                <td><strong>${c.average_runtime_ms} ms</strong></td>
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
      loadJobsFeed(true);
      loadAnalytics();
      alert(`Sync Complete! Discovered ${result.data.new_unique_jobs_added} new roles across connectors.`);
    }
  } catch (err) {
    alert('Sync error: ' + err.message);
  } finally {
    if (syncBtn) syncBtn.textContent = '🔄 Sync Sources';
  }
}

/* TELEGRAM DEEP LINKING VIEW */
function initTelegramView() {
  const testBtn = document.getElementById('send-telegram-test-btn');
  const generateTokenBtn = document.getElementById('generate-tg-token-btn');
  const chatInput = document.getElementById('telegram-chat-id-input');
  const resultAlert = document.getElementById('telegram-test-result');
  const tokenDisplay = document.getElementById('telegram-token-display');

  generateTokenBtn?.addEventListener('click', async () => {
    try {
      const res = await fetch(`${API_BASE}/notifications/telegram/token`, { method: 'POST' });
      const result = await res.json();
      if (result.success) {
        tokenDisplay.classList.remove('hidden');
        tokenDisplay.innerHTML = `
          <div style="background: var(--bg-card); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color); margin-top: 10px;">
            <strong>Linking Token:</strong> <code>${result.token}</code><br>
            <small class="text-muted">${result.instructions}</small>
          </div>
        `;
      }
    } catch (err) {
      alert('Token generation failed: ' + err.message);
    }
  });

  testBtn?.addEventListener('click', async () => {
    const chatId = chatInput.value.trim();
    if (!chatId) return alert('Please enter a Telegram Chat ID.');

    testBtn.textContent = 'Sending...';
    try {
      const res = await fetch(`${API_BASE}/notifications/telegram/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId })
      });
      const result = await res.json();
      resultAlert.classList.remove('hidden');
      resultAlert.textContent = result.message + ' (Formatted MarkdownV2 payload generated).';
    } catch (err) {
      resultAlert.classList.remove('hidden');
      resultAlert.textContent = 'Dispatch failed: ' + err.message;
    } finally {
      testBtn.textContent = '⚡ Send Test Alert';
    }
  });
}

/* SEARCH & FILTERS CONTROLS */
function initSearchAndFilters() {
  document.getElementById('run-search-btn').addEventListener('click', () => loadJobsFeed(true));
  document.getElementById('filter-exp').addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-remote').addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-salary').addEventListener('change', () => loadJobsFeed(true));
  
  document.getElementById('bookmarked-only-btn').addEventListener('click', () => {
    isBookmarkedOnlyFilter = !isBookmarkedOnlyFilter;
    const btn = document.getElementById('bookmarked-only-btn');
    btn.classList.toggle('btn-primary', isBookmarkedOnlyFilter);
    loadJobsFeed(true);
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

  confirmBtn?.addEventListener('click', async () => {
    const name = document.getElementById('modal-search-name').value.trim();
    const query = document.getElementById('modal-search-query').value.trim();
    const exp = document.getElementById('filter-exp').value;
    const remote = document.getElementById('filter-remote').value;
    const minSal = document.getElementById('filter-salary').value;

    if (!name) return alert('Please provide a name for this search rule.');

    try {
      const res = await fetch(`${API_BASE}/searches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          query: query,
          keywords: query,
          experience_level: exp || null,
          remote_type: remote || null,
          min_salary_lpa: minSal ? parseFloat(minSal) : null
        })
      });
      const result = await res.json();
      if (result.success) {
        closeModal();
        alert('Saved search alert created successfully!');
      }
    } catch (err) {
      alert('Failed to save search: ' + err.message);
    }
  });
}

function initCommandPalette() {
  const palette = document.getElementById('command-palette');
  const input = document.getElementById('cmd-input');
  const list = document.getElementById('cmd-results');

  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      palette.classList.toggle('hidden');
      if (!palette.classList.contains('hidden')) input.focus();
    }
    if (e.key === 'Escape' && !palette.classList.contains('hidden')) {
      palette.classList.add('hidden');
    }
  });

  input?.addEventListener('input', () => {
    const val = input.value.toLowerCase().trim();
    if (!val) {
      list.innerHTML = `<li class="cmd-item text-muted">Type a tech keyword (e.g. FastAPI, Python, React, Remote)...</li>`;
      return;
    }

    const matched = currentJobs.filter(j => 
      j.title.toLowerCase().includes(val) || 
      j.company.toLowerCase().includes(val) || 
      (j.raw_tags || '').toLowerCase().includes(val)
    );

    if (matched.length === 0) {
      list.innerHTML = `<li class="cmd-item text-muted">No quick matches for "${escapeHtml(val)}"</li>`;
    } else {
      list.innerHTML = matched.slice(0, 5).map(j => `
        <li class="cmd-item" onclick="selectCmdJob(${j.id})">
          <strong>${escapeHtml(j.title)}</strong> at ${escapeHtml(j.company)}
        </li>
      `).join('');
    }
  });
}

function selectCmdJob(jobId) {
  document.getElementById('command-palette').classList.add('hidden');
  const targetJob = currentJobs.find(j => j.id === jobId);
  if (targetJob) {
    const applyTarget = targetJob.external_apply_url || targetJob.job_url;
    if (applyTarget && applyTarget !== '#') window.open(applyTarget, '_blank');
  }
}
