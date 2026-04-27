from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


class LinkBankRequest(BaseModel):
    bank_name: str
    masked_account: str


class BankAccountResponse(BaseModel):
    id: int
    bank_name: str
    masked_account: str
    aa_consent_id: str
    linked_at: datetime

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    tx_type: str
    merchant: str
    description: str
    timestamp: datetime
    raw_data: dict = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    tx_type: str
    merchant: str
    category: str
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MonthlyCategoryReportItem(BaseModel):
    category: str
    total: float


class MonthlyReportResponse(BaseModel):
    month: int
    year: int
    total_spend: float
    by_category: list[MonthlyCategoryReportItem]
