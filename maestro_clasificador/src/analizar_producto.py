"""
Modulo de ANALISIS AUTOMATIZADO para el Maestro Clasificador.

Este paso requiere razonamiento real (no es determinístico como los modulos
anteriores), asi que esta pensado para correr contra la API de Claude con
la tool de busqueda web habilitada, en tu entorno de Claude Code (donde ya
tenes la ANTHROPIC_API_KEY configurada). Este sandbox de prueba no tiene esa
clave, asi que este modulo documenta el metodo + deja la funcion lista para
conectar.

La metodologia (validada en vivo con el cabezal RICOH GEN6 y los cartuchos
de tinta UV) tiene 4 pasos obligatorios:
"""

PROMPT_ANALISIS = """
Sos un clasificador arancelario experto (NCM/MERCOSUR) trabajando para un
despachante de aduanas paraguayo. Se te da la descripcion de un producto tal
como aparece en una factura comercial. Tu tarea:

PASO 0 - REVISAR SI YA HAY UN NCM CONFIRMADO PARA ALGO PARECIDO
- Antes de investigar de cero, llama a buscar_ncm_confirmado(descripcion).
  Si aparece un resultado, usalo como punto de partida (con su nivel de
  confianza) en vez de repetir toda la investigacion desde cero. Si el
  producto de la factura difiere en algo relevante del que esta guardado,
  aclaralo igual antes de asumir que es el mismo.

PASO 1 - INVESTIGACION PROFUNDA DEL PRODUCTO
- Busca el producto especifico en internet: marca, modelo, fabricante,
  ficha tecnica, hoja de datos (datasheet), manual, o listados de
  comercio B2B (Alibaba, Made-in-China, sitio del fabricante).
- No te quedes con la primera fuente. Cruza al menos 2-3 fuentes
  independientes para confirmar caracteristicas fisicas, materiales,
  funcion, y a que maquina/sistema pertenece.
- Si no encontras el modelo exacto, busca el producto mas parecido
  (misma familia, mismo fabricante, misma funcion) y aclaralo como
  supuesto en vez de inventar caracteristicas.

PASO 2 - DETERMINAR CAPITULO/PARTIDA CANDIDATA
- Aplica las reglas GRI (1, 2a, 2b, 3a, 3b, 5b segun corresponda).
- Revisa las notas de exclusion de Seccion/Capitulo que puedan sacar el
  producto de la partida obvia (por ejemplo, partes electronicas de
  control que la Nota 2f Seccion XVII excluye de partes de vehiculo).
- Si es un repuesto/parte, identifica primero la maquina a la que
  pertenece exclusiva o principalmente, y clasifica como parte de esa
  partida (no como el objeto generico que es en si mismo).

PASO 3 - BUSQUEDA EXHAUSTIVA DE SUBPARTIDA ESPECIFICA (CRITICO)
- Una vez identificada la partida candidata (4 digitos), llama a la
  funcion listar_subpartidas(partida) — trae TODAS las subpartidas
  hijas de 8+ digitos con su descripcion y tasa ANV, de una sola vez.
- Revisa cada una antes de conformarte con un codigo residual "Los
  demas". Un residual solo es aceptable si, tras leer cada hermana
  devuelta por listar_subpartidas, ninguna describe especificamente
  el producto.
- Ejemplo real de este error: un cabezal de impresion clasificado
  directo en "8443.99.90 Los demas" sin llamar listar_subpartidas y
  ver que existe "8443.99.22 Cabezales de impresion" dentro de la
  familia especifica de mecanismos de impresion a chorro de tinta.

PASO 4 - NIVEL DE CONFIANZA Y PUNTOS ABIERTOS
- Asigna confianza ALTA solo si encontraste el codigo especifico y las
  fuentes confirman las caracteristicas relevantes para esa subpartida.
- Asigna confianza MEDIA/BAJA y flaguea el punto abierto en NOTAS si:
  (a) no se identifico el modelo exacto, (b) hay ambiguedad entre dos
  subpartidas posibles, o (c) falta un dato tecnico decisivo.
- Nunca ocultes la incertidumbre: es mejor marcar un punto abierto que
  asumir silenciosamente.
- REGLA CLAVE PARA CODIGO INCOMPLETO: si la investigacion solo permite
  confirmar con seguridad hasta 6 digitos (la subpartida, ej "8443.99")
  pero no hay evidencia suficiente para elegir entre las subpartidas de
  8/10 digitos que cuelgan de ahi, NO hay que forzar ni adivinar el
  resto. Se responde con el codigo de 6 digitos tal como se tiene, y se
  pide expresamente el dato que falta con esta frase (o una muy
  parecida): "Tengo los 6 digitos (XXXX.XX) confirmados, pero no los
  8/10 completos. Favor enviame el NCM completo para ir alimentando
  nuestra base de datos." Esto es preferible a completar con un digito
  que no esta fundamentado.
- CUANDO EL USUARIO COMPLETA EL DATO QUE FALTABA: llamar a
  guardar_ncm_confirmado(descripcion_producto, ncm_completo,
  dato_que_completo) para que quede registrado y la proxima vez que
  aparezca un producto parecido no haya que volver a preguntar.

PASO 5 - RESOLVER EL CODIGO IDENTIFICADOR DE ADUANA (siempre, al final)
- Una vez que la partida de 8 digitos esta confirmada (sin importar si
  fue por investigacion propia o por buscar_ncm_confirmado), llamar a
  resolver_codigo_final(codigo_8digitos).
- Si devuelve tiene_identificador=True, usar ESE codigo completo (11
  digitos + letra) en la columna B del ORDEN — no el NCM simple.
- Si devuelve tiene_identificador=False, la PARTIDA sigue firme (no es
  un punto de clasificacion dudoso), pero falta el identificador que
  usa la aduana. Usar mensaje_identificador_faltante(codigo, producto)
  para pedirlo, y usar el NCM simple de 8 digitos mientras tanto.
- Cuando el usuario pasa el identificador completo, llamar a
  guardar_identificador(codigo_8digitos, identificador_completo) para
  que quede disponible automaticamente la proxima vez.

Devolveme SIEMPRE en este formato:
{
  "producto_identificado": "...",
  "fuentes_consultadas": ["url1", "url2", ...],
  "partida_candidata": "NN.NN",
  "subpartida_final": "NNNN.NN.NN",
  "razonamiento": "...",
  "confianza": "ALTA|MEDIA|BAJA",
  "punto_abierto": "..." o null
}
"""


def analizar_producto(descripcion_producto, contexto=None, api_key=None):
    """Punto de conexion con la API de Claude (web_search + listar_subpartidas
    + este prompt).

    En este sandbox de prueba no hay ANTHROPIC_API_KEY configurada, asi que
    esta funcion queda como plantilla lista para tu entorno de Claude Code:

        import anthropic
        from parse_arancel import listar_subpartidas
        from registro_ncm import buscar_ncm_confirmado, guardar_ncm_confirmado
        from identificador_ncm import (
            resolver_codigo_final, guardar_identificador, mensaje_identificador_faltante,
        )

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=PROMPT_ANALISIS,
            tools=[
                {"type": "web_search_20250305", "name": "web_search"},
                {
                    "name": "listar_subpartidas",
                    "description": "Devuelve todas las subpartidas de 8+ "
                        "digitos que cuelgan de una partida/subpartida del "
                        "Arancel, con descripcion y tasa ANV.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"codigo": {"type": "string"}},
                        "required": ["codigo"],
                    },
                },
                {
                    "name": "buscar_ncm_confirmado",
                    "description": "Busca si ya existe un NCM completo "
                        "confirmado previamente para un producto igual o "
                        "parecido, para no repetir la investigacion.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"descripcion_producto": {"type": "string"}},
                        "required": ["descripcion_producto"],
                    },
                },
                {
                    "name": "guardar_ncm_confirmado",
                    "description": "Guarda un NCM ya confirmado a 8/10 "
                        "digitos para reutilizar en futuras clasificaciones "
                        "de productos parecidos.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "descripcion_producto": {"type": "string"},
                            "ncm_completo": {"type": "string"},
                            "dato_que_completo": {"type": "string"},
                        },
                        "required": ["descripcion_producto", "ncm_completo"],
                    },
                },
                {
                    "name": "resolver_codigo_final",
                    "description": "Dado un NCM de 8 digitos ya confirmado, "
                        "busca si tiene codigo identificador de aduana (11 "
                        "digitos + letra). Devuelve el codigo a usar y si "
                        "tiene identificador o no.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"codigo_ncm_8digitos": {"type": "string"}},
                        "required": ["codigo_ncm_8digitos"],
                    },
                },
                {
                    "name": "guardar_identificador",
                    "description": "Guarda el codigo identificador de aduana "
                        "(11 digitos + letra) que el usuario confirmo para "
                        "un NCM de 8 digitos, para reutilizar automaticamente.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "codigo_ncm": {"type": "string"},
                            "identificador_completo": {"type": "string"},
                        },
                        "required": ["codigo_ncm", "identificador_completo"],
                    },
                },
            ],
            messages=[{"role": "user", "content": descripcion_producto}],
        )
        # Cuando el modelo pida la tool listar_subpartidas, ejecutar
        # parse_arancel.listar_subpartidas(codigo) y devolver el resultado
        # como tool_result antes de continuar la conversacion.
        # Parsear el JSON final de la respuesta y devolver el dict.

    Por ahora, levanta un error claro si se llama sin clave configurada,
    en vez de fallar silenciosamente.
    """
    if not api_key:
        raise RuntimeError(
            "analizar_producto requiere ANTHROPIC_API_KEY. Este sandbox de "
            "prueba no la tiene configurada — conectar en tu entorno de "
            "Claude Code, donde ya esta disponible."
        )
    raise NotImplementedError("Conectar con el cliente de Anthropic aqui.")


def nota_codigo_incompleto(codigo_parcial, descripcion_producto=""):
    """Genera el texto de NOTAS estandar cuando solo se pudo confirmar el
    NCM hasta 6 digitos (subpartida) y falta completar a 8/10 digitos."""
    ref_producto = f' ({descripcion_producto})' if descripcion_producto else ""
    return (
        f'NCM{ref_producto}: tengo los 6 digitos ({codigo_parcial}) confirmados, '
        f'pero no los 8/10 completos. Favor enviame el NCM completo para ir '
        f'alimentando nuestra base de datos y no volver a preguntar la '
        f'proxima vez que aparezca un producto parecido.'
    )


# Resultado ya validado en vivo (Paso 1-4 corridos manualmente en este chat)
EJEMPLOS_VALIDADOS = [
    {
        "descripcion_producto": "Print head RICOH GEN6",
        "producto_identificado": "Ricoh Gen6 printhead (MH5320/MH5340), cabezal "
            "piezoelectrico de inyeccion de tinta para impresoras UV/solvente "
            "industriales, 1280 boquillas, compatible UV/solvente/base acuosa",
        "fuentes_consultadas": [
            "leadingprinterpart.com", "mitraprint.com", "johopetech.com",
            "lfprinterparts.com", "icolorpro.com",
        ],
        "partida_candidata": "84.43",
        "subpartida_final": "8443.99.22",
        "razonamiento": "Parte identificable como exclusivamente destinada a "
            "impresoras de inyeccion de tinta (partida 84.43). Dentro de las "
            "partes (8443.99), existe la subpartida especifica 'Cabezales de "
            "impresion' dentro de 'Mecanismos de impresion a chorro de tinta' "
            "(8443.99.2x) — no corresponde el residual 8443.99.90.",
        "confianza": "ALTA",
        "punto_abierto": None,
    },
    {
        "descripcion_producto": "UV Ink Cartridge CMYK Set",
        "producto_identificado": "Cartuchos de tinta UV para impresoras flatbed "
            "industriales, set CMYK",
        "fuentes_consultadas": ["busqueda directa por tipo de producto"],
        "partida_candidata": "84.43",
        "subpartida_final": "8443.99.23",
        "razonamiento": "Cartucho de tinta, parte/accesorio identificable de "
            "mecanismo de impresion a chorro de tinta — subpartida especifica "
            "'Cartuchos de tinta' (8443.99.23), no residual.",
        "confianza": "ALTA",
        "punto_abierto": None,
    },
]
