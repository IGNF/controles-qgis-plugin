from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsFeatureRequest
)

from BaseControlAlgorithm import BaseControlAlgorithm


class AttributesInconsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.00'
    ALG_DISPLAY_NAME = "Incohérences entre attributs"
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = (
        "Le contrôle détecte les incohérences entre attributs pour une classe donnée d'après la règle suivante :\n"
        "Cas1  : Si Champ1 <> Valeur1 alors Champ2 >= Champ1\n"
        "Cas2  : Si Champ1 <> Valeur1 alors Champ2 <= Champ1\n"
        "Cas3  : Si Champ1 <> Valeur1 alors Champ2 = Valeur2\n"
        "Cas4  : Si Champ1 <> Valeur1 alors Champ2 <> Valeur2\n"
        "Cas5  : Si Champ1 = Valeur1 alors Champ2 = Valeur2\n"
        "Cas6  : Si Champ1 = Valeur1 alors Champ2 <> Valeur2\n"
        "Cas7  : Si Champ1 <> Valeur1 et Champ2 <> Valeur2 alors Champ1 < Champ2\n"
        "Cas8  : Si Champ1 = Valeur1 alors Champ2 <= DATE_DU_JOUR\n"
        "Cas9  : Si Champ1 <> Valeur1 alors Champ2 <= Champ1 + Valeur2 (en mois)\n"
        "Cas10 : Si Champ1 = Valeur1 alors Champ2 = Valeur2 ou Valeur2 ou Valeur2...\n"
        "Cas13 : Si Champ1 = Valeur1 et Champ2 <> Valeur2 alors Champ3 = Valeur3\n"
        "Cas14 : Si Champ1 = Valeur1 alors Champ2 ne contient pas Valeur2"
    )

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

        # param_json : {'couche': {condition: consequence}, ...}
        param_json = self.load_json_parameters(json_path)

        incoherence_attributes_feature = []
        layer_params = self.get_layer_json_parameters(param_json, layer, feedback)
        if layer_params is None:
            return self.processing_done_result()

        for condition, consequence in layer_params:
            request = QgsFeatureRequest()
            request.setFilterExpression(condition)
            for feature in layer.getFeatures(request):
                if not consequence:
                    incoherence_attributes_feature.append(
                        ['Incohérence entre attributs',
                        layer.name(),
                        feature.id(),
                        consequence[0],
                        'Les champs {} et {} ne sont pas cohérents'.format(condition[0], consequence[0]),
                        feature.geometry().pointOnSurface()])

        self.report_issues(incoherence_attributes_feature, 'Incohérence entre attributs')

        return self.processing_done_result()
