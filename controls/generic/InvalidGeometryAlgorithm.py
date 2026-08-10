from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink
)
from ControlPointLayer import ControlPointLayer

class InvalidGeometryAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couche de route en entrée",
                layerType=QgsProcessing.TypeVector
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)

        invalid_geometries = []
        for layer in layers:
            for feature in layer.getFeatures():
                geom = feature.geometry()

                if geom.isEmpty():
                    continue

                if not geom.isGeosValid():
                    error = geom.validateGeometry()

                    if error:
                        for e in error:
                            # Utiliser la position de l'erreur si disponible
                            error_location = e.where() if e.hasWhere() else geom.centroid()

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

        if invalid_geometries:
            controlpoint_layer = ControlPointLayer('Géométrie invalide')
            controlpoint_layer.add_features(invalid_geometries)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.16'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Géométrie invalide"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Vérifie que la géométrie est valide"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return InvalidGeometryAlgorithm()