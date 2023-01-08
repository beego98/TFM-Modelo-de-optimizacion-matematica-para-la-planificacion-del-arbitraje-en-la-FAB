import pandas as pd
import json
import googlemaps

from datetime import time

from FAB_LISTAS import (lista_arbitros, 
                       lista_oficiales)
                
from FAB_PARTIDOS import lectura_partidos

from FAB_FUNCIONES import calculo_de_disponibilidades

from FAB_MODELO_MATEMATICO import modelo_matematico

fecha_de_designacion = '18122022'
fecha_de_designacion_siguiente = '25122022'
solver = 'GUROBI'
rz = ('FUERA',)
# rz = ('CASA',5, time(21,0))

#Información relativa a los árbitros
informacion_arbitros = lista_arbitros('Excels/FIRMAS ARBITROS.xls')
arbitros_coche = informacion_arbitros[0]
lista_de_arbitros = informacion_arbitros[2]

#Información relativa a los oficiales de mesa
informacion_oficiales = lista_oficiales('Excels/FIRMAS OFICIALES.xls')
oficiales_coche = informacion_oficiales[0]
lista_de_oficiales = informacion_oficiales[2]

#Lista conjunta de arbitros y oficiales con coche/moto, respectivamente
arbitros_oficiales_coche = arbitros_coche + oficiales_coche

#Partidos para designar el fin de semana
lecturapartidos = lectura_partidos('Horarios partidos/Partidos.xlsx', fecha_de_designacion)
partidos = lecturapartidos[0]
partidos_por_categoria = lecturapartidos[1]
partidos_totales = pd.concat([partidos, lecturapartidos[2]]).reset_index().drop(columns = 'index')

#Conjuntos de árbitros principales, funciones de anotadores y disponibilidades de árbitros y oficiales de mesa
principales_y_varios = pd.read_excel('Excels/Principales y otros.xlsx', sheet_name = 'PRINCIPALES Y VARIOS')

A1 = list(principales_y_varios['A1'].dropna()) #Arbitros principales A1
A2 = list(principales_y_varios['A2'].dropna()) #Arbitros principales A2
A3 = list(principales_y_varios['A3'].dropna()) #Arbitros principales A3
A4 = list(principales_y_varios['A4'].dropna()) #Arbitros principales A4
P1 = list(principales_y_varios['P1'].dropna()) #Arbitros principales P1
AD = list(principales_y_varios['ACTA DIGITAL LF'].dropna()) #Acta digital categorias FEB
CR = list(principales_y_varios['CRONOS'].dropna()) #Oficiales de Provincial 2 que pueden hacer cronos
F3 = list(principales_y_varios['3F'].dropna()) #Oficiales de Provincial 2 que pueden hacer 3ª Femenina y Junior Femenino 2ª

disponibilidad_excel = pd.read_excel('Excels/Disponibilidades.xlsx', sheet_name = f'DISPONIBILIDAD_{fecha_de_designacion}').fillna(0).set_index('Arbitro-Oficial')
disponibilidades_fijas = pd.read_excel('Excels/Principales y otros.xlsx', sheet_name = 'FIRMAS FIJAS')

prohibiciones = pd.read_excel('Excels/Principales y otros.xlsx', sheet_name = 'PROHIBICIONES').set_index('Arbitro')

partidos_feb = pd.read_excel('Excels/PartidosFEB.xlsx', sheet_name = f'PARTIDOS_FEB_{fecha_de_designacion}').set_index('Arbitro')

disponibilidad = calculo_de_disponibilidades(partidos_totales, disponibilidad_excel, disponibilidades_fijas, partidos_por_categoria, rz)

# start = tp.time()
# df = pd.read_excel('Horarios Partidos/Partidos.xlsx', sheet_name = None)['CAMPOS DE JUEGO'].set_index('Campo')
# # df = df[pd.isna(df.Latitud) == False]
# tiempo = pd.DataFrame(index = df.index, columns = df.index)
# # distancias_andando = pd.DataFrame(index = df.index, columns = df.index)
# for i in df.iterrows():
#     print(i)
#     for j in df.iterrows():
#         Latitud_Origen = i[1]['Latitud'] 
#         Longitud_Origen = i[1]['Longitud']
#         origen = (Latitud_Origen,Longitud_Origen)
        
#         Latitud_Destino = j[1]['Latitud'] 
#         Longitud_Destino = j[1]['Longitud']
#         destino = (Latitud_Destino,Longitud_Destino)
        
#         resultado_coche = round(gmaps.distance_matrix(origen, destino, mode='driving')["rows"][0]["elements"][0]["duration"]["value"]/60)
# #         resultado_andando = round(gmaps.distance_matrix(origen, destino, mode='walking')["rows"][0]["elements"][0]["duration"]["value"]/60)
       
#         if resultado_coche == 0:
#             tiempo.loc[i[0],j[0]] = resultado_coche
#         else:
#             tiempo.loc[i[0],j[0]] = resultado_coche + 10
#         distancias_andando.loc[i[0], j[0]] = resultado_andando
        
# end = tp.time()

# (end-start)/60

tiempo = pd.read_excel('Excels/Tiempo_Entre_Pabellones.xlsx').set_index('Campo')

resolucion = modelo_matematico(fecha_de_designacion,
                               partidos,
                               partidos_por_categoria,
                               lista_de_arbitros,
                               lista_de_oficiales,
                               arbitros_oficiales_coche,
                               CR,
                               F3,
                               AD,
                               A1, 
                               A2,
                               A3,
                               A4,
                               P1,
                               tiempo,
                               disponibilidad,
                               prohibiciones,
                               partidos_feb,
                               0.8,0.2, solver)
    
tiempo_ejecucion = resolucion[0]
Asignacion  = resolucion[1]

arbitros = resolucion[8]
oficiales = resolucion[10]

Partidos_FinDeSemana_Anterior = resolucion[9]

partidos_fin_de_semana = {}
for a in arbitros:
    partidos_fin_de_semana[a] = {}
    df = Asignacion[(Asignacion['Arbitro Principal'] == a)| 
           (Asignacion['Arbitro Auxiliar'] == a)].reset_index()
    
    if len(df) >= 1:
        for c in df.index:
            if df.loc[c, 'Categoria'] in partidos_fin_de_semana[a].keys():
                next
            else:
                partidos_fin_de_semana[a][df.loc[c, 'Categoria']] = []
            
            partidos_fin_de_semana[a][df.loc[c, 'Categoria']].append(df.loc[c, 'Local'])
            partidos_fin_de_semana[a][df.loc[c, 'Categoria']].append(df.loc[c, 'Visitante'])

partidos_fin_de_semana_actual = {}
partidos_fin_de_semana_actual['Finde2'] = Partidos_FinDeSemana_Anterior['Finde1']
partidos_fin_de_semana_actual['Finde1'] = partidos_fin_de_semana

with open(f'Partidos_Fin_De_Semana_Anteriores/Partidos_FinDeSemana_Anteriores_{fecha_de_designacion_siguiente}.json', 'w') as js:
    json.dump(partidos_fin_de_semana_actual, js)

Distribucion = pd.read_excel("Excels/Distribucion de partidos.xlsx", sheet_name = None, engine = "openpyxl")
Equivalencias = Distribucion['EQUIVALENCIAS CATEGORIAS'].set_index('CATEGORIA')

Distribucion_arbitros = Distribucion['ARBITROS']
Distribucion_oficiales = Distribucion['OFICIALES']
distribucion_partidos = pd.concat([Distribucion_arbitros, Distribucion_oficiales]).set_index('ARBITROS')

for a in distribucion_partidos.index:  
    if a in arbitros + oficiales:
        #SÁBADO TARDE INICIO
        if disponibilidad.loc[a, 'ST-Inicio'] == 1:
            distribucion_partidos.loc[a, 'S - 16:15'] = 'No Disponibilidad'

        elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
            if disponibilidad.loc[a, 'ST-Inicio'] < time(18,0):
                distribucion_partidos.loc[a, 'S - 16:15'] = f"A partir de las {disponibilidad.loc[a, 'ST-Inicio']}"
            elif time(18,0) <= disponibilidad.loc[a, 'ST-Inicio'] < time(20,0):
                distribucion_partidos.loc[a, 'S - 18:15'] = f"A partir de las {disponibilidad.loc[a, 'ST-Inicio']}"
            else:
                distribucion_partidos.loc[a, 'S - 20:15'] = f"A partir de las {disponibilidad.loc[a, 'ST-Inicio']}"
        else:
            next       

        #SÁBADO TARDE FINAL
        if disponibilidad.loc[a, 'ST-Final'] != 0:
            if disponibilidad.loc[a, 'ST-Final'] < time(18,0):
                distribucion_partidos.loc[a, 'S - 16:15'] = f"Acabar antes de las {disponibilidad.loc[a, 'ST-Final']}"
            elif time(18,0) <= disponibilidad.loc[a, 'ST-Final'] < time(20,0):
                distribucion_partidos.loc[a, 'S - 18:15'] = f"Acabar antes de las {disponibilidad.loc[a, 'ST-Final']}"
            else:
                distribucion_partidos.loc[a, 'S - 20:15'] = f"Acabar antes de las {disponibilidad.loc[a, 'ST-Final']}"


        #DOMINGO MAÑANA INICIO
        if disponibilidad.loc[a, 'DM-Inicio'] == 1:
            distribucion_partidos.loc[a, 'D - 9:30'] = 'No Disponibilidad'

        elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
            if disponibilidad.loc[a, 'DM-Inicio'] < time(10,30):
                distribucion_partidos.loc[a, 'D - 9:30'] = f"A partir de las {disponibilidad.loc[a, 'DM-Inicio']}"
            elif time(10,30) <= disponibilidad.loc[a, 'DM-Inicio'] < time(12,0):
                distribucion_partidos.loc[a, 'D - 11:00'] = f"A partir de las {disponibilidad.loc[a, 'DM-Inicio']}"
            else:
                distribucion_partidos.loc[a, 'D - 12:30'] = f"A partir de las {disponibilidad.loc[a, 'DM-Inicio']}"
        else:
            next     

        #DOMINGO MAÑANA FINAL
        if disponibilidad.loc[a, 'DM-Final'] != 0:
            if disponibilidad.loc[a, 'DM-Final'] < time(10,30):
                distribucion_partidos.loc[a, 'D - 9:30'] = f"Acabar antes de las {disponibilidad.loc[a, 'DM-Final']}"
            elif time(10,30) <= disponibilidad.loc[a, 'DM-Final'] < time(12,0):
                distribucion_partidos.loc[a, 'D - 11:00'] = f"Acabar antes de las {disponibilidad.loc[a, 'DM-Final']}"
            else:
                distribucion_partidos.loc[a, 'D - 12:30'] = f"Acabar antes de las {disponibilidad.loc[a, 'DM-Final']}"


        #DOMINGO TARDE INICIO
        if disponibilidad.loc[a, 'DT-Inicio'] == 1:
            distribucion_partidos.loc[a, 'D - 16:00'] = 'No Disponibilidad'

        elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
            if disponibilidad.loc[a, 'DT-Inicio'] < time(18,0):
                distribucion_partidos.loc[a, 'D - 16:00'] = f"A partir de las {disponibilidad.loc[a, 'DT-Inicio']}"
            elif time(18,0) <= disponibilidad.loc[a, 'DT-Inicio'] < time(20,0):
                distribucion_partidos.loc[a, 'D - 18:00'] = f"A partir de las {disponibilidad.loc[a, 'DT-Inicio']}"
            else:
                distribucion_partidos.loc[a, 'D - 20:00'] = f"A partir de las {disponibilidad.loc[a, 'DT-Inicio']}"
        else:
            next  

        #DOMINGO TARDE FINAL
        if disponibilidad.loc[a, 'DT-Final'] != 0:
            if disponibilidad.loc[a, 'DT-Final'] < time(18,0):
                distribucion_partidos.loc[a, 'D - 16:00'] = f"Acabar antes de las {disponibilidad.loc[a, 'DT-Final']}"
            elif time(18,0) <= disponibilidad.loc[a, 'DT-Final'] < time(20,0):
                distribucion_partidos.loc[a, 'D - 18:00'] = f"Acabar antes de las {disponibilidad.loc[a, 'DT-Final']}"
            else:
                distribucion_partidos.loc[a, 'D - 20:00'] = f"Acabar antes de las {disponibilidad.loc[a, 'DT-Final']}"

    
        if a in arbitros:
            sub = Asignacion[(Asignacion['Arbitro Principal'] == a)| 
                             (Asignacion['Arbitro Auxiliar'] == a)].sort_values(['Fecha', 'Hora'])
        if a in oficiales:
            sub = Asignacion[(Asignacion['Anotador'] == a) | 
                             (Asignacion['Cronometrador'] == a) | 
                             (Asignacion['Operador 24"'] == a) |
                             (Asignacion['Ayudante Anotador'] == a)]

        
        part_sab_16 = 0
        part_sab_18 = 0
        part_sab_20 = 0
        
        part_dom_9 = 0
        part_dom_11 = 0
        part_dom_13 = 0
        
        part_dom_16 = 0
        part_dom_18 = 0
        part_dom_20 = 0  
        
        if len(sub) > 0:
            for i in sub.index:
                #Categoria del partido
                cat_part = i[0]
                
                #Dia del partido
                dia_part = partidos[(partidos.Categoria == i[0]) &
                                    (partidos['EQUIPO LOCAL'] == i[1]) &
                                    (partidos['EQUIPO VISITANTE'] == i[2])].DiaSem

                #Hora del partido
                hora_part = i[3]
                
                #Dia de partido: SÁBADO
                if dia_part.values[0] == 5:
                    if hora_part < time(18,0):
                        if part_sab_16 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'S - 16:15']) == True:
                                distribucion_partidos.loc[a, 'S - 16:15'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_sab_16 +=1
                            else:
                                distribucion_partidos.loc[a, 'S - 16:15'] = f'''{distribucion_partidos.loc[a, 'S - 16:15']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''
                                part_sab_16 +=1
                            
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'S - 18:15']) == True:
                                distribucion_partidos.loc[a, 'S - 18:15'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_sab_18 += 1
                            else:
                                distribucion_partidos.loc[a, 'S - 18:15'] = f'''{distribucion_partidos.loc[a, 'S - 18:15']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_sab_18 += 1
                                
                             
                    elif time(18,0) <= hora_part < time(20,0):
                        if part_sab_18 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'S - 18:15']) == True:
                                distribucion_partidos.loc[a, 'S - 18:15'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_sab_18 += 1
                            else:
                                distribucion_partidos.loc[a, 'S - 18:15'] = f'''{distribucion_partidos.loc[a, 'S - 18:15']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_sab_18 += 1
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'S - 20:15']) == True:
                                distribucion_partidos.loc[a, 'S - 20:15'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_sab_20 += 1
                            else:
                                distribucion_partidos.loc[a, 'S - 20:15'] = f'''{distribucion_partidos.loc[a, 'S - 20:15']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_sab_20 += 1
                        
                    elif hora_part >= time(20,0):
                        if pd.isna(distribucion_partidos.loc[a, 'S - 20:15']) == True:
                            distribucion_partidos.loc[a, 'S - 20:15'] = Equivalencias.loc[cat_part, 'SIGLAS']
                            part_sab_20 += 1
                        else:
                            distribucion_partidos.loc[a, 'S - 20:15'] = f'''{distribucion_partidos.loc[a, 'S - 20:15']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                            part_sab_20 += 1

                        
                #Día de partido: DOMINGO
                elif dia_part.values[0] == 6:
                    if hora_part < time(10,30):
                        if part_dom_9 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 9:30']) == True:
                                distribucion_partidos.loc[a, 'D - 9:30'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_9 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 9:30'] = f'''{distribucion_partidos.loc[a, 'D - 9:30']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''
                                part_dom_9 += 1
                        
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 11:00']) == True:
                                distribucion_partidos.loc[a, 'D - 11:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_11 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 11:00'] = f'''{distribucion_partidos.loc[a, 'D - 11:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_11 += 1
                        
                    elif time(10,30) <= hora_part < time(12,0):
                        if part_dom_11 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 11:00']) == True:
                                distribucion_partidos.loc[a, 'D - 11:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_11 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 11:00'] = f'''{distribucion_partidos.loc[a, 'D - 11:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_11 += 1
                        
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 12:30']) == True:
                                distribucion_partidos.loc[a, 'D - 12:30'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_13 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 12:30'] = f'''{distribucion_partidos.loc[a, 'D - 12:30']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_13 += 1
                        
                    elif time(12,0) <= hora_part < time(16,0):
                        if pd.isna(distribucion_partidos.loc[a, 'D - 12:30']) == True:
                            distribucion_partidos.loc[a, 'D - 12:30'] = Equivalencias.loc[cat_part, 'SIGLAS']
                            part_dom_13 += 1
                        else:
                            distribucion_partidos.loc[a, 'D - 12:30'] = f'''{distribucion_partidos.loc[a, 'D - 12:30']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                            part_dom_13 += 1
                        
                        
                    elif time(16,0) <= hora_part < time(18,0):
                        if part_dom_16 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 16:00']) == True:
                                distribucion_partidos.loc[a, 'D - 16:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_16 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 16:00'] = f'''{distribucion_partidos.loc[a, 'D - 16:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_16 += 1
                        
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 18:00']) == True:
                                distribucion_partidos.loc[a, 'D - 18:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_18 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 18:00'] = f'''{distribucion_partidos.loc[a, 'D - 18:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_18 += 1
                            
                    elif time(18,0) <= hora_part < time(20,0):
                        if part_dom_18 == 0:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 18:00']) == True:
                                distribucion_partidos.loc[a, 'D - 18:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_18 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 18:00'] = f'''{distribucion_partidos.loc[a, 'D - 18:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_18 += 1
                        else:
                            if pd.isna(distribucion_partidos.loc[a, 'D - 20:00']) == True:
                                distribucion_partidos.loc[a, 'D - 20:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                                part_dom_20 += 1
                            else:
                                distribucion_partidos.loc[a, 'D - 20:00'] = f'''{distribucion_partidos.loc[a, 'D - 20:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                                part_dom_20 += 1
                            
                    elif hora_part >= time(20,0):
                        if pd.isna(distribucion_partidos.loc[a, 'D - 20:00']) == True:
                            distribucion_partidos.loc[a, 'D - 20:00'] = Equivalencias.loc[cat_part, 'SIGLAS']
                            part_dom_20 += 1
                        else:
                            distribucion_partidos.loc[a, 'D - 20:00'] = f'''{distribucion_partidos.loc[a, 'D - 20:00']} - {Equivalencias.loc[cat_part, 'SIGLAS']} ({hora_part})'''     
                            part_dom_20 += 1

Asignacion.to_excel(f'Asignacion_{fecha_de_designacion}.xlsx', sheet_name = 'Asignacion')
distribucion_partidos.to_excel(f'Distribucion_{fecha_de_designacion}.xlsx', sheet_name = 'Distribucion')