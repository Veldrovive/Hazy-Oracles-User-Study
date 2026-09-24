import pytest
from sqlmodel import Session
from hazy_oracles_user_study import EXPANSION_ORDER_BASE64
from hazy_oracles_user_study.database import User, ConversationRoot
from hazy_oracles_user_study.sample_utils import (
    select_sample_for_participant,
    add_lock,
    is_locked,
    add_sent_sample,
    process_returned_sample,
    SampleAlreadyReturnedError,
    UserNotFoundError,
    NoSentSampleError,
    WrongUserError

)
from hazy_oracles_user_study.server_models import TaskResponseRequest, QuestionAskerResponseData


class TestSampleUtils:
    def test_select_sample(self, session: Session, user_list: list[User], conversation_roots: list[ConversationRoot]):
        print(f"Has {len(user_list)} users and {len(conversation_roots)} conversation roots")

        #### User 1 test ####
        sample_return = select_sample_for_participant(
            db=session,
            node_code_expansion_order=EXPANSION_ORDER_BASE64,
            user_unique_id=user_list[0].unique_id,
            zipf_s=float("inf")  # Forces using highest priority tree
        )
        assert sample_return is not None
        sample, node_code, conversation_root, parent_sample = sample_return
        
        add_lock(session, root_id=conversation_root.root_id, user_unique_id=user_list[0].unique_id, timeout_minutes=2)

        assert is_locked(session, root_id=conversation_root.root_id)

        assert sample.task_role == "question_asker"  # First role is always an asker
        assert sample.ambiguous_question == "What condition does the man have?"  # This is the highest priority root
        assert len(sample.dialog_history) == 0  # No previous questions in this conversation

        ####  User 2 test #####
        # Now we need to add a SentSample to simulate the back and forth of a sample being sent and a response being received
        sent_sample = add_sent_sample(db=session, sample_data=sample_return, unique_user_id=user_list[0].unique_id)
        assert sent_sample is not None

        # Now let's see what happens if we request a new sample for a different user without having 
        sample_return_2 = select_sample_for_participant(
            db=session,
            node_code_expansion_order=EXPANSION_ORDER_BASE64,
            user_unique_id=user_list[1].unique_id,
            zipf_s=float("inf")  # Forces using highest priority tree
        )
        assert sample_return_2 is not None
        sample_2, node_code_2, conversation_root_2, parent_sample_2 = sample_return_2
        
        assert sample_2.task_role == "question_asker"  # It is still the case that this is an empty new tree
        assert sample_2.ambiguous_question != sample.ambiguous_question  # Should be a different root

        #### Back to user 1 for returning the response ####
        # And finally we simulate a response
        response_data = TaskResponseRequest(
            login_id=user_list[0].login_id,
            password=user_list[0].password,
            sample_id=sample.sample_id,
            response_data=QuestionAskerResponseData(
                response_type='question_asker',
                previous_answer_meaningful_score=5,
                current_guess="I don't know",
                confidence_score=5,
                next_question="Are you asking about the things on his face?"
            )
        )

        # First, let's cause some errors
        # Non-existent login_id and password
        incorrect_response_data = response_data.model_copy()
        incorrect_response_data.login_id = "not_a_user"
        incorrect_response_data.password = "not_a_password"
        with pytest.raises(UserNotFoundError):
            process_returned_sample(session, incorrect_response_data, EXPANSION_ORDER_BASE64)

        # Existing user, but incorrect
        incorrect_response_data = response_data.model_copy()
        incorrect_response_data.login_id = user_list[1].login_id
        incorrect_response_data.password = user_list[1].password
        with pytest.raises(WrongUserError):
            process_returned_sample(session, incorrect_response_data, EXPANSION_ORDER_BASE64)

        # Wrong sent sample id
        incorrect_response_data = response_data.model_copy()
        incorrect_response_data.sample_id = "not_a_sample_id"
        with pytest.raises(NoSentSampleError):
            process_returned_sample(session, incorrect_response_data, EXPANSION_ORDER_BASE64)

        response_result = process_returned_sample(session, response_data, EXPANSION_ORDER_BASE64)
        assert response_result is True

        # If we try to use this return again it should fail
        with pytest.raises(SampleAlreadyReturnedError):
            response_result = process_returned_sample(session, response_data, EXPANSION_ORDER_BASE64)

        # Now a new user should be able to get a sample from this root
        #### User 3 test ####
        sample_return_3 = select_sample_for_participant(
            db=session,
            node_code_expansion_order=EXPANSION_ORDER_BASE64,
            user_unique_id=user_list[2].unique_id,
            zipf_s=float("inf")  # Forces using highest priority tree
        )
        assert sample_return_3 is not None
        sample_3, node_code_3, conversation_root_3, parent_sample_3 = sample_return_3

        # The root should be the same root as from sample 1
        assert conversation_root_3.root_id == conversation_root.root_id
        assert node_code_3 != node_code

        sent_sample_3 = add_sent_sample(db=session, sample_data=sample_return_3, unique_user_id=user_list[2].unique_id)
        assert sent_sample_3 is not None

        # Now we will try triggering the automod to make sure that the same is not included in future dialogs
        response_data = TaskResponseRequest(
            login_id=user_list[2].login_id,
            password=user_list[2].password,
            sample_id=sample_3.sample_id,
            response_data=QuestionAskerResponseData(
                response_type='question_asker',
                previous_answer_meaningful_score=5,
                current_guess="Acne",
                confidence_score=5,
                next_question="Are you asking about why he is ugly?"  # This counts as toxic
            )
        )
        response_result = process_returned_sample(session, response_data, EXPANSION_ORDER_BASE64)
        assert response_result is False
        