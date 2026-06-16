from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..utils.dependencies import get_current_user
from ..models.user import User
from ..models.query import QueryHistory
from ..schemas.query import QueryRequest, QueryResponse, HistoryItem
from ..services.rag_service import rag_service


router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=QueryResponse)
def ask_question(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        answer, sources = rag_service.ask(request.query)
        history_entry = QueryHistory(
            user_id=current_user.id,
            query=request.query,
            answer=answer,
            sources=[{"text": s["text"], "metadata": s["metadata"]} for s in sources]
        )
        db.add(history_entry)
        db.commit()
        
        return QueryResponse(
            answer=answer,
            sources=[{"text": s["text"], "metadata": s["metadata"]} for s in sources]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(QueryHistory).filter(
        QueryHistory.user_id == current_user.id
    ).order_by(QueryHistory.created_at.desc()).limit(20).all()
