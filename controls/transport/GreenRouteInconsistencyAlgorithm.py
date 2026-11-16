from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class GreenRouteInconsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.05'
    ALG_DISPLAY_NAME = "Incohérence Importance / Itinéraire vert"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle détecte les incohérences entre les attributs Importance et Itinéraire vert.")

    INPUT_LAYER = 'INPUT_LAYER'
    IMPORTANCE_FIELD = 'IMPORTANCE_FIELD'
    IMPORTANCE_VALUES = 'IMPORTANCE_VALUES'
    GREEN_ROUTE_FIELD = 'GREEN_ROUTE_FIELD'
    GREEN_ROUTE_VALUES = 'GREEN_ROUTE_VALUES'

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
                self.IMPORTANCE_FIELD,
                self.tr("Champ Importance"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.IMPORTANCE_VALUES,
                self.tr("Valeurs Importance interdites avec Itinéraire vert"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.IMPORTANCE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.GREEN_ROUTE_FIELD,
                self.tr("Champ Itinéraire vert"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.GREEN_ROUTE_VALUES,
                self.tr("Valeurs Itinéraire vert interdites avec ces Importance"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.GREEN_ROUTE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        importance_field = self.parameterAsString(parameters, self.IMPORTANCE_FIELD, context)
        green_route_field = self.parameterAsString(parameters, self.GREEN_ROUTE_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if importance_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Importance '{}' n'existe pas dans la couche des tronçons").format(importance_field))
            return {'OUTPUT': 'Erreur'}

        if green_route_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Itinéraire vert '{}' n'existe pas dans la couche des tronçons").format(green_route_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        importance_values = field_values_as_string_list(self.parameterAsString(parameters, self.IMPORTANCE_VALUES, context))
        green_route_values = field_values_as_string_list(self.parameterAsString(parameters, self.GREEN_ROUTE_VALUES, context))

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        # Signaler les tronçons dont l'Importance correspond aux valeurs interdites
        # (ex. 3, 4 ou 5) combinée à un Itinéraire vert correspondant aux valeurs
        # interdites (ex. Vrai)
        for feature in segment_layer.getFeatures():
            importance_value = str(feature[importance_field]) if feature[importance_field] is not None else None
            if importance_value not in importance_values:
                continue

            green_route_value = str(feature[green_route_field]) if feature[green_route_field] is not None else None
            if green_route_value not in green_route_values:
                continue

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            invalid_features.append([
                "Incohérence Importance / Itinéraire vert",
                segment_layer.name(),
                self.get_feature_identifier(feature, id_field),
                importance_field,
                "Incohérence entre Importance et Itinéraire vert",
                geom.pointOnSurface()
            ])

        self.report_issues(invalid_features, "Incohérence Importance / Itinéraire vert")

        return self.processing_done_result()
