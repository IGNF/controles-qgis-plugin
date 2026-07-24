from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class SurfaceIntersectionAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorPolygon
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

        intersection_features = []
        for layer in layers:
            if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
                feedback.reportError("{} n'est pas une couche surfacique".format(layer.name()))
                continue

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

                    # Vérifier si les géométries s'intersectent
                    if geom1.intersects(geom2):
                        intersection = geom1.intersection(geom2)

                        # Ne conserver que les intersections surfaciques (pas les contacts de bord)
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
            controlpoint_layer.save()

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