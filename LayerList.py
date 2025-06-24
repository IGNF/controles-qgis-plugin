from qgis.PyQt.QtWidgets import QListWidget

class LayerList(QListWidget):

    def __init__(self, iface):
        super(LayerList, self).__init__()