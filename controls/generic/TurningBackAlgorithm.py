from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsPoint
)
from ControlPointLayer import ControlPointLayer
import math

class TurningBackAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couche de route en entrée",
                layerType=QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)
        angle_threshold = 10.0  # Angle en degrés

        turning_backs = []

        for layer in layers:
            if layer.geometryType() != QgsWkbTypes.LineGeometry:
                feedback.pushWarning(f"La couche {layer.name()} n'est pas linéaire")
                continue

            for feature in layer.getFeatures():
                geom = feature.geometry()

                if geom.isEmpty() or not geom.isGeosValid():
                    continue

                # Parcourir les segments de la ligne
                polyline = geom.asPolyline() if geom.isMultipart() is False else geom.asMultiPolyline()[0]

                for i in range(1, len(polyline) - 1):
                    p1 = polyline[i - 1]
                    p2 = polyline[i]
                    p3 = polyline[i + 1]

                    # Calculer les vecteurs
                    v1_x = p2.x() - p1.x()
                    v1_y = p2.y() - p1.y()
                    v2_x = p3.x() - p2.x()
                    v2_y = p3.y() - p2.y()

                    # Calculer les longueurs des vecteurs
                    len_v1 = math.sqrt(v1_x ** 2 + v1_y ** 2)
                    len_v2 = math.sqrt(v2_x ** 2 + v2_y ** 2)

                    if len_v1 == 0 or len_v2 == 0:
                        continue

                    # Calculer le produit scalaire
                    dot_product = v1_x * v2_x + v1_y * v2_y

                    # Calculer l'angle en radians puis en degrés
                    cos_angle = dot_product / (len_v1 * len_v2)
                    cos_angle = max(-1.0, min(1.0, cos_angle))  # Limiter entre -1 et 1
                    angle_rad = math.acos(cos_angle)
                    angle_deg = math.degrees(angle_rad)

                    # Détecter les rebroussements (angle proche de 180°)
                    deviation = 180.0 - angle_deg

                    if deviation < angle_threshold:
                        turning_backs.append([
                            'Rebroussement',
                            layer.name(),
                            feature.id(),
                            'geometrie',
                            'Rebroussement',
                            QgsPoint(p2.x(), p2.y())
                        ])

        if turning_backs:
            controlpoint_layer = ControlPointLayer('Rebroussement')
            controlpoint_layer.add_features(turning_backs)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.20'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Rebroussement"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Le contrôle détecte les rebroussements définissant un angle < 10° sur les réseaux linéaires concernés"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return TurningBackAlgorithm()