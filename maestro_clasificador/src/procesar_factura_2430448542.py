# -*- coding: utf-8 -*-
"""Clasificacion de la factura MS Motorservice 2430448542 / IMPORT ROENAV S.A.
(cliente 563016). Corrida puntual, no forma parte del pipeline reutilizable."""
import sys
sys.path.insert(0, ".")
from procesar_factura import procesar_factura
from generar_salida import generar_orden_notas

# (pos, referencia, cantidad, unidad_factura, precio_unit, valor_total, descripcion_factura)
LINEAS_RAW = [
("000001","87320690",12,"JGO",13.35,160.20,"JGO BUJES DE BIELA"),
("000002","50013566",10,"PZA",3.01,30.10,"FILTRO DE ACEITE ENERGETIC 566-OX"),
("000003","50014694",10,"PZA",14.27,142.70,"FILTRO DE AIRE 4694-AP"),
("000004","50013423/2",20,"PZA",6.72,134.40,"FILTRO DE AIRE set 423/2-AP"),
("000005","50013205/1",79,"PZA",3.87,305.73,"FILTRO DE AIRE 205/1-AP"),
("000006","50013158",50,"PZA",2.76,138.00,"FILTRO DE COMBUSTIBLE 158-FS"),
("000007","50013265",30,"PZA",6.07,182.10,"FILTRO DE COMBUSTIBLE 265-FP"),
("000010","50014031",20,"PZA",9.20,184.00,"FILTRO DE COMBUSTIBLE 4031-FP"),
("000011","50014660",5,"PZA",10.80,54.00,"FILTRO DE COMBUSTIBLE 4660-FP"),
("000012","50014516",10,"PZA",9.29,92.90,"FILTRO DE AIRE 4516-AP"),
("000013","50014515",5,"PZA",7.11,35.55,"FILTRO DE AIRE 4515-AP"),
("000014","400210400005",2,"PZA",55.84,111.68,"Cadena de distribucion MB"),
("000015","50019181",2,"PZA",5.34,10.68,"FILTRO DE AIRE 9181-AP"),
("000016","50008600",10,"PZA",20.18,201.80,"ATF Pan"),
("000017","50014033",10,"PZA",7.34,73.40,"FILTRO DE AIRE 4033-AR"),
("000020","7.10942.07.0",4,"PZA",96.89,387.56,"BOMBA DE AGUA VARIABLE"),
("000021","7.20607.74.0",6,"PZA",65.57,393.42,"BOMBA DE VACIO"),
("000022","50014749",8,"PZA",1.79,14.32,"FILTRO DE ACEITE 4749-OX"),
("000023","50013576",25,"PZA",3.44,86.00,"FILTRO DE ACEITE 576-OX"),
("000024","50013505",2,"PZA",2.75,5.50,"FILTRO DE ACEITE 505-OX"),
("000025","50014876",10,"PZA",6.11,61.10,"FILTRO DE ACEITE 4876-OX"),
("000026","50019175",5,"PZA",2.11,10.55,"FILTRO DE ACEITE 9175-OX"),
("000027","50013136",250,"PZA",3.37,842.50,"FILTRO DE ACEITE 136-OC"),
("000031","50013384",80,"PZA",3.10,248.00,"FILTRO DE ACEITE 384-OX"),
("000032","50013570",250,"PZA",2.46,615.00,"FILTRO DE ACEITE 570-OX"),
("000033","50014117",80,"PZA",2.48,198.40,"FILTRO DE ACEITE 4117-OX"),
("000034","50014674",40,"PZA",4.45,178.00,"FILTRO DE ACEITE 4674-OX"),
("000035","50019134",30,"PZA",4.02,120.60,"FILTRO DE ACEITE 9134-OX"),
("000038","50013652",30,"PZA",3.98,119.40,"FILTRO DE ACEITE 652-OX"),
("000039","50014487",20,"PZA",5.75,115.00,"FILTRO DE ACEITE 4487-OX"),
("000042","50014483",60,"PZA",2.41,144.60,"FILTRO DE ACEITE 4483-OX"),
("000043","50013695",25,"PZA",1.90,47.50,"FILTRO DE ACEITE 695-OX"),
("000044","50014893",50,"PZA",5.34,267.00,"FILTRO DE ACEITE 4893-OX"),
("000045","50014717",15,"PZA",3.40,51.00,"FILTRO DE ACEITE 4717-OX"),
("000046","50014010",50,"PZA",4.03,201.50,"FILTRO DE ACEITE 4010-OX"),
("000047","50014672",15,"PZA",3.40,51.00,"FILTRO DE ACEITE 4672-OX"),
("000048","50013578",15,"PZA",4.07,61.05,"FILTRO DE ACEITE 578-OX"),
("000049","50014706",15,"PZA",7.87,118.05,"FILTRO DE ACEITE 4706-OX"),
("000052","50014678",5,"PZA",1.88,9.40,"FILTRO DE ACEITE 4678-OS"),
("000053","50013529",10,"PZA",4.44,44.40,"FILTRO DE ACEITE 529-OS"),
("000054","50014668",15,"PZA",6.61,99.15,"FILTRO DE ACEITE 4668-OX"),
("000055","50013227",200,"PZA",2.53,506.00,"FILTRO DE ACEITE 227-OX"),
("000056","50013659",60,"PZA",2.52,151.20,"FILTRO DE ACEITE 659-OX"),
("000057","50014492",40,"PZA",4.38,175.20,"FILTRO DE ACEITE 4492-OX"),
("000058","50013661",15,"PZA",2.53,37.95,"FILTRO DE ACEITE 661-OX"),
("000059","50014126",10,"PZA",4.20,42.00,"FILTRO DE ACEITE 4126-OX"),
("000062","50013016",20,"PZA",3.72,74.40,"FILTRO DE ACEITE 016-OC"),
("000063","50013393",15,"PZA",6.07,91.05,"FILTRO DE AIRE 393-AP"),
("000066","50013435",70,"PZA",6.18,432.60,"FILTRO DE AIRE 435-AP"),
("000069","50014945",25,"PZA",9.05,226.25,"FILTRO DE AIRE 4945-AP"),
("000070","50013446",6,"PZA",5.89,35.34,"FILTRO DE AIRE 446-AP"),
("000071","50014964",20,"PZA",7.70,154.00,"FILTRO DE AIRE 4964-AP"),
("000072","50014742",40,"PZA",6.13,245.20,"FILTRO DE AIRE 4742-AP"),
("000075","50014522",6,"PZA",8.59,51.54,"FILTRO DE AIRE 4522-AP"),
("000076","50014452",6,"PZA",5.02,30.12,"FILTRO DE AIRE 4452-AP"),
("000077","50014034",6,"PZA",10.32,61.92,"FILTRO DE AIRE 4034-AR"),
("000078","50013994",20,"PZA",6.65,133.00,"FILTRO DE AIRE 994-AR"),
("000079","50014094",4,"PZA",8.02,32.08,"FILTRO DE AIRE 4094-AP"),
("000080","50013677",6,"PZA",5.57,33.42,"FILTRO DE AIRE 677-AP"),
("000081","50013911",6,"PZA",5.29,31.74,"FILTRO DE AIRE 911-AP"),
("000082","50014188",6,"PZA",8.47,50.82,"FILTRO DE AIRE 4188-AP"),
("000083","50013238",6,"PZA",3.92,23.52,"FILTRO DE AIRE 238-AP"),
("000084","50013698",20,"PZA",5.50,110.00,"FILTRO DE AIRE 698-AP"),
("000085","50013205/1",200,"PZA",4.17,834.00,"FILTRO DE AIRE 205/1-AP REFERENCIA CLIENTE 50013205"),
("000089","50014683",15,"PZA",5.18,77.70,"FILTRO DE AIRE 4683-AP"),
("000090","50014000",30,"PZA",9.05,271.50,"FILTRO DE AIRE 4000-AR"),
("000093","50014689",10,"PZA",10.83,108.30,"FILTRO DE AIRE 4689-AP"),
("000094","50013924",10,"PZA",6.70,67.00,"FILTRO DE AIRE 924-AP"),
("000097","50014163",20,"PZA",6.88,137.60,"FILTRO DE AIRE 4163-AP"),
("000098","50013711",2,"PZA",11.33,22.66,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000099","50013752",10,"PZA",6.65,66.50,"FILTRO DE HABITACULO 752-AC"),
("000100","50014481",15,"PZA",11.11,166.65,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000101","50013750",4,"PZA",6.17,24.68,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000102","50014762",6,"PZA",4.92,29.52,"FILTRO DE HABITACULO 4762-AC"),
("000103","50014679",40,"PZA",4.38,175.20,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000104","50014548",20,"PZA",14.72,294.40,"FILTRO DE COMBUSTIBLE 4548-FP"),
("000107","50014746",25,"PZA",11.10,277.50,"FKM/FPM FILTRO DE COMBUSTIBLE 4746-FP"),
("000108","50013654",5,"PZA",14.86,74.30,"FILTRO DE COMBUSTIBLE 654-FP"),
("000111","50014486",15,"PZA",16.61,249.15,"FILTRO DE COMBUSTIBLE 4486-FP"),
("000112","50013419",8,"PZA",4.84,38.72,"FILTRO DE COMBUSTIBLE 419-FP"),
("000113","50013032",100,"PZA",4.02,402.00,"FILTRO DE COMBUSTIBLE 032-FP"),
("000114","50013067",15,"PZA",8.27,124.05,"FILTRO DE COMBUSTIBLE 067-FP"),
("000115","50013033",10,"PZA",8.08,80.80,"FILTRO DE COMBUSTIBLE 033-FP"),
("000118","50013655",80,"PZA",6.18,494.40,"FILTRO DE COMBUSTIBLE 655-FP"),
("000119","50013265",60,"PZA",6.53,391.80,"FILTRO DE COMBUSTIBLE 265-FP"),
("000120","50014031",40,"PZA",9.91,396.40,"FILTRO DE COMBUSTIBLE 4031-FP"),
("000124","400210400004",4,"PZA",70.51,282.04,"Cadena de distribucion MB 5.5 L"),
("000125","400210400006",4,"PZA",66.86,267.44,"Cadena de distribucion MB"),
("000126","7.09269.22.0",4,"PZA",29.63,118.52,"FKM/FPM REFRIGERAD.ACEITE"),
("000127","7.14059.55.0",6,"PZA",14.10,84.60,"sensor del numero de revoluciones de rueda"),
("000128","7.07759.98.0",2,"PZA",59.58,119.16,"SENSOR DE MASSA DE AIRE"),
("000129","7.14490.01.0",2,"PZA",57.91,115.82,"SENSOR DE MASSA DE AIRE"),
("000130","7.22684.09.0",10,"PZA",40.83,408.30,"SENSOR DE MASA DE AIRE"),
("000131","7.22684.11.0",10,"PZA",38.61,386.10,"SENSOR DE MASA DE AIRE"),
("000132","7.07759.18.0",5,"PZA",53.66,268.30,"SENSOR DE MASAS DE AEREAS"),
("000133","50012503",2,"PZA",53.63,107.26,"TAPA DE CULATA BMW N46"),
("000134","50012502",2,"PZA",56.36,112.72,"TAPA DE CULATA BMW N20"),
("000135","50014660",25,"PZA",11.46,286.50,"FILTRO DE COMBUSTIBLE 4660-FP"),
("000136","50014516",25,"PZA",9.86,246.50,"FILTRO DE AIRE 4516-AP"),
("000137","50014515",10,"PZA",7.54,75.40,"FILTRO DE AIRE 4515-AP"),
("000138","50013646",2,"PZA",25.60,51.20,"FILTRO DE COMBUSTIBLE 646-FP"),
("000139","50014234",6,"PZA",9.59,57.54,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000140","7.12122.21.0",6,"PZA",36.84,221.04,"RADIADOR ACEITE"),
("000141","50013949",10,"PZA",4.35,43.50,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000144","50014782",25,"PZA",3.72,93.00,"FILTRO DE HABITACULO 4782-AC"),
("000145","50013158",250,"PZA",2.98,745.00,"FILTRO DE COMBUSTIBLE 158-FS"),
("000148","50013568",150,"PZA",2.39,358.50,"FILTRO DE ACEITE 568-OX"),
("000149","400210500003",2,"PZA",96.51,193.02,"Cadena de distribucion MB"),
("000150","7.22466.93.0",4,"PZA",44.89,179.56,"SENSOR DEL DEPOSITO"),
("000151","7.22156.50.0",8,"PZA",45.77,366.16,"BOMBA DE COMBUSTIBLE ELECTRICA"),
("000152","50013908",8,"PZA",9.89,79.12,"FILTRO DE COMBUSTIBLE 908-FP"),
("000153","50014599",10,"PZA",4.60,46.00,"FILTRO DE ACEITE 4599-OX"),
("000156","50014951",30,"PZA",9.26,277.80,"FILTRO DE HABITACULO CON CARBON ACTIVO"),
("000157","50014874",35,"PZA",5.82,203.70,"FILTRO DE ACEITE 4874-OX"),
("000158","7.10942.27.0",3,"PZA",85.85,257.55,"BOMBA DE AGUA VARIABLE"),
("000159","50014688",10,"PZA",4.59,45.90,"FILTRO DE AIRE 4688-AP"),
("000160","50008601",14,"PZA",19.54,273.56,"ATF Pan"),
]


def clasificar(desc):
    d = desc.upper()
    if "BIELA" in d:
        return "8409.91.90", "MEDIA"
    if "TAPA DE CULATA" in d:
        return "8409.91.90", "MEDIA"
    if "HABITACULO" in d:
        return "8421.39.90", "ALTA"
    if "FILTRO DE ACEITE" in d or "FILTRO DE COMBUSTIBLE" in d:
        return "8421.23.00", "ALTA"
    if "FILTRO DE AIRE" in d:
        return "8421.31.00", "ALTA"
    if "CADENA DE DISTRIBUCION" in d:
        return "7315.11.00", "ALTA"
    if "BOMBA DE AGUA" in d:
        return "8413.30.90", "ALTA"
    if "BOMBA DE VACIO" in d:
        return "8414.10.00", "ALTA"
    if "ATF PAN" in d:
        return "8708.40.90", "MEDIA"
    if "BOMBA DE COMBUSTIBLE ELECTRICA" in d:
        return "8413.30.10", "MEDIA"
    if "REVOLUCIONES" in d:
        return "8543.70.99", "ALTA"
    if "MASA DE AIRE" in d or "MASSA DE AIRE" in d or "MASAS DE AEREAS" in d:
        return "8543.70.99", "MEDIA"
    if "SENSOR DEL DEPOSITO" in d:
        return "8708.99.90", "MEDIA"
    if "REFRIGERAD" in d:
        return "8708.91.00", "MEDIA"
    if "RADIADOR ACEITE" in d:
        return "8708.91.00", "ALTA"
    raise ValueError(f"Sin regla de clasificacion para: {desc}")


PAIS_ALEMANIA = "004"  # CODIGO_DE_PAISES.xlsx
MARCA = "MOTORSERVICE"

lineas = []
confianzas = {}
for pos, referencia, cant, ud, precio, valor, desc in LINEAS_RAW:
    ncm, confianza = clasificar(desc)
    confianzas.setdefault(ncm, set()).add(confianza)
    lineas.append({
        "codigo_ncm": ncm,
        "descripcion_factura": desc,
        "cantidad": cant,
        "unidad_texto_factura": ud,
        "fob": valor,
        "pais_origen": PAIS_ALEMANIA,
        "pais_procedencia": PAIS_ALEMANIA,
        "nombre_marca": MARCA,
    })

filas, notas = procesar_factura(lineas, acuerdo="SIN ACUERDO", nuevo_usado="2", marca_libre="ML")

notas_previas = [
    "Factura MS Motorservice International GmbH (Rheinmetall) no. 2430448542 del 04.09.2026, "
    "cliente IMPORT ROENAV S.A. (no. 563016). Total facturado EUR 20.252,23 (117 lineas).",
    "PAIS DE ORIGEN/PROCEDENCIA: la factura no declara pais de origen por linea. Se uso como "
    "referencia tentativa Alemania (004), pais de embarque/sede del proveedor (FCA Hamburg). "
    "Confirmar con el certificado de origen antes de despachar.",
    "PESO BRUTO/NETO: la factura solo trae el peso total del embarque (bruto 1.356 KG / neto "
    "1.087 KG, repartido en 2 cajas + 8 paletas + 1 paleta), sin desglose por item. Se dejaron "
    "en blanco; completar por item con el packing list o el B/L.",
    "NOMBRE DE MARCA: la factura no cita una marca de producto distinta al proveedor/emisor. "
    "Se uso 'MOTORSERVICE' (razon social/marca del emisor, MS Motorservice International GmbH, "
    "grupo Rheinmetall) para todos los items. Si el empaque real declara una submarca especifica "
    "(p.ej. MAHLE, KOLBENSCHMIDT o PIERBURG segun linea de producto), confirmar y corregir.",
    "ACUERDO: proveedor aleman (Union Europea) -> SIN ACUERDO para todas las lineas (no aplica "
    "Mercosur/Mercochile/Mercoperu/Mercobolivia).",
    "CLASIFICACION 8421.23.00: incluye tanto filtros de aceite como filtros de combustible para "
    "motor, porque el texto oficial de la subpartida cubre 'lubricantes o carburantes' en el mismo "
    "codigo -> quedan agrupados en un unico item con muchos subitems.",
    "CLASIFICACION 8409.91.90 (JGO BUJES DE BIELA, TAPA DE CULATA BMW N46/N20): confianza MEDIA. "
    "No hay subpartida especifica para bujes/cojinetes de biela ni tapas de culata en el Arancel "
    "vigente; se uso el residual de partes para motores de encendido por chispa (BMW N46/N20 son "
    "motores nafteros). Existe un criterio alternativo minoritario que clasifica bujes/cojinetes "
    "de biela como cojinetes de friccion generales (8483.30). Confirmar si se dispone de "
    "documentacion tecnica adicional.",
    "CLASIFICACION 8543.70.99 (sensores de revoluciones de rueda y de masa de aire): confianza "
    "ALTA para el sensor de revoluciones (hay resoluciones de aduana de EE.UU. -CBP NY N281447, "
    "NY N009077- que clasifican sensores de velocidad de rueda/ABS en la partida equivalente a "
    "85.43.70). Confianza MEDIA para los sensores de masa de aire, clasificados por analogia (no "
    "se encontro una resolucion puntual para ese sensor); una alternativa posible es 9026.10 "
    "(instrumentos electronicos de medida de caudal de gases).",
    "CLASIFICACION 8708.99.90 (SENSOR DEL DEPOSITO): confianza MEDIA. Se tomo como parte de "
    "vehiculo no expresada en otra partida, siguiendo un antecedente de aduana de EE.UU. sobre "
    "sensores de nivel de combustible. Confirmar si corresponde mejor a 9026.10 (instrumento de "
    "medida de nivel de liquidos).",
    "CLASIFICACION 8708.91.00 (RADIADOR ACEITE y FKM/FPM REFRIGERAD.ACEITE): el item 'RADIADOR "
    "ACEITE' tiene confianza ALTA (partida especifica 'Radiadores y sus partes' del Cap. 87, que "
    "prevalece sobre 84.19 para radiadores de vehiculo). El item 'FKM/FPM REFRIGERAD.ACEITE' tiene "
    "confianza MEDIA: la sigla FKM/FPM (material de sello Viton) sugiere que podria tratarse de un "
    "kit de juntas/retenes para el refrigerador de aceite y no la pieza completa, lo que cambiaria "
    "la partida (juntas: 84.84 o 40.16 segun material). Confirmar con ficha tecnica del producto.",
    "CLASIFICACION 8708.40.90 (ATF Pan): confianza MEDIA. Se tomo como carter/deposito de aceite "
    "de caja de cambios automatica, parte de caja de cambios.",
    "CLASIFICACION 8413.30.10 (BOMBA DE COMBUSTIBLE ELECTRICA): confianza MEDIA, se asumio "
    "aplicacion a motor nafta/gasolina (uso tipico de bombas electricas de combustible sumergidas "
    "en tanque). Si la aplicacion real es diesel, corresponde 8413.30.20.",
]
notas = notas_previas + notas

ruta = generar_orden_notas(filas, notas, "ORDEN_NOTAS_2430448542.xlsx")
print("Filas generadas:", len(filas))
print("Notas generadas:", len(notas))
print("Archivo:", ruta)

total_fob = sum(float(l["fob"]) for l in lineas)
print("Total FOB lineas:", round(total_fob, 2))
