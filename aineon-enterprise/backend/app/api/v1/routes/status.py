from fastapi import APIRouter, Depends
from .... import schemas
from .auth import get_current_user

router = APIRouter()

@router.get("/status", response_model=schemas.Status)
async def get_system_status(current_user: schemas.User = Depends(get_current_user)):
    # TODO: Replace with real data
    return {
        "status": "All systems nominal",
        "phase1_status": "Active",
        "phase2_status": "Active",
        "phase3_status": "Standby",
        "phase4_status": "Active",
        "phase5_status": "Inactive",
    }
