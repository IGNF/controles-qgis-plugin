from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    NULL
)

from BaseControlAlgorithm import BaseControlAlgorithm


class NumericAttributeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.08'
    ALG_DISPLAY_NAME = "Attributs numériques"
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = "contrôle si l'attribut est entièrement composé de chiffres."

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
                            self.get_feature_identifier(feature, id_field),
                            att,
                            '',
                            feature.geometry().pointOnSurface()])

        self.report_issues(numeric_attributes_feature, 'Attributs numériques')

        return self.processing_done_result()
