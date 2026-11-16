from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField
)
from qgis.PyQt.QtCore import QDate, QDateTime, NULL

from FieldValuesParameter import QgsProcessingParameterFieldValues

from BaseControlAlgorithm import BaseControlAlgorithm


class ActivationDateAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'D.26'
    ALG_DISPLAY_NAME = "Date de mise en service"
    ALG_GROUP = 'Controles du thème Transport'
    ALG_GROUP_ID = 'D'
    ALG_HELP = (
        "Ce contrôle vérifie la cohérence entre le champ Etat de l'objet et le champ Date de mise en "
        "service sur la GE. "
        "Si l'Etat de l'objet = « En projet » alors la Date de mise en service doit être vide ou "
        "postérieure à la date du jour. "
        "Si l'Etat de l'objet = « En construction » alors la Date de mise en service doit "
        "obligatoirement être renseignée et être postérieure à la date du jour.")

    INPUT_LAYER = 'INPUT_LAYER'
    ETAT_FIELD = 'ETAT_FIELD'
    DATE_FIELD = 'DATE_FIELD'
    ETAT_PROJET_VALUES = 'ETAT_PROJET_VALUES'
    ETAT_CONSTRUCTION_VALUES = 'ETAT_CONSTRUCTION_VALUES'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche des objets"),
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ETAT_FIELD,
                self.tr("Champ Etat de l'objet"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.DATE_FIELD,
                self.tr("Champ Date de mise en service"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.DateTime
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ETAT_PROJET_VALUES,
                self.tr("Valeur Etat correspondant à « En projet »"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.ETAT_FIELD,
                allowMultiple=False,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ETAT_CONSTRUCTION_VALUES,
                self.tr("Valeur Etat correspondant à « En construction »"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.ETAT_FIELD,
                allowMultiple=False,
                optional=False
            )
        )

        super().initAlgorithm(config)

    @staticmethod
    def _to_qdate(value):
        """Convertit la valeur brute d'un champ date/datetime en QDate (ou None si vide/invalide)."""
        if value is None or value == NULL:
            return None
        if isinstance(value, QDateTime):
            return value.date() if value.isValid() else None
        if isinstance(value, QDate):
            return value if value.isValid() else None
        # Valeur stockée sous forme de chaîne (ex. import depuis un fichier texte/CSV)
        text = str(value).strip()
        if not text:
            return None
        parsed = QDate.fromString(text, 'yyyy-MM-dd')
        if not parsed.isValid():
            parsed = QDateTime.fromString(text, 'yyyy-MM-ddTHH:mm:ss').date()
        return parsed if parsed.isValid() else None

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        etat_field = self.parameterAsString(parameters, self.ETAT_FIELD, context)
        date_field = self.parameterAsString(parameters, self.DATE_FIELD, context)
        etat_projet_value = self.parameterAsString(parameters, self.ETAT_PROJET_VALUES, context)
        etat_construction_value = self.parameterAsString(parameters, self.ETAT_CONSTRUCTION_VALUES, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        if etat_field not in layer.fields().names():
            feedback.reportError(self.tr("Le champ Etat '{}' n'existe pas dans la couche").format(etat_field))
            return {'OUTPUT': 'Erreur'}

        if date_field not in layer.fields().names():
            feedback.reportError(
                self.tr("Le champ Date de mise en service '{}' n'existe pas dans la couche").format(date_field)
            )
            return {'OUTPUT': 'Erreur'}

        today = QDate.currentDate()
        invalid_features = []

        for feature in layer.getFeatures():
            etat_value = feature[etat_field]
            etat_value = str(etat_value) if etat_value is not None and etat_value != NULL else None
            date_value = self._to_qdate(feature[date_field])

            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue

            if etat_value == etat_projet_value:
                if date_value is not None and date_value <= today:
                    invalid_features.append([
                        "Date de mise en service",
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        date_field,
                        "La Date de mise en service n'est pas cohérente avec l'Etat de l'objet",
                        geom.pointOnSurface()
                    ])
            elif etat_value == etat_construction_value:
                if date_value is None:
                    invalid_features.append([
                        "Date de mise en service",
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        date_field,
                        "La Date de mise en service n'est pas cohérente avec l'Etat de l'objet",
                        geom.pointOnSurface()
                    ])
                elif date_value <= today:
                    invalid_features.append([
                        "Date de mise en service",
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        date_field,
                        "La Date de mise en service n'est pas cohérente avec l'Etat de l'objet",
                        geom.pointOnSurface()
                    ])

        self.report_issues(invalid_features, "Incohérence Etat / Date de mise en service")

        return self.processing_done_result()
