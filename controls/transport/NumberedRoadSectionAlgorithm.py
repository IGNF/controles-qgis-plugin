from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessing,
    QgsProcessingParameterBoolean
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class NumberedRoadSectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.24'
    ALG_DISPLAY_NAME = "Tronçon de route / Route numérotée"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle détecte les tronçons de route de Nature = Route empierrée, Chemin, Bac ou liaison maritime, "
        "Piste cyclable, Escalier ou Sentier qui sont liés à un complexe dont le champ Type de route est Autoroute,"
        "Nationale, Route intercommunale ou Route européenne."
        "Il détecte aussi les tronçons de route de Nature = Route empierrée, Chemin, Bac ou liaison maritime,"
        "Escalier ou Sentier qui sont liés à un complexe dont le champ Type de route est Départementale."
        "Il détecte les tronçons de Nature différente de Type autoroutier et Bretelle,"
        "qui sont liés à une Route numérotée ou nommée dont le champ Type de route est Autoroute."
        "Il détecte les tronçons de Nature Type autoroutier qui ne sont liés à aucun complexe "
        "Route numérotée ou nommée de Type de route = Autoroute, Nationale, Départementale ou Route intercommunale"
    )

    SEGMENT_LAYER = 'SEGMENT_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    SEGMENT_KEY_FIELD = 'SEGMENT_KEY_FIELD'
    COMPLEX_LAYER = 'COMPLEX_LAYER'
    COMPLEX_KEY_FIELD = 'COMPLEX_KEY_FIELD'
    COMPLEX_TYPE_FIELD = 'COMPLEX_TYPE_FIELD'
    NATURE_VALUES = 'NATURE_VALUES'
    TYPE_ROUTE_VALUES = 'TYPE_ROUTE_VALUES'
    SEARCH_LINKED = 'SEARCH_LINKED'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SEGMENT_LAYER,
                self.tr("Couche des tronçons de route"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NATURE_FIELD,
                self.tr("Champ Nature"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.SEGMENT_KEY_FIELD,
                self.tr("Champ clé de liaison au complexe"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.COMPLEX_LAYER,
                self.tr("Couche des objets complexes"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.COMPLEX_KEY_FIELD,
                self.tr("Champ clé de l'objet complexe"),
                parentLayerParameterName=self.COMPLEX_LAYER,
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.COMPLEX_TYPE_FIELD,
                self.tr("Champ Type de route"),
                parentLayerParameterName=self.COMPLEX_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.NATURE_VALUES,
                self.tr("Valeurs Nature"),
                parentLayerParameterName=self.SEGMENT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.TYPE_ROUTE_VALUES,
                self.tr("Valeurs Type de route"),
                parentLayerParameterName=self.COMPLEX_LAYER,
                parentFieldParameterName=self.COMPLEX_TYPE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SEARCH_LINKED,
                self.tr("Rechercher les tronçons liés à un complexe"
                "(décocher pour rechercher les tronçons NON liés)"),
                defaultValue=True
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.SEGMENT_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)
        segment_key_field = self.parameterAsString(parameters, self.SEGMENT_KEY_FIELD, context)
        complex_layer = self.parameterAsVectorLayer(parameters, self.COMPLEX_LAYER, context)
        complex_key_field = self.parameterAsString(parameters, self.COMPLEX_KEY_FIELD, context)
        type_route_field = self.parameterAsString(parameters, self.COMPLEX_TYPE_FIELD, context)

        if nature_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche des tronçons").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        if segment_key_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des tronçons").format(segment_key_field))
            return {'OUTPUT': 'Erreur'}

        if complex_key_field not in complex_layer.fields().names():
            feedback.reportError(self.tr("Le champ clé '{}' n'existe pas dans la couche des objets complexes").format(complex_key_field))
            return {'OUTPUT': 'Erreur'}

        if type_route_field not in complex_layer.fields().names():
            feedback.reportError(self.tr("Le champ Type de route '{}' n'existe pas dans la couche des objets complexes").format(type_route_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        nature_values = field_values_as_string_list(self.parameterAsString(parameters, self.NATURE_VALUES, context))
        type_route_values = field_values_as_string_list(self.parameterAsString(parameters, self.TYPE_ROUTE_VALUES, context))

        # Si coché (par défaut), on recherche les tronçons liés à un complexe du Type de route sélectionné.
        # Si décoché, on recherche les tronçons NON liés.
        search_linked = self.parameterAsBoolean(parameters, self.SEARCH_LINKED, context)

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

        self.report_issues(invalid_features, "Tronçon de route / Route numérotée")

        return self.processing_done_result()
