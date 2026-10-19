from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsSpatialIndex,
    QgsProcessingParameterFile,
    QgsFeatureRequest
)

from BaseControlAlgorithm import BaseControlAlgorithm


class RoadSectionWaterSurfaceIntersectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.18'
    ALG_DISPLAY_NAME = "Intersection de tronçons de route avec des surfaces d’eau"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte les tronçons de route traversant des surfaces hydrographiques permanentes et "
        "les tronçons de route inclus dans ces mêmes surfaces"
    )

    ROAD_LAYER = 'ROAD_LAYER'
    WATER_LAYER = 'WATER_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.ROAD_LAYER,
                self.tr("Couche de route en entrée"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.WATER_LAYER,
                self.tr("Couche de surface d'eau en entrée"),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.PARAM_JSON,
                self.tr('Paramètres JSON'),
                extension='json'
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        road_layer = self.parameterAsVectorLayer(parameters, self.ROAD_LAYER, context)
        water_layer = self.parameterAsVectorLayer(parameters, self.WATER_LAYER, context)
        json_path = self.parameterAsFile(parameters, self.PARAM_JSON, context)

        # param_json : {'couche': ['attribut1', 'attribut2', ...], ...}
        param_json = self.load_json_parameters(json_path)

        road_filters = param_json[road_layer.name()]
        water_filters = param_json[water_layer.name()]

        intersect_features = []

        road_request = QgsFeatureRequest()
        if road_filters:
            for filter in road_filters:
                road_request.setFilterExpression(filter)

        water_request = QgsFeatureRequest()
        if road_filters:
            for filter in water_filters:
                water_request.setFilterExpression(filter)

        water_index = QgsSpatialIndex(water_layer.getFeatures(water_request))

        for road_feature in road_layer.getFeatures(road_request):
            if not road_feature.geometry() or not road_feature.geometry().isGeosValid():
                continue
            candidate_ids = water_index.intersects(road_feature.geometry().boundingBox())

            for water_id in candidate_ids:
                water_feature = water_layer.getFeature(water_id)
                for condition in water_filters:
                    if ''.join(condition):
                        continue
                if not water_feature.geometry() or not water_feature.geometry().isGeosValid():
                    continue

                if road_feature.geometry().within(water_feature.geometry()):
                    intersect_features.append(['Intersection de tronçons de route avec des surfaces d’eau',
                                               f"{road_layer.name()} / {water_layer.name()}",
                                               f"{road_feature.id()} / {water_feature.id()}",
                                               'geometry',
                                                'Ce tronçon de route est inclus dans une surface hydrographique',
                                                road_feature.geometry().pointOnSurface()])
                elif road_feature.geometry().intersects(water_feature.geometry()):
                    intersection_geom = road_feature.geometry().intersection(water_feature.geometry())
                    intersect_features.append(['Intersection de tronçons de route avec des surfaces d’eau',
                                               f"{road_layer.name()} / {water_layer.name()}",
                                               f"{road_feature.id()} / {water_feature.id()}",
                                               'geometry',
                                                'Ce tronçon de route traverse une surface hydrographique',
                                                intersection_geom.centroid()])

        self.report_issues(intersect_features, 'Intersection de tronçons de route avec des surfaces d’eau')

        return self.processing_done_result()
