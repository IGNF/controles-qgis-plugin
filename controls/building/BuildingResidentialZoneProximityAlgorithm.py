from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterDistance,
    QgsSpatialIndex,
    QgsWkbTypes,
    QgsFeature
)
from ControlPointLayer import ControlPointLayer
import json


class BuildingResidentialZoneProximity(QgsProcessingAlgorithm):


    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'F.04'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Proximité Bâti / Zone d'habitation"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Bati'

    def groupId(self):
        """Identifiant du groupe"""
        return 'F'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return (
            "Ce contrôle détecte les objets Zone d'habitation de Nature = ‘Lieu-dit habité’ ou ‘Quartier’, d’Importance différente de ‘6’ ou dont le toponyme ne contient pas 'Commune', qui ne sont pas à moins de 250 m d'un objet Bâti / Bâtiment."\
            "Il détecte également les objets Zone d'habitation de Nature = ‘Ruines’ qui ne sont pas à moins de 250 m d'un objet Construction linéaire de Nature = ‘Ruines’. Le contrôle est placé sur les objets incriminés."
        )

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return BuildingResidentialZoneProximity()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'RESIDENTIAL_ZONE_LAYER',
                "Couche Zone d'habitation",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'BUILDING_LAYERS',
                "Couches Bâti / Bâtiment et Construction linéaire",
                layerType=QgsProcessing.TypeVector
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
            QgsProcessingParameterDistance(
                'DISTANCE',
                'Distance de proximité (m)',
                defaultValue=250,
                parentParameterName='RESIDENTIAL_ZONE_LAYER',
                minValue=0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        residential_layer = self.parameterAsVectorLayer(parameters, 'RESIDENTIAL_ZONE_LAYER', context)
        input_layers = self.parameterAsLayerList(parameters, 'BUILDING_LAYERS', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)
        distance = self.parameterAsDouble(parameters, 'DISTANCE', context)

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        residential_params = param_json[residential_layer.name()]
        for building_layer in input_layers:
            if building_layer.name() not in param_json.keys():
                feedback.reportError(
                    "{} n'est pas présent dans le fichier json de paramétrage".format(building_layer.name()))
                return {'OUTPUT': 'Traitement terminé'}

            params = param_json[building_layer.name()]

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
        if issues:
            controlpoint_layer = ControlPointLayer("Proximité Bâti / Zone d'habitation")
            controlpoint_layer.add_features(issues)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

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
