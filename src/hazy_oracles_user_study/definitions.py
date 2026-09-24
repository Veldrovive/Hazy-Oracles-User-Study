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

DEFAULT_ZIPF_S = float(os.getenv("DEFAULT_ZIPF_S", 1.2))

AUTOMOD_TOXICITY_THRESHOLD = float(os.getenv("AUTOMOD_TOXICITY_THRESHOLD", 0.5))
AUTOMOD_SEVERE_TOXICITY_THRESHOLD = float(os.getenv("AUTOMOD_SEVERE_TOXICITY_THRESHOLD", 0.25))

# Load expansion order from pickle file
with open("data/expansion_order.pkl", "rb") as f:
    expansion_order_obj = pickle.load(f)

EXPANSION_ORDER_TUPLES: list[tuple] = expansion_order_obj["expansion_order_tuples"]
EXPANSION_ORDER_BASE64: list[str] = expansion_order_obj["expansion_order_base64"]

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
print(f"Default Zipf s: {DEFAULT_ZIPF_S}")
print(f"Automod toxicity threshold: {AUTOMOD_TOXICITY_THRESHOLD}")
print(f"Automod severe toxicity threshold: {AUTOMOD_SEVERE_TOXICITY_THRESHOLD}")
print(f"Expansion order: {EXPANSION_ORDER_BASE64}")
print(f"Roots path: {ROOTS_PATH}")