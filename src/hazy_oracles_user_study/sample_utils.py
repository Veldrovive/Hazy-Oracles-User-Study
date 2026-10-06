from dataclasses import Field
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select, col, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
import numpy as np
from typing import NamedTuple


from hazy_oracles_user_study.database import (
    TreeLock,
    ModerationEvent,
    SampleResponse,
    ConversationRoot,
    TreeCollectionState,
    SentSample,
    User,
    SampleResponse,
    ACTOR_TYPE,
    SAMPLE_TYPE,
    EVENT_TYPE,
    MODERATION_ACTION
)
from hazy_oracles_user_study.automod import ContentModerator
from hazy_oracles_user_study.utils import generate_uuid
from hazy_oracles_user_study.definitions import (
    PHASE_1_QUALIFICATION_NUM_RESPONSES,
    MAX_AUTOMOD_FLAGS,
    MAX_TOTAL_RESPONSES,
    MAX_DEPTH_1_SAMPLES_PER_USER,
    DEFAULT_ZIPF_S,
    LOCK_TIMEOUT_MINUTES,
    COLLECTIONS
)

from hazy_oracles_user_study.server_models import (
    DialogMessage,
    QuestionAnswererSampleData,
    QuestionAskerSampleData,
    MultimodalInputImage,
    TaskResponseRequest,
)

moderator = ContentModerator()

def add_lock(db: Session, root_id: str, collection_id: str, user_unique_id: str, timeout_minutes: int = LOCK_TIMEOUT_MINUTES):
    """Creates or updates a lock for a specific tree."""
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)).replace(tzinfo=None)
    
    # Check if lock exists (even if expired) to overwrite
    lock = db.get(TreeLock, (root_id, collection_id))
    if not lock:
        lock = TreeLock(root_id=root_id, collection_id=collection_id, user_unique_id=user_unique_id, expires_at=expires_at)
        db.add(lock)
    else:
        lock.user_unique_id = user_unique_id
        lock.expires_at = expires_at
        
    db.commit()

def remove_lock(db: Session, root_id: str, collection_id: str, user_unique_id: str):
    """Removes a lock if it belongs to the user."""
    lock = db.get(TreeLock, (root_id, collection_id))
    if lock and lock.user_unique_id == user_unique_id:
        db.delete(lock)
        db.commit()

def remove_expired_locks(db: Session):
    """Removes all locks that have expired"""
    expired_locks = db.exec(
        select(TreeLock).where(TreeLock.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
    ).all()
    for lock in expired_locks:
        db.delete(lock)
    db.commit()

def is_locked(db: Session, root_id: str, collection_id: str) -> bool:
    """Checks if an active lock exists. Cleans up if it is expired."""
    lock = db.get(TreeLock, (root_id, collection_id))
    if not lock:
        return False
        
    lock_expires_at = lock.expires_at.replace(tzinfo=timezone.utc) if lock.expires_at.tzinfo is None else lock.expires_at
    if lock_expires_at < datetime.now(timezone.utc):
        # Lock expired, clean it up
        db.delete(lock)
        db.commit()
        return False
        
    return True

def flag_response_by_participant(db: Session, sample_id: str, user_unique_id: str, reason: str):
    """Participant flags a sample for review."""
    event = ModerationEvent(
        event_id=generate_uuid(),
        sample_id=sample_id,
        actor_type=ACTOR_TYPE.PARTICIPANT,
        actor_id=user_unique_id,
        event_type=EVENT_TYPE.PARTICIPANT_FLAG,
        action_taken=MODERATION_ACTION.PLACED_ON_HOLD,
        human_notes=reason
    )
    db.add(event)
    
    # Update the actual response moderation status
    response = db.get(SampleResponse, sample_id)
    if response:
        response.moderation_status = MODERATION_ACTION.PLACED_ON_HOLD
        
    db.commit()

def moderate_response(db: Session, sample_id: str, moderator_id: str, action: MODERATION_ACTION, notes: str):
    """Moderator reviews a flagged response and sets final status."""
    event = ModerationEvent(
        event_id=generate_uuid(),
        sample_id=sample_id,
        actor_type=ACTOR_TYPE.HUMAN_MODERATOR,
        actor_id=moderator_id,
        event_type=EVENT_TYPE.MODERATOR_REVIEW,
        action_taken=action, # "cleared" or "permanently_removed"
        human_notes=notes
    )
    db.add(event)
    
    response = db.get(SampleResponse, sample_id)
    if response:
        response.moderation_status = action
        
    db.commit()

def get_zipf_pmf(N, s):
    """Zipfian (Power Law): s determines the heavy tail."""
    k = np.arange(1, N + 1)
    pmf = k**(-float(s))
    return pmf / np.sum(pmf)

class ParticipantCriteria(NamedTuple):
    user: User | None
    exists: bool
    has_ended_participation: bool
    num_responses: int
    num_flagged_responses: int

    @property
    def is_excluded(self) -> bool:
        if not self.exists:
            return True
        if self.has_ended_participation:
            return True
        if self.num_responses <= PHASE_1_QUALIFICATION_NUM_RESPONSES and self.num_flagged_responses >= MAX_AUTOMOD_FLAGS:
            return True
        if self.num_responses >= MAX_TOTAL_RESPONSES:
            return True

        return False

    @property
    def phase(self) -> int:
        if self.num_responses <= PHASE_1_QUALIFICATION_NUM_RESPONSES:
            return 1
        else:
            return 2
    
    @property
    def max_responses_for_this_phase(self) -> int:
        return PHASE_1_QUALIFICATION_NUM_RESPONSES if self.phase == 1 else MAX_TOTAL_RESPONSES

def check_participant_criteria(db: Session, user_unique_id: str | None = None, user_login_id: str | None = None, user_password: str | None = None) -> ParticipantCriteria:
    if user_unique_id is not None:
        user = db.get(User, user_unique_id)
    elif user_login_id is not None and user_password is not None:
        user = db.exec(select(User).where(User.login_id == user_login_id, User.password == user_password)).first()
    else:
        raise ValueError("Must provide either user_unique_id or (user_login_id and user_password)")

    if user is None:
        return ParticipantCriteria(user=None, exists=False, has_ended_participation=False, num_responses=0, num_flagged_responses=0)

    return ParticipantCriteria(user=user, exists=True, has_ended_participation=user.has_ended_participation, num_responses=user.num_responses_given, num_flagged_responses=user.num_automod_flagged_responses)

def add_root(
    db: Session,
    root_id: str,
    ambiguous_question: str,
    priority: float,
    unambiguous_question: str,
    multimodal_file_path: str,
    original_dataset: str,
    original_dataset_sample_id: str,
):
    root = ConversationRoot(
        root_id = root_id,
        ambiguous_question = ambiguous_question,
        priority = priority,
        unambiguous_question = unambiguous_question,
        multimodal_file_path = multimodal_file_path,
        original_dataset = original_dataset,
        original_dataset_sample_id = original_dataset_sample_id,
    )
    try:
        db.add(root)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Tree with id {root_id} already exists.")

class SampleReturn(NamedTuple):
    sample: QuestionAskerSampleData | QuestionAnswererSampleData
    node_code: str
    conversation_root: ConversationRoot
    parent_sample: SampleResponse | None
    collection_id: str
    

def select_sample_for_participant(db: Session, user_unique_id: str, zipf_s: float = DEFAULT_ZIPF_S) -> SampleReturn:
    criteria = check_participant_criteria(db, user_unique_id)
    if criteria.is_excluded:
        if not criteria.exists:
            raise UserNotFoundError("User not found.")
        elif criteria.has_ended_participation:
            raise UserEndedParticipationError("You have chosen to end your participation in the study.")
        elif criteria.num_responses >= MAX_TOTAL_RESPONSES:
            raise MaxResponsesReachedError("You have reached the maximum total number of responses for this study.")
        else:
            print("No samples found. Criteria object: ", criteria)
            raise NoSamplesAvailableError("No samples available at this time.")

    participated_root_ids = db.exec(select(SampleResponse.root_id).where(SampleResponse.user_unique_id == user_unique_id)).all()
    participated_root_ids = set(participated_root_ids)

    remove_expired_locks(db)
    locked_roots = db.exec(select(TreeLock.root_id, TreeLock.collection_id)).all()
    locked_collection_roots = set((r, c) for r, c in locked_roots)

    depth_1_count = db.exec(
        select(func.count(SampleResponse.sample_id)).where(
            SampleResponse.user_unique_id == user_unique_id,
            SampleResponse.depth == 1
        )
    ).one()
    depth_1_capped = depth_1_count >= MAX_DEPTH_1_SAMPLES_PER_USER

    eligible_collections = {}

    for collection_id, config in COLLECTIONS.items():
        expansion_order = config.get("expansion_order", [])
        if not expansion_order:
            continue
            
        unfinished_roots = db.exec(
            select(ConversationRoot.root_id, ConversationRoot.priority, TreeCollectionState)
            .join(
                TreeCollectionState, 
                (TreeCollectionState.root_id == ConversationRoot.root_id) & (TreeCollectionState.collection_id == collection_id), 
                isouter=True
            )
        ).all()
        
        eligible_roots = []
        for root_id, priority, state in unfinished_roots:
            if root_id in participated_root_ids: continue
            if (root_id, collection_id) in locked_collection_roots: continue
            
            if state and state.is_completed: continue
            idx = state.next_expansion_index if state else 0
            
            if idx >= len(expansion_order): continue
            
            node_code = expansion_order[idx]
            
            if len(node_code) % 2 == 1:
                required_role = config.get("asker_role")
            else:
                required_role = config.get("answerer_role")
                
            if required_role != "human": continue
            
            if depth_1_capped and len(node_code) == 1: continue
            
            eligible_roots.append((root_id, priority, node_code))
            
        if eligible_roots:
            completed_roots = db.exec(select(func.count(TreeCollectionState.root_id)).where(TreeCollectionState.collection_id == collection_id, TreeCollectionState.is_completed == True)).one()
            total_roots = len(unfinished_roots) # Every root counts, even if it has no TreeCollectionState
            completion_rate = completed_roots / max(1, total_roots)
            
            eligible_collections[collection_id] = {
                "roots": eligible_roots,
                "completion_rate": completion_rate
            }

    if not eligible_collections:
        # Check if they were excluded because of depth 1 cap
        if depth_1_capped:
            raise Depth1CapReachedError("You have reached the limit for starting new conversations right now. If you check back a bit later, more follow-up tasks should become available.")
        print("No eligible collections found.")
        raise NoSamplesAvailableError("No samples available at this time.")

    # Find the minimum completion rate
    min_rate = min(info["completion_rate"] for info in eligible_collections.values())
    best_collections = [cid for cid, info in eligible_collections.items() if info["completion_rate"] == min_rate]
    
    # Pick a collection randomly if tied
    selected_collection_id = np.random.choice(best_collections)
    eligible_roots = eligible_collections[selected_collection_id]["roots"]
    
    # Sort eligible roots by priority
    eligible_roots.sort(key=lambda x: x[1], reverse=True)
    probabilities = get_zipf_pmf(N=len(eligible_roots), s=zipf_s)
    sampled_index = np.random.choice(np.arange(len(eligible_roots)), p=probabilities)
    selected_root_id, _, next_expansion_node_code = eligible_roots[sampled_index]

    sample_return = _build_sample_return(db, selected_root_id, selected_collection_id, next_expansion_node_code)
    db.commit()
    return sample_return

def _build_sample_return(db: Session, selected_root_id: str, collection_id: str, next_expansion_node_code: str, assigned_sample_id: str = None) -> SampleReturn:
    conversation_root = db.get(ConversationRoot, selected_root_id)
    assert conversation_root is not None

    root_ambiguous_question = conversation_root.ambiguous_question
    root_unambiguous_question = conversation_root.unambiguous_question

    ancestor_samples: list[SampleResponse] = []
    if len(next_expansion_node_code) > 1:
        parent_node_code = next_expansion_node_code[:-1]
        
        base_query = select(SampleResponse).where(
            SampleResponse.root_id == selected_root_id,
            SampleResponse.collection_id == collection_id,
            SampleResponse.node_code == parent_node_code,
            SampleResponse.moderation_status == MODERATION_ACTION.CLEARED
        ).cte(name="ancestor_samples", recursive=True)

        recursive_query = select(SampleResponse).join(
            base_query, SampleResponse.sample_id == base_query.c.parent_sample_id
        )

        ancestors_cte = base_query.union_all(recursive_query)
        ancestor_alias = aliased(SampleResponse, ancestors_cte)
        
        statement = select(ancestor_alias)
        ancestor_samples = list(db.exec(statement).all())
        ancestor_samples.sort(key=lambda s: len(s.node_code))
    assert len(ancestor_samples) == len(next_expansion_node_code) - 1, f"Expected {len(next_expansion_node_code) - 1} ancestor samples, got {len(ancestor_samples)}"

    dialog_history: list[DialogMessage] = []
    for ancestor_sample in ancestor_samples:
        sample_type = ancestor_sample.sample_type
        if sample_type == SAMPLE_TYPE.ASKER:
            assert ancestor_sample.next_question is not None
            dialog_history.append(
                DialogMessage(
                    text = ancestor_sample.next_question,
                    role = "question_asker",
                    is_flagged = ancestor_sample.is_flagged,
                    flagged_reason = ancestor_sample.flagged_reason
                )
            )
        elif sample_type == SAMPLE_TYPE.ANSWERER:
            assert ancestor_sample.answer is not None
            dialog_history.append(
                DialogMessage(
                    text = ancestor_sample.answer,
                    role = "question_answerer",
                    is_flagged = ancestor_sample.is_flagged,
                    flagged_reason = ancestor_sample.flagged_reason
                )
            )

    # step 8: Format the sample into the response
    # First we need to check if the immediate parent of the new node is a question asking or answering node
    next_sample_type = None
    parent_sample = None
    if len(ancestor_samples) == 0:
        next_sample_type = SAMPLE_TYPE.ASKER
    else:
        parent_sample = ancestor_samples[-1]
        assert parent_sample is not None
        parent_sample_type: SAMPLE_TYPE = parent_sample.sample_type
        next_sample_type = SAMPLE_TYPE.ASKER if parent_sample_type == SAMPLE_TYPE.ANSWERER else SAMPLE_TYPE.ANSWERER

    sample_id = assigned_sample_id if assigned_sample_id else generate_uuid()

    if next_sample_type == SAMPLE_TYPE.ANSWERER:
        next_sample = QuestionAnswererSampleData(
            sample_id = sample_id,
            task_role = "question_answerer",
            multimodal_input = MultimodalInputImage(
                type = "image",
                url = f"/api/v1/images?id={selected_root_id}"
            ),
            ambiguous_question = root_ambiguous_question,
            intended_question = root_unambiguous_question,
            dialog_history = dialog_history
        )
    elif next_sample_type == SAMPLE_TYPE.ASKER:
        next_sample = QuestionAskerSampleData(
            sample_id = sample_id,
            task_role = "question_asker",
            multimodal_input = MultimodalInputImage(
                type = "image",
                url = f"/api/v1/images?id={selected_root_id}"
            ),
            ambiguous_question = root_ambiguous_question,
            dialog_history = dialog_history
        )

    return SampleReturn(sample=next_sample, node_code=next_expansion_node_code, conversation_root=conversation_root, parent_sample=parent_sample, collection_id=collection_id)

def get_locked_sample_for_participant(db: Session, user_unique_id: str) -> SampleReturn | None:
    criteria = check_participant_criteria(db, user_unique_id)
    if criteria.is_excluded:
        if not criteria.exists:
            raise UserNotFoundError("User not found.")
        elif criteria.has_ended_participation:
            raise UserEndedParticipationError("You have chosen to end your participation in the study.")
        elif criteria.num_responses >= MAX_TOTAL_RESPONSES:
            raise MaxResponsesReachedError("You have reached the maximum total number of responses for this study.")
        else:
            raise NoSamplesAvailableError("No samples available at this time.")

    remove_expired_locks(db)
    lock = db.exec(select(TreeLock).where(TreeLock.user_unique_id == user_unique_id)).first()
    if not lock:
        return None
        
    sent_sample = db.exec(
        select(SentSample).where(
            SentSample.user_unique_id == user_unique_id,
            SentSample.root_id == lock.root_id,
            SentSample.collection_id == lock.collection_id,
            SentSample.is_returned == False
        ).order_by(SentSample.timestamp.desc())
    ).first()

    if not sent_sample:
        return None

    return _build_sample_return(db, lock.root_id, lock.collection_id, sent_sample.intended_node_code, assigned_sample_id=sent_sample.sample_id)
    
def add_sent_sample(db: Session, sample_data: SampleReturn, unique_user_id: str):
    """
    Adds the sent sample to the database. Should be called by the request handler that called select_sample_for_participant
    """
    parent_id = sample_data.parent_sample.sample_id if sample_data.parent_sample is not None else None
    sent_sample = SentSample(
        sample_id=sample_data.sample.sample_id,
        intended_node_code=sample_data.node_code,
        user_unique_id=unique_user_id,
        parent_id=parent_id,
        root_id=sample_data.conversation_root.root_id,
        collection_id=sample_data.collection_id,
        timestamp=datetime.now(timezone.utc)
    )
    try:
        db.add(sent_sample)
        db.commit()
        db.refresh(sent_sample)
        return sent_sample
    except:
        db.rollback()
        raise

def get_sent_sample(db: Session, sample_id: str) -> SentSample | None:
    return db.get(SentSample, sample_id)

class NoSentSampleError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class WrongUserError(Exception):
    pass

class UserExcludedError(Exception):
    pass

class SampleAlreadyReturnedError(Exception):
    pass

class NoSamplesAvailableError(Exception):
    pass

class UserEndedParticipationError(Exception):
    pass

class MaxResponsesReachedError(Exception):
    pass

class Depth1CapReachedError(Exception):
    pass
    

def process_returned_sample(db: Session, response: TaskResponseRequest) -> bool:
    incoming_sample_id = response.sample_id
    sent_sample = get_sent_sample(db, sample_id=incoming_sample_id)
    if sent_sample is None:
        raise NoSentSampleError(f"No sent sample found for the given sample_id: {incoming_sample_id}")

    criteria = check_participant_criteria(db, user_login_id=response.login_id, user_password=response.password)
    user = criteria.user

    if user is None:
        raise UserNotFoundError(f"No user found for the given login_id: {response.login_id}")
    if user.unique_id != sent_sample.user_unique_id:
        raise WrongUserError(f"The user that is returning the sample (unique_id: {user.unique_id}) is not the user that the sample was sent to (unique_id: {sent_sample.user_unique_id})")

    remove_lock(db, root_id=sent_sample.root_id, collection_id=sent_sample.collection_id, user_unique_id=user.unique_id)
    if criteria.is_excluded:
        raise UserExcludedError(f"User {user.login_id} is excluded from the study")

    if sent_sample.is_returned:
        raise SampleAlreadyReturnedError(f"Sample with id {incoming_sample_id} has already been returned")

    sent_sample.is_returned = True
    db.add(sent_sample)

    user.num_responses_given += 1
    db.add(user)

    collection_id = sent_sample.collection_id
    collection_state = db.get(TreeCollectionState, (sent_sample.root_id, collection_id))
    if collection_state is None:
        collection_state = TreeCollectionState(
            root_id=sent_sample.root_id, 
            collection_id=collection_id, 
            next_expansion_index=0, 
            is_completed=False
        )

    col_config = COLLECTIONS.get(collection_id)
    if col_config is None or "expansion_order" not in col_config:
        raise ValueError(f"Collection {collection_id} not found or missing expansion_order")
    actual_expansion_order = col_config["expansion_order"]

    root_next_expansion_index = collection_state.next_expansion_index
    if collection_state.is_completed or root_next_expansion_index >= len(actual_expansion_order):
        db.commit()
        return False

    root_next_node_code = actual_expansion_order[root_next_expansion_index]
    sent_sample_node_code = sent_sample.intended_node_code
    if root_next_node_code != sent_sample_node_code:
        db.commit()
        return False
    
    depth = len(sent_sample_node_code)

    response_data = response.response_data
    if response_data.response_type == "question_asker":
        returned_sample = SampleResponse(
            sample_id=incoming_sample_id,
            node_code=sent_sample_node_code,
            user_unique_id=user.unique_id,
            parent_sample_id=sent_sample.parent_id,
            root_id=sent_sample.root_id,
            collection_id=collection_id,
            depth=depth,
            timestamp=datetime.now(timezone.utc),
            participant_type="human",
            sample_type=SAMPLE_TYPE.ASKER,
            previous_answer_meaningful_score = response_data.previous_answer_meaningful_score,
            current_guess = response_data.current_guess,
            current_guess_confidence_score = response_data.confidence_score,
            next_question = response_data.next_question
        )
        response_content = response_data.next_question
    elif response_data.response_type == "question_answerer":
        returned_sample = SampleResponse(
            sample_id=incoming_sample_id,
            node_code=sent_sample_node_code,
            user_unique_id=user.unique_id,
            parent_sample_id=sent_sample.parent_id,
            root_id=sent_sample.root_id,
            collection_id=collection_id,
            depth=depth,
            timestamp=datetime.now(timezone.utc),
            participant_type="human",
            sample_type=SAMPLE_TYPE.ANSWERER,
            previous_question_relevant_score = response_data.previous_question_relevant_score,
            answer = response_data.answer
        )
        response_content = response_data.answer
    else:
        raise ValueError(f"Invalid response type: {response_data.response_type}")

    ancestor_samples: list[SampleResponse] = []
    
    history_lines = []
    conversation_root = db.get(ConversationRoot, sent_sample.root_id)
    if conversation_root and conversation_root.ambiguous_question:
        history_lines.append(f"Initial Question: {conversation_root.ambiguous_question}")
        
    if len(sent_sample_node_code) > 1:
        parent_node_code = sent_sample_node_code[:-1]
        
        base_query = select(SampleResponse).where(
            SampleResponse.root_id == sent_sample.root_id,
            SampleResponse.collection_id == collection_id,
            SampleResponse.node_code == parent_node_code,
            SampleResponse.moderation_status == MODERATION_ACTION.CLEARED
        ).cte(name="ancestor_samples", recursive=True)

        recursive_query = select(SampleResponse).join(
            base_query, SampleResponse.sample_id == base_query.c.parent_sample_id
        )

        ancestors_cte = base_query.union_all(recursive_query)
        ancestor_alias = aliased(SampleResponse, ancestors_cte)
        
        statement = select(ancestor_alias)
        ancestor_samples = list(db.exec(statement).all())
        ancestor_samples.sort(key=lambda s: len(s.node_code))
        
        for s in ancestor_samples:
            if s.sample_type == SAMPLE_TYPE.ASKER and s.next_question:
                history_lines.append(f"Question Asker: {s.next_question}")
            elif s.sample_type == SAMPLE_TYPE.ANSWERER and s.answer:
                history_lines.append(f"Question Answerer: {s.answer}")
                
    conversation_context = "\n".join(history_lines)

    moderation_report = moderator.evaluate_text(response_content, fast_fail=False, conversation_context=conversation_context)
    if moderation_report.action != "pass":
        returned_sample.moderation_status = MODERATION_ACTION.PLACED_ON_HOLD
        moderation_event = ModerationEvent(
            event_id = generate_uuid(),
            sample_id = incoming_sample_id,
            timestamp = datetime.now(timezone.utc),
            actor_type = ACTOR_TYPE.AUTOMOD,
            actor_id = None,
            event_type = EVENT_TYPE.AUTOMOD_CHECK,
            action_taken = MODERATION_ACTION.PLACED_ON_HOLD,
            automod_scores = moderation_report.detoxify_scores,
            human_notes = None
        )
        user.num_automod_flagged_responses = (user.num_automod_flagged_responses or 0) + 1
        db.add(user)
        db.add(moderation_event)
        db.add(returned_sample)
        db.commit()
        return False
    else:
        returned_sample.moderation_status = MODERATION_ACTION.CLEARED
        moderation_event = ModerationEvent(
            event_id = generate_uuid(),
            sample_id = incoming_sample_id,
            timestamp = datetime.now(timezone.utc),
            actor_type = ACTOR_TYPE.AUTOMOD,
            actor_id = None,
            event_type = EVENT_TYPE.AUTOMOD_CHECK,
            action_taken = MODERATION_ACTION.CLEARED,
            automod_scores = moderation_report.detoxify_scores,
            human_notes = None
        )
        collection_state.next_expansion_index += 1
        if collection_state.next_expansion_index >= len(actual_expansion_order):
            collection_state.is_completed = True
        db.add(collection_state)
        db.add(moderation_event)
        db.add(returned_sample)
        db.commit()
        return True
