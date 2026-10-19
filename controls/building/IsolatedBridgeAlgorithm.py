from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class IsolatedBridgeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'F.03'
    ALG_DISPLAY_NAME = "Pont isolé"
    ALG_GROUP = 'Controles du thème Bati'
    ALG_GROUP_ID = 'F'
    ALG_HELP = (
        "Ce contrôle se limite à la recherche des Tronçons de route de Position par rapport au sol <= 0 "
        "partageant la géométrie d’une Construction linéaire de Nature = ‘Pont’ (ou à une distance de moins de 50 cm du pont)."
        "Ce contrôle recherche également les Tronçons de route de Position par rapport au sol >= 0 "
        "partageant la géométrie d’une Construction linéaire de Nature = ‘Tunnel’ (ou à une distance de moins de 50 cm du tunnel)."
    )

    ROAD_LAYER = 'ROAD_LAYER'
    POSITION_FIELD = 'POSITION_FIELD'
    CONSTRUCTION_LAYER = 'CONSTRUCTION_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    BRIDGE_VALUE = 'BRIDGE_VALUE'
    TUNNEL_VALUE = 'TUNNEL_VALUE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.ROAD_LAYER,
                self.tr("Couche Tronçons de route"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.POSITION_FIELD,
                self.tr('Champ Position par rapport au sol'),
                parentLayerParameterName=self.ROAD_LAYER
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CONSTRUCTION_LAYER,
                self.tr("Couche Construction linéaire"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NATURE_FIELD,
                self.tr('Champ Nature'),
                parentLayerParameterName=self.CONSTRUCTION_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.BRIDGE_VALUE,
                self.tr('Valeur Pont'),
                parentLayerParameterName=self.CONSTRUCTION_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.TUNNEL_VALUE,
                self.tr('Valeur Tunnel (optionnel)'),
                parentLayerParameterName=self.CONSTRUCTION_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=False,
                optional=True
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        road_layer = self.parameterAsVectorLayer(parameters, self.ROAD_LAYER, context)
        position_field = self.parameterAsString(parameters, self.POSITION_FIELD, context)
        construction_layer = self.parameterAsVectorLayer(parameters, self.CONSTRUCTION_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)

        # Valeur Pont sélectionnée dynamiquement via le widget (champ 'field_values')
        raw_bridge_value = self.parameterAsString(parameters, self.BRIDGE_VALUE, context)
        bridge_values = field_values_as_string_list(raw_bridge_value)
        bridge_value = bridge_values[0] if bridge_values else None

        # Valeur Tunnel sélectionnée dynamiquement via le widget (champ 'field_values')
        raw_tunnel_value = self.parameterAsString(parameters, self.TUNNEL_VALUE, context)
        tunnel_values = field_values_as_string_list(raw_tunnel_value)
        tunnel_value = tunnel_values[0] if tunnel_values else None

        issues = []
        distance_threshold = 0.5  # 50 cm en mètres

        # Séparer les ponts et tunnels
        bridges = []
        tunnels = []

        for construction in construction_layer.getFeatures():
            nature = construction.attribute(nature_field)
            if bridge_value is not None and str(nature) == str(bridge_value):
                bridges.append(construction)
            elif tunnel_value is not None and str(nature) == str(tunnel_value):
                tunnels.append(construction)

        # Vérifier les tronçons de route
        for road in road_layer.getFeatures():
            position = road.attribute(position_field)

            if position is None or position == '':
                continue

            try:
                position = float(position)
            except (TypeError, ValueError):
                continue

            road_geom = road.geometry()
            if road_geom.isEmpty():
                continue

            # Cas 1: Position <= 0 (sous le sol) avec pont
            if position <= 0:
                for bridge in bridges:
                    bridge_geom = bridge.geometry()

                    if road_geom.intersects(bridge_geom) or road_geom.distance(bridge_geom) < distance_threshold:
                        issues.append([
                            'Pont isolé',
                            road_layer.name(),
                            road.id(),
                            position_field,
                            'Problème de position au sol sur le tronçon',
                            road_geom.centroid()
                        ])
                        break

            # Cas 2: Position >= 0 (au-dessus du sol) avec tunnel
            elif tunnel_value and position >= 0:
                for tunnel in tunnels:
                    tunnel_geom = tunnel.geometry()

                    if road_geom.intersects(tunnel_geom) or road_geom.distance(tunnel_geom) < distance_threshold:
                        issues.append([
                            'Pont isolé',
                            road_layer.name(),
                            road.id(),
                            position_field,
                            'Problème de position au sol sur le tronçon',
                            road_geom.centroid()
                        ])
                        break

        self.report_issues(issues, 'Pont isolé')

        return self.processing_done_result()
