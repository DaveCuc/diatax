import markdown
import re
from pathlib import Path
from typing import Tuple, Dict, Any, List
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState

class SiteWriter(BaseAgent):
    """
    SiteWriter Agent: Generator of minimalist and elegant static websites.
    Note: Current implementation focuses on textual and typographic content.
    """
    agent_name = "SiteWriter"
    role = "Minimalist Interface Architect"

    def __init__(self, model: str, llm_service: Any):
        super().__init__(model)
        self.llm_service = llm_service

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Orchestrates the generation of index.html and style.css files with multimedia support.
        """
        try:
            from diatax.services.file_service import FileService
            fs = FileService()
            root = fs.find_project_root(state.reference_path)
            assets_dir = root / "diatax_result" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            # 0. Process Multimedia in each quadrant
            if state.diataxis_results:
                for doc_type, md in state.diataxis_results.items():
                    state.diataxis_results[doc_type] = self._process_multimedia(md, root, assets_dir)

            # 1. Build HTML content
            html_content = self._build_html(state)
            state.web_document_html = html_content
            
            # 2. Build CSS content
            css_content = self._build_css()
            state.web_document_css = css_content

            return state, AgentResponse(status="success", data=html_content, message="Premium minimalist site generated with asset support.")
        except Exception as e:
            return state, AgentResponse(status="error", data="", message=f"Error in site generation: {str(e)}")

    def _process_multimedia(self, md_content: str, root: Path, assets_dir: Path) -> str:
        """
        Searches for local images in Markdown, copies them to assets/ and updates paths.
        """
        from diatax.services.file_service import FileService
        fs = FileService()
        
        # Find image patterns ![alt](path)
        pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def replace_path(match):
            alt_text = match.group(1)
            original_path = match.group(2)
            
            # Only process local paths (no external URLs or base64)
            if original_path.startswith(("http://", "https://", "data:")):
                return match.group(0)
            
            # Try to resolve path relative to project
            absolute_path = (root / original_path).resolve()
            if absolute_path.exists() and absolute_path.is_file():
                new_path = fs.copy_asset(str(absolute_path), assets_dir)
                return f"![{alt_text}]({new_path})"
            
            return match.group(0)

        return re.sub(pattern, replace_path, md_content)

    def _build_html(self, state: WorkflowState) -> str:
        # Generate left sidebar navigation (Global Sections)
        nav_links = '<li><a href="#start" class="nav-link">Introduction</a></li>'
        
        # Generate Central Content (Articles)
        main_content = '<article id="start" class="page">'
        
        # Generate Right Navigation (Table of Contents per block)
        right_sidebar_content = '<div class="toc-group" id="toc-start"><p class="toc-title">ON THIS PAGE</p><ul><li><a href="#start">Top</a></li></ul></div>'
        
        # Metadata / Summary
        meta = state.technical_analysis.get("metadata", {}) if state.technical_analysis else {}
        summary = state.technical_analysis.get("summary", "No summary available.") if state.technical_analysis else ""
        
        main_content += f"""
            <header>
                <p class="badge">PROJECT</p>
                <h1>Introduction</h1>
                <div class="metadata">
                    <span><strong>Version:</strong> {meta.get('version', '1.0.0')}</span>
                    <span><strong>Author:</strong> {meta.get('author', 'Unknown')}</span>
                </div>
                <p class="lead">{summary}</p>
            </header>
        </article>
        """

        if state.diataxis_results:
            for doc_type, md in state.diataxis_results.items():
                anchor_id = doc_type.lower()
                nav_links += f'<li><a href="#{anchor_id}" class="nav-link">{doc_type.capitalize()}</a></li>'
                
                # Convert MD to HTML
                html_snippet = markdown.markdown(md, extensions=['fenced_code', 'tables'])
                
                # Robustly extract headers and inject unique IDs
                local_toc = f'<div class="toc-group" id="toc-{anchor_id}"><p class="toc-title">ON THIS PAGE</p><ul>'
                
                def add_id(match):
                    level = match.group(1)
                    text = match.group(2)
                    clean_id = f"{anchor_id}-{re.sub(r'[^a-zA-Z0-9]', '-', text.lower()).strip('-')}"
                    return f'<h{level} id="{clean_id}">{text}</h{level}>'

                # Replace h2 and h3 with unique IDs
                html_snippet = re.sub(r'<h([2-3])>(.*?)</h[2-3]>', add_id, html_snippet)
                
                # Re-extract for local TOC
                headers = re.findall(r'<h([2-3]) id="(.*?)">(.*?)</h[2-3]>', html_snippet)
                for level, hid, text in headers:
                    indent = "margin-left: 1rem;" if level == "3" else ""
                    local_toc += f'<li style="{indent}"><a href="#{hid}">{text}</a></li>'
                
                local_toc += '</ul></div>'
                right_sidebar_content += local_toc

                main_content += f"""
                <article id="{anchor_id}" class="page">
                    <p class="badge">{doc_type.upper()}</p>
                    <div class="markdown-body">
                        {html_snippet}
                    </div>
                </article>
                """

        return f"""<!-- This is the structural file. Appearance is controlled from style.css -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technical Documentation - Premium</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="layout">
        <!-- Column 1: Global Navigation -->
        <aside class="sidebar-left">
            <nav class="global-nav">
                <div class="brand">DIATAX</div>
                <ul>
                    {nav_links}
                </ul>
            </nav>
        </aside>

        <!-- Column 2: Main Content -->
        <main class="content">
            {main_content}
            <footer>
                <p>Documentation generated by Diatax</p>
            </footer>
        </main>

        <!-- Column 3: Local Index (Right) -->
        <aside class="sidebar-right">
            <nav class="local-nav">
                {right_sidebar_content}
            </nav>
        </aside>
    </div>
</body>
</html>"""

    def _build_css(self) -> str:
        return """/* STYLE FILE: Modify variables in :root to change colors, typography and measurements directly. */
:root {
  --ink: #111111; /* Black for text */
  --paper: #ffffff; /* White for background */
  --accent: #d4af37; /* Elegant gold for accents, titles and links */
  --rule: #e5e5e5; /* Very light gray for dividers */
  --terminal-bg: #0f1419; /* Modern console background */
  --terminal-bar: #1e242e; /* Top console bar */
  --measure: 65ch;
  --serif: ui-serif, Georgia, serif;
  --sans: ui-sans-serif, system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
}

* { box-sizing: border-box; }

html {
  scroll-behavior: smooth;
  font-size: 16px;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  line-height: 1.6;
}

.layout {
  display: grid;
  grid-template-columns: 14rem minmax(0, var(--measure)) 14rem;
  gap: 3rem;
  justify-content: center;
  padding: 0 2rem;
  min-height: 100vh;
}

/* --- HIDDEN PAGES LOGIC (ZERO JS) --- */
.page { display: none; animation: fadeIn 0.4s ease; }

/* Show #start by default if no target */
#start { display: block; }

/* If target exists, hide #start (unless it's the target) */
body:has(.page:target):not(:has(#start:target)) #start { display: none; }

/* Show current target page */
.page:target { display: block; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* --- LEFT SIDEBAR (Global Nav) --- */
.sidebar-left { padding-top: 4rem; }
.global-nav { position: sticky; top: 4rem; }
.brand { font-weight: 900; letter-spacing: 0.15em; margin-bottom: 3rem; color: var(--accent); font-size: 0.75rem; border-left: 2px solid var(--accent); padding-left: 1rem; }

.global-nav ul { list-style: none; padding: 0; margin: 0; }
.global-nav li { margin-bottom: 0.5rem; }
.global-nav a {
  text-decoration: none;
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: block;
  padding: 0.4rem 0;
}
.global-nav a:hover { color: var(--accent); padding-left: 0.5rem; }

/* --- MAIN CONTENT --- */
.content { padding: 4rem 0; }
h1, h2, h3 { font-family: var(--serif); color: var(--ink); line-height: 1.2; margin-top: 3rem; }
h1 { font-size: clamp(2.5rem, 5vw, 3.5rem); margin-top: 0; margin-bottom: 2rem; border-bottom: 2px solid var(--rule); padding-bottom: 1rem; }
h2 { font-size: 1.8rem; color: var(--accent); border-bottom: 1px solid var(--rule); padding-bottom: 0.5rem; }
h3 { font-size: 1.3rem; }

.badge { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.2em; color: var(--accent); margin-bottom: 1rem; text-transform: uppercase; }
.lead { font-size: 1.2rem; color: #444; font-style: italic; margin-bottom: 3rem; }
.metadata { display: flex; gap: 2rem; margin-bottom: 2.5rem; font-size: 0.85rem; color: #888; border-bottom: 1px solid var(--rule); padding-bottom: 1.5rem; }

/* --- RIGHT SIDEBAR (Local TOC) --- */
.sidebar-right { padding-top: 4rem; }
.local-nav { position: sticky; top: 4rem; border-left: 1px solid var(--rule); padding-left: 1.5rem; }
.toc-title { font-size: 0.65rem; font-weight: 900; color: #aaa; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-transform: uppercase; }

.toc-group { display: none; }
.toc-group ul { list-style: none; padding: 0; margin: 0; }
.toc-group li { margin-bottom: 0.75rem; }
.toc-group a { text-decoration: none; color: #777; font-size: 0.8rem; transition: color 0.2s; display: block; }
.toc-group a:hover { color: var(--accent); }

/* Dynamic local TOC highlight */
body:has(#start:target) #toc-start, 
body:not(:has(.page:target)) #toc-start { display: block; }

body:has(#reference:target) #toc-reference { display: block; }
body:has(#howto:target) #toc-howto { display: block; }
body:has(#tutorial:target) #toc-tutorial { display: block; }
body:has(#explanation:target) #toc-explanation { display: block; }

/* --- CODE BLOCKS (REALISTIC TERMINAL) --- */
pre {
    background-color: var(--terminal-bg);
    color: #d1d1d1;
    padding: 1.5rem;
    border-radius: 8px;
    overflow-x: auto;
    font-family: var(--mono);
    font-size: 0.9rem;
    line-height: 1.5;
    margin: 2rem 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    position: relative;
    border: 1px solid #2d333b;
}

pre::before {
    content: "● ● ●";
    display: block;
    height: 24px;
    background: var(--terminal-bar);
    margin: -1.5rem -1.5rem 1rem -1.5rem;
    padding: 0 1rem;
    color: #ff5f56;
    font-size: 10px;
    line-height: 24px;
    letter-spacing: 2px;
    text-shadow: 14px 0 #ffbd2e, 28px 0 #27c93f;
    font-family: sans-serif;
}

code { font-family: var(--mono); background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.9em; color: #c51d1d; }
pre code { background: transparent; padding: 0; color: inherit; }

/* --- TABLES AND OTHERS --- */
table { width: 100%; border-collapse: collapse; margin: 2.5rem 0; font-size: 0.9rem; }
th, td { text-align: left; padding: 1rem; border-bottom: 1px solid var(--rule); }
th { color: var(--accent); font-family: var(--serif); font-weight: 700; }

/* --- FOOTER --- */
footer { margin-top: 10rem; padding-top: 2rem; border-top: 1px solid var(--rule); text-align: center; font-size: 0.75rem; color: #bbb; }

/* RESPONSIVE */
@media (max-width: 1100px) {
  .layout { grid-template-columns: 1fr; padding: 0 2rem; }
  .sidebar-left, .sidebar-right { display: none; }
  .page { display: block !important; margin-bottom: 6rem; }
}
"""
