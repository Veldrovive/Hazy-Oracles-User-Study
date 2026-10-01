from dotenv import load_dotenv
import os
import pickle
from pathlib import Path
load_dotenv()

API_KEY = os.getenv("API_KEY")
ROOTS_PATH = Path(__file__).parent.parent.parent / os.getenv("ROOTS_PATH", "data/conversation_roots")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

MAX_RESPONSES_FOR_ANSWERER_NODE = int(os.getenv("MAX_RESPONSES_FOR_ANSWERER_NODE", 5))
MAX_EXPANSIONS_FOR_ANSWERER_NODE = int(os.getenv("MAX_EXPANSIONS_FOR_ANSWERER_NODE", 2))
MAX_RESPONSES_FOR_ASKER_NODE = int(os.getenv("MAX_RESPONSES_FOR_ASKER_NODE", 3))
MAX_EXPANSIONS_FOR_ASKER_NODE = int(os.getenv("MAX_EXPANSIONS_FOR_ASKER_NODE", 1))
MAX_DEPTH = int(os.getenv("MAX_DEPTH", 4))

LOCK_TIMEOUT_MINUTES = int(os.getenv("LOCK_TIMEOUT_MINUTES", 2))

AVG_CONFIDENCE_SCORE_PRUNE_THRESHOLD = float(os.getenv("AVG_CONFIDENCE_SCORE_PRUNE_THRESHOLD", 0.8))

PHASE_1_QUALIFICATION_NUM_RESPONSES = int(os.getenv("PHASE_1_QUALIFICATION_NUM_RESPONSES", 10))
MAX_AUTOMOD_FLAGS = int(os.getenv("MAX_AUTOMOD_FLAGS", 2))
MAX_TOTAL_RESPONSES = int(os.getenv("MAX_TOTAL_RESPONSES", 100))
MAX_DEPTH_1_SAMPLES_PER_USER = int(os.getenv("MAX_DEPTH_1_SAMPLES_PER_USER", 2))

DEFAULT_ZIPF_S = float(os.getenv("DEFAULT_ZIPF_S", 1.2))

AUTOMOD_TOXICITY_THRESHOLD = float(os.getenv("AUTOMOD_TOXICITY_THRESHOLD", 0.5))
AUTOMOD_SEVERE_TOXICITY_THRESHOLD = float(os.getenv("AUTOMOD_SEVERE_TOXICITY_THRESHOLD", 0.25))

def load_expansion_order(path: str) -> list[str]:
    try:
        with open(path, "rb") as f:
            return pickle.load(f)["expansion_order_base64"]
    except FileNotFoundError:
        return []

# Load default expansion order
DEFAULT_EXPANSION_ORDER = load_expansion_order("data/expansion_order.pkl")
EXPANSION_ORDER_BASE64 = DEFAULT_EXPANSION_ORDER # Keep for backward compatibility

COLLECTIONS = {
    "human-human": {
        "asker_role": "human",
        "answerer_role": "human",
        "expansion_order": load_expansion_order("data/expansion_order_human.pkl") or DEFAULT_EXPANSION_ORDER
    },
    "human-ai-asker": {
        "asker_role": "example_asker_ai",
        "answerer_role": "human",
        "expansion_order": load_expansion_order("data/expansion_order_ai.pkl") or DEFAULT_EXPANSION_ORDER
    },
    "ai-answerer-human": {
        "asker_role": "human",
        "answerer_role": "example_answerer_ai",
        "expansion_order": load_expansion_order("data/expansion_order_ai.pkl") or DEFAULT_EXPANSION_ORDER
    }
}

print(f"Database Url: {DATABASE_URL}")
print(f"Max responses for answerer node: {MAX_RESPONSES_FOR_ANSWERER_NODE}")
print(f"Max expansions for answerer node: {MAX_EXPANSIONS_FOR_ANSWERER_NODE}")
print(f"Max responses for asker node: {MAX_RESPONSES_FOR_ASKER_NODE}")
print(f"Max expansions for asker node: {MAX_EXPANSIONS_FOR_ASKER_NODE}")
print(f"Max depth: {MAX_DEPTH}")
print(f"Lock timeout (minutes): {LOCK_TIMEOUT_MINUTES}")
print(f"Average confidence score prune threshold: {AVG_CONFIDENCE_SCORE_PRUNE_THRESHOLD}")
print(f"Phase 1 qualification num responses: {PHASE_1_QUALIFICATION_NUM_RESPONSES}")
print(f"Max automod flags: {MAX_AUTOMOD_FLAGS}")
print(f"Max total responses: {MAX_TOTAL_RESPONSES}")
print(f"Max depth 1 samples per user: {MAX_DEPTH_1_SAMPLES_PER_USER}")
print(f"Default Zipf s: {DEFAULT_ZIPF_S}")
print(f"Automod toxicity threshold: {AUTOMOD_TOXICITY_THRESHOLD}")
print(f"Automod severe toxicity threshold: {AUTOMOD_SEVERE_TOXICITY_THRESHOLD}")
print(f"Loaded {len(COLLECTIONS)} collections.")
print(f"Roots path: {ROOTS_PATH}")