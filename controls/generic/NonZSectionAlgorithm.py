from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessingParameterField,
QgsProcessing,
QgsProcessingParameterFeatureSink,
NULL
)
from ControlPointLayer import ControlPointLayer
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

class NonZSectionAlgorithm(QgsProcessingAlgorithm):

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
            QgsProcessingParameterFieldValues(
                'ATTRIBUTE_VALUES',
                'Valeurs à contrôler',
                parentLayerParameterName='INPUT_LAYER',
                parentFieldParameterName='ATTRIBUTE_FIELD',
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'Z_FIELD',
                'Champ Z à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
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
        z_field = self.parameterAsString(parameters, 'Z_FIELD', context)

        # Valeurs sélectionnées dynamiquement via le widget (stockées en chaîne séparée par des virgules)
        raw_attribute_values = self.parameterAsString(parameters, 'ATTRIBUTE_VALUES', context)
        selected_values = field_values_as_string_list(raw_attribute_values)

        if attribute_field not in layer.fields().names():
            feedback.reportError(f"L'attribut '{attribute_field}' n'existe pas dans la couche {layer.name()}")
            return {'OUTPUT': 'Erreur'}

        if z_field not in layer.fields().names():
            feedback.reportError(f"Le champ Z '{z_field}' n'existe pas dans la couche {layer.name()}")
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
                    f"L'objet comporte un champ Z vide ({attribute_field}={attribute_value})",
                    feature.geometry().pointOnSurface()
                ])

        if non_z_objects:
            controlpoint_layer = ControlPointLayer('Tronçons sans Z')
            controlpoint_layer.add_features(non_z_objects)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'B.02'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Tronçons sans Z"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques Z'

    def groupId(self):
        """Identifiant du groupe"""
        return 'B'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les objets ayant au moins un Z vide et "\
            "de ‘Méthode d’acquisition altimétrique’ = ‘Photogrammétrie’, ‘Photogrammétrie longue focale’, ‘BDTopo’ ou ‘Levé GPS’"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NonZSectionAlgorithm()