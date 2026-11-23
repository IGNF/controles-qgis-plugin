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


class DiscontinuityAccessAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.30'
    ALG_DISPLAY_NAME = "Discontinuité accès"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons de route dont le champ "
        "Accès véhicule léger = 'A péage'. Sont exclus les tronçons de route de Nature = 'Bac ou liaison maritime'."
    )

    INPUT_LAYER = 'INPUT_LAYER'
    ACCESS_FIELD = 'ACCESS_FIELD'
    ACCESS_VALUES = 'ACCESS_VALUES'
    NATURE_FIELD = 'NATURE_FIELD'
    EXCLUDED_NATURE_VALUES = 'EXCLUDED_NATURE_VALUES'

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
                self.ACCESS_FIELD,
                self.tr("Champ Accès véhicule léger"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ACCESS_VALUES,
                self.tr("Valeurs Accès véhicule léger à contrôler"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.ACCESS_FIELD,
                allowMultiple=True,
                optional=False
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
                self.EXCLUDED_NATURE_VALUES,
                self.tr("Valeurs Nature à exclure"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=True,
                optional=True
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        access_field = self.parameterAsString(parameters, self.ACCESS_FIELD, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if access_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Accès véhicule léger '{}' n'existe pas dans la couche des tronçons").format(access_field))
            return {'OUTPUT': 'Erreur'}

        if nature_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche des tronçons").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        access_values = field_values_as_string_list(self.parameterAsString(parameters, self.ACCESS_VALUES, context))
        excluded_nature_values = field_values_as_string_list(self.parameterAsString(parameters, self.EXCLUDED_NATURE_VALUES, context))

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        # Construire le dictionnaire des extrémités des tronçons dont l'Accès véhicule léger
        # correspond aux valeurs sélectionnées (ex. 'A péage'), en excluant les tronçons dont
        # la Nature correspond aux valeurs exclues (ex. 'Bac ou liaison maritime'), ainsi que
        # la liste des tronçons touchant chaque extrémité (pour l'analyse de connexité)
        endpoints = {}
        segment_endpoints = {}
        feature_by_id = {}

        for feature in segment_layer.getFeatures():
            access_value = str(feature[access_field]) if feature[access_field] is not None else None
            if access_value not in access_values:
                continue

            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else None
            if nature_value in excluded_nature_values:
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
            feature_by_id[feature.id()] = feature

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
                        "Discontinuité accès",
                        segment_layer.name(),
                        self.get_feature_identifier(feature_by_id[connections[0]], id_field),
                        access_field,
                        "Interruption du champ Accès à péage",
                        endpoint_geom
                    ])

        self.report_issues(invalid_features, "Discontinuité accès")

        return self.processing_done_result()

