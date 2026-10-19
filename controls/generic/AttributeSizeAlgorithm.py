from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterFile
)

from BaseControlAlgorithm import BaseControlAlgorithm


class AttributeSizeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.02'
    ALG_DISPLAY_NAME = 'Taille des champs'
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = "Il vérifie que la longueur des attributs ne dépasse pas la longueur maximum définie pour l'archivage FEIV."

    INPUT_LAYER = 'INPUT_LAYER'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.PARAM_JSON,
                self.tr('Paramètres JSON'),
                extension='json'
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        json_path = self.parameterAsFile(parameters, self.PARAM_JSON, context)

        param_json = self.load_json_parameters(json_path)

        size_attributes_feature = []
        layer_params = self.get_layer_json_parameters(param_json, layer, feedback)
        if layer_params is None:
            return self.processing_done_result()

        for feature in layer.getFeatures():
            for att, size in layer_params.items():
                if feature[att] is None or feature[att] == '':
                    continue
                if len(feature[att]) > int(size):
                    size_attributes_feature.append(
                        ['Taille des champs',
                        layer.name(),
                        feature.id(),
                        att,
                        '',
                        feature.geometry().pointOnSurface()])

        self.report_issues(size_attributes_feature, 'Taille des champs')

        return self.processing_done_result()
