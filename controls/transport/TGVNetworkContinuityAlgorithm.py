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
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list


class TGVNetworkContinuityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'NATURE_FIELD',
                "Champ Nature",
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'NATURE_VALUES',
                "Valeurs Nature à contrôler",
                parentLayerParameterName='INPUT_LAYER',
                parentFieldParameterName='NATURE_FIELD',
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
        nature_field = self.parameterAsString(parameters, 'NATURE_FIELD', context)

        if nature_field not in layer.fields().names():
            feedback.reportError(f"Le champ Nature '{nature_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via le widget (chaîne séparée par des virgules)
        nature_values = field_values_as_string_list(self.parameterAsString(parameters, 'NATURE_VALUES', context))

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

        invalid_features = []

        # Construire le dictionnaire des extrémités des tronçons de Nature sélectionnée
        # ainsi que la liste des tronçons touchant chaque extrémité (pour l'analyse de connexité)
        endpoints = {}
        segment_endpoints = {}

        for feature in layer.getFeatures():
            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else None
            if nature_value not in nature_values:
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
                        "Continuité du réseau TGV",
                        layer.name(),
                        connections[0],
                        nature_field,
                        "Interruption du réseau TGV",
                        endpoint_geom
                    ])

        if invalid_features:
            controlpoint_layer = ControlPointLayer("Continuité du réseau TGV")
            controlpoint_layer.add_features(invalid_features)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'I.03'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Continuité du réseau TGV"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Transport'

    def groupId(self):
        """Identifiant du groupe"""
        return 'I'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            ("Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons de voie ferrée "
             "dont le champ Nature = 'LGV’")

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return TGVNetworkContinuityAlgorithm()