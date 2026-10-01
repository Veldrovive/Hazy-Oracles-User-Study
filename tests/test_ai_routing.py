import random
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from hazy_oracles_user_study.server import app, db_manager
from hazy_oracles_user_study.database import User, ConversationRoot, SampleResponse, TreeCollectionState
from hazy_oracles_user_study.server_models import (
    UserStatusUpdateRequest,
    QuestionAskerResponseData,
    QuestionAnswererResponseData,
    TaskSampleRequest,
    TaskResponseRequest
)
from hazy_oracles_user_study.definitions import COLLECTIONS
import hazy_oracles_user_study.server as server_module


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

class TestAIRouting:
    @pytest.fixture(autouse=True)
    def setup_client(self, session: Session):
        def get_session_override():
            return session

        app.dependency_overrides[db_manager.get_session] = get_session_override
        self.client = TestClient(app)
        yield
        app.dependency_overrides.clear()

    def test_mixed_ai_human_routing(self, session: Session, user_list: list[User], conversation_roots: list[ConversationRoot]):
        # Patch API_KEY for tests
        original_key = server_module.API_KEY
        server_module.API_KEY = "test_api_key"
        headers = {"x-api-key": "test_api_key"}

        random.seed(42)

        for user in user_list:
            init_user(self.client, user)
        
        # We simulate two AI models interacting with their respective collections
        ai_models = [
            {"ai_name": "example_asker_ai", "ai_role": "asker", "collection_id": "human-ai-asker"},
            {"ai_name": "example_answerer_ai", "ai_role": "answerer", "collection_id": "ai-answerer-human"},
        ]

        active_human_samples = []
        busy_users = set()

        def process_human_response(active):
            user_idx = active["index"]
            role = active["sample_data"]["task_role"]
            
            if role == "question_asker":
                response_data = QuestionAskerResponseData(
                    response_type="question_asker",
                    previous_answer_meaningful_score=5,
                    current_guess=f"Human guess {user_idx}",
                    confidence_score=5,
                    next_question=f"Human question {user_idx}?"
                )
            else:
                response_data = QuestionAnswererResponseData(
                    response_type="question_answerer",
                    previous_question_relevant_score=5,
                    answer=f"Human answer {user_idx}."
                )
                
            return_response(self.client, active["user"], active["sample_data"]["sample_id"], response_data)

        def poll_and_respond_ai(ai_model):
            # Poll for samples
            resp = self.client.get(
                "/api/v1/ai/task/samples",
                params={
                    "collection_id": ai_model["collection_id"],
                    "ai_name": ai_model["ai_name"],
                    "ai_role": ai_model["ai_role"]
                },
                headers=headers
            )
            assert resp.status_code == 200, resp.text
            samples = resp.json()["data"]

            submitted_any = False
            for sample in samples:
                # Ensure the AI is receiving the correct role (depth implies role)
                node_len = len(sample["node_code"])
                expected_role = "question_asker" if node_len % 2 != 0 else "question_answerer"
                assert expected_role == ("question_asker" if ai_model["ai_role"] == "asker" else "question_answerer")
                
                # Create response
                if ai_model["ai_role"] == "asker":
                    response_data = {
                        "response_type": "question_asker",
                        "previous_answer_meaningful_score": None,
                        "current_guess": "AI Guess",
                        "confidence_score": 50,
                        "next_question": "AI Question"
                    }
                else:
                    response_data = {
                        "response_type": "question_answerer",
                        "previous_question_relevant_score": None,
                        "answer": "AI Answer"
                    }

                payload = {
                    "collection_id": ai_model["collection_id"],
                    "root_id": sample["root_id"],
                    "ai_name": ai_model["ai_name"],
                    "node_code": sample["node_code"],
                    "response_data": response_data
                }
                resp_post = self.client.post("/api/v1/ai/task/response", json=payload, headers=headers)
                assert resp_post.status_code == 200, resp_post.text
                submitted_any = True
            
            return submitted_any

        max_iterations = 20000
        iteration = 0
        while True:
            iteration += 1
            if iteration > max_iterations:
                pytest.fail("Test did not converge after 5000 iterations.")

            added_any_human = False
            ai_submitted_any = False

            # Try to get samples for free human users (one per loop)
            free_users = [i for i, _ in enumerate(user_list) if i not in busy_users]
            random.shuffle(free_users)
            
            for i in free_users:
                user = user_list[i]
                sample_data = get_sample(self.client, user, zipf_s=1.2)
                if sample_data is not None:
                    added_any_human = True
                    delay = random.randint(0, 3)
                    active_human_samples.append({
                        "user": user,
                        "sample_data": sample_data,
                        "delay": delay,
                        "index": i
                    })
                    busy_users.add(i)
                    break

            # Process delayed human responses
            remaining_samples = []
            for active in active_human_samples:
                if active["delay"] <= 0:
                    process_human_response(active)
                    busy_users.remove(active["index"])
                else:
                    active["delay"] -= 1
                    remaining_samples.append(active)
            active_human_samples = remaining_samples

            # AI polling and responding
            for ai_model in ai_models:
                if poll_and_respond_ai(ai_model):
                    ai_submitted_any = True
            
            all_states = session.exec(select(TreeCollectionState)).all()
            all_completed = all(state.is_completed for state in all_states)
            
            if all_completed:
                break
                
            if not added_any_human and not active_human_samples and not ai_submitted_any:
                all_completed_check = all(state.is_completed for state in all_states)
                if not all_completed_check:
                    pass
                break

        server_module.API_KEY = original_key

        responses = session.exec(select(SampleResponse)).all()
        
        # Verify no human responses when they should be AI and vice-versa
        for response in responses:
            coll_id = response.collection_id
            coll_def = COLLECTIONS[coll_id]
            node_len = len(response.node_code)
            
            expected_role = coll_def["asker_role"] if node_len % 2 != 0 else coll_def["answerer_role"]
            
            if expected_role == "human":
                # Ensure the participant type doesn't map to any AI names
                assert response.participant_type != "example_asker_ai"
                assert response.participant_type != "example_answerer_ai"
            else:
                assert response.participant_type == expected_role
