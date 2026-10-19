from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessing,
QgsProcessingParameterField,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsSpatialIndex
)
from ControlPointLayer import ControlPointLayer
from FieldValuesParameter import QgsProcessingParameterFieldValues, field_values_as_string_list


class IsolatedSectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'ETAT_FIELD',
                "Champ Etat",
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.String
            )
        )
        self.addParameter(
            QgsProcessingParameterFieldValues(
                'ETAT_VALUES',
                "Valeurs Etat à contrôler",
                parentLayerParameterName='INPUT_LAYER',
                parentFieldParameterName='ETAT_FIELD',
                allowMultiple=False,
                optional=False
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
        etat_field = self.parameterAsString(parameters, 'ETAT_FIELD', context)

        if etat_field not in layer.fields().names():
            feedback.reportError(f"Le champ Etat '{etat_field}' n'existe pas dans la couche")
            return {'OUTPUT': 'Erreur'}

        # Valeurs sélectionnées dynamiquement via le widget (chaîne séparée par des virgules)
        etat_values = field_values_as_string_list(self.parameterAsString(parameters, 'ETAT_VALUES', context))

        isolated_sections = []

        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type != QgsWkbTypes.LineGeometry:
            feedback.reportError(f"{layer.name()} n'est pas linéaire")
            return {'OUTPUT': 'Traitement terminé'}

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

        if isolated_sections:
            controlpoint_layer = ControlPointLayer('Géométrie tronçons isolés')
            controlpoint_layer.add_features(isolated_sections)
            controlpoint_layer.save_as_temp_layer()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'A.17'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Géométrie tronçons isolés"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques géométriques'

    def groupId(self):
        """Identifiant du groupe"""
        return 'A'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les tronçons isolés sur les réseaux routier, ferré et hydrographique dits En service"\
            "(valeur du champ Etat de l’objet)"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return IsolatedSectionAlgorithm()