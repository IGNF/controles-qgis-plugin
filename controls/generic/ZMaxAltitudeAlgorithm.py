from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer


class ZMaxAltitudeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'MAX_ALTITUDE',
                'Altitude maximale autorisée (m)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=-100
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
        max_altitude = self.parameterAsDouble(parameters, 'MAX_ALTITUDE', context)

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
                    feature.geometry().centroid()
                ])

        if invalid_objects:
            controlpoint_layer = ControlPointLayer('Altitudes hors norme')
            controlpoint_layer.add_features(invalid_objects)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'B.07'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Altitudes hors norme"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques Z'

    def groupId(self):
        """Identifiant du groupe"""
        return 'B'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Vérifie le Z maximal de la géométrie de l'objet ne dépasse pas une certaine valeur"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return ZMaxAltitudeAlgorithm()