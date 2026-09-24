from datetime import datetime, timedelta
from sqlmodel import Session, select, col
import numpy as np


from hazy_oracles_user_study.database import (
    TreeLock,
    ModerationEvent,
    SampleResponse,
    ConversationRoot,
    User,
    ACTOR_TYPE,
    SAMPLE_TYPE,
    EVENT_TYPE,
    MODERATION_ACTION,
)
from hazy_oracles_user_study.automod import ContentModerator
from hazy_oracles_user_study.utils import generate_uuid

from hazy_oracles_user_study.server_models import (
    DialogMessage,
    QuestionAnswererSampleData,
    QuestionAskerSampleData,
    MultimodalInputImage
)
from sqlalchemy.exc import IntegrityError


def add_user(db: Session, unique_id: str, login_id: str, password: str) -> User | None:
    # Add the new user to the db
    new_user = User(
        unique_id=unique_id,
        login_id=login_id,
        password=password,
        has_logged_in=True,
        has_consented=False,
        has_read_asker_instructions=False,
        has_read_answerer_instructions=False,
        num_responses_given=0,
        num_automod_flagged_responses=0,
        has_ended_participation=False,
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        return None
    

# def get_user_summary(db: Session, unique_id: str) -> User:
    