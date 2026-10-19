from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsWkbTypes,
    QgsSpatialIndex,
    QgsGeometry,
    QgsPointXY
)

from BaseControlAlgorithm import BaseControlAlgorithm


class BoundaryIntersectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'K.03'
    ALG_DISPLAY_NAME = "Intersections de limites administratives"
    ALG_GROUP = 'Controles du thème Administratif'
    ALG_GROUP_ID = 'K'
    ALG_HELP = "Un contrôle est généré quand deux limites administratives s'intersectent (pas de noeud commun)"

    INPUT_LAYER = 'INPUT_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)

        invalid_features = []

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

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

        self.report_issues(invalid_features, 'Intersections de limites administratives')

        return self.processing_done_result()
