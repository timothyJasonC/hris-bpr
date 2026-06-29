# WA HR API — Dokumentasi Endpoint

API tambahan untuk absensi (checkin) dan cuti, dipanggil dari WhatsApp gateway/bot.

## Base URL

```
http://<host>:<port>/api/method/wa_hr_api.api.<nama_fungsi>
```

Contoh lokal: `http://127.0.0.1:8002`

## Autentikasi

Semua endpoint butuh header `X-Api-Key` yang nilainya harus sama dengan `API Secret Key` yang diset di doctype **WA HR API Settings** (Desk > WA HR API Settings), dan `Enabled` harus dicentang.

```
X-Api-Key: <api_secret_key>
```

> Catatan: header `Authorization: Bearer <key>` **tidak dipakai** karena bentrok dengan auth bawaan Frappe (request akan ditolak 401 oleh Frappe sendiri sebelum sampai ke fungsi API ini).

Jika `X-Api-Key` salah/kosong atau settings belum `Enabled` → response `401`:
```json
{ "message": { "status": "error", "message": "Unauthorized" } }
```

Employee dicocokkan berdasarkan field `cell_number` pada doctype Employee (harus `status = Active`). Pastikan nomor HP yang dikirim WhatsApp gateway sama formatnya dengan yang disimpan di `cell_number`.

---

## 1. Create Checkin (Clock In / Clock Out)

Membuat record **Employee Checkin**. Tipe log (`IN`/`OUT`) terdeteksi otomatis berdasarkan riwayat checkin employee hari itu.

```
POST /api/method/wa_hr_api.api.create_checkin
```

**Headers**
```
Content-Type: application/json
X-Api-Key: <api_secret_key>
```

**Body**
```json
{
  "phone_number": "08123456789",
  "latitude": -6.200000,
  "longitude": 106.816666
}
```
- `phone_number` (required)
- `latitude`, `longitude` (optional)

**Response sukses (201)**
```json
{
  "message": {
    "status": "success",
    "message": "Clock In berhasil",
    "data": {
      "employee": "HR-EMP-00001",
      "employee_name": "Budi Santoso",
      "log_type": "IN",
      "checkin_time": "2026-06-24 09:00:00",
      "checkin_name": "EMP-CKIN-2026-00001"
    }
  }
}
```

**Response error**
| Kode | Kondisi |
|---|---|
| 400 | `phone_number` kosong, atau sudah Clock In **dan** Clock Out hari itu |
| 401 | API key salah/kosong, atau settings disabled |
| 404 | Employee dengan nomor HP tersebut tidak ditemukan/tidak aktif |
| 500 | Error internal lainnya |

---

## 2. Create Leave Application

Membuat **Leave Application**, dengan validasi: Leave Type harus ada, harus ada Leave Allocation yang aktif untuk periode tersebut, dan saldo cuti harus cukup.

```
POST /api/method/wa_hr_api.api.create_leave_application
```

**Headers**
```
Content-Type: application/json
X-Api-Key: <api_secret_key>
```

**Body**
```json
{
  "phone_number": "08123456789",
  "leave_type": "Casual Leave",
  "start_date": "2026-07-01",
  "end_date": "2026-07-02",
  "description": "Acara keluarga"
}
```
- `phone_number`, `leave_type`, `start_date`, `end_date` (required)
- `description` (optional)

**Response sukses (201)**
```json
{
  "message": {
    "status": "success",
    "message": "Leave Application berhasil dibuat",
    "data": {
      "leave_application_id": "HR-LAP-2026-00001",
      "employee": "HR-EMP-00001",
      "employee_name": "Budi Santoso",
      "leave_type": "Casual Leave",
      "from_date": "2026-07-01",
      "to_date": "2026-07-02",
      "status": "Open",
      "leave_balance": {
        "allocated": 12,
        "remaining": 10,
        "days_applied": 2
      }
    }
  }
}
```

**Response error**
| Kode | Kondisi |
|---|---|
| 400 | Field wajib kosong, Leave Type tidak ditemukan, Leave Allocation tidak ada untuk periode itu, atau saldo cuti tidak cukup |
| 401 | API key salah/kosong, atau settings disabled |
| 404 | Employee dengan nomor HP tersebut tidak ditemukan/tidak aktif |
| 500 | Error internal lainnya |

---

## 3. Check Leave Balance

Mengecek sisa cuti employee untuk semua Leave Type yang punya alokasi aktif (periode alokasi mencakup tanggal hari ini).

```
POST /api/method/wa_hr_api.api.check_leave_balance
```

**Headers**
```
Content-Type: application/json
X-Api-Key: <api_secret_key>
```

**Body**
```json
{
  "phone_number": "08123456789"
}
```
- `phone_number` (required)

**Response sukses (200)**
```json
{
  "message": {
    "status": "success",
    "message": "Data sisa cuti berhasil diambil",
    "data": {
      "employee_id": "HR-EMP-00001",
      "employee_name": "Budi Santoso",
      "department": "Engineering",
      "leave_balance": {
        "Casual Leave": { "allocated": 12, "taken": 2, "remaining": 10 },
        "Sick Leave": { "allocated": 6, "taken": 0, "remaining": 6 }
      }
    }
  }
}
```
> Jika employee tidak punya Leave Allocation aktif sama sekali, `leave_balance` akan berupa object kosong `{}`.

**Response error**
| Kode | Kondisi |
|---|---|
| 400 | `phone_number` kosong |
| 401 | API key salah/kosong, atau settings disabled |
| 404 | Employee dengan nomor HP tersebut tidak ditemukan/tidak aktif |
| 500 | Error internal lainnya |

---

## Setup Settings

1. Buka Desk → cari doctype **WA HR API Settings**
2. Centang **Enabled**
3. Isi **API Secret Key** (ini yang dikirim WhatsApp gateway via header `X-Api-Key`)
4. **Employee Phone Field** default `cell_number` — field Employee yang dicocokkan dengan nomor pengirim WhatsApp
