from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFile,
QgsProcessingParameterFeatureSink,
NULL
)
from ControlPointLayer import ControlPointLayer
import json


class NumericAttributeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorAnyGeometry]
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
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        numeric_attributes_feature = []
        if layer.name() not in param_json.keys():
            feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            for att in param_json[layer.name()]:
                if feature[att] == NULL:
                    continue
                if isinstance(feature[att], (int, float)):
                    numeric_attributes_feature.append(
                        ['Attributs numériques',
                        layer.name(),
                        feature.id(),
                        att,
                        '',
                        feature.geometry().centroid()])

        if numeric_attributes_feature != []:
            controlpoint_layer = ControlPointLayer('Attributs numériques')
            controlpoint_layer.add_features(numeric_attributes_feature)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'C.08'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Attributs numériques"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques attributaires'

    def groupId(self):
        """Identifiant du groupe"""
        return 'C'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "contrôle si l'attribut est entièrement composé de chiffres."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NumericAttributeAlgorithm()