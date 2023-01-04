from FAB_CONJUNTOS import (categorias_federados,
                           categorias_escolares,
                           categorias_feb,
                           categorias_arbitros,
                           categorias_oficiales)

from datetime import datetime, timedelta, time 
import pandas as pd    

from difflib import SequenceMatcher as SQM

import json

'''Se definen un conjunto de diferentes funciones que son necesarias en el preproceso que se realiza a los datos de entrada.'''

#Funcion que determina las disponibilidades de árbitros y oficiales de mesa
def calculo_de_disponibilidades(partidos,
                                disponibilidad, 
                                disponibilidades_fijas,
                                partidos_por_categoria, rz):

    '''
    Esta función determina las diponibilidades de todos los árbitros y oficiales de mesa.

    Los parámetros de la función son los siguientes:

        - partidos: DataFrame que contiene todos los partidos a los cuales hay que asignar árbitros y oficiales de mesa.

        - disponibilidad: DataFrame que contiene si cada árbitro y oficiales de mesa puede realizar partidos en cada franja.

        - disponibilidades_fijas: DataFrame que contiene todos los árbitros y oficiales de mesa que juegan en algún equipo.

        - partidos_por_categoria: Diccionario que contiene el nombre de todos los equipos que juegan partido el fin de semana por categoria del partido.

        - rz: Terna que contiene la siguiente información, (juega o no en casa el equipo de fútbol Real Zaragoza el fin de semana, que día del fin de semana juega, hora de juego)
    '''

    for d in disponibilidades_fijas.index:
        spliteado = disponibilidades_fijas.loc[d, 'Equipos'].split('-')
        if len(spliteado) > 1:
            disponibilidades_fijas.loc[d, 'Categoria'] = spliteado[0].strip()
            disponibilidades_fijas.loc[d, 'Equipo'] = spliteado[1].strip()
        else:
            disponibilidades_fijas.loc[d, 'Categoria'] = spliteado[0]

    #Con la funcion strip, se eliminan espacios en blanco iniciales y finales de una cadena de texto    
            
    disponibilidades_fijas.drop(columns = ['Equipos'], inplace = True)

    for d in disponibilidades_fijas.index:
        valor_buscado = disponibilidades_fijas.loc[d, 'Equipo']
        if pd.isna(valor_buscado) == True:
            disponibilidades_fijas.loc[d, 'Nombre Equipo Exacto'] = disponibilidades_fijas.loc[d, 'Categoria']
        else:
            lista_de_opciones = partidos_por_categoria[disponibilidades_fijas.loc[d, 'Categoria']]
            matches = sorted(lista_de_opciones, key=lambda x: SQM(None, x, valor_buscado).ratio(), reverse=True) 
            disponibilidades_fijas.loc[d, 'Nombre Equipo Exacto'] = matches[0]

        if disponibilidades_fijas.loc[d, 'Categoria'] == 'REAL ZARAGOZA':
            if rz[0] == 'FUERA':
                next
            elif rz[0] == 'CASA':
                disponibilidades_fijas.loc[d, 'Hora De Juego'] = rz[2]
                disponibilidades_fijas.loc[d, 'Dia De Juego'] = rz[1]

        else:    
            sub = partidos[partidos.Categoria == disponibilidades_fijas.loc[d, 'Categoria']]
            partido_exacto = sub[(sub['EQUIPO LOCAL'] == matches[0] ) | (sub['EQUIPO VISITANTE'] == matches[0])]
            if len(partido_exacto) > 0:
                disponibilidades_fijas.loc[d, 'Hora De Juego']= partido_exacto.HoraDeJuego.values[0]
                disponibilidades_fijas.loc[d, 'Dia De Juego'] = partido_exacto.DiaSem.values[0]

    for d in disponibilidades_fijas.index:
        arb = disponibilidades_fijas.loc[d, 'Arbitro-Oficial']
        if disponibilidades_fijas.loc[d, 'Dia De Juego'] == 5:
            if disponibilidad.loc[arb, 'ST-Inicio'] != 1:
                if disponibilidades_fijas.loc[d, 'Hora De Juego'] >= time(18,0):
                    acaba = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') - timedelta(minutes = 90)).time()
                    if disponibilidad.loc[arb, 'ST-Final'] == 0:
                        disponibilidad.loc[arb, 'ST-Final'] = acaba
                    else:
                        disponibilidad.loc[arb, 'ST-Final'] = min(disponibilidad.loc[arb, 'ST-Final'], acaba)
                
                else:
                    empieza = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 180)).time()
                    if disponibilidad.loc[arb, 'ST-Inicio'] == 0:
                        disponibilidad.loc[arb, 'ST-Inicio'] = empieza
                    else:
                        disponibilidad.loc[arb, 'ST-Final'] = max(disponibilidad.loc[arb, 'ST-Inicio'], empieza)
        
        elif disponibilidades_fijas.loc[d, 'Dia De Juego'] == 6:
            if disponibilidades_fijas.loc[d, 'Hora De Juego'] >= time(15,0):
                if disponibilidad.loc[arb, 'DT-Inicio'] != 1:
                    if disponibilidades_fijas.loc[d, 'Hora De Juego'] >= time(18,0):
                        acaba = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') - timedelta(minutes = 90)).time()
                        if disponibilidad.loc[arb, 'DT-Final'] == 0:
                            disponibilidad.loc[arb, 'DT-Final'] = acaba
                        else:
                            disponibilidad.loc[arb, 'DT-Final'] = min(disponibilidad.loc[arb, 'DT-Final'], acaba)

                    else:
                        empieza = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 180)).time()
                        if disponibilidad.loc[arb, 'DT-Inicio'] == 0:
                            disponibilidad.loc[arb, 'DT-Inicio'] = empieza
                        else:
                            disponibilidad.loc[arb, 'DT-Final'] = max(disponibilidad.loc[arb, 'DT-Inicio'], empieza)
            
            else:
                if disponibilidad.loc[arb, 'DM-Inicio'] != 1:
                    if disponibilidades_fijas.loc[d, 'Hora De Juego'] >= time(11,0):
                        acaba = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') - timedelta(minutes = 90)).time()
                        if disponibilidad.loc[arb, 'DM-Final'] == 0:
                            disponibilidad.loc[arb, 'DM-Final'] = acaba
                        else:
                            disponibilidad.loc[arb, 'DM-Final'] = min(disponibilidad.loc[arb, 'DM-Final'], acaba)

                    else:
                        empieza = (datetime.strptime(disponibilidades_fijas.loc[d, 'Hora De Juego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 180)).time()
                        if disponibilidad.loc[arb, 'DM-Inicio'] == 0:
                            disponibilidad.loc[arb, 'DM-Inicio'] = empieza
                        else:
                            disponibilidad.loc[arb, 'DM-Final'] = max(disponibilidad.loc[arb, 'DM-Inicio'], empieza)

    return disponibilidad

#Funcion que crea las tuplas de arbitros para arbitrar cada partido
def tuplas_arbitros(P, partidos, 
                    lista_de_arbitros, 
                    arbitros, PA1, PA2, PA3, PA4, PP1):

    '''
    Esta función que crea las posibles tuplas de árbitros para arbitrar cada partido.

    Los parámetros de la función son los siguientes:

        - P: lista de los partidos para desginar árbitros.

        - partidos: DataFrame que contiene todos los aprtidos a los cuales hay que asignar arbitros y oficiales de mesa.

        - lista_de_arbitros: Diccionario que contiene que árbitros pertenecen a cada categoria de árbitros.

        - arbitros: Lista ordenada de todos los árbitros.

        - PA1: Lista de árbitros principales de categoria A1.

        - PA2: Lista de árbitros principales de categoria A2.

        - PA3: Lista de árbitros principales de categoria A3.

        - PA4: Lista de árbitros principales de categoria A4.

        - PP1: Lista de árbitros principales de categoria Provincial 1.

    '''

    TA = {} #Conjunto de tuplas de árbitros que pueden arbitrar el partido p
    for p in P:
        if ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
             and (partidos.loc[p, 'CAMPO'] == 'PAB. ALCAÑIZ')):
            TA[p] = []
            for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                      lista_de_arbitros[categorias_arbitros[1]] + 
                      lista_de_arbitros[categorias_arbitros[2]]):

                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):

                    TA[p].append((a,b))  
            
            for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                      lista_de_arbitros[categorias_arbitros[4]]):
                
                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):
                    
                    if arbitros.index(a) < arbitros.index(b):
                        TA[p].append((a,b))

        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. ANDORRA')):
            TA[p] = []
            for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                      lista_de_arbitros[categorias_arbitros[1]] + 
                      lista_de_arbitros[categorias_arbitros[2]]):

                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):

                    TA[p].append((a,b))  
            
            for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                      lista_de_arbitros[categorias_arbitros[4]]):
                
                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):
                    
                    if arbitros.index(a) < arbitros.index(b):
                        TA[p].append((a,b))                      
        
        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. LA ALMUNIA')):
            TA[p] = []
            for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                      lista_de_arbitros[categorias_arbitros[1]] + 
                      lista_de_arbitros[categorias_arbitros[2]]):

                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):

                    TA[p].append((a,b))  
            
            for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                      lista_de_arbitros[categorias_arbitros[4]]):
                
                for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):
                    
                    if arbitros.index(a) < arbitros.index(b):
                        TA[p].append((a,b))     

        else:
            TA[p] = []
            ca = partidos.Categoria[p]

            #Partidos de categoria nacional masculino A1
            if ca == categorias_federados[0]:

                for a in (lista_de_arbitros[categorias_arbitros[0]] + PA1):

                    for b in (lista_de_arbitros[categorias_arbitros[0]] + 
                              lista_de_arbitros[categorias_arbitros[1]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
                
            #Partidos de categoria nacional femenina A1
            elif ca == categorias_federados[1]:

                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          PA2):

                    for b in (lista_de_arbitros[categorias_arbitros[0]] + 
                              lista_de_arbitros[categorias_arbitros[1]] + 
                              lista_de_arbitros[categorias_arbitros[2]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
            
            #Partidos de categoria nacional masculino A2
            elif ca == categorias_federados[2]:

                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          PA3):

                    for b in (lista_de_arbitros[categorias_arbitros[0]] + 
                              lista_de_arbitros[categorias_arbitros[1]] + 
                              lista_de_arbitros[categorias_arbitros[2]] + 
                              lista_de_arbitros[categorias_arbitros[3]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))      
            
            #Partidos de categoria nacional femenino A2
            elif ca == categorias_federados[3]:

                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          lista_de_arbitros[categorias_arbitros[3]] + 
                          PA4):

                    for b in (lista_de_arbitros[categorias_arbitros[0]] + 
                              lista_de_arbitros[categorias_arbitros[1]] + 
                              lista_de_arbitros[categorias_arbitros[2]] + 
                              lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))  
            
            #Partidos de categoria Junior Aragon Masculino/Femenino 1ª
            elif ca in (categorias_federados[11], 
                        categorias_federados[12],
                        categorias_federados[18],
                        categorias_federados[19]):

                for a in lista_de_arbitros[categorias_arbitros[0]]:

                    for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):

                        TA[p].append((a,b))  

                for a in lista_de_arbitros[categorias_arbitros[1]]:

                    for b in (lista_de_arbitros[categorias_arbitros[2]] +
                              lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):

                        TA[p].append((a,b))          

                for a in lista_de_arbitros[categorias_arbitros[2]]:

                    for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):

                        TA[p].append((a,b))          


                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]]):

                    for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):
                        
                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))                                              

            #Partidos de categoria 2ª Aragonesa Masculina
            elif ca == categorias_federados[4]:

                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]]):

                    for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):

                        TA[p].append((a,b))  
                
                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]]):
                    
                    for b in (lista_de_arbitros[categorias_arbitros[3]] + 
                              lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]]):
                        
                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
            
            #Partidos de categoria 3ª Aragonesa masculina
            elif ca == categorias_federados[6]:
                for a in (lista_de_arbitros[categorias_arbitros[0]]):

                    for b in (lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]]):

                        TA[p].append((a,b))

                for a in (lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]]):

                    for b in (lista_de_arbitros[categorias_arbitros[4]] +
                              lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]]):

                        TA[p].append((a,b))    

                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]]):  
                    
                    for b in (lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
                
                for a in PP1:
                    for b in lista_de_arbitros[categorias_arbitros[5]]:
                        if a!=b:
                            if b in PP1:
                                if arbitros.index(a) < arbitros.index(b):
                                    TA[p].append((a,b))
                            else:
                                TA[p].append((a,b))
            
            #Junior Masculino 2ª
            elif ca == categorias_federados[13]:

                for a in (lista_de_arbitros[categorias_arbitros[0]]):

                    for b in (lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]] +
                              lista_de_arbitros[categorias_arbitros[7]]):

                        TA[p].append((a,b))

                for a in (lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]]):

                    for b in (lista_de_arbitros[categorias_arbitros[4]] +
                              lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]] +
                              lista_de_arbitros[categorias_arbitros[7]]):

                        TA[p].append((a,b))    

                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]]):  
                    
                    for b in (lista_de_arbitros[categorias_arbitros[4]] + 
                              lista_de_arbitros[categorias_arbitros[5]] +
                              lista_de_arbitros[categorias_arbitros[6]]):

                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
                
                for a in PP1:
                    for b in lista_de_arbitros[categorias_arbitros[5]]:
                        if a!=b:
                            if b in PP1:
                                if arbitros.index(a) < arbitros.index(b):
                                    TA[p].append((a,b))
                            else:
                                TA[p].append((a,b))
            
            #Partidos de categoria 2ª aragonesa femenina
            elif ca == categorias_federados[5]:

                for a in (lista_de_arbitros[categorias_arbitros[0]]):

                    for b in (lista_de_arbitros[categorias_arbitros[6]] + 
                              lista_de_arbitros[categorias_arbitros[7]]):

                        TA[p].append((a,b))   

                for a in (lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]]):

                    for b in (lista_de_arbitros[categorias_arbitros[5]] + 
                              lista_de_arbitros[categorias_arbitros[6]] + 
                              lista_de_arbitros[categorias_arbitros[7]]):
                        TA[p].append((a,b)) 

                for a in (lista_de_arbitros[categorias_arbitros[5]]):

                    for b in (lista_de_arbitros[categorias_arbitros[5]] + 
                              lista_de_arbitros[categorias_arbitros[6]]):
                        
                        if arbitros.index(a) < arbitros.index(b):
                            TA[p].append((a,b))
            
            #Partidos de categoria Social Oro
            elif ca in (categorias_federados[8],
                        categorias_federados[17]):

                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          lista_de_arbitros[categorias_arbitros[3]] +
                          PA4):
                    TA[p].append((a,''))

            #Partidos de categoria Social Plata
            elif ca == categorias_federados[9]:
                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          PP1):
                    TA[p].append((a,''))
            
            #Partidos de categoria Social Bronce
            elif ca == categorias_federados[10]:
                for a in (lista_de_arbitros[categorias_arbitros[0]] + 
                          lista_de_arbitros[categorias_arbitros[1]] + 
                          lista_de_arbitros[categorias_arbitros[2]] + 
                          lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]]):
                    TA[p].append((a,''))
            
            #Partidos de 3ª Aragonesa femenina y Junior Femenino 2ª
            elif ca in (categorias_federados[7],
                        categorias_federados[14]):

                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]] + 
                          lista_de_arbitros[categorias_arbitros[6]]):
                    TA[p].append((a, ''))
            
            #Partidos de categoria Junior femenino 3ª y Junior Masculino 3ª
            elif ca in (categorias_federados[16],
                        categorias_federados[15]):

                for a in (lista_de_arbitros[categorias_arbitros[3]] + 
                          lista_de_arbitros[categorias_arbitros[4]] + 
                          lista_de_arbitros[categorias_arbitros[5]] + 
                          lista_de_arbitros[categorias_arbitros[6]] + 
                          lista_de_arbitros[categorias_arbitros[7]]):
                    TA[p].append((a,''))
            
            else:
                TA[p].append(('',''))
    
    return TA

#Funcion que crea las cuaternas de arbitros para anotar cada partido
def cuaterna_oficiales(P, partidos, lista_de_oficiales, oficiales, OP, AD_FEB, Cronos, F3):

    '''
    Esta función crea las posibles cuaternas de oficiales de mesa para anotar cada partido.

    Los parámetros de la función son los siguientes:

        - P: lista de los partidos para desginar árbitros.

        - partidos: DataFrame que contiene todos los aprtidos a los cuales hay que asignar arbitros y oficiales de mesa.

        - lista_de_oficiales: Diccionario que contiene que oficiales de mesa pertenecen a cada categoria de oficiales.

        - OP: Diccionario que contiene para cada partido, que oficiales de mesa pueden realizarlo

        - AD_FEB: Lista de oficiales de mesa que pueden realizar la función de Acta Digital en los partidos de categoria Liga Femenina

        - Cronos: Lista de oficiales de mesa de categoria Provincial 2, que pueden realizar funciones de cronometrador.

        - F3: Lista de oficiales de mesa de categoria PROVINCIAL 2, que pueden realizar partidos de las categorías 3ª Aragonesa Femenina y Junior Aragón Femenino 2ª

    '''

    TO = {} #Conjunto de cuaternas de oficiales de mesa que pueden arbitrar el partido p
    for p in P:
        if ((partidos.loc[p, 'Categoria'] == '1ª NACIONAL MASCULINA A1') 
             and (partidos.loc[p, 'CAMPO'] == 'PEÑAS CENTER')):
            TO[p] = []
            TO[p].append(('','','',''))

        elif ((partidos.loc[p, 'Categoria'] == '1ª NACIONAL FEMENINA A1') 
             and (partidos.loc[p, 'CAMPO'] == 'PAB. EL PARQUE')):
            TO[p] = []
            TO[p].append(('','','',''))
        
        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'PAB. ALCAÑIZ')):
            TO[p] = []
            for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                        lista_de_oficiales[categorias_oficiales[1]] +
                        lista_de_oficiales[categorias_oficiales[2]] + 
                        lista_de_oficiales[categorias_oficiales[3]] +
                        lista_de_oficiales[categorias_oficiales[4]] + 
                        Cronos):

                if a in OP[p]:

                    for b in (lista_de_oficiales[categorias_oficiales[5]] + 
                                lista_de_oficiales[categorias_oficiales[6]]):

                        if b in OP[p]:
                        
                            if a!=b:
                                TO[p].append((b,a,'', ''))

        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. ANDORRA')):
            TO[p] = []
            for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                        lista_de_oficiales[categorias_oficiales[1]] +
                        lista_de_oficiales[categorias_oficiales[2]] + 
                        lista_de_oficiales[categorias_oficiales[3]] +
                        lista_de_oficiales[categorias_oficiales[4]] + 
                        Cronos):

                if a in OP[p]:

                    for b in (lista_de_oficiales[categorias_oficiales[5]] + 
                                lista_de_oficiales[categorias_oficiales[6]]):

                        if b in OP[p]:
                        
                            if a!=b:
                                TO[p].append((b,a,'', ''))  

        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. LA ALMUNIA')):
            TO[p] = []
            for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                        lista_de_oficiales[categorias_oficiales[1]] +
                        lista_de_oficiales[categorias_oficiales[2]] + 
                        lista_de_oficiales[categorias_oficiales[3]] +
                        lista_de_oficiales[categorias_oficiales[4]] + 
                        Cronos):

                if a in OP[p]:

                    for b in (lista_de_oficiales[categorias_oficiales[5]] + 
                                lista_de_oficiales[categorias_oficiales[6]]):

                        if b in OP[p]:
                        
                            if a!=b:
                                TO[p].append((b,a,'', ''))

        else:
            TO[p] = []
            ca = partidos.Categoria[p]
            
            #Partidos de categoria 1ª Nacional Masculino A1 y 1ª Nacional Femenino A1 
            if ca in (categorias_federados[0],
                      categorias_federados[1]):

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          ['SANCHEZ' , 'ANGOS']):   
                    
                    if a in OP[p]:
                    
                        for b in (lista_de_oficiales[categorias_oficiales[0]] + 
                                  lista_de_oficiales[categorias_oficiales[1]] +
                                  lista_de_oficiales[categorias_oficiales[2]] + 
                                  ['SANCHEZ' , 'ANGOS']):

                            if b in OP[p]:
                            
                                for c in (lista_de_oficiales[categorias_oficiales[0]] + 
                                          lista_de_oficiales[categorias_oficiales[1]] +
                                          lista_de_oficiales[categorias_oficiales[2]] + 
                                          ['SANCHEZ' , 'ANGOS']):

                                    if c in OP[p]:

                                        if a!=b:
                                            if a!=c:
                                                if b!=c:
                                                    TO[p].append((a,b,c,''))
                        
            
            #Partidos de categoria 1ª Nacional Masculino A2 y 1ª Nacional Femenino A2
            elif ca in (categorias_federados[2],
                        categorias_federados[3]):

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]]):   

                    if a in OP[p]:
                    
                        for b in (lista_de_oficiales[categorias_oficiales[0]] + 
                                  lista_de_oficiales[categorias_oficiales[1]] +
                                  lista_de_oficiales[categorias_oficiales[2]] + 
                                  lista_de_oficiales[categorias_oficiales[3]]):

                            if b in OP[p]:
                            
                                for c in (lista_de_oficiales[categorias_oficiales[0]] + 
                                          lista_de_oficiales[categorias_oficiales[1]] +
                                          lista_de_oficiales[categorias_oficiales[2]] + 
                                          lista_de_oficiales[categorias_oficiales[3]]):

                                    if c in OP[p]:

                                        if a!=b:
                                            if a!=c:
                                                if b!=c:
                                                    TO[p].append((a,b,c,''))
            
            #Partidos de categoria 2ªAragonesa Masculina, 2ª Aragonesa Femenina
            #3ªAragonesa Masculina, Junior Aragón Masculino 1ª
            #Junior Aragón Femenino 1ª, Junior Aragón Masculino 2ª
            elif ca in (categorias_federados[4],
                        categorias_federados[5],
                        categorias_federados[6],
                        categorias_federados[11],
                        categorias_federados[12],
                        categorias_federados[13],
                        categorias_federados[18],
                        categorias_federados[19]):

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]] +
                          lista_de_oficiales[categorias_oficiales[4]] + 
                          Cronos):

                    if a in OP[p]:

                        for b in (lista_de_oficiales[categorias_oficiales[3]] +
                                  lista_de_oficiales[categorias_oficiales[4]] +
                                  lista_de_oficiales[categorias_oficiales[5]] + 
                                  lista_de_oficiales[categorias_oficiales[6]]):

                            if b in OP[p]:
                            
                                if a!=b:
                                    
                                    if oficiales.index(a) < oficiales.index(b):
                                        TO[p].append((b,a,'', ''))
            
            #Partidos de categoria Social Masculino Oro y Social Masculina Plata
            elif ca in (categorias_federados[8],
                        categorias_federados[9],
                        categorias_federados[17]):

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]]):

                    if a in OP[p]:

                        TO[p].append((a, '', '', ''))

            #Partidos de categoria Social Masculino Bronce    
            elif ca == categorias_federados[10]:

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]] +
                          lista_de_oficiales[categorias_oficiales[4]] + 
                          Cronos):

                    if a in OP[p]:

                        TO[p].append((a, '', '', ''))
            
            #Partidos de categoria 3ªAragonesa femenina y Junior Aragon Femenino 2ª
            elif ca in (categorias_federados[7],
                        categorias_federados[14]):

                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]] +
                          lista_de_oficiales[categorias_oficiales[4]] + 
                          F3):

                    if a in OP[p]:

                        TO[p].append((a, '', '', ''))

            #Partidos de categoria Junior Aragon Femenino 3ª y Junior Aragon Masculino 3ª
            elif ca in (categorias_federados[15],
                        categorias_federados[16]):
                
                for a in (lista_de_oficiales[categorias_oficiales[0]] + 
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          lista_de_oficiales[categorias_oficiales[3]] +
                          lista_de_oficiales[categorias_oficiales[4]] + 
                          lista_de_oficiales[categorias_oficiales[5]]):

                    if a in OP[p]:
                    
                        TO[p].append((a,'','',''))

            #Partidos de categoria ACB
            elif ca == categorias_feb[0]:
                for a in lista_de_oficiales[categorias_oficiales[0]]:
                    if a in OP[p]:
                        for b in lista_de_oficiales[categorias_oficiales[0]]:
                            if b in OP[p]:
                                if a!=b:
                                    TO[p].append(('', a,b,''))
                    
            #Partidos de categoria liga femenina
            elif ca == categorias_feb[2]:
                for a in AD_FEB:
                    if a in OP[p]:
                        for b in lista_de_oficiales[categorias_oficiales[1]]:
                            if b in OP[p]:
                                for c in lista_de_oficiales[categorias_oficiales[1]]:
                                    if c in OP[p]:
                                        for d in lista_de_oficiales[categorias_oficiales[1]]:
                                            if d in OP[p]:
                                                if a!=b:
                                                    if a!=c:
                                                        if a!=d:
                                                            if b!=c:
                                                                if b!=d:
                                                                    if c!=d:
                                                                        TO[p].append((a,b,c,d))
        
            #Partidos de categoria leb plata, liga femenina 2, liga eba y silla de ruedas
            elif ca in (categorias_feb[1],
                        categorias_feb[3],
                        categorias_feb[4]):
                
                for a in (lista_de_oficiales[categorias_oficiales[0]] +
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]]) :

                    if a in OP[p]:

                        for b in(lista_de_oficiales[categorias_oficiales[0]] +
                                 lista_de_oficiales[categorias_oficiales[1]] +
                                 lista_de_oficiales[categorias_oficiales[2]]):

                            if b in OP[p]:

                                for c in (lista_de_oficiales[categorias_oficiales[0]] +
                                          lista_de_oficiales[categorias_oficiales[1]] +
                                          lista_de_oficiales[categorias_oficiales[2]]) :

                                    if c in OP[p]:

                                        for d in (lista_de_oficiales[categorias_oficiales[0]] +
                                                  lista_de_oficiales[categorias_oficiales[1]] +
                                                  lista_de_oficiales[categorias_oficiales[2]]):

                                            if d in OP[p]:

                                                if a!=b:
                                                    if a!=c:
                                                        if a!=d:
                                                            if b!=c:
                                                                if b!=d:
                                                                    if c!=d:
                                                                        TO[p].append((a,b,c,d))

            
            elif ca == categorias_feb[5]:
                for a in (lista_de_oficiales[categorias_oficiales[0]] +
                          lista_de_oficiales[categorias_oficiales[1]] +
                          lista_de_oficiales[categorias_oficiales[2]] + 
                          ['MAUREL', 'LAPORTA']) :

                    if a in OP[p]:

                        for b in(lista_de_oficiales[categorias_oficiales[0]] +
                                 lista_de_oficiales[categorias_oficiales[1]] +
                                 lista_de_oficiales[categorias_oficiales[2]] + 
                                 ['MAUREL', 'LAPORTA']):

                            if b in OP[p]:

                                for c in (lista_de_oficiales[categorias_oficiales[0]] +
                                          lista_de_oficiales[categorias_oficiales[1]] +
                                          lista_de_oficiales[categorias_oficiales[2]] + 
                                          ['MAUREL', 'LAPORTA']) :

                                    if c in OP[p]:

                                        for d in (lista_de_oficiales[categorias_oficiales[0]] +
                                                lista_de_oficiales[categorias_oficiales[1]] +
                                                lista_de_oficiales[categorias_oficiales[2]] + 
                                                ['MAUREL', 'LAPORTA']):

                                            if d in OP[p]:

                                                if a!=b:
                                                    if a!=c:
                                                        if a!=d:
                                                            if b!=c:
                                                                if b!=d:
                                                                    if c!=d:
                                                                        TO[p].append((a,b,c,d))
            
            else:
                TO[p].append(('','','',''))

    return TO

#Función que crea el conjunto de arbitros que pueden arbitrar cada partido
def arbitros_partidos(PST, PDM, PDT, partidos, lista_de_arbitros, PA4, PP1, disponibilidad):

    '''
    Esta función crea el conjunto de árbitros que pueden arbitrar cada partido.

    Los parámetros de la función son los siguientes:

        - PST: Conjunto de partidos que se juegan el sábado por la tarde.

        - PDM: Conjunto de partidos que se juegan el domingo por la mañana.

        - PDT: Conjunto de partidos que se juegan el domingo por la tarde.

        - partidos: DataFrame que contiene todos los aprtidos a los cuales hay que asignar arbitros y oficiales de mesa.

        - lista_de_arbitros: Diccionario que contiene que árbitros pertenecen a cada categoria de árbitros.

        - PA4: Lista de árbitros principales de categoria A4.

        - PP1: Lista de árbitros principales de categoria Provincial 1.

        - disponibilidad: DataFrame que contiene si cada árbitro y oficiales de mesa puede realizar partidos en cada franja.

    '''
    AP = {}
    for p in PST+PDM+PDT:
        if ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
             and (partidos.loc[p, 'CAMPO'] == 'PAB. ALCAÑIZ')):
            AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                     lista_de_arbitros[categorias_arbitros[1]] + 
                     lista_de_arbitros[categorias_arbitros[2]] + 
                     lista_de_arbitros[categorias_arbitros[3]] + 
                     lista_de_arbitros[categorias_arbitros[4]] + 
                     lista_de_arbitros[categorias_arbitros[5]])

            borrar = []
            for a in AP[p]:
                if p in PST:
                    if disponibilidad.loc[a, 'ST-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'ST-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'ST-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'ST-Final']:
                            borrar.append(a)

                elif p in PDM:
                    if disponibilidad.loc[a, 'DM-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DM-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DM-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DM-Final']:
                            borrar.append(a)    

                elif p in PDT:
                    if disponibilidad.loc[a, 'DT-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DT-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DT-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DT-Final']:
                            borrar.append(a)                                           
            
            for b in borrar:
                AP[p].remove(b)

        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. ANDORRA')):
            AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                     lista_de_arbitros[categorias_arbitros[1]] + 
                     lista_de_arbitros[categorias_arbitros[2]] + 
                     lista_de_arbitros[categorias_arbitros[3]] + 
                     lista_de_arbitros[categorias_arbitros[4]] + 
                     lista_de_arbitros[categorias_arbitros[5]])
            
            borrar = []
            for a in AP[p]:
                if p in PST:
                    if disponibilidad.loc[a, 'ST-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'ST-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'ST-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'ST-Final']:
                            borrar.append(a)

                elif p in PDM:
                    if disponibilidad.loc[a, 'DM-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DM-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DM-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DM-Final']:
                            borrar.append(a)    

                elif p in PDT:
                    if disponibilidad.loc[a, 'DT-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DT-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DT-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DT-Final']:
                            borrar.append(a)                                           
            
            for b in borrar:
                AP[p].remove(b)
        
        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. LA ALMUNIA')):
            AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                     lista_de_arbitros[categorias_arbitros[1]] + 
                     lista_de_arbitros[categorias_arbitros[2]] + 
                     lista_de_arbitros[categorias_arbitros[3]] + 
                     lista_de_arbitros[categorias_arbitros[4]] + 
                     lista_de_arbitros[categorias_arbitros[5]])
            
            borrar = []
            for a in AP[p]:
                if p in PST:
                    if disponibilidad.loc[a, 'ST-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'ST-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'ST-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'ST-Final']:
                            borrar.append(a)

                elif p in PDM:
                    if disponibilidad.loc[a, 'DM-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DM-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DM-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DM-Final']:
                            borrar.append(a)    

                elif p in PDT:
                    if disponibilidad.loc[a, 'DT-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DT-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DT-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DT-Final']:
                            borrar.append(a)                                           
            
            for b in borrar:
                AP[p].remove(b)
        
        else:
            #Partidos de categoria nacional masculina A1
            if partidos.Categoria[p] == categorias_federados[0]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]])
            
            #Partidos de categoria nacional femenina A1
            elif partidos.Categoria[p] == categorias_federados[1]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]])
                
            #Partidos de categoria nacional masculina A2
            elif partidos.Categoria[p] == categorias_federados[2]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]])
            
            #Partidos de categoria nacional femenina A2
            elif partidos.Categoria[p] == categorias_federados[3]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]])
            
            #Partidos de categoria Junior Aragon Femenino 1ª, Junior Aragon Masculino 1ª
            #Partidos de categoria Segunda Aragonesa Masculina
            elif partidos.Categoria[p] in (categorias_federados[4],
                                           categorias_federados[11], 
                                           categorias_federados[12],
                                           categorias_federados[18],
                                           categorias_federados[19]):
                
                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]] +
                         lista_de_arbitros[categorias_arbitros[5]])
            
            #Partidos de categoria 3ª Aragonesa Masculina
            elif partidos.Categoria[p] == categorias_federados[6]:
                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]] +
                         lista_de_arbitros[categorias_arbitros[5]] + 
                         lista_de_arbitros[categorias_arbitros[6]])

            #Partidos de categoria Junior Masculino 2ª
            #Partidos de categoria 2ª Aragonesa Femenina
            elif partidos.Categoria[p] in (categorias_federados[5],
                                           categorias_federados[13]):
                
                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] + 
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]] +
                         lista_de_arbitros[categorias_arbitros[5]] + 
                         lista_de_arbitros[categorias_arbitros[6]] +
                         lista_de_arbitros[categorias_arbitros[7]])
            
            #Partidos de categoria Social Oro
            elif partidos.Categoria[p] in (categorias_federados[8], 
                                           categorias_federados[17]):
                
                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] +
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] +
                         PA4)

            #Partidos de categoria Social Plata 
            elif partidos.Categoria[p] == categorias_federados[9]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] +
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] +
                         lista_de_arbitros[categorias_arbitros[4]] +
                         PP1)

            # Partidos de categoria Social Bronce
            elif partidos.Categoria[p] == categorias_federados[10]:

                AP[p] = (lista_de_arbitros[categorias_arbitros[0]] +
                         lista_de_arbitros[categorias_arbitros[1]] + 
                         lista_de_arbitros[categorias_arbitros[2]] + 
                         lista_de_arbitros[categorias_arbitros[3]] +
                         lista_de_arbitros[categorias_arbitros[4]] +
                         lista_de_arbitros[categorias_arbitros[5]])
            
            #Partidos de categoria 3ªAragonesa Femenina
            #Partidos de categoria Junior Femenino 2ª
            elif partidos.Categoria[p] in (categorias_federados[7],
                                           categorias_federados[14]):

                AP[p] = (lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]] + 
                         lista_de_arbitros[categorias_arbitros[5]] +
                         lista_de_arbitros[categorias_arbitros[6]])

            #Partidos de categoria Junior Masculino 3ª
            #Partidos de categoria Junior Femenino 3ª
            elif partidos.Categoria[p] in (categorias_federados[15],
                                           categorias_federados[16]):

                AP[p] = (lista_de_arbitros[categorias_arbitros[3]] + 
                         lista_de_arbitros[categorias_arbitros[4]] + 
                         lista_de_arbitros[categorias_arbitros[5]] + 
                         lista_de_arbitros[categorias_arbitros[6]] +
                         lista_de_arbitros[categorias_arbitros[7]])
                
            else:
                AP[p] = []


            borrar = []
            for a in AP[p]:
                if p in PST:
                    if disponibilidad.loc[a, 'ST-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'ST-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'ST-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'ST-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'ST-Final']:
                            borrar.append(a)

                elif p in PDM:
                    if disponibilidad.loc[a, 'DM-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DM-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DM-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DM-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DM-Final']:
                            borrar.append(a)    

                elif p in PDT:
                    if disponibilidad.loc[a, 'DT-Inicio'] == 1:
                        borrar.append(a)

                    elif disponibilidad.loc[a, 'DT-Inicio'] != 0:
                        if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[a, 'DT-Inicio']:
                            borrar.append(a)
                    
                    elif disponibilidad.loc[a, 'DT-Final'] != 0:
                        if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[a, 'DT-Final']:
                            borrar.append(a)                                           
            
            for b in borrar:
                AP[p].remove(b)

    return AP

#Función que crea el conjunto de oficiales de mesa que pueden arbitrar cada partido
def oficiales_partidos(PST, PDM, PDT, partidos, lista_de_oficiales, Cronos, F3, disponibilidad):

    '''
    Esta función crea el conjunto de oficiales de mesa que pueden arbitrar cada partido.

    Los parámetros de la función son los siguientes:

        - PST: Conjunto de partidos que se juegan el sábado por la tarde.

        - PDM: Conjunto de partidos que se juegan el domingo por la mañana.

        - PDT: Conjunto de partidos que se juegan el domingo por la tarde

        - partidos: DataFrame que contiene todos los aprtidos a los cuales hay que asignar arbitros y oficiales de mesa.

        - lista_de_oficiales: Diccionario que contiene que oficiales de mesa pertenecen a cada categoria de oficiales.

        - Cronos: Conjunto de oficiales de mesa de categoría PROVINCIAL 2 que pueden realizar funciones de cronometrador.

        - F3: Conjunto de oficiales de mesa de categoría PROVINCIAL 2 que pueden realizar partidos de categoria 3ª Aragonesa Femenina y Junior Aragón Femenino 2ª

        - disponibilidad: DataFrame que contiene si cada árbitro y oficiales de mesa puede realizar partidos en cada franja.
    '''

    OP = {} 
    for p in PST+PDM+PDT:
        #Partidos de categoria 1ª Nacional Masculino A1y 1ª Nacional Femenino A1
        if partidos.Categoria[p] in (categorias_federados[0], 
                                     categorias_federados[1]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] + 
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     ['ANGOS' , 'SANCHEZ']).copy()

        #Partidos de categoria 1ª Nacional Masculino A2 y 1ª Nacional Femenino A2
        elif partidos.Categoria[p] in (categorias_federados[2],
                                       categorias_federados[3]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] + 
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]]).copy()
        
        #Partidos de categoria Social Oro y Social Plata
        elif partidos.Categoria[p] in (categorias_federados[8], 
                                       categorias_federados[9],
                                       categorias_federados[17]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] + 
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]]).copy()

        #Partidos de categoria Social Bronce
        elif partidos.Categoria[p] == categorias_federados[10]:

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] + 
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]] +
                     lista_de_oficiales[categorias_oficiales[4]] +
                     Cronos).copy()
        
        #Partidos de categoria 2ªAragonesa Masculina, 2ªAragonesa Femenina, Junior Aragon Masculino 2ª
        #3ªAragonesa Masculina, Junior Aragon Masculino 1ª y Junior Aragon Femenino 1ª
        elif partidos.Categoria[p] in (categorias_federados[4], 
                                       categorias_federados[5],
                                       categorias_federados[6],
                                       categorias_federados[11],
                                       categorias_federados[12],
                                       categorias_federados[13],
                                       categorias_federados[18],
                                       categorias_federados[19]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] +
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]] + 
                     lista_de_oficiales[categorias_oficiales[4]] + 
                     lista_de_oficiales[categorias_oficiales[5]] +
                     lista_de_oficiales[categorias_oficiales[6]]).copy()

        #Partidos de categoria 3ª Aragonesa Femenina y Junior Aragon Femenino 2ª
        elif partidos.Categoria[p] in (categorias_federados[7], 
                                       categorias_federados[14]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] +
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]] + 
                     lista_de_oficiales[categorias_oficiales[4]] + 
                     F3).copy()
        
        #Partidos de categoria Junior Aragon Masculino 3ª y Junior Aragon Femenino 3ª
        elif partidos.Categoria[p] in (categorias_federados[15], 
                                       categorias_federados[16]):

            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] + 
                     lista_de_oficiales[categorias_oficiales[1]] +
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     lista_de_oficiales[categorias_oficiales[3]] + 
                     lista_de_oficiales[categorias_oficiales[4]] + 
                     lista_de_oficiales[categorias_oficiales[5]]).copy()
        
        #Partidos de categoria ACB
        elif partidos.Categoria[p] == categorias_feb[0]:
            OP[p] = lista_de_oficiales[categorias_oficiales[0]].copy()
        
        #Partidos de categoria LF
        elif partidos.Categoria[p] == categorias_feb[2]:
            OP[p] = lista_de_oficiales[categorias_oficiales[1]].copy()
        
        #Partidos de categorias LF2 y EBA
        elif partidos.Categoria[p] in (categorias_feb[3],
                                       categorias_feb[4]):
            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] +
                     lista_de_oficiales[categorias_oficiales[1]] +
                     lista_de_oficiales[categorias_oficiales[2]]).copy()
        
        elif partidos.Categoria[p] == categorias_feb[5]:
            OP[p] = (lista_de_oficiales[categorias_oficiales[0]] +
                     lista_de_oficiales[categorias_oficiales[1]] +
                     lista_de_oficiales[categorias_oficiales[2]] + 
                     ['MAUREL', 'LAPORTA']).copy()
            
        else:
            OP[p] = []

        #Aplicamos la disponibilidad de los oficiales de mesa, para que no aparezcan como disponibles en partidos que no pueden realizar.
        borrar = []
        for o in OP[p]:
            if p in PST:
                if disponibilidad.loc[o, 'ST-Inicio'] == 1:
                    borrar.append(o)

                elif disponibilidad.loc[o, 'ST-Inicio'] != 0:
                    if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[o, 'ST-Inicio']:
                        borrar.append(o)
                
                elif disponibilidad.loc[o, 'ST-Final'] != 0:
                    if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[o, 'ST-Final']:
                        borrar.append(o)

            elif p in PDM:
                if disponibilidad.loc[o, 'DM-Inicio'] == 1:
                    borrar.append(o)

                elif disponibilidad.loc[o, 'DM-Inicio'] != 0:
                    if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[o, 'DM-Inicio']:
                        borrar.append(o)
                
                elif disponibilidad.loc[o, 'DM-Final'] != 0:
                    if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[o, 'DM-Final']:
                        borrar.append(o)    

            elif p in PDT:
                if disponibilidad.loc[o, 'DT-Inicio'] == 1:
                    borrar.append(o)

                elif disponibilidad.loc[o, 'DT-Inicio'] != 0:
                    if partidos.loc[p, 'HoraDeJuego'] < disponibilidad.loc[o, 'DT-Inicio']:
                        borrar.append(o)
                
                elif disponibilidad.loc[o, 'DT-Final'] != 0:
                    if (datetime.strptime(partidos.loc[p, 'HoraDeJuego'].strftime('%H:%M:%S'), '%H:%M:%S') + timedelta(minutes = 105)).time() > disponibilidad.loc[o, 'DT-Final']:
                        borrar.append(o)                                           
        
        for b in borrar:
            OP[p].remove(b)
    
    return OP

#Funcion que determina que equipos por categoría han sido arbitrados por cada árbitro, en los dos fin de semana anteriores
def partidos_semanas_anteriores(fecha_de_designacion,
                                partidos_por_categoria):

    '''
    Esta función determina que equipos de cada categoria ha arbitrado cada árbitros en los dos fin de semana anteriores al actual
    
    Los parámetros de la funcion son los siguientes:

        - fecha_de_designacion: Fecha en formato 'ddmmyyyy', del fin de semana (domingo) sobre el que se va a ejecutar el modelo.

        - partidos_por_categoria: Diccionario que contiene el nombre de todos los equipos que juegan partido el fin de semana por categoria del partido.
    '''

    with open(f'Partidos_Fin_De_Semana_Anteriores/Partidos_FinDeSemana_Anteriores_{fecha_de_designacion}.json', 'r', encoding = 'utf-8') as js:
        Partidos_FinDeSemana_Anterior_Sin_Validar = json.load(js)

    Partidos_FinDeSemana_Anterior = {}

    for f in Partidos_FinDeSemana_Anterior_Sin_Validar.keys():
        Partidos_FinDeSemana_Anterior[f] = {}
        for a in Partidos_FinDeSemana_Anterior_Sin_Validar[f].keys():
            Partidos_FinDeSemana_Anterior[f][a] = {}
            for c in Partidos_FinDeSemana_Anterior_Sin_Validar[f][a].keys():
                categoria_buena = sorted(partidos_por_categoria.keys(), key = lambda x: SQM(None,x,c).ratio(), reverse = True)
                Partidos_FinDeSemana_Anterior[f][a][categoria_buena[0]] = []
                for p in Partidos_FinDeSemana_Anterior_Sin_Validar[f][a][c]:
                    lista_de_opciones = partidos_por_categoria[categoria_buena[0]]
                    matches = sorted(lista_de_opciones, key=lambda x: SQM(None, x, p).ratio(), reverse=True)
                    if SQM(None, matches[0], p).ratio() >= 0.75:
                        Partidos_FinDeSemana_Anterior[f][a][categoria_buena[0]].append(matches[0])
                    else:
                        Partidos_FinDeSemana_Anterior[f][a][categoria_buena[0]].append(p)

    return Partidos_FinDeSemana_Anterior

#Función que determina el número de árbitros y oficiales de mesa que son necesarios por partido         
def numero_de_arbitros_oficiales_por_partido(P, partidos):

    '''Con esta función se crean dos DataFrame "na" y"no", para indicar en cada partido, el número de árbitros necesarios (na) 
       y el número de oficiales de mesa (no)'''

    na = pd.DataFrame(index = P)
    no = pd.DataFrame(index = P)

    for p in P:
        if ((partidos.loc[p, 'Categoria'] == '1ª NACIONAL MASCULINA A1') 
             and (partidos.loc[p, 'CAMPO'] == 'PEÑAS CENTER')):
            na.loc[p, 'Numero'] = 2
            no.loc[p, 'Numero'] = 0

        elif ((partidos.loc[p, 'Categoria'] == '1ª NACIONAL FEMENINA A1')
               and (partidos.loc[p, 'CAMPO'] == 'PAB. EL PARQUE')):
            na.loc[P, 'Numero'] = 2
            no.loc[p, 'Numero'] = 0
        
        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'PAB. ALCAÑIZ')):
            na.loc[p, 'Numero'] = 2
            no.loc[p, 'Numero'] = 2

        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. ANDORRA')):
            na.loc[p, 'Numero'] = 2
            no.loc[p, 'Numero'] = 2
        
        elif ((partidos.loc[p, 'Categoria'] == 'JUNIOR ARAGON MASCULINO 3ª') 
               and (partidos.loc[p, 'CAMPO'] == 'POL. LA ALMUNIA')):
            na.loc[p, 'Numero'] = 2
            no.loc[p, 'Numero'] = 2

        else:
            ca = partidos.loc[p, 'Categoria']

            if ca in (categorias_federados[0],
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
                na.loc[p, 'Numero'] = 2
            
            elif ca in (categorias_federados[7],
                        categorias_federados[8],
                        categorias_federados[9],
                        categorias_federados[10],
                        categorias_federados[14],
                        categorias_federados[15],
                        categorias_federados[16],
                        categorias_federados[17]):
                na.loc[p, 'Numero'] = 1
            
            else:
                na.loc[p, 'Numero'] = 0

            if ca in (categorias_federados[0],
                    categorias_federados[1],
                    categorias_federados[2], 
                    categorias_federados[3]):
                no.loc[p, 'Numero'] = 3

            elif ca in (categorias_federados[4],
                    categorias_federados[5],
                    categorias_federados[6],
                    categorias_federados[11],
                    categorias_federados[12],
                    categorias_federados[13],
                    categorias_federados[18],
                    categorias_federados[19],
                    categorias_feb[0]):
                no.loc[p, 'Numero'] = 2
            
            elif ca in (categorias_federados[7],
                        categorias_federados[8],
                        categorias_federados[9],
                        categorias_federados[10],
                        categorias_federados[14],
                        categorias_federados[15],
                        categorias_federados[16],
                        categorias_federados[17]):
                no.loc[p, 'Numero'] = 1

            elif ca in (categorias_feb[1],
                        categorias_feb[2],
                        categorias_feb[3],
                        categorias_feb[4],
                        categorias_feb[5]):
                no.loc[p, 'Numero'] = 4
            
            else:
                no.loc[p, 'Numero'] = 0

    return na, no
            
