from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant

from BaseControlAlgorithm import BaseControlAlgorithm


class FictitiousAttributeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.11'
    ALG_DISPLAY_NAME = "Enceinte / Fictif"
    ALG_GROUP = 'controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = (
        "Le but de ce contrôle est de s’assurer que l’attribut Fictif des classes d’objets surfaciques modélisant"
        "des enceintes est correctement codé."
    )

    INPUT_LAYER = 'INPUT_LAYER'
    FICTIF_FIELD = 'FICTIF_FIELD'
    AREA_THRESHOLD = 'AREA_THRESHOLD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FICTIF_FIELD,
                self.tr("Attribut fictif"),
                parentLayerParameterName=self.INPUT_LAYER
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.AREA_THRESHOLD,
                self.tr("Seuil de surface"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=25.0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        fictif_field = self.parameterAsString(parameters, self.FICTIF_FIELD, context)
        area_threshold = self.parameterAsDouble(parameters, self.AREA_THRESHOLD, context)

        fictif_attribute_feature = []
        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            feedback.reportError(self.tr("La couche {} n'est pas surfacique").format(layer.name()))
            return self.processing_done_result()

        field = layer.fields().field(fictif_field)
        if field.type() != QVariant.Bool:
            feedback.reportError(
                self.tr("Le champ '{}' n'est pas de type booléen (type détecté : {})").format(fictif_field, field.typeName())
            )
            return self.processing_done_result()

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

        self.report_issues(fictif_attribute_feature, 'Enceinte/Fictif')

        return self.processing_done_result()
