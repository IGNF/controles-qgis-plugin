from qgis.core import QgsVectorLayer, QgsField, QgsProject, edit, QgsFeature, QgsVectorFileWriter
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QMessageBox
import os
from qgis import processing

class ControlPointLayer(QgsVectorLayer):

    def __init__(self, layer_name):
        QgsVectorLayer.__init__(self, "Point?crs=IGNF:LAMB93", layer_name, "memory")
        self.provider = self.dataProvider()
        self.provider.addAttributes([QgsField("type", QVariant.String),
                                QgsField("couche", QVariant.String),
                                QgsField("id", QVariant.String),
                                QgsField("attribut", QVariant.String),
                                QgsField("Libellé", QVariant.String)])
        self.updateFields()

    def add_features(self,features_array):
        """
        :param features_array: [type, couche, id, attribut, commentaire, geometry]
        """
        for f in features_array:
            controlpoint = QgsFeature()
            controlpoint.setGeometry(f[-1])
            controlpoint.setAttributes(f[:-1])
            self.provider.addFeature(controlpoint)


    def save(self):
        layer_path = os.path.join(os.path.dirname(QgsProject.instance().fileName()), self.name() + '.gpkg')

        if os.path.exists(layer_path):
            reply = QMessageBox.question(
                None,
                "Fichier existant",
                f"La couche '{self.name()}.gpkg' existe déjà.\nVoulez-vous la remplacer ?",
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if reply != QMessageBox.Yes:
                return

            # Retirer du projet toute couche pointant vers ce fichier (libère le verrou OGR)
            project = QgsProject.instance()
            layers_to_remove = [lid for lid, lyr in project.mapLayers().items()
                                if os.path.normpath(lyr.source().split('|')[0]) == os.path.normpath(layer_path)]
            if layers_to_remove:
                project.removeMapLayers(layers_to_remove)

            os.remove(layer_path)

        project = QgsProject.instance()
        params = {'INPUT': self,
                  'OUTPUT': layer_path,
                  'LAYER_NAME': self.name()}
        processing.run("native:savefeatures", params)
        layer = QgsVectorLayer(layer_path + '|layername=' + self.name(), self.name(), "ogr")
        project.addMapLayer(layer)
        QgsProject.instance().addMapLayer(layer)

    def save_as_temp_layer(self):
        """Ajoute la couche directement dans le projet comme couche temporaire (sans fichier)."""
        QgsProject.instance().addMapLayer(self)
