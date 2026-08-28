from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsProcessingParameterNumber,
QgsWkbTypes,
QgsSpatialIndex
)
from ControlPointLayer import ControlPointLayer

class LinearProximityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'DISTANCE',
                'Distance de proximité (mètres)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=0.0
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
        distance = self.parameterAsDouble(parameters, 'DISTANCE', context)

        proximity_issues = []
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"La couche {layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

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
                        'geometr',
                        '',
                        geom.centroid()
                    ])

        if proximity_issues:
            controlpoint_layer = ControlPointLayer('Proximité des linéaires')
            controlpoint_layer.add_features(proximity_issues)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.21'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Proximité des linéaires"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle a pour but de détecter les objets linéaires situés à proximité immédiate d’un objet linéaire"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return LinearProximityAlgorithm()