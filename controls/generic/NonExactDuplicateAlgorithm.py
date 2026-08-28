from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsSpatialIndex,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class NonExactDuplicateAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self, config=None):
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

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)

        duplicates = []
        duplicates.extend(self._detect_exact_overlaps_cross_layer(layers, feedback))

        duplicates.extend(self._detect_partial_overlaps_same_layer(layers, feedback))

        # Créer la couche de points de contrôle si des doublons sont détectés
        if duplicates:
            controlpoint_layer = ControlPointLayer('Doublons')
            controlpoint_layer.add_features(duplicates)
            controlpoint_layer.save_as_temp_layer()

        return {self.OUTPUT: 'Traitement terminé'}

    def _detect_exact_overlaps_cross_layer(self, layers, feedback):
        """Détecte les superpositions géométriques exactes entre couches différentes"""
        duplicates = []

        for i, layer1 in enumerate(layers):
            if feedback.isCanceled():
                break

            for layer2 in layers[i + 1:]:
                # Comparer uniquement les couches différentes
                if layer1.name() == layer2.name():
                    continue

                # Créer un index spatial pour layer2
                spatial_index = QgsSpatialIndex(layer2.getFeatures())

                for f1 in layer1.getFeatures():
                    if not f1.geometry().isGeosValid():
                        continue

                    # Rechercher les candidats proches
                    candidate_ids = spatial_index.intersects(f1.geometry().boundingBox())

                    for fid2 in candidate_ids:
                        f2 = layer2.getFeature(fid2)
                        if not f2.geometry().isGeosValid():
                            continue

                        # Vérifier si les géométries sont exactement égales
                        if f1.geometry().equals(f2.geometry()):
                            duplicates.append([
                                'Doublons',
                                layer1.name(),
                                f1.id(),
                                'geometry',
                                "Doublon surfacique partiel",
                                f1.geometry().pointOnSurface()
                            ])

        return duplicates

    def _detect_partial_overlaps_same_layer(self, layers, feedback):
        """Détecte les chevauchements partiels entre surfaces de même couche"""
        duplicates = []
        total_layers = len(layers)

        for idx, layer in enumerate(layers):

            # Uniquement pour les couches surfaciques
            if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
                continue

            # Créer un index spatial
            spatial_index = QgsSpatialIndex(layer.getFeatures())
            features = list(layer.getFeatures())
            for i, f1 in enumerate(features):
                if not f1.geometry().isGeosValid():
                    continue
                candidate_ids = spatial_index.intersects(f1.geometry().boundingBox())
                for fid2 in candidate_ids:
                    if fid2 <= f1.id():
                        continue
                    f2 = layer.getFeature(fid2)
                    if not f2.geometry().isGeosValid():
                        continue

                    # Vérifier s'il y a un chevauchement (overlap)
                    if f1.geometry().overlaps(f2.geometry()):
                        intersection = f1.geometry().intersection(f2.geometry())
                        duplicates.append([
                            'Doublons',
                            layer.name(),
                            f1.id(),
                            'geometry',
                            "Doublon surfacique partiel",
                            f1.geometry().pointOnSurface()
                        ])

        return duplicates

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.07'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Doublons"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte : "\
            "les objets linéaires, surfaciques et ponctuels en superposition géométrique exacte avec d’autres objets de couches différentes."\
            "les surfaces de même couches se chevauchant entre elles."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NonExactDuplicateAlgorithm()