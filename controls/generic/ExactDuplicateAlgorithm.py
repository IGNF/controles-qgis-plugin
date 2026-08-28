from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
QgsWkbTypes
)
from ControlPointLayer import ControlPointLayer


class ExactDuplicateAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        excluded_param = QgsProcessingParameterField(
            'EXCLUDED_FIELDS',
            'Champs à exclure',
            parentLayerParameterName='INPUT_LAYER',
            allowMultiple=True,
            optional=True
        )
        self.addParameter(excluded_param)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'OUTPUT',
                'Sortie'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT_LAYER', context)
        excluded_fields = self.parameterAsFields(parameters, 'EXCLUDED_FIELDS', context) or []

        doublons = []
        geom_dict = {}
        for f in layer.getFeatures():
            if not f.geometry().isGeosValid():
                continue
            geom = f.geometry().asWkt()
            if geom in geom_dict.keys():
                doublon = True
                fields_names = [field.name() for field in layer.fields()]
                for idx, att_value in enumerate(f.attributes()):
                    att_name = fields_names[idx]
                    if att_name in excluded_fields:
                        continue
                    if att_value != geom_dict[geom].attributes()[idx]:
                        doublon = False
                        break
                if doublon:
                    geom_type = QgsWkbTypes.geometryType(layer.wkbType())
                    if geom_type == QgsWkbTypes.PointGeometry:
                        doublon_type = "Doublons ponctuels parfaits"
                    elif geom_type == QgsWkbTypes.LineGeometry:
                        doublon_type = "Doublons linéaires parfaits"
                    elif geom_type == QgsWkbTypes.PolygonGeometry:
                        doublon_type = "Doublons surfaciques parfaits"
                    else:
                        doublon_type = "Doublons parfaits"
                    doublons.append(['Doublons parfaits',
                                     layer.name(),
                                     geom_dict[geom].id(),
                                     'geometry',
                                     doublon_type,
                                     f.geometry().pointOnSurface()])
            else:
                geom_dict[geom] = f

        if doublons != []:
            controlpoint_layer = ControlPointLayer('Doublons parfaits')
            controlpoint_layer.add_features(doublons)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.05'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Doublons parfaits"

    def group(self):
        """Nom du groupe"""
        return 'controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return "Ce contrôle détecte des objets de même couche ayant exactement les mêmes attributs et la même géométrie"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return ExactDuplicateAlgorithm()