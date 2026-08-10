from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
)
from ControlPointLayer import ControlPointLayer

class ExternalHoleAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couche de route en entrée",
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

        issues = []
        for layer in layers:
            geom_type = layer.geometryType()
            if geom_type != QgsWkbTypes.PolygonGeometry:
                feedback.reportError(f"La couche {layer.name()} n'est pas surfacique")
                continue

                for feature in layer.getFeatures():
                    if feature.geometry().isEmpty() or not feature.geometry().isGeosValid():
                        continue

                    geom = feature.geometry()

                    # Vérifier les multi-surfaces (surfaces composées de polygones disjoints)
                    if geom.isMultipart():
                        parts = geom.asMultiPolygon()
                        if len(parts) > 1:
                            # Vérifier si les parties sont disjointes
                            are_disjoint = True
                            for i in range(len(parts)):
                                for j in range(i + 1, len(parts)):
                                    poly_i = QgsGeometry.fromPolygonXY(parts[i])
                                    poly_j = QgsGeometry.fromPolygonXY(parts[j])
                                    if poly_i.intersects(poly_j):
                                        are_disjoint = False
                                        break
                                if not are_disjoint:
                                    break

                            if are_disjoint:
                                issues.append([
                                    'Recherche des trous externes',
                                    layer.name(),
                                    feature.id(),
                                    'geometry',
                                    'La surface a des trous externes',
                                    geom.centroid()
                                ])
                    else:
                        # Traiter les polygones simples
                        polygon = geom.asPolygon()

                        if len(polygon) > 1:
                            # Il y a des trous (rings intérieurs)
                            exterior_ring = QgsGeometry.fromPolygonXY([polygon[0]])

                            for ring_idx in range(1, len(polygon)):
                                interior_ring = polygon[ring_idx]

                                # Vérifier si le trou a seulement 3 points (polygone plat)
                                if len(interior_ring) == 4:  # 4 points car le dernier = le premier
                                    ring_geom = QgsGeometry.fromPolygonXY([interior_ring])
                                    if ring_geom.area() < 0.0001:  # Seuil pour polygone plat
                                        issues.append([
                                            'Recherche des trous externes',
                                            layer.name(),
                                            feature.id(),
                                            'geometry',
                                            'La surface a des trous externes',
                                            ring_geom.centroid()
                                        ])
                                        continue

                                # Vérifier si le trou est à l'extérieur de la surface
                                ring_geom = QgsGeometry.fromPolygonXY([interior_ring])
                                ring_centroid = ring_geom.centroid()

                                if not exterior_ring.contains(ring_centroid):
                                    issues.append([
                                        'Recherche des trous externes',
                                        layer.name(),
                                        feature.id(),
                                        'geometry',
                                        'La surface a des trous externes',
                                        ring_centroid
                                    ])

            if issues:
                controlpoint_layer = ControlPointLayer('Recherche des trous externes')
                controlpoint_layer.add_features(issues)
                controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.13'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Recherche des trous externes"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte toutes les surfaces trouées incohérentes ou suspectes"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return ExternalHoleAlgorithm()