from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsSpatialIndex,
QgsWkbTypes,
QgsProcessingParameterFile,
QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer
import json


class RoadSectionWaterSurfaceIntersectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'ROAD_LAYER',
                "Couche de route en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'WATER_LAYER',
                "Couche de surface d'eau en entrée",
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                'PARAM_JSON',
                'Paramètres JSON',
                extension='json'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        road_layer = self.parameterAsVectorLayer(parameters, 'ROAD_LAYER', context)
        water_layer = self.parameterAsVectorLayer(parameters, 'WATER_LAYER', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        # param_json : {'couche': ['attribut1', 'attribut2', ...], ...}
        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

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
                                                road_feature.geometry().centroid()])
                elif road_feature.geometry().intersects(water_feature.geometry()):
                    intersection_geom = road_feature.geometry().intersection(water_feature.geometry())
                    intersect_features.append(['Intersection de tronçons de route avec des surfaces d’eau',
                                               f"{road_layer.name()} / {water_layer.name()}",
                                               f"{road_feature.id()} / {water_feature.id()}",
                                               'geometry',
                                                'Ce tronçon de route traverse une surface hydrographique',
                                                intersection_geom.centroid()])
        if intersect_features != []:
            controlpoint_layer = ControlPointLayer('Intersection de tronçons de route avec des surfaces d’eau')
            controlpoint_layer.add_features(intersect_features)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.18'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Intersection de tronçons de route avec des surfaces d’eau"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les tronçons de route traversant des surfaces hydrographiques permanentes et "\
            "les tronçons de route inclus dans ces mêmes surfaces"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return RoadSectionWaterSurfaceIntersectionAlgorithm()