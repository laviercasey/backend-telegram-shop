from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_shop_admin
from backend.app.crud.review import review as review_crud
from app.models.user import User
from app.schemas.review import Review, ReviewCreate, ReviewUpdate, ReviewWithUser

router = APIRouter()

@router.get("/product/{product_id}", response_model=List[ReviewWithUser])
def read_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    reviews = review_crud.get_by_product(
        db=db, product_id=product_id, skip=skip, limit=limit
    )
    return reviews

@router.post("/", response_model=Review)
def create_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if review_in.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create review for another user",
        )
    
    existing_review = review_crud.get_by_user_and_product(
        db=db, user_id=current_user.id, product_id=review_in.product_id
    )
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product",
        )
    
    review = review_crud.create(db=db, obj_in=review_in)
    return review

@router.put("/{review_id}", response_model=Review)
def update_review(
    review_id: int,
    review_in: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    review = review_crud.get(db=db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update another user's review",
        )
    
    review = review_crud.update(db=db, db_obj=review, obj_in=review_in)
    return review

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    review = review_crud.get(db=db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another user's review",
        )
    
    review_crud.remove(db=db, id=review_id)
    return {"status": "success"}

@router.get("/product/{product_id}/rating")
def get_product_rating(
    product_id: int,
    db: Session = Depends(get_db),
) -> Any:
    rating = review_crud.get_product_rating(db=db, product_id=product_id)
    return rating
