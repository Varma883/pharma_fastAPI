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
    role = user.get("role", "user")   #dictionary.get(key, default_value_if_key_not_found)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only can create drugs")
    
    #checking if the drug is existing 
    existing_drug = db.query(Product).filter(Product.ndc == payload.ndc).first()
    if existing_drug:
        raise HTTPException(status_code=400, detail="Drug with this NDC already exists")

    item = Product(**payload.model_dump(),
    created_by=user.get("sub"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item



#Update Drug
@router.put("/{drug_id}", response_model=DrugResponse)
def update_drug(
    drug_id : int,
    payload : DrugCreate,
    db: Session=Depends(get_db),
    user=Depends(verify_jwt)
):
    #to if it is admin
    role = user.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only Admins can delete")
    
    #To check is the drug is present in the DB
    existing_drug = db.query(Product).filter(Product.id == drug_id).first()
    if not existing_drug:
        raise HTTPException(status_code=404, detail={"message": "Drug not found"})
    # #NDC cannot be updated
    # if existing_drug.ndc != payload.ndc:
    #     raise HTTPException(status_code=400, detail="NDC cannot be updated")
    #update the drug
    existing_drug.name = payload.name
    existing_drug.manufacturer = payload.manufacturer
    existing_drug.ndc = payload.ndc
    existing_drug.form = payload.form
    existing_drug.strength = payload.strength
    existing_drug.updated_by = user.get("sub")

    
    db.commit()
    db.refresh(existing_drug)
    return existing_drug


#delte drug
@router.delete("/{drug_id}")
def delete_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),
):

    role =user.get("role", "user")
    if role  != "admin":
        raise HTTPException(status_code=403, detail="Admins only can delete drugs")
    drug= db.query(Product).filter(Product.id== drug_id).first()
    
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")

    db.delete(drug)
    db.commit()
    
    return {"message": "Drug deleted successfully"}