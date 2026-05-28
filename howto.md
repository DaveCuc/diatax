# Guía de Uso: Generación de Documentación con Diatax

Esta guía detalla los pasos necesarios para automatizar la creación de documentación técnica siguiendo el marco de trabajo Diátaxis utilizando Diatax.

## 1. Generación de Documentación Maestra
Para generar el conjunto completo de documentación (Referencia, How-to, Tutorial y Explicación) de un proyecto:

1.  Navegue a la carpeta raíz de su proyecto en la terminal.
2.  Ejecute el comando de generación:
    ```bash
    python -m diatax.main generar .
    ```
3.  Si el modo interactivo está activo, revise la previsualización de cada documento en la terminal.
4.  Seleccione una acción para cada borrador:
    *   **A (Aprobar):** Finaliza el documento y continúa con el siguiente.
    *   **R (Rechazar):** Ingrese retroalimentación específica para que el agente reescriba el contenido.
    *   **I (Ignorar):** Salta el documento actual.

## 2. Ejecución en Modo Automático
Para generar la documentación sin interrupciones manuales (ideal para entornos CI/CD):

1.  Ejecute el comando incluyendo la bandera `--auto`:
    ```bash
    python -m diatax.main generar . --auto
    ```
2.  El sistema procesará todos los tipos de documentos de forma secuencial hasta completar el dashboard.

## 3. Actualización Incremental
Para actualizar únicamente los archivos que han sufrido cambios desde la última ejecución:

1.  Ejecute el comando de actualización:
    ```bash
    python -m diatax.main update .
    ```
2.  El sistema comparará los hashes actuales de los archivos con el registro en `.diatax_cache.json`.
3.  Si se detectan cambios, Diatax regenerará solo las secciones afectadas para optimizar el consumo de tokens.

## 4. Auditoría de Seguridad (SAST)
Para realizar un escaneo de vulnerabilidades en su código fuente:

1.  Ejecute el agente de riesgos:
    ```bash
    python -m diatax.main audit .
    ```
2.  Revise la tabla de resultados generada en la terminal, la cual clasifica los hallazgos por gravedad, ubicación, descripción y solución sugerida.

## 5. Integración de Contexto Externo
Si su proyecto es de gran escala, proporcione un mapa de dependencias para mejorar la precisión del análisis:

1.  Genere un archivo `graphify_result.json` en la raíz de su proyecto utilizando la herramienta [Graphify](https://github.com/safishamsi/graphify).
2.  Ejecute cualquier comando de `generar` o `update`.
3.  Diatax detectará automáticamente el archivo y lo utilizará como fuente primaria de contexto técnico en lugar del análisis de código plano.