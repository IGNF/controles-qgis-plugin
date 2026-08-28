from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsProcessingParameterFeatureSink,
    QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer
import json


class BuildingAltitudeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'ATTRIBUTE_FIELD',
                'Attribut à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'ATTRIBUTE_VALUES',
                'Valeurs à contrôler',
                options=[],
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'ALTITUDE_FIELD',
                'Altitude à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'ALTITUDE_VALUE',
                'Valeur d\'altitude invalide',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=-100
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
        attribute_field = self.parameterAsString(parameters, 'ATTRIBUTE_FIELD', context)
        altitude_field = self.parameterAsString(parameters, 'ALTITUDE_FIELD', context)
        altitude_value = self.parameterAsDouble(parameters, 'ALTITUDE_VALUE', context)

        # Récupérer les valeurs uniques de l'attribut
        unique_values = layer.uniqueValues(layer.fields().indexFromName(attribute_field))
        unique_values_list = sorted([str(v) for v in unique_values if v is not None])

        # Récupérer les indices des valeurs sélectionnées
        selected_indices = self.parameterAsEnums(parameters, 'ATTRIBUTE_VALUES', context)
        selected_values = [unique_values_list[i] for i in selected_indices]

        if attribute_field not in layer.fields().names():
            feedback.reportError(f"L'attribut '{attribute_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        if altitude_field not in layer.fields().names():
            feedback.reportError(f"Le champ altitude '{altitude_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        invalid_buildings = []
        for feature in layer.getFeatures():
            attribute_value = str(feature[attribute_field])

            # Vérifier si la valeur de l'attribut N'est PAS dans les valeurs sélectionnées
            if attribute_value in selected_values:
                continue

            altitude = feature[altitude_field]

            # Vérifier si l'altitude est vide ou égale à la valeur invalide
            if altitude is None or altitude == altitude_value:
                invalid_buildings.append([
                    'Bâti/bâtiment',
                    layer.name(),
                    feature.id(),
                    altitude_field,
                    f'{attribute_field}: {attribute_value}, {altitude_field}: {altitude}',
                    feature.geometry().pointOnSurface()
                ])

        if invalid_buildings:
            controlpoint_layer = ControlPointLayer('Bâti/bâtiment')
            controlpoint_layer.add_features(invalid_buildings)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'B.05'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Bâti/bâtiment"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques Z'

    def groupId(self):
        """Identifiant du groupe"""
        return 'B'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les bâtiments dont la Méthode d’acquisition altimétrique est différente de « Pas de Z » "\
            "et dont le champ ‘Altitude minimale sol’ est à  -100  ou à vide."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return BuildingAltitudeAlgorithm()