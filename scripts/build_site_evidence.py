"""Validate traceable rent listings / field surveys and build the web evidence store."""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["record_type", "id", "candidate_id", "city", "area", "title", "rent_year_idr",
          "building_sqm", "observed_at", "source_url", "lon", "lat", "halal_status",
          "exhaust_status", "rider_status", "notes"]


def number(row, key, integer=False, positive=True):
    raw = (row.get(key) or "").strip()
    if not raw:
        return None
    value = int(raw) if integer else float(raw)
    if positive and value <= 0:
        raise ValueError(f"{row.get('id')}: {key} must be positive")
    return value


def validate(row):
    row = {key: (row.get(key) or "").strip() for key in FIELDS}
    if row["record_type"] not in {"listing", "survey"}:
        raise ValueError(f"{row['id']}: record_type must be listing or survey")
    if not row["id"] or not row["title"] or not row["observed_at"]:
        raise ValueError(f"{row['id']}: id/title/observed_at required")
    datetime.strptime(row["observed_at"], "%Y-%m-%d")
    if row["source_url"]:
        parsed = urlparse(row["source_url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"{row['id']}: source_url must be HTTPS")
    lon, lat = number(row, "lon", positive=False), number(row, "lat", positive=False)
    if (lon is None) != (lat is None):
        raise ValueError(f"{row['id']}: lon/lat must be supplied together")
    if lon is not None and not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError(f"{row['id']}: invalid coordinates")
    year = number(row, "rent_year_idr", integer=True)
    if row["record_type"] == "listing" and (not year or not row["source_url"]):
        raise ValueError(f"{row['id']}: public listing needs yearly rent and source URL")
    if row["record_type"] == "survey" and not row["candidate_id"]:
        raise ValueError(f"{row['id']}: survey needs candidate_id")
    return {
        **row,
        "rent_year_idr": year,
        "rent_month_idr": round(year / 12) if year else None,
        "building_sqm": number(row, "building_sqm"),
        "lon": lon,
        "lat": lat,
        "location_precision": "exact" if lon is not None else "area",
        "availability": "unverified" if row["record_type"] == "listing" else "field_recorded",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/seeds/site_evidence.csv")
    parser.add_argument("--out", default="web/map/data/site_evidence.json")
    args = parser.parse_args()
    source = ROOT / args.input
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = [validate(row) for row in csv.DictReader(handle)]
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate evidence id")
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": args.input.replace("\\", "/"),
        "boundary": "公开挂牌不等于成交价或可租状态；区域级记录不参与具体铺位硬过滤。现场记录由录入方负责。",
        "listings": sorted((r for r in rows if r["record_type"] == "listing"), key=lambda r: r["observed_at"], reverse=True),
        "surveys": sorted((r for r in rows if r["record_type"] == "survey"), key=lambda r: r["observed_at"], reverse=True),
    }
    target = ROOT / args.out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"listings": len(output["listings"]), "surveys": len(output["surveys"]), "out": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
