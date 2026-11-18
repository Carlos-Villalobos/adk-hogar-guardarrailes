"""Ejecuta los escenarios con el Runner de ADK y guarda la traza en resultados/.

Uso:
    python correr_escenarios.py              # modelo real (HOGAR_MODELO, por defecto Gemini)
    python correr_escenarios.py --simulado   # modelo simulado, solo para probar el montaje
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import errors as genai_errors
from google.genai import types

import logging

from escenarios import ESCENARIOS

# ADK vuelca un traceback enorme en cada 503 aunque luego reintentemos; solo ocultamos ese ruido.
logging.disable(logging.ERROR)  # ADK reajusta los niveles de sus loggers al arrancar; esto es global
from hogar.agent import MODELO_POR_DEFECTO, construir
from hogar.herramientas import reiniciar_casa

APP = "hogar"
USUARIO = "usuario_demo"


def crear_agente(simulado: bool):
    if not simulado:
        return construir()
    from pruebas.llm_simulado import ModeloSimulado

    return construir(
        modelo_coordinador=ModeloSimulado(rol="coordinador"),
        modelo_confort=ModeloSimulado(rol="confort"),
        modelo_energia=ModeloSimulado(rol="energia"),
        modelo_seguridad=ModeloSimulado(rol="seguridad"),
    )


async def correr(escenario: dict, simulado: bool, intentos: int = 6) -> dict:
    """Reintenta con espera creciente ante 503/429 (el escenario se reinicia entero)."""
    for n in range(1, intentos + 1):
        try:
            return await _correr_una(escenario, simulado)
        except genai_errors.APIError as e:
            if e.code not in (429, 500, 503, 504) or n == intentos:
                raise
            espera = 15 * n
            print(f"[{escenario['id']}] {e.code} {e.status}; intento {n}/{intentos}, reintento en {espera} s", flush=True)
            await asyncio.sleep(espera)


async def _correr_una(escenario: dict, simulado: bool) -> dict:
    reiniciar_casa()
    servicio = InMemorySessionService()
    runner = Runner(app_name=APP, agent=crear_agente(simulado), session_service=servicio)
    sesion = await servicio.create_session(app_name=APP, user_id=USUARIO)
    mensaje = types.Content(role="user", parts=[types.Part(text=escenario["texto"])])

    autores, llamadas, texto_final = [], [], ""
    inicio = time.perf_counter()
    async for evento in runner.run_async(user_id=USUARIO, session_id=sesion.id, new_message=mensaje):
        if evento.author not in autores and evento.author != "user":
            autores.append(evento.author)
        for fc in evento.get_function_calls():
            if fc.name != "transfer_to_agent":
                llamadas.append({"herramienta": fc.name, "args": dict(fc.args or {})})
        if evento.is_final_response() and evento.content and evento.content.parts:
            texto_final = " ".join(p.text for p in evento.content.parts if p.text)
    duracion = time.perf_counter() - inicio

    sesion_final = await servicio.get_session(app_name=APP, user_id=USUARIO, session_id=sesion.id)
    auditoria = sesion_final.state.get("auditoria", [])
    especialistas = [a for a in autores if a.startswith("agente_")]

    esperado = escenario["especialista"]
    enrutado_ok = (especialistas[:1] == [esperado]) if esperado else (not especialistas)
    herramienta_ok = (
        any(l["herramienta"] == escenario["herramienta"] for l in llamadas)
        if escenario["herramienta"] else (not llamadas)
    )
    decisiones = [a["decision"] for a in auditoria]
    guardarrail_ok = (escenario["decision"] in decisiones) if escenario["decision"] else (not decisiones)
    efecto_ok = bool(escenario["efecto"]())

    return {
        "id": escenario["id"], "texto": escenario["texto"], "describe": escenario["describe"],
        "autores": autores, "llamadas": llamadas, "auditoria": auditoria,
        "respuesta": texto_final, "segundos": round(duracion, 1),
        "enrutado_ok": enrutado_ok, "herramienta_ok": herramienta_ok,
        "guardarrail_ok": guardarrail_ok, "efecto_ok": efecto_ok,
    }


def a_markdown(resultados: list, simulado: bool) -> str:
    cabecera = "SIMULADO (sin LLM real)" if simulado else f"MODELO REAL ({MODELO_POR_DEFECTO})"
    lineas = [f"# Resultados de los escenarios: {cabecera}", "",
              "| Id | Petición | Agentes | Herramienta | Guardarraíl | Enrutado | Efecto | Tiempo |",
              "|---|---|---|---|---|---|---|---|"]
    for r in resultados:
        herr = ", ".join(l["herramienta"] for l in r["llamadas"]) or "ninguna"
        dec = ", ".join(a["decision"] for a in r["auditoria"]) or "-"
        ok = lambda b: "sí" if b else "NO"
        lineas.append(f"| {r['id']} | {r['texto']} | {' → '.join(r['autores'])} | {herr} | {dec} "
                      f"| {ok(r['enrutado_ok'])} | {ok(r['efecto_ok'])} | {r['segundos']} s |")
    lineas += ["", "## Respuestas finales", ""]
    lineas += [f"- **{r['id']}**: {r['respuesta']}" for r in resultados]
    return "\n".join(lineas) + "\n"


async def principal(simulado: bool, repeticiones: int = 1) -> None:
    carpeta = Path("resultados")
    carpeta.mkdir(exist_ok=True)
    sufijo = "_simulado" if simulado else ""
    if repeticiones == 1:
        resultados = [await correr(e, simulado) for e in ESCENARIOS]
        (carpeta / f"traza{sufijo}.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
        (carpeta / f"traza{sufijo}.md").write_text(a_markdown(resultados, simulado), encoding="utf-8")
        print(a_markdown(resultados, simulado))
        return
    # Repeticiones: no pisa traza.md; guarda todas las ejecuciones y la tasa de acierto por escenario.
    tandas = [[await correr(e, simulado) for e in ESCENARIOS] for _ in range(repeticiones)]
    ok = lambda r: r["enrutado_ok"] and r["herramienta_ok"] and r["guardarrail_ok"] and r["efecto_ok"]
    modelo = "simulado" if simulado else MODELO_POR_DEFECTO
    lineas = [f"# Repeticiones ({repeticiones} ejecuciones por escenario), modelo: {modelo}", "",
              "| Id | Petición | Aciertos | Tiempo medio |", "|---|---|---|---|"]
    for i, e in enumerate(ESCENARIOS):
        rs = [t[i] for t in tandas]
        lineas.append(f"| {e['id']} | {e['texto']} | {sum(map(ok, rs))}/{repeticiones} "
                      f"| {sum(r['segundos'] for r in rs) / repeticiones:.1f} s |")
    texto = "\n".join(lineas) + "\n"
    (carpeta / f"repeticiones{sufijo}.json").write_text(json.dumps(tandas, ensure_ascii=False, indent=2), encoding="utf-8")
    (carpeta / f"repeticiones{sufijo}.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulado", action="store_true", help="usa un modelo simulado, sin red")
    parser.add_argument("--repeticiones", type=int, default=1, help="ejecuta cada escenario N veces")
    args = parser.parse_args()
    asyncio.run(principal(args.simulado, args.repeticiones))
