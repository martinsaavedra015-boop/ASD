"""Agrupa lineas de factura por NCM en items+subitems (punto 46 del
instructivo maestro) y arma las filas finales listas para el ORDEN."""
from collections import OrderedDict
from orden_builder import descripcion_oficial, limpiar_texto, mapear_unidad, formato_decimal, formatear_ncm

COL_ORDEN = list("ABCDEFGHIJKLMNO")


def _fila_item(codigo_ncm, cantidad_total, fob_total, unidad_codigo, unidad_texto,
                acuerdo, pais_origen, pais_procedencia, nuevo_usado, marca_libre,
                nombre_marca, peso_bruto, peso_neto, descripcion_cierre):
    desc_oficial = descripcion_oficial(codigo_ncm)
    columna_d = f'{desc_oficial} {descripcion_cierre}'.strip()
    cant_txt = str(int(cantidad_total)) if unidad_texto == "UNIDAD" else formato_decimal(cantidad_total)
    return {
        "A": "N", "B": formatear_ncm(codigo_ncm), "C": acuerdo, "D": columna_d, "E": unidad_codigo,
        "F": formato_decimal(fob_total), "G": cant_txt, "H": cant_txt,
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
        peso_bruto = grupo[0].get("peso_bruto")
        peso_neto = grupo[0].get("peso_neto")

        if len(grupo) == 1:
            linea = grupo[0]
            cant_str = str(int(linea["cantidad"])) if unidad_texto == "UNIDAD" else formato_decimal(linea["cantidad"])
            cierre = f'EN "{cant_str}" "{unidad_texto}" {limpiar_texto(linea["descripcion_factura"])}'
            filas.append(_fila_item(
                codigo_ncm, linea["cantidad"], linea["fob"], unidad_codigo, unidad_texto,
                acuerdo, pais_origen, pais_procedencia, nuevo_usado, marca_libre,
                nombre_marca, peso_bruto, peso_neto, cierre,
            ))
        else:
            cantidad_total = sum(l["cantidad"] for l in grupo)
            fob_total = sum(l["fob"] for l in grupo)
            cant_str = str(int(cantidad_total)) if unidad_texto == "UNIDAD" else formato_decimal(cantidad_total)
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

        if not peso_bruto and not peso_neto:
            notas.append(
                f"Partida {codigo_ncm}: peso bruto/neto en blanco, completar con packing list o B/L."
            )

    return filas, notas
