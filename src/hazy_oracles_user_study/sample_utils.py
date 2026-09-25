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
    LOCK_TIMEOUT_MINUTES
)

from hazy_oracles_user_study.server_models import (
    DialogMessage,
    QuestionAnswererSampleData,
    QuestionAskerSampleData,
    MultimodalInputImage,
    TaskResponseRequest,
)

moderator = ContentModerator()

def add_lock(db: Session, root_id: str, user_unique_id: str, timeout_minutes: int = LOCK_TIMEOUT_MINUTES):
    """Creates or updates a lock for a specific tree."""
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)).replace(tzinfo=None)
    
    # Check if lock exists (even if expired) to overwrite
    lock = db.get(TreeLock, root_id)
    if not lock:
        lock = TreeLock(root_id=root_id, user_unique_id=user_unique_id, expires_at=expires_at)
        db.add(lock)
    else:
        lock.user_unique_id = user_unique_id
        lock.expires_at = expires_at
        
    db.commit()

def remove_lock(db: Session, root_id: str, user_unique_id: str):
    """Removes a lock if it belongs to the user."""
    lock = db.get(TreeLock, root_id)
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

def is_locked(db: Session, root_id: str) -> bool:
    """Checks if an active lock exists. Cleans up if it is expired."""
    lock = db.get(TreeLock, root_id)
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
        next_expansion_index = 0,
        is_completed = False,
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
    

def select_sample_for_participant(db: Session, node_code_expansion_order: list[str], user_unique_id: str, zipf_s: float = DEFAULT_ZIPF_S) -> SampleReturn:
    # step 0: Check if the user is eligible to receive another sample
    criteria = check_participant_criteria(db, user_unique_id)
    if criteria.is_excluded:
        if not criteria.exists:
            raise UserNotFoundError("User not found.")
        elif criteria.has_ended_participation:
            raise UserEndedParticipationError("You have chosen to end your participation in the study.")
        elif criteria.num_responses >= MAX_TOTAL_RESPONSES:
            raise MaxResponsesReachedError("You have reached the maximum total number of responses for this study.")
        else:
            # Spam filtered
            raise NoSamplesAvailableError("No samples available at this time.")

    # step 1: Get the ids of all trees that this person has not participated in
    participated_root_ids = db.exec(select(SampleResponse.root_id).where(SampleResponse.user_unique_id == user_unique_id)).all()
    participated_root_ids = set(root_id for root_id in participated_root_ids)

    # step 2: Get a list of the ids of all trees that are currently locked
    remove_expired_locks(db)
    locked_root_ids = db.exec(select(TreeLock.root_id)).all()
    locked_root_ids = set(root_id for root_id in locked_root_ids)

    # step 2.1: Get a list of the ids of all trees that have not reached the end of the expansion order list
    unfinished_root_ids = db.exec(select(ConversationRoot.root_id, ConversationRoot.priority, ConversationRoot.next_expansion_index).where(ConversationRoot.is_completed == False)).all()

    # step 2.2: Check if user has exceeded the depth 1 limit
    depth_1_count = db.exec(
        select(func.count(SampleResponse.sample_id)).where(
            SampleResponse.user_unique_id == user_unique_id,
            SampleResponse.depth == 1
        )
    ).one()

    # step 3: Compute the subtraction of the unfinished_root_ids with the locked or already participated root ids
    eligible_root_ids_without_constraint = [(root_id, priority) for root_id, priority, _ in unfinished_root_ids if root_id not in locked_root_ids and root_id not in participated_root_ids]

    if depth_1_count >= MAX_DEPTH_1_SAMPLES_PER_USER:
        depth_1_indices = {i for i, code in enumerate(node_code_expansion_order) if len(code) == 1}
        eligible_root_ids = [(root_id, priority) for root_id, priority, next_idx in unfinished_root_ids if root_id not in locked_root_ids and root_id not in participated_root_ids and next_idx not in depth_1_indices]
        
        if len(eligible_root_ids) == 0 and len(eligible_root_ids_without_constraint) > 0:
            raise Depth1CapReachedError("You have reached the limit for starting new conversations right now. If you check back a bit later, more follow-up tasks should become available.")
    else:
        eligible_root_ids = eligible_root_ids_without_constraint

    if len(eligible_root_ids) == 0:
        raise NoSamplesAvailableError("No samples available at this time.")

    # step 4: Order these trees by their priority
    eligible_root_ids.sort(key=lambda x: x[1], reverse=True)

    # step 5: Randomly select a tree based on a bias toward high ranked trees
    probabilities = get_zipf_pmf(N=len(eligible_root_ids), s=zipf_s)
    sampled_index = np.random.choice(np.arange(len(eligible_root_ids)), p=probabilities)
    selected_root_id = eligible_root_ids[sampled_index][0]

    # step 6: Read the next_expansion_index and get the corresponding node id
    conversation_root = db.get(ConversationRoot, selected_root_id)
    assert conversation_root is not None

    next_expansion_index = conversation_root.next_expansion_index
    root_ambiguous_question = conversation_root.ambiguous_question
    root_unambiguous_question = conversation_root.unambiguous_question

    # step 7: Read all ancestors of the node id to expand using a recursive CTE
    next_expansion_node_code = node_code_expansion_order[next_expansion_index]
    
    ancestor_samples: list[SampleResponse] = []
    if len(next_expansion_node_code) > 1:
        parent_node_code = next_expansion_node_code[:-1]
        
        base_query = select(SampleResponse).where(
            SampleResponse.root_id == selected_root_id,
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
                    role = "question_asker"
                )
            )
        elif sample_type == SAMPLE_TYPE.ANSWERER:
            assert ancestor_sample.answer is not None
            dialog_history.append(
                DialogMessage(
                    text = ancestor_sample.answer,
                    role = "question_answerer"
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

    if next_sample_type == SAMPLE_TYPE.ANSWERER:
        next_sample = QuestionAnswererSampleData(
            sample_id = generate_uuid(),
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
            sample_id = generate_uuid(),
            task_role = "question_asker",
            multimodal_input = MultimodalInputImage(
                type = "image",
                url = f"/api/v1/images?id={selected_root_id}"
            ),
            ambiguous_question = root_ambiguous_question,
            dialog_history = dialog_history
        )

    db.commit()

    return SampleReturn(sample=next_sample, node_code=next_expansion_node_code, conversation_root=conversation_root, parent_sample=parent_sample)
    
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
    

def process_returned_sample(db: Session, response: TaskResponseRequest, selected_expansion_order: list[str]) -> bool:
    """
    Called once the user has entered their response. Does checks to make sure this sample should be used.
    Checks whether we have a sent sample in the database that corresponds with this incoming sample.
    Runs automod.
    Checks whether another node for this root with this node id has already come in.
    If we pass, adds this sample and increments the conversation root's next_expansion_index.
    And removes the lock.
    """

    # First, we check if this response actually corresponds to the sample that was sent to the user.
    incoming_sample_id = response.sample_id
    sent_sample = get_sent_sample(db, sample_id=incoming_sample_id)
    if sent_sample is None:
        raise NoSentSampleError(f"No sent sample found for the given sample_id: {incoming_sample_id}")

    # We also need to check if the sent sample was actually sent to the participant that is returning it
    criteria = check_participant_criteria(db, user_login_id=response.login_id, user_password=response.password)
    user = criteria.user

    if user is None:
        raise UserNotFoundError(f"No user found for the given login_id: {response.login_id}")
    if user.unique_id != sent_sample.user_unique_id:
        raise WrongUserError(f"The user that is returning the sample (unique_id: {user.unique_id}) is not the user that the sample was sent to (unique_id: {sent_sample.user_unique_id})")

    # At this point, we remove the lock if it exists no matter what
    remove_lock(db, root_id=sent_sample.root_id, user_unique_id=user.unique_id)
    if criteria.is_excluded:
        raise UserExcludedError(f"User {user.login_id} is excluded from the study")

    if sent_sample.is_returned:
        raise SampleAlreadyReturnedError(f"Sample with id {incoming_sample_id} has already been returned")

    # Update the sent sample to reflect that it has been returned
    sent_sample.is_returned = True
    db.add(sent_sample)

    # Track user response count
    user.num_responses_given += 1
    db.add(user)

    # Check if the expected node code is the same as the node code that the root currently wants expanded
    # If the lock expired and somebody else submitted in the meantime, there might already be a sample for that node code
    conversation_root = db.get(ConversationRoot, sent_sample.root_id)
    if conversation_root is None:
        raise ValueError(f"Conversation root not found for the given root_id: {sent_sample.root_id}")

    root_next_expansion_index = conversation_root.next_expansion_index
    if conversation_root.is_completed or root_next_expansion_index >= len(selected_expansion_order):
        # Conversation root has already reached the end of its expansion order
        db.commit()
        return False

    root_next_node_code = selected_expansion_order[root_next_expansion_index]
    sent_sample_node_code = sent_sample.intended_node_code
    if root_next_node_code != sent_sample_node_code:
        # This isn't an error, but it means that this sample is not going to be shown to anybody else
        db.commit()
        return False
    
    depth = len(sent_sample_node_code)

    # Add the new sample into the database
    response_data = response.response_data
    if response_data.response_type == "question_asker":
        returned_sample = SampleResponse(
            sample_id=incoming_sample_id,
            node_code=sent_sample_node_code,
            user_unique_id=user.unique_id,
            parent_sample_id=sent_sample.parent_id,
            root_id=sent_sample.root_id,
            depth=depth,
            timestamp=datetime.now(timezone.utc),
            participant_type="human",
            sample_type=SAMPLE_TYPE.ASKER,
            
            # Asker Fields
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
            depth=depth,
            timestamp=datetime.now(timezone.utc),
            participant_type="human",
            sample_type=SAMPLE_TYPE.ANSWERER,

            # Answerer Fields
            previous_question_relevant_score = response_data.previous_question_relevant_score,
            answer = response_data.answer
        )
        response_content = response_data.answer
    else:
        raise ValueError(f"Invalid response type: {response_data.response_type}")

    # The automod tells us whether we should use this response
    moderation_report = moderator.evaluate_text(response_content, fast_fail=False)
    if moderation_report.action != "pass":
        # Then we don't place this as a possible response for follow up
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
        # Then we can simply add this as the next node and increment the expansion index
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
        conversation_root.next_expansion_index += 1
        if conversation_root.next_expansion_index >= len(selected_expansion_order):
            conversation_root.is_completed = True
        db.add(conversation_root)
        db.add(moderation_event)
        db.add(returned_sample)
        db.commit()
        return True
