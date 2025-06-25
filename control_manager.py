from qgis.core import QgsVectorLayer, QgsField, QgsProject
from qgis.PyQt.QtCore import QVariant

def create_controlpoint_layer(layer_name):
    controlpoint_layer = QgsVectorLayer(
        "Point?crs=IGNF:LAMB93", layer_name, "memory")
    provider = controlpoint_layer.dataProvider()
    provider.addAttributes([QgsField("type", QVariant.String),
                            QgsField("couche", QVariant.String),
                            QgsField("id", QVariant.String),
                            QgsField("commentaire", QVariant.String)])
    controlpoint_layer.updateFields()
    QgsProject.instance().addMapLayer(controlpoint_layer)
    return controlpoint_layer