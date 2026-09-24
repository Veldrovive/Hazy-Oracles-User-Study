import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from sqlmodel import select
from hazy_oracles_user_study.database import SampleResponse

from hazy_oracles_user_study.server import app, db_manager
from hazy_oracles_user_study.database import User, ConversationRoot
from hazy_oracles_user_study.server_models import (
    UserStatusUpdateRequest,
    TaskSampleRequest,
    TaskResponseRequest,
    QuestionAskerResponseData,
    QuestionAnswererResponseData
)
import random



def init_user(client: TestClient, user: User):
    login_resp = client.get("/api/v1/user/login", params={"login_id": user.login_id, "password": user.password})
    assert login_resp.status_code == 200

    status_req = UserStatusUpdateRequest(login_id=user.login_id, password=user.password).model_dump()
    
    consent_resp = client.post("/api/v1/user/consent", json=status_req)
    assert consent_resp.status_code == 200

    read_asker_resp = client.post("/api/v1/user/read_asker_instructions", json=status_req)
    assert read_asker_resp.status_code == 200

    read_answerer_resp = client.post("/api/v1/user/read_answerer_instructions", json=status_req)
    assert read_answerer_resp.status_code == 200

def get_sample(client: TestClient, user: User, zipf_s: float = 1.2):
    sample_req = TaskSampleRequest(login_id=user.login_id, password=user.password, zipf_s=zipf_s).model_dump()
    sample_resp = client.post("/api/v1/task/sample", json=sample_req)
    assert sample_resp.status_code == 200
    resp_json = sample_resp.json()
    if resp_json.get("status") == "success":
        return resp_json["data"]
    return None

def return_response(client: TestClient, user: User, sample_id: str, response_data):
    response_payload = TaskResponseRequest(
        login_id=user.login_id,
        password=user.password,
        sample_id=sample_id,
        response_data=response_data
    ).model_dump()
    resp = client.post("/api/v1/task/response", json=response_payload)
    assert resp.status_code == 200
    return resp

def run_user_flow(client: TestClient, user: User, asker_response_data, answerer_response_data, zipf_s: float = 1.2):
    init_user(client, user)
    sample_data = get_sample(client, user, zipf_s)
    
    if sample_data["task_role"] == "question_asker":
        response_data = asker_response_data
    else:
        response_data = answerer_response_data
        
    return_response(client, user, sample_data["sample_id"], response_data)
    return sample_data


class TestServer:
    @pytest.fixture(autouse=True)
    def setup_client(self, session: Session):
        def get_session_override():
            return session

        app.dependency_overrides[db_manager.get_session] = get_session_override
        self.client = TestClient(app)
        yield
        app.dependency_overrides.clear()

    def test_server_sample_and_response(
        self, session: Session, user_list: list[User], conversation_roots: list[ConversationRoot]
    ):
        print(f"Has {len(user_list)} users and {len(conversation_roots)} conversation roots")

        #### User 1 test ####
        user1 = user_list[0]
        
        # User needs to be properly initialized
        # call the logged in, consented, and read endpoints
        init_user(self.client, user1)

        # Request a sample
        sample_data1 = get_sample(self.client, user1, zipf_s=100000)  # large zipf_s = samples highest priority with p ~= 1
        
        assert sample_data1["task_role"] == "question_asker"  # First role is always an asker
        assert sample_data1["ambiguous_question"] == conversation_roots[0].ambiguous_question  # This is the highest priority root
        assert len(sample_data1["dialog_history"]) == 0  # No previous questions in this conversation

        #### User 2 test #####
        # Now let's see what happens if we request a new sample for a different user
        # Note: the server endpoint already adds a SentSample, so we don't need to do it manually!
        user2 = user_list[1]
        
        # User 2 needs to be initialized
        init_user(self.client, user2)

        sample_data2 = get_sample(self.client, user2, zipf_s=100000)
        
        assert sample_data2["task_role"] == "question_asker"  # It is still the case that this is an empty new tree
        assert sample_data2["ambiguous_question"] == conversation_roots[1].ambiguous_question  # This is the highest priority root that is not locked
        #### Back to user 1 for returning the response ####
        # And finally we simulate a response
        response_data = QuestionAskerResponseData(
            response_type="question_asker",
            previous_answer_meaningful_score=5,
            current_guess="I don't know",
            confidence_score=5,
            next_question="Are you asking about the things on his face?"
        )

        response_payload = TaskResponseRequest(
            login_id=user1.login_id,
            password=user1.password,
            sample_id=sample_data1["sample_id"],
            response_data=response_data
        ).model_dump()

        # First, let's cause some errors
        # Non-existent login_id and password
        incorrect_payload = response_payload.copy()
        incorrect_payload["login_id"] = "not_a_user"
        incorrect_payload["password"] = "not_a_password"
        resp_err = self.client.post("/api/v1/task/response", json=incorrect_payload)
        assert resp_err.status_code == 401

        # Existing user, but incorrect
        incorrect_payload2 = response_payload.copy()
        incorrect_payload2["login_id"] = user2.login_id
        incorrect_payload2["password"] = user2.password
        resp_err2 = self.client.post("/api/v1/task/response", json=incorrect_payload2)
        assert resp_err2.status_code == 401

        # Wrong sent sample id
        incorrect_payload3 = response_payload.copy()
        incorrect_payload3["sample_id"] = "not_a_sample_id"
        resp_err3 = self.client.post("/api/v1/task/response", json=incorrect_payload3)
        assert resp_err3.status_code == 400

        # Now correct response
        return_response(self.client, user1, sample_data1["sample_id"], response_data)

        # If we try to use this return again it should fail
        resp_already = self.client.post("/api/v1/task/response", json=response_payload)
        assert resp_already.status_code == 400

        # Add response for user2
        return_response(self.client, user2, sample_data2["sample_id"], response_data)

        # Now a new user should be able to get a sample from this root
        #### User 3 test ####
        user3 = user_list[2]

        init_user(self.client, user3)
        sample_data3 = get_sample(self.client, user3, zipf_s=100000)

        # The root should be the same root as from sample 1
        assert sample_data3["ambiguous_question"] == conversation_roots[0].ambiguous_question  # This is the highest priority root

        # Once we get this second response in, it will change to a response with some history
        toxic_response_data = QuestionAskerResponseData(
            response_type="question_asker",
            previous_answer_meaningful_score=5,
            current_guess="Acne",
            confidence_score=5,
            next_question="Are you asking about what is on his face?"
        )

        return_response(self.client, user3, sample_data3["sample_id"], toxic_response_data)

    def test_all_users_flow(self, session: Session, user_list: list[User], conversation_roots: list[ConversationRoot]):
        for i, user in enumerate(user_list):
            asker_response_data = QuestionAskerResponseData(
                response_type="question_asker",
                previous_answer_meaningful_score=5,
                current_guess=f"Guess from user index {i}",
                confidence_score=5,
                next_question=f"Next question from user index {i}?"
            )
            answerer_response_data = QuestionAnswererResponseData(
                response_type="question_answerer",
                previous_question_relevant_score=5,
                previous_question_informative_score=5,
                answer=f"Answer from user index {i}."
            )
            
            sample_data = run_user_flow(
                self.client, 
                user, 
                asker_response_data, 
                answerer_response_data,
                zipf_s=1.2
            )
            assert sample_data is not None

    def test_delayed_responses_flow(self, session: Session, user_list: list[User], conversation_roots: list[ConversationRoot]):
        random.seed(42)
        
        def process_response(active):
            user_idx = active["index"]
            asker_response_data = QuestionAskerResponseData(
                response_type="question_asker",
                previous_answer_meaningful_score=5,
                current_guess=f"Guess from user index {user_idx}",
                confidence_score=5,
                next_question=f"Next question from user index {user_idx}?"
            )
            answerer_response_data = QuestionAnswererResponseData(
                response_type="question_answerer",
                previous_question_relevant_score=5,
                previous_question_informative_score=5,
                answer=f"Answer from user index {user_idx}."
            )
            
            if active["sample_data"]["task_role"] == "question_asker":
                response_data = asker_response_data
            else:
                response_data = answerer_response_data
                
            return_response(self.client, active["user"], active["sample_data"]["sample_id"], response_data)

        for user in user_list:
            init_user(self.client, user)

        active_samples = []
        busy_users = set()
        
        while True:
            added_any = False
            for i, user in enumerate(user_list):
                if i in busy_users:
                    continue
                    
                sample_data = get_sample(self.client, user, zipf_s=1.2)
                if sample_data is not None:
                    added_any = True
                    delay = random.randint(0, 5)
                    active_samples.append({
                        "user": user,
                        "sample_data": sample_data,
                        "delay": delay,
                        "index": i
                    })
                    busy_users.add(i)
            
            remaining_samples = []
            for active in active_samples:
                if active["delay"] <= 0:
                    process_response(active)
                    busy_users.remove(active["index"])
                else:
                    active["delay"] -= 1
                    remaining_samples.append(active)
            active_samples = remaining_samples
            
            if not added_any and not active_samples:
                break
        
        responses = session.exec(select(SampleResponse)).all()
        seen = set()
        for response in responses:
            key = (response.root_id, response.node_code)
            assert key not in seen, f"Duplicate node code {response.node_code} in tree {response.root_id}"
            seen.add(key)


