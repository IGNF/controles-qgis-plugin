from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
    QgsGeometry
)

from BaseControlAlgorithm import BaseControlAlgorithm


class MediumScaleMicroSegmentAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'ME A.3 '
    ALG_DISPLAY_NAME = "ME Géométrie - Micro-segment"
    ALG_GROUP = 'Controles moyenne échelle'
    ALG_GROUP_ID = 'ME'
    ALG_HELP = "Ce contrôle détecte deux points consécutifs non superposés et situés à une distance inférieure ou égale à 10 cm l'un de l'autre ."

    INPUT_LAYER = 'INPUT_LAYER'
    THRESHOLD = 'THRESHOLD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                self.tr('Taille minimale de segment (m)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.1,
                minValue=0.0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        taille_mini = self.parameterAsDouble(parameters, self.THRESHOLD, context)

        micro_segment = []
        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
            feedback.reportError(self.tr("{} n'est ni linéaire ni surfacique").format(layer.name()))
            return self.processing_done_result()
        for f in layer.getFeatures():
            if not f.geometry().isGeosValid():
                continue
            if (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.LineGeometry
                    and QgsWkbTypes.isMultiType(layer.wkbType())):
                geom = f.geometry().asMultiPolyline()
                geom = geom[0]
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.LineGeometry
                  and QgsWkbTypes.isSingleType(layer.wkbType())):
                geom = f.geometry().asPolyline()
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PolygonGeometry
                  and QgsWkbTypes.isSingleType(layer.wkbType())):
                geom = f.geometry().asPolygon()
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PolygonGeometry
                  and QgsWkbTypes.isMultiType(layer.wkbType())):
                geom = f.geometry().asMultiPolygon()
                geom = geom[0][0]
            for i in range(len(geom) - 1):
                segment = QgsGeometry.fromPolylineXY([geom[i], geom[i + 1]])
                if segment.length() < int(taille_mini):
                    micro_segment.append(['ME Géométrie - Micro-segment',
                                          layer.name(),
                                          f.id(),
                                          'geometry',
                                          "L'objet contient un micro-segment",
                                          f.geometry().pointOnSurface()])

        self.report_issues(micro_segment, 'ME Géométrie - Micro-segment')

        return self.processing_done_result()
