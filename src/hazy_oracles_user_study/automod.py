import re
import unidecode
import requests
from typing import NamedTuple, Optional, Dict, Literal
from better_profanity import profanity
from detoxify import Detoxify
from pygarble import EnsembleDetector
from hazy_oracles_user_study.definitions import AUTOMOD_TOXICITY_THRESHOLD, AUTOMOD_SEVERE_TOXICITY_THRESHOLD

JUDGE_VLLM_URL = "http://localhost:9098"
JUDGE_MODEL_KEY = "Qwen/Qwen3.6-35B-A3B-FP8"
JUDGE_PROMPT_TEMPLATE = "Text: {raw_text}\n\nIs the text above a real, coherent sentence written in good faith? It should not be a random collection of words or gibberish trying to trick a markov chain gibberish detector. Answer only with 'Yes' if it is a real, coherent sentence, or 'No' if it is random words, gibberish, or in bad faith."


class ModerationResult(NamedTuple):
    original_text: str
    action: Literal["pass", "reject_gibberish", "reject_profanity", "reject_toxic", "reject_bad_faith"]
    fast_catch_triggered: bool
    detoxify_scores: Optional[Dict[str, float]]
    normalized_text_used: Optional[str]


class ContentModerator:
    def __init__(self, toxicity_threshold: float = AUTOMOD_TOXICITY_THRESHOLD, severe_toxicity_threshold: float = AUTOMOD_SEVERE_TOXICITY_THRESHOLD):
        """
        Initialize the models once when the class is instantiated.
        This prevents reloading the heavy BERT model on every single check.
        """
        print("Loading Detoxify model... (This may take a moment)")
        self.detox_model: Detoxify = Detoxify('multilingual')
        self.toxicity_threshold: float = toxicity_threshold
        self.severe_toxicity_threshold: float = severe_toxicity_threshold
        self.detector: EnsembleDetector = EnsembleDetector()
        
        # Load the default better_profanity dictionary
        profanity.load_censor_words()
        
        # Optional: Add your own custom words to the dictionary
        # profanity.add_censor_words(['customword1', 'customword2'])

    def _normalize_for_detoxify(self, text: str) -> str:
        """
        Prepares text for the BERT model by removing Unicode tricks 
        and translating basic leetspeak back to standard English.
        """
        # 1. Convert fancy fonts/accents back to standard ASCII 
        # (e.g., "𝒻𝓊𝒸𝓀" becomes "fuck")
        text = unidecode.unidecode(text)
        
        # 2. Basic leetspeak mapping to help Detoxify read the intent
        # (better_profanity already handles this internally, but Detoxify needs the help)
        leetspeak_map = {
            '@': 'a',
            '$': 's',
            '0': 'o',
            '1': 'i',
            '!': 'i',
            '3': 'e',
            '#': 'h',
            '+': 't'
        }
        
        trans_table = str.maketrans(leetspeak_map)
        normalized_text = text.translate(trans_table)
        
        return normalized_text.lower()

    def evaluate_text(self, raw_text: str, fast_fail: bool = False) -> ModerationResult:
        """
        Runs the two-step moderation pipeline.
        
        :param raw_text: The user input string.
        :param fast_fail: If True, skips Detoxify if profanity is caught (saves compute).
        :return: ModerationResult containing both fast catch and deep catch results.
        """
        fast_catch_triggered = False
        detoxify_scores = None
        normalized_text_used = None
        action = "pass"

        # ==========================================
        # STEP 0: Gibberish Detection (pygarble)
        # ==========================================
        if self.detector.predict(raw_text):
            action = "reject_gibberish"

            if fast_fail:
                return ModerationResult(
                    original_text=raw_text,
                    action=action,
                    fast_catch_triggered=fast_catch_triggered,
                    detoxify_scores=detoxify_scores,
                    normalized_text_used=normalized_text_used,
                )

        # ==========================================
        # STEP 1: The Fast Catch (better_profanity)
        # ==========================================
        # better_profanity handles leetspeak (a$$) and character spacing (s.h.i.t) automatically
        if profanity.contains_profanity(raw_text):
            fast_catch_triggered = True
            action = "reject_profanity"
            
            # If we only care about rejecting bad text, we can stop here to save ML compute time
            if fast_fail:
                return ModerationResult(
                    original_text=raw_text,
                    action=action,
                    fast_catch_triggered=fast_catch_triggered,
                    detoxify_scores=detoxify_scores,
                    normalized_text_used=normalized_text_used,
                )

        # ==========================================
        # STEP 2: The Deep Catch (Detoxify)
        # ==========================================
        # Clean the text so the ML model can actually read it
        clean_text = self._normalize_for_detoxify(raw_text)
        normalized_text_used = clean_text
        
        # Run predictions
        predictions = self.detox_model.predict(clean_text)
        
        # Convert float32 types to standard Python floats for easier JSON serialization later
        detoxify_scores = {k: float(v) for k, v in predictions.items()}

        # Define your threshold for rejection (e.g., 80% confidence of severe toxicity)
        if detoxify_scores["toxicity"] > self.toxicity_threshold or detoxify_scores["severe_toxicity"] > self.severe_toxicity_threshold:
             action = "reject_toxic"

        # ==========================================
        # STEP 3: Judge LLM Bad Faith Check
        # ==========================================
        if action == "pass":
            prompt_text = JUDGE_PROMPT_TEMPLATE.format(raw_text=raw_text)
            payload = {
                "model": JUDGE_MODEL_KEY,
                "messages": [{"role": "user", "content": prompt_text}],
                "temperature": 0.0
            }
            try:
                res = requests.post(f"{JUDGE_VLLM_URL}/v1/chat/completions", json=payload, timeout=10)
                res.raise_for_status()
                judge_response = res.json()['choices'][0]['message']['content'].strip()
                if not judge_response.lower().startswith("yes"):
                    action = "reject_bad_faith"
            except Exception as e:
                print(f"Error querying Judge VLLM in automod: {e}")

        return ModerationResult(
            original_text=raw_text,
            action=action,
            fast_catch_triggered=fast_catch_triggered,
            detoxify_scores=detoxify_scores,
            normalized_text_used=normalized_text_used,
        )

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    moderator = ContentModerator()

    test_cases = [
        "This is a totally normal and polite sentence.",
        "You are an a$$hole!",                      # Tests leetspeak fast catch
        "I will find where you live and hurt you",  # Tests Detoxify (no profanity, but highly toxic/threatening)
        "You are a 𝒷𝒾𝓉𝒸𝒽",                            # Tests Unicode font evasion
        "gghbghbghb",
        "MEOW MEWO MWO EMEOW MEOW",
        "Much want such no bet",
        "Are you referring to a cat or some other animal with similar sounds?"
    ]

    for test in test_cases:
        print(f"\n--- Testing: '{test}' ---")
        
        # Set fast_fail=False so we can see both outputs for the demonstration
        report = moderator.evaluate_text(test, fast_fail=False)
        
        print(f"Action Taken:      {report.action}")
        print(f"Fast Catch Hit:    {report.fast_catch_triggered}")
        if report.detoxify_scores:
            print(f"Toxicity Score:    {report.detoxify_scores['toxicity']:.2%}")
            print(f"Normalized To:     {report.normalized_text_used}")