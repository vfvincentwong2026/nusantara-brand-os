"""BPOM 公开数据客户端（cekbpom.pom.go.id，接口规格见 docs/BPOM_DATA_SOURCE.md）。

用法：
    client = BPOMClient()
    records = client.search("chitato")           # 按品牌/产品关键词检索
    certs = [bpom_to_certification(r) for r in records]

仅标准库实现；生产环境请控制频率（min_interval），结果落 D1。
"""
import json
import time
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


class BPOMClient:
    BASE = "https://cekbpom.pom.go.id"

    def __init__(self, min_interval: float = 1.0, timeout: int = 30):
        self.min_interval = min_interval
        self.timeout = timeout
        self._jar = CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._jar))
        self._last = 0.0

    def _throttle(self):
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def _get_csrf(self) -> str:
        req = urllib.request.Request(f"{self.BASE}/all-produk?query=init", headers={"User-Agent": "nbo-bpom-client/0.1"})
        self._opener.open(req, timeout=self.timeout).read()
        for c in self._jar:
            if c.name == "XSRF-TOKEN":
                return urllib.parse.unquote(c.value)
        raise RuntimeError("未获取到 XSRF-TOKEN")

    def search(self, keyword: str, max_results: int = 100) -> list[dict]:
        """DataTables 接口分页拉取；返回原始记录列表。"""
        csrf = self._get_csrf()
        out, start = [], 0
        while len(out) < max_results:
            self._throttle()
            body = urllib.parse.urlencode({
                "draw": 1, "start": start, "length": min(100, max_results - len(out)),
                "search[value]": keyword, "search[regex]": "false",
            }).encode()
            req = urllib.request.Request(
                f"{self.BASE}/produk-dt/all", data=body,
                headers={
                    "X-XSRF-TOKEN": csrf, "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{self.BASE}/all-produk?query={urllib.parse.quote(keyword)}",
                    "User-Agent": "nbo-bpom-client/0.1",
                })
            resp = json.loads(self._opener.open(req, timeout=self.timeout).read().decode())
            data = resp.get("data", [])
            if not data:
                break
            out.extend(data)
            if len(out) >= resp.get("recordsFiltered", 0):
                break
            start += len(data)
        return out[:max_results]


def bpom_to_certification(record: dict) -> dict:
    """BPOM 记录 -> 合规引擎字段映射（映射本身是纯函数，测试不触网）。"""
    return {
        "cert_type": "BPOM",
        "cert_no": record.get("PRODUCT_REGISTER", ""),
        "holder": record.get("REGISTRAR", ""),
        "issue_date": record.get("PRODUCT_DATE") or "",
        "expiry_date": record.get("PRODUCT_EXPIRED") or "",
        "status": "valid" if record.get("STATUS") == "Berlaku" else "withdrawn",
        "product_name": record.get("PRODUCT_NAME", ""),
        "brand": record.get("PRODUCT_BRANDS", ""),
        "registrar_npwp": record.get("REGISTRAR_NPWP", ""),
        "manufacturer": record.get("MANUFACTURER_NAME", ""),
        "source_id": record.get("PRODUCT_ID", ""),
    }
