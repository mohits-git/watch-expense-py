from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer


DecimalAsFloat = Annotated[Decimal, PlainSerializer(
    lambda x: float(x), return_type=float
)]
