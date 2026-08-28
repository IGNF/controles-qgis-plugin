from qgis.core import QgsProject
import os

def check_if_exists(control_layer_name):
    directory_path = os.path.dirname(QgsProject.instance().fileName())+'/'+control_layer_name+'.gpkg'
    if os.path.isfile(directory_path):
        return True
    else:
        return False