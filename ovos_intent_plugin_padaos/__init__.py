from ovos_intent_plugin_padaos.padaos_engine import IntentContainer
from ovos_plugin_manager.templates.pipeline import IntentPipelinePlugin, IntentMatch
from ovos_utils.log import LOG
from ovos_utils import classproperty


def _munge(name, skill_id):
    return f"{name}:{skill_id}"


def _unmunge(munged):
    return munged.split(":", 2)


class PadaosPipelinePlugin(IntentPipelinePlugin):

    def __init__(self, bus, config=None):
        super().__init__(bus, config)
        self.engines = {}  # lang: IntentContainer

    # plugin api
    @classproperty
    def matcher_id(self):
        return "padaos"

    def match(self, utterances, lang, message):
        return self.calc_intent(utterances, lang=lang)

    def train(self):
        # no training step needed
        return True

    # implementation
    def _get_engine(self, lang=None):
        lang = lang or self.lang
        if lang not in self.engines:
            self.engines[lang] = IntentContainer()
        return self.engines[lang]

    def register_entity(self, skill_id, entity_name, samples=None, lang=None):
        lang = lang or self.lang
        super().register_entity(skill_id, entity_name, samples, lang)
        container = self._get_engine(lang)
        samples = samples or [entity_name]
        container.add_entity(entity_name, samples)

    def register_intent(self, skill_id, intent_name, samples=None, lang=None):
        lang = lang or self.lang
        super().register_intent(skill_id, intent_name, samples, lang)
        container = self._get_engine(lang)
        samples = samples or [intent_name]
        intent_name = _munge(intent_name, skill_id)
        container.add_intent(intent_name, samples)

    def detach_intent(self, skill_id, intent_name):
        for intent in self.registered_intents:
            if intent.name != intent_name or intent.skill_id != skill_id:
                continue
            LOG.debug("Detaching padaos intent: " + intent_name)
            with self.lock:
                for lang in self.engines:
                    self.engines[lang].remove_intent(_munge(intent.name,
                                                            intent.skill_id))
        super().detach_intent(intent_name)

    def calc_intent(self, utterance, min_conf=0.5, lang=None):
        lang = lang or self.lang
        container = self._get_engine(lang)
        utterance = utterance.strip().lower()
        intent = container.calc_intent(utterance)
        if intent["name"]:

            intent_type, skill_id = _unmunge(intent["intent_type"])
            return IntentMatch(intent_service=intent["intent_engine"],
                               intent_type=intent_type,
                               intent_data=intent["entities"],
                               confidence=1.0,
                               utterance=utterance,
                               skill_id=skill_id)
        return None
