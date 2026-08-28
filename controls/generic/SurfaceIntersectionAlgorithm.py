from qgis.core import (
QgsProcessingAlgorithm,
 QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class SurfaceIntersectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorPolygon]
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

        intersection_features = []
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            feedback.reportError("{} n'est pas une couche surfacique".format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

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
                            feature1.id(),
                            "geometry",
                            "Intersection franche",
                            intersection.centroid()
                        ])

        if intersection_features != []:
            controlpoint_layer = ControlPointLayer('Intersection de surfaciques')
            controlpoint_layer.add_features(intersection_features)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.12'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Intersections de surfaciques"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométrique'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Ce contrôle détecte les intersections entre les objets d’une même classe."\
               "Le contrôle est positionné sur la ou les intersections entre les objets."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return SurfaceIntersectionAlgorithm()