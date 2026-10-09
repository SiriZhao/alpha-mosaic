"""Bounded diagnostic; response excerpt only, never credentials."""

import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import httpx


def probe(url: str) -> dict[str, object]:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        return {"host": urlparse(url).hostname, "status": response.status_code, "excerpt": response.text[:500]}
    except Exception as exc:
        return {"host": urlparse(url).hostname, "status": type(exc).__name__}


if __name__ == "__main__":
    urls = [
        "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=6mo&interval=1d",
        "https://query2.finance.yahoo.com/v8/finance/chart/AAPL?range=6mo&interval=1d",
        "https://stooq.com/q/d/l/?s=aapl.us&i=d",
        "https://api.nasdaq.com/api/quote/AAPL/historical?assetclass=stocks&limit=200",
        "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
    ]
    with ThreadPoolExecutor(max_workers=5) as executor:
        print(json.dumps(list(executor.map(probe, urls)), indent=2))
