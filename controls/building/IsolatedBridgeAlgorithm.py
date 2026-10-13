from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink
)
from ControlPointLayer import ControlPointLayer
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

class IsolatedBridgeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'ROAD_LAYER',
                "Couche Tronçons de route",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'POSITION_FIELD',
                'Champ Position par rapport au sol',
                parentLayerParameterName='ROAD_LAYER'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'CONSTRUCTION_LAYER',
                "Couche Construction linéaire",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'NATURE_FIELD',
                'Champ Nature',
                parentLayerParameterName='CONSTRUCTION_LAYER',
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'BRIDGE_VALUE',
                'Valeur Pont',
                parentLayerParameterName='CONSTRUCTION_LAYER',
                parentFieldParameterName='NATURE_FIELD',
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'TUNNEL_VALUE',
                'Valeur Tunnel (optionnel)',
                parentLayerParameterName='CONSTRUCTION_LAYER',
                parentFieldParameterName='NATURE_FIELD',
                allowMultiple=False,
                optional=True
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
        position_field = self.parameterAsString(parameters, 'POSITION_FIELD', context)
        construction_layer = self.parameterAsVectorLayer(parameters, 'CONSTRUCTION_LAYER', context)
        nature_field = self.parameterAsString(parameters, 'NATURE_FIELD', context)

        # Valeur Pont sélectionnée dynamiquement via le widget (champ 'field_values')
        raw_bridge_value = self.parameterAsString(parameters, 'BRIDGE_VALUE', context)
        bridge_values = field_values_as_string_list(raw_bridge_value)
        bridge_value = bridge_values[0] if bridge_values else None

        # Valeur Tunnel sélectionnée dynamiquement via le widget (champ 'field_values')
        raw_tunnel_value = self.parameterAsString(parameters, 'TUNNEL_VALUE', context)
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

        if issues:
            controlpoint_layer = ControlPointLayer('Pont isolé')
            controlpoint_layer.add_features(issues)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'F.03'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Pont isolé"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Bati'

    def groupId(self):
        """Identifiant du groupe"""
        return 'F'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle se limite à la recherche des Tronçons de route de Position par rapport au sol <= 0 "\
            "partageant la géométrie d’une Construction linéaire de Nature = ‘Pont’ (ou à une distance de moins de 50 cm du pont)."\
            "Ce contrôle recherche également les Tronçons de route de Position par rapport au sol >= 0 "\
            "partageant la géométrie d’une Construction linéaire de Nature = ‘Tunnel’ (ou à une distance de moins de 50 cm du tunnel)."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return IsolatedBridgeAlgorithm()