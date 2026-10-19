from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsWkbTypes,
    QgsPoint
)
import math

from BaseControlAlgorithm import BaseControlAlgorithm


class TurningBackAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.20'
    ALG_DISPLAY_NAME = "Rebroussement"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = "Le contrôle détecte les rebroussements définissant un angle < 10° sur les réseaux linéaires concernés"

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
        angle_threshold = 10.0

        turning_backs = []
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
            feedback.pushWarning(self.tr("La couche {} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isEmpty() or not geom.isGeosValid():
                continue
            polyline = geom.asPolyline() if geom.isMultipart() is False else geom.asMultiPolyline()[0]
            for i in range(1, len(polyline) - 1):
                p1 = polyline[i - 1]
                p2 = polyline[i]
                p3 = polyline[i + 1]
                v1_x = p2.x() - p1.x()
                v1_y = p2.y() - p1.y()
                v2_x = p3.x() - p2.x()
                v2_y = p3.y() - p2.y()
                len_v1 = math.sqrt(v1_x ** 2 + v1_y ** 2)
                len_v2 = math.sqrt(v2_x ** 2 + v2_y ** 2)
                if len_v1 == 0 or len_v2 == 0:
                    continue
                dot_product = v1_x * v2_x + v1_y * v2_y
                cos_angle = dot_product / (len_v1 * len_v2)
                cos_angle = max(-1.0, min(1.0, cos_angle))
                angle_rad = math.acos(cos_angle)
                angle_deg = math.degrees(angle_rad)
                deviation = 180.0 - angle_deg
                if deviation < angle_threshold:
                    turning_backs.append([
                        'Rebroussement',
                        layer.name(),
                        feature.id(),
                        'geometrie',
                        'Rebroussement',
                        QgsPoint(p2.x(), p2.y())
                    ])

        self.report_issues(turning_backs, 'Rebroussement')

        return self.processing_done_result()
