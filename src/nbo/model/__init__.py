from dataclasses import dataclass
from typing import List, Optional

@dataclass
class StoreProfile:
    store_size_sqm: float
    island_region: str
    target_sku_count: int
    fresh_ratio: float
    qris_enabled: bool = False
    mudik_offset: float = 0.0

@dataclass
class SKU:
    id: str
    name: str
    category: str
    barcode: str
    internal_code: str
    halal_certified: bool = False
    bpom_no: Optional[str] = None
    shelf_life_days: int = 365
    fresh_ratio: float = 0.0
    cost_idr: Optional[float] = None      # 采购成本（IDR）
    sell_price_idr: Optional[float] = None  # 售价（IDR，含 PPN 11% 口径见 docs/compliance.md）
    ppn_rate: float = 0.11                 # PPN 增值税率

@dataclass
class Batch:
    id: str
    sku_id: str
    store_id: str
    qty: int
    receive_date: str
    expiry_date: str
    location: Optional[str] = None
