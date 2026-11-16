from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    NULL
)

from BaseControlAlgorithm import BaseControlAlgorithm


class NotNullAttributeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.01'
    ALG_DISPLAY_NAME = "Attributs vides"
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = "Vérifie les attributs qui ne doivent pas être vides"

    INPUT_LAYER = 'INPUT_LAYER'
    FIELDS = 'FIELDS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDS,
                self.tr('Champs à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                allowMultiple=True
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        fields = self.parameterAsFields(parameters, self.FIELDS, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        null_attributes_feature = []

        for feature in layer.getFeatures():
            for attribute in fields:
                if feature[attribute] == NULL:
                    null_attributes_feature.append([
                        'Attributs vides',
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        attribute,
                        'Champs vides pour {}'.format(layer.name()),
                        feature.geometry().pointOnSurface()])

        self.report_issues(null_attributes_feature, 'Attributs vides')

        return self.processing_done_result()
