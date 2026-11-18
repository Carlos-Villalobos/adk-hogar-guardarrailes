# Hogar inteligente con guardarraíles (Google ADK)

Caso práctico del Trabajo 2 de Inteligencia Ambiental (Máster en Sistemas Inteligentes, USAL): un sistema multi-agente con Google ADK en el que un guardarraíl determinista decide si cada herramienta puede ejecutarse, aunque el modelo la pida.

- Un coordinador (`LlmAgent`) delega con `sub_agents` en tres especialistas: confort, energía y seguridad.
- El mismo `before_tool_callback` ([hogar/guardarrailes.py](hogar/guardarrailes.py)) bloquea la calefacción fuera de 10-26 °C, apagar la nevera y abrir la puerta sin `CONFIRMO` en el mensaje del usuario. Cada decisión se guarda en `state["auditoria"]`.
- La casa es simulada ([hogar/herramientas.py](hogar/herramientas.py)); no hay hardware real.

## Requisitos

Python 3.11 o superior (probado con 3.12) y una clave de API de Gemini en `GOOGLE_API_KEY`.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY="tu_clave"            # no la guardes en ningún fichero del repositorio
export HOGAR_MODELO="gemini-3.5-flash-lite"  # por defecto: gemini-flash-latest
```

## Uso

```bash
python correr_escenarios.py                    # 7 escenarios, genera resultados/traza.md y traza.json
python correr_escenarios.py --repeticiones 4   # 4 ejecuciones por escenario, genera resultados/repeticiones.md
python correr_escenarios.py --simulado         # modelo simulado, sin red (solo prueba el montaje)
python -m pytest pruebas                       # 9 tests con modelo simulado
python listar_modelos.py                       # modelos que admite tu clave
adk web                                        # interfaz web de desarrollo en http://127.0.0.1:8000
```

`correr_escenarios.py` reintenta con espera creciente ante los errores 429, 500, 503 y 504 de la API. `adk web` no reintenta.

## Resultados

Con `gemini-3.5-flash-lite`, los 7 escenarios ([escenarios.py](escenarios.py)) acertaron en las 4 repeticiones (28 de 28); el detalle está en [resultados/repeticiones.md](resultados/repeticiones.md). Es una muestra pequeña con un solo modelo ligero. Los resultados del modo `--simulado` no cuentan como resultados reales.

## Limitaciones

- La confirmación de la puerta es una búsqueda de texto: `CONFIRMO` en cualquier parte del mensaje, con cualquier combinación de mayúsculas y minúsculas, la activa. No es una confirmación humana robusta.
- Las reglas están escritas a mano y solo cubren tres herramientas; el resto está permitido por defecto.
- El estado de la casa es global y vive en memoria.

## Licencia

[MIT](LICENSE).
