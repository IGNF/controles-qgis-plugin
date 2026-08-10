from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
)
from ControlPointLayer import ControlPointLayer

class SelfIntersectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couche de route en entrée",
                layerType=QgsProcessing.TypeVectorLine|QgsProcessing.TypeVectorPolygon
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

        self_intersection_issues = []
        for layer in layers:
            geom_type = layer.geometryType()
            if geom_type not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
                feedback.reportError(f"La couche {layer.name()} n'est ni linéaire ni surfacique")
                continue

            for feature in layer.getFeatures():
                if feature.geometry().isEmpty() or not feature.geometry().isGeosValid():
                    continue

                geom = feature.geometry()

                # Vérifier si la géométrie s'auto-intersecte
                if not geom.isSimple():
                    self_intersection_issues.append([
                        'Auto-intersection',
                        layer.name(),
                        feature.id(),
                        'geometry',
                        'Objet auto-intersectant',
                        geom.centroid()
                    ])

        if self_intersection_issues:
            controlpoint_layer = ControlPointLayer('Auto-intersections')
            controlpoint_layer.add_features(self_intersection_issues)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.10'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Auto-intersections"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les objets s’intersectant eux-mêmes. "

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return SelfIntersectionAlgorithm()