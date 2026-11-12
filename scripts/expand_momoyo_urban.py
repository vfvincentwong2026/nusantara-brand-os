"""Momoyo 最后一轮高密度城区补点。"""
import expand_momoyo_dense as base

CITY = base.CITY
DISTRICTS = [
    ("bandung", "Cibaduyut Bandung"), ("bandung", "Lengkong Bandung"),
    ("bandung", "Bandung Kulon"), ("bandung", "Rancasari Bandung"),
    ("surabaya", "Kenjeran Surabaya"), ("surabaya", "Benowo Surabaya"),
    ("surabaya", "Pakal Surabaya"), ("surabaya", "Asemrowo Surabaya"),
    ("semarang", "Pedurungan Semarang"), ("semarang", "Genuk Semarang"),
    ("semarang", "Ngaliyan Semarang"), ("semarang", "Mijen Semarang"),
    ("malang", "Lowokwaru Malang"), ("malang", "Blimbing Malang"), ("malang", "Klojen Malang"),
    ("yogyakarta", "Umbulharjo Yogyakarta"), ("yogyakarta", "Gamping Sleman"),
    ("yogyakarta", "Mlati Sleman"), ("yogyakarta", "Kasihan Bantul"),
    ("medan", "Medan Amplas"), ("medan", "Medan Denai"),
    ("medan", "Medan Johor"), ("medan", "Medan Polonia"),
    ("makassar", "Biringkanaya Makassar"), ("makassar", "Manggala Makassar"),
    ("denpasar", "Mengwi Bali"), ("denpasar", "Canggu Bali"),
    ("denpasar", "Ubud Bali"), ("denpasar", "Sanur Bali"),
]
base.QUERIES = [(city_id, district, CITY[city_id][3], CITY[city_id][4], CITY[city_id][1]) for city_id, district in DISTRICTS]

if __name__ == "__main__":
    base.main()
