from qgis.core import QgsVectorLayer, QgsField, QgsProject, QgsFeature
from qgis.PyQt.QtCore import QVariant

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


    def save_as_temp_layer(self):
        """Ajoute la couche directement dans le projet comme couche temporaire (sans fichier)."""
        QgsProject.instance().addMapLayer(self)
