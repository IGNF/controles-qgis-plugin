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


class JsonSyntaxAlgorithm(QgsProcessingAlgorithm):

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

        json_attributes = []
        if layer.name() not in param_json.keys():
            feedback.reportError("{} n'est pas présent dans le fichier json de paramétrage".format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            for att in param_json[layer.name()]:
                if feature[att] == NULL:
                    continue
                try:
                    json.loads(feature[att])
                except json.JSONDecodeError:
                    json_attributes.append(['Syntaxe des champs JSON',
                                       layer.name(),
                                       feature.id(),
                                       att,
                                       'La syntaxe JSON du champ {} est incorrecte'.format(feature[att]),
                                       feature.geometry().pointOnSurface()])

        if json_attributes != []:
            controlpoint_layer = ControlPointLayer('Syntaxe des champs JSON')
            controlpoint_layer.add_features(json_attributes)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'C.12'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Syntaxe des champs JSON"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques attributaires'

    def groupId(self):
        """Identifiant du groupe"""
        return 'C'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Le but de ce contrôle est de s’assurer que la syntaxe définie pour les champs de format JSON est respectée."\
            "Il s’agit de vérifier que les clés et les valeurs de clés sont conformes à ce qui est spécifié."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return JsonSyntaxAlgorithm()