# -*- coding: utf-8 -*-
"""
Widget wrapper GUI pour QgsProcessingParameterFieldValues.

Ce module enregistre, auprès du registre GUI de Processing, un widget qui se
met à jour dynamiquement : dès que l'utilisateur change la couche ou le champ
associé au paramètre, la liste des valeurs proposées est reconstruite à partir
des valeurs uniques réellement présentes dans le champ sélectionné.

L'enregistrement se fait via register_field_values_widget() (à appeler dans
initGui() du plugin) et le retrait via unregister_field_values_widget()
(à appeler dans unload()).
"""
from qgis.core import QgsProject
from qgis.gui import (
    QgsAbstractProcessingParameterWidgetWrapper,
    QgsProcessingParameterWidgetFactoryInterface,
)

try:
    from qgis.gui import QgsCheckableComboBox
    HAS_CHECKABLE_COMBO = True
except ImportError:
    QgsCheckableComboBox = None
    HAS_CHECKABLE_COMBO = False

from qgis.PyQt.QtWidgets import QComboBox

from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list


class FieldValuesWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):
    """Widget affichant/éditant les valeurs sélectionnées, mis à jour dynamiquement."""

    def __init__(self, parameter, wrapper_type):
        super().__init__(parameter, wrapper_type)
        self._combo = None
        self._wrappers = []
        self._allow_multiple = getattr(parameter, 'allowMultiple', True)

    def _use_checkable_combo(self):
        return HAS_CHECKABLE_COMBO and self._allow_multiple

    def createWidget(self):
        if self._use_checkable_combo():
            self._combo = QgsCheckableComboBox()
        else:
            # allowMultiple=False (ou QgsCheckableComboBox indisponible) :
            # simple combo à sélection unique, non éditable.
            self._combo = QComboBox()
            self._combo.setEditable(False)
        return self._combo

    def setWidgetValue(self, value, context):
        if self._combo is None:
            return
        values = field_values_as_string_list(value)
        if self._use_checkable_combo() and hasattr(self._combo, 'setCheckedItems'):
            self._combo.setCheckedItems(values)
        elif values:
            idx = self._combo.findText(values[0])
            if idx >= 0:
                self._combo.setCurrentIndex(idx)

    def widgetValue(self):
        if self._combo is None:
            return ''
        if self._use_checkable_combo() and hasattr(self._combo, 'checkedItems'):
            return ','.join(self._combo.checkedItems())
        return self._combo.currentText()

    def postInitialize(self, wrappers):
        """Appelé par QGIS une fois tous les widgets du dialogue créés."""
        self._wrappers = wrappers
        param = self.parameterDefinition()

        for wrapper in wrappers:
            try:
                pname = wrapper.parameterDefinition().name()
            except Exception:
                continue
            if pname in (param.parentLayerParameterName, param.parentFieldParameterName):
                try:
                    wrapper.widgetValueHasChanged.connect(self._on_parent_changed)
                except Exception:
                    pass

        self._update_choices()

    def _on_parent_changed(self, *args):
        self._update_choices()

    def _resolve_layer(self, value):
        """Résout la valeur brute du widget de couche vers un QgsVectorLayer."""
        if value is None:
            return None
        # Déjà une couche
        if hasattr(value, 'fields'):
            return value
        # Chaîne : id ou nom de couche
        layer = QgsProject.instance().mapLayer(str(value))
        if layer is not None:
            return layer
        found = QgsProject.instance().mapLayersByName(str(value))
        if found:
            return found[0]
        return None

    def _update_choices(self):
        if self._combo is None:
            return

        param = self.parameterDefinition()
        layer = None
        field_name = None

        for wrapper in self._wrappers:
            pname = wrapper.parameterDefinition().name()
            if pname == param.parentLayerParameterName:
                try:
                    layer = self._resolve_layer(wrapper.parameterValue())
                except Exception:
                    layer = None
            elif pname == param.parentFieldParameterName:
                try:
                    field_name = wrapper.parameterValue()
                except Exception:
                    field_name = None

        # Conserver la sélection courante si possible
        current_values = []
        if self._use_checkable_combo() and hasattr(self._combo, 'checkedItems'):
            current_values = self._combo.checkedItems()
        elif self._combo.currentText():
            current_values = [self._combo.currentText()]

        self._combo.clear()

        if layer is None or not field_name:
            return

        try:
            idx = layer.fields().indexFromName(field_name)
            if idx < 0:
                return
            unique_values = layer.uniqueValues(idx)
            values_list = sorted({str(v) for v in unique_values if v is not None and str(v) != ''})
        except Exception:
            values_list = []

        if not values_list:
            return

        if HAS_CHECKABLE_COMBO:
            self._combo.addItems(values_list)
            kept = [v for v in current_values if v in values_list]
            if kept:
                if self._use_checkable_combo():
                    self._combo.setCheckedItems(kept)
                else:
                    idx = self._combo.findText(kept[0])
                    if idx >= 0:
                        self._combo.setCurrentIndex(idx)
        else:
            self._combo.addItems(values_list)


class FieldValuesWidgetFactory(QgsProcessingParameterWidgetFactoryInterface):
    """Factory reliant le type de paramètre 'field_values' à son widget."""

    def parameterType(self):
        return QgsProcessingParameterFieldValues.TYPE_NAME

    def compatibleDataTypes(self, parameter):
        return []

    def createWidgetWrapper(self, parameter, wrapper_type):
        return FieldValuesWidgetWrapper(parameter, wrapper_type)

    def createModelerWidgetWrapper(self, model, child_id, parameter, context):
        from qgis.gui import QgsProcessingModelerParameterWidget
        widget = QgsProcessingModelerParameterWidget(model, child_id, parameter, context)
        widget.populateSources([], [], [])
        return widget


_factory_instance = None


def register_field_values_widget():
    """Enregistre le widget dynamique auprès de QGIS (à appeler dans initGui())."""
    global _factory_instance
    try:
        from qgis.gui import QgsGui
        if _factory_instance is None:
            _factory_instance = FieldValuesWidgetFactory()
        QgsGui.instance().processingGuiRegistry().addParameterWidgetFactory(_factory_instance)
    except Exception:
        # Ne bloque jamais le chargement du plugin en cas d'incompatibilité GUI
        pass


def unregister_field_values_widget():
    """Retire le widget dynamique (à appeler dans unload())."""
    global _factory_instance
    try:
        from qgis.gui import QgsGui
        if _factory_instance is not None:
            QgsGui.instance().processingGuiRegistry().removeParameterWidgetFactory(_factory_instance)
    except Exception:
        pass


