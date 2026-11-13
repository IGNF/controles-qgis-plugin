from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes,
    QgsGeometry,
    QgsPointXY
)

from BaseControlAlgorithm import BaseControlAlgorithm


class DiscontinuityRoadClassificationAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.27'
    ALG_DISPLAY_NAME = "Discontinuité palier"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle recherche les discontinuités, c'est-à-dire les noeuds d'ordre 1 sur le réseau autoroutier, "
        "puis sur le réseau autoroutier ou national et enfin sur le réseau autoroutier, national ou départemental."
    )

    # Paliers cumulés étudiés successivement : Autoroutier, puis +National, puis +Départemental
    ROAD_CLASSIFICATION_LEVELS = [
        {'Autoroute'},
        {'Autoroute', 'Nationale'},
        {'Autoroute', 'Nationale', 'Départementale'},
    ]

    SEGMENT_LAYER = 'SEGMENT_LAYER'
    SEGMENT_KEY_FIELD = 'SEGMENT_KEY_FIELD'
    COMPLEX_LAYER = 'COMPLEX_LAYER'
    COMPLEX_KEY_FIELD = 'COMPLEX_KEY_FIELD'
    COMPLEX_TYPE_FIELD = 'COMPLEX_TYPE_FIELD'

    INPUT_LAYER = SEGMENT_LAYER

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
                self.SEGMENT_KEY_FIELD,
                self.tr("Champ clé de liaison au complexe"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.COMPLEX_LAYER,
                self.tr("Couche des objets complexes Route numérotée ou nommée"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.COMPLEX_KEY_FIELD,
                self.tr("Champ clé de l'objet complexe"),
                parentLayerParameterName=self.COMPLEX_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.COMPLEX_TYPE_FIELD,
                self.tr("Champ Type de route"),
                parentLayerParameterName=self.COMPLEX_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.SEGMENT_LAYER, context)
        segment_key_field = self.parameterAsString(parameters, self.SEGMENT_KEY_FIELD, context)
        complex_layer = self.parameterAsVectorLayer(parameters, self.COMPLEX_LAYER, context)
        complex_key_field = self.parameterAsString(parameters, self.COMPLEX_KEY_FIELD, context)
        type_route_field = self.parameterAsString(parameters, self.COMPLEX_TYPE_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if segment_key_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des tronçons").format(segment_key_field))
            return {'OUTPUT': 'Erreur'}

        if complex_key_field not in complex_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des objets complexes").format(complex_key_field))
            return {'OUTPUT': 'Erreur'}

        if type_route_field not in complex_layer.fields().names():
            feedback.reportError(self.tr("Le champ Type de route '{}' n'existe pas dans la couche des objets complexes").format(type_route_field))
            return {'OUTPUT': 'Erreur'}

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        # Type de route de chaque objet complexe, indexé par clé
        type_route_by_key = {}
        for complex_feature in complex_layer.getFeatures():
            key_value = complex_feature[complex_key_field]
            if key_value is None:
                continue
            type_route_value = complex_feature[type_route_field]
            type_route_by_key[key_value] = str(type_route_value) if type_route_value is not None else None

        # Lecture des tronçons avec le Type de route de l'objet complexe auquel ils sont liés
        segments = []
        feature_by_id = {}
        for feature in segment_layer.getFeatures():
            key_value = feature[segment_key_field]
            type_route_value = type_route_by_key.get(key_value) if key_value is not None else None
            if type_route_value is None:
                continue

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            vertices = list(geom.vertices())
            if len(vertices) < 2:
                continue

            segments.append((feature.id(), type_route_value, vertices[0], vertices[-1]))
            feature_by_id[feature.id()] = feature

        invalid_features = []

        if not segments:
            return self.processing_done_result()

        # Pour chaque palier cumulé (Autoroutier ; +National ; +Départemental), on
        # construit le sous-graphe des tronçons concernés et on recherche les
        # noeuds d'ordre 1 (extrémités libres), révélateurs d'une discontinuité.
        for level in self.ROAD_CLASSIFICATION_LEVELS:
            endpoints = {}
            segment_endpoints = {}

            for feature_id, type_route_value, start_point, end_point in segments:
                if type_route_value not in level:
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
                        "Discontinuité palier",
                        segment_layer.name(),
                        self.get_feature_identifier(feature_by_id[connections[0]], id_field),
                        type_route_field,
                        "Discontinuité de classement",
                        endpoint_geom
                    ])

        self.report_issues(invalid_features, "Discontinuité palier")

        return self.processing_done_result()

