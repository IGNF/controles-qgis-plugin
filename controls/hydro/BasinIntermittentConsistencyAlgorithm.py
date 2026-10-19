from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessing
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class BasinIntermittentConsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'G.01'
    ALG_DISPLAY_NAME = "Cohérence Bassin / Intermittent"
    ALG_GROUP = 'Controles du thème hydrographique'
    ALG_GROUP_ID = 'G'
    ALG_HELP = (
        "Ce contrôle détecte les surfaces hydrographiques dont la Nature est Réservoir-bassin ou "
        "Réservoir-bassin piscicole ou Réservoir-bassin d'orage et dont le champ Persistance est égal à Permanent"
    )

    INPUT_LAYER = 'INPUT_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    NATURE_VALUES = 'NATURE_VALUES'
    PERSISTANCE_FIELD = 'PERSISTANCE_FIELD'
    PERSISTANCE_VALUES = 'PERSISTANCE_VALUES'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NATURE_FIELD,
                self.tr('Champ Nature'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.NATURE_VALUES,
                self.tr('Valeurs Nature à contrôler'),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.PERSISTANCE_FIELD,
                self.tr('Champ Persistance'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.PERSISTANCE_VALUES,
                self.tr('Valeurs Persistance à contrôler'),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.PERSISTANCE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)
        persistance_field = self.parameterAsString(parameters, self.PERSISTANCE_FIELD, context)

        field_names = layer.fields().names()
        if nature_field not in field_names:
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        if persistance_field not in field_names:
            feedback.reportError(self.tr("Le champ Persistance '{}' n'existe pas dans la couche").format(persistance_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via le widget (stockées en chaîne séparée par des virgules)
        raw_nature_values = self.parameterAsString(parameters, self.NATURE_VALUES, context)
        selected_nature_values = field_values_as_string_list(raw_nature_values)

        raw_persistance_values = self.parameterAsString(parameters, self.PERSISTANCE_VALUES, context)
        selected_persistance_values = field_values_as_string_list(raw_persistance_values)

        invalid_features = []
        for feature in layer.getFeatures():
            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else ''
            persistance_value = str(feature[persistance_field]) if feature[persistance_field] is not None else ''

            if nature_value in selected_nature_values and persistance_value in selected_persistance_values:
                invalid_features.append([
                    'Cohérence Bassin / Intermittent',
                    layer.name(),
                    feature.id(),
                    nature_field,
                    "Le champ Persistance des surfaces hydrographiques dont la Nature est {} doit être à {}".format(
                        selected_nature_values, selected_persistance_values),
                    feature.geometry().pointOnSurface()
                ])

        self.report_issues(invalid_features, 'Cohérence Bassin / Intermittent')

        return self.processing_done_result()
