const API_BASE = '/api/v1';

let currentJobs = [];
let isBookmarkedOnlyFilter = false;

let currentFeedPage = 1;
let totalFeedPages = 1;
let totalFeedRecords = 0;
let isLoadingMoreFeed = false;

let selectedSalaryMin = null;
let selectedSalaryMax = null;

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initCommandPalette();
  initSearchAndFilters();
  initModals();
  initTelegramView();
  initInfiniteScroll();
  initApplicationWorkspaceEvents();
  initSpotlightEffect();
  
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
      if (tabTarget === 'applications') loadApplicationWorkspace();
      if (tabTarget === 'bookmarks') loadBookmarksFeed();
      if (tabTarget === 'analytics') loadAnalytics();
      if (tabTarget === 'connectors') loadConnectorHealth();
    });
  });

  document.getElementById('sync-now-btn')?.addEventListener('click', triggerManualSync);
  document.getElementById('trigger-sync-panel-btn')?.addEventListener('click', triggerManualSync);
}

/* ACETERNITY UI SPOTLIGHT MOUSE TRACKING */
function initSpotlightEffect() {
  document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.job-card, .bento-card, .kanban-card');
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}

/* JOBS FEED & USER-DRIVEN SEARCH */
async function loadJobsFeed(reset = true) {
  const container = document.getElementById('jobs-container');
  const loadMoreBtn = document.getElementById('load-more-btn');
  const loadMoreSpinner = document.getElementById('load-more-spinner');

  if (reset) {
    currentFeedPage = 1;
    currentJobs = [];
    container.innerHTML = '<div class="loading-skeleton">Searching live opportunities...</div>';
  }

  const q = document.getElementById('job-search-input').value.trim();
  const exp = document.getElementById('filter-exp').value;
  const remote = document.getElementById('filter-remote').value;
  const minSal = selectedSalaryMin || document.getElementById('filter-salary').value;
  const maxSal = selectedSalaryMax;

  let url = `${API_BASE}/jobs/search?page=${currentFeedPage}&limit=30`;
  if (q) url += `&keyword=${encodeURIComponent(q)}`;
  if (exp) url += `&experience_level=${encodeURIComponent(exp)}`;
  if (remote) url += `&remote_type=${encodeURIComponent(remote)}`;
  if (minSal) url += `&salary_min=${encodeURIComponent(minSal)}`;
  if (maxSal) url += `&salary_max=${encodeURIComponent(maxSal)}`;

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
      <div class="card card-padded text-center" style="grid-column: 1 / -1;">
        <h3>No matching opportunities found</h3>
        <p class="text-muted">Try searching with a specific keyword, salary chip, or location.</p>
      </div>`;
    return;
  }

  container.innerHTML = jobs.map(job => {
    const applyTarget = job.external_apply_url || job.job_url || (job.url !== '#' ? job.url : null);
    
    const vStatus = job.verification_status || 'VERIFIED';
    let vBadgeHtml = '<span class="badge badge-pulse">🟢 Verified Today</span>';
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
        Link unavailable
      </button>`;

    const salaryDisp = job.salary_range ? `💰 ${escapeHtml(job.salary_range)}` : '💰 Disclosed on App';

    return `
      <div class="job-card">
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
          <span class="detail-item">${salaryDisp}</span>
        </div>

        <div class="job-tags">
          ${(job.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>

        <div class="job-card-footer">
          <small class="posted-date">Via ${escapeHtml(job.source)} • Seen: ${formatDate(job.first_seen)}</small>
          <div class="action-buttons">
            <button class="btn btn-sm btn-ghost" onclick="saveToApplicationWorkspace('${escapeHtml(job.company)}', '${escapeHtml(job.title)}', '${escapeHtml(applyTarget || '')}')">
              💼 Track
            </button>
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

/* APPLICATION WORKSPACE KANBAN */
async function loadApplicationWorkspace() {
  const container = document.getElementById('kanban-board-container');
  container.innerHTML = '<div class="loading-skeleton">Loading Application Kanban Workspace...</div>';

  try {
    const res = await fetch(`${API_BASE}/applications`);
    const result = await res.json();

    if (result.success) {
      const apps = result.data || [];
      const columns = ['Saved', 'Applied', 'OA Scheduled', 'Interview', 'Offer', 'Rejected'];

      container.innerHTML = columns.map(col => {
        const colApps = apps.filter(a => a.status === col);
        return `
          <div class="kanban-column">
            <div class="kanban-header">
              <span class="kanban-title">${col}</span>
              <span class="badge">${colApps.length}</span>
            </div>
            <div class="kanban-cards-wrapper" style="display: flex; flex-direction: column; gap: 10px;">
              ${colApps.length === 0 ? '<small class="text-muted" style="text-align: center; padding: 10px;">No applications</small>' : colApps.map(a => `
                <div class="kanban-card">
                  <strong style="font-size: 14px;">${escapeHtml(a.role)}</strong>
                  <small class="text-muted">${escapeHtml(a.company)}</small>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                    <span class="tag">${escapeHtml(a.source || 'Manual')}</span>
                    <select onchange="updateApplicationStatus(${a.id}, this.value)" style="font-size: 11px; padding: 2px 4px; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 4px;">
                      ${columns.map(c => `<option value="${c}" ${c === a.status ? 'selected' : ''}>${c}</option>`).join('')}
                    </select>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    container.innerHTML = `<div class="card card-padded text-muted">Error loading Application Workspace.</div>`;
  }
}

async function updateApplicationStatus(id, newStatus) {
  try {
    await fetch(`${API_BASE}/applications/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    loadApplicationWorkspace();
  } catch (err) {
    alert('Status update failed: ' + err.message);
  }
}

async function saveToApplicationWorkspace(company, role, jobUrl) {
  try {
    const res = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, role, job_url: jobUrl, status: 'Saved' })
    });
    const result = await res.json();
    if (result.success) {
      alert(`Tracked ${role} at ${company} in Application Workspace!`);
    }
  } catch (err) {
    alert('Failed to track application: ' + err.message);
  }
}

function initApplicationWorkspaceEvents() {
  document.getElementById('export-applications-btn')?.addEventListener('click', () => {
    window.open(`${API_BASE}/applications/export?format=csv`, '_blank');
  });

  const csvInput = document.getElementById('csv-file-input');
  csvInput?.addEventListener('change', async () => {
    if (!csvInput.files || csvInput.files.length === 0) return;
    const formData = new FormData();
    formData.append('file', csvInput.files[0]);

    try {
      const res = await fetch(`${API_BASE}/applications/import`, {
        method: 'POST',
        body: formData
      });
      const result = await res.json();
      alert(result.message);
      loadApplicationWorkspace();
    } catch (err) {
      alert('CSV import failed: ' + err.message);
    }
  });

  document.getElementById('add-custom-application-btn')?.addEventListener('click', () => {
    const comp = prompt('Company Name:');
    if (!comp) return;
    const role = prompt('Role Title:');
    if (!role) return;
    saveToApplicationWorkspace(comp, role, '#');
  });
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
    const res = await fetch(`${API_BASE}/dashboard/metrics`);
    const result = await res.json();
    if (result.success) {
      const data = result.metrics;
      document.getElementById('stat-total-jobs').textContent = data.total_discovered_jobs || 0;
      document.getElementById('stat-remote-jobs').textContent = data.total_applications || 0;
      document.getElementById('stat-fresher-jobs').textContent = data.active_interviews || 0;
      document.getElementById('stat-avg-salary').textContent = `${data.response_rate_pct}%`;
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
  if (syncBtn) syncBtn.innerHTML = '<span>🔄 Syncing...</span>';

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
    if (syncBtn) syncBtn.innerHTML = '<span>🔄 Sync Sources</span>';
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
  document.getElementById('job-search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') loadJobsFeed(true);
  });
  document.getElementById('filter-exp').addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-remote').addEventListener('change', () => loadJobsFeed(true));
  document.getElementById('filter-salary').addEventListener('change', () => loadJobsFeed(true));

  // Salary Chips Handler
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
    const minSal = selectedSalaryMin || document.getElementById('filter-salary').value;

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
  const triggerBtn = document.getElementById('cmd-k-btn');

  triggerBtn?.addEventListener('click', () => {
    palette.classList.remove('hidden');
    input.focus();
  });

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

// Centralized Auth State Manager & UI Controller
const AuthState = {
  user: null,
  async check() {
    try {
      const res = await fetch('/api/v1/auth/me');
      const data = await res.json();
      if (data.authenticated && data.user) {
        this.user = data.user;
      } else {
        this.user = null;
      }
    } catch (e) {
      console.warn("Auth check error:", e);
      this.user = null;
    }
    this.render();
  },
  render() {
    const unauthGroup = document.getElementById('auth-unauthenticated-controls');
    const authGroup = document.getElementById('auth-authenticated-controls');
    const nameDisplay = document.getElementById('user-display-name');

    const profileUnauth = document.getElementById('profile-unauth-view');
    const profileAuth = document.getElementById('profile-auth-view');
    const profileName = document.getElementById('profile-name-field');
    const profileEmail = document.getElementById('profile-email-field');
    const profileVerifBadge = document.getElementById('profile-verif-badge');
    const profileResendBtn = document.getElementById('profile-resend-verif-btn');

    if (this.user) {
      if (unauthGroup) unauthGroup.style.display = 'none';
      if (authGroup) authGroup.classList.remove('hidden');
      if (nameDisplay) nameDisplay.textContent = this.user.name || this.user.email;

      if (profileUnauth) profileUnauth.classList.add('hidden');
      if (profileAuth) profileAuth.classList.remove('hidden');
      if (profileName) profileName.value = this.user.name || '';
      if (profileEmail) profileEmail.value = this.user.email || '';
      
      if (profileVerifBadge) {
        if (this.user.email_verified) {
          profileVerifBadge.textContent = 'Verified ✓';
          profileVerifBadge.className = 'badge badge-success';
          if (profileResendBtn) profileResendBtn.classList.add('hidden');
        } else {
          profileVerifBadge.textContent = 'Unverified';
          profileVerifBadge.className = 'badge badge-warning';
          if (profileResendBtn) profileResendBtn.classList.remove('hidden');
        }
      }
    } else {
      if (unauthGroup) unauthGroup.style.display = 'flex';
      if (authGroup) authGroup.classList.add('hidden');

      if (profileUnauth) profileUnauth.classList.remove('hidden');
      if (profileAuth) profileAuth.classList.add('hidden');
    }
  }
};

function setupAuthHandlers() {
  const loginModal = document.getElementById('login-modal');
  const signupModal = document.getElementById('signup-modal');
  const otpModal = document.getElementById('otp-modal');
  const forgotModal = document.getElementById('forgot-password-modal');

  // Open modals
  document.getElementById('open-login-btn')?.addEventListener('click', () => loginModal?.classList.remove('hidden'));
  document.getElementById('profile-open-login-btn')?.addEventListener('click', () => loginModal?.classList.remove('hidden'));
  document.getElementById('open-signup-btn')?.addEventListener('click', () => signupModal?.classList.remove('hidden'));
  document.getElementById('profile-open-signup-btn')?.addEventListener('click', () => signupModal?.classList.remove('hidden'));
  document.getElementById('open-forgot-modal')?.addEventListener('click', (e) => {
    e.preventDefault();
    loginModal?.classList.add('hidden');
    forgotModal?.classList.remove('hidden');
  });

  // Close modals
  document.getElementById('close-login-modal')?.addEventListener('click', () => loginModal?.classList.add('hidden'));
  document.getElementById('cancel-login')?.addEventListener('click', () => loginModal?.classList.add('hidden'));
  document.getElementById('close-signup-modal')?.addEventListener('click', () => signupModal?.classList.add('hidden'));
  document.getElementById('cancel-signup')?.addEventListener('click', () => signupModal?.classList.add('hidden'));
  document.getElementById('close-otp-modal')?.addEventListener('click', () => otpModal?.classList.add('hidden'));
  document.getElementById('cancel-otp')?.addEventListener('click', () => otpModal?.classList.add('hidden'));
  document.getElementById('close-forgot-modal')?.addEventListener('click', () => forgotModal?.classList.add('hidden'));
  document.getElementById('cancel-forgot')?.addEventListener('click', () => forgotModal?.classList.add('hidden'));

  // Submit Login
  document.getElementById('submit-login-btn')?.addEventListener('click', async () => {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error-msg');

    errorDiv.classList.add('hidden');
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        loginModal.classList.add('hidden');
        await AuthState.check();
      } else {
        errorDiv.textContent = data.detail || 'Login failed.';
        errorDiv.classList.remove('hidden');
      }
    } catch (err) {
      errorDiv.textContent = 'Network error during login.';
      errorDiv.classList.remove('hidden');
    }
  });

  // Submit Signup
  document.getElementById('submit-signup-btn')?.addEventListener('click', async () => {
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm-password').value;
    const errorDiv = document.getElementById('signup-error-msg');

    errorDiv.classList.add('hidden');
    if (password !== confirm) {
      errorDiv.textContent = 'Passwords do not match.';
      errorDiv.classList.remove('hidden');
      return;
    }

    try {
      const res = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        signupModal.classList.add('hidden');
        await AuthState.check();
      } else {
        errorDiv.textContent = data.detail || 'Signup failed.';
        errorDiv.classList.remove('hidden');
      }
    } catch (err) {
      errorDiv.textContent = 'Network error during signup.';
      errorDiv.classList.remove('hidden');
    }
  });

  // Logout Handlers
  const handleLogout = async () => {
    try {
      await fetch('/api/v1/auth/logout', { method: 'POST' });
      await AuthState.check();
    } catch (e) {
      console.error("Logout failed:", e);
    }
  };
  document.getElementById('header-logout-btn')?.addEventListener('click', handleLogout);
  document.getElementById('profile-logout-btn')?.addEventListener('click', handleLogout);

  // Request OTP
  document.getElementById('profile-request-otp-btn')?.addEventListener('click', async () => {
    if (!AuthState.user) return;
    try {
      await fetch('/api/v1/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: AuthState.user.email })
      });
      otpModal?.classList.remove('hidden');
    } catch (e) {
      alert("Failed to request OTP.");
    }
  });

  // Verify OTP
  document.getElementById('submit-otp-btn')?.addEventListener('click', async () => {
    const otp = document.getElementById('otp-code-input').value;
    const errorDiv = document.getElementById('otp-error-msg');
    errorDiv.classList.add('hidden');

    try {
      const res = await fetch('/api/v1/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: AuthState.user.email, otp })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        otpModal.classList.add('hidden');
        await AuthState.check();
        alert("OTP verified successfully!");
      } else {
        errorDiv.textContent = data.detail || "Invalid OTP.";
        errorDiv.classList.remove('hidden');
      }
    } catch (e) {
      errorDiv.textContent = "Error verifying OTP.";
      errorDiv.classList.remove('hidden');
    }
  });

  // Submit Forgot Password
  document.getElementById('submit-forgot-btn')?.addEventListener('click', async () => {
    const email = document.getElementById('forgot-email-input').value;
    const errorDiv = document.getElementById('forgot-error-msg');
    errorDiv.classList.add('hidden');

    try {
      const res = await fetch('/api/v1/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      errorDiv.textContent = data.message || "Reset link dispatched if email exists.";
      errorDiv.className = "alert alert-success mt-2";
      errorDiv.classList.remove('hidden');
    } catch (e) {
      errorDiv.textContent = "Error requesting password reset.";
      errorDiv.className = "alert alert-error mt-2";
      errorDiv.classList.remove('hidden');
    }
  });

  // Submit Change Password
  document.getElementById('submit-change-password-btn')?.addEventListener('click', async () => {
    const old_password = document.getElementById('change-old-password').value;
    const new_password = document.getElementById('change-new-password').value;
    const msgDiv = document.getElementById('change-password-msg');

    msgDiv.classList.add('hidden');
    try {
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_password, new_password })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        msgDiv.textContent = "Password updated successfully!";
        msgDiv.className = "alert alert-success mt-3";
        msgDiv.classList.remove('hidden');
        document.getElementById('change-old-password').value = '';
        document.getElementById('change-new-password').value = '';
      } else {
        msgDiv.textContent = data.detail || "Failed to change password.";
        msgDiv.className = "alert alert-error mt-3";
        msgDiv.classList.remove('hidden');
      }
    } catch (e) {
      msgDiv.textContent = "Error changing password.";
      msgDiv.className = "alert alert-error mt-3";
      msgDiv.classList.remove('hidden');
    }
  });
}

// Initialize Auth on Startup
document.addEventListener('DOMContentLoaded', () => {
  AuthState.check();
  setupAuthHandlers();
});

