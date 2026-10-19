from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsWkbTypes,
    QgsSpatialIndex
)
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list

from BaseControlAlgorithm import BaseControlAlgorithm


class IsolatedSectionAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'A.17'
    ALG_DISPLAY_NAME = "Géométrie tronçons isolés"
    ALG_GROUP = 'Controles génériques géométriques'
    ALG_GROUP_ID = 'A'
    ALG_HELP = (
        "Ce contrôle détecte les tronçons isolés sur les réseaux routier, ferré et hydrographique dits En service"
        "(valeur du champ Etat de l’objet)"
    )

    INPUT_LAYER = 'INPUT_LAYER'
    ETAT_FIELD = 'ETAT_FIELD'
    ETAT_VALUES = 'ETAT_VALUES'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ETAT_FIELD,
                self.tr("Champ Etat"),
                parentLayerParameterName=self.INPUT_LAYER,
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                self.ETAT_VALUES,
                self.tr("Valeurs Etat à contrôler"),
                parentLayerParameterName=self.INPUT_LAYER,
                parentFieldParameterName=self.ETAT_FIELD,
                allowMultiple=False,
                optional=False
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        etat_field = self.parameterAsString(parameters, self.ETAT_FIELD, context)

        if etat_field not in layer.fields().names():
            feedback.reportError(self.tr("Le champ Etat '{}' n'existe pas dans la couche").format(etat_field))
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via le widget (chaîne séparée par des virgules)
        etat_values = field_values_as_string_list(self.parameterAsString(parameters, self.ETAT_VALUES, context))

        isolated_sections = []

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(self.tr("{} n'est pas linéaire").format(layer.name()))
            return self.processing_done_result()

        spatial_index = QgsSpatialIndex()
        features_dict = {}

        for f in layer.getFeatures():
            etat_value = str(f[etat_field]) if f[etat_field] is not None else ''
            if etat_value not in etat_values:
                continue
            if not f.geometry() or not f.geometry().isGeosValid():
                continue
            features_dict[f.id()] = f
            spatial_index.addFeature(f)

        for fid, feature in features_dict.items():
            geom = feature.geometry()
            bbox = geom.boundingBox()
            bbox.grow(0.01)
            nearby_ids = spatial_index.intersects(bbox)
            is_isolated = True
            for nearby_id in nearby_ids:
                if nearby_id == fid:
                    continue
                nearby_feature = features_dict[nearby_id]
                nearby_geom = nearby_feature.geometry()
                if geom.touches(nearby_geom) or geom.intersects(nearby_geom):
                    is_isolated = False
                    break
            if is_isolated:
                isolated_sections.append([
                    'Géométrie tronçons isolés',
                    layer.name(),
                    feature.id(),
                    'geometry',
                    "Ce tronçon est isolé",
                    geom.centroid()
                ])

        self.report_issues(isolated_sections, 'Géométrie tronçons isolés')

        return self.processing_done_result()
