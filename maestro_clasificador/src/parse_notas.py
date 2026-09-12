"""Parsea las Notas Explicativas del Sistema Armonizado (txt, ~2000 paginas)
en fragmentos indexados por partida. Usa cache en JSON."""
import re
import json
import os
from config import NOTAS_EXPLICATIVAS_TXT, NOTAS_CACHE_JSON

SECCION_RE = re.compile(r"^\s*SECCIÓN\s+([IVXLCDM]+)\s*$")
CAPITULO_RE = re.compile(r"^\s*CAP[IÍ]TULO\s+(\d+)\s*$")
PARTIDA_RE = re.compile(r"^\s*(\d{2}\.\d{2})\s")

HEADER_RE = re.compile(
    r"\fSECCIÓN[^\n]*\n\s*Sistema Armonizado de Designación y Codificación de Mercancías VII Enmienda\n*",
    re.IGNORECASE,
)


def _parsear_notas():
    with open(NOTAS_EXPLICATIVAS_TXT, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    cleaned = HEADER_RE.sub("\n", raw)
    cleaned = re.sub(r"SECCIÓN\s+[IVXLCDM]+\s*\n\s*Notas Explicativas\n", "\n", cleaned)
    cleaned = cleaned.replace("\f", "\n")
    lines = cleaned.split("\n")

    chunks = []
    cur_seccion = cur_capitulo = cur_partida = None
    buf = []

    def flush():
        text = "\n".join(buf).strip()
        if text:
            chunks.append({"seccion": cur_seccion, "capitulo": cur_capitulo,
                            "partida": cur_partida, "text": text})
        buf.clear()

    for line in lines:
        m_sec, m_cap, m_par = SECCION_RE.match(line), CAPITULO_RE.match(line), PARTIDA_RE.match(line)
        if m_sec:
            flush(); cur_seccion = m_sec.group(1); cur_partida = None; buf.append(line); continue
        if m_cap:
            flush(); cur_capitulo = m_cap.group(1); cur_partida = None; buf.append(line); continue
        if m_par:
            flush(); cur_partida = m_par.group(1); buf.append(line); continue
        buf.append(line)
    flush()

    merged = []
    carry = None
    for c in chunks:
        if carry is not None:
            c["text"] = carry["text"] + "\n" + c["text"]
            c["partida"] = c["partida"] or carry["partida"]
            c["capitulo"] = c["capitulo"] or carry["capitulo"]
            carry = None
        if len(c["text"]) < 120:
            carry = c
            continue
        merged.append(c)
    if carry is not None and merged:
        merged[-1]["text"] += "\n" + carry["text"]
    return merged


def _cargar_chunks():
    if os.path.exists(NOTAS_CACHE_JSON):
        with open(NOTAS_CACHE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    chunks = _parsear_notas()
    with open(NOTAS_CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    return chunks


chunks = _cargar_chunks()
_by_partida = {}
for _c in chunks:
    if _c["partida"]:
        _by_partida.setdefault(_c["partida"], []).append(_c)


def consultar_partida(codigo_partida):
    """codigo_partida en formato 'XX.XX' (4 digitos). Devuelve la lista de
    fragmentos de Notas Explicativas para esa partida (normalmente 1)."""
    return _by_partida.get(codigo_partida, [])


if __name__ == "__main__":
    print(f"Notas Explicativas: {len(chunks)} fragmentos, {len(_by_partida)} partidas cubiertas.")
    print(consultar_partida("96.17")[0]["text"][:200])
