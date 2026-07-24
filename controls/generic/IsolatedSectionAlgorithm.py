from qgis.core import (
QgsProcessingAlgorithm,
QgsProcessingParameterMultipleLayers,
QgsProcessing,
QgsProcessingParameterFile,
QgsProcessingParameterFeatureSink,
QgsWkbTypes,
QgsSpatialIndex,
QgsFeatureRequest
)
from ControlPointLayer import ControlPointLayer
import json


class IsolatedSectionAlgorithm(QgsProcessingAlgorithm):


    def initAlgorithm(self):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYERS',
                "Couches en entrée",
                layerType=QgsProcessing.TypeVectorLine
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
        layers = self.parameterAsLayerList(parameters, 'INPUT_LAYERS', context)
        json_path = self.parameterAsFile(parameters, 'PARAM_JSON', context)

        with open(json_path, "r", encoding="utf-8") as f:
            param_json = json.load(f)

        isolated_sections = []

        for layer in layers:
            if layer.name() not in param_json.keys():
                feedback.reportError('{} not in param.json'.format(layer.name()))
                continue

            geom_type = QgsWkbTypes.geometryType(layer.wkbType())
            if geom_type != QgsWkbTypes.LineGeometry:
                feedback.reportError(f"{layer.name()} n'est pas linéaire")
                continue

            # Récupérer la condition de filtrage depuis le JSON
            filter_condition = param_json[layer.name()]

            # Construire l'index spatial pour les tronçons filtrés
            spatial_index = QgsSpatialIndex()
            features_dict = {}

            # Appliquer le filtre depuis le JSON
            request = QgsFeatureRequest()
            if filter_condition:
                request.setFilterExpression(filter_condition)

            for f in layer.getFeatures(request):
                if not f.geometry() or not f.geometry().isGeosValid():
                    continue

                features_dict[f.id()] = f
                spatial_index.addFeature(f)

            # Détecter les tronçons isolés
            for fid, feature in features_dict.items():
                geom = feature.geometry()

                # Chercher les tronçons voisins (avec une petite tolérance)
                bbox = geom.boundingBox()
                bbox.grow(0.01)  # Tolérance de 1 cm

                nearby_ids = spatial_index.intersects(bbox)

                # Vérifier si le tronçon est connecté à d'autres
                is_isolated = True
                for nearby_id in nearby_ids:
                    if nearby_id == fid:
                        continue

                    nearby_feature = features_dict[nearby_id]
                    nearby_geom = nearby_feature.geometry()

                    # Vérifier si les géométries se touchent
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
            controlpoint_layer.save()

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
            "Ce contrôle détecte les tronçons isolés sur les réseaux routier, ferré et hydrographique."

    def createInstance(self):
        """Crée une nouvelle instance de l'algorithme"""
        return IsolatedSectionAlgorithm()