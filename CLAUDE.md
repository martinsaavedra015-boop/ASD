# ASD

Este repo contiene **Maestro Clasificador**: un pipeline para clasificar
arancelariamente (NCM/MERCOSUR) facturas de exportación y generar los
archivos ORDEN+NOTAS para despachos aduaneros en Paraguay.

Todo el código, datos de referencia y la documentación completa del flujo
están en `maestro_clasificador/`. **Antes de hacer cualquier otra cosa, leer
`maestro_clasificador/README.md`** — ahí está la arquitectura, el flujo de
uso paso a paso y las reglas de negocio ya confirmadas (no volver a
preguntarlas).

## Regla clave de esta sesión

Si el usuario sube una **factura de exportación** (PDF), un **certificado de
origen MERCOSUR**, u otro documento de despacho — no tratarlo como un PDF
genérico ni preguntar "¿qué querés que haga con esto?". Asumir que el pedido
implícito es correr el flujo de `maestro_clasificador`:

1. Extraer las líneas de la factura (código NCM si ya viene, descripción,
   cantidad, unidad, FOB, país de origen, marca).
2. Antes de investigar de cero, revisar `cache/ncm_confirmados.json` vía
   `registro_ncm.buscar_ncm_confirmado` — puede que el producto ya se haya
   clasificado en una sesión anterior.
3. Si no hay NCM confirmado ni viene en la factura, investigar el producto
   (identidad real del proveedor/comprador, actividad económica, web) antes
   de asumir una partida — y marcar la confianza como MEDIA/BAJA si no hay
   certeza, nunca forzar un código sin fundamento.
4. Si llega también un **Certificado de Origen MERCOSUR** u otro documento
   de la misma operación, ese documento manda sobre cualquier suposición
   previa — reclasificar y actualizar `registro_ncm` si corresponde.
5. Procesar con `procesar_factura.procesar_factura(...)` y generar el XLSX
   con `generar_salida.generar_orden_notas(...)` en `salidas/`, y entregar
   el archivo al usuario.

Los archivos de referencia (`data/`) se indexan una sola vez y quedan en
`cache/` — no volver a parsear el Arancel/Notas Explicativas si el cache ya
existe.
