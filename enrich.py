#!/usr/bin/env python3
"""Enrich an address CSV using APIVex. Python 3.10+, standard library only."""
import argparse
import csv
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL = "https://api.apivex.com/zillow/search_address"
FIELDS = ["input_address", "status", "http_status", "match_review", "zpid",
          "returned_address", "price", "currency", "bedrooms", "bathrooms",
          "living_area", "home_type", "home_status", "zestimate", "rent_zestimate"]


def normalize(address, code, body):
    row = dict.fromkeys(FIELDS, "")
    row.update(input_address=address, http_status=code, status="unexpected_response")
    if code < 200 or code >= 300:
        row["status"] = "http_error"
        return row
    if body is None or body == [] or body == {}:
        row["status"] = "no_result"
        return row
    if isinstance(body, list):
        row["status"] = "multiple_results_review" if len(body) > 1 else "unexpected_response"
        return row
    if not isinstance(body, dict) or not body.get("zpid") or not isinstance(body.get("address"), dict):
        return row
    a = body["address"]
    row.update(status="returned", match_review="required", zpid=body["zpid"],
               returned_address=", ".join(str(a[k]) for k in ("streetAddress", "city", "state", "zipcode") if a.get(k)))
    for output, source in {"price": "price", "currency": "currency", "bedrooms": "bedrooms",
                           "bathrooms": "bathrooms", "living_area": "livingArea", "home_type": "homeType",
                           "home_status": "homeStatus", "zestimate": "zestimate", "rent_zestimate": "rentZestimate"}.items():
        row[output] = body.get(source) if body.get(source) is not None else ""
    return row


def fetch_address(address, key):
    request = Request(URL + "?" + urlencode({"address": address}),
                      headers={"x-apivex-key": key, "Accept": "application/json"})
    for attempt in range(3):
        retry_after = None
        try:
            with urlopen(request, timeout=60) as response:
                code, raw = response.status, response.read()
        except HTTPError as exc:
            code, raw = exc.code, exc.read()
            retry_after = exc.headers.get("Retry-After")
        except (URLError, TimeoutError):
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            return {**normalize(address, 0, None), "status": "network_error"}
        if (code == 429 or 500 <= code <= 599) and attempt < 2:
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** (attempt + 1)
            time.sleep(min(delay, 60))
            continue
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return {**normalize(address, code, None), "status": "invalid_json" if 200 <= code < 300 else "http_error"}
        return normalize(address, code, body)


def csv_safe(value):
    # Prevent API/input text being treated as a formula when opened in a spreadsheet.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=10, help="Maximum input rows (default: 10)")
    parser.add_argument("--delay", type=float, default=1, help="Seconds between unique addresses (minimum: 1)")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must be different files.")
    if args.limit < 1 or args.delay < 1:
        parser.error("Limit and delay must be at least 1.")
    key = os.environ.get("APIVEX_API_KEY")
    if not key:
        parser.error("Set APIVEX_API_KEY in your environment first.")
    cache = {}
    processed = 0
    with args.input.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or "address" not in reader.fieldnames:
            parser.error("Input CSV must have an address column.")
        # Exclusive creation prevents accidentally overwriting a previous export.
        with args.output.open("x", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(destination, fieldnames=FIELDS)
            writer.writeheader()
            for item in reader:
                if processed >= args.limit:
                    break
                address = (item.get("address") or "").strip()
                if not address:
                    result = {**normalize(address, 0, None), "status": "empty_address"}
                elif address in cache:
                    result = cache[address]
                else:
                    if cache:
                        time.sleep(args.delay)
                    result = fetch_address(address, key)
                    cache[address] = result
                writer.writerow({k: csv_safe(v) for k, v in result.items()})
                destination.flush()
                processed += 1
                if result["http_status"] in (401, 403, 429):
                    print(f"Stopped after HTTP {result['http_status']}; partial output saved. Check credentials, quota or rate limits.")
                    return 1
    print(f"Saved {processed} rows. Review returned addresses and status before using the data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
