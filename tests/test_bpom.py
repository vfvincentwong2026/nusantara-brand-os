from nbo.bpom import bpom_to_certification

RECORD = {
    "PRODUCT_ID": "EREG300449202500020",
    "PRODUCT_REGISTER": "MD 272831023097",
    "PRODUCT_NAME": "Keripik Kentang Rasa Sapi Panggang",
    "PRODUCT_BRANDS": "Chitato",
    "STATUS": "Berlaku",
    "REGISTRAR": "PT INDOFOOD FORTUNA MAKMUR",
    "REGISTRAR_NPWP": "013463476057000",
    "MANUFACTURER_NAME": "PT INDOFOOD FORTUNA MAKMUR",
    "PRODUCT_DATE": "2025-07-14",
    "PRODUCT_EXPIRED": "2026-08-15",
}


def test_bpom_record_mapping():
    c = bpom_to_certification(RECORD)
    assert c["cert_type"] == "BPOM"
    assert c["cert_no"] == "MD 272831023097"
    assert c["holder"] == "PT INDOFOOD FORTUNA MAKMUR"
    assert c["status"] == "valid"
    assert c["expiry_date"] == "2026-08-15"
    assert c["brand"] == "Chitato"
    assert c["registrar_npwp"] == "013463476057000"


def test_bpom_withdrawn_status():
    r = dict(RECORD, STATUS="Ditarik")
    assert bpom_to_certification(r)["status"] == "withdrawn"
