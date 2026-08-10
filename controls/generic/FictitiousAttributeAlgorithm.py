from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsWkbTypes,
    QgsProject,
    NULL
)
from ControlPointLayer import ControlPointLayer


class FictitiousAttributeAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorPolygon
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)

        fictif_attribute_feature = []
        for layer in layers:
            if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
                feedback.reportError(f"La couche {layer.name()} n'est pas surfacique")
                continue
            for feature in layer.getFeatures():
                if feature.geometry().isEmpty() or feature.geometry().isGeosValid() is False:
                    continue
                if (feature.geometry().area() == 25 and feature['fictif'] is False) \
                    or (feature.geometry().area() != 25 and feature['fictif'] is True):
                        fictif_attribute_feature.append([
                            'Enceinte/Fictif',
                            layer.name(),
                            feature.id(),
                            'Fictif',
                            "La valeur du champ ‘Fictif’ n’est pas cohérente avec la surface de l’objet {} ".format(
                                layer.name()),
                            feature.geometry().centroid()])
        if fictif_attribute_feature:
            controlpoint_layer = ControlPointLayer('Enceinte/Fictif')
            controlpoint_layer.add_features(fictif_attribute_feature)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}