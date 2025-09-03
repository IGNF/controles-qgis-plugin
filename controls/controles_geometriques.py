<<<<<<< HEAD
from qgis.core import QgsProject, QgsWkbTypes
from ..ControlPointLayer import ControlPointLayer
=======
from qgis.core import QgsProject, QgsFeature, edit, QgsWkbTypes
from .. import control_manager
>>>>>>> 2617f6507858cfcfd3249259777e3834be6300aa

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
<<<<<<< HEAD
                doublons.append(['doublon',
                                 layer_name,
                                 geom_dict[geom].id(),
                                 'geometry',
                                 'doublon avec {}'.format(f.id()),
                                 f.geometry().centroid()])
            else:
                geom_dict[geom]=f
    if doublons != []:
        controlpoint_layer = ControlPointLayer('doublon')
        controlpoint_layer.add_features(doublons)
=======
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
>>>>>>> 2617f6507858cfcfd3249259777e3834be6300aa


def valid_geometry(layers_names):
    """
    :param layers_names: array
    """
    geom_not_valid = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            if not f.geometry().isValid():
<<<<<<< HEAD
                geom_not_valid.append(['valid_geometry',
                                       layer_name,
                                       f.id(),
                                       'geometry',
                                       'geometrie invalide',
                                       f.geometry().centroid()])
    if geom_not_valid!=[]:
        controlpoint_layer = ControlPointLayer('valid_geometry')
        controlpoint_layer.add_features(geom_not_valid)
=======
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
>>>>>>> 2617f6507858cfcfd3249259777e3834be6300aa


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
<<<<<<< HEAD
                        micro_polygons.append(['micro_polygon',
                                               layer_name,
                                               f.id(),
                                               'geometry',
                                               'aire inferieure à {} m2'.format(taille_mini),
                                               f.geometry().centroid()])
    if micro_polygons != []:
        controlpoint_layer = ControlPointLayer('micro_polygon')
        controlpoint_layer.add_features(micro_polygons)
=======
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
>>>>>>> 2617f6507858cfcfd3249259777e3834be6300aa


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
<<<<<<< HEAD
                        micro_linear.append(['micro_polygon',
                                             layer_name,
                                             f.id(),
                                             'geometry',
                                             'longueur inferieure à {} m'.format(taille_mini),
                                             f.geometry().centroid()])
    if micro_linear != []:
        controlpoint_layer = ControlPointLayer('micro_linear')
        controlpoint_layer.add_features(micro_linear)
=======
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
>>>>>>> 2617f6507858cfcfd3249259777e3834be6300aa





