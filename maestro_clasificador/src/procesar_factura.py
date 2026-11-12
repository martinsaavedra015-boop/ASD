"""Agrupa lineas de factura por NCM en items+subitems (punto 46 del
instructivo maestro) y arma las filas finales listas para el ORDEN."""
import json
import re
from collections import OrderedDict
from config import UNIDAD_ESTADISTICA_KG_JSON
from orden_builder import descripcion_oficial, jerarquia_ncm, limpiar_texto, mapear_unidad, formato_decimal, formatear_ncm

COL_ORDEN = list("ABCDEFGHIJKLMNO")
MAX_DESC_DNA = 200
with open(UNIDAD_ESTADISTICA_KG_JSON, encoding="utf-8") as _f:
    NCM_ESTADISTICA_KG = {re.sub(r"\D", "", c)[:8] for c in json.load(_f)["ncm"]}  # largo maximo de la descripcion en KitApp (ORA-12899)


def _fila_item(codigo_ncm, cantidad_total, fob_total, unidad_codigo, unidad_texto,
                acuerdo, pais_origen, pais_procedencia, nuevo_usado, marca_libre,
                nombre_marca, peso_bruto, peso_neto, descripcion_cierre):
    desc_oficial = descripcion_oficial(codigo_ncm)
    columna_d = f'{desc_oficial} {descripcion_cierre}'.strip()
    if len(columna_d) > MAX_DESC_DNA:
        # La DNA (KIT_ART.LARTMERCAD) admite 200 caracteres. Como en los
        # despachos oficializados: se corta el texto del Arancel en la primera
        # coma ("PRODUCTOS Y PREPARACIONES ... PARA EL LAVADO DE LA PIEL");
        # si aun asi no entra, va directo el item sin el texto del Arancel.
        corto = " ".join(
            limpiar_texto(re.split(r"[,;]", desc)[0]) for _, desc in jerarquia_ncm(codigo_ncm)
        ).strip()
        columna_d = f'{corto} {descripcion_cierre}'.strip()
        if not corto or len(columna_d) > MAX_DESC_DNA:
            columna_d = descripcion_cierre.strip()
    cant_txt = str(int(cantidad_total)) if unidad_texto == "UNIDAD" else formato_decimal(cantidad_total)
    cant_estadistica = cant_txt
    if re.sub(r"\D", "", codigo_ncm)[:8] in NCM_ESTADISTICA_KG and peso_neto:
        cant_estadistica = peso_neto  # unidad estadistica KG: = peso neto
    return {
        "A": "N", "B": formatear_ncm(codigo_ncm), "C": acuerdo, "D": columna_d, "E": unidad_codigo,
        "F": formato_decimal(fob_total), "G": cant_txt, "H": cant_estadistica,
        "I": peso_bruto or "", "J": nuevo_usado, "K": pais_origen, "L": pais_procedencia,
        "M": peso_neto or "", "N": marca_libre, "O": nombre_marca,
    }


def _fila_subitem(cantidad, fob, marca_libre, nombre_marca, descripcion, cantidad_estadistica):
    """Subitems reutilizan A-F con otro significado (punto 46 del
    instructivo): A=cantidad subitem, B=FOB subitem, C=marca libre,
    D=nombre marca, E=descripcion (verbatim factura), F=cantidad
    estadistica subitem."""
    desc_limpia = limpiar_texto(descripcion)
    return {
        "A": str(int(cantidad)) if float(cantidad).is_integer() else formato_decimal(cantidad),
        "B": formato_decimal(fob),
        "C": marca_libre,
        "D": nombre_marca,
        "E": desc_limpia,
        "F": str(int(cantidad_estadistica)) if float(cantidad_estadistica).is_integer() else formato_decimal(cantidad_estadistica),
        "G": "", "H": "", "I": "", "J": "", "K": "", "L": "", "M": "", "N": "", "O": "",
    }


def _sumar_peso(grupo, campo):
    """Peso del item = suma de los pesos de todas sus lineas (antes solo se
    tomaba la primera linea del grupo). Acepta numeros o texto con coma
    decimal. Devuelve texto con coma decimal, o "" si falta en alguna linea."""
    total = 0.0
    for linea in grupo:
        v = linea.get(campo)
        if v in (None, ""):
            return ""
        total += float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
    return formato_decimal(total)


def procesar_factura(lineas, acuerdo="SIN ACUERDO", nuevo_usado="2", marca_libre="ML"):
    """lineas: lista de dicts ya clasificados, cada uno con:
    codigo_ncm, descripcion_factura, cantidad, unidad_texto_factura, fob,
    pais_origen, pais_procedencia (opcional), nombre_marca, peso_bruto
    (opcional), peso_neto (opcional).

    Devuelve: (filas [lista de dicts columna->valor], notas [lista de str])
    """
    grupos = OrderedDict()
    for linea in lineas:
        grupos.setdefault(linea["codigo_ncm"], []).append(linea)

    filas, notas = [], []

    for codigo_ncm, grupo in grupos.items():
        unidad_codigo, unidad_texto = mapear_unidad(grupo[0]["unidad_texto_factura"])
        pais_origen = grupo[0]["pais_origen"]
        pais_procedencia = grupo[0].get("pais_procedencia", pais_origen)
        nombre_marca = grupo[0]["nombre_marca"]
        peso_bruto = _sumar_peso(grupo, "peso_bruto")
        peso_neto = _sumar_peso(grupo, "peso_neto")

        if len(grupo) == 1:
            linea = grupo[0]
            cant_str = int(linea["cantidad"]) if unidad_texto == "UNIDAD" else linea["cantidad"]
            cierre = f'EN "{cant_str}" "{unidad_texto}" {limpiar_texto(linea["descripcion_factura"])}'
            filas.append(_fila_item(
                codigo_ncm, linea["cantidad"], linea["fob"], unidad_codigo, unidad_texto,
                acuerdo, pais_origen, pais_procedencia, nuevo_usado, marca_libre,
                nombre_marca, peso_bruto, peso_neto, cierre,
            ))
        else:
            cantidad_total = sum(l["cantidad"] for l in grupo)
            fob_total = sum(l["fob"] for l in grupo)
            cant_str = int(cantidad_total) if unidad_texto == "UNIDAD" else cantidad_total
            cierre = f'EN "{cant_str}" "{unidad_texto}" DETALLADO EN SUBITEM'
            filas.append(_fila_item(
                codigo_ncm, cantidad_total, fob_total, unidad_codigo, unidad_texto,
                acuerdo, pais_origen, pais_procedencia, nuevo_usado, marca_libre,
                nombre_marca, peso_bruto, peso_neto, cierre,
            ))
            for linea in grupo:
                filas.append(_fila_subitem(
                    linea["cantidad"], linea["fob"], marca_libre, linea["nombre_marca"],
                    linea["descripcion_factura"], linea["cantidad"],
                ))
            notas.append(
                f"Partida {codigo_ncm}: {len(grupo)} lineas de factura agrupadas en un item "
                f"con {len(grupo)} subitems (mismo NCM)."
            )

        if not peso_bruto or not peso_neto:
            notas.append(
                f"FALTA PESO en partida {codigo_ncm}: el peso nunca puede quedar en blanco. "
                f"Tomarlo del packing list/B/L o estimarlo por ficha tecnica antes de entregar."
            )

    return filas, notas
