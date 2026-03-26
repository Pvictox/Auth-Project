from fastapi import APIRouter, HTTPException, Path, status

router = APIRouter(
    prefix="/test",
    tags=["test"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{test_id}", tags=["test"], status_code=status.HTTP_200_OK)
async def read_test(
    test_id: int = Path(..., description="The ID of the test to retrieve"),
):
    if test_id < 10:
        raise HTTPException(
            status_code=400, detail="test_id must be greater than 10"
        )
    response = {"test_id": test_id, "message": "This is a test endpoint"}
    return response
