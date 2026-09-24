from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field
from hazy_oracles_user_study.definitions import DEFAULT_ZIPF_S

# Base Models
class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str

# 1. /api/v1/user/create
class UserCreateRequest(BaseModel):
    api_key: str

class UserCreateData(BaseModel):
    login_id: str
    password: str

class UserCreateResponse(BaseModel):
    status: Literal["success"] = "success"
    data: UserCreateData

class UserStatusUpdateRequest(BaseModel):
    login_id: str
    password: str


# 2. /api/v1/user/summary
class UserSummaryRequest(BaseModel):
    login_id: str
    password: str

class UserSummaryData(BaseModel):
    current_phase: int
    responses_completed: int
    max_responses_allowed: int
    is_active: bool

    has_logged_in: bool
    has_consented: bool
    has_read_asker_instructions: bool
    has_read_answerer_instructions: bool

class UserSummaryResponse(BaseModel):
    status: Literal["success"] = "success"
    data: UserSummaryData


# 3. /api/v1/task/sample
class TaskSampleRequest(BaseModel):
    login_id: str
    password: str
    zipf_s: float = Field(default=DEFAULT_ZIPF_S)

class MultimodalInputImage(BaseModel):
    type: Literal["image"]
    url: str

class MultimodalInputText(BaseModel):
    type: Literal["text"]
    content: str

class DialogMessage(BaseModel):
    role: Literal["question_asker", "question_answerer"]
    text: str

class QuestionAskerSampleData(BaseModel):
    sample_id: str
    task_role: Literal["question_asker"]
    multimodal_input: Union[MultimodalInputImage, MultimodalInputText]
    ambiguous_question: str
    dialog_history: List[DialogMessage]

class QuestionAnswererSampleData(BaseModel):
    sample_id: str
    task_role: Literal["question_answerer"]
    multimodal_input: Union[MultimodalInputImage, MultimodalInputText]
    ambiguous_question: str
    intended_question: str
    dialog_history: List[DialogMessage]

class TaskSampleResponseSuccess(BaseModel):
    status: Literal["success"] = "success"
    data: Union[QuestionAskerSampleData, QuestionAnswererSampleData]

class TaskSampleResponseNoSample(BaseModel):
    status: Literal["no_sample"] = "no_sample"
    reason: str
    message: str


# 4. /api/v1/task/response
class QuestionAskerResponseData(BaseModel):
    response_type: Literal["question_asker"]
    previous_answer_meaningful_score: int
    current_guess: str
    confidence_score: int
    next_question: str

class QuestionAnswererResponseData(BaseModel):
    response_type: Literal["question_answerer"]
    previous_question_relevant_score: int
    previous_question_informative_score: int
    answer: str

class TaskResponseRequest(BaseModel):
    login_id: str
    password: str
    sample_id: str
    response_data: Union[QuestionAskerResponseData, QuestionAnswererResponseData]

class TaskResponseSuccess(BaseModel):
    status: Literal["success"] = "success"
    message: str
