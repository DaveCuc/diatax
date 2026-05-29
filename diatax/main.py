import typer
import json
import warnings
import logging
from enum import Enum
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Silencing logs and warnings
warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)

from diatax.config import save_config, load_config
from diatax.core.models import WorkflowState, AgentResponse
from diatax.services.llm_service import LLMService
from diatax.services.file_service import FileService
from diatax.agents.researcher import Researcher
from diatax.agents.writers.diataxis_writers import (
    TutorialWriter, HowToWriter, ExplanationWriter, ReferenceWriter
)
from diatax.agents.judges.diataxis_judges import (
    TutorialJudge, HowToJudge, ExplanationJudge, ReferenceJudge
)
from diatax.agents.exporters.site_writer import SiteWriter
from diatax.agents.risk_agent import RiskAgent

class DocType(str, Enum):
    reference = "reference"
    howto = "howto"
    tutorial = "tutorial"
    explanation = "explanation"
    all = "TODO"

app = typer.Typer(help="Multi-agent documentation generator based on Diátaxis.")
console = Console()

MODEL_CATALOG = {
    "1": {"provider": "gemini", "model": "gemini/gemini-3.5-flash", "name": "Gemini 3.5 Flash (Most intelligent / Stable)"},
    "2": {"provider": "gemini", "model": "gemini/gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro (Advanced Intelligence / Preview)"},
    "3": {"provider": "gemini", "model": "gemini/gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash-Lite (Frontier Performance / Stable)"},
    "4": {"provider": "gemini", "model": "gemini/gemini-2.5-pro", "name": "Gemini 2.5 Pro (Most Advanced / Deep Reasoning)"},
    "5": {"provider": "gemini", "model": "gemini/gemini-2.5-flash", "name": "Gemini 2.5 Flash (Best Price-Performance)"},
    "6": {"provider": "gemini", "model": "gemini/gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash-Lite (Fastest & Budget-Friendly)"},
    "7": {"provider": "gemini", "model": "gemini/deep-research-preview-04-2026", "name": "Gemini Deep Research (Autonomous Researcher)"},
    "8": {"provider": "gemini", "model": "gemini/deep-research-max-preview-04-2026", "name": "Gemini Deep Research Max (Maximum Comprehensiveness)"},
    "9": {"provider": "gemini", "model": "gemini/antigravity-preview-05-2026", "name": "Antigravity Agent (Managed Sandbox Agent)"},
    "10": {"provider": "groq", "model": "groq/llama-3.3-70b-versatile", "name": "Groq LLaMA 3.3 70B (Extreme Speed)"}
}

VERSION = "1.2.0"

def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Diatax v{VERSION}[/bold cyan]")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Shows version and exits."
    ),
):
    """Multi-agent documentation generator based on Diátaxis."""
    pass

@app.command()
def config():
    """Configures the AI provider and output language."""
    console.print("\n[bold yellow]--- Configuración de IA - Diatax ---[/bold yellow]")
    table = Table(title="Catálogo de Modelos Disponibles", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Modelo", style="cyan")
    table.add_column("Proveedor", style="green")
    for idx, data in MODEL_CATALOG.items():
        table.add_row(idx, data["name"], data["provider"].upper())
    console.print(table)
    
    selection = Prompt.ask("[bold]Elige una opción[/bold]", choices=list(MODEL_CATALOG.keys()))
    option = MODEL_CATALOG[selection]
    
    api_key = ""
    while not api_key:
        api_key = Prompt.ask(f"[bold cyan]Ingresa tu API Key para {option['provider'].upper()}[/bold cyan]", password=True).strip()
        if not api_key:
            console.print("[bold red]❌ La API Key no puede estar vacía.[/bold red]")

    output_language = Prompt.ask("[bold cyan]Elige el idioma de salida[/bold cyan]", choices=["spanish", "english", "french", "german", "portuguese"], default="spanish")
    save_config(option["provider"], option["model"], api_key, output_language)
    
    message = f"[green]¡Configuración blindada exitosamente![/green]\n\nModelo: [bold]{option['name']}[/bold]\nIdioma: [bold]{output_language.capitalize()}[/bold]"
    console.print(Panel(message, title="Sistema Configurado", border_style="green"))

def orchestrate_cycle(state: WorkflowState, doc_type: DocType, model: str, llm: LLMService, status=None, auto_mode: bool = False) -> WorkflowState:
    writers = {DocType.reference: ReferenceWriter, DocType.howto: HowToWriter, DocType.tutorial: TutorialWriter, DocType.explanation: ExplanationWriter}
    judges = {DocType.reference: ReferenceJudge, DocType.howto: HowToJudge, DocType.tutorial: TutorialJudge, DocType.explanation: ExplanationJudge}

    writer = writers[doc_type](model=model, llm_service=llm)
    judge = judges[doc_type](model=model, llm_service=llm)
    state.final_document_approved = False
    state.writing_attempts = 0
    state.judge_feedback = None

    max_attempts = 3
    while not state.final_document_approved and state.writing_attempts < max_attempts:
        if status: status.update(f"[bold blue]✍️ Escribiendo {doc_type.value}...")
        state, resp_write = writer.execute(state)
        
        if resp_write.status == "error":
            console.print(Panel(f"Critical error in agent [bold]{writer.agent_name}[/bold]:\n{resp_write.message}", title="Fallo de Agente", border_style="red"))
            break

        if not auto_mode and state.markdown_draft:
            if status: status.stop()
            preview = state.markdown_draft[:500] + "..."
            console.print(Panel(preview, title=f"Previsualización: {doc_type.value.upper()}", border_style="cyan"))
            action = Prompt.ask("¿Acción?", choices=["A", "R", "I"], default="A").upper()
            if action == "A": state.final_document_approved = True; break
            elif action == "R":
                state.judge_feedback = Prompt.ask("[bold cyan]Corrección[/bold cyan]")
                state.writing_attempts = 0; status.start(); continue
            else: status.start()

        if status: status.update(f"[bold yellow]⚖️ Evaluando calidad de {doc_type.value}...")
        state, resp_judge = judge.execute(state)
        if state.final_document_approved: break
    return state

@app.command()
def update(path: str = typer.Argument(".", help="Path to update")):
    """Updates documentation incrementally for the entire project."""
    target_path = os.getcwd() if path == "." else os.path.abspath(path)
    engine_path = os.path.dirname(os.path.abspath(__file__))
    
    file_service = FileService()
    files = file_service.get_python_files(target_path)
    
    with console.status("[bold green]⚡ Checking for changes...", spinner="dots") as status:
        cache = file_service.read_cache()
        project_changed = False
        
        for file in files:
            current_hash = file_service.calculate_hash(file)
            if cache.get(file) != current_hash:
                project_changed = True
                cache[file] = current_hash
        
        if project_changed:
            status.update("[bold blue]ℹ Changes detected. Updating holistic documentation...")
            run_generation_flow(target_path, DocType.all, status, auto_mode=True)
            file_service.save_cache(cache)
            status.stop()
            console.print("[bold green]✅ Update completed successfully.")
        else:
            status.stop()
            console.print(Panel("⚡ [bold green]Everything up to date.[/bold green]\nNo changes detected in project files.", title="Incremental Cache", border_style="green"))

@app.command()
def generar(
    path: str = typer.Argument(".", help="Path to document"),
    doc_type: Optional[DocType] = typer.Option(DocType.all, "--type", "-t"),
    auto: bool = typer.Option(False, "--auto")
):
    """Rule 4: Master Generation. Processes project context ONCE."""
    target_path = os.getcwd() if path == "." else os.path.abspath(path)
    engine_path = os.path.dirname(os.path.abspath(__file__))
    
    with console.status("[bold green]⚡ Iniciando generación maestra...", spinner="dots") as status:
        run_generation_flow(target_path, doc_type, status, auto_mode=auto)

def run_generation_flow(path: str, doc_type: DocType, status, auto_mode: bool = False):
    """Rule 3: Aggregated Context Router & Single Session Orchestration."""
    # Note: engine_path can be used here if config.json or system prompts are needed from the package
    config_data = load_config()
    if not config_data:
        status.stop(); console.print(Panel("[red]Error: Configura primero.[/red]", border_style="red")); raise typer.Exit(1)

    file_service = FileService()
    llm_service = LLMService()

    # --- RULE 2: SILENT PRE-FLIGHT ---
    graph_ctx = file_service.check_graph_context(path)
    if graph_ctx["has_graph"]:
        if graph_ctx["error"]: console.print(f"[bold red]⚠ Warning: {graph_ctx['error']}[/bold red]")
        else: console.print(f"[bold cyan][NOTICE] Graphify context detected.[/bold cyan]")

    state = WorkflowState(reference_path=path, has_graph=graph_ctx["has_graph"], output_language=config_data.get("output_language", "spanish"))
    
    try:
        # --- RULE 3: CONTEXT ROUTING ---
        status.update("[bold cyan]🔍 Routing aggregated context...")
        context = file_service.get_aggregated_context(path)
        if context["origin"] == "graphify": state.graphify_context = json.loads(context["content"])
        else: state.raw_code = context["content"]

        state.readme_context = file_service.read_local_readme(path)
        
        # 1. Researcher Global Analysis
        researcher = Researcher(model=config_data["model"], llm_service=llm_service)
        status.update("[bold cyan]🔍 Project-wide Technical Analysis...")
        state, resp_res = researcher.execute(state)

        if resp_res.status != "success":
            status.stop()
            error_report = f"• [bold red]Technical Analysis Failed:[/bold red]\n  {resp_res.message}\n\n[bold yellow]Report here:[/bold yellow] https://github.com/DaveCuc/diatax/issues"
            console.print(Panel(error_report, title="Error Crítico", border_style="red")); raise typer.Exit(1)

        # 2. Master Document Generation (ONE execution per session)
        final_results_md = {}
        types_to_process = [DocType.reference, DocType.howto, DocType.tutorial, DocType.explanation] if doc_type == DocType.all else [doc_type]
        for t in types_to_process:
            state = orchestrate_cycle(state, t, config_data["model"], llm_service, status=status, auto_mode=auto_mode)
            if state.markdown_draft: final_results_md[t.value] = state.markdown_draft; state.diataxis_results[t.value] = state.markdown_draft

        # 3. Export
        if state.diataxis_results:
            site_writer = SiteWriter(model=config_data["model"], llm_service=llm_service)
            status.update("[bold gold3]🏗️ Assembling Master Dashboard...")
            state, _ = site_writer.execute(state)
            file_service.export_results(state, final_results_md, reference_path=path)
            status.stop(); console.print("[bold green]🚀 Master documentation generated successfully!")
        else:
            status.stop(); console.print("[red]No content generated.[/red]")

    except typer.Exit: raise
    except Exception as e:
        if status: status.stop()
        console.print(Panel(f"[red]{str(e)}[red]", title="Error Crítico", border_style="red")); raise typer.Exit(1)

@app.command()
def audit(path: str = typer.Argument(".", help="Path to audit")):
    """Performs a security audit."""
    config_data = load_config()
    if not config_data: console.print(Panel("[red]Error: Configura primero.[/red]", border_style="red")); raise typer.Exit(1)
    file_service = FileService(); llm_service = LLMService(); files = file_service.get_python_files(path)
    if not files: return
    console.print(f"\n[bold magenta]🛡️ Iniciando Auditoría de Seguridad (SAST)...[/bold magenta]\n")
    with console.status("[bold magenta]🔍 Analizando...", spinner="bouncingBar") as status:
        for file in files:
            status.update(f"🛡️ Auditando: {file}...")
            state = WorkflowState()
            try:
                with open(file, "r", encoding="utf-8") as f: state.raw_code = f.read()
            except Exception: continue
            risk_agent = RiskAgent(model=config_data["model"], llm_service=llm_service)
            state, response = risk_agent.execute(state)
            if response.status == "success":
                risks = response.data.get("found_risks", [])
                if not risks: console.print(f"  [bold green]✅ {file}:[/bold green] Sin riesgos.")
                else:
                    console.print(f"  [bold red]❌ {file}:[/bold red] {len(risks)} riesgos.")
                    table = Table(show_header=True, header_style="bold white on red", border_style="red")
                    table.add_column("Gravedad"); table.add_column("Ubicación"); table.add_column("Descripción"); table.add_column("Solución")
                    for r in risks:
                        color = "red" if r['severity'].lower() == 'high' else "yellow"
                        table.add_row(f"[{color}]{r['severity']}[/{color}]", r.get('location', 'N/A'), r['description'], r['suggested_solution'])
                    console.print(table); console.print("") 
            else: console.print(f"  [bold yellow]⚠️ {file}:[/bold yellow] Fallo ({response.message})")
    console.print("\n[bold green]✔ Auditoría finalizada.[/bold green]\n")

if __name__ == "__main__":
    app()
