"""Registro de sufijos de valor de KitApp (NA/NB/NC/ZA/ZB) e ISCPOSICION por
producto, para no volver a elegirlos a mano en cada despacho.
Archivo: data/sufijos_confirmados.json (versionado)."""
import json
import re
from datetime import date
from config import SUFIJOS_JSON


def _clave(marca, nombre):
    norm = lambda t: re.sub(r"\s+", " ", str(t or "")).strip().upper()
    return f"{norm(marca)}|{norm(nombre)}"


def _cargar():
    with open(SUFIJOS_JSON, encoding="utf-8") as f:
        return json.load(f)


def buscar_sufijos(marca, nombre, ncm=""):
    """Devuelve (sufijos_del_producto o None, criterio_general_del_ncm o None)."""
    datos = _cargar()
    prod = datos["productos"].get(_clave(marca, nombre))
    ncm8 = re.sub(r"\D", "", ncm)[:8]
    gen = next((v for k, v in datos["por_ncm"].items() if re.sub(r"\D", "", k) == ncm8), None)
    return prod, gen


def guardar_sufijos(marca, nombre, ncm, despacho="", **sufijos):
    datos = _cargar()
    datos["productos"][_clave(marca, nombre)] = {"ncm": ncm, **sufijos, "despacho": despacho,
                                                  "fecha": str(date.today())}
    with open(SUFIJOS_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
