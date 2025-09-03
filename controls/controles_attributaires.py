from qgis.core import QgsProject, QgsFeature, edit
from .. import control_manager
import json
from jsonschema import validate

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
                    null_attributes_feature.append(feature, attribute, layer_name)
    if null_attributes_feature != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('attributs_not_null')
        for f in null_attributes_feature:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(f[0].geometry().centroid())
                controlpoint.setAttributes(['attributs_not_null',f[2] , f[0].id(), f[1], None])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


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
                    attributes.append(feature, att, layer_name, size)
    if attributes != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('attributs_size')
        for f in attributes:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(f[0].geometry().centroid())
                controlpoint.setAttributes(['attributs_size', f[2], f[0].id(), f[1],
                                            'longueur requise : {}'.format(f[3])])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


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
                    attributes.append(feature, att, layer_name, values)
    if attributes != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('attributs_values')
        for f in attributes:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(f[0].geometry().centroid())
                controlpoint.setAttributes(['attributs_values', f[2], f[0].id(), f[1],
                                            'valeurs autorisées : '.format(','.join(f[3]))])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()


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
                    validate(instance=json_data, schema=schema)
                except Exception as e:
                    attributes.append(feature, att, layer_name, values)
    if attributes != []:
        controlpoint_layer = control_manager.create_controlpoint_layer('json_error')
        for f in attributes:
            with edit(controlpoint_layer):
                controlpoint = QgsFeature()
                controlpoint.setGeometry(f[0].geometry().centroid())
                controlpoint.setAttributes(['json_error', f[2], f[0].id(), f[1],
                                            'json invalide : '.format(f[3])])
                controlpoint_layer.dataProvider().addFeature(controlpoint)
                controlpoint_layer.updateExtents()