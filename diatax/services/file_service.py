from __future__ import annotations
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING, List

if TYPE_CHECKING:
    from diatax.core.models import WorkflowState

class FileService:
    """
    Servicio encargado de la gestión de archivos, caché incremental
    y manejo de assets multimedia.
    """

    def obtener_contexto(self, ruta: str) -> Dict[str, Any]:
        """
        Lee el contexto de la ruta proporcionada. 
        Prioriza graph.json si existe. Si es un directorio, lee todos los archivos relevantes.
        """
        path = Path(ruta)
        
        # 1. Intentar buscar integración con Graphify (graph.json)
        directorio = path if path.is_dir() else path.parent
        graph_file = directorio / "graph.json"

        if graph_file.exists():
            try:
                with open(graph_file, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                return {
                    "origen": "graphify",
                    "contenido": datos,
                    "ruta": str(graph_file)
                }
            except (json.JSONDecodeError, OSError):
                pass

        # 2. Lectura de código fuente
        if not path.exists():
            raise FileNotFoundError(f"La ruta no existe: {ruta}")

        if path.is_dir():
            # Si es un directorio, recolectamos el contenido de los archivos relevantes
            extensiones_validas = {".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", ".h", ".cs"}
            contenido_acumulado = []
            
            # Recorrer archivos (limitando profundidad para evitar excesos)
            for root, dirs, files in os.walk(path):
                # Ignorar carpetas ocultas o de entorno
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'venv', 'node_modules', 'dist'}]
                
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in extensiones_validas:
                        try:
                            rel_path = file_path.relative_to(path)
                            with open(file_path, "r", encoding="utf-8") as f:
                                contenido_acumulado.append(f"--- FILE: {rel_path} ---\n{f.read()}\n")
                        except Exception:
                            continue
            
            if not contenido_acumulado:
                raise ValueError(f"No se encontraron archivos de código válidos en: {ruta}")
            
            return {
                "origen": "codigo_crudo",
                "contenido": "\n".join(contenido_acumulado),
                "ruta": str(path)
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                contenido = f.read()
            return {
                "origen": "codigo_crudo",
                "contenido": contenido,
                "ruta": str(path)
            }
        except OSError as e:
            raise OSError(f"No se pudo leer el archivo {ruta}: {str(e)}")

    def obtener_archivos_python(self, ruta_base: str) -> List[str]:
        """
        Busca archivos .py de forma recursiva ignorando carpetas de sistema/entorno.
        """
        path = Path(ruta_base)
        if path.is_file():
            return [str(path)] if path.suffix == ".py" else []

        excluidos = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "diatax_result"}
        archivos_py = []

        for p in path.rglob("*.py"):
            # Verificar si algún padre está en la lista de excluidos
            if not any(part in excluidos or part.startswith(".") for part in p.parts):
                archivos_py.append(str(p))

        return archivos_py

    def calcular_hash(self, ruta: str) -> str:
        """Calcula el hash SHA-256 del contenido de un archivo."""
        import hashlib
        path = Path(ruta)
        if not path.is_file():
            return ""
        
        try:
            contenido = path.read_bytes()
            return hashlib.sha256(contenido).hexdigest()
        except Exception:
            return ""

    def leer_cache(self) -> Dict[str, str]:
        """
        Lee el archivo de caché de hashes.
        Nota: Actualmente no se maneja la purga de caché antigua o archivos inexistentes.
        """
        cache_file = Path(".diatax_cache.json")
        if not cache_file.exists():
            return {}
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def guardar_cache(self, cache_data: Dict[str, str]):
        """
        Guarda la caché aplicando purga de huérfanos y límite de tamaño.
        """
        # 1. Limpieza de huérfanos (archivos que ya no existen)
        cache_limpia = {}
        for key, val in cache_data.items():
            # Intentar deducir la ruta del archivo (asumiendo formato path_tipo)
            try:
                posible_path = Path(key.rsplit("_", 1)[0])
                if posible_path.exists():
                    cache_limpia[key] = val
            except Exception:
                # Si el formato de la llave es extraño, lo conservamos por seguridad
                cache_limpia[key] = val
        
        # 2. Límite de tamaño (Máximo 1000 registros)
        if len(cache_limpia) > 1000:
            # Eliminar el 20% más antiguo (primeras llaves insertadas)
            num_a_eliminar = int(len(cache_limpia) * 0.20)
            claves = list(cache_limpia.keys())
            for i in range(num_a_eliminar):
                cache_limpia.pop(claves[i])

        cache_file = Path(".diatax_cache.json")
        cache_file.write_text(json.dumps(cache_limpia, indent=4), encoding="utf-8")

    def copiar_asset(self, ruta_origen: str, directorio_assets: Path) -> str:
        """
        Copia un archivo local al directorio de assets y devuelve la nueva ruta relativa.
        """
        origen = Path(ruta_origen)
        if not origen.exists() or not origen.is_file():
            return ruta_origen
        
        nombre_archivo = origen.name
        destino = directorio_assets / nombre_archivo
        
        try:
            shutil.copy2(origen, destino)
            return f"./assets/{nombre_archivo}"
        except Exception:
            return ruta_origen

    def encontrar_raiz_proyecto(self, ruta_inicial: str) -> Path:
        """
        Busca hacia arriba desde la ruta inicial hasta encontrar un marcador de raíz
        (.git, pyproject.toml, requirements.txt, .diatax_cache.json).
        Si no encuentra nada, devuelve el directorio de la ruta inicial.
        """
        path = Path(ruta_inicial).resolve()
        start_dir = path if path.is_dir() else path.parent
        
        marcadores = {".git", "pyproject.toml", "requirements.txt", ".diatax_cache.json", "GEMINI.md"}
        
        current = start_dir
        for _ in range(10):  # Limitar la búsqueda hacia arriba a 10 niveles
            if any((current / m).exists() for m in marcadores):
                return current
            if current.parent == current: # Llegamos a la raíz del sistema
                break
            current = current.parent
            
        return start_dir

    def cargar_grafo_estatico(self, ruta_referencia: str) -> Optional[Dict[str, Any]]:
        """
        Busca y carga un mapa de dependencias preexistente (Graphify, etc.) en la raíz.
        """
        raiz = self.encontrar_raiz_proyecto(ruta_referencia)
        nombres_grafo = ["graphify_result.json", "graph_meta.json", ".graphify.json"]
        
        for nombre in nombres_grafo:
            grafo_path = raiz / nombre
            if grafo_path.exists():
                try:
                    with open(grafo_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return None

    def leer_readme_local(self, ruta_referencia: str) -> str:
        """
        Busca y lee el README.md del proyecto desde la raíz detectada.
        """
        raiz = self.encontrar_raiz_proyecto(ruta_referencia)
        for nombre in ["README.md", "readme.md", "README.MD"]:
            readme_path = raiz / nombre
            if readme_path.exists():
                try:
                    return readme_path.read_text(encoding="utf-8")
                except Exception:
                    continue
        return ""

    def exportar_resultados(self, estado: WorkflowState, resultados_md: Dict[str, str], ruta_referencia: str = "."):
        """
        Exporta los resultados a una carpeta con diseño HTML premium y actualiza el README.md.
        """
        raiz = self.encontrar_raiz_proyecto(ruta_referencia)
        output_dir = raiz / "diatax_result"
        output_dir.mkdir(exist_ok=True)

        # 1. Guardar Markdowns crudos individuales
        for tipo, contenido in resultados_md.items():
            (output_dir / f"{tipo}.md").write_text(contenido, encoding="utf-8")

        # 2. Guardar el index.html semántico
        if estado.documento_web_html:
            (output_dir / "index.html").write_text(estado.documento_web_html, encoding="utf-8")

        # 3. Guardar el style.css externo
        if estado.documento_web_css:
            (output_dir / "style.css").write_text(estado.documento_web_css, encoding="utf-8")

        # 4. Actualización Segura del README.md del usuario
        self._actualizar_readme_con_link(raiz, output_dir)

    def _actualizar_readme_con_link(self, raiz: Path, output_dir: Path):
        """Inyecta de forma segura el link de documentación en el README del usuario."""
        marker_start = "<!-- DOCUMENTOR_START -->"
        marker_end = "<!-- DOCUMENTOR_END -->"
        
        rel_link = os.path.relpath(output_dir / "index.html", raiz).replace("\\", "/")
        
        content_to_inject = (
            f"\n{marker_start}\n"
            f"## 📚 Documentación Interactiva\n"
            f"Este proyecto utiliza un Dashboard Diátaxis autogenerado. [Ver Documentación Web Completa](./{rel_link})\n"
            f"{marker_end}\n"
        )

        readme_file = None
        for nombre in ["README.md", "readme.md", "README.MD"]:
            if (raiz / nombre).exists():
                readme_file = raiz / nombre
                break
        
        if not readme_file:
            # Si no existe README, creamos uno básico
            readme_file = raiz / "README.md"
            readme_file.write_text(f"# Proyecto\n{content_to_inject}", encoding="utf-8")
            return

        readme_content = readme_file.read_text(encoding="utf-8")
        
        if marker_start in readme_content and marker_end in readme_content:
            # Reemplazar contenido entre marcadores
            import re
            pattern = f"{re.escape(marker_start)}.*?{re.escape(marker_end)}"
            new_content = re.sub(pattern, content_to_inject.strip(), readme_content, flags=re.DOTALL)
            readme_file.write_text(new_content, encoding="utf-8")
        else:
            # Añadir al final si no existen marcadores
            with open(readme_file, "a", encoding="utf-8") as f:
                f.write(f"\n{content_to_inject}")
