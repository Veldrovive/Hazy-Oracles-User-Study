import os
import json
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Union
from contextlib import asynccontextmanager
from tqdm import tqdm

from hazy_oracles_user_study.definitions import *
from hazy_oracles_user_study.database import DatabaseManager
from hazy_oracles_user_study.database import User
from hazy_oracles_user_study.database import (
    SentSample, SampleResponse, ConversationRoot, ModerationEvent
)
from sqlmodel import Session, select

from hazy_oracles_user_study.server_models import (
    UserCreateRequest,
    UserCreateResponse,
    UserCreateData,
    UserSummaryRequest,
    UserSummaryResponse,
    UserSummaryData,
    UserStatusUpdateRequest,
    SuccessResponse,
    TaskSampleRequest,
    TaskSampleResponseSuccess,
    TaskSampleResponseNoSample,
    TaskResponseRequest,
    TaskResponseSuccess,
    ErrorResponse
)
from hazy_oracles_user_study.utils import generate_uuid
from hazy_oracles_user_study.user_utils import add_user
from hazy_oracles_user_study.sample_utils import (
    select_sample_for_participant,
    add_sent_sample,
    add_lock,
    add_root,
    process_returned_sample,
    check_participant_criteria,
    UserNotFoundError,
    WrongUserError,
    UserExcludedError,
    NoSentSampleError,
    SampleAlreadyReturnedError
)

db_manager = DatabaseManager(DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database and create tables if they don't exist
    db_manager.create_db_and_tables()
    
    
    with Session(db_manager.engine) as session:
        print(f"Total root dirs: {len(list(ROOTS_PATH.iterdir()))}")
        progress = tqdm(ROOTS_PATH.iterdir(), desc="Loading conversation roots")
        for roots_dir in progress:
            if not roots_dir.is_dir():
                continue
            
            roots_file = roots_dir / "roots.json"
            if not roots_file.exists():
                continue

            roots_data = json.load(roots_file.open("r"))
            for root_data in roots_data["roots"]:
                root = ConversationRoot.model_validate(root_data)
                
                # Check if root already exists
                existing_root = session.get(ConversationRoot, root.root_id)
                if existing_root:
                    continue
                    
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
    yield

app = FastAPI(
    title="Hazy Oracles User Study API",
    description="API for the Hazy Oracles user study.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post(
    "/api/v1/user/create",
    response_model=UserCreateResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key. Did not create user."},
        409: {"model": ErrorResponse, "description": "User already exists."}
    }
)
async def create_user(request: UserCreateRequest, session: Session = Depends(db_manager.get_session)):
    """
    Creates a new user with a login id, password, and internal unique id which is never served.
    """
    # Check if API key passes
    rec_api_key = request.api_key
    if API_KEY != rec_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid API key. Did not create user.").model_dump()
        )

    # Generate login id, password, and unique id
    unique_id = generate_uuid(32)
    login_id = request.login_id if request.login_id else generate_uuid(16)
    password = request.password if request.password else generate_uuid(16)

    new_user = add_user(session, unique_id, login_id, password)
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(status="error", message="User already exists.").model_dump()
        )
    
    return UserCreateResponse(
        status="success",
        data=UserCreateData(
            login_id=new_user.login_id,
            password=new_user.password
        )
    )
    

@app.post(
    "/api/v1/user/summary",
    response_model=UserSummaryResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def get_user_summary(request: UserSummaryRequest, session: Session = Depends(db_manager.get_session)):
    """
    Used to get informaton about the logged in user.
    """
    # Find a user with the given login id and password
    criteria = check_participant_criteria(session, user_login_id=request.login_id, user_password=request.password)

    # Check if user exists
    if criteria.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    user = criteria.user

    # Get max responses for the user's current phase
    max_responses_allowed = criteria.max_responses_for_this_phase

    # Return user summary
    return UserSummaryResponse(
        status="success",
        data=UserSummaryData(
            current_phase=criteria.phase,
            responses_completed=user.num_responses_given,
            max_responses_allowed=max_responses_allowed,
            is_active=not criteria.is_excluded,

            has_logged_in=user.has_logged_in,
            has_consented=user.has_consented,
            has_read_asker_instructions=user.has_read_asker_instructions,
            has_read_answerer_instructions=user.has_read_answerer_instructions,
        )
    )

@app.post(
    "/api/v1/user/consent",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def update_user_consent(request: UserStatusUpdateRequest, session: Session = Depends(db_manager.get_session)):
    """
    Updates the has_consented flag to True for the logged in user.
    """
    stmt = select(User).where(User.login_id == request.login_id, User.password == request.password)
    user = session.exec(stmt).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    
    user.has_consented = True
    session.add(user)
    session.commit()
    
    return SuccessResponse(message="User consent updated successfully.")

@app.post(
    "/api/v1/user/read_asker_instructions",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def update_read_asker_instructions(request: UserStatusUpdateRequest, session: Session = Depends(db_manager.get_session)):
    """
    Updates the has_read_asker_instructions flag to True for the logged in user.
    """
    stmt = select(User).where(User.login_id == request.login_id, User.password == request.password)
    user = session.exec(stmt).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    
    user.has_read_asker_instructions = True
    session.add(user)
    session.commit()
    
    return SuccessResponse(message="User asker instructions status updated successfully.")

@app.post(
    "/api/v1/user/read_answerer_instructions",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def update_read_answerer_instructions(request: UserStatusUpdateRequest, session: Session = Depends(db_manager.get_session)):
    """
    Updates the has_read_answerer_instructions flag to True for the logged in user.
    """
    stmt = select(User).where(User.login_id == request.login_id, User.password == request.password)
    user = session.exec(stmt).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    
    user.has_read_answerer_instructions = True
    session.add(user)
    session.commit()
    
    return SuccessResponse(message="User answerer instructions status updated successfully.")

@app.get(
    "/api/v1/user/login",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def user_login(login_id: str, password: str, session: Session = Depends(db_manager.get_session)):
    """
    Verifies the user exists and updates has_logged_in to True.
    Uses GET with query parameters.
    """
    criteria = check_participant_criteria(session, user_login_id=login_id, user_password=password)
    user = criteria.user

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    
    user.has_logged_in = True
    session.add(user)
    session.commit()
    
    return SuccessResponse(message="User logged in successfully.")

@app.post(
    "/api/v1/task/sample",
    response_model=Union[TaskSampleResponseSuccess, TaskSampleResponseNoSample],
    responses={
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def get_task_sample(request: TaskSampleRequest, session: Session = Depends(db_manager.get_session)):
    """
    Retrieves a sample for the user to work on based on their assigned role.
    """
    # 1. authenticate user
    stmt = select(User).where(User.login_id == request.login_id, User.password == request.password)
    user = session.exec(stmt).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message="Invalid login or password.").model_dump()
        )
    
    # 2. get sample
    sample_return = select_sample_for_participant(
        db=session,
        node_code_expansion_order=EXPANSION_ORDER_BASE64,
        user_unique_id=user.unique_id,
        zipf_s=request.zipf_s
    )
    
    if sample_return is None:
        return TaskSampleResponseNoSample(
            status="no_sample",
            reason="no_samples_available",
            message="No samples available at this time."
        )
        
    sample, node_code, conversation_root, parent_sample = sample_return
    
    # 3. Add as sent sample
    add_sent_sample(db=session, sample_data=sample_return, unique_user_id=user.unique_id)
    
    # 4. Put a lock on the tree
    add_lock(db=session, root_id=conversation_root.root_id, user_unique_id=user.unique_id, timeout_minutes=LOCK_TIMEOUT_MINUTES)
    
    return TaskSampleResponseSuccess(
        status="success",
        data=sample
    )

@app.post(
    "/api/v1/task/response",
    response_model=TaskResponseSuccess,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid sample ID or response already submitted."},
        401: {"model": ErrorResponse, "description": "Inactive login or invalid credentials."}
    }
)
async def submit_task_response(request: TaskResponseRequest, session: Session = Depends(db_manager.get_session)):
    """
    Submit a response for a given task sample.
    """
    try:
        process_returned_sample(
            db=session,
            response=request,
            selected_expansion_order=EXPANSION_ORDER_BASE64
        )
        return TaskResponseSuccess(
            status="success",
            message="Response submitted successfully."
        )
    except (UserNotFoundError, WrongUserError, UserExcludedError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(status="error", message=str(e)).model_dump()
        )
    except (NoSentSampleError, SampleAlreadyReturnedError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(status="error", message=str(e)).model_dump()
        )

@app.get(
    "/api/v1/images",
    response_class=FileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Image not found."}
    }
)
async def get_image(id: str, session: Session = Depends(db_manager.get_session)):
    """
    Serves the multimodal image associated with a given conversation root ID.
    """
    root = session.get(ConversationRoot, id)
    if not root:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(status="error", message="Conversation root not found.").model_dump()
        )
    
    file_path = root.multimodal_file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(status="error", message="Image file not found.").model_dump()
        )
    
    return FileResponse(file_path)

# --- SPA Production Serving ---

FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.isdir(FRONTEND_DIST):
    # Mount the /assets directory directly
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    # Catch-all route for SPA routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 1. If it's a direct file request (like favicon.ico, manifest.json in the dist root)
        requested_file = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(requested_file):
            return FileResponse(requested_file)
        
        # 2. Otherwise, fall back to index.html to allow React Router to handle the route
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
