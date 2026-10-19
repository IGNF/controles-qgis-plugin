from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes
)

from BaseControlAlgorithm import BaseControlAlgorithm


class ExactDuplicateAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.05'
    ALG_DISPLAY_NAME = "Doublons parfaits"
    ALG_GROUP = 'controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = "Ce contrôle détecte des objets de même couche ayant exactement les mêmes attributs et la même géométrie"

    INPUT_LAYER = 'INPUT_LAYER'
    EXCLUDED_FIELDS = 'EXCLUDED_FIELDS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        excluded_param = QgsProcessingParameterField(
            self.EXCLUDED_FIELDS,
            self.tr('Champs à exclure'),
            parentLayerParameterName=self.INPUT_LAYER,
            allowMultiple=True,
            optional=True
        )
        self.addParameter(excluded_param)
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        excluded_fields = self.parameterAsFields(parameters, self.EXCLUDED_FIELDS, context) or []

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

        self.report_issues(doublons, 'Doublons parfaits')

        return self.processing_done_result()
