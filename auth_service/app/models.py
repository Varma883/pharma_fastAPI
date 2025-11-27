from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(UserLogin):
    full_name: str | None = None
    role: str | None = "user"  # "user" or "admin"


class User(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    is_active: bool = True
    role: str = "user"


class UserInDB(User):
    hashed_password: str



# Temporary fake DB (replace later with Postgres)
# Example Argon2 hash for password "tani123" (you can regenerate if you want):
fake_db: dict[str, UserInDB] = {
    "tani": UserInDB(
        id=1,
        username="tani",
        full_name="Tani Varma",
        is_active=True,
        role="admin",
        hashed_password=(
            # your existing Argon2 hash for "tani123"
            "$argon2id$v=19$m=65536,t=3,p=4$MSakdO6d8/5/z1nLGUMoxQ"
            "$TbiqUK1Vrb7qILXWRQns2J1sg8xNEdzeZPTYhCFWGps"
        ),
    )
}