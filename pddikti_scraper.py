#!/usr/bin/env python3
"""
PDDikti Mahasiswa Scraper
=========================

Mencari data mahasiswa berdasarkan NAMA LENGKAP pada situs resmi PDDikti
(https://pddikti.kemdiktisaintek.go.id), memfilter hasil yang namanya
100% sama dengan input, lalu mengambil data detail dan menampilkannya
di terminal.

Cara pakai:
    python3 pddikti_scraper.py "Awangku Muhammad Hamzah"
    python3 pddikti_scraper.py            # mode interaktif (input diminta)
    python3 pddikti_scraper.py "Nama" --json    # keluarkan JSON mentah
    python3 pddikti_scraper.py "Nama" --all     # tampilkan semua hasil (tak hanya yang 100% cocok)

Catatan teknis:
    Situs PDDikti adalah SPA (React). Data diambil dari API internal:
      - Pencarian : GET /api/pencarian/mhs/{nama}
      - Detail    : GET /api/detail/mhs/{id}
    API menolak request tanpa header Referer/Origin dari domain PDDikti,
    sehingga header tersebut wajib dikirim.

Penulis : Ruka AI 🐢
Lisensi : MIT
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    sys.exit(
        "Modul 'requests' belum terpasang.\n"
        "Pasang dengan: pip install requests"
    )


# ---------------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------------

BASE_URL = "https://pddikti.kemdiktisaintek.go.id"
API_SEARCH = BASE_URL + "/api/pencarian/mhs/{nama}"
API_DETAIL = BASE_URL + "/api/detail/mhs/{id}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Referer": BASE_URL + "/",
    "Origin": BASE_URL,
}

TIMEOUT = 30

# Label ramah untuk field data detail
FIELD_LABELS = {
    "nama": "Nama",
    "nim": "NIM",
    "nama_pt": "Perguruan Tinggi",
    "kode_pt": "Kode PT",
    "prodi": "Program Studi",
    "kode_prodi": "Kode Prodi",
    "jenjang": "Jenjang",
    "jenis_kelamin": "Jenis Kelamin",
    "jenis_daftar": "Jenis Daftar",
    "tanggal_masuk": "Tanggal Masuk",
    "status_saat_ini": "Status Saat Ini",
    "id": "ID Mahasiswa",
    "id_pt": "ID PT",
    "id_sms": "ID SMS",
}


# ---------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------

def normalisasi(teks: str) -> str:
    """Normalisasi nama untuk perbandingan: huruf besar, spasi tunggal, tanpa aksen."""
    if not teks:
        return ""
    teks = unicodedata.normalize("NFKD", teks)
    teks = "".join(c for c in teks if not unicodedata.combining(c))
    teks = teks.upper()
    teks = re.sub(r"[^A-Z0-9 ]", " ", teks)
    teks = re.sub(r"\s+", " ", teks).strip()
    return teks


def nama_sama_persis(nama_api: str, nama_input: str) -> bool:
    """True jika nama dari API 100% sama dengan input (setelah normalisasi)."""
    return normalisasi(nama_api) == normalisasi(nama_input)


def garis(char: str = "=", panjang: int = 70) -> str:
    return char * panjang


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class PddiktiError(Exception):
    """Kesalahan saat mengakses PDDikti."""


def _get_json(url: str, sesi: requests.Session) -> Dict[str, Any]:
    try:
        resp = sesi.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        raise PddiktiError("Koneksi ke PDDikti timeout. Coba lagi nanti.")
    except requests.exceptions.ConnectionError:
        raise PddiktiError("Tidak dapat terhubung ke PDDikti. Periksa koneksi internet.")

    if resp.status_code == 403:
        raise PddiktiError(
            "Akses ditolak (403). PDDikti mungkin sedang membatasi permintaan."
        )
    if resp.status_code == 404:
        raise PddiktiError("Endpoint tidak ditemukan (404).")
    if resp.status_code != 200:
        raise PddiktiError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        return resp.json()
    except ValueError:
        raise PddiktiError("Respons bukan JSON yang valid.")


def cari_mahasiswa(nama: str, sesi: requests.Session) -> List[Dict[str, Any]]:
    """Cari mahasiswa berdasarkan nama. Mengembalikan list hasil pencarian."""
    url = API_SEARCH.format(nama=quote(nama, safe=""))
    data = _get_json(url, sesi)

    if data.get("status") != "success":
        raise PddiktiError(
            f"Pencarian gagal: {data.get('message', 'tanpa pesan')}"
        )

    hasil = data.get("data") or []
    if isinstance(hasil, dict):  # jaga-jaga jika API mengembalikan objek tunggal
        hasil = [hasil]
    return hasil


def ambil_detail(id_mahasiswa: str, sesi: requests.Session) -> Dict[str, Any]:
    """Ambil data detail mahasiswa berdasarkan ID hasil pencarian.

    ID dari PDDikti berbentuk base64 (mengandung '+', '/', '='). Karakter
    tersebut TIDAK boleh di-encode ulang, karena server memvalidasi bentuk
    mentahnya. Jadi ID ditempel apa adanya.
    """
    url = API_DETAIL.format(id=id_mahasiswa)
    data = _get_json(url, sesi)

    if data.get("status") != "success":
        raise PddiktiError(
            f"Gagal mengambil detail: {data.get('message', 'tanpa pesan')}"
        )
    return data.get("data") or {}


# ---------------------------------------------------------------------------
# Tampilan
# ---------------------------------------------------------------------------

JENIS_KELAMIN = {"L": "Laki-laki", "P": "Perempuan"}


def tampilkan_detail(detail: Dict[str, Any], indeks: Optional[int] = None) -> None:
    print(garis())
    judul = "DATA MAHASISWA PDDIKTI"
    if indeks is not None:
        judul += f" (#{indeks})"
    print(judul.center(70))
    print(garis())

    urutan = [
        "nama", "nim", "nama_pt", "kode_pt", "prodi", "kode_prodi",
        "jenjang", "jenis_kelamin", "jenis_daftar", "tanggal_masuk",
        "status_saat_ini",
    ]

    for key in urutan:
        if key not in detail:
            continue
        nilai = detail.get(key)
        if nilai is None or str(nilai).strip() == "":
            nilai = "-"
        nilai = str(nilai).strip()

        if key == "jenis_kelamin":
            nilai = JENIS_KELAMIN.get(nilai.upper(), nilai)

        label = FIELD_LABELS.get(key, key)
        print(f"  {label:<20}: {nilai}")

    print(garis("-"))
    print(f"  {'ID Mahasiswa':<20}: {detail.get('id', '-')}")
    print(garis())


def tampilkan_ringkasan(hasil: List[Dict[str, Any]], nama_input: str) -> None:
    """Tampilkan tabel ringkas hasil pencarian."""
    print(garis("-"))
    print(f"  Hasil pencarian mentah untuk: {nama_input}")
    print(garis("-"))
    for i, item in enumerate(hasil, 1):
        cocok = " [100% COCOK]" if nama_sama_persis(item.get("nama", ""), nama_input) else ""
        print(f"  {i}. {item.get('nama', '-')}{cocok}")
        print(f"     NIM   : {item.get('nim', '-')}")
        print(f"     PT    : {item.get('nama_pt', '-')}")
        print(f"     Prodi : {item.get('nama_prodi', '-')}")
    print(garis("-"))


# ---------------------------------------------------------------------------
# Alur utama
# ---------------------------------------------------------------------------

def proses(nama_input: str, tampilkan_semua: bool = False,
           keluarkan_json: bool = False) -> int:
    """Jalankan pencarian + ambil detail. Return exit code."""
    nama_input = nama_input.strip()
    if not nama_input:
        print("Error: nama tidak boleh kosong.", file=sys.stderr)
        return 2

    sesi = requests.Session()

    if not keluarkan_json:
        print(f"\n[1/3] Mencari \"{nama_input}\" di PDDikti ...")

    try:
        hasil = cari_mahasiswa(nama_input, sesi)
    except PddiktiError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not hasil:
        if not keluarkan_json:
            print("Tidak ada mahasiswa yang ditemukan.")
        else:
            print(json.dumps({"status": "empty", "data": []}, ensure_ascii=False, indent=2))
        return 0

    # Filter: nama harus 100% sama dengan input
    if tampilkan_semua:
        target = hasil
    else:
        target = [h for h in hasil if nama_sama_persis(h.get("nama", ""), nama_input)]

    if not keluarkan_json:
        print(f"      Ditemukan {len(hasil)} hasil pencarian.")
        if not tampilkan_semua:
            print(f"      Cocok 100% dengan input: {len(target)} data.")
        if len(target) == 0:
            print("\nTidak ada nama yang 100% sama dengan input.")
            print("Berikut hasil pencarian yang mirip:\n")
            tampilkan_ringkasan(hasil, nama_input)

    if not target:
        return 0

    if not keluarkan_json:
        print(f"\n[2/3] Mengambil data detail ({len(target)} data) ...")

    semua_detail: List[Dict[str, Any]] = []
    for item in target:
        id_mhs = item.get("id")
        if not id_mhs:
            continue
        try:
            detail = ambil_detail(id_mhs, sesi)
            semua_detail.append(detail)
        except PddiktiError as e:
            if not keluarkan_json:
                print(f"      Gagal ambil detail untuk {item.get('nama')}: {e}",
                      file=sys.stderr)

    if keluarkan_json:
        print(json.dumps(
            {"status": "success", "query": nama_input, "data": semua_detail},
            ensure_ascii=False, indent=2,
        ))
        return 0

    print(f"\n[3/3] Selesai.\n")
    for i, detail in enumerate(semua_detail, 1):
        tampilkan_detail(detail, indeks=i if len(semua_detail) > 1 else None)
        print()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scrape data mahasiswa dari PDDikti berdasarkan nama lengkap.",
        epilog='Contoh: python3 pddikti_scraper.py "Awangku Muhammad Hamzah"',
    )
    parser.add_argument("nama", nargs="?", help="Nama lengkap mahasiswa")
    parser.add_argument("--all", action="store_true",
                        help="Tampilkan semua hasil pencarian, bukan hanya yang 100%% cocok")
    parser.add_argument("--json", action="store_true",
                        help="Keluarkan hasil dalam format JSON")
    args = parser.parse_args()

    nama = args.nama
    if not nama:
        try:
            nama = input("Masukkan nama lengkap mahasiswa: ")
        except (EOFError, KeyboardInterrupt):
            print("\nDibatalkan.")
            return 130

    try:
        return proses(nama, tampilkan_semua=args.all, keluarkan_json=args.json)
    except KeyboardInterrupt:
        print("\nDibatalkan oleh pengguna.")
        return 130


if __name__ == "__main__":
    sys.exit(main())