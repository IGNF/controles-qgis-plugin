from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessing,
    QgsGeometry,
    QgsPointXY
)

from BaseControlAlgorithm import BaseControlAlgorithm


class WatercourseContinuityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'G.08'
    ALG_DISPLAY_NAME = "Continuité des cours d'eau"
    ALG_GROUP = 'Controles du thème hydrographique'
    ALG_GROUP_ID = 'G'
    ALG_HELP = (
        "Ce contrôle recherche les discontinuités de tracé des objets complexes hydrographiques, "
        "constitués de tronçons hydrographiques et les tracés des objets complexes dotés de plus de 2 extrémités."
    )

    COMPLEX_LAYER = 'COMPLEX_LAYER'
    COMPLEX_KEY_FIELD = 'COMPLEX_KEY_FIELD'
    SEGMENT_LAYER = 'SEGMENT_LAYER'
    SEGMENT_KEY_FIELD = 'SEGMENT_KEY_FIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.COMPLEX_LAYER,
                self.tr("Couche des objets complexes hydrographiques"),
                types=[QgsProcessing.TypeVectorPoint]
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
            QgsProcessingParameterVectorLayer(
                self.SEGMENT_LAYER,
                self.tr("Couche des tronçons hydrographiques (lignes)"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.SEGMENT_KEY_FIELD,
                self.tr("Champ clé de liaison dans les tronçons"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        complex_layer = self.parameterAsVectorLayer(parameters, self.COMPLEX_LAYER, context)
        complex_key_field = self.parameterAsString(parameters, self.COMPLEX_KEY_FIELD, context)
        segment_layer = self.parameterAsVectorLayer(parameters, self.SEGMENT_LAYER, context)
        segment_key_field = self.parameterAsString(parameters, self.SEGMENT_KEY_FIELD, context)

        if complex_key_field not in complex_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des objets complexes").format(complex_key_field))
            return {'OUTPUT': 'Erreur'}

        if segment_key_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des tronçons").format(segment_key_field))
            return {'OUTPUT': 'Erreur'}

        # Regrouper les tronçons par valeur de la clé de l'objet complexe
        segments_by_key = {}
        for feature in segment_layer.getFeatures():
            key_value = feature[segment_key_field]
            if key_value is None:
                continue
            segments_by_key.setdefault(key_value, []).append(feature)

        invalid_features = []
        for complex_feature in complex_layer.getFeatures():
            key_value = complex_feature[complex_key_field]
            if key_value is None:
                continue

            segments = segments_by_key.get(key_value)
            if not segments:
                continue

            # Construire le dictionnaire des extrémités des tronçons liés à l'objet complexe
            # ainsi que la liste des tronçons touchant chaque extrémité (pour l'analyse de connexité)
            endpoints = {}
            segment_endpoints = {}
            for segment in segments:
                geom = segment.geometry()
                if geom is None or geom.isEmpty():
                    continue

                vertices = list(geom.vertices())
                if len(vertices) < 2:
                    continue

                start_point = vertices[0]
                end_point = vertices[-1]

                start_key = (round(start_point.x(), 6), round(start_point.y(), 6))
                end_key = (round(end_point.x(), 6), round(end_point.y(), 6))

                endpoints.setdefault(start_key, []).append(segment.id())
                endpoints.setdefault(end_key, []).append(segment.id())
                segment_endpoints[segment.id()] = (start_key, end_key)

            if not segment_endpoints:
                continue

            # Les extrémités libres (degré 1) correspondent soit à une discontinuité
            # (plusieurs tronçons non connectés), soit à une ramification du tracé.
            # Un tracé continu sans ramification ne doit comporter que 2 extrémités libres.
            free_endpoints_count = sum(1 for connections in endpoints.values() if len(connections) == 1)

            # Recherche des composantes connexes parmi les tronçons (deux tronçons sont
            # connectés s'ils partagent une extrémité) afin de distinguer une discontinuité
            # (non connexité) d'une simple ramification (plus de 2 extrémités).
            visited_segments = set()
            components_count = 0
            for segment_id in segment_endpoints:
                if segment_id in visited_segments:
                    continue
                components_count += 1
                stack = [segment_id]
                visited_segments.add(segment_id)
                while stack:
                    current_id = stack.pop()
                    for point_key in segment_endpoints[current_id]:
                        for neighbour_id in endpoints.get(point_key, []):
                            if neighbour_id not in visited_segments:
                                visited_segments.add(neighbour_id)
                                stack.append(neighbour_id)

            error_message = None
            if components_count > 1:
                error_message = "Le cours d'eau n'est pas connexe"
            elif free_endpoints_count > 2:
                error_message = "Le cours d'eau comprend plus de deux extrémités"

            if error_message:
                # Placer un point d'erreur sur chaque extrémité libre (degré 1) du graphe,
                # qui matérialise la discontinuité ou la ramification détectée.
                for point_key, connections in endpoints.items():
                    if len(connections) == 1:
                        endpoint_geom = QgsGeometry.fromPointXY(QgsPointXY(point_key[0], point_key[1]))
                        invalid_features.append([
                            "Continuité des cours d'eau",
                            complex_layer.name(),
                            complex_feature.id(),
                            complex_key_field,
                            error_message,
                            endpoint_geom
                        ])

        self.report_issues(invalid_features, "Continuité des cours d'eau")

        return self.processing_done_result()
