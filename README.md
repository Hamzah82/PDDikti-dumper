# PDDikti Mahasiswa Scraper 🐢

Tool Python untuk mengambil data mahasiswa dari situs resmi **PDDikti**
(Pangkalan Data Pendidikan Tinggi) berdasarkan **nama lengkap**.

Cara kerja singkat:

1. Input nama lengkap → cari ke `https://pddikti.kemdiktisaintek.go.id/search/NAMA`
2. Ambil hasil pencarian dari API internal PDDikti
3. Filter hasil yang namanya **100% sama** dengan input
4. Ambil data detail (setara tombol **"Lihat Detail"**) untuk setiap hasil yang cocok
5. Tampilkan langsung di terminal

---

## Instalasi

```bash
pip install requests
```

## Cara Pakai

```bash
# Cara dasar
python3 pddikti_scraper.py "Awangku Muhammad Hamzah"

# Mode interaktif (nama diminta lewat prompt)
python3 pddikti_scraper.py

# Tampilkan SEMUA hasil pencarian (bukan hanya yang 100% cocok)
python3 pddikti_scraper.py "Awangku Muhammad" --all

# Keluarkan hasil sebagai JSON (untuk diproses program lain)
python3 pddikti_scraper.py "Awangku Muhammad Hamzah" --json
```

## Contoh Output

```
[1/3] Mencari "Awangku Muhammad Hamzah" di PDDikti ...
      Ditemukan 1 hasil pencarian.
      Cocok 100% dengan input: 1 data.

[2/3] Mengambil data detail (1 data) ...

[3/3] Selesai.

======================================================================
                        DATA MAHASISWA PDDIKTI
======================================================================
  Nama                : AWANGKU MUHAMMAD HAMZAH
  NIM                 : 26081010214
  Perguruan Tinggi    : Universitas Pembangunan Nasional Veteran Jawa Timur
  Kode PT             : 001059
  Program Studi       : Informatika
  Kode Prodi          : 55202
  Jenjang             : Sarjana
  Jenis Kelamin       : Laki-laki
  Jenis Daftar        : Peserta didik baru
  Tanggal Masuk       : 2026-08-03
  Status Saat Ini     : -
----------------------------------------------------------------------
  ID Mahasiswa        : ...
======================================================================
```

## Opsi

- `--all` — tampilkan semua hasil pencarian, tidak difilter 100% cocok
- `--json` — keluarkan JSON mentah (cocok untuk pipeline/otomasi)

## Catatan Teknis

Situs PDDikti adalah **SPA (React)**, sehingga HTML mentahnya tidak berisi data.
Tool ini memanggil API internal yang dipakai frontend-nya:

- Pencarian : `GET /api/pencarian/mhs/{nama}`
- Detail    : `GET /api/detail/mhs/{id}`

API menolak request tanpa header `Referer` dan `Origin` dari domain PDDikti,
jadi kedua header itu wajib dikirim.

**ID mahasiswa** dari PDDikti berbentuk base64 (mengandung `+`, `/`, `=`).
ID tersebut harus ditempel **apa adanya** pada URL detail — kalau di-encode
ulang, server akan membalas `{"message":"invalid id"}`.

## Batasan

- Nama harus diketik cukup lengkap; pencarian PDDikti berbasis kecocokan kata
- Data yang tampil hanya yang dipublikasikan PDDikti
- Mohon gunakan secara wajar dan hormati ketentuan layanan PDDikti

## Lisensi

MIT