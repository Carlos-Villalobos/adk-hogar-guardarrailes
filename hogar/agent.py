"""Sistema multiagente de hogar inteligente con guardarraíl determinista.

root_agent es el coordinador (LlmAgent) y delega con sub_agents en tres
especialistas. Los especialistas llevan el guardarraíl como before_tool_callback.
El modelo se elige con la variable de entorno HOGAR_MODELO.
"""
import os

from google.adk.agents import LlmAgent

from .guardarrailes import guardarrail_herramientas
from .herramientas import (
    abrir_puerta,
    apagar_dispositivo,
    consumo_actual,
    estado_puerta,
    fijar_calefaccion,
    guardar_preferencia,
    leer_temperatura,
)

MODELO_POR_DEFECTO = os.environ.get("HOGAR_MODELO", "gemini-flash-latest")


def construir(modelo_coordinador=None, modelo_confort=None, modelo_energia=None, modelo_seguridad=None):
    """Crea el árbol de agentes. Los modelos se pueden sustituir (por ejemplo en tests)."""
    por_defecto = MODELO_POR_DEFECTO
    confort = LlmAgent(
        name="agente_confort",
        model=modelo_confort or por_defecto,
        description="Consulta temperaturas, programa la calefacción y guarda la temperatura preferida.",
        instruction=(
            "Eres el especialista en confort térmico de una casa. Usa siempre las herramientas "
            "para leer o cambiar la temperatura y responde con los datos que devuelvan. "
            "Si una herramienta responde 'bloqueado', explica el motivo al usuario y no insistas."
        ),
        tools=[leer_temperatura, fijar_calefaccion, guardar_preferencia],
        before_tool_callback=guardarrail_herramientas,
    )
    energia = LlmAgent(
        name="agente_energia",
        model=modelo_energia or por_defecto,
        description="Informa del consumo eléctrico y apaga dispositivos.",
        instruction=(
            "Eres el especialista en energía de una casa. Usa las herramientas para consultar el "
            "consumo o apagar dispositivos y responde con los datos que devuelvan. "
            "Si una herramienta responde 'bloqueado', explica el motivo y no insistas."
        ),
        tools=[consumo_actual, apagar_dispositivo],
        before_tool_callback=guardarrail_herramientas,
    )
    seguridad = LlmAgent(
        name="agente_seguridad",
        model=modelo_seguridad or por_defecto,
        description="Consulta y controla la puerta principal.",
        instruction=(
            "Eres el especialista en seguridad de una casa. Usa las herramientas para consultar "
            "o abrir la puerta principal. Si una herramienta responde 'bloqueado', explica al "
            "usuario qué debe hacer para confirmar y no vuelvas a intentarlo."
        ),
        tools=[estado_puerta, abrir_puerta],
        before_tool_callback=guardarrail_herramientas,
    )
    return LlmAgent(
        name="coordinador",
        model=modelo_coordinador or por_defecto,
        description="Coordinador de la casa inteligente.",
        instruction=(
            "Eres el coordinador de una casa inteligente. Transfiere la conversación al "
            "especialista adecuado: temperatura y calefacción a agente_confort; consumo y "
            "dispositivos a agente_energia; puerta y seguridad a agente_seguridad. "
            "Si la petición no corresponde a ninguno, responde tú que no puedes ayudar con eso."
        ),
        sub_agents=[confort, energia, seguridad],
    )


root_agent = construir()
