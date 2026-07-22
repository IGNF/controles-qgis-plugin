from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFeatureSink,
    QgsWkbTypes
)
from ..ControlPointLayer import ControlPointLayer


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
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)

        doublons = []
        for layer in layers:
            geom_type = QgsWkbTypes.geometryType(layer.wkbType())
            if geom_type != QgsWkbTypes.LineGeometry:
                feedback.reportError(f"{layer.name()} n'est pas linéaire")
                continue

            geom_dict = {}
            for f in layer.getFeatures():
                if not f.geometry().isGeosValid():
                    continue

                geom_wkt = f.geometry().asWkt()

                if geom_wkt in geom_dict:
                    doublons.append([
                        "Doublons linéaires",
                        layer.name(),
                        geom_dict[geom_wkt].id(),
                        "geometry",
                        f"Doublon linéaire détecté (géométrie commune avec l'entité {geom_dict[geom_wkt].id()})",
                        f.geometry().centroid()
                    ])
                else:
                    geom_dict[geom_wkt] = f

        if doublons:
            controlpoint_layer = ControlPointLayer("Doublons linéaires")
            controlpoint_layer.add_features(doublons)
            controlpoint_layer.save()

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