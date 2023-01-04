import pandas as pd

from FAB_CONJUNTOS import categorias_feb, categorias_federados, categorias_escolares, campos_desplazamientos

## https://stackoverflow.com/questions/40950310/strip-trim-all-strings-of-a-dataframe
def trim_all_columns(df):
    """
    Trim whitespace from ends of each value across all series in dataframe
    """
    trim_strings = lambda x: x.strip() if isinstance(x, str) else x
    return df.applymap(trim_strings)

def lectura_partidos(fichero,name):
    '''
    Esta función crea el DataFrame que contiene todos los partidos a los cuales hay que asignar árbitros y oficiales de mesa.

    Los parámetros de entrada son el nombre del fichero, y la pestaña de la excel donde se encuentran los partidos del fin de semana correspondiente.
    '''

    campos_de_juego = pd.read_excel('Horarios Partidos/Partidos.xlsx', sheet_name= 'CAMPOS DE JUEGO').set_index('Campo').index
    partidos = pd.read_excel(fichero, sheet_name = name, engine = 'openpyxl')
    partidos.rename(columns = {'PISTA JUEGO': 'CAMPO'}, inplace = True)
    partidos = trim_all_columns(partidos)

    partidos_por_categoria = {}

    cat = ""
    for j in partidos.index:
        if pd.isna(partidos.loc[j, 'EQUIPO LOCAL']) == False:
            if partidos.loc[j, 'EQUIPO LOCAL'] in categorias_federados + categorias_feb:
                cat = partidos.loc[j, 'EQUIPO LOCAL']
                if cat in partidos_por_categoria.keys():
                    next
                else:
                    partidos_por_categoria[cat] = []
                    
            elif partidos.loc[j, 'EQUIPO LOCAL'] in categorias_escolares:
                cat = partidos.loc[j, 'EQUIPO LOCAL']
                break
                    
            elif (pd.isna(partidos.loc[j, 'EQUIPO LOCAL']) == False):
                partidos.loc[j, 'Categoria'] = cat
                partidos_por_categoria[cat].append(partidos.loc[j, 'EQUIPO LOCAL'])
                partidos_por_categoria[cat].append(partidos.loc[j, 'EQUIPO VISITANTE'])
                if partidos.loc[j, 'CAMPO'] in campos_desplazamientos:
                    partidos.loc[j, 'Coche'] = "Si"
                else:
                    partidos.loc[j, 'Coche'] = "No"
    
    partidos = partidos.dropna().reset_index().drop(columns = 'index')

    for i in range(len(partidos)):
        partidos.loc[i,'HoraDeJuego'] = partidos.loc[i,'HORA']
        partidos.loc[i,'HORA'] = partidos.loc[i,'HORA'].strftime("%H:%M:%S")
        partidos.loc[i,'DiaSem'] = partidos.FECHA[i].weekday()

        if partidos.loc[i,'DiaSem'] == 5:
            partidos.loc[i,'HORA'] = int(partidos.loc[i,'HORA'][0:2])*60 + int(partidos.loc[i,'HORA'][3:5]) + 1
        
        elif partidos.loc[i, 'DiaSem'] == 6: 
            partidos.loc[i,'HORA'] = 24*60 + int(partidos.loc[i,'HORA'][0:2])*60 + int(partidos.loc[i,'HORA'][3:5]) + 1

    partidos_no_validos = partidos[~partidos.CAMPO.isin(campos_de_juego)]
    partidos = partidos[partidos.CAMPO.isin(campos_de_juego)].reset_index().drop(columns = 'index')

    #Eliminar aquellos partidos que se juegan en el campo PEÑAS CENTER, que no son de categoria nacional masculino A1, ya que lo arbitran, los árbitros de huesca
    #Lo mismo ocurre con el pabellon El Parque de huesca, que juega el nacional femenino, y tenemos que arbitrarlo árbitros de Zaragoza, en contadas ocasiones,
    #por norma general NO.

    part = partidos[((partidos.CAMPO == 'PEÑAS CENTER') & (partidos.Categoria != categorias_federados[0])) |
                    (partidos.CAMPO == 'PAB. EL PARQUE') & (partidos.Categoria != categorias_federados[1])].index
    for pr in part:
        partidos.drop(pr, inplace = True)
    
    partidos = partidos.reset_index().drop(columns = 'index')
            
    partidos_validos = partidos[(partidos.DiaSem == 6) | (partidos.DiaSem == 5)].reset_index().drop(columns = 'index')

    partidos_validos = partidos_validos[['Categoria', 'EQUIPO LOCAL', 'EQUIPO VISITANTE', 'FECHA', 'HORA', 'CAMPO', 'Coche', 'HoraDeJuego','DiaSem']]
    partidos_no_validos = partidos_no_validos[['Categoria', 'EQUIPO LOCAL', 'EQUIPO VISITANTE', 'FECHA', 'HORA', 'CAMPO', 'Coche', 'HoraDeJuego','DiaSem']]
    
    
    return partidos_validos, partidos_por_categoria, partidos_no_validos