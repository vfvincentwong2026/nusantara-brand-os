"""合规引擎 v1：BPOM / Halal / SNI 三证状态机 + 到期预警。"""
from dataclasses import dataclass
from datetime import date

CERT_TYPES = ("BPOM", "HALAL", "SNI")

# 状态：pending 申请中 / valid 有效 / expiring 临期 / expired 已过期 / withdrawn 已撤证
TRANSITIONS = {
    "pending": {"valid", "withdrawn"},
    "valid": {"expiring", "withdrawn"},
    "expiring": {"valid", "expired", "withdrawn"},
    "expired": {"valid", "withdrawn"},
    "withdrawn": set(),
}


@dataclass
class Certification:
    cert_type: str            # BPOM / HALAL / SNI
    cert_no: str              # 证书/注册号
    holder: str               # 持证公司
    sku_id: str = ""
    issue_date: str = ""      # YYYY-MM-DD
    expiry_date: str = ""     # YYYY-MM-DD，空 = 长期
    status: str = "pending"

    def __post_init__(self):
        if self.cert_type not in CERT_TYPES:
            raise ValueError(f"未知证书类型: {self.cert_type}")


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def derive_status(cert: Certification, today: date, warn_days: int = 90) -> str:
    """按到期日推导状态；状态优先级：withdrawn > expired > expiring > valid。"""
    if cert.status == "withdrawn":
        return "withdrawn"
    if not cert.expiry_date:
        return "valid"
    expiry = _parse(cert.expiry_date)
    if expiry < today:
        return "expired"
    if (expiry - today).days <= warn_days:
        return "expiring"
    return "valid"


class ComplianceEngine:
    def __init__(self, warn_days: int = 90):
        self.warn_days = warn_days
        self.certs: list[Certification] = []

    def add(self, cert: Certification) -> Certification:
        self.certs.append(cert)
        return cert

    def transition(self, cert: Certification, to_status: str, today: date | None = None) -> None:
        """状态机迁移：仅允许 TRANSITIONS 定义的边。to_status=expiring/expired 时按日期自动推导校验。"""
        if to_status not in TRANSITIONS:
            raise ValueError(f"未知状态: {to_status}")
        current = derive_status(cert, today or date.today(), self.warn_days)
        if to_status == current:
            cert.status = to_status
            return
        if to_status not in TRANSITIONS.get(current, set()):
            raise ValueError(f"非法迁移: {current} -> {to_status}")
        cert.status = to_status

    def warnings(self, today: date | None = None) -> list[Certification]:
        """到期预警清单：expiring + expired，按到期日升序。"""
        today = today or date.today()
        out = [c for c in self.certs if derive_status(c, today, self.warn_days) in ("expiring", "expired")]
        return sorted(out, key=lambda c: c.expiry_date)

    def by_sku(self, sku_id: str) -> list[Certification]:
        return [c for c in self.certs if c.sku_id == sku_id]
