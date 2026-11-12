"""Valida un CSV ORDEN antes de entregarlo al usuario. Correr SIEMPRE:
    python3 src/validar_csv.py salidas/ARCHIVO.csv
Chequea todas las reglas ya corregidas por el usuario (sin encabezado, sin
BOM, sin comillas, sin parentesis, pesos completos, subitems que suman)."""
import re, sys


def validar(ruta):
    raw = open(ruta, "rb").read()
    err = []
    ok = lambda c, m: None if c else err.append(m)
    ok(not raw.startswith(b"\xef\xbb\xbf"), "tiene BOM")
    ok(all(b < 128 for b in raw), "caracteres no ASCII")
    ok(b'"' not in raw, "tiene comillas")
    ok(b"(" not in raw and b")" not in raw, "tiene parentesis")
    rows = [l.split(";") for l in raw.decode().split("\r\n") if l]
    ok(rows and rows[0][0] == "N", "la primera fila no es un item (encabezado?)")
    ok(all(len(r) == 15 for r in rows), "filas sin 15 columnas")
    dec = re.compile(r"^\d+,\d{2}$")
    f = lambda x: float(x.replace(",", "."))
    items, cur = [], None
    for i, r in enumerate(rows, 1):
        if r[0] == "N":
            ok(re.match(r"^\d{4}\.\d{2}\.\d{2}(\.\d{3}[A-Z])?$", r[1]), f"fila {i}: NCM {r[1]}")
            ok(re.search(r" EN \d+(,\d+)? \S+", r[3]) and not r[3].startswith("EN "), f"fila {i}: descripcion {r[3]}")
            ok(not re.search(r"[.,\-]", r[3].split(" EN ")[0]), f"fila {i}: signos en descripcion")
            ok(r[4].isdigit() and len(r[4]) == 2, f"fila {i}: codigo unidad")
            ok(dec.match(r[5]), f"fila {i}: formato FOB")
            ok(r[8] and r[12], f"fila {i}: peso bruto/neto vacio")
            ok(r[9] in ("1", "2") and r[13] == "ML" and r[14], f"fila {i}: nuevo/ML/marca")
            cur = dict(fob=f(r[5]), cant=f(r[6]), sub=[], fila=i)
            items.append(cur)
        else:
            ok(cur and dec.match(r[1]) and r[2] == "ML" and r[4] and not any(r[6:]), f"fila {i}: subitem mal armado")
            ok(not re.search(r"[.,\-]", r[4]), f"fila {i}: signos en descripcion subitem")
            cur["sub"].append((f(r[0]), f(r[1])))
    for it in items:
        if it["sub"]:
            ok(len(it["sub"]) > 1, f"fila {it['fila']}: item con un solo subitem")
            ok(abs(sum(s[1] for s in it["sub"]) - it["fob"]) < .005, f"fila {it['fila']}: FOB subitems no suma")
            ok(abs(sum(s[0] for s in it["sub"]) - it["cant"]) < .005, f"fila {it['fila']}: cantidad subitems no suma")
    return err, rows, items


def validar_xlsx(ruta_xlsx, rows_csv):
    import openpyxl
    ws = openpyxl.load_workbook(ruta_xlsx)["ORDEN"]
    x = [[("" if c is None else str(c)) for c in r] for r in ws.iter_rows(values_only=True)]
    err = []
    if x and x[0][0] != "N":
        err.append("XLSX: la hoja ORDEN tiene fila de titulos")
    if x != rows_csv:
        err.append("XLSX: la hoja ORDEN no es identica al CSV")
    return err


if __name__ == "__main__":
    err, rows, items = validar(sys.argv[1])
    import os
    xl = sys.argv[1][:-4] + ".xlsx"
    if os.path.exists(xl):
        err += validar_xlsx(xl, rows)
    print(f"{len(rows)} filas, {len(items)} items")
    print("OK" if not err else "ERRORES:\n" + "\n".join(err))
    sys.exit(1 if err else 0)
