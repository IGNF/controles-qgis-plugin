# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ControlesBDUniProvider
                                 A QGIS plugin
 Processing Provider for BDUni Controls
                              -------------------
        begin                : 2025-06-11
        copyright            : (C) 2025 by GSchittek
        email                : gabin.schittek@ign.fr
 ***************************************************************************/
"""

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
import os
import importlib
import inspect
from qgis.core import QgsProcessingAlgorithm


class ControlesBDUniProvider(QgsProcessingProvider):
    """Provider de processing pour les contrôles BDUni"""

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        """Identifiant unique du provider"""
        return 'controles_bduni'

    def name(self):
        """Nom affiché du provider"""
        return 'Contrôles BDUni'

    def icon(self):
        """Icône du provider"""
        return QIcon(os.path.join(os.path.dirname(__file__), 'icon.png'))

    def loadAlgorithms(self):
        """Charge tous les algorithmes de contrôle"""
        controls_dir = os.path.join(os.path.dirname(__file__), 'controls')

        # Structure des catégories
        categories = {
            'administrative': 'Administratif',
            'building': 'Bâti',
            'complex': 'Complexe',
            'electric': 'Électrique',
            'generic': 'Générique',
            'hydro': 'Hydro',
            'medium_scale': 'Moyenne échelle',
            'metadata': 'Métadonnées',
            'transport': 'Transport'
        }

        # Parcourir chaque catégorie
        for category_dir, category_name in categories.items():
            category_path = os.path.join(controls_dir, category_dir)
            if not os.path.isdir(category_path):
                continue

            # Parcourir les fichiers Python dans chaque catégorie
            for filename in os.listdir(category_path):
                if not filename.endswith('.py') or filename.startswith('__'):
                    continue

                module_name = filename[:-3]  # Enlever .py
                module_path = f"controls.{category_dir}.{module_name}"

                try:
                    # Importer le module
                    module = importlib.import_module(module_path, package='controles_bduni_plugin')

                    # Chercher les classes qui héritent de QgsProcessingAlgorithm
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, QgsProcessingAlgorithm) and
                            obj is not QgsProcessingAlgorithm and
                            hasattr(obj, 'processAlgorithm')):
                            try:
                                # Créer une instance de l'algorithme
                                algo = obj()
                                # Ajouter au provider
                                self.addAlgorithm(algo)
                            except Exception as e:
                                # Ignorer les erreurs d'instanciation
                                pass

                except Exception as e:
                    # Ignorer les erreurs d'import
                    pass

    def unload(self):
        """Décharge le provider"""
        pass

    def longName(self):
        """Nom long du provider"""
        return self.name()

