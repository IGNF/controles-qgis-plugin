from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessing,
    NULL
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class NonZSectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'B.02'
    ALG_DISPLAY_NAME = "Tronçons sans Z"
    ALG_GROUP = 'Controles génériques Z'
    ALG_GROUP_ID = 'B'
    ALG_HELP = (
        "Ce contrôle détecte les objets ayant au moins un Z vide et "
        "de ‘Méthode d’acquisition altimétrique’ = ‘Photogrammétrie’, ‘Photogrammétrie longue focale’, ‘BDTopo’ ou ‘Levé GPS’"
    )

    INPUT_LAYER = 'INPUT_LAYER'
    ATTRIBUTE_FIELD = 'ATTRIBUTE_FIELD'
    ATTRIBUTE_VALUES = 'ATTRIBUTE_VALUES'
    Z_FIELD = 'Z_FIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTRIBUTE_FIELD,
                self.tr('Attribut à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ATTRIBUTE_VALUES,
                self.tr('Valeurs à contrôler'),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.ATTRIBUTE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.Z_FIELD,
                self.tr('Champ Z à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        attribute_field = self.parameterAsString(parameters, self.ATTRIBUTE_FIELD, context)
        z_field = self.parameterAsString(parameters, self.Z_FIELD, context)

        # Valeurs sélectionnées dynamiquement via le widget (stockées en chaîne séparée par des virgules)
        raw_attribute_values = self.parameterAsString(parameters, self.ATTRIBUTE_VALUES, context)
        selected_values = field_values_as_string_list(raw_attribute_values)

        if attribute_field not in layer.fields().names():
            feedback.reportError(self.tr("L'attribut '{}' n'existe pas dans la couche {}").format(attribute_field, layer.name()))
            return {'OUTPUT': 'Erreur'}

        if z_field not in layer.fields().names():
            feedback.reportError(self.tr("Le champ Z '{}' n'existe pas dans la couche {}").format(z_field, layer.name()))
            return {'OUTPUT': 'Erreur'}

        non_z_objects = []

        for feature in layer.getFeatures():

            # Vérifier la valeur de l'attribut
            attribute_value = str(feature[attribute_field])
            if attribute_value not in selected_values:
                continue

            z_value = feature[z_field]
            if z_value is None or z_value == NULL:
                non_z_objects.append([
                    'Tronçon sans Z',
                    layer.name(),
                    feature.id(),
                    z_field,
                    "L'objet comporte un champ Z vide ({}={})".format(attribute_field, attribute_value),
                    feature.geometry().pointOnSurface()
                ])

        self.report_issues(non_z_objects, 'Tronçons sans Z')

        return self.processing_done_result()
