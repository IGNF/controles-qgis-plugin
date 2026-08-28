from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFile,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsSpatialIndex,
QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer
import json


class IsolatedSectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
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
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        isolated_sections = []

        if layer.name() not in param_json.keys():
            feedback.reportError('{} not in param.json'.format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

        filter_condition = param_json[layer.name()]

        spatial_index = QgsSpatialIndex()
        features_dict = {}

        request = QgsFeatureRequest()
        if filter_condition:
            request.setFilterExpression(filter_condition)

        for f in layer.getFeatures(request):
            if not f.geometry() or not f.geometry().isGeosValid():
                continue
            features_dict[f.id()] = f
            spatial_index.addFeature(f)

        for fid, feature in features_dict.items():
            geom = feature.geometry()
            bbox = geom.boundingBox()
            bbox.grow(0.01)
            nearby_ids = spatial_index.intersects(bbox)
            is_isolated = True
            for nearby_id in nearby_ids:
                if nearby_id == fid:
                    continue
                nearby_feature = features_dict[nearby_id]
                nearby_geom = nearby_feature.geometry()
                if geom.touches(nearby_geom) or geom.intersects(nearby_geom):
                    is_isolated = False
                    break
            if is_isolated:
                isolated_sections.append([
                    'Géométrie tronçons isolés',
                    layer.name(),
                    feature.id(),
                    'geometry',
                    "Ce tronçon est isolé",
                    geom.centroid()
                ])

        if isolated_sections:
            controlpoint_layer = ControlPointLayer('Géométrie tronçons isolés')
            controlpoint_layer.add_features(isolated_sections)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.17'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Géométrie tronçons isolés"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les tronçons isolés sur les réseaux routier, ferré et hydrographique."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return IsolatedSectionAlgorithm()