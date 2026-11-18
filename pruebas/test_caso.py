import asyncio
import pytest
from escenarios import ESCENARIOS
from correr_escenarios import correr
from hogar import herramientas as h


def setup_function():
    h.reiniciar_casa()


def test_calefaccion_valida():
    assert h.fijar_calefaccion("dormitorio", 21)["status"] == "ok"


def test_habitacion_inexistente():
    assert h.leer_temperatura("garaje")["status"] != "ok"


@pytest.mark.parametrize("esc", ESCENARIOS, ids=lambda e: e["id"])
def test_escenario_simulado(esc):
    r = asyncio.run(correr(esc, True))
    assert r["enrutado_ok"] and r["herramienta_ok"] and r["guardarrail_ok"] and r["efecto_ok"]
