from fastapi import APIRouter

router = APIRouter()

@router.get("/users/pending")
def get_pending_users():
    # TODO: Implement logic to get pending users
    return {"message": "Get pending users endpoint not implemented yet"}
