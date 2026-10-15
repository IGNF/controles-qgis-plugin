from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessing,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink
)
from ControlPointLayer import ControlPointLayer
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list


class NumberedRoadSectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'SEGMENT_LAYER',
                "Couche des tronçons de route",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'NATURE_FIELD',
                "Champ Nature",
                parentLayerParameterName='SEGMENT_LAYER',
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'SEGMENT_KEY_FIELD',
                "Champ clé de liaison au complexe",
                parentLayerParameterName='SEGMENT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'COMPLEX_LAYER',
                "Couche des objets complexes",
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'COMPLEX_KEY_FIELD',
                "Champ clé de l'objet complexe",
                parentLayerParameterName='COMPLEX_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'COMPLEX_TYPE_FIELD',
                "Champ Type de route",
                parentLayerParameterName='COMPLEX_LAYER',
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'NATURE_VALUES',
                "Valeurs Nature",
                parentLayerParameterName='SEGMENT_LAYER',
                parentFieldParameterName='NATURE_FIELD',
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'TYPE_ROUTE_VALUES',
                "Valeurs Type de route",
                parentLayerParameterName='COMPLEX_LAYER',
                parentFieldParameterName='COMPLEX_TYPE_FIELD',
                allowMultiple=True,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                'SEARCH_LINKED',
                "Rechercher les tronçons liés à un complexe"
                "(décocher pour rechercher les tronçons NON liés)",
                defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, 'SEGMENT_LAYER', context)
        nature_field = self.parameterAsString(parameters, 'NATURE_FIELD', context)
        segment_key_field = self.parameterAsString(parameters, 'SEGMENT_KEY_FIELD', context)
        complex_layer = self.parameterAsVectorLayer(parameters, 'COMPLEX_LAYER', context)
        complex_key_field = self.parameterAsString(parameters, 'COMPLEX_KEY_FIELD', context)
        type_route_field = self.parameterAsString(parameters, 'COMPLEX_TYPE_FIELD', context)

        if nature_field not in segment_layer.fields().names():
            feedback.reportError(f"Le champ Nature '{nature_field}' n'existe pas dans la couche des tronçons")
            return {'OUTPUT': 'Erreur'}

        if segment_key_field not in segment_layer.fields().names():
            feedback.reportError(f"Le champ clé '{segment_key_field}' n'existe pas dans la couche des tronçons")
            return {'OUTPUT': 'Erreur'}

        if complex_key_field not in complex_layer.fields().names():
            feedback.reportError(f"Le champ clé '{complex_key_field}' n'existe pas dans la couche des objets complexes")
            return {'OUTPUT': 'Erreur'}

        if type_route_field not in complex_layer.fields().names():
            feedback.reportError(f"Le champ Type de route '{type_route_field}' n'existe pas dans la couche des objets complexes")
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        nature_values = field_values_as_string_list(self.parameterAsString(parameters, 'NATURE_VALUES', context))
        type_route_values = field_values_as_string_list(self.parameterAsString(parameters, 'TYPE_ROUTE_VALUES', context))

        # Si coché (par défaut), on recherche les tronçons liés à un complexe du Type de route sélectionné.
        # Si décoché, on recherche les tronçons NON liés.
        search_linked = self.parameterAsBoolean(parameters, 'SEARCH_LINKED', context)

        # Construire le dictionnaire des Types de route des complexes, indexé par clé
        type_route_by_key = {}
        for complex_feature in complex_layer.getFeatures():
            key_value = complex_feature[complex_key_field]
            if key_value is None:
                continue
            type_route_value = complex_feature[type_route_field]
            type_route_by_key.setdefault(key_value, set()).add(
                str(type_route_value) if type_route_value is not None else None
            )

        invalid_features = []

        for segment in segment_layer.getFeatures():
            nature_value = str(segment[nature_field]) if segment[nature_field] is not None else None
            if nature_value not in nature_values:
                continue

            key_value = segment[segment_key_field]
            linked_types = type_route_by_key.get(key_value, set()) if key_value is not None else set()
            matching_types = linked_types & set(type_route_values)

            if search_linked or not matching_types:
                invalid_features.append([
                    "Tronçon de route / Route numérotée",
                    segment_layer.name(),
                    segment.id(),
                    nature_field,
                    "La nature du tronçon n'est pas compatible avec le Type de route numérotée",
                    segment.geometry().pointOnSurface()
                ])

        if invalid_features:
            controlpoint_layer = ControlPointLayer("Tronçon de route / Route numérotée")
            controlpoint_layer.add_features(invalid_features)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'D.24'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Tronçon de route / Route numérotée"

    def group(self):
        """Nom du groupe"""
        return 'Controles du thème Transport'

    def groupId(self):
        """Identifiant du groupe"""
        return 'D'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            ("Ce contrôle détecte les tronçons de route de Nature = Route empierrée, Chemin, Bac ou liaison maritime, "
             "Piste cyclable, Escalier ou Sentier qui sont liés à un complexe dont le champ Type de route est Autoroute,"
             "Nationale, Route intercommunale ou Route européenne."
             "Il détecte aussi les tronçons de route de Nature = Route empierrée, Chemin, Bac ou liaison maritime,"
             "Escalier ou Sentier qui sont liés à un complexe dont le champ Type de route est Départementale."
             "Il détecte les tronçons de Nature différente de Type autoroutier et Bretelle,"
             "qui sont liés à une Route numérotée ou nommée dont le champ Type de route est Autoroute."
             "Il détecte les tronçons de Nature Type autoroutier qui ne sont liés à aucun complexe "
             "Route numérotée ou nommée de Type de route = Autoroute, Nationale, Départementale ou Route intercommunale")

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NumberedRoadSectionAlgorithm()