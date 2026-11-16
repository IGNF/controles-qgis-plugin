from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class TrafficDirectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.20'
    ALG_DISPLAY_NAME = "Sens / Nature / Urbain"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle détecte : "
        "Cas 1 : les tronçons de Nature « Type autoroutier » ou « Rond-point » qui n'ont pas leur "
        "Sens de circulation à « Sens direct » ou à « Sens inverse ». "
        "Cas 2 : les tronçons dont le Sens de circulation est à « Sans objet » qui sont de Nature "
        "« Route à 2 chaussées » ou « Bretelle » ou « Route empierrée » ou « Chemin ». "
        "Cas 3 : les tronçons dont le Sens de circulation n'est pas à « Sans objet » et qui pourtant "
        "sont de Nature : « Bac ou liaison maritime », « Escalier » ou « Sentier ». "
        "Les valeurs contrôlées sont modifiables en paramètre.")

    INPUT_LAYER = 'INPUT_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    SENS_FIELD = 'SENS_FIELD'
    NATURE_VALUES = 'NATURE_VALUES'
    SENS_VALUES = 'SENS_VALUES'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche des tronçons de route"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NATURE_FIELD,
                self.tr("Champ Nature"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.SENS_FIELD,
                self.tr("Champ Sens de circulation"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.NATURE_VALUES,
                self.tr("Valeurs Nature"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.SENS_VALUES,
                self.tr("Valeurs Sens de circulation attendues"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.SENS_FIELD,
                allowMultiple=True,
                optional=False
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)
        sens_field = self.parameterAsString(parameters, self.SENS_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if nature_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche des tronçons").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        if sens_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Sens de circulation '{}' n'existe pas dans la couche des tronçons").format(sens_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        case1_nature_values = field_values_as_string_list(self.parameterAsString(parameters, self.CASE1_NATURE_VALUES, context))
        sens_values = field_values_as_string_list(self.parameterAsString(parameters, self.SENS_VALUES, context))

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        for feature in segment_layer.getFeatures():
            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else None
            sens_value = str(feature[sens_field]) if feature[sens_field] is not None else None

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            if nature_value in case1_nature_values and sens_value not in sens_values:
                invalid_features.append([
                    "Sens de circulation incohérent avec la Nature",
                    segment_layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    sens_field,
                    "Incohérence entre Nature et Sens de circulation",
                    geom.pointOnSurface()
                ])


        self.report_issues(invalid_features, "Incohérence Nature / Sens de circulation")

        return self.processing_done_result()
