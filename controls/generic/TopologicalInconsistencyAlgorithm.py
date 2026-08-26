from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsGeometry,
QgsPointXY
)
from ControlPointLayer import ControlPointLayer


class TopologicalInconsistencyAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                "Sortie"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)

        inconsistencies = []
        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

        features = list(layer.getFeatures())

        connected_endpoints = set()
        for f1 in features:
            if not f1.geometry().isGeosValid():
                continue
            start1 = f1.geometry().vertexAt(0)
            end1 = f1.geometry().vertexAt(f1.geometry().constGet().nCoordinates() - 1)
            for f2 in features:
                if f1.id() == f2.id() or not f2.geometry().isGeosValid():
                    continue
                start2 = f2.geometry().vertexAt(0)
                end2 = f2.geometry().vertexAt(f2.geometry().constGet().nCoordinates() - 1)
                if start1.distance(start2) < 0.001 or start1.distance(end2) < 0.001:
                    connected_endpoints.add((f1.id(), 'start'))
                if end1.distance(start2) < 0.001 or end1.distance(end2) < 0.001:
                    connected_endpoints.add((f1.id(), 'end'))

        for feature in features:
            if not feature.geometry().isGeosValid():
                continue
            geom = feature.geometry()
            start_point = geom.vertexAt(0)
            end_point = geom.vertexAt(geom.constGet().nCoordinates() - 1)
            if (feature.id(), 'start') not in connected_endpoints:
                start_geom = QgsGeometry.fromPointXY(QgsPointXY(start_point))
                buffer = start_geom.buffer(2.0, 8)
                for other_feature in features:
                    if feature.id() == other_feature.id() or not other_feature.geometry().isGeosValid():
                        continue
                    if buffer.intersects(other_feature.geometry()):
                        inconsistencies.append([
                            "Incohérences topologiques",
                            layer.name(),
                            feature.id(),
                            "geometry",
                            'Incohérence topologique détectée',
                            start_geom
                        ])
                        break
            if (feature.id(), 'end') not in connected_endpoints:
                end_geom = QgsGeometry.fromPointXY(QgsPointXY(end_point))
                buffer = end_geom.buffer(2.0, 8)
                for other_feature in features:
                    if feature.id() == other_feature.id() or not other_feature.geometry().isGeosValid():
                        continue
                    if buffer.intersects(other_feature.geometry()):
                        inconsistencies.append([
                            "Incohérences topologiques",
                            layer.name(),
                            feature.id(),
                            "geometry",
                            'Incohérence topologique détectée',
                            end_geom
                        ])
                        break

        if inconsistencies:
            controlpoint_layer = ControlPointLayer("Incohérences topologiques")
            controlpoint_layer.add_features(inconsistencies)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.09'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Incohérences topologiques"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Ce contrôle vérifie pour chaque graphe, que les extrémités de tronçon qui ne coïncident pas avec"\
               "l'extrémité d'un autre tronçon ne se trouvent pas à moins de 2 m d'un objet de même couche."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return TopologicalInconsistencyAlgorithm()