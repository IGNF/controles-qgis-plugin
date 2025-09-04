from qgis.core import QgsProject
from ..ControlPointLayer import ControlPointLayer
import json


def not_null_attribute(layers_names, attributes_array):
    """
    :param layers_names: array
    :param attributes_array:
    """
    null_attributes_feature = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for attribute in attributes_array:
                if feature.isNull(feature.fieldNameIndex(attribute)):
                    null_attributes_feature.append(['attributs_not_null',
                                                    layer_name,
                                                    feature.id(),
                                                    attribute,
                                                    '',
                                                    feature.geometry().centroid()])
    if null_attributes_feature != []:
        controlpoint_layer = ControlPointLayer('attributs_not_null')
        controlpoint_layer.add_features(null_attributes_feature)


def attribute_size(layers_names, attributes_dict):
    """
    :param layers_names: array
    :param attributes_dict: {'nom':'taille'}
    """
    attributes = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, size in attributes_dict:
                if feature.fieldNameIndex(att).length() > size:
                    attributes.append(['attributs_size',
                                       layer_name,
                                       feature.id(),
                                       att,
                                       'longueur requise : {}'.format(size),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attributes_size')
        controlpoint_layer.add_features(attributes)


def attribute_values(layers_names, attributes_dict):
    """
    :param layers_names: array
    :param attributes_dict: {'nom':[value1,value2,value3]}
    :return:
    """
    attributes = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, values in attributes_dict:
                if feature.fieldNameIndex(att) not in values:
                    attributes.append(['attributs_values',
                                       layer_name,
                                       feature.id(),
                                       att,
                                       'valeurs autorisées : '.format(','.join(values)),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attributes_values')
        controlpoint_layer.add_features(attributes)


def attribute_json_check(layers_names, attributes_dict, schema):
    """
    :param layers_names: array
    :param attributes_dict: {'nom':'json_string'}
    :param schema: jsonschema
    :return:
    """
    attributes = []
    for layer_name in layers_names:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, values in attributes_dict:
                try:
                    json_data = json.loads(feature.fieldNameIndex(att))
                    for key, expected_type in schema.items():
                        if key not in json_data:
                            attributes.append([feature, att, layer_name, values])
                except json.JSONDecodeError as e:
                    attributes.append(['json_error',
                                       layer_name,
                                       feature.id(),
                                       att,
                                      'json invalide : '.format(values),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('json_check')
        controlpoint_layer.add_features(attributes)

