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

from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterFeatureSink

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
        return QgsProcessingAlgorithm.tr(self, string)

    # ------------------------------------------------------------------
    # Paramètres communs
    # ------------------------------------------------------------------
    def initAlgorithm(self, config=None):
        """
        Ajoute le paramètre de sortie standard ('OUTPUT').
        Les sous-classes doivent ajouter leurs propres paramètres AVANT
        d'appeler `super().initAlgorithm(config)`.
        """
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
    # Helpers couche de résultats
    # ------------------------------------------------------------------
    def report_issues(self, issues, layer_name=None):
        """
        Crée une couche de points de contrôle (ControlPointLayer) à partir
        d'une liste d'anomalies détectées et l'ajoute au projet si elle
        contient des entités.

        :param issues: liste d'éléments [type, couche, id, attribut, commentaire, geometry]
        :param layer_name: nom de la couche résultat (par défaut : displayName())
        :return: la ControlPointLayer créée, ou None si `issues` est vide
        """
        if not issues:
            return None
        controlpoint_layer = ControlPointLayer(layer_name or self.displayName())
        controlpoint_layer.add_features(issues)
        controlpoint_layer.save_as_temp_layer()
        return controlpoint_layer

    @staticmethod
    def processing_done_result():
        """Message de retour standard pour `processAlgorithm()`."""
        return {'OUTPUT': 'Traitement terminé'}

