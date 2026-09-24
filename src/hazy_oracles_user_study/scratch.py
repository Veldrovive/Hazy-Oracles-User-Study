from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from enum import Enum

class MODERATION_ACTION(str, Enum):
    CLEARED = "cleared"

class SampleResponse(SQLModel, table=True):
    sample_id: str = Field(primary_key=True)
    node_code: str
    parent_sample_id: Optional[str] = None
    root_id: str
    moderation_status: MODERATION_ACTION

engine = create_engine("sqlite://")
SQLModel.metadata.create_all(engine)

with Session(engine) as db:
    s1 = SampleResponse(sample_id="1", node_code="A", root_id="R", moderation_status=MODERATION_ACTION.CLEARED)
    s2 = SampleResponse(sample_id="2", node_code="AB", parent_sample_id="1", root_id="R", moderation_status=MODERATION_ACTION.CLEARED)
    s3 = SampleResponse(sample_id="3", node_code="ABC", parent_sample_id="2", root_id="R", moderation_status=MODERATION_ACTION.CLEARED)
    db.add(s1)
    db.add(s2)
    db.add(s3)
    db.commit()

    # We want ancestors of "ABC", starting from "AB"
    parent_node_code = "ABC"[:-1]
    
    base_query = select(SampleResponse).where(
        SampleResponse.root_id == "R",
        SampleResponse.node_code == parent_node_code,
        SampleResponse.moderation_status == MODERATION_ACTION.CLEARED
    ).cte(name="ancestor_samples", recursive=True)

    recursive_query = select(SampleResponse).join(
        base_query, SampleResponse.sample_id == base_query.c.parent_sample_id
    )

    ancestors_cte = base_query.union_all(recursive_query)

    from sqlalchemy.orm import aliased
    ancestor_alias = aliased(SampleResponse, ancestors_cte)
    
    statement = select(ancestor_alias)
    
    results = db.exec(statement).all()
    print("Results:", [r.node_code for r in results])
