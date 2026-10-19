from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessing,
    NULL
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class BuildingAltitudeAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'B.05'
    ALG_DISPLAY_NAME = "Bâti/bâtiment"
    ALG_GROUP = 'Controles génériques Z'
    ALG_GROUP_ID = 'B'
    ALG_HELP = (
        "Ce contrôle détecte les bâtiments dont la Méthode d’acquisition altimétrique est différente de « Pas de Z » "
        "et dont le champ ‘Altitude minimale sol’ est à  -100  ou à vide."
    )

    INPUT_LAYER = 'INPUT_LAYER'
    ATTRIBUTE_FIELD = 'ATTRIBUTE_FIELD'
    ATTRIBUTE_VALUES = 'ATTRIBUTE_VALUES'
    ALTITUDE_FIELD = 'ALTITUDE_FIELD'
    ALTITUDE_VALUE = 'ALTITUDE_VALUE'

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
                self.ALTITUDE_FIELD,
                self.tr('Altitude à vérifier'),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ALTITUDE_VALUE,
                self.tr("Valeur d'altitude invalide"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=-100
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        attribute_field = self.parameterAsString(parameters, self.ATTRIBUTE_FIELD, context)
        altitude_field = self.parameterAsString(parameters, self.ALTITUDE_FIELD, context)
        altitude_value = self.parameterAsDouble(parameters, self.ALTITUDE_VALUE, context)

        # Valeurs sélectionnées dynamiquement via le widget (stockées en chaîne séparée par des virgules)
        raw_attribute_values = self.parameterAsString(parameters, self.ATTRIBUTE_VALUES, context)
        selected_values = field_values_as_string_list(raw_attribute_values)

        if attribute_field not in layer.fields().names():
            feedback.reportError(self.tr("L'attribut '{}' n'existe pas dans la couche").format(attribute_field))
            return {'OUTPUT': 'Erreur'}

        if altitude_field not in layer.fields().names():
            feedback.reportError(self.tr("Le champ altitude '{}' n'existe pas dans la couche").format(altitude_field))
            return {'OUTPUT': 'Erreur'}

        invalid_buildings = []
        for feature in layer.getFeatures():
            attribute_value = str(feature[attribute_field])

            # Vérifier si la valeur de l'attribut est dans les valeurs sélectionnées
            if attribute_value not in selected_values:
                continue

            altitude = feature[altitude_field]

            # Vérifier si l'altitude est vide ou égale à la valeur invalide
            if altitude is None or altitude == altitude_value or altitude == NULL:
                invalid_buildings.append([
                    'Bâti/bâtiment',
                    layer.name(),
                    feature.id(),
                    altitude_field,
                    'Le champ "Altitude minimale sol" doit être différent de "-100" ou de vide" ',
                    feature.geometry().pointOnSurface()
                ])

        self.report_issues(invalid_buildings, 'Bâti/bâtiment')

        return self.processing_done_result()
