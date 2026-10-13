from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsGeometry,
)
from ControlPointLayer import ControlPointLayer

class ExternalHoleAlgorithm(QgsProcessingAlgorithm):

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

        issues = []
        geom_type = layer.geometryType()
        if geom_type != QgsWkbTypes.PolygonGeometry:
            feedback.reportError(f"La couche {layer.name()} n'est pas surfacique")
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isEmpty():
                continue

            if geom.isMultipart():
                polygons = geom.asMultiPolygon()
            else:
                polygons = [geom.asPolygon()]

            # 1. Multi-surfaces : surface composée de plusieurs polygones disjoints
            if len(polygons) > 1:
                parts_geom = [QgsGeometry.fromPolygonXY(part) for part in polygons]
                are_disjoint = True
                for i in range(len(parts_geom)):
                    for j in range(i + 1, len(parts_geom)):
                        if parts_geom[i].intersects(parts_geom[j]):
                            are_disjoint = False
                            break
                    if not are_disjoint:
                        break

                if not are_disjoint:
                    issues.append([
                        'Recherche des trous externes',
                        layer.name(),
                        feature.id(),
                        'geometry',
                        'La surface est composée de plusieurs polygones disjoints (multi-surface)',
                        geom.pointOnSurface()
                    ])

            # 2. & 3. Analyse des trous (anneaux intérieurs) de chaque partie
            for polygon in polygons:
                if len(polygon) <= 1:
                    continue  # pas de trou dans cette partie

                exterior_ring = QgsGeometry.fromPolygonXY([polygon[0]])

                for ring_idx in range(1, len(polygon)):
                    interior_ring = polygon[ring_idx]
                    ring_geom = QgsGeometry.fromPolygonXY([interior_ring])

                    # Trou défini par seulement 3 points (le 4e point ferme
                    # l'anneau) formant un polygone plat, difficile à voir
                    if len(interior_ring) <= 4:
                        issues.append([
                            'Recherche des trous externes',
                            layer.name(),
                            feature.id(),
                            'geometry',
                            "Le trou est défini par seulement trois points et forme un polygone plat",
                            ring_geom.pointOnSurface()
                        ])
                        continue

                    # Trou apparaissant à l'extérieur de la surface
                    ring_centroid = ring_geom.pointOnSurface()
                    if not exterior_ring.contains(ring_centroid):
                        issues.append([
                            'Recherche des trous externes',
                            layer.name(),
                            feature.id(),
                            'geometry',
                            "Le trou apparaît à l'extérieur de la surface",
                            ring_centroid
                        ])

        if issues:
            controlpoint_layer = ControlPointLayer('Recherche des trous externes')
            controlpoint_layer.add_features(issues)
            controlpoint_layer.save_as_temp_layer()

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