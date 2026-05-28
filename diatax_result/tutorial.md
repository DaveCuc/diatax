# Tutorial: Generación de Documentación con Diatax

Este tutorial te guiará a través de la creación de tu primera documentación técnica utilizando **Diatax**. Al finalizar, tendrás un sitio web estático, elegante y profesional que documenta tu código fuente automáticamente.

---

### Paso 1: Preparación del entorno
Asegúrate de estar en la carpeta raíz de tu proyecto. Diatax detectará automáticamente tus archivos `.py` y cualquier archivo `README.md` existente para contextualizar la documentación.

**Acción:** Ejecuta el siguiente comando en tu terminal:
```bash
python -m diatax.main generar .
```

**Qué esperar:** Verás una barra de progreso en la terminal mientras los agentes (Researcher, Writers, Judges) analizan tu código. El sistema te mostrará una previsualización del contenido generado para cada sección (Tutorial, How-to, etc.).

---

### Paso 2: Interacción con los Agentes (HITL)
Diatax utiliza un sistema de "Human-in-the-Loop" (HITL). Cuando un agente termine de redactar una sección, verás una previsualización en pantalla.

**Acción:** Ante la pregunta `¿Acción?`, elige una de las siguientes opciones:
*   **A (Aprobar):** Acepta el contenido y pasa a la siguiente sección.
*   **R (Rechazar/Corregir):** Te permitirá escribir un comentario para que el agente mejore el texto.
*   **I (Ignorar):** Continúa con el proceso sin realizar cambios.

**Qué esperar:** Si eliges **A**, el sistema continuará automáticamente con la siguiente categoría de la metodología Diátaxis.

---

### Paso 3: Visualización del Dashboard
Una vez que el proceso finalice, Diatax ensamblará todos los archivos en un sitio web estático.

**Acción:** Navega a la carpeta recién creada en tu proyecto:
```bash
cd diatax_result
```

**Qué esperar:** Encontrarás los archivos `index.html` y `style.css`. Abre `index.html` en tu navegador web favorito. Verás un dashboard minimalista con navegación lateral, índice de contenidos y una tipografía optimizada para lectura técnica.

---

### Paso 4: Actualización Incremental
A medida que tu código evoluciona, no es necesario regenerar toda la documentación desde cero.

**Acción:** Realiza cambios en tus archivos fuente y ejecuta:
```bash
python -m diatax.main update .
```

**Qué esperar:** Diatax comparará los hashes de tus archivos actuales con el caché previo (`.diatax_cache.json`). Solo se procesarán los archivos que hayan sido modificados, ahorrando tiempo y tokens de API.

---

### Resumen de resultados
Tras completar este tutorial, tu proyecto ahora cuenta con:
1.  **Documentación Diátaxis:** Archivos `.md` individuales para Referencia, How-to, Tutorial y Explicación.
2.  **Dashboard Web:** Un sitio `index.html` profesional en la carpeta `diatax_result/`.
3.  **Integración:** Un enlace automático a tu documentación insertado en tu `README.md` principal.

¡Tu proyecto ahora es mucho más accesible para otros desarrolladores!