import pyomo.environ as py
import pandas as pd

from datetime import datetime, timedelta

import time

from SaveData import save_data

#Importamos diferentes conjuntos definidos en otros scripts .py
from FAB_CONJUNTOS import categorias_feb, categorias_federados, categorias_arbitros, categorias_oficiales, campos_desplazamientos

#Importamos diferentes funciones definidas en otros scripts .py
from FAB_FUNCIONES import (arbitros_partidos, 
                           oficiales_partidos, 
                           tuplas_arbitros, 
                           cuaterna_oficiales, 
                           partidos_semanas_anteriores, 
                           numero_de_arbitros_oficiales_por_partido)

def modelo_matematico(fecha_de_designacion,
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
                      alpha, beta, solver):
    '''
    Esta función crea el modelo matemático que permite resolver el problema de asignar árbitros y oficiales de mesa a los partidos de la Federación Aragonesa de
    Baloncesto. 

    Los parámetros de la función son los siguientes:

        - fecha_de_designacion: Fecha en formato 'ddmmyyyy', del fin de semana (domingo) sobre el que se va a ejecutar el modelo.

        - partidos: DF que contiene todos los partidos a los cuales hay que asignar árbitros y oficiales de mesa.

        - partidos_por_categoria: Diccionario que contiene el nombre de todos los equipos que juegan partido el fin de semana por categoria del partido.

        - lista_de_arbitros: Diccionario que contiene que árbitros pertenecen a cada categoria de árbitros.

        - lista_de_oficiales: Diccionario que contiene que oficiales de mesa pertenecen a cada categoria de oficiales de mesa.

        - arbitros_oficiales_coche: Lista de los árbitros y oficiales de mesa que disponen de coche a lo largo del fin de semana.

        - CR: Lista de oficiales de mesa de categoria Provincial 2 que pueden hacer la función de cronometrador.

        - F3: Lista de oficiales de mesa de categoria Provincial 2 que pueden hacer partidos de categoria 3ª Aragonesa Femenina y Junior Aragón Femenino 2ª.

        - AD: Lista de oficiales de mesa que pueden realizar el acta digital en categorias FEB.

        - A1: Lista de árbitros principales de categoria A1.

        - A2: Lista de árbitros principales de categoria A2.

        - A3: Lista de árbitros principales de categoria A3.

        - A4: Lista de árbitros principales de categoria A4.

        - P1: Lista de árbitros principales de categoria Provincial 1.

        - tiempo: DF que contiene la distancia entre todos los campos de juego posibles

        - disponibilidad: DF que contiene si cada árbitro y oficiales de mesa puede realizar partidos en cada franja.

        - prohibiciones: DF que contiene que árbitros que no pueden arbitrar partidos de una categoría determinada.

        - partidos_feb: DF que contiene si los árbitros del grupo FEB, han tenido partido de la Federación Española de Baloncesto o no.
    '''

    ##CONJUNTOS

    partidos = partidos[partidos.CAMPO != 'PAB. EL PARQUE'].reset_index().drop(columns = ['index'], axis = 1)

    #Conjunto de partidos que se juegan el sábado por la mañana
    PSM = list(partidos[partidos.HORA < 14*60 + 1].index) 
    #Conjunto de partidos que se juegan el sábado por la tarde
    PST = list(partidos[(partidos.HORA >= (14*60 + 1)) & (partidos.HORA <= 24*60)].index)
    #Conjunto de partidos que se juegan el domingo por la mañana
    PDM = list(partidos[(partidos.HORA >= 24*60) & (partidos.HORA < (24+14)*60 + 1)].index) 
    #Conjunto de partidos que se juegan el domingo por la tarde
    PDT = list(partidos[partidos.HORA >= (24+14)*60 + 1].index)

    #Conjunto de partidos
    P = PSM + PST + PDM + PDT

    #Conjunto de las diferentes franjas de juego
    F = [PST, PDM, PDT]

    #Conjunto de partidos de categoría 1ª Nacional Femenina A1
    NFA1 = list(partidos[partidos.Categoria == categorias_federados[1]].index)
    #Conjunto de partidos de categoría 1ª Nacional Masculina A1
    NMA1 = list(partidos[partidos.Categoria == categorias_federados[0]].index)
    #Conjunto de partidos de categoría 1ª Nacional Femenina A2
    NFA2 = list(partidos[partidos.Categoria == categorias_federados[3]].index)
    #Conjunto de partidos de categoría 1ª Nacional Masculina A2
    NMA2 = list(partidos[partidos.Categoria == categorias_federados[2]].index)

    #Conjunto de partidos de categoria 2ª Aragonesa Femenina y Junior Aragón Masculino 2ª
    PD = list(partidos[(partidos.Categoria == categorias_federados[13] )|
                    (partidos.Categoria == categorias_federados[5])].index)

    #Conjunto de partidos de categoria nacional
    PN = NFA1 + NMA1 + NFA2 + NMA2

    #Conjunto de partidos de categorías FEB.
    PFEB = list(partidos[partidos.Categoria.isin(categorias_feb)].index)
    #Conjunto de partios de categoría LIGA EBA y LIGA FEMENINA 2
    P_EBA_LF2 = list(partidos[partidos.Categoria.isin([categorias_feb[3], categorias_feb[4]])].index)
    #Conjunto de partidos de Baloncesto en Silla de Ruedas
    PBSR = list(partidos[(partidos.Categoria == categorias_feb[5])].index)
    
    #Conjunto de partidos que implican desplazamiento
    PC = partidos[partidos.Coche == 'Si'].index 

    #Conjunto de arbitros. 
    ### NOTA: Se estan eliminado los árbitros de categoría ESCUELA, ya que no pueden realizan ningún partido federado ###
    arbitros = []
    for c in categorias_arbitros:
        if c == categorias_arbitros[-1]:
            next
        else:
            arbitros = arbitros + lista_de_arbitros[c]
    A = arbitros.copy() 

    #Conjunto de árbitros de categoría FEB
    AFEB = lista_de_arbitros[categorias_arbitros[0]]
    #Conjunto de árbitros de categoría A1.
    AA1 = lista_de_arbitros[categorias_arbitros[1]]
    #Conjunto de árbitros de categoría A2
    AA2 = lista_de_arbitros[categorias_arbitros[2]]
    #Conjunto de árbitros de categoría A3
    AA3 = lista_de_arbitros[categorias_arbitros[3]]
    #Conjunto de árbitros de categoría A4
    AA4 = lista_de_arbitros[categorias_arbitros[4]]
    #Conjunto de árbitros de categoría P3
    AP3 = lista_de_arbitros[categorias_arbitros[7]]

    #Arbitros de categoria nacional
    AN = AFEB + AA1 + AA2 + AA3 + AA4

    #Conjunto de oficiales de mesa
    oficiales = []
    for c in categorias_oficiales:
        oficiales = oficiales + lista_de_oficiales[c]
    O = oficiales.copy() 

    #Conjunto de oficiales de mesa de categoría ACB
    OA = lista_de_oficiales[categorias_oficiales[0]]
    #Conjunto de oficiales de mesa de categoría LIGA FEM Y LEB PLATA
    OLF = lista_de_oficiales[categorias_oficiales[1]]
    #Conjunto de oficiales de mesa de categoría LIGA FEM 2 Y EBA
    OLF2 = lista_de_oficiales[categorias_oficiales[2]]
    #Conjunto de oficiales de mesa de categoría 1 DIVISION
    O1 = lista_de_oficiales[categorias_oficiales[3]]
    #Conjunto de oficiales de mesa de categoría PROVINCIAL 1
    OP1 = lista_de_oficiales[categorias_oficiales[4]]
    #Conjunto de oficiales de mesa de categoría PROVINCIAL 2
    OP2 = lista_de_oficiales[categorias_oficiales[5]]
    #Conjunto de oficiales de mesa de categoría NUEVOS
    OE = lista_de_oficiales[categorias_oficiales[6]]

    #Conjunto de oficiales de mesa de categoria nacional
    ON = OA + OLF + OLF2 + O1

    ## CR: Conjunto de oficiales de mesa de categoria PROVINCIAL 2 que pueden realizar funciones de cronometrador (Conjunto definido en los parámetros de la función)
    ## F3: Conjunto de oficiales de mesa de cateogria PROVINCIAL 2 que pueden realizar partidos de categoría 3ª Aragonesa Femenina y Junior Aragón Femenino 2ª

    #Conjunto de los diferentes campos de juego
    C = list(tiempo.index)

    #Conjunto de árbitros y oficiales de mesa que disponen de coche
    CH = arbitros_oficiales_coche.copy() 
    for c in CH:
        if c in A+O:
            next
        else:
            CH.remove(c)

    #Conjunto de arbitros que pueden arbitrar el partido p
    AP = arbitros_partidos(PST, PDM, PDT, partidos, lista_de_arbitros, A4, P1, disponibilidad)    
    #Conjunto de partidos que puede arbitrar el arbitro a
    PA = {} 
    for a in A:
        lista = []
        for p in P:
            if a in AP[p]:
                lista.append(p)
            else:
                next
        PA[a] = lista

    #Conjunto de oficiales que pueden anotar el partido p
    OP = oficiales_partidos(PST, PDM, PDT, partidos, lista_de_oficiales, CR, F3, disponibilidad)
    #Conjunto de partidos que puede arbitrar el oficial o
    PO = {} 
    for o in O:
        lista = []
        for p in P:
            if o in OP[p]:
                lista.append(p)
            else:
                next
        PO[o] = lista

    #Conjunto de categorías de los partidos a arbitrar
    CA = list(partidos.Categoria.unique())

    #Conjunto de tuplas de árbitros que pueden arbitrar el partido p
    TA = tuplas_arbitros(P, partidos, lista_de_arbitros, arbitros, A1, A2, A3, A4, P1)
    #Conjunto de cuaternas de oficiales de mesa que pueden arbitrar el partido p
    TO = cuaterna_oficiales(P, partidos, lista_de_oficiales, oficiales, OP, AD, CR, F3)

    Partidos_FinDeSemana_Anterior = partidos_semanas_anteriores(fecha_de_designacion,
                                                                partidos_por_categoria)

    #Se ajusta el conjunto de tuplas y el resto de conjuntos, en funcion de los partidos de los fin de semana anterior, las prohibiciones de arbitrar algunas
    #categorias de los arbitros
    for p in partidos.index:
        lista = TA[p]
        hora = partidos.loc[p, 'HoraDeJuego']
        
        borrar_arbitro_ap = []

        for a in disponibilidad.index:
            if a in PA.keys():
                borrar_tupla = []
                borrar_arbitro_pa = []
                
                categoria = partidos.loc[p, 'Categoria']
                
                if a in prohibiciones.index:
                    pro_sub = prohibiciones[prohibiciones.index == a]
                    for ps in pro_sub.Categoria:
                        if categoria == ps:
                            borrar_arbitro_ap.append(a)
                            borrar_arbitro_pa.append(p)
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l])
                            
                            
                
                if a in Partidos_FinDeSemana_Anterior['Finde1'].keys():
                    if categoria in Partidos_FinDeSemana_Anterior['Finde1'][a].keys():
                        if partidos.loc[p, 'EQUIPO LOCAL'] in Partidos_FinDeSemana_Anterior['Finde1'][a][categoria]:
                            borrar_arbitro_ap.append(a)
                            borrar_arbitro_pa.append(p)
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l])

                        if partidos.loc[p, 'EQUIPO VISITANTE'] in Partidos_FinDeSemana_Anterior['Finde1'][a][categoria]:
                            borrar_arbitro_ap.append(a)
                            borrar_arbitro_pa.append(p)                    
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l])       
                                    
                if a in Partidos_FinDeSemana_Anterior['Finde2'].keys():
                    if categoria in Partidos_FinDeSemana_Anterior['Finde2'][a].keys():
                        if partidos.loc[p, 'EQUIPO LOCAL'] in Partidos_FinDeSemana_Anterior['Finde2'][a][categoria]:
                            borrar_arbitro_ap.append(a)
                            borrar_arbitro_pa.append(p)
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l])

                        if partidos.loc[p, 'EQUIPO VISITANTE'] in Partidos_FinDeSemana_Anterior['Finde2'][a][categoria]:
                            borrar_arbitro_ap.append(a)
                            borrar_arbitro_pa.append(p)                    
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l])                                  
                
                if p in PST:
                    if disponibilidad.loc[a, 'ST-Inicio'] == 1:
                        for l in range(len(lista)):
                            if a in lista[l]:
                                if lista[l] in borrar_tupla:
                                    next
                                else:
                                    borrar_tupla.append(lista[l])

                    elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
                        if hora < disponibilidad.loc[a, 'ST-Inicio']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                                    
                    elif disponibilidad.loc[a, 'ST-Final'] != 0:
                        if (datetime.strptime(hora.strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'ST-Final']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                                    
                elif p in PDM:
                    if disponibilidad.loc[a, 'DM-Inicio'] == 1:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 

                    elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
                        if hora < disponibilidad.loc[a, 'DM-Inicio']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                        
                    elif disponibilidad.loc[a, 'DM-Final'] != 0:
                        if (datetime.strptime(hora.strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DM-Final']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                    
                elif p in PDT:
                    if disponibilidad.loc[a, 'DT-Inicio'] == 1:
                        for l in range(len(lista)):
                            if a in lista[l]:
                                if lista[l] in borrar_tupla:
                                    next
                                else:
                                    borrar_tupla.append(lista[l]) 

                    elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
                        if hora < disponibilidad.loc[a, 'DT-Inicio']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                                        
                    elif disponibilidad.loc[a, 'DT-Final'] != 0:
                        if (datetime.strptime(hora.strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DT-Final']:
                            for l in range(len(lista)):
                                if a in lista[l]:
                                    if lista[l] in borrar_tupla:
                                        next
                                    else:
                                        borrar_tupla.append(lista[l]) 
                
                for b in borrar_tupla:
                    TA[p].remove(b)

                for ba in borrar_arbitro_pa:
                    if ba in PA[a]:
                        PA[a].remove(ba)
        
        for c in borrar_arbitro_ap:
            if c in AP[p]:
                AP[p].remove(c)     

    ##PARÁMETROS
    #Hora de inicio del partido p
    h = partidos.HORA 

    #Campo de juego del partido p
    m = partidos['CAMPO'].to_dict() 

    #Tiempo que cuesta ir del campo de juego del partido p al campo de juego del partido q
    t = tiempo.stack().to_dict() 

    #Duración aproximada del partido p
    duracion_partido = pd.DataFrame()
    for p in range(len(partidos)):
        if partidos.loc[p, 'Categoria'] in (categorias_federados[0],
                                            categorias_federados[1],
                                            categorias_federados[2],
                                            categorias_federados[3],
                                            categorias_federados[4],
                                            categorias_federados[5],
                                            categorias_federados[6],
                                            categorias_federados[11],
                                            categorias_federados[12],
                                            categorias_federados[13],
                                            categorias_federados[18],
                                            categorias_federados[19]):
            duracion_partido.loc[p, 'Duracion'] = 105
        elif partidos.loc[p, 'Categoria'] in (categorias_federados[7],
                                            categorias_federados[8],
                                            categorias_federados[9],
                                            categorias_federados[10],
                                            categorias_federados[14],
                                            categorias_federados[15],
                                            categorias_federados[16],
                                            categorias_federados[17]):
            duracion_partido.loc[p, 'Duracion'] = 90
        
        elif partidos.loc[p, 'Categoria'] in categorias_feb:
            duracion_partido.loc[p, 'Duracion'] = 135
                  
    d = duracion_partido.Duracion #Duración aproximada del partido p

    #Tiempo mínimo anterior a la hora de inicio del partido p, que deben estar los árbitros en el terreno de juego
    tiempo_antes_partido_arbitros = pd.DataFrame()
    for p in range(len(partidos)):
        if partidos.loc[p, 'Categoria'] in (categorias_federados[0],
                                            categorias_federados[1]):
            tiempo_antes_partido_arbitros.loc[p, 'Antes'] = 40
        
        elif partidos.loc[p, 'Categoria'] in (categorias_federados[2],
                                            categorias_federados[3],
                                            categorias_federados[11],
                                            categorias_federados[12],
                                            categorias_federados[18],
                                            categorias_federados[19]):
            tiempo_antes_partido_arbitros.loc[p, 'Antes'] = 30
        
        else:
            tiempo_antes_partido_arbitros.loc[p, 'Antes'] = 25

    #Tiempo mínimo anterior a la hora de inicio del partido p, que deben estar los oficiales de mesa en el terreno de juego
    tiempo_antes_partido_oficiales = pd.DataFrame()
    for p in range(len(partidos)):
        if partidos.loc[p, 'Categoria'] in (categorias_federados[0],
                                            categorias_federados[1],
                                            categorias_federados[2],
                                            categorias_federados[3],
                                            categorias_federados[11],
                                            categorias_federados[12],
                                            categorias_federados[18],
                                            categorias_federados[19]):
            
            tiempo_antes_partido_oficiales.loc[p, 'Antes'] = 30
        
        elif partidos.loc[p, 'Categoria'] in (categorias_feb[5]):
            tiempo_antes_partido_oficiales.loc[p, 'Antes'] = 45
        
        elif partidos.loc[p, 'Categoria'] in (categorias_feb[3],
                                            categorias_feb[4]):
            tiempo_antes_partido_oficiales.loc[p, 'Antes'] = 60
        
        elif partidos.loc[p, 'Categoria'] in (categorias_feb[0],
                                            categorias_feb[2]):
            tiempo_antes_partido_oficiales.loc[p, 'Antes'] = 75
        else:
            tiempo_antes_partido_oficiales.loc[p, 'Antes'] = 25
            
    la = tiempo_antes_partido_arbitros.Antes #Tiempo que se debe estar el arbitro en el campo del partido p antes de su hora de inicio
    lo = tiempo_antes_partido_oficiales.Antes #Tiempo que debe estar el oficial de mesa en el campo del partido p antes de su hora de inicio

    #Categoria del partido p
    ct = partidos.Categoria.to_dict() 

    #Indica si los arbitros pertenecientes a la categoría FEB, han tenido partido en la federacion española o no
    pf = partidos_feb.Decision.to_dict() 

    #Máxima categoria que puede arbitrar cada árbitro de categoría nacional
    mc = {} 
    for a in AN:
        if a in lista_de_arbitros[categorias_arbitros[0]] + lista_de_arbitros[categorias_arbitros[1]]:
            mc[a] = categorias_federados[0]
        
        elif a in lista_de_arbitros[categorias_arbitros[2]]:
            mc[a] = categorias_federados[1]
        
        elif a in lista_de_arbitros[categorias_arbitros[3]]:
            mc[a] = categorias_federados[2]
        
        elif a in lista_de_arbitros[categorias_arbitros[4]]:
            mc[a] = categorias_federados[3]
            
    #Número de árbitros necesarios para cada partido, y número de oficiales de mesa necesarios para cada partido
    numero_por_partido = numero_de_arbitros_oficiales_por_partido(P, partidos)
    na = numero_por_partido[0].Numero
    no = numero_por_partido[1].Numero    

    #Número máximo de partidos que hay en una franja
    mx = sorted([len(PST), len(PDM), len(PDT)])[2]
    #Número máximo de partidos entre las franjas que no corresponden al valor del parámetro mx
    mn = sorted([len(PST), len(PDM), len(PDT)])[1] 

    #Número mínimo de árbitros de categoria A1, que tienen que árbitrar los partidos de categoria 1ª Nacional Masculina A1 durante el fin de semana
    mn = 0
    for a in AA1:
        if [x for x in PA[a] if x in NMA1] != []:
            mn+=1
    ma1 = min(0.75*mn, 0.75*2*len(NMA1)) 

    #Número mínimo de árbitros de categoria A2, que tienen que árbitrar los partidos de categoria 1ª Nacional Femenina A1 durante el fin de semana
    mn = 0
    for a in AA2:
        if [x for x in PA[a] if x in NFA1] != []:
            mn+=1
    fa1 = min(0.75*mn, 0.75*2*len(NFA1)) 

    #Número mínimo de árbitros de categoria A3, que tienen que árbitrar los partidos de categoria 1ª Nacional Masculina A2 durante el fin de semana
    mn = 0
    for a in AA3:
        if [x for x in PA[a] if x in NMA2] != []:
            mn+=1
    ma2 = min(0.75*mn, 0.75*2*len(NMA2)) 

    #Número mínimo de árbitros de categoria A4, que tienen que árbitrar los partidos de categoria 1ª Nacional Femenina A2 durante el fin de semana
    mn = 0
    for a in AA4:
        if [x for x in PA[a] if x in NFA2] != []:
            mn+=1
    fa2 = min(0.75*mn, 0.75*2*len(NFA2))

    #Número mínimo de árbitros de categoria P3, que tienen que arbitrar los partidos de categoría 2ª Aragonesa Femenina y Junior Aragón Masculina 2ª
    mn = 0
    for a in AP3:
        if [x for x in PA[a] if x in PD] != []:
            mn +=1
    pad = min(0.75*mn, 0.75*2*len(PD))       

    ##CONJUNTOS AUXILIARES CREADOS PARA FACILITAR LA DECLARACIÓN DE LAS VARIABLES DE DECISIÓN x,y,z
    x_index = [(p,i,j) for p in P for (i,j) in TA[p]]

    y_index = [(p,a) for p in P for a in A+O]
    y_index_arbitros = [(p,a) for p in P for a in AP[p]]
    y_index_anotadores = [(p,a) for p in P for a in OP[p]]

    z_index = [(p,a,c,o,ay) for p in P for (a,c,o,ay) in TO[p]]   

    '''EMPIEZA EL MODELO MATEMÁTICO CON LA LIBRERIA PYOMO'''
    start = time.time()
    modelo = py.ConcreteModel('Modelo Arbitraje')     

    ## CONJUNTOS
    modelo.PSM = py.Set(initialize = PSM) #Conjunto de partidos que se juegan el sábado por la mañana
    modelo.PST = py.Set(initialize = PST) #Conjunto de partidos que se juegan el sábado por la tarde
    modelo.PDM = py.Set(initialize = PDM) #Conjunto de partidos que se juegan el domingo por la mañana
    modelo.PDT = py.Set(initialize = PDT) #Conjunto de partidos que se juegan el domingo por la tarde

    modelo.P = py.Set(initialize = P) #Conjunto de partidos

    #F: Conjunto de las diferentes franjas de juego, no se define como un conjunto de pyomo ya que no lo interpreta de la manera correcta

    modelo.NFA1 = py.Set(initialize = NFA1) #Conjunto de partidos de categoría 1ª Nacional Femenina A1
    modelo.NMA1 = py.Set(initialize = NMA1) #Conjunto de partidos de categoría 1ª Nacional Masculina A1
    modelo.NFA2 = py.Set(initialize = NFA2) #Conjunto de partidos de categoría 1ª Nacional Femenina A2
    modelo.NMA2 = py.Set(initialize = NMA2) #Conjunto de partidos de categoría 1ª Nacional Masculina A2
    modelo.PD = py.Set(initialize = PD) #Conjuntos de partidos de categoría Junior Aragón Masculino 2ª y 2ª Aragonesa Femenina

    modelo.PN = py.Set(initialize = PN) #Conjunto de partidos de categoria nacional

    modelo.PFEB = py.Set(initialize = PFEB) #Conjunto de partidos de categorías FEB
    modelo.P_EBA_LF2 = py.Set(initialize = P_EBA_LF2) #Conjunto de partidos de categoría LIGA EBA Y LIGA FEMENINA 2
    modelo.PBSR = py.Set(initialize  = PBSR)

    #CF: Conjunto de partidos de categoría federada en la FAB

    modelo.PC = py.Set(initialize = PC) #Conjunto de partidos que implican desplazamiento

    modelo.A = py.Set(initialize = A) #Conjunto de arbitros

    modelo.AFEB = py.Set(initialize = AFEB) #Conjunto de árbitros de categoría FEB
    modelo.AA1 = py.Set(initialize = AA1) #Conjunto de árbitros de categoría A1
    modelo.AA2 = py.Set(initialize = AA2) #Conjunto de árbitros de categoría A2
    modelo.AA3 = py.Set(initialize = AA3) #Conjunto de árbitros de categoría A3
    modelo.AA4 = py.Set(initialize = AA4) #Conjunto de árbitros de categoría A4
    modelo.AP3 = py.Set(initialize = AP3) #Conjunto de árbitros de categoría P3

    modelo.AN = py.Set(initialize = AN) #Conjunto de árbitros de categoria nacional

    modelo.O = py.Set(initialize = O) #Conjunto de oficiales de mesa

    modelo.OA = py.Set(initialize = OA) #Conjuntos de oficiales de mesa de categoría ACB
    modelo.OLF = py.Set(initialize = OLF) #Conjuntos de oficiales de mesa de categoría LIGA FEM Y LEB PLATA
    modelo.OLF2 = py.Set(initialize = OLF2) #Conjunto de oficiales de mesa de categoría LIGA FEM 2 Y EBA
    modelo.O1 = py.Set(initialize = O1) #Conjunto de oficiales de mesa de categoría 1 DIVISION
    modelo.OP1 = py.Set(initialize = OP1) #Conjunto de oficiales de mesa de categoria PROVINCIAL 1
    modelo.OP2 = py.Set(initialize = OP2) #Conjunto de oficiales de mesa de categoria PROVINCIAL 2
    modelo.OE = py.Set(initialize = OE) #Conjunto de oficiales de mesa de categoria NUEVOS

    modelo.ON = py.Set(initialize = ON) #Conjunto de oficiales de categoria nacional

    modelo.CR = py.Set(initialize = CR) #Conjunto de oficiales de mesa de categoría PROVINCIAL 2, que pueden realizar funciones de cronometrador.
    modelo.F3 = py.Set(initialize = F3) #Conjunto de oficiales de mesa de categoría PROVINCIAL 2, que pueden hacer partidos de categoría 3ª Aragonesa Femenina y Junior Aragón Femenino 2ª

    modelo.C = py.Set(initialize = C) #Conjunto de campos de juego.

    #CD: Conjunto de los diferentes campos de juego que implican desplazamiento

    modelo.CH = py.Set(initialize = CH) #Conjunto de árbitros y oficiales de mesa que disponen de coche

    modelo.AP = py.Set(modelo.P, initialize = AP) #Conjunto de arbitros que pueden realizar el partido p
    modelo.PA = py.Set(modelo.A, initialize = PA) #Conjunto de partidos que puede arbitrar el árbitro a

    modelo.OP = py.Set(modelo.P, initialize = OP) #Conjunto de oficiales de mesa que pueden realizar el partido p
    modelo.PO = py.Set(modelo.O, initialize = PO) #Conjunto de partidos que puede arbitrar el oficial de mesa o

    modelo.CA = py.Set(initialize = CA) #Conjunto de categorías de los partidos a arbitrar
    modelo.TA = py.Set(modelo.P, initialize = TA) #Conjunto de tuplas de arbitros que pueden arbitrar el partido correspondiente
    modelo.TO = py.Set(modelo.P, initialize = TO) #Conjunto de quaternas de oficiales de mesa que pueden anotar el partido correspondiente

    ## PARÁMETROS
    modelo.h = py.Param(modelo.P, initialize = h) #Hora, en minutos, de inicio del partido p
    modelo.m = py.Param(modelo.P, initialize = m) #Campo de juego del partido p

    modelo.t = py.Param(modelo.C, modelo.C, initialize = t) #Tiempo que cuesta ir del campo de juego del partido p al campo de juego del partido q

    modelo.d = py.Param(modelo.P, initialize = d) #Duración aproximada del partido p
    modelo.la = py.Param(modelo.P, initialize = la) #Tiempo mínimo anterior a la hora de inicio del partido p, que deben estar los árbitros en el terreno de juego
    modelo.lo = py.Param(modelo.P, initialize = lo) #Tiempo mínimo anterior a la hora de inicio del partido p, que deben estar los oficiales de mesa en el terreno de juego

    modelo.ct = py.Param(modelo.P, initialize = ct) #Categoría del partido p
    modelo.mc = py.Param(modelo.A, initialize = mc) #Máxima categoría que puede arbitrar el árbitro a

    modelo.pf = py.Param(modelo.AFEB, initialize = pf) #Indica si los arbitros pertenecientes a la categoría FEB, han tenido partido en la federacion española o no

    modelo.na = py.Param(modelo.P, initialize = na) #Número de árbitros necesarios para el partido p
    modelo.no = py.Param(modelo.P, initialize = no) #Número de oficiales de mesa necesarios para el partido p

    modelo.ma1 = py.Param(initialize = ma1) #Número mínimo de árbitros de categoria A1, que tienen que arbitrar los partidos de la categoria 1ª Nacional Masculina A1
    modelo.fa1 = py.Param(initialize = fa1) #Número mínimo de árbitros de categoria A2, que tienen que arbitrar los partidos de la categoria 1ª Nacional Femenina A1
    modelo.ma2 = py.Param(initialize = ma2) #Número mínimo de árbitros de categoria A3, que tienen que arbitrar los partidos de la categoria 1ª Nacional Masculina A2
    modelo.fa2 = py.Param(initialize = fa2) #Número mínimo de árbitros de categoría A4, que tienen que arbitrar los partidos de la categoria 1ª Nacional Femenina A2
    modelo.pad = py.Param(initialize = pad) #Número mínimo de árbitros de categoría P3, que tienen que arbitrar los partidos de las categorías Junior Aragon Masculino 2ª y 2ª Aragonesa Femenina

    print(ma1)
    print(fa1)
    print(ma2)
    print(fa2)

    modelo.mx = py.Param(initialize = mx) #Número máximo de partidos que hay en una franja
    modelo.mn = py.Param(initialize = mn) #Número máximo de partidos entre las franjas que no corresponden al valor del parámetro mx

    M = 10000 #Big-M

    ## CONJUNTOS AUXILIARES PARA LAS VARIABLES DE DECISIÓN
    modelo.x_index = py.Set(initialize = x_index)
    modelo.y_index = py.Set(initialize = y_index)
    modelo.z_index = py.Set(initialize = z_index)
    modelo.y_index_arbitros = py.Set(initialize = y_index_arbitros)
    modelo.y_index_anotadores = py.Set(initialize = y_index_anotadores)

    ## VARIABLES DE DECISIÓN
    modelo.x = py.Var(modelo.x_index, domain = py.Binary) #Si el partido p lo arbitran el árbitro principal i, y el arbitro auxiliar j
    modelo.z = py.Var(modelo.z_index, domain = py.Binary) #Si el partido p lo anotan el oficial de mesa a, el cronometrador c, el operador de 24" a y el ayudante de anotador y
    modelo.y = py.Var(modelo.y_index, domain = py.Binary) #Si el partido p lo arbitra/anota el árbitro/oficial de mesa a

    modelo.st = py.Var(modelo.A.union(modelo.O), domain = py.Binary) #Si el árbitro/oficial de mesa a, tiene partido el sábado por la tarde
    modelo.dm = py.Var(modelo.A.union(modelo.O), domain = py.Binary) #Si el árbitro/oficial de mesa a, tiene partido el domingo por la mañana
    modelo.dt = py.Var(modelo.A.union(modelo.O), domain = py.Binary) #Si el árbitro/oficial de mesa a, tiene partido el domingo por la tarde

    modelo.v = py.Var(modelo.A.union(modelo.O), domain = py.NonNegativeIntegers) #Número de franjas en las que el árbitro/oficial de mesa a tiene partidos

    modelo.w = py.Var(modelo.A.union(modelo.O), domain = py.Binary) #Si el árbitro/oficial de mesa a, tiene partido en dos o menos franjas

    ## FUNCIÓN OBJETIVO (REALMENTE MULTI-OBJETIVO)
    def objetivo(modelo):
        rest1 = sum(modelo.x[p,i,j] for (p,i,j) in modelo.x_index) + sum(modelo.z[p,a,c,o,ay] for (p,a,c,o,ay) in modelo.z_index)
        rest2 = sum(modelo.w[a] for a in modelo.A.union(modelo.O))
        return alpha*rest1 + beta*rest2

    modelo.obj = py.Objective(rule = objetivo, sense = py.maximize)

    ##RESTRICCIONES
    '''1. Cada partido puede ser arbitrado/anotado por una única tupla/cuaterna de árbitros/oficiales de mesa, respectivamente.'''
    def todos_partidos_arbitrados(modelo,p):
        rest = sum(modelo.x[p,i,j] for (i,j) in modelo.TA[p]) <= 1
        return rest

    modelo.todos_partidos_arbitrados = py.Constraint(modelo.P, rule = todos_partidos_arbitrados)

    def todos_partidos_anotados(modelo,p):
        rest = sum(modelo.z[p,a,c,o,ay] for (a,c,o,ay) in modelo.TO[p]) <= 1
        return rest

    modelo.todos_partidos_anotados = py.Constraint(modelo.P, rule = todos_partidos_anotados)
    print("Restriccion 1 'Todos los partidos deben ser arbitrados' añadida")

    '''2. Relacion entre las variables x-y, z-y.'''
    def unico_arbitro(modelo,p,a):
        AR = [x for x in modelo.TA[p] if x[0] == a]
        AU = [x for x in modelo.TA[p] if x[1] == a]
        rest = modelo.y[p,a] == sum(modelo.x[p,i,j] for (i,j) in AR) + sum(modelo.x[p,i,j] for (i,j) in AU)
        return rest

    modelo.unico_arbitro = py.Constraint(modelo.y_index_arbitros, rule = unico_arbitro)

    def unico_anotador(modelo,p,a):       
        ACO = [x for x in modelo.TO[p] if x[0] == a] 
        CAO = [x for x in modelo.TO[p] if x[1] == a] 
        OCA = [x for x in modelo.TO[p] if x[2] == a]
        AY = [x for x in modelo.TO[p] if x[3] == a]
        
        rest = modelo.y[p,a] == (sum(modelo.z[p,i,c,o,ay] for (i,c,o,ay) in ACO) + 
                                    sum(modelo.z[p,i,c,o,ay] for (i,c,o,ay) in CAO ) + 
                                    sum(modelo.z[p,i,c,o,ay] for (i,c,o,ay) in OCA) + 
                                    sum(modelo.z[p,i,c,o,ay] for (i,c,o,ay) in AY))
        return rest

    modelo.unico_anotador = py.Constraint(modelo.y_index_anotadores, rule = unico_anotador)

    print("Restriccion 2 'Relación entre las variables x-y, z-y' añadida")

    '''3. Los árbitros y oficiales de mesa que no tengan el partido p en su conjunto de partidos
          que pueden realizar, no pueden realizar ese partido'''
    modelo.eliminar = py.ConstraintList()
    for p in modelo.P:
        for a in modelo.A-modelo.AP[p]:
            modelo.eliminar.add(modelo.y[p,a] == 0)
        
        for o in modelo.O - modelo.OP[p]:
            modelo.eliminar.add(modelo.y[p,o] == 0)
            
    print("Restriccion 3 'Partidos que no se pueden realizar' añadida")        

    '''4.Cada árbitro/oficial tiene que cumplir con las diferentes horas de los partidos'''
    def partidos_distinto_campo_arbitros(modelo,p,a,q):
        rest = modelo.h[p]*modelo.y[p,a] + modelo.d[p] + modelo.la[q] + modelo.t[modelo.m[p],modelo.m[q]] -M*(1-modelo.y[p,a]) <= modelo.h[q]*modelo.y[q,a] + M*(1-modelo.y[q,a])
        return rest

    def partidos_distinto_campo_oficiales(modelo,p,a,q):
        rest = modelo.h[p]*modelo.y[p,a] + modelo.d[p] + modelo.lo[q] + modelo.t[modelo.m[p],modelo.m[q]] -M*(1-modelo.y[p,a]) <= modelo.h[q]*modelo.y[q,a] + M*(1-modelo.y[q,a])
        return rest

    def partidos_mismo_campo(modelo,p,a,q):
        rest = modelo.h[p]*modelo.y[p,a] + 75 + modelo.t[modelo.m[p],modelo.m[q]] -M*(1-modelo.y[p,a]) <= modelo.h[q]*modelo.y[q,a] + M*(1-modelo.y[q,a])
        return rest

    rest3_1 = [(p,a,q) for p in P for a in AP[p] for q in PA[a] if q in P if q!=p if h[p] <= h[q] if m[p]!=m[q]]
    rest3_2 = [(p,a,q) for p in P for a in OP[p] for q in PO[a] if q in P if q!=p if h[p] <= h[q] if m[p]!=m[q]]

    rest3_3 = [(p,a,q) for p in P for a in AP[p] for q in PA[a] if q in P if q!=p if h[p] <= h[q] if m[p]==m[q]]
    rest3_4 = [(p,a,q) for p in P for a in OP[p] for q in PO[a] if q in P if q!=p if h[p] <= h[q] if m[p]==m[q]]

    modelo.partidos_distinto_campo1 = py.Constraint(rest3_1, rule = partidos_distinto_campo_arbitros)
    modelo.partidos_distinto_campo2 = py.Constraint(rest3_2, rule = partidos_distinto_campo_oficiales)

    modelo.partidos_mismo_campo1 = py.Constraint(rest3_3, rule = partidos_mismo_campo)
    modelo.partidos_mismo_campo2 = py.Constraint(rest3_4, rule = partidos_mismo_campo)

    modelo.horas_partidos_nuevo = py.ConstraintList()
    for p in P:
        for a in AP[p]:
            for q in PA[a]:
                if q in P:
                    if q!=p:
                        if h[p] <= h[q]:
                            if 2160 <= h[p] <= 2280:
                                modelo.horas_partidos_nuevo.add(modelo.h[p]*modelo.y[p,a] + modelo.d[p] + 60 + modelo.la[q] + modelo.t[modelo.m[p],modelo.m[q]] -10000*(1-modelo.y[p,a]) <= modelo.h[q]*modelo.y[q,a] + 10000*(1-modelo.y[q,a]))
                                
        for a in OP[p]:
            for q in PO[a]:
                if q in P:
                    if q!=p:
                        if h[p] <= h[q]:
                            if 2160 <= h[p] <= 2280:
                                modelo.horas_partidos_nuevo.add(modelo.h[p]*modelo.y[p,a] + modelo.d[p] + 60 + modelo.lo[q] + modelo.t[modelo.m[p],modelo.m[q]] -10000*(1-modelo.y[p,a]) <= modelo.h[q]*modelo.y[q,a] + 10000*(1-modelo.y[q,a]))
                                

    print("Restriccion 4 'Horario de los partidos' añadida")

    '''5. Cada arbitro de categoria nacional puede arbitrar a lo sumo 1 partido de su máxima categoria por fin de semana'''
    modelo.maxima_categoria_arbitros = py.ConstraintList()
    for a in modelo.AN:
        if mc[a] in modelo.CA:
            if modelo.PA[a] != []:
                if [p for p in modelo.PA[a] if modelo.ct[p] == modelo.mc[a]] != []:
                    modelo.maxima_categoria_arbitros.add(sum(modelo.y[p,a] for p in modelo.PA[a] if modelo.ct[p] == modelo.mc[a]) <= 1)

    print("Restriccion 5 'Partido de máxima categoria' añadida")

    '''6. Cada árbitro de categoria nacional puede arbitrar a lo sumo 2 partidos al fin de semana de categorias nacionales (A1 o A2) + FEB'''
    modelo.nacionales = py.ConstraintList()
    for a in modelo.AN:
        if a in modelo.AFEB:
            if PA[a] != []:
                interseccion = [p for p in modelo.PA[a] if p in modelo.PN]
                if interseccion != []:
                    modelo.nacionales.add(sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PN) + modelo.pf[a] <= 2)
        else:
            if PA[a] != []:
                interseccion = [p for p in modelo.PA[a] if p in modelo.PN]
                if interseccion != []:
                    modelo.nacionales.add(sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PN) <= 2)

    print("Restriccion 6 'Partidos de categoria nacional' añadida")            

    '''7. Todos los árbitros de categoría A1 o A2, deben árbitrar al menos un partido al fin de semana de categoría nacional'''
    for a in modelo.AA1.union(modelo.AA2):
        if PA[a] != []:
            interseccion = [p for p in modelo.PA[a] if p in modelo.PN]
            if interseccion != []:
                modelo.nacionales.add(sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PN) >= 1)

    print("Restriccion 7 'Arbitros de categoria A1, A2 minimo 1 partido' añadida")

    '''8. Los partidos de categoria nacional deben ser arbitrados por un mínimo de árbitros de la categoría correspondiente'''    
    modelo.partidos_por_categoria = py.ConstraintList()
    modelo.partidos_por_categoria.add(sum(modelo.y[p,a] for p in modelo.NFA1 for a in modelo.AA2 if a in modelo.AP[p]) >= modelo.fa1)
    modelo.partidos_por_categoria.add(sum(modelo.y[p,a] for p in modelo.NMA1 for a in modelo.AA1 if a in modelo.AP[p]) >= modelo.ma1)
    modelo.partidos_por_categoria.add(sum(modelo.y[p,a] for p in modelo.NFA2 for a in modelo.AA4 if a in modelo.AP[p]) >= modelo.fa2)
    modelo.partidos_por_categoria.add(sum(modelo.y[p,a] for p in modelo.NMA2 for a in modelo.AA3 if a in modelo.AP[p]) >= modelo.ma2)
    modelo.partidos_por_categoria.add(sum(modelo.y[p,a] for p in modelo.PD for a in modelo.AP3 if a in modelo.AP[p]) >= modelo.pad)

    print("Restriccion 8 'Partidos de categoría nacional' añadida")

    '''9. Los árbitros solo pueden arbitrar una de las siguientes dos categorias en el fin de semana NFA1 y NMA1'''
    '''De Nacional Masculino + Nacional Femenino solo un partido a lo sumo'''
    '''De Nacional Femenino + Autonomica de Chicas solo un partido a lo sumo'''
    modelo.partidos_naciones_arbitros = py.ConstraintList()
    for a in modelo.A:
        modelo.partidos_naciones_arbitros.add(sum(modelo.y[p,a] for p in NFA1+NMA1) <= 1)
        modelo.partidos_naciones_arbitros.add(sum(modelo.y[p,a] for p in NFA1+NMA2) <= 1)

    arbitros_nacionales_masculinos_disponibles = []
    for p in NMA1:
        for a in AP[p]:
            if a in arbitros_nacionales_masculinos_disponibles:
                next
            else:
                if a in AFEB:
                    if pf[a] == 1:
                        next
                    else:
                        arbitros_nacionales_masculinos_disponibles.append(a)
                else:
                    arbitros_nacionales_masculinos_disponibles.append(a)
    
    if len(arbitros_nacionales_masculinos_disponibles) >= len(NMA1)*2:
        for a in modelo.AFEB:
            modelo.partidos_naciones_arbitros.add(sum(modelo.y[p,a] for p in NFA1 + NMA1) + modelo.pf[a] <= 1) 
    else:
        for a in modelo.AFEB:
            modelo.partidos_naciones_arbitros.add(sum(modelo.y[p,a] for p in NFA1 + NMA1) <= 1)

    print("Restriccion 'Arbitros combinacion en categoria nacional' añadida")
        
    '''10. Cada fin de semana cada árbitro, puede árbitrar a lo sumo 4 partidos federados'''
    modelo.partidos_maximos_totales = py.ConstraintList()
    for a in modelo.A:
        if PA[a] != []:
            modelo.partidos_maximos_totales.add(sum(modelo.y[p,a] for p in modelo.PA[a]) <= 4)
            
    print("Restriccion 10 'Número máximos de partidos a lo largo del fin de semana' añadida")    
        
    '''11. Partidos mínimos y máximos que pueden realizar tanto árbitros como oficiales'''
    modelo.federados = py.ConstraintList()
    for a in modelo.A:
        if PA[a] != []:
            modelo.federados.add(sum(modelo.y[p,a] for p in modelo.PA[a]) >= 1)
            
    for o in modelo.O:
        if PO[o]!= []:
            if o in OE:
                modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) <= 1)
                
            elif o in OP2:
                modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 1)
                if o in F3:
                    modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) <= 4)
                else:
                    modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) <= 3)
                    
            elif o in OP1:
                modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 1)
                modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) <= 4)
                    
            elif o in OA + OLF + OLF2 + O1:
                if len(PO[o]) > modelo.mx:
                    modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 3)
                elif len(PO[o]) < modelo.mn:
                    modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 1)
                else:
                    modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 2)
                    
            else:
                modelo.federados.add(sum(modelo.y[p,o] for p in modelo.PO[o]) >= 1)

    print("Restriccion 11 'Todos los árbitros y oficiales tienen al menos un partido' añadida")

    modelo.restricciones_oficiales = py.ConstraintList()
    '''12. Los oficiales de mesa pueden hacer a lo sumo un partido de categoria FEB a lo largo del fin de semana'''    
    for o in modelo.ON:
        modelo.restricciones_oficiales.add(sum(modelo.y[p,o] for p in PFEB) <= 1)

    print("Restriccion 12 'Partidos de categoria FEB para oficiales' añadida")    

    '''13. En los partidos de liga EBA, debe haber un mínimo de oficiales de la categoria liga eba. Siempre que se pueda ese mínimo sera 3.'''
    oficiales_eba_disponibles = []
    for p in P_EBA_LF2:
        for o in OP[p]:
            if o in oficiales_eba_disponibles:
                next
            else:
                if o in OLF2:
                    oficiales_eba_disponibles.append(o)
    
    moed = min(3,int(len(oficiales_eba_disponibles)/len(P_EBA_LF2)))
    print('moed', moed)

    for p in P_EBA_LF2:
        modelo.restricciones_oficiales.add(sum(modelo.y[p,o] for o in OLF2) >= moed)

    print("Restriccion 13 'Partidos de liga EBA, número de oficiales' añadida")

    '''14. Tener al menos 1 partido nacional todos los oficiales que pueda'''
    for o in ON:
        if PO[o] != []:
            interseccion = [p for p in modelo.PO[o] if p in modelo.PN]
            if interseccion != []:
                modelo.restricciones_oficiales.add(sum(modelo.y[p,o] for p in (PN + PBSR)) >= 1)

    print("Restriccion 14 'Partidos nacionales oficiales' añadida")

    '''15. En todos los partidos que conlleven desplazamiento, al menos 1 de los integrantes del equipo arbitral debe llevar coche'''
    def desplazamientos_coche(modelo, p):
        rest = sum(modelo.y[p,a] for a in modelo.CH if a in modelo.AP[p].union(modelo.OP[p])) >= 1
        return rest

    modelo.desplazamientos_coche = py.Constraint(modelo.PC, rule = desplazamientos_coche)

    print("Restriccion 15 'Desplazamiento en los partidos' añadida")

    '''16. En cada franja los árbitros/oficiales de mesa pueden realizar a lo sumo dos partidos'''
    modelo.partidos_franja = py.ConstraintList()
    for a in modelo.A:
        for f in F:
            if [p for p in modelo.PA[a] if p in f] != []:
                modelo.partidos_franja.add(sum(modelo.y[p,a] for p in modelo.PA[a] if p in f) <= 2)
                
    for a in modelo.O:
        for f in F:
            if [p for p in modelo.PO[a] if p in f] != []:
                modelo.partidos_franja.add(sum(modelo.y[p,a] for p in modelo.PO[a] if p in f) <= 2)
                
    print("Restriccion 16 'Partidos máximos por franjas' añadida")    

    '''17. En los partidos con desplazamiento, si hay dos partidos seguidos, los tienen que arbitrar/anotar las mismas personas'''
    modelo.partidos_con_desplazamiento = py.ConstraintList()
    modelo.arbitros_oficiales_mismo_campo = py.ConstraintList()
    for c in modelo.C:
        for f in F:
            sub = [x for x in f if partidos.loc[x, 'CAMPO'] == c if partidos.loc[x, 'Categoria'] in categorias_federados]
            if c in campos_desplazamientos:
                #Partidos que se juegan dentro de la franaja correspondiente y en el campo correspondiente. Esta restricción sólo
                #se aplica a los partidos de categoria federado/escolar. No a partidos de categoría FEB.
                if len(sub) == 2:
                    for p in sub:
                        for q in sub:
                            if modelo.h[p] < modelo.h[q]:
                                
                                ##OFICIALES DE MESA##
                                if no[p] <= no[q]:
                                    #Si hay un desplazamiento de dos partidos, siendo el número de oficiales de mesa menor o igual en el
                                    #primer partido que en el segundo. Si en el primero se necesita un/dos oficial de mesa, este/estos obligatoriamente
                                    #tendrá que hacer también el segundo partido.                        
                                    for a in modelo.O:
                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[q,a])
                                    
                                else:
                                    #Si hay un desplazamiento de dos partidos, siendo el número de oficiales de mesa mayor o igual en el 
                                    #primer partido que en el segundo. Aquellos oficiales de mesa que hagan el segundo partido, deberán haber 
                                    #hecho también el primer partido
                                    for a in modelo.O:
                                        modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[p,a])   
                                    
                                    #Además hay que asegurarse que aquellas personas que hagan el primer partido, pero no el segundo, tengan coche
                                    #para volver a Zaragoza tras acabar el primer partido
                                    modelo.partidos_con_desplazamiento.add(sum(modelo.y[q,a] for a in modelo.CH) + 1 <= sum(modelo.y[p,a] for a in modelo.CH)) 
                                
                                if no[p] < no[q]:
                                    modelo.partidos_con_desplazamiento.add(sum(modelo.y[p,a] for a in modelo.CH) + 1 <= sum(modelo.y[q,a] for a in modelo.CH))                                                
                                
                                ##ÁRBITROS##
                                if ((modelo.ct[p] in [categorias_federados[0], categorias_federados[1]]) or
                                    (modelo.ct[q] in [categorias_federados[0], categorias_federados[1]])) :
                                    next
                                    
                                else:
    #                                 print('2 partidos fuera de Zaragoza', c,p,q)
                                    if na[p] <= na[q]:
                                        #Si hay un desplazamiento de dos partidos, siendo el número de árbitros menor o igual en el
                                        #primer partido que en el segundo. Si en el primero se necesita un árbitro, este obligatoriamente
                                        #tendrá que hacer también el segundo partido.
                                        for a in modelo.A:
                                            modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[q,a])

                                    else:
                                        #El segundo partido requiere unicamente un árbitro, mientras que el primero requiere dos arbitros.
                                        #Por ello, uno de los árbitros del primer partido, deberá hacer el segundo partido
                                        #Lo mismo ocurre, con los oficiales de mesa      
                                        for a in modelo.A:
                                            modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[p,a])

                                    #Para que el partido anterior lo realice el árbitro de menor categoría
                                    if na[p] < na[q]:
                                        for (a1,a2) in modelo.TA[q]:
                                            modelo.partidos_con_desplazamiento.add(modelo.y[q,a2] <= modelo.y[p,a2])

                                    if na[q] < na[p]:
                                        for (a1,a2) in modelo.TA[p]:
                                            modelo.partidos_con_desplazamiento.add(modelo.y[p,a2] <= modelo.y[q,a2])
                        

                elif len(sub) == 3:
                    for p in sub:
                        for q in sub:
                            for r in sub:
                                if modelo.h[p] < modelo.h[q]:
                                    if modelo.h[q] < modelo.h[r]:
                                        if na[p] == na[q]:
                                            if no[p] == no[q]:
    #                                             print('3 partidos FUERA de Zaragoza', c,p,q)
                                                for a in modelo.A:
                                                    modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[q,a])

                                                for a in modelo.O:
                                                    modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[q,a])
                            
                                        elif na[q] == na[r]:
                                            if no[q] == no[r]:
    #                                             print('3 partidos FUERA de Zaragoza', c,p,q)
                                                for a in modelo.A:
                                                    modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[r,a])

                                                for a in modelo.O:
                                                    modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[r,a])
                            

            else:
                if len(sub) == 2:
                    for p in sub:
                        for q in sub:
                            if modelo.h[p] < modelo.h[q]:
                                if modelo.h[q] - 120 <= modelo.h[p]:
                                    if modelo.h[p] + 90 <= modelo.h[q]:
                                        ##OFICIALES##
                                        if no[p] == 1:
                                            #Si se hace el primer partido se tiene que hacer también el segundo
                                            for o in modelo.O:
                                                modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,o] <= modelo.y[q,o])

                                        elif no[p] == 2:
                                            #Al menos un oficial que haya hecho el primer partido deberá hacer también el segundo partido
                                            for (a1,a2,a3,a4) in modelo.TO[p]:
                                                modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,a1] + modelo.y[p,a2] -1 <= modelo.y[q,a1] + modelo.y[q,a2])

                                        elif no[p] == 3:
                                            #Al menos un oficial que haya hecho el primer partido deberá hacer también el segundo partido
                                            for (a1,a2,a3,a4) in modelo.TO[p]:
                                                modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,a1] + modelo.y[p,a2] + modelo.y[p,a3] -2 <= modelo.y[q,a1] + modelo.y[q,a2] + modelo.y[q,a3])

                                        ##ÁRBITROS##
                                        if ((modelo.ct[p] in [categorias_federados[0], categorias_federados[1]]) or 
                                            (modelo.ct[q] in [categorias_federados[0], categorias_federados[1]])) :
                                            next
                                        else:
                                            if na[p] == 1:
                                                for a in modelo.A:
                                                    modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,a] <= modelo.y[q,a])

                                            elif na[p] == 2:
                                                if (p in PN and q in PN):
                                                    next
                                                else:
                                                    #Al menos un árbitros que haya hecho el primer partido deberá hacer también el segundo partido
                                                    for (a1,a2) in modelo.TA[p]:
                                                        modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,a1] + modelo.y[p,a2] -1 <= modelo.y[q,a1] + modelo.y[q,a2])

                                else:
                                    #Como hay tanta diferencia entre el primer y el segundo partido. Los árbitros/oficiales
                                    #de mesa que hagan el primer partido, no podrán hacer el segundo
    #                                 print('2 partidos en Zaragoza con mucha diferencia', c,p,q)
                                    for a in modelo.A:
                                        modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,a] <= 1 - modelo.y[q,a])
                                    for o in modelo.O:
                                        modelo.arbitros_oficiales_mismo_campo.add(modelo.y[p,o] <= 1 - modelo.y[q,o])

                elif len(sub) == 3:
                    for p in sub:
                        for q in sub:
                            for r in sub:
                                if p!=q:
                                    if p!=r:
                                        if q!=r:
                                            if modelo.h[p] <= modelo.h[q] <= modelo.h[r]:
                                                if modelo.h[q] - modelo.h[p] <= 30:
                                                    if modelo.h[r] - modelo.h[p] <= 120:
                                                        if modelo.h[r] - modelo.h[q] <= 120:
                                                            if na[p] == 1:
                                                                if na[p] == na[q]:
                                                                    if na[r] == 2:
                                                                        for a in modelo.A:
                                                                            modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[r,a])
                                                                            modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[r,a])
                    
                                                                        for o in modelo.O:
                                                                            modelo.partidos_con_desplazamiento.add(modelo.y[p,o] <= modelo.y[r,o])
                                                                            modelo.partidos_con_desplazamiento.add(modelo.y[q,o] <= modelo.y[r,o])



                                                elif modelo.h[p] + 75 < modelo.h[q]:
                                                    if modelo.h[q] + 75 < modelo.h[r]:
                                                        #Siempre que haya mas de 1 hora y 15 de diferencia entre cada partido.
                                                        #Tanto árbitros como oficiales si se hace el segundo partido, se ha tenido que hacer el primer partido
                                                        #o se tendrá que hacer el tercer partido.
                                                        if q in modelo.PN:
                                                            if p in modelo.PN and r in modelo.PN:
                                                                next
                                                            elif p in modelo.PN and r not in modelo.PN:
                                                                for (a1,a2) in modelo.TA[q]:
                                                                    modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] -1 <= modelo.y[r,a1] + modelo.y[r,a2])
                                                            elif p not in modelo.PN and r in modelo.PN:
                                                                for (a1,a2) in modelo.TA[q]:
                                                                    modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] -1 <= modelo.y[p,a1] + modelo.y[p,a2])
                                                            else:
                                                                for (a1,a2) in modelo.TA[q]:
                                                                    modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] -1 <= modelo.y[p,a1] + modelo.y[p,a2] +modelo.y[r,a1] + modelo.y[r,a2])

                                                        else:
                                                            for a in modelo.A:
                                                                modelo.partidos_con_desplazamiento.add(modelo.y[q,a] <= modelo.y[p,a]+modelo.y[r,a])

                                                        for (a1,a2,a3,a4) in modelo.TO[q]:
                                                            if no[q] == 3:
                                                                modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] + modelo.y[q,a3] -2 <= modelo.y[p,a1] + modelo.y[p,a2] + modelo.y[p,a3])
                                                                modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] + modelo.y[q,a3] -2 <= modelo.y[r,a1] + modelo.y[r,a2] + modelo.y[r,a3])

                                                            elif no[q] == 2:
                                                                modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] <= modelo.y[p,a1] + modelo.y[p,a2] + modelo.y[r,a1] + modelo.y[r,a2])
                                                                # modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] + modelo.y[q,a2] - 1 <= modelo.y[r,a1] + modelo.y[r,a2])

                                                            elif no[q] == 1:
                                                                modelo.partidos_con_desplazamiento.add(modelo.y[q,a1] <= modelo.y[p,a1] + modelo.y[r,a1])
                                                        
                                                        for a in modelo.A.union(modelo.O):
                                                            modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= 1 - modelo.y[r,a])
                                                
                                            
                elif len(sub) == 4:
                    for p in sub:
                        for q in sub:
                            for r in sub:
                                for s in sub:
                                    if modelo.h[p] + 75 < modelo.h[q]:
                                        if modelo.h[q] + 75 < modelo.h[r]:
                                            if modelo.h[r] + 75 < modelo.h[s]:
                                                if na[p] == 2:
                                                    for (a1,a2) in modelo.TA[p]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,a1] + modelo.y[p,a2] -1 <= modelo.y[q,a1] + modelo.y[q,a2])
                                                    
                                                if no[p] == 2:
                                                    for (a1,a2,a3,a4) in modelo.TO[p]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,a1] + modelo.y[p,a2] -1 <= modelo.y[q,a1] + modelo.y[q,a2])

                                                if no[p] == 3:
                                                    for (a1,a2,a3,a4) in modelo.TO[p]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,a1] + modelo.y[p,a2] + modelo.y[p,a3] -2 <= modelo.y[q,a1] + modelo.y[q,a2] + modelo.y[q,a3])
                                                
                                                if na[p] == 1:
                                                    for a in modelo.A:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,a] <= modelo.y[q,a])
                                                    for o in modelo.O:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[p,o] <= modelo.y[q,o])
                                                
                                                if na[r] == 2:
                                                    for (a1,a2) in modelo.TA[r]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[r,a1] + modelo.y[r,a2] -1 <= modelo.y[s,a1] + modelo.y[s,a2])
                                                    
                                                if no[r] == 2:
                                                    for (a1,a2,a3,a4) in modelo.TO[r]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[r,a1] + modelo.y[r,a2] -1 <= modelo.y[s,a1] + modelo.y[s,a2])
                                                
                                                if no[r] == 3:
                                                    for (a1,a2,a3,a4) in modelo.TO[p]:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[r,a1] + modelo.y[r,a2] + modelo.y[r,a3] -2 <= modelo.y[s,a1] + modelo.y[s,a2] + modelo.y[s,a3])
                                            
                                                if na[r] == 1:
                                                    for a in modelo.A:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[r,a] <= modelo.y[s,a])
                                                    for o in modelo.O:
                                                        modelo.partidos_con_desplazamiento.add(modelo.y[r,o] <= modelo.y[s,o])
                                                
                                                
                                        
    modelo.restricciones_varias = py.ConstraintList()

    modelo.restricciones_varias.add(sum(modelo.y[p, 'TEJEDOR'] for p in PST if p in PA['TEJEDOR']) <= 1)
    modelo.restricciones_varias.add(sum(modelo.y[p, 'TEJEDOR'] for p in PDM + PDT if p in PA['TEJEDOR']) <= 1)    

    def franjas_arbitros_st(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PST)/len(modelo.PST) <= modelo.st[a]
        return rest

    def franjas_oficiales_st(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PO[a] if p in modelo.PST)/len(modelo.PST) <= modelo.st[a]
        return rest

    def franjas_arbitros_dm(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PDM)/len(modelo.PDM) <= modelo.dm[a]
        return rest

    def franjas_oficiales_dm(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PO[a] if p in modelo.PDM)/len(modelo.PDM) <= modelo.dm[a]
        return rest

    def franjas_arbitros_dt(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PA[a] if p in modelo.PDT)/len(modelo.PDT) <= modelo.dt[a]
        return rest

    def franjas_oficiales_dt(modelo,a):
        rest = sum(modelo.y[p,a] for p in modelo.PO[a] if p in modelo.PDT)/len(modelo.PDT) <= modelo.dt[a]
        return rest

    modelo.franjas_arbitros_st = py.Constraint(modelo.A, rule = franjas_arbitros_st)
    modelo.franjas_oficiales_st = py.Constraint(modelo.O, rule = franjas_oficiales_st)
    modelo.franjas_arbitros_dm = py.Constraint(modelo.A, rule = franjas_arbitros_dm)
    modelo.franjas_oficiales_dm = py.Constraint(modelo.O, rule = franjas_oficiales_dm)
    modelo.franjas_arbitros_dt = py.Constraint(modelo.A, rule = franjas_arbitros_dt)
    modelo.franjas_oficiales_dt = py.Constraint(modelo.O, rule = franjas_oficiales_dt)

    modelo.tres_franjas = py.ConstraintList()                
    for a in modelo.A.union(modelo.O):
        modelo.tres_franjas.add(modelo.v[a] == modelo.st[a] + modelo.dm[a] + modelo.dt[a])
        modelo.tres_franjas.add(modelo.v[a] + modelo.w[a] <= 3)
        modelo.tres_franjas.add(3*(1- modelo.w[a]) <= modelo.v[a])

    for p in modelo.PFEB:
        modelo.tres_franjas.add(sum(modelo.z[p,a,c,o,ay] for (a,c,o,ay) in modelo.TO[p]) == 1)


    if solver == 'GUROBI':
        ##Solver GUROBI
        opt = py.SolverFactory("gurobi", solver_io = 'python')
        opt.options['TimeLimit'] = 3600*6
        # opt.options['TimeLimit'] = 1000
        # opt.options['MIPGap'] = 0.004
    
    elif solver == 'CPLEX':
        ##SOLVER CPLEX
        opt = py.SolverFactory("cplex")
        opt.options['timelimit'] = 3600*6
    
    elif solver == 'CBC':
        ##SOLVER CBC
        opt = py.SolverFactory("cbc")
        opt.options['seconds'] = 4000

    # opt.options['infestol'] = 0.01
    print('Comenzando a resolver')
    opt.solve(modelo, tee = True).write()
    end = time.time()

    ##OBTENCIÓN DE RESULTADOS
    variable_x = save_data(modelo, 'x').rename(columns = {0: 'Partido', 1:'Arbitro_Principal', 2:'Arbitro_Auxiliar', 3:'Decision'}).set_index('Partido')
    variable_x = variable_x[variable_x.Decision == 1]

    variable_z = save_data(modelo, 'z').rename(columns = {0: 'Partido', 1:'Anotador', 2:'Cronometrador', 3:'Operador 24"', 4: 'Ayudante Anotador', 5:'Decision'}).set_index('Partido')
    variable_z = variable_z[variable_z.Decision == 1]

    variable_y = save_data(modelo, 'y').rename(columns = {0:'Partido',1:'Arbitro',2:'Decision'})
    variable_y = variable_y[variable_y.Decision == 1]

    variable_v = save_data(modelo, 'v').rename(columns = {0: 'Árbitro/Anotador', 1: 'Decision'})

    variable_w = save_data(modelo, 'w').rename(columns = {0: 'Árbitro/Anotador', 1: 'Decision'})
    variable_w = variable_w[variable_w.Decision == 1]

    Asignacion = pd.DataFrame()
    for p in partidos.index:
        Asignacion.loc[p,'Categoria'] = partidos.loc[p,'Categoria']
        Asignacion.loc[p,'Local'] = partidos.loc[p,'EQUIPO LOCAL']
        Asignacion.loc[p,'Visitante'] = partidos.loc[p,'EQUIPO VISITANTE']
        Asignacion.loc[p,'Hora'] = partidos.loc[p,'HoraDeJuego']
        Asignacion.loc[p,'Fecha'] = partidos.loc[p,'FECHA']
        Asignacion.loc[p,'Campo'] = partidos.loc[p,'CAMPO']
        if p in variable_x.index:
            Asignacion.loc[p,'Arbitro Principal'] = variable_x.loc[p,'Arbitro_Principal']
            Asignacion.loc[p,'Arbitro Auxiliar'] = variable_x.loc[p,'Arbitro_Auxiliar']
        else:
            Asignacion.loc[p,'Arbitro Principal'] = ""
            Asignacion.loc[p,'Arbitro Auxiliar'] = ""
            
        if p in variable_z.index:
            Asignacion.loc[p,'Anotador'] = variable_z.loc[p,'Anotador']
            Asignacion.loc[p,'Cronometrador'] = variable_z.loc[p,'Cronometrador']
            Asignacion.loc[p,'Operador 24"'] = variable_z.loc[p,'Operador 24"']
            Asignacion.loc[p, 'Ayudante Anotador'] = variable_z.loc[p, 'Ayudante Anotador']

        else:
            Asignacion.loc[p,'Anotador'] = ""
            Asignacion.loc[p,'Cronometrador'] = ""
            Asignacion.loc[p,'Operador 24"'] = ""
            Asignacion.loc[p, 'Ayudante Anotador'] = ""
            
    Asignacion.set_index(['Categoria', 'Local', 'Visitante', 'Hora', 'Fecha', 'Campo'], inplace = True)
    Asignacion.sort_values(['Categoria','Fecha','Hora'])

    tiempo_ejecucion = (end - start)/60

    return tiempo_ejecucion, Asignacion, modelo.obj(), variable_x, variable_y, variable_z, variable_v, variable_w, arbitros, Partidos_FinDeSemana_Anterior, oficiales

                                                    