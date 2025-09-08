from qgis.core import QgsProject, QgsWkbTypes
from ..ControlPointLayer import ControlPointLayer

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


def valid_geometry(layers_names):
    """
    :param layers_names: array
    """
    geom_not_valid = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            if not f.geometry().isGeosValid():
                geom_not_valid.append(['valid_geometry',
                                       layer_name,
                                       f.id(),
                                       'geometry',
                                       'geometrie invalide',
                                       f.geometry().centroid()])
    if geom_not_valid!=[]:
        controlpoint_layer = ControlPointLayer('valid_geometry')
        controlpoint_layer.add_features(geom_not_valid)


def micro_polygon(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: json
    """
    micro_polygons = []
    for layer_name in layers_names:
        taille_mini = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.wkbType() == QgsWkbTypes.Polygon or layer.wkbType() == QgsWkbTypes.MultiPolygon:
            for f in layer.getFeatures():
                if f.geometry().isGeosValid():
                    if f.geometry().area() < int(taille_mini):
                        micro_polygons.append(['micro_polygon',
                                               layer_name,
                                               f.id(),
                                               'geometry',
                                               'aire inferieure à {} m2'.format(taille_mini),
                                               f.geometry().centroid()])
    if micro_polygons != []:
        controlpoint_layer = ControlPointLayer('micro_polygon')
        controlpoint_layer.add_features(micro_polygons)


def micro_linear(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: json
    """
    micro_linear = []
    for layer_name in layers_names:
        taille_mini = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.geometryType() == QgsWkbTypes.LineString or layer.geometryType() == QgsWkbTypes.MultiLineString:
            for f in layer.getFeatures():
                if f.geometry().isValid():
                    if f.geometry().length() < taille_mini:
                        micro_linear.append(['micro_polygon',
                                             layer_name,
                                             f.id(),
                                             'geometry',
                                             'longueur inferieure à {} m'.format(taille_mini),
                                             f.geometry().centroid()])
    if micro_linear != []:
        controlpoint_layer = ControlPointLayer('micro_linear')
        controlpoint_layer.add_features(micro_linear)





