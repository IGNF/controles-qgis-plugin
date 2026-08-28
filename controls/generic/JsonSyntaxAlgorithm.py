from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
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
            QgsProcessingParameterField(
                'FIELDS',
                'Champs à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                allowMultiple=True
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
        fields = self.parameterAsFields(parameters, 'FIELDS', context)

        json_attributes = []

        for feature in layer.getFeatures():
            for att in fields:
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