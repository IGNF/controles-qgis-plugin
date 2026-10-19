from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsGeometry,
QgsPointXY
)
from ControlPointLayer import ControlPointLayer


class DiscontinuityGreenRouteAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'SEGMENT_LAYER',
                "Couche des tronçons de route",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'GREEN_ROUTE_FIELD',
                "Champ Itinéraire vert",
                parentLayerParameterName='SEGMENT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, 'SEGMENT_LAYER', context)
        green_route_field = self.parameterAsString(parameters, 'GREEN_ROUTE_FIELD', context)

        if green_route_field not in segment_layer.fields().names():
            feedback.reportError(f"Le champ Itinéraire vert '{green_route_field}' n'existe pas dans la couche des tronçons")
            return {'OUTPUT': 'Erreur'}

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{segment_layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

        invalid_features = []

        # Construire le dictionnaire des extrémités des tronçons appartenant au réseau vert
        # (Itinéraire vert = VRAI), ainsi que la liste des tronçons touchant chaque
        # extrémité (pour l'analyse de connexité)
        endpoints = {}
        segment_endpoints = {}

        for feature in segment_layer.getFeatures():
            if not bool(feature[green_route_field]):
                continue

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            vertices = list(geom.vertices())
            if len(vertices) < 2:
                continue

            start_point = vertices[0]
            end_point = vertices[-1]

            start_key = (round(start_point.x(), 6), round(start_point.y(), 6))
            end_key = (round(end_point.x(), 6), round(end_point.y(), 6))

            endpoints.setdefault(start_key, []).append(feature.id())
            endpoints.setdefault(end_key, []).append(feature.id())
            segment_endpoints[feature.id()] = (start_key, end_key)

        if not segment_endpoints:
            return {'OUTPUT': 'Traitement terminé'}

        # Les extrémités libres (degré 1) correspondent soit à une discontinuité
        # (plusieurs tronçons non connectés), soit à une ramification du tracé.
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

        error_detected = components_count > 1 or free_endpoints_count > 2

        if error_detected:
            # Placer un point d'erreur sur chaque extrémité libre (degré 1) du graphe,
            # qui matérialise la discontinuité ou la ramification détectée.
            for point_key, connections in endpoints.items():
                if len(connections) == 1:
                    endpoint_geom = QgsGeometry.fromPointXY(QgsPointXY(point_key[0], point_key[1]))
                    invalid_features.append([
                        "Discontinuité itinéraire vert",
                        segment_layer.name(),
                        connections[0],
                        green_route_field,
                        "",
                        endpoint_geom
                    ])

        if invalid_features:
            controlpoint_layer = ControlPointLayer("Discontinuité itinéraire vert")
            controlpoint_layer.add_features(invalid_features)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'D.14'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Discontinuité itinéraire vert"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Transport'

    def groupId(self):
        """Identifiant du groupe"""
        return 'D'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            ("Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons appartenant au réseau vert.")

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return DiscontinuityGreenRouteAlgorithm()
