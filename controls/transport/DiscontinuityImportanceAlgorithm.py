from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes,
    QgsGeometry,
    QgsPointXY
)

from BaseControlAlgorithm import BaseControlAlgorithm


class DiscontinuityImportanceAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.15'
    ALG_DISPLAY_NAME = "Discontinuité importance"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Le contrôle recherche les anomalies suivantes :"
        "- extrémités du graphe formé par toutes les routes d'importance 1 (routes d'Importance 1 "
        "en cul-de-sac ou poursuivies uniquement par des routes de moindre Importance),"
        "- extrémités du graphe formé par toutes les routes d'Importance 1 ou 2 (routes d'Importance 1 ou 2 "
        "en cul-de-sac ou poursuivies uniquement par des routes de moindre Importance),"
        "- extrémités du graphe formé par toutes les routes d'Importance 1, 2 ou 3 (routes d'Importance 1, 2 ou 3 "
        "en cul-de-sac ou poursuivies uniquement par des routes de moindre Importance),"
        "- extrémités du graphe formé par toutes les routes d'Importance 1, 2, 3 ou 4 "
        "en cul-de-sac ou poursuivies uniquement par des routes de moindre Importance)"
    )

    # Niveaux d'importance cumulés étudiés : {1}, {1,2}, {1,2,3}, {1,2,3,4}
    IMPORTANCE_LEVELS = [1, 2, 3, 4]

    SEGMENT_LAYER = 'SEGMENT_LAYER'
    IMPORTANCE_FIELD = 'IMPORTANCE_FIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SEGMENT_LAYER,
                self.tr("Couche des tronçons de route"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.IMPORTANCE_FIELD,
                self.tr("Champ Importance"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.SEGMENT_LAYER, context)
        importance_field = self.parameterAsString(parameters, self.IMPORTANCE_FIELD, context)

        if importance_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Importance '{}' n'existe pas dans la couche des tronçons").format(importance_field))
            return {'OUTPUT': 'Erreur'}

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        # Lecture des tronçons avec leur valeur d'Importance (ignorée si non numérique)
        segments = []
        for feature in segment_layer.getFeatures():
            raw_value = feature[importance_field]
            if raw_value is None or raw_value == '':
                continue

            try:
                importance_value = int(str(raw_value).strip())
            except (TypeError, ValueError):
                continue

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            vertices = list(geom.vertices())
            if len(vertices) < 2:
                continue

            segments.append((feature.id(), importance_value, vertices[0], vertices[-1]))

        if not segments:
            return self.processing_done_result()

        # Pour chaque niveau cumulé d'Importance (1 ; 1-2 ; 1-2-3 ; 1-2-3-4), on
        # construit le sous-graphe des tronçons concernés et on recherche les
        # extrémités de degré 1 (cul-de-sac, ou connexion uniquement à des
        # routes de moindre Importance situées hors du sous-graphe).
        for level in self.IMPORTANCE_LEVELS:
            endpoints = {}
            segment_endpoints = {}

            for feature_id, importance_value, start_point, end_point in segments:
                if importance_value > level:
                    continue

                start_key = (round(start_point.x(), 6), round(start_point.y(), 6))
                end_key = (round(end_point.x(), 6), round(end_point.y(), 6))

                endpoints.setdefault(start_key, []).append(feature_id)
                endpoints.setdefault(end_key, []).append(feature_id)
                segment_endpoints[feature_id] = (start_key, end_key)

            if not segment_endpoints:
                continue

            for point_key, connections in endpoints.items():
                if len(connections) == 1:
                    endpoint_geom = QgsGeometry.fromPointXY(QgsPointXY(point_key[0], point_key[1]))
                    invalid_features.append([
                        "Discontinuité importance",
                        segment_layer.name(),
                        connections[0],
                        importance_field,
                        '',
                        endpoint_geom
                    ])

        self.report_issues(invalid_features, "Discontinuité importance")

        return self.processing_done_result()

