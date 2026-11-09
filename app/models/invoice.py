from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str = ""
    item_code: str = ""
    unit: str = ""
    quantity: Decimal | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)


class Invoice(BaseModel):
    document_date: date | None = None
    number: str = ""
    incoming_number: str = ""
    incoming_date: date | None = None
    supplier: str = ""
    source_supplier: str = ""
    supplier_inn: str = ""
    recipient: str = ""
    contract: str = ""
    currency: str = "UZS"
    warehouse: str = ""
    vat: str = "Без НДС"
    responsible: str = ""
    exchange: str = ""
    power_of_attorney: str = ""
    customs: str = ""
    contract_ta: str = ""
    security_approved: str = ""
    last_modified: str = ""
    comment: str = ""
    total: Decimal | None = Field(default=None, ge=0)
    items: list[Item] = Field(default_factory=list, max_length=200)
    warnings: list[str] = Field(default_factory=list)
