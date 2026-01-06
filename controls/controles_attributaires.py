from qgis.core import QgsProject, NULL
from ..ControlPointLayer import ControlPointLayer
import json


def not_null_attribute(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: json
    """
    null_attributes_feature = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            raise Exception('{} not in param.json'.format(layer_name))
        param_layer = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for attribute in param_layer:
                if feature[attribute]==NULL:
                    null_attributes_feature.append(['not_null_attribute',
                                                    layer_name,
                                                    feature.id(),
                                                    attribute,
                                                    '',
                                                    feature.geometry().centroid()])
    if null_attributes_feature != []:
        controlpoint_layer = ControlPointLayer('not_null_attribute')
        controlpoint_layer.add_features(null_attributes_feature)
        controlpoint_layer.save()
    return len(null_attributes_feature)


def attribute_size(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: {'nom':'taille'}
    """
    attributes = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            raise Exception('{} not in param.json'.format(layer_name))
        param_layer = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, size in param_layer.items():
                if feature[att]==NULL:
                    continue
                if len(feature[att]) > int(size):
                    attributes.append(['attribute_size',
                                       layer_name,
                                       feature.id(),
                                       att,
                                       '{} : taille max {}'.format(feature[att], size),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attribute_size')
        controlpoint_layer.add_features(attributes)
        controlpoint_layer.save()
    return len(attributes)


def attribute_values(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: {'nom':[value1,value2,value3]}
    """
    attributes = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            raise Exception('{} not in param.json'.format(layer_name))
        param_layer = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, values in param_layer.items():
                if feature[att] == NULL:
                    continue
                if feature[att] not in values:
                    attributes.append(['attribute_values',
                                       layer_name,
                                       feature.id(),
                                       att,
                                       '{} : valeurs autorisées : {} '.format(feature[att], ','.join(values)),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attribute_values')
        controlpoint_layer.add_features(attributes)
        controlpoint_layer.save()
    return len(attributes)


def attribute_json_check(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: {'nom':'json_string'}
    """
    attributes = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            raise Exception('{} not in param.json'.format(layer_name))
        param_layer = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att in param_layer:
                if feature[att] == NULL:
                    continue
                try:
                    json_data = json.loads(feature[att])
                except json.JSONDecodeError as e:
                    attributes.append(['json_error',
                                       layer_name,
                                       feature.id(),
                                       att,
                                      'json invalide : {}'.format(feature[att]),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attribute_json_check')
        controlpoint_layer.add_features(attributes)
        controlpoint_layer.save()
    return len(attributes)


def attribute_type(layers_names, param_json):
    """
    :param layers_names: array
    :param param_json: {'nom':'type'}
    """
    attributes = []
    for layer_name in layers_names:
        if layer_name not in param_json.keys():
            continue
        param_layer = param_json[layer_name]
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        for feature in layer.getFeatures():
            for att, values in param_layer.items():
                if feature[att] == NULL:
                    continue
                if feature[att] not in values:
                    attributes.append(['attribute_type',
                                       layer_name,
                                       feature.id(),
                                       att,
                                       '{} : valeurs autorisées : {} '.format(feature[att], ','.join(values)),
                                       feature.geometry().centroid()])
    if attributes != []:
        controlpoint_layer = ControlPointLayer('attribute_type')
        controlpoint_layer.add_features(attributes)
        controlpoint_layer.save()
    return len(attributes)

