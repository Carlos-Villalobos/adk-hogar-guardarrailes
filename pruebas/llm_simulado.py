"""Modelo de lenguaje simulado y determinista, solo para probar el montaje sin red.

NO es un LLM: decide por palabras clave. Sirve para comprobar que el enrutado de
ADK, las herramientas y el guardarraíl funcionan. Las medidas del caso práctico
con un modelo real se hacen con correr_escenarios.py sin la opción --simulado.
"""
import re
from typing import AsyncGenerator

from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai import types


def _partes(llm_request: LlmRequest):
    for contenido in reversed(llm_request.contents or []):
        for parte in reversed(contenido.parts or []):
            yield contenido.role, parte


def _ultimo_texto_usuario(llm_request: LlmRequest) -> str:
    for rol, parte in _partes(llm_request):
        texto = getattr(parte, "text", None)
        if rol == "user" and texto and "QUOTED_AGENT_CONTENT" not in texto and not texto.startswith("For context:"):
            return texto
    return ""


def _respuesta_herramienta_reciente(llm_request: LlmRequest):
    """Respuesta de una herramienta real (no de transfer_to_agent) posterior al último mensaje."""
    for rol, parte in _partes(llm_request):
        texto = getattr(parte, "text", None)
        if texto and rol == "user" and "QUOTED_AGENT_CONTENT" not in texto and not texto.startswith("For context:"):
            return None
        fr = getattr(parte, "function_response", None)
        if fr is not None and fr.name != "transfer_to_agent":
            return fr
    return None


def _llamada(herramienta: str, /, **args) -> LlmResponse:
    parte = types.Part(function_call=types.FunctionCall(name=herramienta, args=args))
    return LlmResponse(content=types.Content(role="model", parts=[parte]))


def _texto(texto: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=texto)]))


class ModeloSimulado(BaseLlm):
    rol: str = "coordinador"
    model: str = "simulado"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        texto = _ultimo_texto_usuario(llm_request).lower()
        if self.rol == "coordinador":
            yield self._coordinador(texto)
            return
        resp = _respuesta_herramienta_reciente(llm_request)
        if resp is not None:
            yield _texto(f"Resultado de {resp.name}: {resp.response}")
            return
        yield self._especialista(texto)

    def _coordinador(self, texto: str) -> LlmResponse:
        if any(p in texto for p in ("temperatura", "calefacci", "frio", "frío")):
            return _llamada("transfer_to_agent", agent_name="agente_confort")
        if any(p in texto for p in ("consumo", "apaga", "dispositivo", "nevera")):
            return _llamada("transfer_to_agent", agent_name="agente_energia")
        if any(p in texto for p in ("puerta", "cerradura", "seguridad")):
            return _llamada("transfer_to_agent", agent_name="agente_seguridad")
        return _texto("Ningún especialista cubre esa petición.")

    def _especialista(self, texto: str) -> LlmResponse:
        habitacion = "dormitorio" if "dormitorio" in texto else "salon"
        numero = re.search(r"(\d+(?:[.,]\d+)?)", texto)
        if self.rol == "confort":
            if "calefacci" in texto and numero:
                return _llamada("fijar_calefaccion", habitacion=habitacion, objetivo_c=float(numero.group(1).replace(",", ".")))
            return _llamada("leer_temperatura", habitacion=habitacion)
        if self.rol == "energia":
            if "consumo" in texto:
                return _llamada("consumo_actual")
            for nombre in ("nevera", "horno", "televisor", "luz_salon"):
                if nombre in texto:
                    return _llamada("apagar_dispositivo", nombre=nombre)
            return _llamada("consumo_actual")
        if "abre" in texto or "abrir" in texto:
            return _llamada("abrir_puerta")
        return _llamada("estado_puerta")
