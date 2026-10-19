from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsWkbTypes
)

from BaseControlAlgorithm import BaseControlAlgorithm


class LinearDuplicateAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.06'
    ALG_DISPLAY_NAME = "Doublons partiels linéaires"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte des objets linéaires de même couche ayant une géométrie commune."
        "Il ne tient pas compte des attributs et ne détecte pas les superpositions entre objets de couches différentes"
    )

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

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

        doublons = []
        features = list(layer.getFeatures())
        for i, f1 in enumerate(features):
            if not f1.geometry().isGeosValid():
                continue

            for f2 in features[i + 1:]:
                if not f2.geometry().isGeosValid():
                    continue

                intersection = f1.geometry().intersection(f2.geometry())

                if not intersection.isEmpty() and intersection.type() == QgsWkbTypes.LineGeometry:
                    if intersection.length() > 0:
                        doublons.append([
                            "Doublons partiels linéaire",
                            layer.name(),
                            f1.id(),
                            "geometry",
                            'Doublon partiel linéaire',
                            intersection.pointOnSurface()
                        ])

        self.report_issues(doublons, "Doublons linéaires")

        return self.processing_done_result()
