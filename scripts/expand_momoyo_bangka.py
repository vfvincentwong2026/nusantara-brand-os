"""Momoyo 邦加岛及巴厘东部收尾补点。"""
import expand_momoyo_regencies as base

base.AREAS = [
    ("pangkalpinang", "槟港", "Pangkalpinang", -2.1290, 106.1130, "邦加岛", 1.10),
    ("sungailiat", "双溪利亚", "Sungailiat Bangka", -1.8500, 106.1160, "邦加岛", 1.10),
    ("toboali", "托博阿利", "Toboali Bangka", -2.9830, 106.4500, "邦加岛", 1.10),
    ("koba", "科巴", "Koba Bangka", -2.5000, 106.4000, "邦加岛", 1.10),
    ("mentok", "门托克", "Mentok Bangka", -1.9830, 105.1830, "邦加岛", 1.10),
    ("negara", "内加拉", "Negara Bali", -8.3560, 114.6160, "巴厘", 1.08),
    ("amlapura", "安拉普拉", "Amlapura Bali", -8.4500, 115.6160, "巴厘", 1.08),
    ("bangli", "邦利", "Bangli Bali", -8.4540, 115.3540, "巴厘", 1.06),
    ("klungkung", "克隆孔", "Klungkung Bali", -8.5330, 115.4000, "巴厘", 1.06),
]

if __name__ == "__main__":
    base.main()
