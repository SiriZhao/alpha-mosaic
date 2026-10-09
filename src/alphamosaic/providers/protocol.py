"""External data provider boundary."""

from datetime import date
from typing import Protocol

from alphamosaic.core.contracts import DataBatch, ProviderHealth, SecurityIdentity


class DataProvider(Protocol):
    def health(self) -> ProviderHealth: ...

    def universe(self, limit: int) -> tuple[list[SecurityIdentity], str]: ...

    def history(self, symbol: str, start: date, end: date) -> DataBatch: ...
