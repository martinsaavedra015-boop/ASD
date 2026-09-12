"""Registro persistente de NCMs ya confirmados por descripcion de producto
(para casos de clasificacion genuinamente dudosa entre subpartidas — NO
confundir con identificador_ncm.py, que es sobre el sufijo de aduana de una
partida ya firme)."""
import json
import os
from datetime import date
from config import REGISTRO_NCM_JSON


def _cargar():
    if not os.path.exists(REGISTRO_NCM_JSON):
        return {}
    with open(REGISTRO_NCM_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_archivo(datos):
    with open(REGISTRO_NCM_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def guardar_ncm_confirmado(descripcion_producto, ncm_completo, dato_que_completo=""):
    datos = _cargar()
    clave = descripcion_producto.strip().lower()
    datos[clave] = {
        "descripcion_original": descripcion_producto,
        "ncm_completo": ncm_completo,
        "dato_que_completo": dato_que_completo,
        "fecha": str(date.today()),
    }
    _guardar_archivo(datos)
    return datos[clave]


def buscar_ncm_confirmado(descripcion_producto):
    datos = _cargar()
    clave = descripcion_producto.strip().lower()
    if clave in datos:
        return datos[clave]
    palabras_buscadas = set(clave.split())
    mejor, mejor_overlap = None, 0
    for k, v in datos.items():
        overlap = len(palabras_buscadas & set(k.split()))
        if overlap > mejor_overlap and overlap >= max(2, len(palabras_buscadas) // 2):
            mejor, mejor_overlap = v, overlap
    return mejor


def listar_confirmados():
    return _cargar()
