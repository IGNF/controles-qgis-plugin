from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes,
    QgsGeometry,
    QgsPointXY
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class TGVNetworkContinuityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'I.03'
    ALG_DISPLAY_NAME = "Continuité du réseau TGV"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'I'
    ALG_HELP = "Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons de voie ferrée dont le champ Nature = 'LGV’"

    INPUT_LAYER = 'INPUT_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    NATURE_VALUES = 'NATURE_VALUES'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
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
            QgsProcessingParameterFieldValues(
                self.NATURE_VALUES,
                self.tr("Valeurs Nature à contrôler"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=False,
                optional=False
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)

        if nature_field not in layer.fields().names():
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via le widget (chaîne séparée par des virgules)
        nature_values = field_values_as_string_list(self.parameterAsString(parameters, self.NATURE_VALUES, context))

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

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
            return self.processing_done_result()

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

        self.report_issues(invalid_features, "Continuité du réseau TGV")

        return self.processing_done_result()
