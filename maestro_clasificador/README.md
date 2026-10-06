# Maestro Clasificador

Pipeline en Python para automatizar la clasificación arancelaria NCM y la
generación de archivos ORDEN+NOTAS para despachos aduaneros en Paraguay.
Construido y validado en conversación con Claude — este README resume la
arquitectura para retomarlo en Claude Code.

## Por qué existe esto

El flujo original corría como proyecto de Claude.ai: había que resubir los
5 archivos de referencia (Arancel, Notas Explicativas, países, unidades,
identificadores) en cada sesión, compitiendo por el límite de carga con las
facturas a clasificar. Acá los archivos de referencia viven en disco y se
indexan una sola vez — sin límite práctico de volumen.

## Estructura

```
maestro_clasificador/
├── data/           # Archivos de referencia (Arancel, Notas Explicativas, etc.)
├── cache/          # Índices ya parseados (se regeneran solos si se borran)
├── salidas/        # Acá se guardan los XLSX/CSV generados
├── src/            # Todo el código
│   ├── config.py               # Rutas centrales — todo lo demás las importa de acá
│   ├── parse_arancel.py        # Indexa el Arancel Nacional Vigente por código NCM
│   ├── parse_notas.py          # Indexa las Notas Explicativas (2000 páginas) por partida
│   ├── identificador_ncm.py    # Resuelve el código identificador de aduana (11 dígitos+letra)
│   ├── orden_builder.py        # Arma una fila ORDEN individual (reglas de formato)
│   ├── procesar_factura.py     # Agrupa líneas de factura en items/subitems
│   ├── generar_salida.py       # Genera el XLSX (ORDEN+NOTAS) y CSV final
│   ├── registro_ncm.py         # Memoria de NCMs confirmados (clasificación dudosa)
│   └── analizar_producto.py    # Metodología de investigación (requiere API)
└── requirements.txt
```

## Instalación

```bash
cd maestro_clasificador
pip install -r requirements.txt
export ANTHROPIC_API_KEY="tu-clave-aca"
```

La primera vez que corras algo, `parse_arancel.py` y `parse_notas.py` van a
parsear los archivos de `data/` y guardar el resultado en `cache/` — las
próximas corridas son instantáneas. Si actualizás algún archivo en `data/`,
borrá el cache correspondiente para que se regenere.

## Cómo se usa (flujo típico)

1. **Analizar cada línea de factura** con `analizar_producto.py` — esto
   necesita la API de Claude con `web_search` habilitado, más las tools
   `listar_subpartidas`, `buscar_ncm_confirmado`/`guardar_ncm_confirmado` y
   `resolver_codigo_final`/`guardar_identificador` conectadas (ver el
   template completo dentro del archivo). Devuelve el NCM de 8 dígitos con
   nivel de confianza.
2. **Armar la lista de líneas ya clasificadas** (código NCM + cantidad +
   FOB + país + marca + descripción tal como viene en la factura).
3. **Procesar la factura**: `procesar_factura.procesar_factura(lineas)` —
   agrupa por NCM, arma items/subitems, devuelve filas + notas.
4. **Generar el archivo final**:
   `generar_salida.generar_orden_notas(filas, notas, "nombre.xlsx")`.

```python
from procesar_factura import procesar_factura
from generar_salida import generar_orden_notas

lineas = [
    {
        "codigo_ncm": "8443.32.38",
        "descripcion_factura": "UV Flatbed Printer Model A2513",
        "cantidad": 1,
        "unidad_texto_factura": "1 set",
        "fob": 23730.00,
        "pais_origen": "720",
        "nombre_marca": "JUCOLOR",
    },
    # ... mas lineas
]
filas, notas = procesar_factura(lineas)
generar_orden_notas(filas, notas, "ORDEN_NOTAS_ejemplo.xlsx")
```

## Reglas de negocio importantes (ya confirmadas, no volver a preguntar)

- **Tasa de referencia: siempre ANV**, nunca AEC (AEC es solo dato de
  contexto).
- **Decimales con coma**, no punto (`23730,00`, formato paraguayo).
- **NUEVO/USADO**: `2`=nuevo (default), `1`=usado. Nunca "N"/"U".
- **MARCA LIBRE**: `"ML"` por default.
- **Unidad**: "piezas"/"pza"/"pcs"/"set" casi siempre son **UNIDAD (07)**,
  no PIEZAS (64). PIEZAS solo con justificación explícita puntual.
- **Descripción del ítem**: arranca desde el nivel de 8 dígitos del
  Arancel (nunca el texto genérico de 6 dígitos), sin puntos, comas ni
  guiones, todo en mayúsculas sin tildes.
- **Código identificador de aduana** (11 dígitos + letra): se resuelve
  aparte de la clasificación. Si la partida está firme pero no hay
  identificador en la referencia, no es un problema de clasificación — solo
  falta ese dato puntual (`identificador_ncm.mensaje_identificador_faltante`).
- **Entrega: siempre XLSX + CSV**. El CSV (`generar_salida.generar_csv`)
  se sube directo a KitApp y es igual a `ejemplos/CSV_REFERENCIA_DNA.csv`
  (CSV real aceptado): formato Excel "CSV (delimitado por comas)" con
  configuración paraguaya, o sea separador `;` y coma decimal, **SIN fila
  de títulos** (arranca directo con el primer ítem), **sin comillas** (el
  cierre va `EN 23200 UNIDAD DETALLADO EN SUBITEM`), enteros sin decimales,
  15 columnas, ANSI sin BOM, CRLF.
- **Peso bruto/neto: NUNCA en blanco** (confirmado por el usuario). Fuente:
  packing list / B/L > factura > estimación. Si es estimado, aclararlo en
  NOTAS como ESTIMADO, con la base del cálculo.
- **Nunca entregar un título como posición**: la columna B tiene que ser
  siempre un código seleccionable del sistema (11 dígitos + letra). Si
  `resolver_codigo_final` no encuentra identificador, revisar si el sistema
  de aduana abre esa subpartida en más ítems de los que trae el
  `ARANCEL_2022` local (caso real: `9403.20.00` es título; el sistema abre
  `9403.20.10.000Y` cocinas / `9403.20.90.000B` los demás). En ese caso
  clasificar en la apertura correcta, pasar `descripcion_arancel` en la
  línea (texto de 8+ dígitos que no está en el Arancel local) y guardar el
  código con `guardar_identificador`.
- **Memoria versionada**: `cache/ncm_confirmados.json` y
  `cache/identificadores_aprendidos.json` se commitean (el resto de
  `cache/` no) para que lo aprendido no se pierda entre sesiones.
- **Toy'N Gee Limited**: si el proveedor es este, la marca siempre es
  "TOY N GEE" (con la N), nunca la licencia/personaje del producto.
- **Búsqueda exhaustiva de subpartida**: antes de resolver en un código
  residual "Los demás", siempre revisar con
  `parse_arancel.listar_subpartidas(partida)` todas las subpartidas
  hermanas — hay casos reales (cabezales de impresión, cartuchos de tinta)
  donde existe una subpartida específica que no aparece si no se mira el
  árbol completo.

## Notas sobre la investigación de productos (`analizar_producto.py`)

La metodología tiene 5 pasos: (0) revisar si ya hay un NCM confirmado para
algo parecido, (1) investigar el producto en profundidad (múltiples
fuentes), (2) determinar partida candidata con reglas GRI, (3) búsqueda
exhaustiva de subpartida específica, (4) nivel de confianza — si solo se
puede confirmar hasta 6 dígitos, no forzar el resto, pedir el dato que
falta, (5) resolver el código identificador de aduana por separado.

Este paso requiere razonamiento real y no corre como script puro — está
pensado para conectarse a la API de Claude en este entorno de Claude Code,
donde `ANTHROPIC_API_KEY` ya está disponible.
