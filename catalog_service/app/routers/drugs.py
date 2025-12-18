from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.schemas import DrugCreate, DrugResponse
from app.models import Product
from app.db import get_db
from shared.auth_utils import verify_jwt

router = APIRouter()
UPLOAD_DIR = "uploads"



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
async def create_drug(
    name: str = Form(...),
    manufacturer: str = Form(...),
    ndc: str = Form(...),
    form: str = Form(None),
    strength: str = Form(None),
    price: float = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    user=Depends(verify_jwt),
):
    # user is the decoded JWT payload
    role = user.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only can create drugs")
    
    #checking if the drug is existing 
    existing_drug = db.query(Product).filter(Product.ndc == ndc).first()
    if existing_drug:
        raise HTTPException(status_code=400, detail="Drug with this NDC already exists")

    image_url = None
    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # URL that the frontend will use (Kong will proxy /catalog/static to this)
        image_url = f"/catalog/static/{file_name}"

    item = Product(
        name=name,
        manufacturer=manufacturer,
        ndc=ndc,
        form=form,
        strength=strength,
        price=price,
        image_url=image_url,
        created_by=user.get("sub")
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item



#Update Drug
@router.put("/{drug_id}", response_model=DrugResponse)
async def update_drug(
    drug_id : int,
    name: str = Form(...),
    manufacturer: str = Form(...),
    ndc: str = Form(...),
    form: str = Form(None),
    strength: str = Form(None),
    price: float = Form(...),
    image: UploadFile = File(None),
    db: Session=Depends(get_db),
    user=Depends(verify_jwt)
):
    #to if it is admin
    role = user.get("role", "user")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only Admins can delete")
    
    # To check if the drug is present in the DB
    existing_drug = db.query(Product).filter(Product.id == drug_id).first()
    if not existing_drug:
        raise HTTPException(status_code=404, detail={"message": "Drug not found"})

    # Check if the new NDC is already taken by ANOTHER drug
    if ndc != existing_drug.ndc:
        conflict_drug = db.query(Product).filter(Product.ndc == ndc, Product.id != drug_id).first()
        if conflict_drug:
            raise HTTPException(status_code=400, detail=f"The NDC '{ndc}' is already assigned to another drug ({conflict_drug.name})")

    if image:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Optional: Delete old image if it exists
        if existing_drug.image_url:
            old_file_name = existing_drug.image_url.split("/")[-1]
            old_file_path = os.path.join(UPLOAD_DIR, old_file_name)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

        existing_drug.image_url = f"/catalog/static/{file_name}"

    #update the drug
    existing_drug.name = name
    existing_drug.manufacturer = manufacturer
    existing_drug.ndc = ndc
    existing_drug.form = form
    existing_drug.strength = strength
    existing_drug.price = price
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