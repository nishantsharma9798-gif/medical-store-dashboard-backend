from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic.alias_generators import to_camel
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    client_id: UUID | None
    permissions: list[str]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class LoginResponse(BaseModel):
    access_token: str
    user: UserOut

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SignupRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    business_name: str
    admin_name: str
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    token: str
    new_password: str
