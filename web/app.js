/**
 * Gardu · The State of MCP Servers
 * Interactive landing page JavaScript
 * No dependencies - vanilla JS only
 */

(function() {
  'use strict';

  // ============================================
  // State & Data
  // ============================================
  const data = window.MCPDATA || null;
  
  // Table state
  const tableState = {
    servers: {
      search: '',
      category: 'all',
      sort: 'stars-desc'
    },
    skills: {
      search: '',
      category: 'all',
      sort: 'stars-desc'
    }
  };

  // Observations - grounded in real data
  const observations = [
    {
      text: 'The MCP ecosystem is massive — roughly <strong>359,500 public GitHub repositories</strong> have "mcp" in their name. This is a broad upper bound; the actual number of distinct servers is smaller, but the scale shows explosive growth.'
    },
    {
      text: 'Top categories are <strong>Official & SDK</strong>, <strong>Code & Dev tools</strong>, and <strong>Agents & Frameworks</strong>, followed by <strong>Browser & Web</strong> automation. The ecosystem is developer-tool heavy, with browser automation as a close second.'
    },
    {
      text: 'The big top servers mostly <strong>PASS</strong> the static scan. Medium findings are primarily MCP-config hygiene issues: unpinned <code>npx</code> versions, plain-HTTP remote URLs, and secret-shaped environment parameters — not active injection payloads.'
    },
    {
      text: '<strong>Skills are now the bigger, faster-growing surface</strong> and the primary instruction-injection vector. The top skills repos have more stars than most servers, and they directly shape agent behavior through prompts and workflows.'
    },
    {
      text: 'Almost no top server ships a <strong>security attestation</strong>. There\'s no SBOM, no signed release, no vulnerability disclosure policy. Gardu/Hexbane scans before you load — but the ecosystem assumes trust by default.'
    },
    {
      text: '<strong>Recommendation:</strong> Pin versions (no floating tags), prefer vendor/official servers over community forks, gate remote HTTP calls through allowlists, and run a scanner like Hexbane in your CI before deploying MCP servers to production.'
    }
  ];

  // ============================================
  // Theme Management
  // ============================================
  function initTheme() {
    const stored = localStorage.getItem('gardu-theme');
    // Brief: default to dark (Hexbane is dark-first); respect an explicit saved choice.
    const theme = stored || 'dark';

    document.documentElement.setAttribute('data-theme', theme);
    
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        document.body.classList.add('theme-transitioning');
        
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('gardu-theme', next);
        
        setTimeout(() => {
          document.body.classList.remove('theme-transitioning');
        }, 300);
      });
    }
  }

  // ============================================
  // Utility Functions
  // ============================================
  function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '—';
    return num.toLocaleString('en-US');
  }

  function formatRelativeDate(dateStr) {
    if (!dateStr) return '—';
    
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays < 1) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours < 1) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return diffMins <= 0 ? 'just now' : `${diffMins}m ago`;
      }
      return `${diffHours}h ago`;
    }
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
    return `${Math.floor(diffDays / 365)}y ago`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function truncate(str, maxLength = 60) {
    if (!str || str.length <= maxLength) return str;
    return str.slice(0, maxLength) + '…';
  }

  function getNestedValue(obj, path) {
    if (!obj || !path) return null;
    return path.split('.').reduce((acc, key) => {
      return acc && acc[key] !== undefined ? acc[key] : null;
    }, obj);
  }

  // ============================================
  // Count-Up Animation
  // ============================================
  function animateCountUp(element, target, duration = 1500) {
    if (!element || target === null || target === undefined) return;
    
    const start = 0;
    const startTime = performance.now();
    
    function easeOutQuart(t) {
      return 1 - Math.pow(1 - t, 4);
    }
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutQuart(progress);
      
      const current = Math.floor(start + (target - start) * eased);
      element.textContent = formatNumber(current);
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = formatNumber(target);
      }
    }
    
    requestAnimationFrame(update);
  }

  function initStatsAnimation() {
    // Small verdict-pill counts: set immediately (no scroll dependency) so the
    // headline numbers are visible without scrolling.
    document.querySelectorAll('.pill-count[data-count-target]').forEach(el => {
      const value = getNestedValue(data, el.dataset.countTarget);
      if (value !== null && value !== undefined) el.textContent = formatNumber(value);
    });

    // Big stat values: count up on scroll into view.
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const value = getNestedValue(data, entry.target.dataset.countTarget);
          if (value !== null && value !== undefined) {
            animateCountUp(entry.target, value);
          }
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-count-target]').forEach(el => {
      if (!el.classList.contains('pill-count')) observer.observe(el);
    });
  }

  // ============================================
  // Render Functions
  // ============================================
  function renderHero() {
    if (!data) return;
    
    const asOfEl = document.getElementById('asOfDate');
    const scannerEl = document.getElementById('scannerVersion');
    
    if (asOfEl && data.meta?.as_of) {
      asOfEl.textContent = formatDate(data.meta.as_of);
      asOfEl.setAttribute('datetime', data.meta.as_of);
    }
    
    if (scannerEl && data.meta?.version) {
      scannerEl.textContent = data.meta.version;
    }
  }

  function renderScanTable() {
    const tbody = document.getElementById('scanTableBody');
    if (!tbody || !data) return;
    
    const scannedRepos = data.ecosystem?.scanned_repos || [];
    const scanResults = data.scan?.results || [];
    const scanStatus = data.scan?.status || 'pending';
    
    if (scannedRepos.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="4" class="table-empty">No repositories scanned yet. Scan status: <strong>${scanStatus}</strong></td>
        </tr>
      `;
      return;
    }
    
    const rows = scannedRepos.map(repo => {
      const result = scanResults.find(r => r.repo === repo);
      const filesScanned = result?.files_scanned ?? '—';
      const findings = result?.findings_total ?? '—';
      const verdict = result?.verdict ?? (scanStatus === 'pending' ? 'pending' : null);
      
      let verdictHtml = '—';
      if (verdict === 'pending' || verdict === null) {
        verdictHtml = '<span class="verdict-badge pending">scanning…</span>';
      } else if (verdict === 'PASS') {
        verdictHtml = '<span class="verdict-badge pass">PASS</span>';
      } else if (verdict === 'REVIEW') {
        verdictHtml = '<span class="verdict-badge review">REVIEW</span>';
      } else if (verdict === 'FAIL') {
        verdictHtml = '<span class="verdict-badge fail">FAIL</span>';
      }
      
      return `
        <tr>
          <td><a href="https://github.com/${escapeHtml(repo)}" target="_blank" rel="noopener" class="repo-link">
            <span class="repo-name">${escapeHtml(repo)}</span>
          </a></td>
          <td class="text-mono">${filesScanned}</td>
          <td class="text-mono">${findings}</td>
          <td>${verdictHtml}</td>
        </tr>
      `;
    }).join('');
    
    tbody.innerHTML = rows;
    
    // Update scan status text
    const statusEl = document.getElementById('scanStatusText');
    if (statusEl) {
      statusEl.textContent = scanStatus;
    }
  }

  function renderFindings() {
    const container = document.getElementById('findingsList');
    if (!container || !data) return;
    
    const results = data.scan?.results || [];
    
    // Filter to repos with notable findings
    const reposWithFindings = results.filter(r => r.notable && r.notable.length > 0);
    
    if (reposWithFindings.length === 0) {
      // Keep the empty state that's already in HTML
      return;
    }
    
    const html = reposWithFindings.map(result => {
      const findingsHtml = result.notable.map(finding => {
        const severityClass = (finding.severity || 'low').toLowerCase();
        const likelyDocTag = finding.likely_doc 
          ? `<span class="finding-doc-tag">likely doc / false alarm</span>` 
          : '';
        
        return `
          <div class="finding-item">
            <div class="finding-severity ${severityClass}"></div>
            <div class="finding-content">
              <div class="finding-rule">
                <span class="rule-badge">${escapeHtml(finding.rule || 'HB???')}</span>
                <span class="finding-family">${escapeHtml(finding.family || 'Unknown')}</span>
              </div>
              <div class="finding-location">${escapeHtml(finding.file || 'unknown')}:${finding.line || '?'}</div>
              <div class="finding-snippet">${escapeHtml(truncate(finding.snippet || '', 100))}</div>
            </div>
            <div class="finding-meta">
              ${likelyDocTag}
            </div>
          </div>
        `;
      }).join('');
      
      return `
        <div class="finding-group">
          <div class="finding-group-header">
            <span class="finding-group-title">${escapeHtml(result.repo)}</span>
          </div>
          ${findingsHtml}
        </div>
      `;
    }).join('');
    
    container.innerHTML = html;
  }

  function renderCategoryChips(categories, containerId, stateKey) {
    const container = document.getElementById(containerId);
    if (!container || !categories) return;
    
    const cats = Object.keys(categories).sort();
    const state = tableState[stateKey];
    
    const chips = [
      `<button class="filter-chip ${state.category === 'all' ? 'active' : ''}" data-category="all">All</button>`,
      ...cats.map(cat => 
        `<button class="filter-chip ${state.category === cat ? 'active' : ''}" data-category="${escapeHtml(cat)}">${escapeHtml(cat)}</button>`
      )
    ].join('');
    
    container.innerHTML = chips;
    
    // Add click handlers
    container.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        state.category = chip.dataset.category;
        renderCategoryChips(categories, containerId, stateKey);
        renderTable(stateKey);
      });
    });
  }

  function filterAndSort(items, state) {
    let filtered = [...items];
    
    // Search filter
    if (state.search) {
      const searchLower = state.search.toLowerCase();
      filtered = filtered.filter(item => {
        const name = (item.name || '').toLowerCase();
        const desc = (item.desc || '').toLowerCase();
        const owner = (item.owner || '').toLowerCase();
        return name.includes(searchLower) || desc.includes(searchLower) || owner.includes(searchLower);
      });
    }
    
    // Category filter
    if (state.category && state.category !== 'all') {
      filtered = filtered.filter(item => item.category === state.category);
    }
    
    // Sort
    const [sortKey, sortDir] = state.sort.split('-');
    filtered.sort((a, b) => {
      let valA = a[sortKey];
      let valB = b[sortKey];
      
      // Handle null/undefined
      if (valA === null || valA === undefined) valA = sortDir === 'asc' ? Infinity : -Infinity;
      if (valB === null || valB === undefined) valB = sortDir === 'asc' ? Infinity : -Infinity;
      
      // Handle dates
      if (sortKey === 'pushed') {
        valA = valA ? new Date(valA).getTime() : 0;
        valB = valB ? new Date(valB).getTime() : 0;
      }
      
      // Handle strings
      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
      
      let comparison = 0;
      if (valA < valB) comparison = -1;
      if (valA > valB) comparison = 1;
      
      return sortDir === 'asc' ? comparison : -comparison;
    });
    
    // Verdict sort (special case)
    if (sortKey === 'verdict') {
      const verdictOrder = { 'PASS': 0, 'REVIEW': 1, 'FAIL': 2, null: 3, undefined: 3 };
      filtered.sort((a, b) => {
        const aOrder = verdictOrder[a.verdict] ?? 3;
        const bOrder = verdictOrder[b.verdict] ?? 3;
        return aOrder - bOrder;
      });
    }
    
    return filtered;
  }

  function renderTable(stateKey) {
    const state = tableState[stateKey];
    const isServers = stateKey === 'servers';
    const items = isServers ? (data?.servers?.servers || []) : (data?.skills?.skills || []);
    const tbody = document.getElementById(isServers ? 'serversTableBody' : 'skillsTableBody');
    
    if (!tbody || !data) return;
    
    const filtered = filterAndSort(items, state);
    
    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="table-empty">No matching items found</td>
        </tr>
      `;
      return;
    }
    
    const scanStatus = data.scan?.status || 'pending';
    
    const rows = filtered.map((item, index) => {
      const rank = index + 1;
      const stars = formatNumber(item.stars);
      const lang = item.lang || '—';
      const pushed = formatRelativeDate(item.pushed);
      
      let scanHtml = '—';
      if (isServers && item.scanned) {
        if (scanStatus === 'pending' || !item.verdict) {
          scanHtml = '<span class="scan-indicator pending" title="scanning…">…</span>';
        } else if (item.verdict === 'PASS') {
          scanHtml = '<span class="scan-indicator pass" title="PASS">✓</span>';
        } else if (item.verdict === 'REVIEW') {
          scanHtml = '<span class="scan-indicator review" title="REVIEW">!</span>';
        } else if (item.verdict === 'FAIL') {
          scanHtml = '<span class="scan-indicator fail" title="FAIL">✕</span>';
        }
      }
      
      return `
        <tr>
          <td class="col-rank">${rank}</td>
          <td class="col-name">
            <a href="https://github.com/${escapeHtml(item.full_name)}" target="_blank" rel="noopener" class="repo-link">
              <span class="repo-name">${escapeHtml(item.name)}</span>
              <span class="repo-owner">@${escapeHtml(item.owner)}</span>
            </a>
          </td>
          <td class="col-category">
            <span class="category-tag">${escapeHtml(item.category || '—')}</span>
          </td>
          <td class="col-stars">${stars}</td>
          <td class="col-lang">${escapeHtml(lang)}</td>
          <td class="col-pushed" title="${escapeHtml(item.pushed || '')}">${pushed}</td>
          ${isServers ? `<td class="col-scan">${scanHtml}</td>` : ''}
        </tr>
      `;
    }).join('');
    
    tbody.innerHTML = rows;
  }

  function renderObservations() {
    const container = document.getElementById('observationsList');
    if (!container) return;
    
    const html = observations.map(obs => `
      <li>
        <p>${obs.text}</p>
      </li>
    `).join('');
    
    container.innerHTML = html;
  }

  function renderDataSection() {
    if (!data) return;
    
    // Update dates
    const dates = ['sourceDate', 'footerDate'];
    dates.forEach(id => {
      const el = document.getElementById(id);
      if (el && data.meta?.as_of) {
        el.textContent = formatDate(data.meta.as_of);
        el.setAttribute('datetime', data.meta.as_of);
      }
    });
    
    // Setup copy button
    const copyBtn = document.getElementById('copyScanCmd');
    const codeEl = document.getElementById('scanCommand');
    
    if (copyBtn && codeEl) {
      copyBtn.addEventListener('click', async () => {
        const text = codeEl.textContent;
        try {
          await navigator.clipboard.writeText(text);
          copyBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          `;
          setTimeout(() => {
            copyBtn.innerHTML = `
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
            `;
          }, 2000);
        } catch (err) {
          console.error('Failed to copy:', err);
        }
      });
    }
  }

  function initSearchAndSort() {
    // Servers
    const serversSearch = document.getElementById('serversSearch');
    const serversSort = document.getElementById('serversSort');
    
    if (serversSearch) {
      serversSearch.addEventListener('input', (e) => {
        tableState.servers.search = e.target.value;
        renderTable('servers');
      });
    }
    
    if (serversSort) {
      serversSort.addEventListener('change', (e) => {
        tableState.servers.sort = e.target.value;
        renderTable('servers');
      });
    }
    
    // Skills
    const skillsSearch = document.getElementById('skillsSearch');
    const skillsSort = document.getElementById('skillsSort');
    
    if (skillsSearch) {
      skillsSearch.addEventListener('input', (e) => {
        tableState.skills.search = e.target.value;
        renderTable('skills');
      });
    }
    
    if (skillsSort) {
      skillsSort.addEventListener('change', (e) => {
        tableState.skills.sort = e.target.value;
        renderTable('skills');
      });
    }
  }

  // ============================================
  // Initialization
  // ============================================
  function init() {
    // Initialize theme first
    initTheme();
    
    // Check if data is available
    if (!data) {
      console.warn('MCPDATA not found - render empty states');
      renderHero();
      renderScanTable();
      renderFindings();
      renderObservations();
      renderDataSection();
      return;
    }
    
    // Render all sections
    renderHero();
    renderScanTable();
    renderFindings();
    renderObservations();
    renderDataSection();
    
    // Render category chips
    renderCategoryChips(data.servers?.categories, 'serversCategories', 'servers');
    renderCategoryChips(data.skills?.categories, 'skillsCategories', 'skills');
    
    // Render tables
    renderTable('servers');
    renderTable('skills');
    
    // Initialize search/sort handlers
    initSearchAndSort();
    
    // Initialize stats animation
    initStatsAnimation();
    
    // Setup scroll animations for sections
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
