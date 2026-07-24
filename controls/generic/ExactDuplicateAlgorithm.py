from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class ExactDuplicateAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context):
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)

        doublons = []
        for layer in layers:
            geom_dict = {}
            for f in layer.getFeatures():
                if not f.geometry().isGeosValid():
                    continue
                geom = f.geometry().asWkt()
                if geom in geom_dict.keys():
                    doublon = True
                    for att in f.attributes():
                        if f[att] != geom_dict[geom][att]:
                            doublon = False
                            break
                    if doublon:
                        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
                        if geom_type == QgsWkbTypes.PointGeometry:
                            doublon_type = "Doublons ponctuels parfaits"
                        elif geom_type == QgsWkbTypes.LineGeometry:
                            doublon_type = "Doublons linéaires parfaits"
                        elif geom_type == QgsWkbTypes.PolygonGeometry:
                            doublon_type = "Doublons surfaciques parfaits"
                        else:
                            doublon_type = "Doublons parfaits"
                        doublons.append(['Doublons parfaits',
                                         layer.name(),
                                         geom_dict[geom].id(),
                                         'geometry',
                                         doublon_type,
                                         f.geometry().centroid()])
                else:
                    geom_dict[geom] = f
        if doublons != []:
            controlpoint_layer = ControlPointLayer('Doublons parfaits')
            controlpoint_layer.add_features(doublons)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.05'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Doublons parfaits"

    def group(self):
        """Nom du groupe"""
        return 'controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Ce contrôle détecte des objets de même couche ayant exactement les mêmes attributs et la même géométrie"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return ExactDuplicateAlgorithm()