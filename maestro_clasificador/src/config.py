"""Configuracion central de rutas del Maestro Clasificador.

Todo el resto del codigo importa las rutas desde aca — no hay rutas
absolutas del sandbox de prueba en ningun otro archivo.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz del paquete
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
OUTPUT_DIR = os.path.join(BASE_DIR, "salidas")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ARANCEL_XLSX = os.path.join(DATA_DIR, "ARANCEL_2022_COMENTADO.xlsx")
NOTAS_EXPLICATIVAS_TXT = os.path.join(DATA_DIR, "Notas_Explicativas_VII_Enmienda.txt")
CODIGO_PAISES_XLSX = os.path.join(DATA_DIR, "CODIGO_DE_PAISES.xlsx")
UNIDADES_MEDIDA_XLSX = os.path.join(DATA_DIR, "UNIDADES_DE_MEDIDA.xlsx")
INSTRUCCIONES_MAESTRAS_XLSX = os.path.join(DATA_DIR, "INSTRUCCIONES_MAESTRAS1.xlsx")
NCMS_IDENTIFICADOR_XLSX = os.path.join(DATA_DIR, "NCMs_con_codigo_identificador.xlsx")

ARANCEL_CACHE_JSON = os.path.join(CACHE_DIR, "arancel_index.json")
NOTAS_CACHE_JSON = os.path.join(CACHE_DIR, "notas_chunks.json")

REGISTRO_NCM_JSON = os.path.join(CACHE_DIR, "ncm_confirmados.json")
IDENTIFICADORES_APRENDIDOS_JSON = os.path.join(CACHE_DIR, "identificadores_aprendidos.json")
