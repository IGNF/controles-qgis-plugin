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


class ZMaxAltitudeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'PYLON_LAYER',
                "Couche de pylones",
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'LINE_LAYER',
                "Couche de lignes électriques",
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
            QgsProcessingParameterEnum(
                'ATTRIBUTE_VALUES',
                'Valeurs à contrôler',
                options=[],
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        pylon_layer = self.parameterAsVectorLayer(parameters, 'PYLON_LAYER', context)
        line_layer = self.parameterAsVectorLayer(parameters, 'LINE_LAYER', context)
        distance_threshold = self.parameterAsDouble(parameters, 'DISTANCE_THRESHOLD', context)
        attribute_field = self.parameterAsString(parameters, 'ATTRIBUTE_FIELD', context)
        attribute_values = self.parameterAsEnums(parameters, 'ATTRIBUTE_VALUES', context)

        invalid_objects = []

        # Extraire tous les points intermédiaires des lignes électriques
        intermediate_points = []
        for line_feature in line_layer.getFeatures():
            geom = line_feature.geometry()
            if geom.isEmpty():
                continue

            vertices = list(geom.vertices())
            for vertex in vertices[1:-1]:
                intermediate_points.append((QgsPoint(vertex), line_feature))

        # Créer un index spatial pour les points intermédiaires
        spatial_index = QgsSpatialIndex()
        intermediate_dict = {}
        for idx, (point, line_feature) in enumerate(intermediate_points):
            point_geom = QgsGeometry.fromPointXY(point)
            spatial_index.addFeature(idx, point_geom.boundingBox())
            intermediate_dict[idx] = (point, line_feature)

        # Vérifier chaque pylône (contrôles a, b, c)
        for pylon_feature in pylon_layer.getFeatures():
            pylon_geom = pylon_feature.geometry()
            if pylon_geom.isEmpty():
                continue

            pylon_point = pylon_geom.asPoint()
            acquisition_method = pylon_feature.get(attribute_field, '')

            # Trouver les points intermédiaires proches
            nearby_ids = spatial_index.nearestNeighbor(pylon_point, 1)

            if nearby_ids:
                nearest_id = nearby_ids[0]
                nearest_point, nearest_line = intermediate_dict[nearest_id]
                distance = pylon_point.distance(nearest_point.x(), nearest_point.y())

                # Contrôle a) : Z différent si superposés et acquisition photogrammétrique
                if distance < 0.01 and acquisition_method in attribute_values:
                    if pylon_point.z() is not None and nearest_point.z() is not None:
                        if abs(pylon_point.z() - nearest_point.z()) > 0.01:
                            invalid_objects.append([
                                "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique",
                                pylon_layer.name(),
                                pylon_feature.id(),
                                'geometrie',
                                'Le Z du pylône est différent du Z du point intermédiaire de la ligne électrique',
                                pylon_geom
                            ])

                # Contrôle b) : Non superposé mais < 10m
                elif distance < distance_threshold:
                    invalid_objects.append([
                        "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique",
                        pylon_layer.name(),
                        pylon_feature.id(),
                        'geometrie',
                        "Le pylône est situé à moins de 10 m du point intermédiaire le plus proche de la ligne électrique",
                        pylon_geom
                    ])

            # Contrôle c) : Pylône sans point intermédiaire dans un rayon de 10m
            has_nearby_intermediate = False
            for idx, (inter_point, _) in intermediate_dict.items():
                distance = pylon_point.distance(inter_point.x(), inter_point.y())
                if distance <= distance_threshold:
                    has_nearby_intermediate = True
                    break

            if not has_nearby_intermediate:
                invalid_objects.append([
                    "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique",
                    pylon_layer.name(),
                    pylon_feature.id(),
                    'geometrie',
                    "Le pylône n'est pas rattaché à un point intermédiaire de la ligne électrique",
                    pylon_geom
                ])

        # Contrôle d) : Points intermédiaires sans pylône dans un rayon de 10m
        for idx, (inter_point, line_feature) in intermediate_dict.items():
            has_nearby_pylon = False
            for pylon_feature in pylon_layer.getFeatures():
                pylon_geom = pylon_feature.geometry()
                if pylon_geom.isEmpty():
                    continue
                pylon_point = pylon_geom.asPoint()
                distance = pylon_point.distance(inter_point.x(), inter_point.y())

                if distance <= distance_threshold:
                    has_nearby_pylon = True
                    break

            if not has_nearby_pylon:
                invalid_objects.append([
                    "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique",
                    line_layer.name(),
                    line_feature.id(),
                    'geometrie',
                    "Le point intermédiaire de la ligne électrique n'a pas de pylône situé à moins de 10 m",
                    QgsGeometry.fromPointXY(inter_point)
                ])

        if invalid_objects:
            controlpoint_layer = ControlPointLayer("Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique")
            controlpoint_layer.add_features(invalid_objects)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'H.01'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique"

    def group(self):
        """Nom du groupe"""
        return 'Controles sur le réseau électrique'

    def groupId(self):
        """Identifiant du groupe"""
        return 'H'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte :"\
"parmi les pylônes dont le champ Méthode d’acquisition altimétrique est égal à ‘Photogrammétrie’ ou ‘Photogrammétrie longue focale’, ceux dont le Z est différent du Z du point intermédiaire de la ligne électrique"\
"les pylônes non superposés à un point intermédiaire de la ligne électrique et situés à une distance inférieure à 10 m de celui-ci"\
"les pylônes non superposés à un point intermédiaire de la ligne électrique et situés à une distance supérieure à 10 m de celui-ci"\
"les points intermédiaires des lignes électriques n’ayant pas de pylône dans un rayon de 10 m"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return ZMaxAltitudeAlgorithm()