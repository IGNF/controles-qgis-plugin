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


class AttributesInconsistencyAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYERS = 'INPUT_LAYERS'
    JSON_FILE = 'PARAM_JSON'
    OUTPUT = 'OUTPUT'

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'C.03'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Incohérences entre attributs"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques attributaires'

    def groupId(self):
        """Identifiant du groupe"""
        return 'C'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Le contrôle détecte les incohérences entre attributs pour une classe donnée d'après la règle suivante :"\
            "Si Champ1 <> Valeur1 alors Champ2 = Valeur2."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return AttributesInconsistencyAlgorithm()

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

        #param_json : {'couche': [{condition: consequence}, ...], ...}
        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        incoherence_attributes_feature = []
        for layer in layers:
            if layer.name() not in param_json.keys():
                feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
                continue
            for feature in layer.getFeatures():
                for condition, consequence in param_json[layer.name()]:
                    # condition et consequence [attributs, operateur, valeur]
                    if ' '.join(condition) and not ' '.join(consequence):
                        incoherence_attributes_feature.append(
                            ['Incohérence entre attributs',
                            layer.name(),
                            feature.id(),
                            consequence[0],
                            'Les champs {} et {} ne sont pas cohérents'.format(condition[0], consequence[0]),
                            feature.geometry().centroid()])
        if incoherence_attributes_feature != []:
            controlpoint_layer = ControlPointLayer('Incohérence entre attributs')
            controlpoint_layer.add_features(incoherence_attributes_feature)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}