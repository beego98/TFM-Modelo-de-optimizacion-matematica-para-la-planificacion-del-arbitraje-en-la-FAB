import pandas as pd

from FAB_CONJUNTOS import categorias_arbitros, categorias_oficiales

'''
Funciones que leen las listas de árbitros y oficiales respectivamente
'''

def lista_oficiales(name):
    '''
    Esta función lee correctamente la excel proporcinada por el CAAB donde se encuentra el listado de oficiales de mesa por categoria, 
    indicando además si cada oficial de mesa dispone de coche, de moto, de ambas o de ninguna.
    
    El parámetro de entrada es la ruta donde se encuentra la excel a leer.
    '''

    oficiales = pd.read_excel(name)
    oficiales.columns = oficiales.iloc[0]
    oficiales = oficiales[1:].set_index('OFICIALES')

    oficiales_coche = []
    oficiales_moto = []
    oficiales_sin_transporte = []

    lista_de_oficiales = {}
    for ca in categorias_oficiales:
        lista_de_oficiales[ca] = []

    oficiales.COCHE = oficiales.COCHE.astype(str)
    oficiales.index = oficiales.index.astype(str)
    for o in oficiales.index:
        if o in categorias_oficiales:
            next
        else:
            if "+" in oficiales.COCHE[o]:
                oficiales_coche.append(o)
            elif "-" in oficiales.COCHE[o]:
                oficiales_moto.append(o)
            elif "#" in oficiales.COCHE[o]:
                oficiales_coche.append(o)
                oficiales_moto.append(o)
            else:
                oficiales_sin_transporte.append(o)
    
    anterior = categorias_oficiales[0]
    for i in range(len(oficiales)):
        if oficiales.index[i].upper() in categorias_oficiales:
            anterior = oficiales.index[i].upper()
            next
        else:
            lista_de_oficiales[anterior].append(oficiales.index[i])

    eliminar = ['I', 'II', 'OFICIALES', 'ARBITROS', 'nan']
    for c in categorias_oficiales:
        for e in eliminar:
            if e in lista_de_oficiales[c]:
                while e in lista_de_oficiales[c]:
                    lista_de_oficiales[c].remove(e)
    
    return oficiales_coche, oficiales_moto, lista_de_oficiales

def lista_arbitros(name):
    '''
    Esta función lee correctamente la excel proporcinada por el CAAB donde se encuentra el listado de arbitros por categoria, indicando además si cada árbitro
    dispone de coche, de moto, de ambas o de ninguna.
    
    El parámetro de entrada es la ruta donde se encuentra la excel a leer.
    '''
    arbitros = pd.read_excel(name)
    arbitros.columns = arbitros.iloc[0]
    arbitros = arbitros.iloc[1:,1:].set_index('ARBITROS')

    arbitros_coche = []
    arbitros_moto = []
    arbitros_sin_transporte = []

    lista_de_arbitros = {}
    for ca in categorias_arbitros:
        lista_de_arbitros[ca] = []

    arbitros.COCHE = arbitros.COCHE.astype(str)
    arbitros.index = arbitros.index.astype(str)
    for a in arbitros.index:
        if a in categorias_arbitros:
            next
        else:
            if "+" in arbitros.COCHE[a]:
                arbitros_coche.append(a)
            elif "-" in arbitros.COCHE[a]:
                arbitros_moto.append(a)
            elif "#" in arbitros.COCHE[a]:
                arbitros_coche.append(a)
                arbitros_moto.append(a)
            else:
                arbitros_sin_transporte.append(a)

    anterior = categorias_arbitros[0]
    for i in range(len(arbitros)):
        if arbitros.index[i].upper() in categorias_arbitros:
            anterior = arbitros.index[i].upper()
            next
        else:
            lista_de_arbitros[anterior].append(arbitros.index[i])
    
    eliminar = ['I', 'II', 'OFICIALES', 'ARBITROS', 'nan']
    for c in categorias_arbitros:
        for e in eliminar:
            if e in lista_de_arbitros[c]:
                while e in lista_de_arbitros[c]:
                    lista_de_arbitros[c].remove(e)
                    
        if 'MATEU' in lista_de_arbitros[c]:
            lista_de_arbitros[c].remove('MATEU')
    
    return arbitros_coche, arbitros_moto, lista_de_arbitros