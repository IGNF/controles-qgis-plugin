from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer
import json


class AttributesInconsistencyAlgorithm(QgsProcessingAlgorithm):

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

        #param_json : {'couche': {condition: consequence}, ...}
        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        incoherence_attributes_feature = []
        if layer.name() not in param_json.keys():
            feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        for condition, consequence in param_json[layer.name()]:
            request = QgsFeatureRequest()
            request.setFilterExpression(condition)
            for feature in layer.getFeatures(request):
                if not consequence:
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