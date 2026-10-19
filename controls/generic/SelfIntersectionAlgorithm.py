from qgis.core import (
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsWkbTypes,
)

from BaseControlAlgorithm import BaseControlAlgorithm


class SelfIntersectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.10'
    ALG_DISPLAY_NAME = "Auto-intersections"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = "Ce contrôle détecte les objets s’intersectant eux-mêmes. "

    INPUT_LAYER = 'INPUT_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)

        self_intersection_issues = []
        geom_type = layer.geometryType()
        if geom_type not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
            feedback.reportError(self.tr("La couche {} n'est ni linéaire ni surfacique").format(layer.name()))
            return self.processing_done_result()

        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isEmpty() or geom.isNull():
                continue
            if not geom.isSimple():
                self_intersection_issues.append([
                    'Auto-intersection',
                    layer.name(),
                    feature.id(),
                    'geometry',
                    'Objet auto-intersectant',
                    geom.pointOnSurface()
                ])

        self.report_issues(self_intersection_issues, 'Auto-intersections')

        return self.processing_done_result()

