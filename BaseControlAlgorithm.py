# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BaseControlAlgorithm
                                 A QGIS plugin
 Classe de base commune à tous les algorithmes de contrôle BDUni.

 Cette classe factorise les comportements identiques retrouvés dans les
 70+ algorithmes du dossier `controls/` :
   - métadonnées (name, displayName, group, groupId, shortHelpString, createInstance)
   - ajout du paramètre de sortie standard
   - chargement du fichier JSON de paramétrage ('PARAM_JSON')
   - récupération des paramètres associés à une couche + remontée d'erreur
   - création et ajout au projet d'une couche de résultats (ControlPointLayer)
   - message de retour standard de `processAlgorithm`

 Utilisation dans un algorithme concret :

     from BaseControlAlgorithm import BaseControlAlgorithm

     class MonControleAlgorithm(BaseControlAlgorithm):
         ALG_NAME = 'A.01'
         ALG_DISPLAY_NAME = "Mon contrôle"
         ALG_GROUP = 'Controles génériques'
         ALG_GROUP_ID = 'A'
         ALG_HELP = "Description du contrôle."

         def initAlgorithm(self, config=None):
             self.addParameter(QgsProcessingParameterVectorLayer('INPUT_LAYER', ...))
             super().initAlgorithm(config)  # ajoute le paramètre OUTPUT

         def processAlgorithm(self, parameters, context, feedback):
             layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
             issues = [...]
             self.report_issues(issues)
             return self.processing_done_result()

                               -------------------
        begin                : 2025-06-11
        copyright            : (C) 2025 by GSchittek
        email                : gabin.schittek@ign.fr
 ***************************************************************************/
"""

import json
import logging
import inspect

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterField,
    QgsFeatureSink,
    QgsWkbTypes,
    NULL,
)

from ControlPointLayer import ControlPointLayer

logger = logging.getLogger(__name__)


class BaseControlAlgorithm(QgsProcessingAlgorithm):
    """Classe de base pour tous les algorithmes de contrôle BDUni."""

    # À redéfinir dans chaque sous-classe
    ALG_NAME = None
    ALG_DISPLAY_NAME = None
    ALG_GROUP = None
    ALG_GROUP_ID = None
    ALG_HELP = ""

    OUTPUT = 'OUTPUT'
    PARAM_JSON = 'PARAM_JSON'

    # Nom par défaut du paramètre de couche en entrée (défini par les
    # sous-classes), utilisé comme parentLayerParameterName pour ID_FIELD
    INPUT_LAYER = 'INPUT_LAYER'

    # Nom par défaut du paramètre permettant de choisir un champ identifiant
    ID_FIELD = 'ID_FIELD'

    def __init_subclass__(cls, **kwargs):
        """
        Vérifie, dès la définition de la classe, que chaque sous-classe
        redéfinit bien `ALG_NAME`. Cela permet de détecter l'oubli au
        moment de l'import du module plutôt qu'au premier appel de `name()`.
        """
        super().__init_subclass__(**kwargs)
        if cls.ALG_NAME is None:
            raise NotImplementedError(f"{cls.__name__} doit définir ALG_NAME")

    # ------------------------------------------------------------------
    # Métadonnées communes
    # ------------------------------------------------------------------
    def name(self):
        """Identifiant unique de l'algorithme."""
        if not self.ALG_NAME:
            raise NotImplementedError(f"{type(self).__name__} doit définir ALG_NAME")
        return self.ALG_NAME

    def displayName(self):
        """Nom affiché de l'algorithme."""
        return self.tr(self.ALG_DISPLAY_NAME or self.ALG_NAME)

    def group(self):
        """Nom du groupe."""
        return self.tr(self.ALG_GROUP or '')

    def groupId(self):
        """Identifiant du groupe."""
        return self.ALG_GROUP_ID or ''

    def shortHelpString(self):
        """Description de l'algorithme."""
        return self.tr(self.ALG_HELP or '')

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme (factory générique)."""
        return type(self)()

    def tr(self, string):
        return QCoreApplication.translate(self.__class__.__name__, string)

    # ------------------------------------------------------------------
    # Paramètres communs
    # ------------------------------------------------------------------
    def initAlgorithm(self, config=None):
        """
        Ajoute le paramètre de sortie standard ('OUTPUT') ainsi que le
        paramètre optionnel 'ID_FIELD' permettant de choisir un champ à
        utiliser comme identifiant dans la couche de résultats (à la place
        de `feature.id()`).
        Les sous-classes doivent ajouter leurs propres paramètres AVANT
        d'appeler `super().initAlgorithm(config)`.
        """
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr("Identifiant"),
                parentLayerParameterName=self.INPUT_LAYER,
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Sortie'), optional=True)
        )

    # ------------------------------------------------------------------
    # Helpers JSON de paramétrage
    # ------------------------------------------------------------------
    @staticmethod
    def load_json_parameters(json_path):
        """Charge et retourne le contenu d'un fichier JSON de paramétrage."""
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_layer_json_parameters(self, param_json, layer, feedback):
        """
        Récupère les paramètres JSON associés à une couche donnée.
        Signale une erreur via `feedback` et retourne None si la couche
        n'est pas présente dans le fichier JSON.
        """
        if layer.name() not in param_json:
            feedback.reportError(
                self.tr("{} n'est pas présent dans le fichier json de paramétrage").format(layer.name())
            )
            return None
        return param_json[layer.name()]

    # ------------------------------------------------------------------
    # Helpers champ identifiant (remplace feature.id())
    # ------------------------------------------------------------------
    def add_id_field_parameter(self, parent_layer_parameter_name, field_param_name=None, description=None):
        """
        Ajoute un paramètre optionnel permettant de choisir, pour une couche
        donnée, un champ à utiliser comme identifiant dans la couche de
        résultats à la place de `feature.id()`.

        :param parent_layer_parameter_name: nom du paramètre de couche associé
        :param field_param_name: nom du paramètre créé (par défaut : ID_FIELD,
            ou ID_FIELD_<parent_layer_parameter_name> si plusieurs couches)
        :param description: libellé affiché (par défaut généré automatiquement)
        """
        field_param_name = field_param_name or self.ID_FIELD
        self.addParameter(
            QgsProcessingParameterField(
                field_param_name,
                self.tr(description or "Champ identifiant (remplace l'id de l'entité)"),
                parentLayerParameterName=parent_layer_parameter_name,
                optional=True
            )
        )

    def get_id_field(self, parameters, context, field_param_name=None):
        """Récupère le nom du champ identifiant choisi (ou None si non défini)."""
        field_param_name = field_param_name or self.ID_FIELD
        if field_param_name not in parameters:
            return None
        value = self.parameterAsString(parameters, field_param_name, context)
        return value or None

    @staticmethod
    def get_feature_identifier(feature, id_field=None):
        """
        Retourne l'identifiant à utiliser pour une entité dans la couche de
        résultats : la valeur du champ `id_field` si celui-ci est fourni et
        valide, sinon `feature.id()`.
        """
        if id_field:
            try:
                value = feature[id_field]
                if value is not None and str(value) != '':
                    return value
            except KeyError:
                pass
        return feature.id()

    def validate_id_field(self, layers, id_field, feedback):
        """
        Vérifie que le champ identifiant choisi (`id_field`) respecte la
        contrainte NOT NULL / UNIQUE, pour chaque couche fournie dans
        laquelle ce champ existe effectivement.

        :param layers: une couche, ou une liste/tuple de couches
        :param id_field: nom du champ identifiant choisi (ou None)
        :param feedback: objet feedback de l'algorithme (pour remonter l'erreur)
        :return: True si la contrainte est respectée (ou si id_field est None
            ou si le champ n'existe dans aucune des couches), False sinon
            (une erreur est alors remontée via `feedback`).
        """
        if not id_field:
            return True
        if not isinstance(layers, (list, tuple)):
            layers = [layers]

        for layer in layers:
            if layer is None or id_field not in layer.fields().names():
                continue

            seen_values = set()
            for feature in layer.getFeatures():
                value = feature[id_field]
                if value is None or value == NULL or str(value) == '':
                    feedback.reportError(
                        self.tr(
                            "Le champ identifiant '{}' contient des valeurs vides dans la couche '{}' : "
                            "il doit être non nul et unique."
                        ).format(id_field, layer.name())
                    )
                    return False
                if value in seen_values:
                    feedback.reportError(
                        self.tr(
                            "Le champ identifiant '{}' contient des valeurs en doublon dans la couche '{}' "
                            "(valeur : '{}') : il doit être non nul et unique."
                        ).format(id_field, layer.name(), value)
                    )
                    return False
                seen_values.add(value)

        return True

    def get_validated_id_field(self, parameters, context, layers, feedback, field_param_name=None):
        """
        Raccourci combinant `get_id_field` et `validate_id_field`.

        :return: tuple (id_field, ok). Si `ok` est False, une erreur a déjà
            été remontée via `feedback` et l'algorithme appelant doit
            interrompre son traitement (`return {'OUTPUT': 'Erreur'}`).
        """
        id_field = self.get_id_field(parameters, context, field_param_name)
        ok = self.validate_id_field(layers, id_field, feedback)
        return id_field, ok

    # ------------------------------------------------------------------
    # Helpers couche de résultats
    # ------------------------------------------------------------------
    @staticmethod
    def _get_calling_processing_context():
        """
        Retrouve les objets `parameters` et `context` de l'appel en cours à
        `processAlgorithm` en remontant la pile d'appels. Cela permet à
        `report_issues` d'accéder au paramètre de sortie `OUTPUT` sans que
        chaque sous-classe ait besoin de les lui transmettre explicitement
        (tous les appels à `report_issues` ont lieu depuis `processAlgorithm`,
        qui reçoit toujours `parameters` et `context`).

        :return: tuple (parameters, context), ou (None, None) si introuvable.
        """
        frame = inspect.currentframe()
        try:
            caller = frame.f_back.f_back if frame is not None else None
            depth = 0
            while caller is not None and depth < 5:
                local_vars = caller.f_locals
                if 'parameters' in local_vars and 'context' in local_vars:
                    return local_vars['parameters'], local_vars['context']
                caller = caller.f_back
                depth += 1
            return None, None
        finally:
            del frame

    def report_issues(self, issues, layer_name=None):
        """
        Crée une couche de points de contrôle (ControlPointLayer) à partir
        d'une liste d'anomalies détectées.

        Si le paramètre de sortie `OUTPUT` a été renseigné lors de
        l'exécution de l'algorithme (ex. : exécution via la boîte à outils
        Processing avec une destination choisie), les entités sont écrites
        dans le sink correspondant. Sinon (ex. : exécution via le dialogue
        personnalisé du plugin, qui ne renseigne pas `OUTPUT`), la couche
        est ajoutée au projet comme couche temporaire (comportement
        historique).

        :param issues: liste d'éléments [type, couche, id, attribut, commentaire, geometry]
        :param layer_name: nom de la couche résultat (par défaut : displayName())
        :return: la ControlPointLayer créée, ou None si `issues` est vide
        """
        if not issues:
            return None

        controlpoint_layer = ControlPointLayer(layer_name or self.displayName())
        controlpoint_layer.add_features(issues)

        parameters, context = self._get_calling_processing_context()
        sink = None
        dest_id = None
        if parameters is not None and context is not None:
            try:
                sink, dest_id = self.parameterAsSink(
                    parameters,
                    self.OUTPUT,
                    context,
                    controlpoint_layer.fields(),
                    QgsWkbTypes.Point,
                    controlpoint_layer.crs(),
                )
            except Exception as e:
                logger.warning(
                    "Impossible de créer le sink OUTPUT pour '%s' : %s", self.displayName(), e
                )
                sink = None

        if sink is not None:
            for feature in controlpoint_layer.getFeatures():
                sink.addFeature(feature, QgsFeatureSink.FastInsert)
            self._last_output_dest_id = dest_id
        else:
            self._last_output_dest_id = None
            controlpoint_layer.save_as_temp_layer()

        return controlpoint_layer

    def processing_done_result(self):
        """
        Message/résultat de retour standard pour `processAlgorithm()`.
        Si `report_issues` a écrit dans le sink `OUTPUT`, retourne son
        identifiant de destination (nécessaire à QGIS pour exposer/charger
        la couche résultat). Sinon, retourne le message historique.
        """
        dest_id = getattr(self, '_last_output_dest_id', None)
        if dest_id is not None:
            return {self.OUTPUT: dest_id}
        return {self.OUTPUT: 'Traitement terminé'}

