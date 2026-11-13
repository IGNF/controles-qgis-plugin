from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsWkbTypes
)

from BaseControlAlgorithm import BaseControlAlgorithm


class SurfaceIntersectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.12'
    ALG_DISPLAY_NAME = "Intersections de surfaciques"
    ALG_GROUP = 'Controles génériques géométrique'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte les intersections entre les objets d’une même classe."
        "Le contrôle est positionné sur la ou les intersections entre les objets."
    )

    INPUT_LAYER = 'INPUT_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        intersection_features = []
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            feedback.reportError(self.tr("{} n'est pas une couche surfacique").format(layer.name()))
            return self.processing_done_result()

        features = list(layer.getFeatures())
        for i, feature1 in enumerate(features):
            geom1 = feature1.geometry()
            if not geom1 or geom1.isNull():
                continue
            for j in range(i + 1, len(features)):
                feature2 = features[j]
                geom2 = feature2.geometry()
                if not geom2 or geom2.isNull():
                    continue
                if geom1.intersects(geom2):
                    intersection = geom1.intersection(geom2)
                    if intersection.area() > 0:
                        intersection_features.append([
                            'Intersection de surfaciques',
                            layer.name(),
                            self.get_feature_identifier(feature1, id_field),
                            "geometry",
                            "Intersection franche",
                            intersection.centroid()
                        ])

        self.report_issues(intersection_features, 'Intersection de surfaciques')

        return self.processing_done_result()
