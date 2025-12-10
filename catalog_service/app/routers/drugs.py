from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import DrugCreate, DrugResponse
from app.models import Product
from app.db import get_db
from shared.auth_utils import verify_jwt

router = APIRouter()



#get all drugs
@router.get("", response_model=list[DrugResponse])
@router.get("/", response_model=list[DrugResponse])
def list_drugs(
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),
):
    return db.query(Product).all()


#get drug by id
@router.get("/{drug_id}", response_model=DrugResponse)
def get_drug_by_id(
    drug_id: int,
    db: Session=Depends(get_db),
    user=Depends(verify_jwt),
):
    
    drug= db.query(Product).filter(Product.id== drug_id).first()

    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug

#create drug
@router.post("", response_model=DrugResponse)
@router.post("/", response_model=DrugResponse)
def create_drug(
    payload: DrugCreate,
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),
):
    # user is the decoded JWT payload
    role = user.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only can create drugs")
    
    existing_drug = db.query(Product).filter(Product.ndc == payload.ndc).first()
    if existing_drug:
        raise HTTPException(status_code=400, detail="Drug with this NDC already exists")

    item = Product(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item