from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterString
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


def _is_empty_value(value, empty_values):
    if value is None or str(value).strip() == '':
        return True
    return str(value) in empty_values


def _split_prefixes(value):
    return [prefix.strip() for prefix in str(value).split(',') if prefix.strip() != '']


class NumberedNamedRoadAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.23'
    ALG_DISPLAY_NAME = "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle détecte les Routes numérotées ou nommées dont : "
        "Cas 1 : le Type de route est une route numérotée et le champ Gestionnaire est à « Sans valeur ». "
        "Cas 2 : le Type de route est une route numérotée et le champ Numéro est à « Sans valeur ». "
        "Cas 3 / Cas 4 : le Type de route n'est pas une route numérotée (route nommée) et le champ "
        "Gestionnaire n'est pas vide. "
        "Cas 5 à 8 : le Type de route est une route numérotée et le champ Numéro ne commence pas par "
        "l'un des préfixes attendus. "
        "Cas 9 : le Type de route est une route numérotée et le champ Toponymie détaillée est différent "
        "de « Sans valeur ». "
        "Cas 10 : le Type de route est une route nommée et le champ Toponymie détaillée est vide. "
        "Cas 11 : le Type de route est une route nommée et le champ Numéro n'est pas vide. "
        "Les Types de route contrôlés, les valeurs « Sans valeur » et les préfixes attendus sont "
        "modifiables en paramètre.")

    INPUT_LAYER = 'INPUT_LAYER'
    TYPE_ROUTE_FIELD = 'TYPE_ROUTE_FIELD'
    GESTIONNAIRE_FIELD = 'GESTIONNAIRE_FIELD'
    NUMERO_FIELD = 'NUMERO_FIELD'
    TOPONYMIE_FIELD = 'TOPONYMIE_FIELD'

    TYPE_ROUTE_VALUES = 'TYPE_ROUTE_VALUES'
    NUMERO_VALUES = 'NUMERO_VALUES'
    GESTIONNAIRE_VALUES = 'GESTIONNAIRE_VALUES'
    TOPONYMY_VALUES = 'TOPONYMY_VALUES'

    PREFIXES = 'PREFIXES'


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche des routes numérotées ou nommées"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.TYPE_ROUTE_FIELD,
                self.tr("Champ Type de route"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.GESTIONNAIRE_FIELD,
                self.tr("Champ Gestionnaire"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NUMERO_FIELD,
                self.tr("Champ Numéro"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.TOPONYMIE_FIELD,
                self.tr("Champ Toponymie détaillée"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.TYPE_ROUTE_VALUES,
                self.tr("Valeurs Type de route des routes numérotées"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.TYPE_ROUTE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.NUMERO_VALUES,
                self.tr("Valeurs 'Sans valeur' pour numéro"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NUMERO_FIELD,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.GESTIONNAIRE_VALUES,
                self.tr("Valeurs 'Sans valeur' pour gestionnaire"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.GESTIONNAIRE_FIELD,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.TOPONYMY_VALUES,
                self.tr("Valeurs 'Sans valeur' pour toponymie"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.TOPONYMIE_FIELD,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PREFIXES,
                self.tr("Préfixes attendus"),
                optional=True
            )
        )

        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        type_route_field = self.parameterAsString(parameters, self.TYPE_ROUTE_FIELD, context)
        gestionnaire_field = self.parameterAsString(parameters, self.GESTIONNAIRE_FIELD, context)
        numero_field = self.parameterAsString(parameters, self.NUMERO_FIELD, context)
        toponymie_field = self.parameterAsString(parameters, self.TOPONYMIE_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        for field_name, field_label in (
            (type_route_field, "Type de route"),
            (gestionnaire_field, "Gestionnaire"),
            (numero_field, "Numéro"),
            (toponymie_field, "Toponymie détaillée"),
        ):
            if field_name not in layer.fields().names():
                feedback.reportError(self.tr("Le champ {} '{}' n'existe pas dans la couche").format(field_label, field_name))
                return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        numbered_type_values = field_values_as_string_list(self.parameterAsString(parameters, self.TYPE_ROUTE_VALUES, context))
        numero_empty_values = field_values_as_string_list(self.parameterAsString(parameters, self.NUMERO_VALUES, context))
        gestionnaire_empty_values = field_values_as_string_list(self.parameterAsString(parameters, self.GESTIONNAIRE_VALUES, context))
        toponymy_empty_values = field_values_as_string_list(self.parameterAsString(parameters, self.TOPONYMY_VALUES, context))
        prefixes = _split_prefixes(self.parameterAsString(parameters, self.PREFIXES, context))

        invalid_features = []

        for feature in layer.getFeatures():
            type_route_value = feature[type_route_field]
            type_route_value = str(type_route_value) if type_route_value is not None else None
            gestionnaire_value = feature[gestionnaire_field]
            numero_value = feature[numero_field]
            toponymie_value = feature[toponymie_field]

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            point = geom.pointOnSurface()

            # Les types cochés dans le paramètre correspondent aux routes "nommées" ;
            # les routes "numérotées" sont celles dont le Type de route n'est pas coché
            is_numbered_type = type_route_value in numbered_type_values

            # Cas 1 : route numérotée sans Gestionnaire
            if is_numbered_type and _is_empty_value(gestionnaire_value, gestionnaire_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    gestionnaire_field,
                    " le champ \"Gestionnaire\" ne doit pas être vide",
                    point
                ])

            # Cas 2 : route numérotée sans Numéro
            if is_numbered_type and _is_empty_value(numero_value, numero_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    numero_field,
                    "le champ \"Numéro\" ne doit pas être vide",
                    point
                ])

            # Cas 3 / Cas 4 : Gestionnaire renseigné pour une route non numérotée (nommée)
            if is_numbered_type and not _is_empty_value(gestionnaire_value, gestionnaire_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    gestionnaire_field,
                    "le champ \"Gestionnaire\" doit être vide",
                    point
                ])

            # Cas 5 à 8 : route numérotée dont le Numéro ne commence pas par un préfixe attendu
            if is_numbered_type and prefixes and not _is_empty_value(numero_value, numero_empty_values):
                if not any(str(numero_value).startswith(prefix) for prefix in prefixes):
                    invalid_features.append([
                        "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        numero_field,
                        "le champ \"Numéro\" doit contenir la lettre {}".format(prefixes),
                        point
                    ])

            # Cas 9 : route numérotée dont la Toponymie détaillée est renseignée
            if is_numbered_type and not _is_empty_value(toponymie_value, toponymy_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    toponymie_field,
                    "le champ \"Toponymie détaillée\" doit être vide",
                    point
                ])

            # Cas 10 : route nommée dont la Toponymie détaillée est vide
            if is_numbered_type and _is_empty_value(toponymie_value, toponymy_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    toponymie_field,
                    "le champ \"Toponymie détaillée\" ne doit pas être vide",
                    point
                ])

            # Cas 11 : route nommée dont le Numéro est renseigné
            if is_numbered_type and not _is_empty_value(numero_value, numero_empty_values):
                invalid_features.append([
                    "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée",
                    layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    numero_field,
                    "le champ \"Numéro\" doit être vide",
                    point
                ])

        self.report_issues(invalid_features, "Route numérotée ou nommée : Type de route / Gestionnaire / Numéro / Toponymie détaillée")

        return self.processing_done_result()
