from qgis.core import (
    QgsProcessingParameterVectorLayer,
    QgsProcessing,
    QgsProcessingParameterFile,
    QgsFeatureRequest,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils
)

from BaseControlAlgorithm import BaseControlAlgorithm


class AttributesInconsistencyAlgorithm(BaseControlAlgorithm):

    ALG_NAME = 'C.00'
    ALG_DISPLAY_NAME = "Incohérences entre attributs"
    ALG_GROUP = 'Controles génériques attributaires'
    ALG_GROUP_ID = 'C'
    ALG_HELP = (
        "Cas1 Si Champ1 <> Valeur1 alors Champ2 >= Champ1\n"
        "Cas2 Si Champ1 <> Valeur1 alors Champ2 <= Champ1\n"
        "Cas3 Si Champ1 <> Valeur1 alors Champ2 = Valeur2\n"
        "Cas4 Si Champ1 <> Valeur1 alors Champ2 <> Valeur2\n"
        "Cas5 Si Champ1 = Valeur1 alors Champ2 = Valeur2\n"
        "Cas6 Si Champ1 = Valeur1 alors Champ2 <> Valeur2\n"
        "Cas7 Si Champ1 <> Valeur1 et Champ2 <> Valeur2 alors Champ1 < Champ2\n"
        "Cas8 Si Champ1 = Valeur1 alors Champ2 <= DATE_DU_JOUR\n"
        "Cas9 Si Champ1 <> Valeur1 alors Champ2 <= Champ1 + Valeur2 (en mois)\n"
        "Cas10 Si Champ1 = Valeur1 alors Champ2 = Valeur2 ou Valeur2 ou Valeur2...\n"
        "Cas13 Si Champ1 = Valeur1 et Champ2 <> Valeur2 alors Champ3 = Valeur3\n"
        "Cas14 Si Champ1 = Valeur1 alors Champ2 ne contient pas Valeur2"
    )

    INPUT_LAYER = 'INPUT_LAYER'

    # Opérateurs de comparaison directement traduisibles dans une expression QGIS
    COMPARISON_OPERATORS = ('=', '!=', '>', '<', '>=', '<=')

    # Libellés utilisés pour la description humaine des conditions
    OPERATOR_LABELS = {
        '=': '=',
        '!=': '≠',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
        'is': 'est',
        'start': 'commence par',
        'start2': 'commence par',
    }

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr("Couche en entrée"),
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.PARAM_JSON,
                self.tr('Paramètres JSON'),
                extension='json'
            )
        )
        super().initAlgorithm(config)

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        json_path = self.parameterAsFile(parameters, self.PARAM_JSON, context)
        id_field = self.get_id_field(parameters, context)
        if not self.validate_id_field(layer, id_field, feedback):
            return {'OUTPUT': 'Erreur'}

        # param_json : [{'classe': <nom de couche>, 'regles': [{'id', 'si', 'alors'}, ...]}, ...]
        param_json = self.load_json_parameters(json_path)

        layer_rules = self.get_layer_rules(param_json, layer, feedback)
        if layer_rules is None:
            return self.processing_done_result()

        incoherence_attributes_feature = []

        expr_context = QgsExpressionContext()
        expr_context.appendScope(QgsExpressionContextUtils.layerScope(layer))

        for regle in layer_rules:
            si_conditions = regle.get('si', [])
            alors_conditions = regle.get('alors', [])
            if not alors_conditions:
                continue

            premise_expr = self.build_expression(si_conditions, 'AND') or 'TRUE'
            consequence_expr_str = self.build_expression(alors_conditions, 'OR')
            consequence_expression = QgsExpression(consequence_expr_str)
            if consequence_expression.hasParserError():
                feedback.reportError(
                    self.tr("Règle {} ignorée : expression invalide ({})").format(
                        regle.get('id'), consequence_expression.parserErrorString()
                    )
                )
                continue

            request = QgsFeatureRequest()
            request.setFilterExpression(premise_expr)
            if request.filterExpression().hasParserError():
                feedback.reportError(
                    self.tr("Règle {} ignorée : condition 'si' invalide ({})").format(
                        regle.get('id'), request.filterExpression().parserErrorString()
                    )
                )
                continue

            attributs_consequence = ', '.join(
                dict.fromkeys(cond['attribut'] for cond in alors_conditions)
            )
            message = self.describe_rule(regle, si_conditions, alors_conditions)

            for feature in layer.getFeatures(request):
                expr_context.setFeature(feature)
                result = consequence_expression.evaluate(expr_context)
                if consequence_expression.hasEvalError():
                    feedback.reportError(
                        self.tr("Règle {} : erreur d'évaluation sur l'entité {} ({})").format(
                            regle.get('id'),
                            self.get_feature_identifier(feature, id_field),
                            consequence_expression.evalErrorString()
                        )
                    )
                    continue
                if not result:
                    incoherence_attributes_feature.append(
                        ['Incohérence entre attributs',
                        layer.name(),
                        self.get_feature_identifier(feature, id_field),
                        attributs_consequence,
                        message,
                        feature.geometry().pointOnSurface()])

        self.report_issues(incoherence_attributes_feature, 'Incohérence entre attributs')

        return self.processing_done_result()

    # ------------------------------------------------------------------
    # Récupération des règles associées à la couche en cours
    # ------------------------------------------------------------------
    def get_layer_rules(self, param_json, layer, feedback):
        """
        Récupère la liste des règles associées à une couche dans le fichier
        JSON de paramétrage (format [{'classe': ..., 'regles': [...]}, ...]).
        """
        for layer_rules in param_json:
            if layer_rules.get('classe') == layer.name():
                return layer_rules.get('regles', [])
        feedback.reportError(
            self.tr("{} n'est pas présent dans le fichier json de paramétrage").format(layer.name())
        )
        return None

    # ------------------------------------------------------------------
    # Construction des expressions QGIS à partir des règles JSON
    # ------------------------------------------------------------------
    @staticmethod
    def quote_field(field_name):
        return '"{}"'.format(field_name.replace('"', '\\"'))

    @staticmethod
    def unquote_valeur(valeur):
        """Retire les guillemets encadrant une valeur littérale du JSON."""
        if isinstance(valeur, str) and len(valeur) >= 2 and valeur.startswith('"') and valeur.endswith('"'):
            return valeur[1:-1]
        return valeur or ''

    @classmethod
    def literal_expression(cls, raw):
        """Traduit une valeur littérale brute en expression QGIS."""
        if raw == '':
            return "''"
        lower_raw = raw.lower()
        if lower_raw == 'today':
            return 'now()'
        if lower_raw == 'true':
            return 'TRUE'
        if lower_raw == 'false':
            return 'FALSE'
        escaped = raw.replace("'", "\\'")
        return "'{}'".format(escaped)

    @classmethod
    def value_expression(cls, condition):
        """Construit le membre droit (valeur) d'une condition."""
        valeur = condition.get('valeur', '')
        if condition.get('type') == 'attribute':
            field_name = valeur.strip('<>')
            return cls.quote_field(field_name)
        return cls.literal_expression(cls.unquote_valeur(valeur))

    @classmethod
    def prefix_value_expression(cls, condition):
        """
        Construit le membre droit d'un opérateur 'start'/'start2' : une
        valeur littérale (avec échappement des jokers LIKE) ou une
        référence à un autre attribut.
        """
        if condition.get('type') == 'attribute':
            field_name = condition.get('valeur', '').strip('<>')
            return cls.quote_field(field_name)
        raw = cls.unquote_valeur(condition.get('valeur', ''))
        escaped = raw.replace('\\', '\\\\').replace("'", "\\'").replace('%', '\\%').replace('_', '\\_')
        return "'{}'".format(escaped)

    @classmethod
    def condition_expression(cls, condition):
        """Traduit une condition JSON ('si' ou 'alors') en expression QGIS."""
        field_ref = cls.quote_field(condition['attribut'])
        operateur = condition['operateur']

        if operateur == 'is':
            return '{} IS {}'.format(field_ref, cls.value_expression(condition))

        if operateur in ('start', 'start2'):
            # 'start' (préfixe littéral) et 'start2' (préfixe = valeur d'un autre
            # attribut) sont traduits de la même façon : le champ doit commencer
            # par la valeur (littérale ou attribut) désignée.
            return "{} LIKE ({} || '%')".format(field_ref, cls.prefix_value_expression(condition))

        if operateur in cls.COMPARISON_OPERATORS:
            # Une comparaison à une valeur vide doit tolérer les champs NULL
            if condition.get('type') != 'attribute' and cls.unquote_valeur(condition.get('valeur', '')) == '':
                return "COALESCE({}, '') {} ''".format(field_ref, operateur)
            return '{} {} {}'.format(field_ref, operateur, cls.value_expression(condition))

        raise ValueError("Opérateur non géré : {}".format(operateur))

    @classmethod
    def build_expression(cls, conditions, join_word):
        """Combine une liste de conditions JSON avec ET (si) ou OU (alors)."""
        if not conditions:
            return None
        parts = ['({})'.format(cls.condition_expression(cond)) for cond in conditions]
        return (' {} '.format(join_word)).join(parts)

    # ------------------------------------------------------------------
    # Description humaine de la règle (pour le message de l'anomalie)
    # ------------------------------------------------------------------
    @classmethod
    def describe_condition(cls, condition):
        attribut = condition['attribut']
        operateur = cls.OPERATOR_LABELS.get(condition['operateur'], condition['operateur'])
        if condition.get('type') == 'attribute':
            valeur = condition.get('valeur', '')
        else:
            raw = cls.unquote_valeur(condition.get('valeur', ''))
            valeur = '"{}"'.format(raw) if raw != '' else '(vide)'
        return '{} {} {}'.format(attribut, operateur, valeur)

    @classmethod
    def describe_rule(cls, regle, si_conditions, alors_conditions):
        alors_desc = ' ou '.join(cls.describe_condition(cond) for cond in alors_conditions)
        if si_conditions:
            si_desc = ' et '.join(cls.describe_condition(cond) for cond in si_conditions)
            return "Règle {} non respectée : si {} alors {}".format(regle.get('id'), si_desc, alors_desc)
        return "Règle {} non respectée : {}".format(regle.get('id'), alors_desc)
