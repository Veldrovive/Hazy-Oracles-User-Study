from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, JSON

class SAMPLE_TYPE(str, Enum):
    ASKER = "asker"
    ANSWERER = "answerer"
    SKIP = "skip"

class ACTOR_TYPE(str, Enum):
    AUTOMOD = "automod"
    PARTICIPANT = "participant"
    HUMAN_MODERATOR = "human_moderator"

class EVENT_TYPE(str, Enum):
    AUTOMOD_CHECK = "automod_check"
    PARTICIPANT_FLAG = "participant_flag"
    MODERATOR_REVIEW = "moderator_review"

class MODERATION_ACTION(str, Enum):
    CLEARED = "cleared"
    PLACED_ON_HOLD = "placed_on_hold"
    PERMANENTLY_REMOVED = "permanently_removed"

class User(SQLModel, table=True):
    login_id: str = Field(index=True)
    password: str
    unique_id: str = Field(primary_key=True, index=True)
    has_logged_in: bool
    has_consented: bool
    has_read_asker_instructions: bool
    has_read_answerer_instructions: bool

    num_responses_given: int = Field(default=0)
    num_automod_flagged_responses: int = Field(default=0)
    has_ended_participation: bool = Field(default=False)

class SentSample(SQLModel, table=True):
    sample_id: str = Field(primary_key=True, index=True)
    intended_node_code: str = Field(index=True)
    user_unique_id: str = Field(index=True)  # Links to the unique id field in the User table
    parent_id: Optional[str] = Field(default=None, index=True)
    root_id: str = Field(default=None, index=True)
    timestamp: datetime
    is_returned: bool = Field(default=False, index=True)

class SampleResponse(SQLModel, table=True):
    sample_id: str = Field(primary_key=True, index=True)
    node_code: str = Field(index=True)  # Defines the position of the node in the tree e.g. "ADBCB"
    user_unique_id: str = Field(index=True)
    parent_sample_id: Optional[str] = Field(default=None, index=True)
    root_id: str = Field(index=True)

    depth: int = Field(index=True)
    timestamp: datetime
    participant_type: str # ("human" or the name of the language model)
    sample_type: SAMPLE_TYPE # (enum of asker or answerer or skip)

    moderation_status: MODERATION_ACTION = Field(default="cleared", index=True)

    # Relevant only for asker (kept for data analysis, not pruning)
    previous_answer_meaningful_score: Optional[float] = None
    current_guess: Optional[str] = None
    current_guess_confidence_score: Optional[float] = None
    next_question: Optional[str] = None

    # Relevant only for answerer (empty if skip or asker)
    previous_question_relevant_score: Optional[float] = None
    previous_question_informative_score: Optional[float] = None
    answer: Optional[str] = None

class ConversationRoot(SQLModel, table=True):
    root_id: str = Field(primary_key=True, index=True)
    ambiguous_question: str
    priority: float
    unambiguous_question: str
    multimodal_file_path: str
    original_dataset: str
    original_dataset_sample_id: str

    next_expansion_index: int = Field(index=True, default=0)
    is_completed: bool = Field(index=True, default=False)

class ModerationEvent(SQLModel, table=True):
	event_id: str = Field(primary_key=True, index=True)
	sample_id: str = Field(index=True)  # Links directly to the SampleResponse
	timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

	# Defines the entity taking the action
	actor_type: ACTOR_TYPE  # (Enum: 'automod', 'participant', 'human_moderator')
	actor_id: Optional[str] = Field(index=True)  # user_unique_id if participant/moderator, otherwise None

	# The specific action being recorded
	event_type: EVENT_TYPE  # (Enum: 'automod_check', 'participant_flag', 'moderator_review')
	
	# The outcome of the event determining visibility in the pool
	action_taken: MODERATION_ACTION  # (Enum: 'cleared', 'placed_on_hold', 'permanently_removed')

	# Flexible storage for outputs and reasons
	# For automod: Maps flag types (e.g., 'obscenity', 'threats') to their float scores
	# For humans: Can store categorical reasons for flags/rejections
	automod_scores: Optional[dict[str, float]] = Field(default=None, sa_column=Column(JSON))
	human_notes: Optional[str] = Field(default=None)

class TreeLock(SQLModel, table=True):
    root_id: str = Field(primary_key=True)  # One lock per tree
    user_unique_id: str = Field(index=True)
    expires_at: datetime

class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, echo=False)

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        with Session(self.engine) as session:
            yield session