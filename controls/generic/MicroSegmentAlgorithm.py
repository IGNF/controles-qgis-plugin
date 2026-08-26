from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterFile,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsGeometry
)
from ControlPointLayer import ControlPointLayer
import json


class MicroSegmentAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                'PARAM_JSON',
                'Paramètres JSON',
                extension='json'
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        micro_segment = []
        if layer.name() not in param_json.keys():
            feedback.reportError('{} not in param.json'.format(layer.name()))
            return {'OUTPUT': 'Traitement terminé'}

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
            feedback.reportError(f"{layer.name()} n'est ni linéaire ni surfacique")
            return {'OUTPUT': 'Traitement terminé'}

        taille_mini = param_json[layer.name()]
        for f in layer.getFeatures():
            if not f.geometry().isGeosValid():
                continue
            if (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.LineGeometry
                    and QgsWkbTypes.isMultiType(layer.wkbType())):
                geom = f.geometry().asMultiPolyline()
                geom = geom[0]
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.LineGeometry
                  and QgsWkbTypes.isSingleType(layer.wkbType())):
                geom = f.geometry().asPolyline()
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PolygonGeometry
                  and QgsWkbTypes.isSingleType(layer.wkbType())):
                geom = f.geometry().asPolygon()
            elif (QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PolygonGeometry
                  and QgsWkbTypes.isMultiType(layer.wkbType())):
                geom = f.geometry().asMultiPolygon()
                geom = geom[0][0]
            for i in range(len(geom) - 1):
                segment = QgsGeometry.fromPolylineXY([geom[i], geom[i + 1]])
                if segment.length() < int(taille_mini):
                    micro_segment.append(['Micro-segments',
                                          layer.name(),
                                          f.id(),
                                          'geometry',
                                          "L'objet contient un micro-segment",
                                          f.geometry().centroid()])

        if micro_segment != []:
            controlpoint_layer = ControlPointLayer('Micro-segments')
            controlpoint_layer.add_features(micro_segment)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.03'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Micro-segments"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte deux points consécutifs non superposés et situés à une distance inférieure ou égale à 10 cm l'un de l'autre ."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return MicroSegmentAlgorithm()