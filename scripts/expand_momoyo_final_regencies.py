"""Momoyo 阶段目标收尾：巴厘、南加里曼丹、苏拉威西及苏门答腊重点城镇。"""
import expand_momoyo_regencies as base

base.AREAS = [
    ("kuta", "库塔", "Kuta Bali", -8.7180, 115.1690, "巴厘", 1.06),
    ("seminyak", "水明漾", "Seminyak Bali", -8.6910, 115.1560, "巴厘", 1.06),
    ("jimbaran", "金巴兰", "Jimbaran Bali", -8.7900, 115.1600, "巴厘", 1.06),
    ("tabanan", "塔巴南", "Tabanan Bali", -8.5400, 115.1250, "巴厘", 1.06),
    ("gianyar", "吉安雅", "Gianyar Bali", -8.5400, 115.3250, "巴厘", 1.06),
    ("kandangan", "坎丹岸", "Kandangan", -2.8000, 115.2330, "加里曼丹", 1.10),
    ("rantau", "兰陶", "Rantau Kalimantan", -2.9330, 115.1330, "加里曼丹", 1.10),
    ("kotabaru", "哥打巴鲁", "Kotabaru Kalimantan", -3.2830, 116.1500, "加里曼丹", 1.12),
    ("muara-teweh", "穆阿拉特维", "Muara Teweh", -0.9500, 114.8830, "加里曼丹", 1.12),
    ("kasongan", "卡松岸", "Kasongan", -1.8830, 113.4000, "加里曼丹", 1.10),
    ("watampone", "瓦坦波内", "Watampone", -4.5330, 120.3330, "苏拉威西", 1.12),
    ("sengkang", "盛康", "Sengkang", -4.1330, 120.0330, "苏拉威西", 1.12),
    ("polewali", "波勒瓦利", "Polewali Mandar", -3.4330, 119.3500, "苏拉威西", 1.12),
    ("tebing-tinggi", "直名丁宜", "Tebing Tinggi Sumatera", 3.3270, 99.1530, "苏门答腊", 1.08),
    ("tanjung-balai", "丹戎巴莱", "Tanjung Balai Sumatera", 2.9670, 99.8000, "苏门答腊", 1.08),
]

if __name__ == "__main__":
    base.main()
