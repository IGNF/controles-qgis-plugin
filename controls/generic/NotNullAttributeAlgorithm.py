from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
NULL
)
from ControlPointLayer import ControlPointLayer


class NotNullAttributeAlgorithm(QgsProcessingAlgorithm):

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

        null_attributes_feature = []

        for feature in layer.getFeatures():
            for attribute in fields:
                if feature[attribute] == NULL:
                    null_attributes_feature.append([
                        'Attributs vides',
                        layer.name(),
                        feature.id(),
                        attribute,
                        'Champs vides pour {}'.format(layer.name()),
                        feature.geometry().pointOnSurface()])

        if null_attributes_feature:
            controlpoint_layer = ControlPointLayer('Attributs vides')
            controlpoint_layer.add_features(null_attributes_feature)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'C.01'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Attributs vides"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques attributaires'

    def groupId(self):
        """Identifiant du groupe"""
        return 'C'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Vérifie les attributs qui ne doivent pas être vides"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NotNullAttributeAlgorithm()