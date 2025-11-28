from qgis.core import QgsVectorLayer, QgsField, QgsProject, edit, QgsFeature, QgsVectorFileWriter
from qgis.PyQt.QtCore import QVariant
import os
import processing

class ControlPointLayer(QgsVectorLayer):

    def __init__(self, layer_name):
        QgsVectorLayer.__init__(self, "Point?crs=IGNF:LAMB93", layer_name, "memory")
        self.provider = self.dataProvider()
        self.provider.addAttributes([QgsField("type", QVariant.String),
                                QgsField("couche", QVariant.String),
                                QgsField("id", QVariant.String),
                                QgsField("attribut", QVariant.String),
                                QgsField("commentaire", QVariant.String)])
        self.updateFields()
        self.save()


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
        print(os.path.dirname(QgsProject.instance().fileName())+'/'+self.name())
        params = {'INPUT': self,
                  'OUTPUT': os.path.dirname(QgsProject.instance().fileName())+'/'+self.name()+'.gpkg',
                  'LAYER_NAME': self.name()}
        processing.run("native:savefeatures", params)
        layer_path = os.path.dirname(QgsProject.instance().fileName())+'/'+self.name()+'.gpkg'
        layer = QgsVectorLayer(layer_path+'|layername='+self.name(), self.name(), "ogr")
        QgsProject.instance().addMapLayer(layer)