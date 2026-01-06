from qgis.core import QgsProject, QgsWkbTypes, QgsGeometryValidator
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
                doublons.append(['doublon_geometrique',
                                 layer_name,
                                 geom_dict[geom].id(),
                                 'geometry',
                                 'doublon avec {}'.format(f.id()),
                                 f.geometry().centroid()])
            else:
                geom_dict[geom]=f
    if doublons != []:
        controlpoint_layer = ControlPointLayer('doublon_geometrique')
        controlpoint_layer.add_features(doublons)


def valid_geometry(layers_names):
    """
    :param layers_names: array
    """
    geom_not_valid = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for f in layer.getFeatures():
            validator = QgsGeometryValidator(f.geometry())
            error = validator.validateGeometry(f.geometry())
            if error:
                #print(f.geometry().validateGeometry().where())
                geom_not_valid.append(['valid_geometry',
                                       layer_name,
                                       f.id(),
                                       'geometry',
                                       'geometrie invalide',
                                       f.geometry().centroid()])
    if geom_not_valid!=[]:
        controlpoint_layer = ControlPointLayer('valid_geometry')
        controlpoint_layer.add_features(geom_not_valid)


def micro_object(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: json
    """
    micro_object = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            continue
        taille_mini = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.wkbType() == QgsWkbTypes.Polygon or layer.wkbType() == QgsWkbTypes.MultiPolygon:
            for f in layer.getFeatures():
                if f.geometry().isGeosValid():
                    if f.geometry().area() < int(taille_mini):
                        micro_object.append(['micro_object',
                                               layer_name,
                                               f.id(),
                                               'geometry',
                                               'aire inferieure à {} m2'.format(taille_mini),
                                               f.geometry().centroid()])
        elif layer.wkbType() == QgsWkbTypes.LineString or layer.wkbType() == QgsWkbTypes.MultiLineString:
            for f in layer.getFeatures():
                if f.geometry().isGeosValid():
                    if f.geometry().length() < int(taille_mini):
                        micro_object.append(['micro_object',
                                               layer_name,
                                               f.id(),
                                               'geometry',
                                               'longueur inferieure à {} m'.format(taille_mini),
                                               f.geometry().centroid()])
    if micro_object != []:
        controlpoint_layer = ControlPointLayer('micro_object')
        controlpoint_layer.add_features(micro_object)


def troncon_isole(layers_names):
    """
    :param layers_names: array
    """
    isole = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        if layer.wkbType() == QgsWkbTypes.LineString or layer.wkbType() == QgsWkbTypes.MultiLineString:
            n = layer.featureCount()
            for i in range(n):
                trouve = False
                fi = layer.getFeature(i)
                geomi = fi.geometry()
                pointsi = [point for point in geomi.vertices()]
                for j in range(n):
                    if i!=j:
                        fj = layer.getFeature(j)
                        geomj = fj.geometry()
                        pointsj = [point for point in geomj.vertices()]
                        print(pointsi)
                        print(pointsj)
                        if pointsi[0] == pointsj[0] or pointsi[-1] == pointsj[-1] or \
                                pointsi[0] == pointsj[-1] or pointsi[-1] == pointsj[0]:
                            print('trouvé')
                            trouve = True
                            break
                if not trouve:
                    isole.append(['troncon_isole', layer_name, fi.id(), 'geometry', '', fi.geometry().centroid()])
    if isole != []:
        controlpoint_layer = ControlPointLayer('troncon_isole')
        controlpoint_layer.add_features(isole)







