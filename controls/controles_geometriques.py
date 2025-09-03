from qgis.core import QgsProject, QgsFeature, edit, QgsWkbTypes
from .. import control_manager

def doublon_geometrique(layers_names):
    """
    :param layers_names: array
    """
    doublons = []
    for layer_name in layers_names:
        geom_dict = {}
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            geom = f.geometry().asWkt()
            if geom in geom_dict.keys():
                doublons.append([layer_name, geom_dict[geom], f])
            else:
                geom_dict[geom]=f
    if doublons != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('doublon')
        for d in doublons:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(d[1].geometry().centroid())
                controlpoint.setAttributes(['doublon', d[0], d[1].id(), 'geometry', 'doublon avec {}'.format(d[2].id())])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


def valid_geometry(layers_names):
    """
    :param layers_names: array
    """
    geom_not_valid = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            if not f.geometry().isValid():
                geom_not_valid.append([layer_name, f])
    if geom_not_valid!=[]:
        controlpoint_layer = control_manager.create_controlpoint_layer('geom_valid')
        for g in geom_not_valid:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(g[1].geometry().centroid())
                controlpoint.setAttributes(['geom_valid', g[0], g[1].id(), 'geometry', 'geometrie invalide'])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


def micro_polygon(layers_names, taille_mini):
    """
    :param layers_names: array
    :param taille_mini: int en m2
    """
    micro_polygons = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.geometryType() == QgsWkbTypes.Polygon or layer.geometryType() == QgsWkbTypes.MultiPolygon:
            for f in layer.getFeatures():
                if f.geometry().isValid():
                    if f.geometry().area() < taille_mini:
                        micro_polygons.append([layer_name, f])
    if micro_polygons != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('micro_polygon')
        for m in micro_polygons:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(m[1].geometry().centroid())
                controlpoint.setAttributes(['micro_polygon', m[0], m[1].id(), 'geometry',
                                            'aire inferieure à {} m2'.format(taille_mini)])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


def micro_linear(layers_names, taille_mini):
    """
    :param layers_names: array
    :param taille_mini: float en m
    """
    micro_linear = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.geometryType() == QgsWkbTypes.LineString or layer.geometryType() == QgsWkbTypes.MultiLineString:
            for f in layer.getFeatures():
                if f.geometry().isValid():
                    if f.geometry().length() < taille_mini:
                        micro_linear.append([layer_name, f])
    if micro_linear != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('micro_polygon')
        for m in micro_linear:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(m[1].geometry().centroid())
                controlpoint.setAttributes(['micro_polygon', m[0], m[1].id(), 'geometry',
                                            'aire inferieure à {} m'.format(taille_mini)])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()





