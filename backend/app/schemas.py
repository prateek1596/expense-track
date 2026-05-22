from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str


class LinkBankRequest(BaseModel):
    bank_name: str
    masked_account: str


class BankAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_name: str
    masked_account: str
    aa_consent_id: str
    linked_at: datetime


class LinkBankResponse(BaseModel):
    account: BankAccountResponse
    consent_url: str


class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    tx_type: str
    merchant: str
    description: str
    timestamp: datetime
    raw_data: dict = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    amount: float
    tx_type: str
    merchant: str
    category: str
    description: str
    timestamp: datetime


class PaginatedTransactions(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    per_page: int


class MonthlyCategoryReportItem(BaseModel):
    category: str
    total: float


class MonthlyReportResponse(BaseModel):
    month: int
    year: int
    total_spend: float
    by_category: list[MonthlyCategoryReportItem]


class RecurringMerchantItem(BaseModel):
    merchant: str
    category: str
    count: int
    total: float
    average: float
    first_seen: datetime
    last_seen: datetime


class RecurringSpendingResponse(BaseModel):
    month: int
    year: int
    lookback_months: int
    recurring_merchants: list[RecurringMerchantItem]


class BudgetCreateRequest(BaseModel):
    category: str
    monthly_limit: float
    month: int
    year: int


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    monthly_limit: float
    month: int
    year: int
