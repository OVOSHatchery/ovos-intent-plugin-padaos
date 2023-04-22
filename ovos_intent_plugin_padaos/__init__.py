from padaos import IntentContainer
from ovos_plugin_manager.intents import IntentExtractor, IntentPriority, IntentDeterminationStrategy
from ovos_utils.log import LOG


class PadaosExtractor(IntentExtractor):
    def __init__(self, config=None,
                 strategy=IntentDeterminationStrategy.SEGMENT_MULTI,
                 priority=IntentPriority.REGEX_MEDIUM,
                 segmenter=None):
        super().__init__(config, strategy=strategy,
                         priority=priority, segmenter=segmenter)
        self.engines = {}  # lang: IntentContainer

    def _get_engine(self, lang=None):
        lang = lang or self.lang
        if lang not in self.engines:
            self.engines[lang] = IntentContainer()
        return self.engines[lang]

    def register_entity(self, entity_name, samples=None, lang=None):
        lang = lang or self.lang
        container = self._get_engine(lang)
        samples = samples or [entity_name]
        super().register_entity(entity_name, samples)
        container.add_entity(entity_name, samples)

    def register_intent(self, intent_name, samples=None, lang=None):
        lang = lang or self.lang
        container = self._get_engine(lang)
        samples = samples or [intent_name]
        super().register_intent(intent_name, samples)
        container.add_intent(intent_name, samples)

    def calc_intent(self, utterance, min_conf=0.5, lang=None, session=None):
        lang = lang or self.lang
        container = self._get_engine(lang)
        utterance = utterance.strip().lower()
        intent = container.calc_intent(utterance)
        if intent["name"]:
            remainder = self.get_utterance_remainder(
                utterance, samples=self.registered_intents[intent["name"]])
            intent["intent_engine"] = "padaos"
            intent["intent_type"] = intent.pop("name")
            intent["utterance"] = utterance
            intent["utterance_remainder"] = remainder
            modifier = len(self.segmenter.segment(utterance))
            intent["conf"] = 1 / modifier - 0.1
            return intent
        return None
