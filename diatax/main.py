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

# Configuración de silencio para logs y advertencias
warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("litellm").setLevel(logging.ERROR)

from diatax.config import guardar_configuracion, cargar_configuracion
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
    # Nota: 'TODO' significa 'Todos los cuadrantes' (All), no un pendiente de desarrollo.
    all = "TODO"

app = typer.Typer(help="Generador de documentación Multiagente basado en Diátaxis.")
console = Console()

# Catálogo estricto de modelos verificados (Gemini 3, 2.5 y Series Pro)
# Nota: LLMService soporta OpenAI, Anthropic, etc. vía LiteLLM. Este catálogo es una selección curada.
MODEL_CATALOG = {
    "1": {"proveedor": "gemini", "modelo": "gemini-3.5-flash", "nombre": "Gemini 3.5 Flash (Más Inteligente / Estable)"},
    "2": {"proveedor": "gemini", "modelo": "gemini-3.1-pro-preview", "nombre": "Gemini 3.1 Pro (Inteligencia Avanzada / Preview)"},
    "3": {"proveedor": "gemini", "modelo": "gemini-3-flash-preview", "nombre": "Gemini 3 Flash (Velocidad de Frontera / Preview)"},
    "4": {"proveedor": "gemini", "modelo": "gemini-3.1-flash-lite", "nombre": "Gemini 3.1 Flash-Lite (Económico / Estable)"},
    "5": {"proveedor": "gemini", "modelo": "gemini-2.5-pro", "nombre": "Gemini 2.5 Pro (Razonamiento Profundo y Código)"},
    "6": {"proveedor": "gemini", "modelo": "gemini-2.5-flash", "nombre": "Gemini 2.5 Flash (Balance Precio-Desempeño)"},
    "7": {"proveedor": "gemini", "modelo": "gemini-2.5-flash-lite", "nombre": "Gemini 2.5 Flash-Lite (Ultra Rápido y Barato)"},
    "8": {"proveedor": "gemini", "modelo": "deep-research-preview-04-2026", "nombre": "Gemini Deep Research (Investigación Autónoma)"},
    "9": {"proveedor": "groq", "modelo": "groq/llama-3.3-70b-versatile", "nombre": "Groq LLaMA 3.3 70B (Velocidad Extrema)"}
}

VERSION = "1.0.0"

def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]CLI Documentor v{VERSION}[/bold cyan] - [gold]Cuahutencos Tech[/gold]")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Muestra la versión y sale."
    ),
):
    """
    Generador de documentación Multiagente basado en Diátaxis.
    """
    pass

@app.command()
def config():
    """
    Configura el proveedor de IA y la llave de acceso mediante un menú interactivo.
    """
    console.print("\n[bold yellow]--- Configuración de IA - CLI Documentor ---[/bold yellow]")
    
    table = Table(title="Catálogo de Modelos Disponibles", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Modelo", style="cyan")
    table.add_column("Proveedor", style="green")

    for idx, data in MODEL_CATALOG.items():
        table.add_row(idx, data["nombre"], data["proveedor"].upper())

    console.print(table)
    
    seleccion = Prompt.ask("[bold]Elige una opción[/bold]", choices=list(MODEL_CATALOG.keys()))
    opcion = MODEL_CATALOG[seleccion]
    
    # Sanitización y Validación Anti-Vacíos
    api_key = ""
    while not api_key:
        api_key = Prompt.ask(f"[bold cyan]Ingresa tu API Key para {opcion['proveedor'].upper()}[/bold cyan]", password=True).strip()
        if not api_key:
            console.print("[bold red]❌ La API Key no puede estar vacía. Inténtalo de nuevo.[/bold red]")

    guardar_configuracion(opcion["proveedor"], opcion["modelo"], api_key)
    
    mensaje = f"[green]¡Configuración blindada exitosamente![/green]\n\nModelo: [bold]{opcion['nombre']}[/bold]\nProveedor: [bold]{opcion['proveedor'].upper()}[/bold]"
    console.print(Panel(mensaje, title="Sistema Configurado", border_style="green"))

def orquestar_ciclo(state: WorkflowState, tipo: DocType, model: str, llm: LLMService, status=None, modo_auto: bool = False) -> WorkflowState:
    """Orquesta un ciclo completo de Writer/Judge para un tipo específico con soporte HITL."""
    writers = {
        DocType.reference: ReferenceWriter,
        DocType.howto: HowToWriter,
        DocType.tutorial: TutorialWriter,
        DocType.explanation: ExplanationWriter
    }
    judges = {
        DocType.reference: ReferenceJudge,
        DocType.howto: HowToJudge,
        DocType.tutorial: TutorialJudge,
        DocType.explanation: ExplanationJudge
    }

    writer = writers[tipo](model=model, llm_service=llm)
    judge = judges[tipo](model=model, llm_service=llm)

    # Reset de estado para el nuevo tipo
    state.documento_final_aprobado = False
    state.intentos_escritura = 0
    state.feedback_juez = None

    max_intentos = 3
    while not state.documento_final_aprobado and state.intentos_escritura < max_intentos:
        intento = state.intentos_escritura + 1
        
        # Actualizar spinner con estados granulares
        if status:
            if intento == 1:
                status.update(f"[bold magenta]🧠 Pensando estructura para {tipo.value}...")
            else:
                status.update(f"[bold orange3]↻ Refinando {tipo.value} (Intento {intento}/{max_intentos})...")
        
        # Ejecutar Writer
        if status:
            status.update(f"[bold blue]✍️ Escribiendo borrador de {tipo.value}...")
        
        state, resp_write = writer.execute(state)
        
        if resp_write.status == "error":
            diag_msg = (
                f"[bold red]⚠ El ciclo se ha detenido para evitar un bucle infinito.[/bold red]\n\n"
                f"El agente [bold]{writer.nombre_agente}[/bold] reportó un error crítico:\n"
                f"[dim]'{resp_write.message}'[/dim]\n\n"
                f"[bold yellow]Posibles causas:[/bold yellow]\n"
                f"• [bold]Tokens Agotados:[/bold] Tu cuota con {model.split('/')[0].upper()} podría haber expirado.\n"
                f"• [bold]Límite de Velocidad (Rate Limit):[/bold] Estás enviando peticiones demasiado rápido.\n"
                f"• [bold]Conexión Inestable:[/bold] Hubo un micro-corte en el servicio de LiteLLM/Groq.\n"
                f"• [bold]Contexto demasiado grande:[/bold] El archivo es muy extenso para el modelo elegido."
            )
            console.print(Panel(diag_msg, title="Diagnóstico de Fallo", border_style="red"))
            break

        # --- FASE HITL (HUMAN-IN-THE-LOOP) ---
        if not modo_auto and state.borrador_markdown:
            if status: status.stop()
            
            # Mostrar extracto al usuario
            preview = state.borrador_markdown[:500] + "..." if len(state.borrador_markdown) > 500 else state.borrador_markdown
            console.print(Panel(preview, title=f"[bold cyan]Previsualización: {tipo.value.upper()}[/bold cyan]", border_style="cyan"))
            
            accion = Prompt.ask(
                "[bold yellow]Acción requerida[/bold yellow]: (A)probar, (R)echazar con Feedback, (I)gnorar y continuar automatizado?",
                choices=["A", "R", "I"],
                default="A"
            ).upper()
            
            if accion == "A":
                state.documento_final_aprobado = True
                console.print(f"[bold green]✅ {tipo.value.capitalize()} aprobado por el usuario.")
                if status: status.start()
                break
            elif accion == "R":
                feedback_humano = Prompt.ask("[bold cyan]Ingresa tu corrección para la IA[/bold cyan]")
                # Inyectar feedback humano en la pizarra para el Writer
                state.feedback_juez = f"El desarrollador líder ha rechazado el borrador anterior con esta instrucción: {feedback_humano}. Reescribe el documento aplicando estrictamente este cambio."
                state.intentos_escritura = 0 # Reiniciar intentos para dar oportunidad a la IA
                console.print("[dim]↻ Reiniciando ciclo de escritura con feedback humano...[/dim]")
                if status: status.start()
                continue
            else: # Ignorar e ir al Juez automático
                console.print("[dim]→ Continuando con validación automática del Juez...[/dim]")
                if status: status.start()

        # Ejecutar Judge (Validación Automática)
        if status:
            status.update(f"[bold yellow]⚖️ Evaluando calidad de {tipo.value}...")
        
        state, resp_judge = judge.execute(state)
        
        if resp_judge.status == "error":
            console.print(f"[red]⚠ Error en evaluación del Juez. Abortando ciclo.[/red]")
            break
        
        if state.documento_final_aprobado:
            console.print(f"[bold green]✅ {tipo.value.capitalize()} listo y aprobado.")
        elif intento == max_intentos:
            console.print(f"[bold red]⚠️ Cortocircuito activado: {tipo.value.capitalize()} no logró el estándar Diátaxis en {max_intentos} intentos. Forzando avance para evitar bloqueos.[/bold red]")
            break

    return state

@app.command()
def update(
    ruta: str = typer.Argument(".", help="Ruta del código a actualizar"),
    tipo: DocType = typer.Option(DocType.all, "--tipo", "-t", help="Tipo de documentación"),
    auto: bool = typer.Option(False, "--auto", help="Modo 100% automático (sin pausas interactivas)")
):
    """
    Actualiza la documentación solo para los archivos que han cambiado.
    """
    file_service = FileService()
    archivos = file_service.obtener_archivos_python(ruta)
    
    if not archivos:
        console.print(f"[yellow]No se encontraron archivos .py en {ruta}[/yellow]")
        return

    with console.status("[bold green]⚡ Iniciando actualización inteligente...", spinner="dots") as status:
        cache = file_service.leer_cache()
        cambios_detectados = False
        
        for archivo in archivos:
            # Identificador único en el caché (ruta + tipo)
            current_hash = file_service.calcular_hash(archivo)
            cache_key = f"{archivo}_{tipo.value}"
            
            if cache.get(cache_key) == current_hash and current_hash != "":
                continue

            cambios_detectados = True
            status.update(f"[bold blue]ℹ Cambios en {archivo}. Actualizando...[/bold blue]")
            ejecutar_flujo_generacion(archivo, tipo, status, modo_auto=auto)
            
            # Guardar hash
            cache[cache_key] = current_hash
            file_service.guardar_cache(cache)

        if not cambios_detectados:
            status.stop()
            console.print(Panel(
                f"⚡ [bold green]Todo al día[/bold green]\nNo se detectaron cambios en los archivos de {ruta}.",
                title="Caché Incremental",
                border_style="green"
            ))
        else:
            console.print("[dim]✔ Caché de hashes actualizado.[/dim]")

@app.command()
def generar(
    ruta: str = typer.Argument(".", help="Ruta del código a documentar"),
    tipo: Optional[DocType] = typer.Option(None, "--tipo", "-t", help="Tipo de documentación Diátaxis"),
    auto: bool = typer.Option(False, "--auto", help="Modo 100% automático (sin pausas interactivas)")
):
    """Lee el código y genera la documentación técnica completa."""
    # Menú Interactivo si no hay tipo
    if tipo is None:
        console.print("\n[bold yellow]Selecciona el tipo de documentación:[/bold yellow]")
        console.print("1) Reference [dim](Referencia técnica)[/dim]")
        console.print("2) How-to [dim](Guías de tareas)[/dim]")
        console.print("3) Tutorial [dim](Aprendizaje)[/dim]")
        console.print("4) Explanation [dim](Comprensión)[/dim]")
        console.print("5) [bold red]TODO[/bold red] [dim](Generar los 4 cuadrantes)[/dim]")
        
        opcion = Prompt.ask("Opción", choices=["1", "2", "3", "4", "5"], default="1")
        mapeo = {"1": DocType.reference, "2": DocType.howto, "3": DocType.tutorial, "4": DocType.explanation, "5": DocType.all}
        tipo = mapeo[opcion]

    file_service = FileService()
    archivos = file_service.obtener_archivos_python(ruta)
    
    if not archivos:
        console.print(f"[yellow]No se encontraron archivos .py en {ruta}[/yellow]")
        return

    with console.status("[bold green]⚡ Iniciando proceso de documentación...", spinner="dots") as status:
        for archivo in archivos:
            status.update(f"[bold cyan]📄 Procesando: {archivo}...")
            ejecutar_flujo_generacion(archivo, tipo, status, modo_auto=auto)

def ejecutar_flujo_generacion(ruta: str, tipo: DocType, status, modo_auto: bool = False):
    """
    Lógica central de generación. 
    Nota: La lógica Human-in-the-Loop es básica; falta manejo avanzado de historial de contexto largo.
    """
    config = cargar_configuracion()
    if not config:
        status.stop()
        console.print(Panel("[red]Error: Configura primero.[/red]", border_style="red"))
        raise typer.Exit(1)

    state = WorkflowState()
    state.ruta_referencia = ruta
    file_service = FileService()
    llm_service = LLMService()

    try:
        status.update("[bold cyan]🔍 Leyendo y analizando código fuente...")
        # Cargar contexto del README real si existe
        state.contexto_readme = file_service.leer_readme_local(ruta)
        
        # Cargar mapa de dependencias estático si existe (Graphify)
        state.mapa_dependencias = file_service.cargar_grafo_estatico(ruta)
        
        contexto = file_service.obtener_contexto(ruta)
        if contexto["origen"] == "graphify":
            state.contexto_graphify = contexto["contenido"]
        else:
            state.codigo_crudo = contexto["contenido"]

        # 1. Fase Researcher + Human-in-the-Loop
        researcher = Researcher(model=config["modelo"], llm_service=llm_service)
        status.update("[bold cyan]🔍 Investigando estructura y huecos del código...")
        state, resp_res = researcher.execute(state)

        if resp_res.status != "success":
            status.stop()
            console.print(Panel(f"[bold red]Falla en el análisis técnico:[/bold red]\n{resp_res.message}", title="Error de Researcher", border_style="red"))
            raise typer.Exit(1)

        huecos = state.analisis_tecnico.get("huecos_de_codigo", [])
        if huecos and not modo_auto:
            status.stop() # Pausar spinner para el prompt
            console.print(Panel("\n".join([f"• {h}" for h in huecos]), title="[bold yellow]Human-in-the-Loop: Huecos detectados[/bold yellow]", border_style="yellow"))
            explicacion = Prompt.ask("[bold cyan]¿Puedes explicar qué hacen estas partes? (Enter para omitir)[/bold cyan]")
            if explicacion:
                state.contexto_usuario = explicacion
            status.start() # Reanudar spinner

        # 2. Orquestación de agentes Diátaxis
        resultados_finales_md = {}
        tipos_a_procesar = [DocType.reference, DocType.howto, DocType.tutorial, DocType.explanation] if tipo == DocType.all else [tipo]

        for t in tipos_a_procesar:
            state = orquestar_ciclo(state, t, config["modelo"], llm_service, status=status, modo_auto=modo_auto)
            if state.borrador_markdown:
                resultados_finales_md[t.value] = state.borrador_markdown
                state.resultados_diataxis[t.value] = state.borrador_markdown

        # 3. Generación de Sitio Web (SiteWriter)
        if state.resultados_diataxis:
            site_writer = SiteWriter(model=config["modelo"], llm_service=llm_service)
            status.update("[bold gold3]🏗️ Ensamblando Dashboard Web...")
            state, resp_site = site_writer.execute(state)
            
            # 4. Fase de Exportación Física
            status.update("[bold green]💾 Exportando resultados a la raíz del proyecto...")
            file_service.exportar_resultados(state, resultados_finales_md, ruta_referencia=ruta)
            
            raiz_proyecto = file_service.encontrar_raiz_proyecto(ruta)
            final_msg = (
                f"[bold green]✔ ¡Proceso finalizado con éxito![/bold green]\n\n"
                f"La documentación ha sido exportada a: [bold cyan]{raiz_proyecto / 'diatax_result'}[/bold cyan]\n"
                f"Puedes abrir el sitio premium aquí: [bold yellow]{raiz_proyecto / 'diatax_result' / 'index.html'}[/bold yellow]"
            )
            status.stop()
            console.print("[bold green]🚀 Proceso finalizado. Documentación web generada con éxito.")
            console.print(Panel(final_msg, title="Exportación Completada", border_style="cyan", padding=(1, 2)))
        else:
            if status: status.stop()
            console.print("[red]No se pudo generar ningún contenido para exportar.[/red]")

    except Exception as e:
        if status: status.stop()
        console.print(Panel(f"[red]{str(e)}[/red]", title="Error Crítico", border_style="red"))
        raise typer.Exit(1)

@app.command()
def audit(
    ruta: str = typer.Argument(".", help="Ruta del código a auditar")
):
    """
    Realiza una auditoría de seguridad profunda en busca de vulnerabilidades.
    """
    config = cargar_configuracion()
    if not config:
        console.print(Panel("[red]Error: Configura primero.[/red]", border_style="red"))
        raise typer.Exit(1)

    file_service = FileService()
    llm_service = LLMService()
    archivos = file_service.obtener_archivos_python(ruta)

    if not archivos:
        console.print(f"[yellow]No se encontraron archivos para auditar en {ruta}[/yellow]")
        return

    console.print(f"\n[bold magenta]🛡️ Iniciando Auditoría de Seguridad (SAST)...[/bold magenta]\n")
    
    with console.status("[bold magenta]🔍 Analizando vulnerabilidades...", spinner="bouncingBar") as status:
        for archivo in archivos:
            status.update(f"[bold magenta]🛡️ Auditando: {archivo}...")
            
            # Preparar estado para el RiskAgent
            state = WorkflowState()
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    state.codigo_crudo = f.read()
            except Exception:
                continue

            risk_agent = RiskAgent(model=config["modelo"], llm_service=llm_service)
            state, response = risk_agent.execute(state)

            if response.status == "success":
                riesgos = response.data.get("riesgos_encontrados", [])
                
                if not riesgos:
                    console.print(f"  [bold green]✅ {archivo}:[/bold green] Sin riesgos detectados.")
                else:
                    console.print(f"  [bold red]❌ {archivo}:[/bold red] Se encontraron {len(riesgos)} riesgos.")
                    
                    table = Table(show_header=True, header_style="bold white on red", border_style="red")
                    table.add_column("Gravedad", width=10)
                    table.add_column("Ubicación", width=20)
                    table.add_column("Descripción")
                    table.add_column("Solución Sugerida")

                    for r in riesgos:
                        color = "red" if r['gravedad'].lower() == 'alta' else "yellow" if r['gravedad'].lower() == 'media' else "blue"
                        table.add_row(
                            f"[{color}]{r['gravedad']}[/{color}]",
                            r.get('linea_o_funcion', 'N/A'),
                            r['descripcion'],
                            r['solucion_sugerida']
                        )
                    console.print(table)
                    console.print("") # Espacio extra
            else:
                console.print(f"  [bold yellow]⚠️ {archivo}:[/bold yellow] No se pudo auditar ({response.message})")

    console.print("\n[bold green]✔ Auditoría finalizada.[/bold green]\n")

if __name__ == "__main__":
    app()
