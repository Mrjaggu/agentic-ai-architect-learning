#!/usr/bin/env python3
"""
Build script v2 for the Agentic AI Architect reader.

Layout: this file lives in reader/, chapter markdown lives in chapters/,
both siblings of the repo root. Run from anywhere as:
    pip install markdown beautifulsoup4
    python3 reader/build_reader_v2.py
Output (index.html, Agentic-AI-Reader.html) is always written to the repo
root, since that's what GitHub Pages serves.
Reuses the existing enhanced shell (sidebar, search, theme toggle, progress
tracking, Mermaid infra) extracted from the current index.html, and fixes/adds:
  - removes the duplicated chapter-meta-bar (the "two 5 min read" bug)
  - wraps standard chapter sections (Why the industry needed it, Worked example,
    Failure story, Design decisions, Trade-offs, Industry implementation,
    Hands-on lab, Architect's take, Governance & security lens,
    Interview-ready lines) in styled, icon-labelled callout cards
  - renders ```mermaid fenced blocks as live diagrams inside the existing
    .visual-diagram-card / .mermaid structure
  - styles remaining ```text ASCII diagrams as clean diagram boxes instead of
    code snippets
  - renders "Interview-ready lines" as quote chips instead of a plain list
"""
import glob
import html
import os
import re

import markdown
from bs4 import BeautifulSoup, NavigableString

# Repo layout: this script lives in reader/, chapter markdown lives in
# chapters/, both siblings of the repo root where index.html is published
# (GitHub Pages serves the root, so the built HTML must land there).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CHAPTERS_DIR = os.path.join(REPO_ROOT, "chapters")

CHAPTER_ORDER = [
    ("00-CURRICULUM.md", "Overview", "Curriculum Overview", "Foundations"),
    ("ch01-evolution.md", "Ch 1", "The Evolution of AI Systems", "Module A — Foundations"),
    ("ch02-agent-anatomy.md", "Ch 2", "Anatomy of an AI Agent", "Module A — Foundations"),
    ("ch03-design-patterns.md", "Ch 3", "Agent Design Patterns", "Module A — Foundations"),
    ("ch04-agent-graphs.md", "Ch 4", "Agent Graphs & State Machines", "Module B — Orchestration & Harness"),
    ("ch05-agent-harness.md", "Ch 5", "Agent Harness Engineering", "Module B — Orchestration & Harness"),
    ("ch06-agent-backend.md", "Ch 6", "Backend & System Design for Agent Services", "Module B — Orchestration & Harness"),
    ("ch07-deployment.md", "Ch 7", "Deploying Agent Systems", "Module B — Orchestration & Harness"),
    ("ch08-context-engineering.md", "Ch 8", "Context Engineering", "Module B — Orchestration & Harness"),
    ("ch09-memory-architecture.md", "Ch 9", "Memory Architecture", "Module B — Orchestration & Harness"),
    ("ch10-enterprise-rag.md", "Ch 10", "Enterprise RAG, Properly", "Module C — Knowledge Architecture"),
    ("ch11-knowledge-graphs.md", "Ch 11", "Knowledge Graphs & Graph RAG", "Module C — Knowledge Architecture"),
    ("ch12-knowledge-routing.md", "Ch 12", "Agentic Retrieval & Knowledge Routing", "Module C — Knowledge Architecture"),
    ("ch13-tools-function-calling.md", "Ch 13", "Tools & Function Calling", "Module D — Tools, MCP & Multi-Agent"),
    ("ch14-mcp-protocol-stack.md", "Ch 14", "MCP, A2A & Protocol Stack", "Module D — Tools, MCP & Multi-Agent"),
    ("ch15-multi-agent.md", "Ch 15", "Multi-Agent Systems", "Module D — Tools, MCP & Multi-Agent"),
    ("ch16-observability.md", "Ch 16", "Agent Observability", "Module E — Production AI"),
    ("ch17-evals.md", "Ch 17", "Evals", "Module E — Production AI"),
    ("ch18-reliability-cost.md", "Ch 18", "Reliability & Cost Engineering", "Module E — Production AI"),
    ("ch19-security-guardrails.md", "Ch 19", "Security & Guardrails", "Module F — Governance & Platform"),
    ("ch20-autonomy-governance.md", "Ch 20", "Autonomy Levels & Governance", "Module F — Governance & Platform"),
    ("ch21-reference-architecture.md", "Ch 21", "Enterprise Reference Architecture", "Module F — Governance & Platform"),
    ("ch22-interview-qa.md", "Ch 22", "Interview Q&A Bank", "Module F — Governance & Platform"),
    ("ch23-case-study.md", "Ch 23", "End-to-End Case Studies", "Module F — Governance & Platform"),
    ("ch24-model-strategy.md", "Ch 24", "Model Strategy & Multi-Model Architecture", "Module G — The Architect's Toolkit"),
    ("ch25-failure-engineering.md", "Ch 25", "How Agentic Systems Fail", "Module G — The Architect's Toolkit"),
    ("ch26-distributed-agent-systems.md", "Ch 26", "Distributed Agent Systems", "Module G — The Architect's Toolkit"),
    ("ch27-decision-frameworks.md", "Ch 27", "Architecture Decision Frameworks", "Module G — The Architect's Toolkit"),
    ("ch28-ecosystem-landscape.md", "Ch 28", "The 2026 Agentic AI Ecosystem", "Module G — The Architect's Toolkit"),
]

# (keyword-in-h2-text, css-class-suffix, icon, card-title-override-or-None)
SECTION_RULES = [
    (r"governance\s*&?\s*security lens", "governance", "🛡️", "Governance & Security Lens"),
    (r"interview questions\s*&?\s*answers", "qa", "🎤", "Interview Questions & Answers"),
    (r"interview-ready lines", "interview", "💬", "Interview-Ready Lines"),
    (r"architect'?s take", "architect", "🏦", None),
    (r"hands-on lab", "lab", "🧪", None),
    (r"why the industry needed", "why", "🎯", None),
    (r"worked example", "worked", "🧩", None),
    (r"a failure story|the fix, |a wrong recommendation|a duplicate refund|notification storm|fraud flag|identity trap", "failure", "🔥", None),
    (r"trade-?offs?", "tradeoffs", "🔄", None),
    (r"design decisions?", "design", "⚖️", None),
    (r"industry implementation|how companies actually implement", "industry", "🏭", None),
]

BIO_CARD = """<div class="bio-card" style="background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:28px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
  <h2 style="margin-top:0;font-size:1.6em;margin-bottom:4px;">Hi there 👋 I'm Ajay Jangid</h2>
  <div style="color:var(--accent);font-weight:600;font-size:1.05em;margin-bottom:12px;">🚀 AI Architect | GenAI | Agentic AI | Enterprise AI Systems</div>
  <p style="margin:0 0 12px;font-size:0.96em;line-height:1.65;">
    An <strong>AI Architect</strong> with <strong>7+ years of experience</strong> across AI/ML, NLP, Search, and Information Retrieval, specializing in designing production-grade <strong>Generative AI, Agentic Workflows, and Multi-Agent Platforms</strong>.
  </p>
  <div style="font-size:0.9em;display:flex;gap:14px;flex-wrap:wrap;align-items:center;">
    <a href="https://www.linkedin.com/in/ajayjangid21/" target="_blank" style="color:var(--accent);font-weight:600;text-decoration:none;">🔗 LinkedIn</a>
    <span style="color:var(--muted)">•</span>
    <a href="https://medium.com/@jangidajay271" target="_blank" style="color:var(--accent);font-weight:600;text-decoration:none;">✍️ Medium</a>
    <span style="color:var(--muted)">•</span>
    <a href="mailto:jangidajay271@gmail.com" style="color:var(--accent);font-weight:600;text-decoration:none;">✉️ Contact</a>
  </div>
</div>"""


def find_chapter_file(pattern_name):
    p = os.path.join(CHAPTERS_DIR, pattern_name)
    if os.path.exists(p):
        return p
    matches = glob.glob(p)
    return matches[0] if matches else None


def md_to_soup(md_text):
    html_out = markdown.markdown(
        md_text,
        extensions=["fenced_code", "tables", "sane_lists"],
    )
    return BeautifulSoup(html_out, "html.parser")


def transform_mermaid_and_diagrams(soup):
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        if not code:
            continue
        classes = code.get("class", [])
        is_mermaid = any(c == "language-mermaid" for c in classes)
        is_text = any(c == "language-text" for c in classes)
        if is_mermaid:
            raw = code.decode_contents()
            raw = html.unescape(raw)
            card = soup.new_tag("div", **{"class": "visual-diagram-card"})
            badge = soup.new_tag("span", **{"class": "diagram-badge"})
            badge.string = "DIAGRAM"
            mm = soup.new_tag("div", **{"class": "mermaid"})
            mm.append(NavigableString(raw))
            card.append(badge)
            card.append(mm)
            pre.replace_with(card)
        elif is_text:
            raw = code.decode_contents()
            raw = html.unescape(raw)
            box = soup.new_tag("div", **{"class": "diagram-box"})
            newpre = soup.new_tag("pre")
            newpre.append(NavigableString(raw))
            box.append(newpre)
            pre.replace_with(box)
    return soup


def classify_h2(text):
    t = text.lower()
    for pattern, cls, icon, title_override in SECTION_RULES:
        if re.search(pattern, t):
            return cls, icon, title_override
    return None, None, None


def wrap_section_cards(soup):
    """Wrap each classified H2 (and its following siblings up to the next
    H2/H1/HR) into a styled callout <div>."""
    body_children = list(soup.contents)
    h2s = [el for el in body_children if getattr(el, "name", None) == "h2"]

    for h2 in h2s:
        cls, icon, title_override = classify_h2(h2.get_text())
        if not cls:
            continue

        # collect following siblings until next h1/h2/hr
        siblings = []
        node = h2.next_sibling
        while node is not None:
            nxt = node.next_sibling
            if getattr(node, "name", None) in ("h1", "h2", "hr"):
                break
            siblings.append(node)
            node = nxt

        wrapper = soup.new_tag("div", **{"class": f"section-card section-{cls}"})
        h2.insert_before(wrapper)
        h2.extract()

        header = soup.new_tag("div", **{"class": "section-card-header"})
        icon_span = soup.new_tag("span", **{"class": "section-card-icon"})
        icon_span.string = icon
        title_span = soup.new_tag("span", **{"class": "section-card-title"})
        title_span.string = title_override if title_override else h2.get_text()
        header.append(icon_span)
        header.append(title_span)
        wrapper.append(header)

        body = soup.new_tag("div", **{"class": "section-card-body"})
        for sib in siblings:
            body.append(sib.extract())
        wrapper.append(body)

        # Interview-ready lines: style the <ul> as quote chips
        if cls == "interview":
            ul = body.find("ul")
            if ul:
                ul["class"] = ul.get("class", []) + ["interview-list"]

    return soup


def chapter_to_html(md_path, extra_prefix_html=None):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    soup = md_to_soup(text)
    soup = transform_mermaid_and_diagrams(soup)
    soup = wrap_section_cards(soup)
    body_html = "".join(str(c) for c in soup.contents)
    if extra_prefix_html:
        body_html = extra_prefix_html + body_html
    return body_html


def build():
    with open(f"{SCRIPT_DIR}/reader-base.css", "r", encoding="utf-8") as f:
        orig_css = f.read()
    orig_css_body = orig_css.split("\n", 1)[1]  # drop leading "<style>" line
    orig_css_body = re.sub(r"</style>\s*$", "", orig_css_body.rstrip())  # drop trailing "</style>" line

    with open(f"{SCRIPT_DIR}/reader-shell.js", "r", encoding="utf-8") as f:
        orig_script = f.read()  # full "<script>...</script>"

    # Fix the read-time / word-count calc to ignore diagram content, and skip
    # wrapping diagram/mermaid blocks in a code-copy container.
    orig_script = orig_script.replace(
        "if (pre.classList.contains('mermaid')) return;",
        "if (pre.classList.contains('mermaid')) return;\n    if (pre.closest('.diagram-box') || pre.closest('.visual-diagram-card')) return;",
    )
    orig_script = orig_script.replace(
        "const text = currentSec.innerText || '';\n  const wordCount = text.split(/\\s+/).length;",
        "const clone = currentSec.cloneNode(true);\n  clone.querySelectorAll('.visual-diagram-card, .diagram-box').forEach(n => n.remove());\n  const text = clone.innerText || '';\n  const wordCount = text.split(/\\s+/).filter(Boolean).length;",
    )

    # Robustness: if the Mermaid CDN is blocked/slow/ad-blocked, don't let
    # that ReferenceError take down the entire reader (sidebar, nav, search).
    orig_script = orig_script.replace(
        "mermaid.initialize({",
        "window.__mermaidReady = (typeof mermaid !== 'undefined');\nif (window.__mermaidReady) { try { mermaid.initialize({",
    )
    orig_script = orig_script.replace(
        "    tertiaryColor: '#171b26'\n  }\n});",
        "    tertiaryColor: '#171b26'\n  }\n}); } catch (e) { window.__mermaidReady = false; console.warn('Mermaid init failed:', e); } }",
    )
    orig_script = orig_script.replace(
        "  try {\n    mermaid.init(undefined, currentSec.querySelectorAll('.mermaid'));\n  } catch (err) {\n    console.log('Mermaid init:', err);\n  }",
        "  try {\n    if (window.__mermaidReady) mermaid.init(undefined, currentSec.querySelectorAll('.mermaid'));\n  } catch (err) {\n    console.log('Mermaid init:', err);\n  }",
    )

    extra_css = """
/* ============ v2 additions: section callout cards ============ */
.section-card {
  border: 1px solid var(--border);
  border-left: 4px solid var(--accent);
  background: var(--card-bg);
  border-radius: 10px;
  padding: 4px 20px 18px;
  margin: 26px 0;
}
.section-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 0 10px;
  font-family: 'Outfit', sans-serif;
}
.section-card-icon { font-size: 1.3rem; line-height: 1; }
.section-card-title {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--ink);
}
.section-card-body > *:first-child { margin-top: 0; }
.section-card-body > *:last-child { margin-bottom: 0; }

.section-why       { border-left-color: #f59e0b; }
.section-worked     { border-left-color: #6366f1; }
.section-failure    { border-left-color: #ef4444; }
.section-design     { border-left-color: #3b82f6; }
.section-tradeoffs  { border-left-color: #a855f7; }
.section-industry   { border-left-color: #14b8a6; }
.section-lab        { border-left-color: #22c55e; }
.section-architect  { border-left-color: #d97706; }
.section-governance {
  border-left-color: #dc2626;
  background: linear-gradient(135deg, var(--card-bg), rgba(220,38,38,0.05));
}
.section-interview  {
  border-left-color: #64748b;
  background: transparent;
}
.section-qa {
  border-left-color: #0891b2;
  background: transparent;
}
.section-qa .section-card-body p:has(> strong:only-child) {
  color: #0891b2;
  margin-bottom: 6px;
}

/* Interview-ready lines as quote chips */
ul.interview-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
ul.interview-list li {
  position: relative;
  padding: 10px 16px 10px 38px;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  font-style: italic;
  color: var(--ink);
  font-size: 0.95rem;
}
ul.interview-list li::before {
  content: "\\201C";
  position: absolute;
  left: 12px;
  top: 4px;
  font-size: 1.6rem;
  font-style: normal;
  color: var(--accent);
  opacity: 0.7;
  font-family: Georgia, serif;
}

/* Plain ASCII diagram boxes (non-mermaid) */
.diagram-box {
  background: var(--pre-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 20px;
  margin: 22px 0;
  overflow-x: auto;
}
.diagram-box pre {
  margin: 0;
  background: transparent;
  color: var(--pre-ink);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  line-height: 1.5;
}

/* Mermaid diagram cards */
.visual-diagram-card { overflow-x: auto; }
.visual-diagram-card svg { max-width: 100%; height: auto; }

/* De-duplicated single meta bar spacing */
.chapter-meta-bar { margin-bottom: 20px; }
"""

    full_css = "<style>\n" + orig_css_body.rstrip() + "\n" + extra_css + "\n</style>"

    # Build META for JS + sections HTML
    meta_entries = []
    sections_html_parts = []

    for i, (fname, label, title, module) in enumerate(CHAPTER_ORDER):
        path = find_chapter_file(fname)
        if not path:
            raise SystemExit(f"Missing chapter file: {fname}")
        prefix = BIO_CARD if i == 0 else None
        body_html = chapter_to_html(path, extra_prefix_html=prefix)
        sections_html_parts.append(
            f'<section class="chapter" id="c{i}" hidden>\n{body_html}\n</section>'
        )
        meta_entries.append(
            '  {"label": %s, "title": %s, "module": %s}'
            % (
                repr(label).replace("'", '"'),
                repr(title).replace("'", '"'),
                repr(module).replace("'", '"'),
            )
        )

    sections_html = "\n\n".join(sections_html_parts)
    meta_js = "const META = [\n" + ",\n".join(meta_entries) + "\n];\n\n"

    # splice META into the script (replace the old META block)
    orig_script = re.sub(
        r"const META = \[.*?\];\n\n",
        meta_js,
        orig_script,
        count=1,
        flags=re.DOTALL,
    )

    doc = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic AI Architect — Interactive Learning Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
{full_css}
</head>
<body>

<div id="reading-progress"></div>

<header>
  <button class="mobile-toggle" id="sidebarToggle" aria-label="Toggle Sidebar">☰</button>
  <a href="#" class="brand">
    ⚡ Agentic AI Architect
    <span class="brand-badge">PRO</span>
  </a>

  <button class="search-btn" id="openSearch">
    🔍 <span>Search curriculum...</span>
    <kbd>/</kbd>
  </button>

  <div class="header-right">
    <button class="theme-toggle" id="themeToggle" title="Toggle Light/Dark Theme">🌙</button>
  </div>
</header>

<div class="app-container">
  <aside class="sidebar" id="sidebar">
    <div class="progress-card">
      <div class="progress-card-title">
        <span>Curriculum Progress</span>
        <span id="progressPercent">0%</span>
      </div>
      <div class="progress-meter">
        <div class="progress-meter-fill" id="progressMeterFill"></div>
      </div>
    </div>
    <div id="sidebarNav"></div>
  </aside>

  <main class="content-area">
    <div class="chapter-meta-bar" id="chapterMetaBar">
      <span id="readTime">⏱️ ~5 min read</span>
      <button id="toggleCompleteBtn">Mark as Completed</button>
    </div>
{sections_html}
  </main>
</div>

<div class="bottom-nav">
  <button id="prevBtn">← Previous Chapter</button>
  <span id="posIndicator" style="font-size:0.88rem;color:var(--muted);font-weight:500;">Overview</span>
  <button id="nextBtn">Next Chapter →</button>
</div>

<div class="modal-overlay" id="searchModal">
  <div class="search-modal">
    <div class="search-modal-header">
      🔍 <input type="text" id="searchInput" placeholder="Search chapters, topics, tools (e.g. MCP, LangGraph)..." autofocus />
    </div>
    <div class="search-results" id="searchResults">
      <div style="padding:20px;text-align:center;color:var(--muted);font-size:0.9rem;">Type to start searching across all 23 chapters...</div>
    </div>
  </div>
</div>

{orig_script}
</body>
</html>
"""

    with open(f"{REPO_ROOT}/index.html", "w", encoding="utf-8") as f:
        f.write(doc)
    with open(f"{REPO_ROOT}/Agentic-AI-Reader.html", "w", encoding="utf-8") as f:
        f.write(doc)

    print("Built", len(doc), "bytes;", len(CHAPTER_ORDER), "sections")


if __name__ == "__main__":
    build()
