# -*- coding: utf-8 -*-
"""
Paramètre de processing personnalisé permettant de choisir une ou plusieurs
valeurs parmi les valeurs uniques présentes dans un champ d'une couche.

Contrairement à QgsProcessingParameterEnum (dont les options sont figées à la
construction du paramètre), ce paramètre est associé, côté GUI, à un widget
(voir FieldValuesWidget.py) qui reconstruit dynamiquement la liste des valeurs
proposées en fonction de la couche et du champ sélectionnés dans le dialogue
de l'algorithme.

La valeur est stockée en interne comme une chaîne de valeurs séparées par des
virgules (compatible avec un usage en ligne de commande / modeleur).
"""
from qgis.core import QgsProcessingParameterString, QgsProcessingParameterDefinition


class QgsProcessingParameterFieldValues(QgsProcessingParameterString):
    """Paramètre représentant une sélection de valeurs d'un champ."""

    TYPE_NAME = 'field_values'

    def __init__(self, name, description='', parentLayerParameterName='',
                 parentFieldParameterName='', allowMultiple=True,
                 defaultValue=None, optional=False):
        super().__init__(name, description, defaultValue=defaultValue,
                          multiLine=False, optional=optional)
        self.parentLayerParameterName = parentLayerParameterName
        self.parentFieldParameterName = parentFieldParameterName
        self.allowMultiple = allowMultiple

    def type(self):
        return QgsProcessingParameterFieldValues.TYPE_NAME

    @staticmethod
    def typeName():
        return QgsProcessingParameterFieldValues.TYPE_NAME

    def clone(self):
        is_optional = bool(self.flags() & QgsProcessingParameterDefinition.FlagOptional)
        return QgsProcessingParameterFieldValues(
            self.name(),
            self.description(),
            self.parentLayerParameterName,
            self.parentFieldParameterName,
            self.allowMultiple,
            self.defaultValue(),
            is_optional
        )


def field_values_as_string_list(value):
    """Convertit la valeur brute du paramètre (str ou liste) en liste de chaînes.

    Fonction autonome (et non méthode statique de la classe) car les
    sous-classes de classes SIP (C++) comme QgsProcessingParameterString
    utilisent une métaclasse qui ne préserve pas correctement @staticmethod
    (l'appel se retrouve lié, provoquant un argument 'self' supplémentaire).
    """
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v) != '']
    return [v for v in str(value).split(',') if v != '']



