from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsGeometry
)

from BaseControlAlgorithm import BaseControlAlgorithm


class InvalidGeometryAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.16'
    ALG_DISPLAY_NAME = "Géométrie invalide"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = "Vérifie que la géométrie est valide"

    INPUT_LAYER = 'INPUT_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVector]
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)

        invalid_geometries = []
        for feature in layer.getFeatures():
            geom = feature.geometry()

            if geom.isEmpty():
                continue

            if not geom.isGeosValid():
                error = geom.validateGeometry()

                if error:
                    for e in error:
                        error_location = QgsGeometry.fromPointXY(e.where()) if e.hasWhere() else geom.centroid()
                        invalid_geometries.append([
                            'Géométrie invalide',
                            layer.name(),
                            feature.id(),
                            'geometrie',
                            e.what(),
                            error_location
                        ])
                else:
                    invalid_geometries.append([
                        'Géométrie invalide',
                        layer.name(),
                        feature.id(),
                        'geometrie',
                        'Géométrie invalide',
                        geom.centroid()
                    ])

        self.report_issues(invalid_geometries)

        return self.processing_done_result()
