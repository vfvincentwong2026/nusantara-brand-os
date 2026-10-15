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

@dataclass
class Batch:
    id: str
    sku_id: str
    store_id: str
    qty: int
    receive_date: str
    expiry_date: str
    location: Optional[str] = None
