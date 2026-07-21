# -*- coding: utf-8 -*-
"""
Script pour charger les contrôles BDUni dans la boîte à outils QGIS
À exécuter depuis la console Python de QGIS
"""

import sys
import os
import gc
from qgis.core import QgsApplication, QgsMessageLog, Qgis

# Chemin du plugin (adapter si nécessaire)
PLUGIN_PATH = os.path.dirname(__file__)


def is_provider_valid(provider):
    """Vérifie si l'objet C++ du provider existe encore"""
    try:
        import sip
        return not sip.isdeleted(provider) and provider is not None
    except:
        return False


def load_controles_bduni_processing():
    """
    Charge le provider de processing des contrôles BDUni dans la boîte à outils QGIS
    """
    try:
        # Ajouter le chemin du plugin au sys.path si nécessaire
        if PLUGIN_PATH not in sys.path:
            sys.path.insert(0, PLUGIN_PATH)

        # Obtenir le registre de processing
        registry = QgsApplication.processingRegistry()

        # Vérifier si le provider est déjà chargé et le supprimer proprement
        existing_providers = [p for p in registry.providers()
                            if p.id() == 'controles_bduni' and is_provider_valid(p)]

        if existing_providers:
            QgsMessageLog.logMessage(
                "Le provider 'Contrôles BDUni' est déjà chargé. Rechargement...",
                "Contrôles BDUni",
                Qgis.Info
            )
            for provider in existing_providers:
                try:
                    registry.removeProvider(provider)
                except RuntimeError:
                    # Le provider C++ a déjà été supprimé
                    pass

        # Forcer le nettoyage de la mémoire
        gc.collect()
        QgsApplication.processEvents()

        # Nettoyer les modules Python en cache pour forcer la réimportation
        modules_to_remove = [key for key in list(sys.modules.keys())
                           if 'processing_provider' in key.lower() or
                              ('controles' in key.lower() and 'bduni' in key.lower())]
        for module in modules_to_remove:
            sys.modules.pop(module, None)

        # Importer le provider (réimportation propre)
        from processing_provider import ControlesBDUniProvider

        # Créer une nouvelle instance
        provider = ControlesBDUniProvider()

        # Enregistrer le provider
        if not registry.addProvider(provider):
            raise Exception("Impossible d'enregistrer le provider dans le registre")

        # Message de succès
        num_algos = len(provider.algorithms())
        msg = f"Provider 'Contrôles BDUni' chargé avec succès ! {num_algos} algorithme(s) disponible(s)."
        QgsMessageLog.logMessage(msg, "Contrôles BDUni", Qgis.Success)
        print(msg)

        # Lister les algorithmes chargés
        if num_algos > 0:
            print("\nAlgorithmes disponibles :")
            for algo in provider.algorithms():
                print(f"  - {algo.displayName()} (ID: {algo.id()})")
        else:
            print("\n⚠️ Aucun algorithme chargé. Vérifiez que :")
            print("  1. Les fichiers d'algorithmes existent dans controls/")
            print("  2. Les classes implémentent createInstance()")
            print("  3. Il n'y a pas d'erreurs d'import")

        # Garder une référence globale pour éviter la suppression prématurée
        import __main__
        __main__._controles_provider_instance = provider

        return provider

    except Exception as e:
        error_msg = f"Erreur lors du chargement du provider : {str(e)}"
        QgsMessageLog.logMessage(error_msg, "Contrôles BDUni", Qgis.Critical)
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None


def unload_controles_bduni_processing():
    """
    Décharge le provider de processing des contrôles BDUni
    """
    try:
        registry = QgsApplication.processingRegistry()
        providers = [p for p in registry.providers()
                    if p.id() == 'controles_bduni' and is_provider_valid(p)]

        if providers:
            for provider in providers:
                try:
                    registry.removeProvider(provider)
                except RuntimeError:
                    pass

            # Nettoyer la référence globale
            import __main__
            if hasattr(__main__, '_controles_provider_instance'):
                delattr(__main__, '_controles_provider_instance')

            # Forcer le nettoyage
            gc.collect()

            msg = "Provider 'Contrôles BDUni' déchargé avec succès."
            QgsMessageLog.logMessage(msg, "Contrôles BDUni", Qgis.Info)
            print(msg)
        else:
            msg = "Le provider 'Contrôles BDUni' n'est pas chargé."
            QgsMessageLog.logMessage(msg, "Contrôles BDUni", Qgis.Warning)
            print(msg)

    except Exception as e:
        error_msg = f"Erreur lors du déchargement du provider : {str(e)}"
        QgsMessageLog.logMessage(error_msg, "Contrôles BDUni", Qgis.Critical)
        print(error_msg)


# Exécution automatique si appelé comme script principal
if __name__ == '__console__' or __name__ == '__main__':
    print("=" * 60)
    print("CHARGEMENT DES CONTRÔLES BDUNI DANS LA BOÎTE À OUTILS")
    print("=" * 60)
    provider = load_controles_bduni_processing()
    print("=" * 60)
    print("\nPour décharger le provider, exécutez :")
    print("  unload_controles_bduni_processing()")
    print("\nPour recharger, exécutez à nouveau :")
    print("  load_controles_bduni_processing()")
