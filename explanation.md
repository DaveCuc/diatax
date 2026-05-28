# Explicación: El Ecosistema Diatax

Esta guía proporciona una visión profunda sobre el diseño, la arquitectura y la filosofía detrás de **Diatax**. Entender el "porqué" de este sistema es fundamental para aprovechar al máximo su capacidad de automatización técnica.

## La Filosofía: Diátaxis como Núcleo
El marco de trabajo **Diátaxis** no es solo una convención de nombres; es una respuesta a la crisis de la documentación técnica moderna. La mayoría de los proyectos sufren de "documentación monolítica", donde tutoriales, referencias y conceptos se mezclan, confundiendo al usuario.

Diatax implementa este marco mediante una orquestación de agentes especializados. Al separar las preocupaciones en cuatro tipos de documentos, garantizamos que el usuario encuentre exactamente lo que necesita:
*   **Tutoriales:** Para aprender haciendo.
*   **How-tos:** Para resolver problemas específicos.
*   **Referencias:** Para consultar hechos técnicos.
*   **Explicaciones:** Para comprender el contexto y el diseño.

## Arquitectura Multi-Agente
Diatax no es un simple script de LLM; es un sistema de **orquestación de agentes**. Cada agente tiene un rol definido y un conjunto de criterios de evaluación (Jueces) que aseguran la calidad:

1.  **Researcher (El Arquitecto):** Su función es realizar una "lectura global". A diferencia de un LLM que solo ve un archivo, el Researcher analiza la estructura completa del proyecto, identificando dependencias y brechas lógicas.
2.  **Writers (Los Especialistas):** Cada escritor está configurado con un *system prompt* específico que restringe su estilo y enfoque según el tipo de documento Diátaxis.
3.  **Judges (El Control de Calidad):** Actúan como un filtro de seguridad. Si un documento no cumple con los principios de su categoría (por ejemplo, si un "How-to" incluye demasiada teoría), el Juez lo rechaza y solicita correcciones, cerrando el ciclo de retroalimentación.
4.  **SiteWriter (El Arquitecto de Interfaz):** Este agente es responsable de la experiencia de usuario final. Su diseño "Zero-JS" (basado en selectores CSS `:has` y `:target`) garantiza que la documentación sea rápida, ligera y extremadamente portable.

## Decisiones de Diseño y Restricciones Técnicas

### 1. Seguridad "Fail-Secure"
La integración con el sistema de *keyring* del sistema operativo (macOS Keychain, Windows Credential Locker) es una decisión de diseño crítica. Al evitar el almacenamiento de claves API en archivos de texto plano, Diatax protege al usuario contra la exposición accidental de credenciales en repositorios Git.

### 2. Contexto Agregado vs. Graphify
El sistema maneja dos niveles de entrada:
*   **Raw Code:** Una concatenación inteligente de archivos fuente. Es ideal para proyectos pequeños y medianos.
*   **Graphify Context:** Para proyectos de gran escala, Diatax permite la inyección de grafos de dependencias. Esto es vital porque los LLMs tienen límites de ventana de contexto (*context window*); un grafo permite al agente entender la arquitectura sin necesidad de procesar cada línea de código individualmente.

### 3. Resiliencia ante el LLM
El sistema asume que los LLMs pueden fallar o devolver formatos inesperados. Por ello, implementa:
*   **JSON Resilience:** Uso de expresiones regulares (regex) para extraer estructuras de datos incluso cuando el modelo añade texto conversacional innecesario.
*   **Circuit Breaker:** Lógica de reintentos y manejo de errores que garantiza que, si un agente falla, el sistema no se detenga catastróficamente, sino que reporte el error de forma clara.

## Conexiones y Perspectivas
Diatax se sitúa en la intersección entre la **Ingeniería de Software** y la **Comunicación Técnica**. Mientras que herramientas como Docusaurus o MkDocs se enfocan en la *presentación*, Diatax se enfoca en la *generación y mantenimiento*.

La capacidad de realizar **actualizaciones incrementales** mediante hashing SHA-256 es lo que permite que Diatax sea una herramienta de desarrollo continuo y no solo un generador de "una sola vez". Al detectar cambios solo en los archivos modificados, el sistema optimiza el consumo de tokens y reduce drásticamente el tiempo de espera.

## Reflexión Final
La documentación técnica es un activo vivo. Al automatizar la creación de referencias y guías, Diatax permite que los desarrolladores se concentren en escribir código, mientras el sistema asegura que la "historia" del proyecto se mantenga coherente, precisa y, sobre todo, útil para el usuario final. La elegancia de su dashboard minimalista es un recordatorio de que, en la documentación, menos es a menudo más.