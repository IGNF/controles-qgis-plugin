from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsProject,
    NULL
)
from ControlPointLayer import ControlPointLayer
import json


class NotNullAttributeAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                'PARAM_JSON',
                'Paramètres JSON',
                extension='json'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        json_path = self.parameterAsFile(parameters, self.JSON_FILE, context)
        # param_json : {'couche': ['attribut1', 'attribut2', ...], ...}

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        null_attributes_feature = []
        for layer in layers:
            if layer.name() not in param_json.keys():
                feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
                continue
            for feature in layer.getFeatures():
                for attribute in param_json[layer.name()]:
                    if feature[attribute] == NULL:
                        null_attributes_feature.append([
                            'Attributs vides',
                            layer.name(),
                            feature.id(),
                            attribute,
                            'Champs vides pour {}'.format(layer.name()),
                            feature.geometry().centroid()])
        if null_attributes_feature:
            controlpoint_layer = ControlPointLayer('Attributs vides')
            controlpoint_layer.add_features(null_attributes_feature)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}