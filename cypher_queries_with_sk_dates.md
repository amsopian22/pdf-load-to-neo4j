# Cypher Queries untuk SK dengan Tanggal

## 1. Query Nama dan Tanggal SK PNS

```cypher
// Query 1: Nama pegawai PNS dengan tanggal SK
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
WHERE e.document_type = 'PNS'
RETURN e.name AS nama_pegawai,
       e.employee_number AS nomor_pegawai,
       sd.formatted_date AS tanggal_sk,
       sd.raw_date AS tanggal_sk_asli,
       d.filename AS nama_file_sk,
       e.department AS bagian
ORDER BY sd.formatted_date DESC
```

## 2. Query Semua SK dengan Tanggal (PNS dan PPPK)

```cypher
// Query 2: Semua karyawan dengan tanggal SK
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
RETURN e.name AS nama_pegawai,
       e.employee_number AS nomor_pegawai,
       e.document_type AS jenis_sk,
       sd.formatted_date AS tanggal_sk,
       sd.raw_date AS tanggal_sk_asli,
       sd.day AS hari,
       sd.month AS bulan,
       sd.year AS tahun,
       sd.month_name AS nama_bulan,
       d.filename AS nama_file_sk,
       e.department AS bagian
ORDER BY sd.formatted_date DESC
```

## 3. Query Analisis SK per Tahun

```cypher
// Query 3: Analisis SK per tahun
MATCH (sd:SKDate)
OPTIONAL MATCH (e:Employee)-[:APPOINTED_ON]->(sd)
OPTIONAL MATCH (d:Document)-[:ISSUED_ON]->(sd)
RETURN sd.year AS tahun,
       count(DISTINCT e) AS jumlah_karyawan,
       count(DISTINCT d) AS jumlah_dokumen,
       collect(DISTINCT e.document_type) AS jenis_sk
ORDER BY tahun DESC
```

## 4. Query SK dalam Rentang Tanggal

```cypher
// Query 4: SK dalam rentang tanggal tertentu
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
WHERE sd.formatted_date >= '2024-01-01' AND sd.formatted_date <= '2024-12-31'
RETURN e.name AS nama_pegawai,
       e.document_type AS jenis_sk,
       sd.formatted_date AS tanggal_sk,
       sd.raw_date AS tanggal_sk_asli,
       e.department AS bagian
ORDER BY sd.formatted_date DESC
```

## 5. Query SK per Bulan

```cypher
// Query 5: SK per bulan dalam tahun tertentu
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
WHERE sd.year = 2024
RETURN sd.month AS bulan,
       sd.month_name AS nama_bulan,
       count(DISTINCT e) AS jumlah_karyawan,
       collect(DISTINCT e.document_type) AS jenis_sk,
       collect(e.name) AS nama_karyawan
ORDER BY sd.month
```

## 6. Query Mencari SK Tanpa Tanggal

```cypher
// Query 6: Karyawan yang SK-nya tidak memiliki tanggal
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
WHERE NOT EXISTS((e)-[:APPOINTED_ON]->(:SKDate))
RETURN e.name AS nama_pegawai,
       e.employee_number AS nomor_pegawai,
       e.document_type AS jenis_sk,
       d.filename AS nama_file_sk,
       e.department AS bagian
ORDER BY e.name
```

## 7. Query Statistik Lengkap SK

```cypher
// Query 7: Statistik lengkap SK dengan tanggal
MATCH (sd:SKDate)
OPTIONAL MATCH (e:Employee)-[:APPOINTED_ON]->(sd)
OPTIONAL MATCH (d:Document)-[:ISSUED_ON]->(sd)
RETURN sd.formatted_date AS tanggal_sk,
       sd.raw_date AS tanggal_asli,
       count(DISTINCT e) AS jumlah_karyawan,
       count(DISTINCT d) AS jumlah_dokumen,
       collect(DISTINCT e.document_type) AS jenis_sk,
       collect(e.name) AS nama_karyawan
ORDER BY sd.formatted_date DESC
```

## 8. Query Pencarian SK berdasarkan Nama

```cypher
// Query 8: Mencari SK berdasarkan nama karyawan
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
OPTIONAL MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
WHERE e.name CONTAINS 'SABARUDDIN' // Ganti dengan nama yang dicari
RETURN e.name AS nama_pegawai,
       e.employee_number AS nomor_pegawai,
       e.document_type AS jenis_sk,
       sd.formatted_date AS tanggal_sk,
       sd.raw_date AS tanggal_sk_asli,
       d.filename AS nama_file_sk,
       e.department AS bagian
```

## 9. Query Departemen dengan SK Terbanyak

```cypher
// Query 9: Departemen dengan SK terbanyak
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
OPTIONAL MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
RETURN e.department AS departemen,
       count(DISTINCT e) AS jumlah_karyawan,
       count(DISTINCT d) AS jumlah_sk,
       collect(DISTINCT e.document_type) AS jenis_sk,
       min(sd.formatted_date) AS sk_tertua,
       max(sd.formatted_date) AS sk_terbaru
ORDER BY jumlah_karyawan DESC
```

## 10. Query Relasi Lengkap Knowledge Graph

```cypher
// Query 10: Visualisasi relasi lengkap
MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
MATCH (e)-[:WORKS_IN]->(dept:Department)
RETURN e, d, sd, dept
LIMIT 50
```

## Contoh Hasil Query

Setelah menjalankan pipeline yang sudah diperbarui, Anda akan mendapatkan data seperti:

```
nama_pegawai: SABARUDDIN
nomor_pegawai: 01
tanggal_sk: 2024-01-15
tanggal_sk_asli: 15 Januari 2024
nama_file_sk: 01 SABARUDDIN.pdf
bagian: Sub Bagian Umum dan Kepegawaian
```

## Struktur Graph Database yang Diperbarui

```
Nodes:
- Employee: {name, employee_number, document_type, department}
- Document: {filename, content, document_type, department}
- SKDate: {formatted_date, raw_date, day, month, year, month_name}
- Department: {name}
- Keyword: {word}

Relationships:
- Employee-[:HAS_DOCUMENT]->Document
- Employee-[:APPOINTED_ON]->SKDate
- Document-[:ISSUED_ON]->SKDate
- Employee-[:WORKS_IN]->Department
- Document-[:BELONGS_TO]->Department
- Document-[:CONTAINS_KEYWORD]->Keyword
```