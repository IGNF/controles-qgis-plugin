from qgis.PyQt.QtWidgets import QListWidget, QListWidgetItem
from qgis import QtCore
import os

class ControlList(QListWidget):

    def __init__(self, iface):
        super(ControlList, self).__init__()


    def load_controls(self):
        directory_path = os.path.dirname(__file__)+'/controls'
        files = [f.split('.')[0].replace('_',' ') for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        for i in files:
            item = QListWidgetItem(i)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.addItem(i)
        self.show()