"""Guardarraíl determinista: reglas de seguridad fuera del modelo.

Se engancha como before_tool_callback de cada especialista. Corre ANTES de que
la herramienta se ejecute y puede bloquearla devolviendo un diccionario, que ADK
usa como resultado de la herramienta en lugar de ejecutarla.

La confirmación humana se busca en el último mensaje del usuario, no en algo que
el modelo pueda escribir por su cuenta: así el LLM no puede autoconfirmarse.
"""
RANGO_CALEFACCION_C = (10.0, 26.0)
DISPOSITIVOS_PROTEGIDOS = {"nevera"}
PALABRA_CONFIRMACION = "CONFIRMO"


def _texto_usuario(tool_context) -> str:
    contenido = getattr(tool_context, "user_content", None)
    if contenido is None or not getattr(contenido, "parts", None):
        return ""
    return " ".join(p.text for p in contenido.parts if getattr(p, "text", None))


def _registrar(tool_context, herramienta: str, args: dict, decision: str, motivo: str) -> None:
    auditoria = list(tool_context.state.get("auditoria", []))
    auditoria.append({"herramienta": herramienta, "args": dict(args), "decision": decision, "motivo": motivo})
    tool_context.state["auditoria"] = auditoria


def guardarrail_herramientas(tool, args, tool_context):
    """before_tool_callback: devuelve None para permitir o un dict para bloquear."""
    nombre = tool.name
    motivo = ""

    if nombre == "fijar_calefaccion":
        minimo, maximo = RANGO_CALEFACCION_C
        objetivo = args.get("objetivo_c")
        if objetivo is None or not (minimo <= float(objetivo) <= maximo):
            motivo = f"El objetivo debe estar entre {minimo:g} y {maximo:g} grados."
    elif nombre == "apagar_dispositivo":
        if str(args.get("nombre", "")).strip().lower() in DISPOSITIVOS_PROTEGIDOS:
            motivo = "Este dispositivo está protegido y no se puede apagar."
    elif nombre == "abrir_puerta":
        if PALABRA_CONFIRMACION not in _texto_usuario(tool_context).upper():
            motivo = f"Acción crítica: requiere que el usuario escriba {PALABRA_CONFIRMACION} en su mensaje."

    if motivo:
        _registrar(tool_context, nombre, args, "bloqueado", motivo)
        return {"status": "bloqueado", "motivo": motivo}
    _registrar(tool_context, nombre, args, "permitido", "")
    return None
