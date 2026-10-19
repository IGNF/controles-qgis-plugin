from qgis.core import (
    QgsProcessingParameterMultipleLayers,
    QgsProcessing,
    QgsSpatialIndex,
    QgsWkbTypes
)

from BaseControlAlgorithm import BaseControlAlgorithm


class NonExactDuplicateAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.07'
    ALG_DISPLAY_NAME = "Doublons"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte : "
        "les objets linéaires, surfaciques et ponctuels en superposition géométrique exacte avec d’autres objets de couches différentes."
        "les surfaces de même couches se chevauchant entre elles."
    )

    INPUT_LAYERS = 'INPUT_LAYERS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr("Couches en entrée"),
                layerType=QgsProcessing.TypeVectorAnyGeometry
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)

        duplicates = []
        duplicates.extend(self._detect_exact_overlaps_cross_layer(layers, feedback))

        duplicates.extend(self._detect_partial_overlaps_same_layer(layers, feedback))

        self.report_issues(duplicates, 'Doublons')

        return self.processing_done_result()

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
