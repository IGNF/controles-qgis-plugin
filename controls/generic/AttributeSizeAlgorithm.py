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

from ...ControlPointLayer import ControlPointLayer
import json


class AttributeSizeAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
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
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        # param_json : {'couche': [{'att1':'size1'}, {'att2':'size2'}], ...}
        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        size_attributes_feature = []
        for layer in layers:
            if layer.name() not in param_json.keys():
                feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
                continue
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
                            feature.geometry().centroid()])
        if size_attributes_feature != []:
            controlpoint_layer = ControlPointLayer('Taille des champs')
            controlpoint_layer.add_features(size_attributes_feature)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        return 'attributesize'

    def displayName(self):
        return 'Vérification taille des attributs'

    def group(self):
        return 'Contrôles génériques'

    def groupId(self):
        return 'generic_controls'

    def createInstance(self):
        return AttributeSizeAlgorithm()