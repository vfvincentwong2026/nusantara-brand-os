from datetime import date

import pytest

from nbo.compliance import Certification, ComplianceEngine, derive_status

TODAY = date(2026, 10, 19)


def _cert(expiry="2027-10-19", status="valid"):
    return Certification(cert_type="BPOM", cert_no="MD 123", holder="PT Contoh",
                         sku_id="sku1", issue_date="2026-01-01",
                         expiry_date=expiry, status=status)


def test_derive_status_valid():
    assert derive_status(_cert("2027-10-19"), TODAY) == "valid"


def test_derive_status_expiring_within_90d():
    assert derive_status(_cert("2026-12-18"), TODAY) == "expiring"


def test_derive_status_expired():
    assert derive_status(_cert("2026-01-01"), TODAY) == "expired"


def test_derive_status_withdrawn_locked():
    assert derive_status(_cert("2027-01-01", "withdrawn"), TODAY) == "withdrawn"


def test_derive_status_no_expiry_is_valid():
    assert derive_status(_cert(""), TODAY) == "valid"


def test_transition_legal_and_illegal():
    c = _cert("2027-10-19", "pending")
    eng = ComplianceEngine()
    eng.transition(c, "valid", TODAY)
    assert c.status == "valid"
    with pytest.raises(ValueError):
        eng.transition(c, "pending", TODAY)  # 不允许回退


def test_withdrawn_is_terminal():
    c = _cert("2027-10-19", "withdrawn")
    eng = ComplianceEngine()
    with pytest.raises(ValueError):
        eng.transition(c, "valid", TODAY)


def test_warnings_sorted_by_expiry():
    eng = ComplianceEngine(warn_days=90)
    late = eng.add(_cert("2027-01-05"))
    early = eng.add(_cert("2026-11-01"))
    ok = eng.add(_cert("2028-06-01"))
    warns = eng.warnings(TODAY)
    assert [w.expiry_date for w in warns] == ["2026-11-01", "2027-01-05"]
    assert all(w.cert_no != ok.cert_no or w.expiry_date != ok.expiry_date for w in warns)


def test_reject_unknown_cert_type():
    with pytest.raises(ValueError):
        Certification(cert_type="ISO", cert_no="x", holder="y")
