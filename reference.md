# Referencia Técnica: Diatax

## Descripción General
Diatax es una herramienta de línea de comandos (CLI) diseñada para la generación automatizada de documentación técnica basada en el marco de trabajo **Diátaxis**. El sistema orquesta agentes especializados para analizar código fuente, generar contenido estructurado y ensamblar un tablero web estático.

## Arquitectura del Sistema
El sistema opera mediante un flujo de trabajo síncrono que integra los siguientes componentes:

### 1. Capa de Configuración y Seguridad
*   **`diatax.config`**: Gestiona la persistencia de la configuración.
    *   **Almacenamiento**: Utiliza `keyring` para credenciales (API Keys) y un archivo JSON (`~/.diatax_config.json`) para preferencias de usuario.
    *   **Política Fail-Secure**: Si el acceso al almacén de claves falla, el sistema interrumpe la ejecución para evitar la exposición de credenciales en texto plano.

### 2. Agentes (Agentes Especializados)
*   **`Researcher`**: Analiza la estructura del proyecto y el contexto (código fuente o grafos de dependencias) para generar metadatos técnicos.
*   **`Writers` (Tutorial, HowTo, Explanation, Reference)**: Generan contenido en formato Markdown siguiendo las directrices específicas de Diátaxis.
*   **`Judges`**: Evalúan la calidad del contenido generado por los escritores, validando el cumplimiento de los criterios técnicos y estilísticos.
*   **`RiskAgent`**: Realiza auditorías SAST (Static Application Security Testing) sobre el código fuente.
*   **`SiteWriter`**: Genera el tablero web estático (`index.html` y `style.css`) a partir de los resultados de los escritores.

### 3. Servicios
*   **`LLMService`**: Abstracción sobre `LiteLLM` para la comunicación con proveedores de IA.
    *   **Parámetros de solicitud**: `temperature=0.2`, `max_tokens=4000`.
    *   **Manejo de errores**: Implementa recuperación mediante expresiones regulares ante respuestas JSON malformadas.
*   **`FileService`**: Gestiona la lectura de archivos, el cálculo de hashes (SHA-256) para actualizaciones incrementales y la copia de activos multimedia.

## Estructura de Datos (WorkflowState)
El estado del sistema se mantiene en un objeto `WorkflowState` compartido entre agentes:
*   `raw_code`: Contenido del código fuente analizado.
*   `graphify_context`: Datos de dependencias (si están presentes).
*   `diataxis_results`: Diccionario que contiene el contenido generado para cada tipo de documento.
*   `technical_analysis`: Metadatos y resumen técnico del proyecto.
*   `writing_attempts`: Contador de intentos de escritura (límite: 3).

## Comandos de la CLI

| Comando | Descripción |
| :--- | :--- |
| `generar [path]` | Inicia el flujo de generación maestra de documentación. |
| `update [path]` | Ejecuta una actualización incremental basada en hashes de archivos. |
| `audit [path]` | Realiza un escaneo de seguridad (SAST) sobre los archivos del proyecto. |
| `config` | Configura el proveedor de IA, el modelo y el idioma de salida. |

## Limitaciones Técnicas
1.  **Contexto**: El sistema depende de la ventana de contexto del modelo seleccionado; proyectos masivos sin un archivo de contexto de grafos (`graphify_result.json`) pueden exceder los límites de tokens.
2.  **Generación de UI**: El `SiteWriter` utiliza generación basada en expresiones regulares para HTML/CSS; la complejidad del diseño está limitada a la estructura predefinida.
3.  **Auditoría**: El `RiskAgent` se basa en análisis de LLM, lo cual puede generar falsos positivos en comparación con herramientas SAST dedicadas (ej. Bandit, Semgrep).
4.  **Actualizaciones**: La lógica de regeneración parcial no está implementada; el sistema realiza una actualización holística al detectar cambios en cualquier archivo.