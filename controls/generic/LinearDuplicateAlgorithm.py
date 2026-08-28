from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class LinearDuplicateAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                "Sortie"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)

        doublons = []
        for layer in layers:
            geom_type = QgsWkbTypes.geometryType(layer.wkbType())
            if geom_type != QgsWkbTypes.LineGeometry:
                feedback.reportError(f"{layer.name()} n'est pas linéaire")
                continue

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
                                intersection.centroid()
                            ])

        if doublons:
            controlpoint_layer = ControlPointLayer("Doublons linéaires")
            controlpoint_layer.add_features(doublons)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.06'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Doublons partiels linéaires"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Ce contrôle détecte des objets linéaires de même couche ayant une géométrie commune."\
               "Il ne tient pas compte des attributs et ne détecte pas les superpositions entre objets de couches différentes"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return LinearDuplicateAlgorithm()