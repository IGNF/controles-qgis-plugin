from qgis.core import QgsProject, QgsFeature, edit
from .. import control_manager

def doublon(layers_names):
    print('doublon')
    doublons = []
    for layer_name in layers_names:
        geom_dict = {}
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            geom = f.geometry().asWkt()
            if geom in geom_dict.keys():
                print("doublons doublon")
                doublons.append([layer_name, geom_dict[geom], f])
            else:
                geom_dict[geom]=f
    if doublons != []:
        print('doublon trouvé')
        controlpoint_layer = control_manager.create_controlpoint_layer('doublon')
        for d in doublons:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(d[1].geometry().centroid())
                controlpoint.setAttributes(['doublon', d[0], d[1].id(), 'doublon avec {}'.format(d[2].id())])
                controlpoint.setAttributes(['doublon', d[0], d[1].id(), 'doublon avec {}'.format(d[2].id())])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()