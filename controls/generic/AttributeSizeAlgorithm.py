from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink
)

from ControlPointLayer import ControlPointLayer
import json


class AttributeSizeAlgorithm(QgsProcessingAlgorithm):


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

        size_attributes_feature = []
        if layer.name() not in param_json.keys():
            feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            for att, size in param_json[layer.name()].items():
                if feature[att] is None or feature[att] == '':
                    continue
                if len(feature[att]) > int(size):
                    size_attributes_feature.append(
                        ['Taille des champs',
                        layer.name(),
                        feature.id(),
                        att,
                        '',
                        feature.geometry().pointOnSurface()])

        if size_attributes_feature != []:
            controlpoint_layer = ControlPointLayer('Taille des champs')
            controlpoint_layer.add_features(size_attributes_feature)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        return 'C.02'

    def displayName(self):
        return 'Taille des champs'

    def group(self):
        return 'Controles génériques attributaires'

    def groupId(self):
        return 'C'

    def createInstance(self):
        return AttributeSizeAlgorithm()

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Il vérifie que la longueur des attributs ne dépasse pas la longueur maximum définie pour l'archivage FEIV."