# Diatax - Instrucciones del Proyecto

Este proyecto es un generador de documentación multiagente que utiliza LLMs para analizar código y generar documentación siguiendo el marco Diátaxis.

## Convenciones de Desarrollo

- **Lenguaje:** Python 3.10+
- **CLI:** Typer + Rich
- **IA:** LiteLLM (para soporte multi-proveedor)
- **Estilo:** Seguir PEP 8. Usar Type Hints en todas las funciones.
- **Estructura de Agentes:** Los agentes se encuentran en `diatax/agents/` y deben seguir una estructura de clase clara.

## Flujo de Trabajo

1. El `Researcher` analiza el código fuente.
2. El `Writer` genera la documentación basada en el análisis.
3. El `Judge` valida el resultado y sugiere mejoras.

## Comandos Útiles

- Ejecutar CLI: `python -m diatax.main --help`
- Configurar: `python -m diatax.main config --provider <p> --model <m>`
- Generar: `python -m diatax.main generar <ruta>`

## Notas de Configuración
La configuración se guarda en `~/.diatax_config.json`.
