# Caso práctico: hogar inteligente con guardarraíles (Google ADK)

## Qué tienes que hacer tú (unos 20 minutos)

1. Copia esta carpeta `adk_hogar` a tu Mac (sin `.venv`).
2. Clave gratuita de Gemini: entra en https://aistudio.google.com/apikey y crea una API key.
3. En la terminal, dentro de `adk_hogar`:
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install google-adk
   export GOOGLE_API_KEY="tu_clave"
   export HOGAR_MODELO="gemini-flash-latest"   # o el modelo que te deje usar tu cuota
   ```
4. Ejecuta los escenarios (genera `resultados/traza.md` y `traza.json`):
   ```
   python correr_escenarios.py
   ```
5. Interfaz web para las capturas (desde `adk_hogar`, la carpeta que contiene `hogar/`):
   ```
   adk web
   ```
   Abre http://localhost:8000, elige `hogar` y escribe las 7 peticiones de `escenarios.py`.
6. Capturas que necesito (PNG):
   - Instalación: `pip show google-adk` con la versión.
   - `adk web` con E1 (traza coordinador → agente_confort → herramienta).
   - E3 y E5 (herramienta bloqueada, con el motivo) y E6 (permitida con CONFIRMO).
   - Pestaña de estado/eventos mostrando `auditoria`.
   - Terminal con `python correr_escenarios.py` y la tabla final.
7. Envíame `resultados/traza.md` y las capturas. Si algún escenario falla con el modelo real, es un resultado válido: lo analizamos.

Sin clave: `python correr_escenarios.py --simulado` y `python -m pytest pruebas` funcionan sin red (modelo simulado, NO sustituye la medición real).
