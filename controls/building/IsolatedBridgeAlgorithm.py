from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterEnum,
QgsProcessingParameterFeatureSink
)
from ControlPointLayer import ControlPointLayer

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
                parentLayerParameterName='ROAD_LAYER',
                type=QgsProcessingParameterField.Numeric
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
            QgsProcessingParameterEnum(
                'BRIDGE_VALUE',
                'Valeur Pont',
                options=[],
                allowMultiple=False
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'TUNNEL_VALUE',
                'Valeur Tunnel (optionnel)',
                options=[],
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

        # Récupérer les valeurs uniques du champ Nature
        nature_values = list(
            set([f[nature_field] for f in construction_layer.getFeatures() if f[nature_field] is not None]))

        # Récupérer les indices sélectionnés
        bridge_idx = self.parameterAsEnum(parameters, 'BRIDGE_VALUE', context)
        tunnel_idx = self.parameterAsEnum(parameters, 'TUNNEL_VALUE', context)

        bridge_value = nature_values[bridge_idx] if bridge_idx < len(nature_values) else None
        tunnel_value = nature_values[tunnel_idx] if tunnel_idx is not None and tunnel_idx < len(nature_values) else None

        issues = []
        distance_threshold = 0.5  # 50 cm en mètres

        # Séparer les ponts et tunnels
        bridges = []
        tunnels = []

        for construction in construction_layer.getFeatures():
            nature = construction.attribute(nature_field)
            if nature == bridge_value:
                bridges.append(construction)
            elif tunnel_value and nature == tunnel_value:
                tunnels.append(construction)

        # Vérifier les tronçons de route
        for road in road_layer.getFeatures():
            position = road.attribute(position_field)

            if position is None:
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
            controlpoint_layer.save()

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