from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterDistance,
    QgsSpatialIndex,
    QgsFeature
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class BuildingUninhabitedLocalityProximityAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'F.05'
    ALG_DISPLAY_NAME = "Proximité Bâti / Lieu-dit non habité"
    ALG_GROUP = 'Controles du thème Bati'
    ALG_GROUP_ID = 'F'
    ALG_HELP = (
        "Ce contrôle détecte les objets Lieu-dit non habité de Nature = ‘Lieu-dit non habité’ "
        "qui sont à moins de 50 m d'un objet Bâtiment ou d'un objet Construction linéaire de Nature = ‘Ruines’"
    )

    LOCALITY_LAYER = 'LOCALITY_LAYER'
    LOCALITY_NATURE_FIELD = 'LOCALITY_NATURE_FIELD'
    LOCALITY_NATURE_VALUE = 'LOCALITY_NATURE_VALUE'
    BUILDING_LAYERS = 'BUILDING_LAYERS'
    CONSTRUCTION_NATURE_FIELD = 'CONSTRUCTION_NATURE_FIELD'
    RUINS_VALUE = 'RUINS_VALUE'
    DISTANCE = 'DISTANCE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LOCALITY_LAYER,
                self.tr("Couche Lieu-dit non habité"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.LOCALITY_NATURE_FIELD,
                self.tr('Champ Nature lieu dit'),
                parentLayerParameterName=self.LOCALITY_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.LOCALITY_NATURE_VALUE,
                self.tr('Valeur Nature lieu dit'),
                parentLayerParameterName=self.LOCALITY_LAYER,
                parentFieldParameterName=self.LOCALITY_NATURE_FIELD,
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BUILDING_LAYERS,
                self.tr("Couches Bâti ou Construction linéaire"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.CONSTRUCTION_NATURE_FIELD,
                self.tr('Champ Nature Construction linéaire'),
                parentLayerParameterName=self.BUILDING_LAYERS,
                type=QgsProcessingParameterField.String,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.RUINS_VALUE,
                self.tr('Valeur Nature Construction linéaire'),
                parentLayerParameterName=self.BUILDING_LAYERS,
                parentFieldParameterName=self.CONSTRUCTION_NATURE_FIELD,
                allowMultiple=False,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                self.tr('Distance de proximité (m)'),
                defaultValue=50,
                parentParameterName=self.LOCALITY_LAYER,
                minValue=0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        locality_layer = self.parameterAsVectorLayer(parameters, self.LOCALITY_LAYER, context)
        locality_nature_field = self.parameterAsString(parameters, self.LOCALITY_NATURE_FIELD, context)
        locality_nature_values = field_values_as_string_list(
            self.parameterAsString(parameters, self.LOCALITY_NATURE_VALUE, context)
        )
        locality_nature_value = locality_nature_values[0] if locality_nature_values else None

        building_layer = self.parameterAsVectorLayer(parameters, self.BUILDING_LAYERS, context)
        construction_nature_field = self.parameterAsString(parameters, self.CONSTRUCTION_NATURE_FIELD, context)
        ruins_values = field_values_as_string_list(
            self.parameterAsString(parameters, self.RUINS_VALUE, context)
        )
        ruins_value = ruins_values[0] if ruins_values else None

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)


        def ruins_filter(feature):
            if not construction_nature_field or not ruins_value:
                return True
            return str(feature.attribute(construction_nature_field)) == str(ruins_value)

        if building_layer is not None:
            building_index, building_features = self._build_index([building_layer], feature_filter=ruins_filter)
        else:
            building_index, building_features = QgsSpatialIndex(), {}

        issues = []

        for locality in locality_layer.getFeatures():
            if locality_nature_value is not None and str(locality.attribute(locality_nature_field)) != str(locality_nature_value):
                continue

            geom = locality.geometry()
            if geom is None or geom.isEmpty():
                continue

            if self._has_feature_within_distance(geom, building_index, building_features, distance):
                issues.append([
                    "Proximité Bâti / Lieu-dit non habité",
                    locality_layer.name(),
                    locality.id(),
                    'geometry',
                    "Il y a un Bâtiment à moins de {}m du Lieu-dit non habité de Nature 'Lieu-dit non habité'".format(
                        distance),
                    geom.pointOnSurface()
                ])

        self.report_issues(issues, "Proximité Bâti / Lieu-dit non habité")

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
