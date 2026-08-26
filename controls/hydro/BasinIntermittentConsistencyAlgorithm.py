from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessing,
    QgsProcessingParameterFeatureSink
)
from ControlPointLayer import ControlPointLayer


class BasinIntermittentConsistencyAlgorithm(QgsProcessingAlgorithm):

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
                'NATURE_FIELD',
                'Champ Nature',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'NATURE_VALUES',
                'Valeurs Nature à contrôler',
                options=[],
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'PERSISTANCE_FIELD',
                'Champ Persistance',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'PERSISTANCE_VALUES',
                'Valeurs Persistance à contrôler',
                options=[],
                allowMultiple=True,
                optional=False
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
        nature_field = self.parameterAsString(parameters, 'NATURE_FIELD', context)
        persistance_field = self.parameterAsString(parameters, 'PERSISTANCE_FIELD', context)

        field_names = layer.fields().names()
        if nature_field not in field_names:
            feedback.reportError(f"Le champ Nature '{nature_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        if persistance_field not in field_names:
            feedback.reportError(f"Le champ Persistance '{persistance_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        # Valeurs uniques triées pour Nature
        nature_unique = sorted(
            [str(v) for v in layer.uniqueValues(layer.fields().indexFromName(nature_field)) if v is not None]
        )
        selected_nature_indices = self.parameterAsEnums(parameters, 'NATURE_VALUES', context)
        selected_nature_values = [nature_unique[i] for i in selected_nature_indices]

        # Valeurs uniques triées pour Persistance
        persistance_unique = sorted(
            [str(v) for v in layer.uniqueValues(layer.fields().indexFromName(persistance_field)) if v is not None]
        )
        selected_persistance_indices = self.parameterAsEnums(parameters, 'PERSISTANCE_VALUES', context)
        selected_persistance_values = [persistance_unique[i] for i in selected_persistance_indices]

        invalid_features = []
        for feature in layer.getFeatures():
            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else ''
            persistance_value = str(feature[persistance_field]) if feature[persistance_field] is not None else ''

            if nature_value in selected_nature_values and persistance_value in selected_persistance_values:
                invalid_features.append([
                    'Cohérence Bassin / Intermittent',
                    layer.name(),
                    feature.id(),
                    nature_field,
                    "Le champ Persistance des surfaces hydrographiques dont la Nature est {} doit être à {}".format(
                        selected_nature_values, selected_persistance_values),
                    feature.geometry().centroid()
                ])

        if invalid_features:
            controlpoint_layer = ControlPointLayer('Cohérence Bassin / Intermittent')
            controlpoint_layer.add_features(invalid_features)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'G.01'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Cohérence Bassin / Intermittent"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème hydrographique'

    def groupId(self):
        """Identifiant du groupe"""
        return 'G'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les surfaces hydrographiques dont la Nature est Réservoir-bassin ou "\
            "Réservoir-bassin piscicole ou Réservoir-bassin d'orage et dont le champ Persistance est égal à Permanent"
    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return BasinIntermittentConsistencyAlgorithm()