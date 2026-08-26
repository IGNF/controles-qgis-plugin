from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterVectorLayer,
QgsProcessingParameterField,
QgsProcessing,
QgsProcessingParameterFeatureSink,
QgsProcessingParameterEnum,
QgsPoint
)
from ControlPointLayer import ControlPointLayer

class NonZSectionAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                "Couche en entrée",
                types=[QgsProcessing.TypeVector]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'ATTRIBUTE_FIELD',
                'Attribut à vérifier',
                parentLayerParameterName='INPUT_LAYER',
                type=QgsProcessingParameterField.Any
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'ATTRIBUTE_VALUES',
                'Valeurs à contrôler',
                options=[],
                allowMultiple=True,
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
        attribute_field = self.parameterAsString(parameters, 'ATTRIBUTE_FIELD', context)

        # Récupérer les valeurs uniques de l'attribut pour construire les options
        unique_values = layer.uniqueValues(layer.fields().indexFromName(attribute_field))
        unique_values_list = sorted([str(v) for v in unique_values if v is not None])

        # Récupérer les indices des valeurs sélectionnées
        selected_indices = self.parameterAsEnums(parameters, 'ATTRIBUTE_VALUES', context)
        selected_values = [unique_values_list[i] for i in selected_indices]

        if attribute_field not in layer.fields().names():
            feedback.reportError(f"L'attribut '{attribute_field}' n'existe pas dans la couche {layer.name()}")
            return {'OUTPUT': 'Erreur'}

        non_z_objects = []

        for feature in layer.getFeatures():
            geom = feature.geometry()

            if geom.isEmpty() or not geom.isGeosValid():
                continue

            # Vérifier la valeur de l'attribut
            attribute_value = str(feature[attribute_field])
            if attribute_value not in selected_values:
                continue

            # Vérifier si au moins un Z est vide (None ou NaN)
            has_empty_z = False
            vertices = geom.vertices()

            while vertices.hasNext():
                vertex = vertices.next()
                if vertex.z() is None or vertex.z() != vertex.z():  # NaN check
                    has_empty_z = True
                    empty_z_point = QgsPoint(vertex.x(), vertex.y())
                    break

            if has_empty_z:
                non_z_objects.append([
                    'Tronçon sans Z',
                    layer.name(),
                    feature.id(),
                    'geometrie',
                    f"L'objet comporte au moins 1 point sans Z ({attribute_field}={attribute_value})",
                    empty_z_point
                ])

        if non_z_objects:
            controlpoint_layer = ControlPointLayer('Tronçons sans Z')
            controlpoint_layer.add_features(non_z_objects)
            controlpoint_layer.save()

        return {'OUTPUT': 'Traitement terminé'}

    def name(self):
        """Identifiant unique de l'algorithme"""
        return 'B.02'

    def displayName(self):
        """Nom affiché de l'algorithme"""
        return "Tronçons sans Z"

    def group(self):
        """Nom du groupe"""
        return 'Controles génériques Z'

    def groupId(self):
        """Identifiant du groupe"""
        return 'B'

    def shortHelpString(self):
        """Description de l'algorithme"""
        return \
            "Ce contrôle détecte les objets ayant au moins un Z vide et "\
            "de ‘Méthode d’acquisition altimétrique’ = ‘Photogrammétrie’, ‘Photogrammétrie longue focale’, ‘BDTopo’ ou ‘Levé GPS’"

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return NonZSectionAlgorithm()