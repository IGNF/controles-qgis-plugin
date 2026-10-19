from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsGeometry
)

from BaseControlAlgorithm import BaseControlAlgorithm


class RouteContinuityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'L.01'
    ALG_DISPLAY_NAME = "Continuité de l’Itinéraire FFR"
    ALG_GROUP = 'Controles des complexes et des liens'
    ALG_GROUP_ID = 'L'
    ALG_HELP = "Ce contrôle détecte toutes les discontinuités du graphe formé par les tronçons de route liés à chaque objet Itinéraire FFR."

    INPUT_LAYER = 'INPUT_LAYER'
    ATTRIBUTE_FIELD = 'ATTRIBUTE_FIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTRIBUTE_FIELD,
                self.tr('Attribut à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        attribute_field = self.parameterAsString(parameters, self.ATTRIBUTE_FIELD, context)

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
                        endpoint_geom = QgsGeometry.fromPoint(vertices[0])
                    else:
                        endpoint_geom = QgsGeometry.fromPoint(vertices[-1])

                    invalid_objects.append([
                        'Continuité de l’Itinéraire FFR',
                        layer.name(),
                        feature.id(),
                        attribute_field,
                        'Discontinuité de l’Itinéraire FFR',
                        endpoint_geom
                    ])

        self.report_issues(invalid_objects, "Continuité de l'Itinéraire FFR")

        return self.processing_done_result()
