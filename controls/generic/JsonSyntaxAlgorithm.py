from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    NULL
)
import json

from BaseControlAlgorithm import BaseControlAlgorithm


class JsonSyntaxAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.12'
    ALG_DISPLAY_NAME = "Syntaxe des champs JSON"
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = (
        "Le but de ce contrôle est de s’assurer que la syntaxe définie pour les champs de format JSON est respectée."
        "Il s’agit de vérifier que les clés et les valeurs de clés sont conformes à ce qui est spécifié."
    )

    INPUT_LAYER = 'INPUT_LAYER'
    FIELDS = 'FIELDS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELDS,
                self.tr('Champs à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                allowMultiple=True
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        fields = self.parameterAsFields(parameters, self.FIELDS, context)

        json_attributes = []

        for feature in layer.getFeatures():
            for att in fields:
                if feature[att] == NULL:
                    continue
                try:
                    json.loads(feature[att])
                except json.JSONDecodeError:
                    json_attributes.append(['Syntaxe des champs JSON',
                                       layer.name(),
                                       feature.id(),
                                       att,
                                       'La syntaxe JSON du champ {} est incorrecte'.format(feature[att]),
                                       feature.geometry().pointOnSurface()])

        self.report_issues(json_attributes, 'Syntaxe des champs JSON')

        return self.processing_done_result()
