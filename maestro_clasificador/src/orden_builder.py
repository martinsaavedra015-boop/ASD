import re
import unicodedata
from parse_arancel import records, _normalize
from identificador_ncm import resolver_codigo_final


def quitar_tildes(texto):
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def limpiar_texto(texto):
    """Mayusculas, sin tildes, sin periodos, comas ni guiones (solo
    espacios), sin comillas. (Confirmado por Martin: nunca puntos ni
    guiones ni comas en la descripcion, pese al ejemplo con typo del
    instructivo original.)"""
    t = quitar_tildes(texto).upper()
    t = t.replace('"', "").replace("'", "")
    t = re.sub(r"[.,\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def formato_decimal(numero):
    """Monto con 2 decimales y coma como separador decimal (formato
    paraguayo). Ej: 23730.00 -> '23730,00'"""
    return f"{numero:.2f}".replace(".", ",")


UNIDADES = {
    "03": "METRO CUADRADO", "04": "METRO CUBICO", "02": "METROS", "50": "MICROCURIE",
    "49": "MILICURIE", "68": "MILIGRAMO", "67": "MILILITRO", "11": "MILLAR", "08": "PAR",
    "12": "PIES", "13": "PIES CUADRADAS", "63": "RESMAS", "65": "ROLLOS", "29": "TONELADA",
    "07": "UNIDAD", "30": "YARDAS", "06": "1000 KILOWATT HORA", "64": "PIEZAS", "10": "QUILATE",
    "61": "KG.BRUTO", "01": "KILOGRAMO", "62": "KITS", "05": "LITROS", "14": "GRAMO",
    "31": "GRUESAS", "66": "BOVINAS", "16": "CAJAS", "48": "CURIE", "09": "DOCENA", "17": "GALONES",
}


def mapear_unidad(texto_factura):
    """Mapea el texto de unidad de la factura al codigo/texto oficial.

    Regla clave (confirmada por Martin): 'piezas'/'pza'/'pcs'/'set'/'unit'
    casi siempre son UNIDAD (07) en la practica, NO PIEZAS (64). PIEZAS (64)
    se reserva solo para casos con justificacion explicita puntual."""
    t = texto_factura.strip().lower()
    t = re.sub(r"^[\d.,\s]+", "", t)
    ambiguas_a_unidad = {"pza", "pzas", "piezas", "pcs", "pc", "pieces", "piece",
                          "set", "sets", "unit", "units", "unidad", "unidades"}
    if t in ambiguas_a_unidad:
        return "07", "UNIDAD"
    equivalencias = {
        "kg": "01", "kgs": "01", "kilogramo": "01", "kilogramos": "01",
        "caja": "16", "cajas": "16", "box": "16", "boxes": "16",
        "litro": "05", "litros": "05", "l": "05", "liters": "05",
        "rollo": "65", "rollos": "65", "roll": "65", "rolls": "65",
        "par": "08", "pares": "08", "pair": "08", "pairs": "08",
        "docena": "09", "docenas": "09", "dozen": "09",
        "metro": "02", "metros": "02", "m": "02",
        "m2": "03", "m3": "04",
    }
    codigo = equivalencias.get(t)
    if codigo:
        return codigo, UNIDADES[codigo]
    return "07", "UNIDAD"  # default: UNIDAD, se flaguea en NOTAS aparte


def jerarquia_ncm(codigo):
    """Devuelve [(codigo, descripcion), ...] desde el nivel de 8 digitos
    en adelante (excluye el texto generico de 6 digitos — punto 7 del
    instructivo maestro)."""
    n = _normalize(codigo)
    if not n or not n[0].isdigit():
        return []
    candidatos = []
    for k in records:
        kn = _normalize(k)
        if kn and kn[0].isdigit() and n.startswith(kn):
            candidatos.append((len(kn), k))
    candidatos.sort()
    resultado = []
    for _, k in candidatos:
        kn = _normalize(k)
        if len(kn) >= 8:
            resultado.append((k, records[k]["descripcion"]))
    return resultado


def descripcion_oficial(codigo):
    jer = jerarquia_ncm(codigo)
    partes = [limpiar_texto(desc) for _, desc in jer]
    return " ".join(p for p in partes if p)


def formatear_ncm(codigo):
    """Resuelve automaticamente el codigo identificador de 11 digitos+letra
    cuando corresponde (ver identificador_ncm.py)."""
    codigo_final, _tiene_id = resolver_codigo_final(codigo)
    return codigo_final


def construir_fila_orden(item):
    """item: dict con codigo_ncm, descripcion_producto, cantidad, fob,
    pais_origen_codigo, acuerdo, unidad_codigo (default '07'), nuevo_usado
    ('2'=nuevo default, '1'=usado)."""
    desc_oficial = descripcion_oficial(item["codigo_ncm"])
    cantidad = item["cantidad"]
    unidad_texto = item.get("unidad_texto", "UNIDAD")
    if item.get("descripcion_producto"):
        cierre = f'EN "{cantidad}" "{unidad_texto}" {limpiar_texto(item["descripcion_producto"])}'
    else:
        cierre = f'EN "{cantidad}" "{unidad_texto}"'
    columna_d = f"{desc_oficial} {cierre}"

    return {
        "A": "N",
        "B": formatear_ncm(item["codigo_ncm"]),
        "C": item.get("acuerdo", "SIN ACUERDO"),
        "D": columna_d,
        "E": item.get("unidad_codigo", "07"),
        "F": formato_decimal(item["fob"]),
        "G": str(int(cantidad)) if unidad_texto == "UNIDAD" else formato_decimal(cantidad),
        "H": str(int(cantidad)) if unidad_texto == "UNIDAD" else formato_decimal(cantidad),
        "I": item.get("peso_bruto", ""),
        "J": item.get("nuevo_usado", "2"),
        "K": item.get("pais_origen", ""),
        "L": item.get("pais_procedencia", ""),
        "M": item.get("peso_neto", ""),
        "N": item.get("marca_libre", "ML"),
        "O": item.get("nombre_marca", ""),
    }
