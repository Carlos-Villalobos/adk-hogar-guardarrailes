"""Herramientas simuladas de una casa inteligente (no hay hardware real).

Cada función es una herramienta de ADK: el modelo lee su docstring y sus tipos
para decidir cuándo llamarla. El estado de la casa vive en el diccionario CASA.
"""
import copy

from google.adk.tools import ToolContext

CASA_INICIAL = {
    "habitaciones": {
        "salon": {"temperatura_c": 24.5, "calefaccion_c": None},
        "dormitorio": {"temperatura_c": 18.0, "calefaccion_c": None},
    },
    "dispositivos": {
        "televisor": {"encendido": True, "w": 120},
        "horno": {"encendido": True, "w": 2000},
        "nevera": {"encendido": True, "w": 150},
        "luz_salon": {"encendido": True, "w": 40},
    },
    "puerta_principal": {"cerrada": True},
}

CASA: dict = {}


def reiniciar_casa() -> None:
    """Devuelve la casa simulada a su estado inicial (útil entre escenarios)."""
    CASA.clear()
    CASA.update(copy.deepcopy(CASA_INICIAL))


reiniciar_casa()


def _normalizar(texto: str) -> str:
    return texto.strip().lower().replace("ó", "o").replace("á", "a").replace(" ", "_")


def leer_temperatura(habitacion: str) -> dict:
    """Devuelve la temperatura actual en grados Celsius de una habitación.

    Args:
        habitacion: nombre de la habitación, por ejemplo "salon" o "dormitorio".
    """
    clave = _normalizar(habitacion)
    datos = CASA["habitaciones"].get(clave)
    if datos is None:
        return {"status": "error", "mensaje": f"Habitación desconocida: {habitacion}"}
    return {"status": "ok", "habitacion": clave, "temperatura_c": datos["temperatura_c"]}


def fijar_calefaccion(habitacion: str, objetivo_c: float) -> dict:
    """Programa la calefacción de una habitación a una temperatura objetivo.

    Args:
        habitacion: nombre de la habitación, por ejemplo "salon" o "dormitorio".
        objetivo_c: temperatura objetivo en grados Celsius.
    """
    clave = _normalizar(habitacion)
    datos = CASA["habitaciones"].get(clave)
    if datos is None:
        return {"status": "error", "mensaje": f"Habitación desconocida: {habitacion}"}
    datos["calefaccion_c"] = float(objetivo_c)
    return {"status": "ok", "habitacion": clave, "objetivo_c": float(objetivo_c)}


def guardar_preferencia(temperatura_c: float, tool_context: ToolContext) -> dict:
    """Guarda la temperatura preferida del usuario para futuras sesiones.

    Args:
        temperatura_c: temperatura preferida en grados Celsius.
    """
    tool_context.state["user:temperatura_preferida"] = float(temperatura_c)
    return {"status": "ok", "temperatura_preferida_c": float(temperatura_c)}


def consumo_actual() -> dict:
    """Devuelve el consumo eléctrico actual en vatios, total y por dispositivo."""
    por_dispositivo = {
        nombre: d["w"] for nombre, d in CASA["dispositivos"].items() if d["encendido"]
    }
    return {"status": "ok", "total_w": sum(por_dispositivo.values()), "por_dispositivo": por_dispositivo}


def apagar_dispositivo(nombre: str) -> dict:
    """Apaga un dispositivo eléctrico de la casa.

    Args:
        nombre: nombre del dispositivo, por ejemplo "televisor", "horno" o "luz_salon".
    """
    clave = _normalizar(nombre)
    dispositivo = CASA["dispositivos"].get(clave)
    if dispositivo is None:
        return {"status": "error", "mensaje": f"Dispositivo desconocido: {nombre}"}
    dispositivo["encendido"] = False
    return {"status": "ok", "dispositivo": clave, "encendido": False}


def estado_puerta() -> dict:
    """Indica si la puerta principal está cerrada con llave."""
    return {"status": "ok", "puerta_principal_cerrada": CASA["puerta_principal"]["cerrada"]}


def abrir_puerta() -> dict:
    """Abre la cerradura de la puerta principal. Es una acción crítica."""
    CASA["puerta_principal"]["cerrada"] = False
    return {"status": "ok", "puerta_principal_cerrada": False}
