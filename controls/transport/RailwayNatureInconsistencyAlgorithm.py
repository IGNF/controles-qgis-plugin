from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class RailwayNatureInconsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'I.01'
    ALG_DISPLAY_NAME = "Voies ferrées : cohérence Nature / Energie / Largeur de voie"
    ALG_GROUP = 'Controles du thème Transport ferroviaire'
    ALG_GROUP_ID = 'I'
    ALG_HELP = (
        "Ce contrôle détecte : "
        "les tronçons de voies ferrées dont le champ Nature = « LGV », « Métro » ou « Tramway » et "
        "dont le champ Electrifié est différent de « 1 » (Vrai) ; "
        "les tronçons de voies ferrées dont le champ Nature = « LGV » et dont le champ Largeur est "
        "différent de « Normale ».")

    INPUT_LAYER = 'INPUT_LAYER'
    NATURE_FIELD = 'NATURE_FIELD'
    ELECTRIFIE_FIELD = 'ELECTRIFIE_FIELD'
    LARGEUR_FIELD = 'LARGEUR_FIELD'
    NATURE_ELECTRIFIEE_VALUES = 'NATURE_ELECTRIFIEE_VALUES'
    LARGEUR_NORMALE_VALUE = 'LARGEUR_NORMALE_VALUE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche des tronçons de voies ferrées"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.NATURE_FIELD,
                self.tr("Champ Nature"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ELECTRIFIE_FIELD,
                self.tr("Champ Electrifié"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.LARGEUR_FIELD,
                self.tr("Champ Largeur de voie"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.NATURE_ELECTRIFIEE_VALUES,
                self.tr("Valeurs Nature attendues électrifiées (LGV, Métro, Tramway)"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.NATURE_FIELD,
                allowMultiple=True,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.LARGEUR_NORMALE_VALUE,
                self.tr("Valeur Largeur de voie correspondant à « Normale »"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.LARGEUR_FIELD,
                allowMultiple=False,
                optional=True
            )
        )

        super().initAlgorithm(config)

    @staticmethod
    def _to_bool(value):
        """Convertit la valeur brute du champ Electrifié en booléen (True pour « 1 »/Vrai)."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return text in ('1', 'true', 'vrai', 'oui', 'yes')

    def processAlgorithm(self, parameters, context, feedback):
        segment_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        nature_field = self.parameterAsString(parameters, self.NATURE_FIELD, context)
        electrifie_field = self.parameterAsString(parameters, self.ELECTRIFIE_FIELD, context)
        largeur_field = self.parameterAsString(parameters, self.LARGEUR_FIELD, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(segment_layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if nature_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Nature '{}' n'existe pas dans la couche des tronçons").format(nature_field))
            return {'OUTPUT': 'Erreur'}

        if electrifie_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Electrifié '{}' n'existe pas dans la couche des tronçons").format(electrifie_field))
            return {'OUTPUT': 'Erreur'}

        if largeur_field not in segment_layer.fields().names():
            feedback.reportError(self.tr("Le champ Largeur de voie '{}' n'existe pas dans la couche des tronçons").format(largeur_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via les widgets (chaînes séparées par des virgules)
        nature_electrifiee_values = field_values_as_string_list(
            self.parameterAsString(parameters, self.NATURE_ELECTRIFIEE_VALUES, context)
        )
        # Valeur attendue pour le champ Electrifié (booléen « Vrai », non paramétrable)
        electrifie_vrai_value = True
        # La valeur « LGV » est la première des valeurs Nature électrifiées sélectionnées
        # (paramètre NATURE_ELECTRIFIEE_VALUES, saisi dans l'ordre LGV / Métro / Tramway)
        largeur_normale_value = self.parameterAsString(parameters, self.LARGEUR_NORMALE_VALUE, context) or None

        geom_type = QgsWkbTypes.geometryType(segment_layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(segment_layer.name()))
            return self.processing_done_result()

        invalid_features = []

        for feature in segment_layer.getFeatures():
            nature_value = str(feature[nature_field]) if feature[nature_field] is not None else None
            electrifie_value = self._to_bool(feature[electrifie_field])
            largeur_value = str(feature[largeur_field]) if feature[largeur_field] is not None else None

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            if nature_value in nature_electrifiee_values and electrifie_value != electrifie_vrai_value:
                invalid_features.append([
                    "Electrification incohérente avec la Nature",
                    segment_layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    electrifie_field,
                    "La valeur du champ Nature et celle du champ Electrifié sont incohérentes",
                    geom.pointOnSurface()
                ])

            if nature_value in nature_electrifiee_values and largeur_normale_value is not None and largeur_value != largeur_normale_value:
                invalid_features.append([
                    "Largeur de voie incohérente avec la Nature",
                    segment_layer.name(),
                    self.get_feature_identifier(feature, id_field),
                    largeur_field,
                    "La valeur du champ Nature et celle du champ Largeur de voie sont incohérentes",
                    geom.pointOnSurface()
                ])

        self.report_issues(invalid_features, "Incohérence Nature / Energie / Largeur de voie")

        return self.processing_done_result()
