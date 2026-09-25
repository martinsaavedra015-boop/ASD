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
                # descripcion del ultimo NCM (la fila se corta en dos o mas
                # renglones) si trae datos de AEC/ANV/OMC, o si el ultimo
                # NCM todavia no recibio sus tasas (renglon intermedio de
                # una descripcion larga, ej. 3401.30.00). Todos esos casos
                # son la misma partida, no una nota aparte.
                aec = row[2] if len(row) > 2 else None
                anv = row[3] if len(row) > 3 else None
                omc = row[4] if len(row) > 4 else None
                trae_tasas = aec is not None or anv is not None or omc is not None
                sin_tasas_aun = (
                    ultimo_codigo is not None
                    and len(ultimo_codigo.replace(".", "")) >= 7  # solo lineas arancelarias, no partidas de 4/6
                    and all(records[ultimo_codigo][k] is None for k in ("aec", "anv", "omc"))
                )
                if ultimo_codigo is not None and (trae_tasas or sin_tasas_aun):
                    rec = records[ultimo_codigo]
                    rec["descripcion"] = f'{rec["descripcion"]} {text}'.strip()
                    if aec is not None:
                        rec["aec"] = aec
                    if anv is not None:
                        rec["anv"] = anv
                    if omc is not None:
                        rec["omc"] = omc
                else:
                    notas_buffer.append(text)
            i += 1
            continue
        if col_a is not None:
            codigo = str(col_a).strip()
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
