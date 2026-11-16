"""Parsea el Arancel Nacional Vigente (xlsx) en un indice consultable por
codigo NCM. Usa un cache en JSON para no re-parsear el xlsx (pesado) en
cada corrida.
"""
import openpyxl
import json
import re
import os
from config import ARANCEL_XLSX, ARANCEL_CACHE_JSON, IDENTIFICADORES_APRENDIDOS_JSON

CAPITULO_HDR_RE = re.compile(r"^Cap[ií]tulo\s+\d+$")


def _parsear_arancel():
    wb = openpyxl.load_workbook(ARANCEL_XLSX, data_only=True, read_only=True)
    ws = wb["Arancel"]

    records = {}
    cur_seccion = None
    cur_capitulo = None
    notas_buffer = []
    ultimo_codigo = None
    ultimo_fue_nota = False

    rows = list(ws.iter_rows(min_row=1, values_only=True))
    i = 0
    while i < len(rows):
        row = rows[i]
        col_a, col_b = row[0], row[1]
        if col_a == "NCM":
            i += 1
            continue
        if col_a is None and col_b:
            text = str(col_b).strip()
            if text.startswith("Sección"):
                cur_seccion = text
                notas_buffer.clear()
                ultimo_codigo = None
            elif CAPITULO_HDR_RE.match(text):
                titulo = None
                j = i + 1
                while j < len(rows) and j < i + 4:
                    nxt = rows[j][1]
                    if nxt and not re.match(r"^CAP\d+$", str(nxt).strip()):
                        titulo = str(nxt).strip()
                        break
                    j += 1
                cur_capitulo = f"{text}: {titulo}" if titulo else text
                notas_buffer.clear()
                ultimo_codigo = None
                i = j
                continue
            else:
                # Fila sin codigo en columna A: es la continuacion de la
                # descripcion del ultimo NCM (la fila se corta en dos
                # renglones) si trae datos de AEC/ANV/OMC, o si el
                # anterior directamente no tenia descripcion todavia.
                # Ambos casos son la misma partida, no una nota aparte.
                # Celdas de tasa vacias ("") cuentan como sin dato.
                aec, anv, omc = (row[c] if len(row) > c and not (row[c] is None or str(row[c]).strip() == "") else None for c in (2, 3, 4))
                continua = ultimo_codigo is not None and not ultimo_fue_nota and text[:1].islower() and not records[ultimo_codigo]["descripcion"].rstrip().endswith((".", ":"))
                if ultimo_codigo is not None and (aec is not None or anv is not None or omc is not None or continua):
                    rec = records[ultimo_codigo]
                    rec["descripcion"] = f'{rec["descripcion"]} {text}'.strip()
                    if aec is not None:
                        rec["aec"] = aec
                    if anv is not None:
                        rec["anv"] = anv
                    if omc is not None:
                        rec["omc"] = omc
                elif ultimo_fue_nota and not text.startswith("-") and notas_buffer:
                    # Segundo renglon de un encabezado sin codigo (ej. "- Asientos
                    # transformables en cama, excepto el material de" / "acampar o
                    # de jardin:"): pertenece al encabezado, no al NCM anterior.
                    notas_buffer[-1] = f"{notas_buffer[-1]} {text}"
                else:
                    notas_buffer.append(text)
                    # Solo un encabezado de guiones ("- Asientos ...") abre un
                    # bloque propio; otra fila suelta no corta la continuacion.
                    ultimo_fue_nota = text.startswith("-")
            i += 1
            continue
        if col_a is not None:
            codigo = str(col_a).strip()
            ultimo_fue_nota = False
            if codigo in records and re.match(r"^\d{4}\.\d", codigo):
                # Codigo repetido en el Excel fuente (errata, ej. 9401.41.00 "Los
                # demas" que en realidad es 9401.49.00): se conserva el primero.
                ultimo_codigo = None
                i += 1
                continue
            desc = str(col_b).strip() if col_b else ""
            aec = row[2] if len(row) > 2 else None
            anv = row[3] if len(row) > 3 else None
            omc = row[4] if len(row) > 4 else None
            records[codigo] = {
                "descripcion": desc, "aec": aec, "anv": anv, "omc": omc,
                "seccion": cur_seccion, "capitulo": cur_capitulo,
            }
            ultimo_codigo = codigo
        i += 1
    return records


def _cargar_records():
    if os.path.exists(ARANCEL_CACHE_JSON):
        with open(ARANCEL_CACHE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    records = _parsear_arancel()
    with open(ARANCEL_CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    return records


records = _cargar_records()


def _normalize(codigo):
    return codigo.replace(".", "")


_norm_index = {}
for _k in records:
    _norm_index.setdefault(_normalize(_k), []).append(_k)


def lookup_arancel(codigo):
    """Busca por codigo exacto (ignorando formato de puntos) o, si no
    existe, por prefijo (una partida de 4 digitos devuelve sus subpartidas).
    NOTA: la tasa de referencia a reportar siempre es ANV, no AEC."""
    n = _normalize(codigo)
    exact = [dict(records[k], codigo=k) for nk, ks in _norm_index.items() if nk == n for k in ks]
    if exact:
        return exact[0] if len(exact) == 1 else exact
    prefix = {k: v for nk, ks in _norm_index.items() if nk.startswith(n) for k in ks for v in [records[k]]}
    return prefix


def listar_subpartidas(codigo):
    """Devuelve todas las subpartidas de 8+ digitos que cuelgan del codigo
    dado. Funcion clave para la busqueda exhaustiva antes de resolver en un
    codigo residual 'Los demas' — ver PASO 3 de analizar_producto.py."""
    n = _normalize(codigo)
    resultado = []
    for k, v in records.items():
        kn = _normalize(k)
        if not kn or not kn[0].isdigit():
            continue
        if kn.startswith(n) and len(kn) >= 8:
            resultado.append({"codigo": k, "descripcion": v["descripcion"], "anv": v["anv"]})
    resultado.sort(key=lambda r: _normalize(r["codigo"]))
    return resultado


if __name__ == "__main__":
    print(f"Arancel cargado: {len(records)} codigos.")
    print(lookup_arancel("8443.32.38"))
