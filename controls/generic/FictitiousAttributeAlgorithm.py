from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsProcessingParameterField,
QgsProcessingParameterNumber,
QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
from ControlPointLayer import ControlPointLayer


class FictitiousAttributeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'FICTIF_FIELD',
                "Attribut fictif",
                parentLayerParameterName='INPUT_LAYER'
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'AREA_THRESHOLD',
                "Seuil de surface",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=25.0
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
        fictif_field = self.parameterAsString(parameters, 'FICTIF_FIELD', context)
        area_threshold = self.parameterAsDouble(parameters, 'AREA_THRESHOLD', context)

        fictif_attribute_feature = []
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            feedback.reportError(f"La couche {layer.name()} n'est pas surfacique")
            return {'OUTPUT': 'Traitement terminé'}

        field = layer.fields().field(fictif_field)
        if field.type() != QVariant.Bool:
            feedback.reportError(
                f"Le champ '{fictif_field}' n'est pas de type booléen (type détecté : {field.typeName()})"
            )
            return {'OUTPUT': 'Traitement terminé'}

        for feature in layer.getFeatures():
            if feature.geometry().isEmpty() or feature.geometry().isGeosValid() is False:
                continue
            if (feature.geometry().area() == area_threshold and feature[fictif_field] is False) \
                or (feature.geometry().area() != area_threshold and feature[fictif_field] is True):
                    fictif_attribute_feature.append([
                        'Enceinte/Fictif',
                        layer.name(),
                        feature.id(),
                        fictif_field,
                        "La valeur du champ '{}' n'est pas cohérente avec la surface de l'objet {} ".format(
                            fictif_field, layer.name()),
                        feature.geometry().pointOnSurface()])

        if fictif_attribute_feature:
            controlpoint_layer = ControlPointLayer('Enceinte/Fictif')
            controlpoint_layer.add_features(fictif_attribute_feature)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'C.11'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Enceinte / Fictif"

    def group(self):
        """Nom du groupe"""
        return 'controles génériques attributaires'

    def groupId(self):
        """Identifiant du groupe"""
        return 'C'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Le but de ce contrôle est de s’assurer que l’attribut Fictif des classes d’objets surfaciques modélisant"\
            "des enceintes est correctement codé."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return FictitiousAttributeAlgorithm()