from decimal import Decimal
import enum
from pydantic import BaseModel, ConfigDict


class EventType(enum.Enum):
    USER_WELCOME = "USER_WELCOME"
    EXPENSE_APPROVED = "EXPENSE_APPROVED"
    EXPENSE_REJECTED = "EXPENSE_REJECTED"
    ADVANCE_REJECTED = "ADVANCE_REJECTED"
    ADVANCE_APPROVED = "ADVANCE_APPROVED"


class Notification(BaseModel):
    class User(BaseModel):
        name: str
        email: str

    class Expense(BaseModel):
        expense_id: str
        purpose: str
        amount: Decimal

    class Advance(BaseModel):
        advance_id: str
        purpose: str
        amount: Decimal

    event_type: EventType
    user: User
    expense: Expense | None
    advance: Advance | None

    model_config = ConfigDict(
        use_enum_values=True,
    )
