from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes
)
from FieldValuesParameter import QgsProcessingParameterFieldValues

from BaseControlAlgorithm import BaseControlAlgorithm


class RailwayGroundRelativePositionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'I.02'
    ALG_DISPLAY_NAME = "Voies ferrées : cohérence Position par rapport au sol / Méthode d'acquisition planimétrique"
    ALG_GROUP = 'Controles du thème Transport ferroviaire'
    ALG_GROUP_ID = 'I'
    ALG_HELP = (
        "Ce contrôle détecte les tronçons de voies ferrées dont le champ Position par rapport au sol "
        "est inférieur à « 0 » et dont le champ Méthode d'acquisition planimétrique = « Photogrammétrie ».")

    INPUT_LAYER = 'INPUT_LAYER'
    POSITION_FIELD = 'POSITION_FIELD'
    METHODE_FIELD = 'METHODE_FIELD'
    METHODE_PHOTOGRAMMETRIE_VALUE = 'METHODE_PHOTOGRAMMETRIE_VALUE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche des tronçons de voies ferrées"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.POSITION_FIELD,
                self.tr("Champ Position par rapport au sol"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.METHODE_FIELD,
                self.tr("Champ Méthode d'acquisition planimétrique"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.METHODE_PHOTOGRAMMETRIE_VALUE,
                self.tr("Valeur Méthode d'acquisition planimétrique"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.METHODE_FIELD,
                allowMultiple=False,
                optional=False
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        position_field = self.parameterAsString(parameters, self.POSITION_FIELD, context)
        methode_field = self.parameterAsString(parameters, self.METHODE_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if position_field not in segment_layer.fields().names():
            feedback.reportError(
                self.tr("Le champ Position par rapport au sol '{}' n'existe pas dans la couche des tronçons").format(position_field)
            )
            return {'OUTPUT': 'Erreur'}

        if methode_field not in segment_layer.fields().names():
            feedback.reportError(
                self.tr("Le champ Méthode d'acquisition planimétrique '{}' n'existe pas dans la couche des tronçons").format(methode_field)
            )
            return {'OUTPUT': 'Erreur'}

        methode_photogrammetrie_value = self.parameterAsString(parameters, self.METHODE_PHOTOGRAMMETRIE_VALUE, context)

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        for feature in segment_layer.getFeatures():
            position_value = feature[position_field]
            methode_value = str(feature[methode_field]) if feature[methode_field] is not None else None

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            if position_value is None:
                continue

            try:
                position_value = float(position_value)
            except (TypeError, ValueError):
                continue

            if position_value < 0 and methode_value == methode_photogrammetrie_value:
                invalid_features.append([
                    "Voies ferrées : cohérence Position par rapport au sol / Méthode d'acquisition planimétrique",
                    segment_layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    position_field,
                    "La valeur du champ <Position par rapport au sol> et celle du champ <Méthode d’acquisition planimétrique> sont incohérentes",
                    geom.pointOnSurface()
                ])

        self.report_issues(invalid_features, "Voies ferrées : cohérence Position par rapport au sol / Méthode d'acquisition planimétrique")

        return self.processing_done_result()
