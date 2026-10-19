from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterDistance,
    QgsSpatialIndex,
    QgsFeature
)

from BaseControlAlgorithm import BaseControlAlgorithm


class BuildingResidentialZoneProximityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'F.04'
    ALG_DISPLAY_NAME = "Proximité Bâti / Zone d'habitation"
    ALG_GROUP = 'Controles du thème Bati'
    ALG_GROUP_ID = 'F'
    ALG_HELP = (
        "Ce contrôle détecte les objets Zone d'habitation de Nature = ‘Lieu-dit habité’ ou ‘Quartier’, d’Importance différente de ‘6’ ou dont le toponyme ne contient pas 'Commune', qui ne sont pas à moins de 250 m d'un objet Bâti / Bâtiment."
        "Il détecte également les objets Zone d'habitation de Nature = ‘Ruines’ qui ne sont pas à moins de 250 m d'un objet Construction linéaire de Nature = ‘Ruines’. Le contrôle est placé sur les objets incriminés."
    )

    RESIDENTIAL_ZONE_LAYER = 'RESIDENTIAL_ZONE_LAYER'
    BUILDING_LAYERS = 'BUILDING_LAYERS'
    DISTANCE = 'DISTANCE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.RESIDENTIAL_ZONE_LAYER,
                self.tr("Couche Zone d'habitation"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.BUILDING_LAYERS,
                self.tr("Couches Bâti / Bâtiment et Construction linéaire"),
                layerType=QgsProcessing.TypeVector
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.PARAM_JSON,
                self.tr('Paramètres JSON'),
                extension='json'
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                self.tr('Distance de proximité (m)'),
                defaultValue=250,
                parentParameterName=self.RESIDENTIAL_ZONE_LAYER,
                minValue=0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        residential_layer = self.parameterAsVectorLayer(parameters, self.RESIDENTIAL_ZONE_LAYER, context)
        input_layers = self.parameterAsLayerList(parameters, self.BUILDING_LAYERS, context)
        json_path = self.parameterAsFile(parameters, self.PARAM_JSON, context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        param_json = self.load_json_parameters(json_path)

        residential_params = self.get_layer_json_parameters(param_json, residential_layer, feedback)
        if residential_params is None:
            return self.processing_done_result()

        for building_layer in input_layers:
            params = self.get_layer_json_parameters(param_json, building_layer, feedback)
            if params is None:
                return self.processing_done_result()

        # Index spatial pour la recherche des Bâti / Bâtiment les plus proches
        building_index, building_features = self._build_index(building_layer)

        issues = []

        for zone in residential_layer.getFeatures():
            for [attribute,operator,value] in residential_params:
                if not zone.attributes(attribute)+str(operator)+str(value):
                    continue

            for building in building_features:
                for [attribute,operator,value] in params:
                    if not building.attributes(attribute)+str(operator)+str(value):
                        continue
                    if not self._has_feature_within_distance(zone.geometry(), building_index, building_features, distance):
                        issues.append([
                            "Proximité Bâti / Zone d'habitation",
                            residential_layer.name(),
                            zone.id(),
                            'geometry',
                            "Pas de Bâtiment à moins de {}m de la Zone d'habitation".format(distance),
                            zone.geometry().pointOnSurface()
                        ])
        self.report_issues(issues)

        return self.processing_done_result()

    @staticmethod
    def _build_index(layers, feature_filter=None):
        """
        Construit un index spatial à partir d'une ou plusieurs couches, en gérant
        les éventuelles collisions d'identifiants entre couches.
        Retourne (index, {id_unique: feature}).
        """
        spatial_index = QgsSpatialIndex()
        features_dict = {}
        counter = 0
        for layer in layers:
            for feature in layer.getFeatures():
                if feature_filter is not None and not feature_filter(feature):
                    continue
                geom = feature.geometry()
                if geom is None or geom.isEmpty():
                    continue
                indexed_feature = QgsFeature(feature)
                indexed_feature.setId(counter)
                spatial_index.addFeature(indexed_feature)
                features_dict[counter] = feature
                counter += 1
        return spatial_index, features_dict

    @staticmethod
    def _has_feature_within_distance(geom, spatial_index, features_dict, distance):
        """Vérifie si un objet indexé est à moins de `distance` mètres de `geom`."""
        candidate_ids = spatial_index.nearestNeighbor(geom, 5, distance)
        for fid in candidate_ids:
            candidate = features_dict.get(fid)
            if candidate is None:
                continue
            candidate_geom = candidate.geometry()
            if candidate_geom is None or candidate_geom.isEmpty():
                continue
            if geom.distance(candidate_geom) < distance:
                return True
        return False
