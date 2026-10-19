from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessing
)

from BaseControlAlgorithm import BaseControlAlgorithm


class ZMaxAltitudeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'B.07'
    ALG_DISPLAY_NAME = "Altitudes hors norme"
    ALG_GROUP = 'Controles génériques Z'
    ALG_GROUP_ID = 'B'
    ALG_HELP = "Vérifie le Z maximal de la géométrie de l'objet ne dépasse pas une certaine valeur"

    INPUT_LAYER = 'INPUT_LAYER'
    MAX_ALTITUDE = 'MAX_ALTITUDE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ALTITUDE,
                self.tr('Altitude maximale autorisée (m)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=-100
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        max_altitude = self.parameterAsDouble(parameters, self.MAX_ALTITUDE, context)

        invalid_objects = []

        for feature in layer.getFeatures():
            geom = feature.geometry()

            if geom.isEmpty() or not geom.isGeosValid():
                continue

            # Récupérer tous les Z de la géométrie
            z_values = []
            vertices = geom.vertices()

            while vertices.hasNext():
                vertex = vertices.next()
                if vertex.z() is not None and vertex.z() == vertex.z():  # Exclure NaN
                    z_values.append(vertex.z())

            if not z_values:
                continue

            # Vérifier si le Z maximal dépasse la valeur autorisée
            z_max = max(z_values)
            if z_max > max_altitude:
                invalid_objects.append([
                    'Altitudes hors norme',
                    layer.name(),
                    feature.id(),
                    'geometrie',
                    '{} avec Z > {}m'.format(layer.name(), max_altitude),
                    feature.geometry().pointOnSurface()
                ])

        self.report_issues(invalid_objects, 'Altitudes hors norme')

        return self.processing_done_result()
