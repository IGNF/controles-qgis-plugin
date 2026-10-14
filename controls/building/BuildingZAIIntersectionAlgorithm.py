from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessing,
    QgsProcessingParameterFeatureSink,
    QgsSpatialIndex,
    QgsFeature
)
from ControlPointLayer import ControlPointLayer


class BuildingZAIIntersectionAlgorithm(QgsProcessingAlgorithm):


    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'F.06'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Intersection Bâti / ZAI"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Bati'

    def groupId(self):
        """Identifiant du groupe"""
        return 'F'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return (
            "Ce contrôle détecte des objets ‘Zone d’activité ou d’intérêt’ et ‘Equipement de transport’ "\
            "qui n’intersectent pas un Bâtiment BDUni.")

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return BuildingZAIIntersectionAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'ZAI_LAYER',
                "Couche Zone d'activité ou d'intérêt ou Equipement de transport",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'BUILDING_LAYERS',
                "Couches Bâtiment BDUni",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        zai_layer = self.parameterAsVectorLayer(parameters, 'ZAI_LAYER', context)
        building_layers = self.parameterAsVectorLayer(parameters, 'BUILDING_LAYERS', context)

        building_index, building_features = self._build_index([building_layers])

        issues = []

        if zai_layer is not None:
            issues.extend(self._find_non_intersecting_features(
                zai_layer, "Zone d'activité ou d'intérêt", building_index, building_features
            ))

        if issues:
            controlpoint_layer = ControlPointLayer("Intersection Bâti / ZAI")
            controlpoint_layer.add_features(issues)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def _find_non_intersecting_features(self, layer, label, building_index, building_features):
        """Retourne la liste des lignes de contrôle pour les objets de `layer` qui
        n'intersectent aucun Bâtiment BDUni."""
        issues = []
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            if not self._intersects_building(geom, building_index, building_features):
                issues.append([
                    "Intersection Bâti / ZAI",
                    layer.name(),
                    feature.id(),
                    'geometry',
                    "Cet objet n’intersecte aucun bâtiment",
                    geom.pointOnSurface()
                ])
        return issues

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
    def _intersects_building(geom, spatial_index, features_dict):
        """Vérifie si `geom` intersecte au moins un objet indexé."""
        candidate_ids = spatial_index.intersects(geom.boundingBox())
        for fid in candidate_ids:
            candidate = features_dict.get(fid)
            if candidate is None:
                continue
            candidate_geom = candidate.geometry()
            if candidate_geom is None or candidate_geom.isEmpty():
                continue
            if geom.intersects(candidate_geom):
                return True
        return False
