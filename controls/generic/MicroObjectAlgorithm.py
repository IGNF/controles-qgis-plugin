from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterNumber,
    QgsWkbTypes
)

from BaseControlAlgorithm import BaseControlAlgorithm


class MicroObjectAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.15'
    ALG_DISPLAY_NAME = "Micro-objets"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte :"
        "Les objets linéaires de longueur ≤ 3 m ou < 2 m pour les Tronçons de route"
        "Les objets surfaciques de surface ≤ 9 m2 ou < 0.2 m2 pour les Bâtiments et Réservoirs ou ≤ 2 m2 pour les Constructions surfaciques et Postes de transformation"
    )

    INPUT_LAYER = 'INPUT_LAYER'
    THRESHOLD = 'THRESHOLD'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                self.tr('Seuil (m ou m²)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=3.0,
                minValue=0.0
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)

        micro_objects = []
        if layer.geometryType() not in [QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry]:
            feedback.pushWarning(self.tr("La couche {} n'est ni linéaire ni surfacique, elle sera ignorée").format(layer.name()))
            return self.processing_done_result()

        for feature in layer.getFeatures():
            comment = ''
            geom = feature.geometry()
            if geom.isEmpty() or not geom.isGeosValid():
                continue
            is_micro = False
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                length = geom.length()
                if length <= threshold:
                    is_micro = True
                    comment = 'Objet de longueur <= {}m'.format(length)
            elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                area = geom.area()
                if area <= threshold:
                    is_micro = True
                    comment = 'Objet de surface <= {}m²'.format(area)
            if is_micro:
                micro_objects.append([
                    'Micro-objet',
                    layer.name(),
                    feature.id(),
                    'geometrie',
                    comment,
                    geom.centroid()
                ])

        self.report_issues(micro_objects, 'Micro-objets')

        return self.processing_done_result()
