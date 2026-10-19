from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
    QgsSpatialIndex
)

from BaseControlAlgorithm import BaseControlAlgorithm


class LinearProximityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.21'
    ALG_DISPLAY_NAME = "Proximité des linéaires"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = "Ce contrôle a pour but de détecter les objets linéaires situés à proximité immédiate d’un objet linéaire"

    INPUT_LAYER = 'INPUT_LAYER'
    DISTANCE = 'DISTANCE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                self.tr('Distance de proximité (mètres)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        proximity_issues = []
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("La couche {} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

        spatial_index = QgsSpatialIndex()
        features_dict = {}

        for feature in layer.getFeatures():
            if feature.geometry().isEmpty() or feature.geometry().isGeosValid() is False:
                continue
            spatial_index.addFeature(feature)
            features_dict[feature.id()] = feature

        for feature_id, feature in features_dict.items():
            geom = feature.geometry()
            search_rect = geom.boundingBox()
            search_rect.grow(distance)
            candidate_ids = spatial_index.intersects(search_rect)
            for candidate_id in candidate_ids:
                if candidate_id == feature_id:
                    continue
                candidate_feature = features_dict[candidate_id]
                candidate_geom = candidate_feature.geometry()
                actual_distance = geom.distance(candidate_geom)
                if 0 < actual_distance <= distance:
                    proximity_issues.append([
                        'Proximité des linéaires',
                        layer.name(),
                        feature.id(),
                        'geometry',
                        '',
                        geom.centroid()
                    ])

        self.report_issues(proximity_issues, 'Proximité des linéaires')

        return self.processing_done_result()
