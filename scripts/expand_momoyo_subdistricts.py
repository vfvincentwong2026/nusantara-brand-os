"""Momoyo 都市圈下一级行政区补点，复用高密度采集逻辑。"""
import expand_momoyo_dense as base

CITY = base.CITY
DISTRICTS = [
    ("jakarta", "Cakung Jakarta"), ("jakarta", "Duren Sawit Jakarta"),
    ("jakarta", "Cipayung Jakarta"), ("jakarta", "Ciracas Jakarta"),
    ("jakarta", "Cilandak Jakarta"), ("jakarta", "Jagakarsa Jakarta"),
    ("jakarta", "Pasar Minggu Jakarta"), ("jakarta", "Tebet Jakarta"),
    ("jakarta", "Cengkareng Jakarta"), ("jakarta", "Kebon Jeruk Jakarta"),
    ("jakarta", "Kalideres Jakarta"), ("jakarta", "Grogol Petamburan Jakarta"),
    ("bogor", "Parung Bogor"), ("bogor", "Gunung Putri Bogor"),
    ("bogor", "Citeureup Bogor"), ("bogor", "Ciawi Bogor"), ("bogor", "Dramaga Bogor"),
    ("depok", "Sawangan Depok"), ("depok", "Cimanggis Depok"),
    ("depok", "Limo Depok"), ("depok", "Cinere Depok"),
    ("tangerang", "Curug Tangerang"), ("tangerang", "Legok Tangerang"),
    ("tangerang", "Cisauk Tangerang"), ("tangerang", "Cipondoh Tangerang"),
    ("bekasi", "Tambun Bekasi"), ("bekasi", "Cibitung Bekasi"), ("bekasi", "Babelan Bekasi"),
    ("surabaya", "Rungkut Surabaya"), ("surabaya", "Sukolilo Surabaya"), ("surabaya", "Wonokromo Surabaya"),
    ("bandung", "Arcamanik Bandung"), ("bandung", "Kiaracondong Bandung"),
]
base.QUERIES = [(city_id, district, CITY[city_id][3], CITY[city_id][4], CITY[city_id][1]) for city_id, district in DISTRICTS]

if __name__ == "__main__":
    base.main()
