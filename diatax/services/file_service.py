from __future__ import annotations
import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from diatax.core.models import WorkflowState

class FileService:
    """
    Service responsible for file management, aggregated context reading,
    and multimedia asset handling.
    """

    def check_graph_context(self, reference_path: str) -> Dict[str, Any]:
        """
        Looks for Graphify context (graphify_result.json) strictly in the target path.
        Phase 1: Pre-flight (Silent Detection).
        """
        path = Path(reference_path)
        directory = path if path.is_dir() else path.parent
        graphify_file = directory / "graphify_result.json"

        if graphify_file.exists():
            try:
                with open(graphify_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "has_graph": True,
                    "data": data,
                    "path": str(graphify_file),
                    "error": None
                }
            except (json.JSONDecodeError, OSError) as e:
                return {
                    "has_graph": True,
                    "data": None,
                    "path": str(graphify_file),
                    "error": f"Corrupted or unreadable graph file: {str(e)}"
                }
        
        return {
            "has_graph": False,
            "data": None,
            "path": None,
            "error": None
        }

    def get_aggregated_context(self, path_str: str) -> Dict[str, Any]:
        """
        Rule 3: Aggregated Context Router.
        Path A: Uses graphify_result.json if present.
        Path B (Fallback): Reads all .py files and concatenates content into a global variable.
        """
        # --- PATH A: Graphify Detection ---
        graph_ctx = self.check_graph_context(path_str)
        if graph_ctx["has_graph"] and graph_ctx["data"]:
            return {
                "origin": "graphify",
                "content": json.dumps(graph_ctx["data"], indent=2),
                "path": graph_ctx["path"]
            }

        # --- PATH B: Aggregated Code Reading ---
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path_str}")

        valid_extensions = {".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", ".h", ".cs"}
        accumulated_content = []
        
        # If it's a file, just read it. If directory, crawl it.
        if path.is_file():
            files_to_read = [path]
        else:
            files_to_read = []
            for root, dirs, files in os.walk(path):
                # Ignore system/environment folders
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'venv', 'node_modules', 'dist', 'diatax_result'}]
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in valid_extensions:
                        files_to_read.append(file_path)

        for file_path in files_to_read:
            try:
                rel_path = file_path.relative_to(path if path.is_dir() else path.parent)
                with open(file_path, "r", encoding="utf-8") as f:
                    accumulated_content.append(f"--- FILE: {rel_path} ---\n{f.read()}\n")
            except Exception:
                continue

        if not accumulated_content:
            raise ValueError(f"No valid code files found in: {path_str}")
        
        return {
            "origin": "aggregated_raw_code",
            "content": "\n".join(accumulated_content),
            "path": str(path)
        }

    def get_python_files(self, base_path: str) -> List[str]:
        """Recursively searches for .py files for hashing/update purposes."""
        path = Path(base_path)
        if path.is_file():
            return [str(path)] if path.suffix == ".py" else []

        excluded = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "diatax_result"}
        python_files = []
        for p in path.rglob("*.py"):
            if not any(part in excluded or part.startswith(".") for part in p.parts):
                python_files.append(str(p))
        return python_files

    def calculate_hash(self, path_str: str) -> str:
        path = Path(path_str)
        if not path.is_file(): return ""
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception: return ""

    def read_cache(self) -> Dict[str, str]:
        cache_file = Path(".diatax_cache.json")
        if not cache_file.exists(): return {}
        try: return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception: return {}

    def save_cache(self, cache_data: Dict[str, str]):
        cache_file = Path(".diatax_cache.json")
        cache_file.write_text(json.dumps(cache_data, indent=4), encoding="utf-8")

    def copy_asset(self, source_path: str, assets_dir: Path) -> str:
        source = Path(source_path)
        if not source.exists() or not source.is_file(): return source_path
        destination = assets_dir / source.name
        try:
            shutil.copy2(source, destination)
            return f"./assets/{source.name}"
        except Exception: return source_path

    def find_project_root(self, initial_path: str) -> Path:
        path = Path(initial_path).resolve()
        start_dir = path if path.is_dir() else path.parent
        markers = {".git", "pyproject.toml", "requirements.txt", ".diatax_cache.json", "GEMINI.md"}
        current = start_dir
        for _ in range(10):
            if any((current / m).exists() for m in markers): return current
            if current.parent == current: break
            current = current.parent
        return start_dir

    def read_local_readme(self, reference_path: str) -> str:
        """Reads README.md strictly from the target path."""
        path = Path(reference_path)
        root = path if path.is_dir() else path.parent
        for name in ["README.md", "readme.md", "README.MD"]:
            readme_path = root / name
            if readme_path.exists():
                try: return readme_path.read_text(encoding="utf-8")
                except Exception: continue
        return ""

    def export_results(self, state: WorkflowState, md_results: Dict[str, str], reference_path: str = "."):
        """Exports consolidated project-wide documentation strictly to target_path/diatax_result."""
        path = Path(reference_path)
        root = path if path.is_dir() else path.parent
        output_dir = root / "diatax_result"
        output_dir.mkdir(exist_ok=True)

        for doc_type, content in md_results.items():
            (output_dir / f"{doc_type}.md").write_text(content, encoding="utf-8")

        if state.web_document_html:
            (output_dir / "index.html").write_text(state.web_document_html, encoding="utf-8")
        if state.web_document_css:
            (output_dir / "style.css").write_text(state.web_document_css, encoding="utf-8")

        self._update_readme_with_link(root, output_dir)

    def _update_readme_with_link(self, root: Path, output_dir: Path):
        marker_start = "<!-- DOCUMENTOR_START -->"
        marker_end = "<!-- DOCUMENTOR_END -->"
        rel_link = os.path.relpath(output_dir / "index.html", root).replace("\\", "/")
        content_to_inject = (
            f"\n{marker_start}\n"
            f"## 📚 Interactive Documentation\n"
            f"This project uses an autogenerated Diátaxis Dashboard. [View Full Web Documentation](./{rel_link})\n"
            f"{marker_end}\n"
        )
        readme_file = root / "README.md"
        if not readme_file.exists():
            readme_file.write_text(f"# Project\n{content_to_inject}", encoding="utf-8")
            return
        content = readme_file.read_text(encoding="utf-8")
        if marker_start in content and marker_end in content:
            import re
            pattern = f"{re.escape(marker_start)}.*?{re.escape(marker_end)}"
            new_content = re.sub(pattern, content_to_inject.strip(), content, flags=re.DOTALL)
            readme_file.write_text(new_content, encoding="utf-8")
        else:
            with open(readme_file, "a", encoding="utf-8") as f:
                f.write(f"\n{content_to_inject}")
