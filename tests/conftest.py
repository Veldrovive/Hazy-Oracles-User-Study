import pytest
from sqlmodel import Session, SQLModel, create_engine
from pathlib import Path
import json

from hazy_oracles_user_study.database import (
    User, 
    ConversationRoot,
)
from hazy_oracles_user_study.user_utils import add_user
from hazy_oracles_user_study.sample_utils import add_root

TEST_USER_DEFINITIONS = [{ "unique_id": f"uuid_{i}", "login_id": f"user{i}", "password": f"pw{i}"} for i in range(64)]

ROOTS_PATH = Path(__file__).parent.parent / "data" / "conversation_roots"

@pytest.fixture(name="session", scope="class")
def session_fixture():
    db_path = Path(__file__).parent / "test.db"
    if db_path.exists():
        db_path.unlink()
    # Setup a file-based SQLite database for testing
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="class")
def user_list(session: Session):
    """
    This fixture has scope="class", meaning it will be created once
    per test class and shared across all tests that request it.
    It takes the session fixture and adds the users to the database.
    """
    users = []
    for user_definition in TEST_USER_DEFINITIONS:
        user = add_user(session, **user_definition)
        users.append(user)
    return users

@pytest.fixture(scope="class")
def conversation_roots(session: Session):
    all_roots = []
    for roots_dir in ROOTS_PATH.iterdir():
        if not roots_dir.is_dir():
            continue
        
        roots_file = roots_dir / "roots.json"
        if not roots_file.exists():
            continue

        roots_data = json.load(roots_file.open("r"))
        for root_data in roots_data["roots"]:
            root = ConversationRoot.model_validate(root_data)
            add_root(
                session,
                root_id=root.root_id,
                ambiguous_question=root.ambiguous_question,
                priority=root.priority,
                unambiguous_question=root.unambiguous_question,
                multimodal_file_path=root.multimodal_file_path,
                original_dataset=root.original_dataset,
                original_dataset_sample_id=root.original_dataset_sample_id,
            )
            all_roots.append(root)

    # Reverse sorted by priority (so highest priority is first)
    all_roots.sort(key=lambda x: x.priority, reverse=True)

    return all_roots
