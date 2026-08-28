from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
NULL
)
from ControlPointLayer import ControlPointLayer


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

        numeric_attributes_feature = []

        for feature in layer.getFeatures():
            for att in fields:
                if feature[att] == NULL:
                    continue
                if not isinstance(feature[att], (int, float)):
                    try:
                        float(feature[att])
                    except (ValueError, TypeError):
                        numeric_attributes_feature.append(
                            ['Attributs numériques',
                            layer.name(),
                            feature.id(),
                            att,
                            '',
                            feature.geometry().pointOnSurface()])

        if numeric_attributes_feature != []:
            controlpoint_layer = ControlPointLayer('Attributs numériques')
            controlpoint_layer.add_features(numeric_attributes_feature)
            controlpoint_layer.save_as_temp_layer()

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