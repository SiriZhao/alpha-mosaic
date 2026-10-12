"""Universe discovery, explicit watchlists, and user imports."""

import csv
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from alphamosaic.providers.protocol import DataProvider


def normalize_symbols(symbols: list[str]) -> list[str]:
    normalized = list(dict.fromkeys(item.strip().upper() for item in symbols if item.strip()))
    if any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", item) for item in normalized):
        raise ValueError("invalid US ticker")
    if len(normalized) > 100:
        raise ValueError("maximum 100 symbols per research scan")
    return normalized


@dataclass(frozen=True)
class Universe:
    name: str
    source: str
    symbols: list[str]


class UniversePool(StrEnum):
    BROAD_LIQUIDITY = "BROAD_LIQUIDITY"
    SP500_CURRENT = "SP500_CURRENT"
    QUALITY_GROWTH = "QUALITY_GROWTH"
    EARNINGS_REVISION = "EARNINGS_REVISION"
    EVENT_CATALYST = "EVENT_CATALYST"
    USER_WATCHLIST = "USER_WATCHLIST"


class UniverseManager:
    def __init__(self, provider: DataProvider):
        self.provider = provider

    def discover(self, limit: int = 30) -> Universe:
        if not 1 <= limit <= 100:
            raise ValueError("universe limit must be 1..100")
        identities, source = self.provider.universe(limit)
        return Universe(
            "US broad liquid current sample", source, [item.symbol for item in identities]
        )

    def discover_pool(self, pool: UniversePool, limit: int = 30) -> Universe:
        if pool == UniversePool.BROAD_LIQUIDITY:
            return self.discover(limit)
        raise ValueError(f"{pool.value} requires a licensed or user-supplied symbol list")

    def specified(self, symbols: list[str], name: str = "User watchlist") -> Universe:
        return Universe(
            name,
            "Explicit user list; identities verified against live provider",
            normalize_symbols(symbols),
        )

    def imported(self, path: Path) -> Universe:
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames or "symbol" not in reader.fieldnames:
                    raise ValueError("CSV requires a symbol column")
                symbols = [row["symbol"] for row in reader]
        else:
            symbols = path.read_text(encoding="utf-8-sig").splitlines()
        return self.specified(symbols, "Imported user universe")

    def index_members(self, symbols: list[str], source_url: str) -> Universe:
        if not source_url.startswith("https://"):
            raise ValueError("index membership requires a supplied licensed source URL")
        return Universe(
            "User-supplied current index members",
            source_url + "; not historical membership",
            normalize_symbols(symbols),
        )
