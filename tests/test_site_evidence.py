import csv
import json
import subprocess
from pathlib import Path

from scripts.build_site_evidence import validate

ROOT = Path(__file__).resolve().parent.parent


def test_public_rent_snapshots_are_traceable_and_area_scoped():
    data = json.loads((ROOT / "web/map/data/site_evidence.json").read_text(encoding="utf-8"))
    assert len(data["listings"]) == 5
    assert data["surveys"] == []
    for row in data["listings"]:
        assert row["source_url"].startswith("https://")
        assert row["rent_year_idr"] > 0
        assert row["rent_month_idr"] == round(row["rent_year_idr"] / 12)
        assert row["observed_at"]
        assert row["availability"] == "unverified"
        assert row["location_precision"] == "area" and row["lon"] is None and row["lat"] is None
    assert "区域级记录不参与" in data["boundary"]


def test_evidence_validation_requires_coordinates_pair_and_candidate_for_survey():
    base = {"record_type": "survey", "id": "S-1", "candidate_id": "ST-04", "title": "现场核验", "observed_at": "2026-11-14"}
    row = validate(base)
    assert row["record_type"] == "survey" and row["availability"] == "field_recorded"
    exact = validate({**base, "lon": "106.8", "lat": "-6.2"})
    assert exact["location_precision"] == "exact" and exact["lat"] == -6.2
    try:
        validate({**base, "lon": "106.8"})
        assert False, "unpaired coordinate must fail"
    except ValueError:
        pass
    try:
        validate({**base, "candidate_id": ""})
        assert False, "survey without candidate must fail"
    except ValueError:
        pass


def test_evidence_source_csv_matches_output():
    with (ROOT / "data/seeds/site_evidence.csv").open(encoding="utf-8-sig", newline="") as handle:
        source = list(csv.DictReader(handle))
    data = json.loads((ROOT / "web/map/data/site_evidence.json").read_text(encoding="utf-8"))
    assert len(source) == len(data["listings"]) + len(data["surveys"])


def test_evidence_workflow_is_wired_and_deployed():
    html = (ROOT / "web/map/index.html").read_text(encoding="utf-8")
    evidence = (ROOT / "web/map/evidence.js").read_text(encoding="utf-8")
    spatial = (ROOT / "web/map/spatial.js").read_text(encoding="utf-8")
    deploy = (ROOT / "scripts/deploy.py").read_text(encoding="utf-8")
    for element in ("importEvidence", "downloadTemplate", "exportEvidence", "saveSurvey", "surveyHalal", "surveyExhaust", "surveyRider"):
        assert f'id="{element}"' in html
    assert './evidence.js' in html and "site_evidence.json" in evidence
    assert "localStorage" in evidence and "parseCSV" in evidence and "location_precision" in evidence
    assert "NBOEvidence.rentFor" in spatial and "NBOEvidence.universities" in spatial
    assert "refreshLivePOIs" in spatial and "evidence-points" in spatial
    assert '"evidence.js"' in deploy and '"site_evidence.json"' in deploy
    assert "scripts/build_site_evidence.py" in deploy


def test_evidence_completeness_and_confidence_demotion_behavior():
    script = r"""
const elements = {};
global.window = {};
global.localStorage = {getItem: () => null};
global.document = {getElementById: id => elements[id] ||= {value: '', innerHTML: '', textContent: ''}};
const candidates = ['NONE', 'RENT', 'SURVEY', 'FULL'].map(id => ({id, name: id, city: '雅加达', suitability: 80}));
const listing = {record_type: 'listing', id: 'L1', candidate_id: 'RENT', city: '雅加达', title: '精确挂牌', observed_at: '2026-11-14', location_precision: 'exact', rent_month_idr: 8000000};
const survey = {record_type: 'survey', id: 'S1', candidate_id: 'SURVEY', city: '雅加达', title: '现场', observed_at: '2026-11-14', location_precision: 'area', rent_month_idr: null};
const full = {record_type: 'survey', id: 'S2', candidate_id: 'FULL', city: '雅加达', title: '完整现场', observed_at: '2026-11-14', location_precision: 'exact', rent_month_idr: 12000000};
global.fetch = async () => ({ok: true, json: async () => ({listings: [listing], surveys: [survey, full]})});
require('./web/map/evidence.js');
(async () => {
  const api = await window.NBOEvidence.init(candidates);
  const result = candidates.map(c => ({id: c.id, quality: api.completeness(c), decision: api.decisionScore(c)}));
  console.log(JSON.stringify(result));
})().catch(error => {console.error(error); process.exit(1);});
"""
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
    result = {row["id"]: row for row in json.loads(completed.stdout)}
    assert result["NONE"]["quality"]["score"] == 0 and result["NONE"]["decision"] == 68
    assert result["RENT"]["quality"]["score"] == 70 and result["RENT"]["decision"] == 76.4
    assert result["SURVEY"]["quality"]["score"] == 30 and result["SURVEY"]["decision"] == 71.6
    assert result["FULL"]["quality"] == {
        "score": 100, "grade": "A", "factor": 1, "hasExactRent": True,
        "hasSurvey": True, "hasExactLocation": True, "linked": 1,
    }
    assert result["FULL"]["decision"] == 80
