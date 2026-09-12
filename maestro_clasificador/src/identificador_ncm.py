"""Resuelve el codigo identificador de aduana (11 digitos + letra) para un
NCM de 8 digitos ya clasificado, usando NCMs_con_codigo_identificador.xlsx
como referencia, mas un cache de identificadores aprendidos en esta sesion
(los que el usuario va confirmando cuando no estan en la referencia).

IMPORTANTE: esto NO pone en duda la clasificacion (la partida de 8 digitos
ya esta firme). Solo resuelve si existe o no el sufijo adicional que usa
la aduana paraguaya para esa posicion puntual.
"""
import openpyxl
import re
import os
import json
from config import NCMS_IDENTIFICADOR_XLSX, IDENTIFICADORES_APRENDIDOS_JSON

_wb = openpyxl.load_workbook(NCMS_IDENTIFICADOR_XLSX, data_only=True, read_only=True)
_ws = _wb["Detalle"]
_codigos_raw = [r[0] for r in _ws.iter_rows(min_row=2, values_only=True) if r[0]]


def _solo_digitos(codigo):
    return re.sub(r"[^0-9]", "", codigo)


def formatear_identificador(codigo):
    """Normaliza un codigo identificador (con o sin puntos) al formato
    NNNN.NN.NN.NNNL. Devuelve (codigo_formateado, ok: bool)."""
    letra = codigo[-1] if codigo and codigo[-1].isalpha() else ""
    digitos = _solo_digitos(codigo)
    if len(digitos) != 11 or not letra:
        return codigo, False
    return f"{digitos[0:4]}.{digitos[4:6]}.{digitos[6:8]}.{digitos[8:11]}{letra}", True


_codigos_identificador = []
_vistos = set()
for _c in _codigos_raw:
    _f, _ok = formatear_identificador(_c)
    if _ok and _f not in _vistos:
        _codigos_identificador.append(_f)
        _vistos.add(_f)


def _cargar_aprendidos():
    if not os.path.exists(IDENTIFICADORES_APRENDIDOS_JSON):
        return {}
    with open(IDENTIFICADORES_APRENDIDOS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_aprendidos(datos):
    with open(IDENTIFICADORES_APRENDIDOS_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def guardar_identificador(codigo_ncm, identificador_completo):
    """Guarda un codigo identificador confirmado por el usuario para una
    partida ya clasificada (no estaba en la referencia subida)."""
    codigo_normalizado, ok = formatear_identificador(identificador_completo)
    if not ok:
        raise ValueError(f"'{identificador_completo}' no tiene el formato esperado (11 digitos + letra)")
    datos = _cargar_aprendidos()
    datos[_solo_digitos(codigo_ncm)] = codigo_normalizado
    _guardar_aprendidos(datos)
    return codigo_normalizado


def mensaje_identificador_faltante(codigo_ncm, descripcion_producto=""):
    """Mensaje estandar: la PARTIDA esta confirmada, solo falta el
    identificador de aduana (no es un punto de clasificacion dudoso)."""
    ref = f' ({descripcion_producto})' if descripcion_producto else ""
    return (
        f'NCM{ref}: la partida {codigo_ncm} esta confirmada, pero no tengo el '
        f'codigo identificador completo que usa la aduana (los 3 numeros y la '
        f'letra adicionales). Favor enviame el codigo identificador completo '
        f'para ir alimentando nuestra base.'
    )


def resolver_codigo_final(codigo_ncm_8digitos):
    """Match por los 8 digitos completos del NCM (no por 6).
    Devuelve (codigo_a_usar, tiene_identificador: bool)."""
    aprendidos = _cargar_aprendidos()
    clave = _solo_digitos(codigo_ncm_8digitos)
    if clave in aprendidos:
        return aprendidos[clave], True

    ocho = clave[:8]
    matches = [c for c in _codigos_identificador if _solo_digitos(c)[:8] == ocho]
    if not matches:
        return codigo_ncm_8digitos, False
    if len(matches) == 1:
        return matches[0], True
    return codigo_ncm_8digitos, False  # ambiguo -> flagear


if __name__ == "__main__":
    print(f"Identificadores de referencia cargados: {len(_codigos_identificador)}")
    for t in ["8443.99.22", "8443.99.23", "8415.10.11"]:
        print(t, "->", resolver_codigo_final(t))
