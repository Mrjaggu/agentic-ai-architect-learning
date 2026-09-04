<script>
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    fontFamily: 'Inter, sans-serif',
    primaryColor: '#6366f1',
    primaryTextColor: '#ffffff',
    lineColor: '#818cf8',
    secondaryColor: '#1e1b4b',
    tertiaryColor: '#171b26'
  }
});

const META = [
  {"label": "Overview", "title": "Curriculum Overview", "module": "Foundations"},
  {"label": "Ch 1", "title": "The Evolution of AI Systems", "module": "Module A — Foundations"},
  {"label": "Ch 2", "title": "Anatomy of an AI Agent", "module": "Module A — Foundations"},
  {"label": "Ch 3", "title": "Agent Design Patterns", "module": "Module A — Foundations"},
  {"label": "Ch 4", "title": "Agent Graphs & State Machines", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 5", "title": "Agent Harness Engineering", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 6", "title": "Backend & System Design for Agent Services", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 7", "title": "Deploying Agent Systems", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 8", "title": "Context Engineering", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 9", "title": "Memory Architecture", "module": "Module B — Orchestration & Harness"},
  {"label": "Ch 10", "title": "Enterprise RAG, Properly", "module": "Module C — Knowledge Architecture"},
  {"label": "Ch 11", "title": "Knowledge Graphs & Graph RAG", "module": "Module C — Knowledge Architecture"},
  {"label": "Ch 12", "title": "Agentic Retrieval & Knowledge Routing", "module": "Module C — Knowledge Architecture"},
  {"label": "Ch 13", "title": "Tools & Function Calling", "module": "Module D — Tools, MCP & Multi-Agent"},
  {"label": "Ch 14", "title": "MCP, A2A & Protocol Stack", "module": "Module D — Tools, MCP & Multi-Agent"},
  {"label": "Ch 15", "title": "Multi-Agent Systems", "module": "Module D — Tools, MCP & Multi-Agent"},
  {"label": "Ch 16", "title": "Agent Observability", "module": "Module E — Production AI"},
  {"label": "Ch 17", "title": "Evals", "module": "Module E — Production AI"},
  {"label": "Ch 18", "title": "Reliability & Cost Engineering", "module": "Module E — Production AI"},
  {"label": "Ch 19", "title": "Security & Guardrails", "module": "Module F — Governance & Platform"},
  {"label": "Ch 20", "title": "Autonomy Levels & Governance", "module": "Module F — Governance & Platform"},
  {"label": "Ch 21", "title": "Enterprise Reference Architecture", "module": "Module F — Governance & Platform"},
  {"label": "Ch 22", "title": "Interview Q&A Bank", "module": "Module F — Governance & Platform"},
  {"label": "Ch 23", "title": "End-to-End Case Studies", "module": "Module F — Governance & Platform"}
];

const secs = document.querySelectorAll('.chapter');
let cur = 0;
let completedSet = new Set(JSON.parse(localStorage.getItem('completed_chapters') || '[]'));

// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
function setTheme(isDark) {
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.classList.toggle('light', !isDark);
  themeToggle.textContent = isDark ? '🌙' : '☀️';
  localStorage.setItem('pref_theme', isDark ? 'dark' : 'light');
}
setTheme(localStorage.getItem('pref_theme') !== 'light');
themeToggle.onclick = () => setTheme(!document.documentElement.classList.contains('dark'));

// Sidebar Construction
const sidebarNav = document.getElementById('sidebarNav');
let lastModule = '';

META.forEach((m, i) => {
  if (m.module !== lastModule) {
    lastModule = m.module;
    const modHeader = document.createElement('div');
    modHeader.className = 'module-header';
    modHeader.textContent = m.module;
    sidebarNav.appendChild(modHeader);
  }

  const link = document.createElement('div');
  link.className = 'nav-link';
  link.dataset.index = i;

  const cb = document.createElement('div');
  cb.className = 'nav-checkbox' + (completedSet.has(i) ? ' checked' : '');
  cb.textContent = completedSet.has(i) ? '✓' : '';
  cb.onclick = (e) => {
    e.stopPropagation();
    toggleComplete(i);
  };

  const label = document.createElement('span');
  label.textContent = (m.label === 'Overview' ? 'Overview' : m.label + ' — ' + m.title);

  link.appendChild(cb);
  link.appendChild(label);
  link.onclick = () => show(i);

  sidebarNav.appendChild(link);
});

function updateProgressUI() {
  const pct = Math.round((completedSet.size / META.length) * 100);
  document.getElementById('progressPercent').textContent = pct + '%';
  document.getElementById('progressMeterFill').style.width = pct + '%';
  
  document.querySelectorAll('.nav-checkbox').forEach((cb, idx) => {
    const isDone = completedSet.has(idx);
    cb.classList.toggle('checked', isDone);
    cb.textContent = isDone ? '✓' : '';
  });

  const toggleBtn = document.getElementById('toggleCompleteBtn');
  if (completedSet.has(cur)) {
    toggleBtn.textContent = 'Completed ✓';
    toggleBtn.style.background = 'var(--success)';
    toggleBtn.style.color = '#fff';
    toggleBtn.style.borderColor = 'var(--success)';
  } else {
    toggleBtn.textContent = 'Mark as Completed';
    toggleBtn.style.background = 'var(--accent-light)';
    toggleBtn.style.color = 'var(--accent)';
    toggleBtn.style.borderColor = 'var(--accent)';
  }
}

function toggleComplete(idx) {
  if (completedSet.has(idx)) completedSet.delete(idx);
  else completedSet.add(idx);
  localStorage.setItem('completed_chapters', JSON.stringify([...completedSet]));
  updateProgressUI();
}

document.getElementById('toggleCompleteBtn').onclick = () => toggleComplete(cur);

// Show Chapter Function
function show(i, push) {
  cur = Math.max(0, Math.min(META.length - 1, i));
  secs.forEach((s, j) => { s.hidden = j !== cur; });

  document.querySelectorAll('.nav-link').forEach((l, idx) => {
    l.classList.toggle('active', idx === cur);
  });

  document.getElementById('posIndicator').textContent = (cur === 0 ? 'Overview' : META[cur].label) + ' / ' + (META.length - 1);
  document.getElementById('prevBtn').disabled = cur === 0;
  document.getElementById('nextBtn').disabled = cur === META.length - 1;

  // Calculate read time
  const currentSec = secs[cur];
  const text = currentSec.innerText || '';
  const wordCount = text.split(/\s+/).length;
  const readMins = Math.max(1, Math.round(wordCount / 200));
  document.getElementById('readTime').textContent = `⏱️ ~${readMins} min read (${wordCount.toLocaleString()} words)`;

  updateProgressUI();

  if (push !== false) location.hash = cur === 0 ? 'overview' : 'ch' + String(cur).padStart(2, '0');
  window.scrollTo(0, 0);

  // Re-run Mermaid rendering for current visible section
  try {
    mermaid.init(undefined, currentSec.querySelectorAll('.mermaid'));
  } catch (err) {
    console.log('Mermaid init:', err);
  }

  // Close sidebar on mobile
  document.getElementById('sidebar').classList.remove('open');
}

function fromHash() {
  const h = location.hash.replace('#', '');
  if (h === 'overview') return 0;
  const m = h.match(/^ch(\d+)$/);
  return m ? parseInt(m[1], 10) : 0;
}

document.getElementById('prevBtn').onclick = () => show(cur - 1);
document.getElementById('nextBtn').onclick = () => show(cur + 1);
window.addEventListener('hashchange', () => show(fromHash(), false));

// Wrap Code blocks with Copy Buttons
secs.forEach(sec => {
  sec.querySelectorAll('pre').forEach(pre => {
    if (pre.classList.contains('mermaid')) return;
    const parent = pre.parentNode;
    if (parent.classList.contains('code-container')) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'code-container';

    const header = document.createElement('div');
    header.className = 'code-header';
    header.innerHTML = '<span>Snippet</span>';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-code-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(pre.innerText);
      copyBtn.textContent = 'Copied! ✓';
      setTimeout(() => copyBtn.textContent = 'Copy', 2000);
    };

    header.appendChild(copyBtn);
    parent.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
  });
});

// Scroll Reading Progress
window.onscroll = () => {
  const winScroll = document.documentElement.scrollTop;
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  const scrolled = (winScroll / height) * 100;
  document.getElementById('reading-progress').style.width = scrolled + '%';
};

// Search Engine
const searchModal = document.getElementById('searchModal');
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

function openSearchModal() {
  searchModal.classList.add('open');
  searchInput.focus();
}
function closeSearchModal() {
  searchModal.classList.remove('open');
}

document.getElementById('openSearch').onclick = openSearchModal;
searchModal.onclick = (e) => { if (e.target === searchModal) closeSearchModal(); };

searchInput.oninput = () => {
  const q = searchInput.value.toLowerCase().trim();
  if (!q) {
    searchResults.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);font-size:0.9rem;">Type to start searching...</div>';
    return;
  }

  let matches = [];
  secs.forEach((sec, idx) => {
    const text = sec.innerText;
    if (text.toLowerCase().includes(q)) {
      const matchPos = text.toLowerCase().indexOf(q);
      const snippet = text.substring(Math.max(0, matchPos - 40), Math.min(text.length, matchPos + 80)).replace(/\n/g, ' ');
      matches.push({ idx, meta: META[idx], snippet });
    }
  });

  if (matches.length === 0) {
    searchResults.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);font-size:0.9rem;">No matching chapters found.</div>';
    return;
  }

  searchResults.innerHTML = '';
  matches.slice(0, 8).forEach(m => {
    const item = document.createElement('div');
    item.className = 'search-item';
    item.innerHTML = `
      <div class="search-item-title">${m.meta.label === 'Overview' ? 'Overview' : m.meta.label + ' — ' + m.meta.title}</div>
      <div class="search-item-snippet">...${m.snippet}...</div>
    `;
    item.onclick = () => {
      closeSearchModal();
      show(m.idx);
    };
    searchResults.appendChild(item);
  });
};

// Keyboard Shortcuts
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeSearchModal();
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
    e.preventDefault();
    openSearchModal();
  }
  if (document.activeElement.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft') show(cur - 1);
  if (e.key === 'ArrowRight') show(cur + 1);
});

// Mobile Sidebar Toggle
document.getElementById('sidebarToggle').onclick = () => {
  document.getElementById('sidebar').classList.toggle('open');
};

show(fromHash(), false);
</script>
