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


class NumericAttributeAlgorithm(QgsProcessingAlgorithm):


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

        numeric_attributes_feature = []
        for layer in layers:
            if layer.name() not in param_json.keys():
                feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
                continue
            for feature in layer.getFeatures():
                for att in param_json[layer.name()]:
                    if feature[att] == NULL:
                        continue
                    if  isinstance(feature[att], (int, float)):
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
        return 'attributes_inconsistency'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Incohérence d'attributs"

    def group(self):
        """Nom du groupe"""
        return 'Générique'

    def groupId(self):
        """Identifiant du groupe"""
        return 'generic'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Détecte les incohérences entre attributs selon les règles définies dans le fichier JSON"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NumericAttributeAlgorithm()