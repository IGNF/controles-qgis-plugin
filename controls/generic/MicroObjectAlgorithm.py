from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsProcessingParameterNumber,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer

class MicroObjectAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'THRESHOLD',
                'Seuil (m ou m²)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=3.0,
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
        threshold = self.parameterAsDouble(parameters, 'THRESHOLD', context)

        micro_objects = []
        if layer.geometryType() not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
            feedback.pushWarning(f"La couche {layer.name()} n'est ni linéaire ni surfacique, elle sera ignorée")
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            comment = ''
            geom = feature.geometry()
            if geom.isEmpty() or not geom.isGeosValid():
                continue
            is_micro = False
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                length = geom.length()
                if length <= threshold:
                    is_micro = True
                    comment = 'Objet de longueur <= {}m'.format(length)
            elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                area = geom.area()
                if area <= threshold:
                    is_micro = True
                    comment = 'Objet de surface <= {}m²'.format(area)
            if is_micro:
                micro_objects.append([
                    'Micro-objet',
                    layer.name(),
                    feature.id(),
                    'geometrie',
                    comment,
                    geom.centroid()
                ])

        if micro_objects:
            controlpoint_layer = ControlPointLayer('Micro-objets')
            controlpoint_layer.add_features(micro_objects)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.15'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Micro-objets"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte :"\
            "Les objets linéaires de longueur ≤ 3 m ou < 2 m pour les Tronçons de route"\
            "Les objets surfaciques de surface ≤ 9 m2 ou < 0.2 m2 pour les Bâtiments et Réservoirs ou ≤ 2 m2 pour les Constructions surfaciques et Postes de transformation"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return MicroObjectAlgorithm()