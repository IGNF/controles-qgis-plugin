from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsSpatialIndex,
QgsGeometry,
QgsPointXY
)
from ControlPointLayer import ControlPointLayer
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list


class BoundaryIntersectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
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

        invalid_features = []

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

        spatial_index = QgsSpatialIndex()
        features_dict = {}

        for f in layer.getFeatures():
            if not f.geometry() or not f.geometry().isGeosValid():
                continue
            features_dict[f.id()] = f
            spatial_index.addFeature(f)

        def vertex_set(geom):
            """Ensemble des sommets de la géométrie, arrondis pour tolérer les imprécisions numériques."""
            return {(round(v.x(), 6), round(v.y(), 6)) for v in geom.vertices()}

        processed_pairs = set()

        for fid, feature in features_dict.items():
            geom = feature.geometry()
            bbox = geom.boundingBox()
            nearby_ids = spatial_index.intersects(bbox)

            for nearby_id in nearby_ids:
                if nearby_id == fid:
                    continue

                pair_key = tuple(sorted((fid, nearby_id)))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                nearby_feature = features_dict[nearby_id]
                nearby_geom = nearby_feature.geometry()

                if not geom.intersects(nearby_geom):
                    continue

                intersection_geom = geom.intersection(nearby_geom)
                if intersection_geom is None or intersection_geom.isEmpty():
                    continue

                vertices_1 = vertex_set(geom)
                vertices_2 = vertex_set(nearby_geom)

                # Points d'intersection qui ne correspondent pas à un sommet (noeud) commun
                # aux deux limites administratives
                reported_points = set()
                for vertex in intersection_geom.vertices():
                    point_key = (round(vertex.x(), 6), round(vertex.y(), 6))
                    if point_key in reported_points:
                        continue
                    if point_key not in vertices_1 or point_key not in vertices_2:
                        reported_points.add(point_key)
                        invalid_features.append([
                            'Intersections de limites administratives',
                            layer.name(),
                            '{}, {}'.format(feature.id(), nearby_feature.id()),
                            'geometry',
                            "Intersection de limites administratives",
                            QgsGeometry.fromPointXY(QgsPointXY(point_key[0], point_key[1]))
                        ])

        if invalid_features:
            controlpoint_layer = ControlPointLayer('Intersections de limites administratives')
            controlpoint_layer.add_features(invalid_features)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'K.03'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Intersections de limites administratives"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Administratif'

    def groupId(self):
        """Identifiant du groupe"""
        return 'K'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Un contrôle est généré quand deux limites administratives s'intersectent (pas de noeud commun)"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return BoundaryIntersectionAlgorithm()