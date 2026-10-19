from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsPointXY,
    QgsSpatialIndex,
    QgsGeometry
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class PylonElectricLineInconsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'H.01'
    ALG_DISPLAY_NAME = "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique"
    ALG_GROUP = 'Controles sur le réseau électrique'
    ALG_GROUP_ID = 'H'
    ALG_HELP = (
        "Ce contrôle détecte :"
        "parmi les pylônes dont le champ Méthode d’acquisition altimétrique est égal à ‘Photogrammétrie’ ou ‘Photogrammétrie longue focale’, ceux dont le Z est différent du Z du point intermédiaire de la ligne électrique"
        "les pylônes non superposés à un point intermédiaire de la ligne électrique et situés à une distance inférieure à 10 m de celui-ci"
        "les pylônes non superposés à un point intermédiaire de la ligne électrique et situés à une distance supérieure à 10 m de celui-ci"
        "les points intermédiaires des lignes électriques n’ayant pas de pylône dans un rayon de 10 m"
    )

    PYLON_LAYER = 'PYLON_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    ATTRIBUTE_FIELD = 'ATTRIBUTE_FIELD'
    ATTRIBUTE_VALUES = 'ATTRIBUTE_VALUES'
    DISTANCE_THRESHOLD = 'DISTANCE_THRESHOLD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PYLON_LAYER,
                self.tr("Couche de pylones"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LINE_LAYER,
                self.tr("Couche de lignes électriques"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTRIBUTE_FIELD,
                self.tr('Attribut à vérifier'),
                parentLayerParameterName=self.PYLON_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ATTRIBUTE_VALUES,
                self.tr('Valeurs à contrôler'),
                parentLayerParameterName=self.PYLON_LAYER,
                parentFieldParameterName=self.ATTRIBUTE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE_THRESHOLD,
                self.tr('Distance seuil (m)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        pylon_layer = self.parameterAsVectorLayer(parameters, self.PYLON_LAYER, context)
        line_layer = self.parameterAsVectorLayer(parameters, self.LINE_LAYER, context)
        distance_threshold = self.parameterAsDouble(parameters, self.DISTANCE_THRESHOLD, context)
        attribute_field = self.parameterAsString(parameters, self.ATTRIBUTE_FIELD, context)

        # Valeurs sélectionnées dynamiquement via le widget (stockées en chaîne séparée par des virgules)
        raw_attribute_values = self.parameterAsString(parameters, self.ATTRIBUTE_VALUES, context)
        attribute_values = field_values_as_string_list(raw_attribute_values)

        invalid_objects = []

        # Extraire tous les points intermédiaires des lignes électriques
        intermediate_points = []
        for line_feature in line_layer.getFeatures():
            geom = line_feature.geometry()
            if geom.isEmpty():
                continue

            vertices = list(geom.vertices())
            for vertex in vertices[1:-1]:
                # geom.vertices() retourne déjà des QgsPoint : pas besoin de reconstruire
                intermediate_points.append((vertex, line_feature))

        # Créer un index spatial pour les points intermédiaires
        spatial_index = QgsSpatialIndex()
        intermediate_dict = {}
        for idx, (point, line_feature) in enumerate(intermediate_points):
            point_geom = QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))
            spatial_index.addFeature(idx, point_geom.boundingBox())
            intermediate_dict[idx] = (point, line_feature)

        # Vérifier chaque pylône (contrôles a, b, c)
        for pylon_feature in pylon_layer.getFeatures():
            pylon_geom = pylon_feature.geometry()
            if pylon_geom.isEmpty():
                continue

            pylon_point = pylon_geom.asPoint()
            if attribute_field and attribute_field in pylon_feature.fields().names():
                acquisition_method = str(pylon_feature[attribute_field])
            else:
                acquisition_method = ''

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
        flagged_line_ids = set()

        for idx, (inter_point, line_feature) in intermediate_dict.items():
            if line_feature.id() in flagged_line_ids:
                continue

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
                flagged_line_ids.add(line_feature.id())
                invalid_objects.append([
                    "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique",
                    line_layer.name(),
                    line_feature.id(),
                    'geometrie',
                    "Le point intermédiaire de la ligne électrique n'a pas de pylône situé à moins de 10 m",
                    QgsGeometry.fromPointXY(QgsPointXY(inter_point.x(), inter_point.y()))
                ])

        self.report_issues(invalid_objects, "Recherche d'incohérence géométrique entre pylône et point intermédiaire de la ligne éléctrique")

        return self.processing_done_result()
