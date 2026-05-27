import markdown
import re
from typing import Tuple, Dict, Any, List
from diatax.agents.base import BaseAgent
from diatax.core.models import AgentResponse, WorkflowState

class SiteWriter(BaseAgent):
    """
    Agente SiteWriter: Generador de sitios web estáticos minimalistas y elegantes.
    Nota: La implementación actual se centra en contenido textual y tipográfico; no incluye soporte para assets externos (imágenes, videos).
    """
    nombre_agente = "SiteWriter"
    rol = "Arquitecto de Interfaz Minimalista"

    def __init__(self, model: str, llm_service: Any):
        super().__init__(model)
        self.llm_service = llm_service

    def execute(self, state: WorkflowState) -> Tuple[WorkflowState, AgentResponse]:
        """
        Orquesta la generación de los archivos index.html y style.css con soporte multimedia.
        """
        try:
            from documentador.services.file_service import FileService
            fs = FileService()
            raiz = fs.encontrar_raiz_proyecto(state.ruta_referencia)
            assets_dir = raiz / "documentator_result" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            # 0. Procesar Multimedia en cada cuadrante
            if state.resultados_diataxis:
                for tipo, md in state.resultados_diataxis.items():
                    state.resultados_diataxis[tipo] = self._procesar_multimedia(md, raiz, assets_dir)

            # 1. Construir contenido HTML
            html_content = self._build_html(state)
            state.documento_web_html = html_content
            
            # 2. Construir contenido CSS
            css_content = self._build_css()
            state.documento_web_css = css_content

            return state, AgentResponse(status="success", data=html_content, message="Sitio minimalista premium generado con soporte de assets.")
        except Exception as e:
            return state, AgentResponse(status="error", data="", message=f"Error en generación de sitio: {str(e)}")

    def _procesar_multimedia(self, md_content: str, raiz: Path, assets_dir: Path) -> str:
        """
        Busca imágenes locales en el Markdown, las copia a assets/ y actualiza las rutas.
        """
        from diatax.services.file_service import FileService
        fs = FileService()
        
        # Encontrar patrones de imagen ![alt](ruta)
        patron = r'!\[(.*?)\]\((.*?)\)'
        
        def reemplazar_ruta(match):
            alt_text = match.group(1)
            ruta_original = match.group(2)
            
            # Solo procesar rutas locales (no URL externas ni base64)
            if ruta_original.startswith(("http://", "https://", "data:")):
                return match.group(0)
            
            # Intentar resolver la ruta relativa al proyecto
            ruta_absoluta = (raiz / ruta_original).resolve()
            if ruta_absoluta.exists() and ruta_absoluta.is_file():
                nueva_ruta = fs.copiar_asset(str(ruta_absoluta), assets_dir)
                return f"![{alt_text}]({nueva_ruta})"
            
            return match.group(0)

        return re.sub(patron, reemplazar_ruta, md_content)

    def _build_html(self, state: WorkflowState) -> str:
        # Generar navegación lateral izquierda (Secciones Globales)
        nav_links = '<li><a href="#inicio" class="nav-link">Introducción</a></li>'
        
        # Generar Contenido Central (Artículos)
        main_content = '<article id="inicio" class="page">'
        
        # Generar Navegación Derecha (Índice por bloque)
        right_sidebar_content = '<div class="toc-group" id="toc-inicio"><p class="toc-title">EN ESTA PÁGINA</p><ul><li><a href="#inicio">Arriba</a></li></ul></div>'
        
        # Inicio / Metadata
        meta = state.analisis_tecnico.get("metadata", {}) if state.analisis_tecnico else {}
        summary = state.analisis_tecnico.get("summary", "Sin resumen disponible.") if state.analisis_tecnico else ""
        
        main_content += f"""
            <header>
                <p class="badge">PROYECTO</p>
                <h1>Introducción</h1>
                <div class="metadata">
                    <span><strong>Versión:</strong> {meta.get('version', '1.0.0')}</span>
                    <span><strong>Autor:</strong> {meta.get('autor', 'Desconocido')}</span>
                </div>
                <p class="lead">{summary}</p>
            </header>
        </article>
        """

        if state.resultados_diataxis:
            for tipo, md in state.resultados_diataxis.items():
                anchor_id = tipo.lower()
                nav_links += f'<li><a href="#{anchor_id}" class="nav-link">{tipo.capitalize()}</a></li>'
                
                # Convertir MD a HTML
                html_snippet = markdown.markdown(md, extensions=['fenced_code', 'tables'])
                
                # Extraer encabezados de forma robusta e inyectar IDs únicos
                local_toc = f'<div class="toc-group" id="toc-{anchor_id}"><p class="toc-title">EN ESTA PÁGINA</p><ul>'
                
                def add_id(match):
                    level = match.group(1)
                    text = match.group(2)
                    clean_id = f"{anchor_id}-{re.sub(r'[^a-zA-Z0-0]', '-', text.lower()).strip('-')}"
                    return f'<h{level} id="{clean_id}">{text}</h{level}>'

                # Reemplazar h2 y h3 con IDs únicos
                html_snippet = re.sub(r'<h([2-3])>(.*?)</h[2-3]>', add_id, html_snippet)
                
                # Re-extraer para el TOC local
                headers = re.findall(r'<h([2-3]) id="(.*?)">(.*?)</h[2-3]>', html_snippet)
                for level, hid, text in headers:
                    indent = "margin-left: 1rem;" if level == "3" else ""
                    local_toc += f'<li style="{indent}"><a href="#{hid}">{text}</a></li>'
                
                local_toc += '</ul></div>'
                right_sidebar_content += local_toc

                main_content += f"""
                <article id="{anchor_id}" class="page">
                    <p class="badge">{tipo.upper()}</p>
                    <div class="markdown-body">
                        {html_snippet}
                    </div>
                </article>
                """

        return f"""<!-- Este es el archivo estructural. La apariencia visual y los colores (blanco, negro, dorado) se controlan completamente desde el archivo style.css -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentación Técnica - Premium</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="layout">
        <!-- Columna 1: Navegación Global -->
        <aside class="sidebar-left">
            <nav class="global-nav">
                <div class="brand">DIATAX</div>
                <ul>
                    {nav_links}
                </ul>
            </nav>
        </aside>

        <!-- Columna 2: Contenido Principal -->
        <main class="content">
            {main_content}
            <footer>
                <p>Documentación generada por Diatax</p>
            </footer>
        </main>

        <!-- Columna 3: Índice por bloque (Derecha) -->
        <aside class="sidebar-right">
            <nav class="local-nav">
                {right_sidebar_content}
            </nav>
        </aside>
    </div>
</body>
</html>"""

    def _build_css(self) -> str:
        return """/* ARCHIVO DE ESTILOS: Modifica las variables en :root para cambiar los colores, tipografía y medidas de la página directamente. */
:root {
  --ink: #111111; /* Negro para texto */
  --paper: #ffffff; /* Blanco para fondo */
  --accent: #d4af37; /* Dorado elegante para acentos, títulos y enlaces */
  --rule: #e5e5e5; /* Gris muy claro para bordes divisores */
  --terminal-bg: #0f1419; /* Fondo tipo consola moderna */
  --terminal-bar: #1e242e; /* Barra superior de consola */
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

/* --- LÓGICA DE PÁGINAS OCULTAS (ZERO JS) --- */
/* Nota: Al usar :target, el estado de la 'página' activa se pierde si se recarga el sitio sin el hash en la URL. */
.page { display: none; animation: fadeIn 0.4s ease; }

/* Mostrar #inicio por defecto si no hay target */
#inicio { display: block; }

/* Si hay un target, ocultar #inicio (a menos que él mismo sea el target) */
body:has(.page:target):not(:has(#inicio:target)) #inicio { display: none; }

/* Mostrar la página que es el target actual */
.page:target { display: block; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* --- SIDEBAR IZQUIERDA (Global Nav) --- */
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

/* Estilo para el link activo basado en el hash (limitado pero funcional) */
/* Nota: Al usar cero JS, no podemos mantener resaltado el botón global cuando se navega por sus sub-secciones. Dependemos del :hover para feedback visual. */

/* --- CONTENIDO CENTRAL --- */
.content { padding: 4rem 0; }
h1, h2, h3 { font-family: var(--serif); color: var(--ink); line-height: 1.2; margin-top: 3rem; }
h1 { font-size: clamp(2.5rem, 5vw, 3.5rem); margin-top: 0; margin-bottom: 2rem; border-bottom: 2px solid var(--rule); padding-bottom: 1rem; }
h2 { font-size: 1.8rem; color: var(--accent); border-bottom: 1px solid var(--rule); padding-bottom: 0.5rem; }
h3 { font-size: 1.3rem; }

.badge { font-size: 0.65rem; font-weight: 800; letter-spacing: 0.2em; color: var(--accent); margin-bottom: 1rem; text-transform: uppercase; }
.lead { font-size: 1.2rem; color: #444; font-style: italic; margin-bottom: 3rem; }
.metadata { display: flex; gap: 2rem; margin-bottom: 2.5rem; font-size: 0.85rem; color: #888; border-bottom: 1px solid var(--rule); padding-bottom: 1.5rem; }

/* --- SIDEBAR DERECHA (Local TOC) --- */
.sidebar-right { padding-top: 4rem; }
.local-nav { position: sticky; top: 4rem; border-left: 1px solid var(--rule); padding-left: 1.5rem; }
.toc-title { font-size: 0.65rem; font-weight: 900; color: #aaa; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-transform: uppercase; }

.toc-group { display: none; }
.toc-group ul { list-style: none; padding: 0; margin: 0; }
.toc-group li { margin-bottom: 0.75rem; }
.toc-group a { text-decoration: none; color: #777; font-size: 0.8rem; transition: color 0.2s; display: block; }
.toc-group a:hover { color: var(--accent); }

/* Resaltado del TOC local dinámico */
body:has(#inicio:target) #toc-inicio, 
body:not(:has(.page:target)) #toc-inicio { display: block; }

body:has(#reference:target) #toc-reference { display: block; }
body:has(#howto:target) #toc-howto { display: block; }
body:has(#tutorial:target) #toc-tutorial { display: block; }
body:has(#explanation:target) #toc-explanation { display: block; }

/* --- BLOQUES DE CÓDIGO (TERMINAL REALISTA) --- */
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

/* Efecto de barra de terminal */
pre::before {
    content: "● ● ●";
    display: block;
    height: 24px;
    background: var(--terminal-bar);
    margin: -1.5rem -1.5rem 1rem -1.5rem;
    padding: 0 1rem;
    color: #ff5f56; /* El primer punto rojo */
    font-size: 10px;
    line-height: 24px;
    letter-spacing: 2px;
    text-shadow: 14px 0 #ffbd2e, 28px 0 #27c93f;
    font-family: sans-serif;
}

code { font-family: var(--mono); background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.9em; color: #c51d1d; }
pre code { background: transparent; padding: 0; color: inherit; }

/* --- TABLAS Y OTROS --- */
table { width: 100%; border-collapse: collapse; margin: 2.5rem 0; font-size: 0.9rem; }
th, td { text-align: left; padding: 1rem; border-bottom: 1px solid var(--rule); }
th { color: var(--accent); font-family: var(--serif); font-weight: 700; }

/* --- FOOTER --- */
footer { margin-top: 10rem; padding-top: 2rem; border-top: 1px solid var(--rule); text-align: center; font-size: 0.75rem; color: #bbb; }

/* RESPONSIVE */
@media (max-width: 1100px) {
  .layout { grid-template-columns: 1fr; padding: 0 2rem; }
  .sidebar-left, .sidebar-right { display: none; }
  .page { display: block !important; margin-bottom: 6rem; } /* En móvil mostramos todo en cascada */
}
"""""