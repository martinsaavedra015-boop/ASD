"""Genera el archivo final XLSX (hojas ORDEN + NOTAS) y CSV a partir de las
filas ya armadas por procesar_factura.py / orden_builder.py."""
import os
import csv
import openpyxl
from openpyxl.styles import Font, Alignment
from config import OUTPUT_DIR

ENCABEZADOS = [
    "N", "POSICION ARANCELARIA", "ACUERDO", "ITEM/DESCRIPCION", "COD UNIDAD",
    "MONTO FOB", "CANTIDAD UNIDAD", "CANTIDAD ESTADISTICA", "PESO BRUTO",
    "NUEVO/USADO", "PAIS ORIGEN", "PAIS PROCEDENCIA", "PESO NETO",
    "MARCA LIBRE", "NOMBRE MARCA",
]
COL_ORDEN = list("ABCDEFGHIJKLMNO")


def generar_orden_notas(filas, notas, nombre_archivo):
    """filas: lista de dicts columna->valor (de procesar_factura.py).
    nombre_archivo: solo el nombre, se guarda en OUTPUT_DIR."""
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ORDEN"
    ws.append(ENCABEZADOS)
    for cell in ws[1]:
        cell.font = Font(name="Arial", bold=True)
    for fila in filas:
        ws.append([fila[c] for c in COL_ORDEN])
    for row in ws.iter_rows(min_row=1):
        for cell in row:
            cell.font = Font(name="Arial", size=cell.font.size or 10, bold=cell.font.bold)
    for row in ws.iter_rows(min_row=2, min_col=6, max_col=8):
        for cell in row:
            cell.number_format = "@"

    ws2 = wb.create_sheet("NOTAS")
    ws2.append(["#", "Observación"])
    ws2["A1"].font = Font(name="Arial", bold=True)
    ws2["B1"].font = Font(name="Arial", bold=True)
    for i, nota in enumerate(notas, start=1):
        ws2.append([i, nota])
        ws2[f"B{i+1}"].alignment = Alignment(wrap_text=True)

    for ws_ in (ws, ws2):
        for col_cells in ws_.columns:
            length = max((len(str(c.value)) if c.value else 0) for c in col_cells)
            ws_.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 10), 60)

    wb.save(ruta_salida)
    return ruta_salida


def generar_csv(filas, nombre_archivo):
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    with open(ruta_salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\r\n")
        writer.writerow(ENCABEZADOS)
        for fila in filas:
            writer.writerow([fila[c] for c in COL_ORDEN])
    return ruta_salida
