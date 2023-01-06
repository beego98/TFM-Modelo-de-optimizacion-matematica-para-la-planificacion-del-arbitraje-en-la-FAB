import pandas as pd

'''
Funcion para guardar los datos de un modelo de optimización de manera legible en un dataframe
'''

def save_data(model,name):
    '''
    model debe indicar el nombre de modelo de optimizacion
    name debe indicar el nombre de la variable del modelo de optimizacion
    '''

    entity = model.__getattribute__(name)
    if entity.dim() > 1:
        variable = pd.DataFrame( [v[0] + (v[1].value,) for v in entity.iteritems()] )
    
    else:
        variable = pd.DataFrame( (v[0] , v[1].value) for v in entity.iteritems() )

    return variable