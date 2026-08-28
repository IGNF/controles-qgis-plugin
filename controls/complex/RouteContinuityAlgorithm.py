from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsFeatureRequest,
QgsPoint,
QgsSpatialIndex,
QgsGeometry
)
from ControlPointLayer import ControlPointLayer


class RouteContinuityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'ATTRIBUTE_FIELD',
                'Attribut à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
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
        attribute_field = self.parameterAsString(parameters, 'ATTRIBUTE_FIELD', context)

        invalid_objects = []

        # Grouper les tronçons par valeur d'attribut
        groups = {}
        for feature in layer.getFeatures():
            attr_value = feature[attribute_field]
            if attr_value is None or attr_value == '':
                continue

            if attr_value not in groups:
                groups[attr_value] = []
            groups[attr_value].append(feature)

        # Vérifier la continuité pour chaque groupe
        for attr_value, features in groups.items():
            if len(features) < 2:
                continue

            # Créer un dictionnaire des extrémités
            endpoints = {}
            for feature in features:
                geom = feature.geometry()
                if geom.isEmpty():
                    continue

                # Récupérer le premier et dernier point
                vertices = list(geom.vertices())
                if len(vertices) < 2:
                    continue

                start_point = vertices[0]
                end_point = vertices[-1]

                start_key = (round(start_point.x(), 6), round(start_point.y(), 6))
                end_key = (round(end_point.x(), 6), round(end_point.y(), 6))

                if start_key not in endpoints:
                    endpoints[start_key] = []
                endpoints[start_key].append((feature, 'start'))

                if end_key not in endpoints:
                    endpoints[end_key] = []
                endpoints[end_key].append((feature, 'end'))

            # Détecter les extrémités isolées (discontinuités)
            for point_key, connections in endpoints.items():
                if len(connections) == 1:
                    feature, endpoint_type = connections[0]
                    geom = feature.geometry()
                    vertices = list(geom.vertices())

                    if endpoint_type == 'start':
                        endpoint_geom = QgsGeometry.fromPointXY(vertices[0])
                    else:
                        endpoint_geom = QgsGeometry.fromPointXY(vertices[-1])

                    invalid_objects.append([
                        'Continuité de l’Itinéraire FFR',
                        layer.name(),
                        feature.id(),
                        attribute_field,
                        'Discontinuité de l’Itinéraire FFR',
                        endpoint_geom
                    ])

        if invalid_objects:
            controlpoint_layer = ControlPointLayer("Continuité de l'Itinéraire FFR")
            controlpoint_layer.add_features(invalid_objects)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'L.01'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Continuité de l’Itinéraire FFR"

    def group(self):
        """Nom du groupe"""
        return 'Controles des complexes et des liens'

    def groupId(self):
        """Identifiant du groupe"""
        return 'L'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons de route liés à chaque objet Itinéraire FFR."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return RouteContinuityAlgorithm()