-- Create a new schema for the Pet Clinic
CREATE SCHEMA PETCLINIC; 

-- Set the search path to the schema
SET SEARCH_PATH TO PETCLINIC;

-- Create the tables in the schema
-- 1. USER table
CREATE TABLE "USER" (
email VARCHAR(50) PRIMARY KEY,
password VARCHAR(100) NOT NULL,
alamat TEXT NOT NULL,
nomor_telepon VARCHAR(15) NOT NULL
);

--2. PEGAWAI table
CREATE TABLE PEGAWAI (
no_pegawai UUID PRIMARY KEY,
tanggal_mulai_kerja DATE NOT NULL,
tanggal_akhir_kerja DATE,
email_user VARCHAR(50) NOT NULL,
FOREIGN KEY (email_user) REFERENCES "USER"(email)
);

--3. KLIEN table
CREATE TABLE KLIEN (
no_identitas UUID PRIMARY KEY,
tanggal_registrasi DATE NOT NULL,
email VARCHAR(50) NOT NULL,
FOREIGN KEY (email) REFERENCES "USER"(email)
);

-- 4. INDIVIDU table
CREATE TABLE INDIVIDU (
no_identitas_klien UUID PRIMARY KEY,
nama_depan VARCHAR(50) NOT NULL,
nama_tengah VARCHAR(50),
nama_belakang VARCHAR(50) NOT NULL,
FOREIGN KEY (no_identitas_klien) REFERENCES KLIEN(no_identitas)
);

-- 5. PERUSAHAAN table
CREATE TABLE PERUSAHAAN (
no_identitas_klien UUID PRIMARY KEY,
nama_perusahaan VARCHAR(100) NOT NULL,
FOREIGN KEY (no_identitas_klien) REFERENCES KLIEN(no_identitas)
);

-- 6. FRONT_DESK table
CREATE TABLE FRONT_DESK (
no_front_desk UUID PRIMARY KEY,
FOREIGN KEY (no_front_desk) REFERENCES PEGAWAI(no_pegawai)
);

-- 7. TENAGA_MEDIS table
CREATE TABLE TENAGA_MEDIS (
no_tenaga_medis UUID PRIMARY KEY,
no_izin_praktik VARCHAR(20) UNIQUE NOT NULL,
FOREIGN KEY (no_tenaga_medis) REFERENCES PEGAWAI(no_pegawai)
);


-- 8. PERAWAT_HEWAN table
CREATE TABLE PERAWAT_HEWAN (
no_perawat_hewan UUID PRIMARY KEY,
FOREIGN KEY (no_perawat_hewan) REFERENCES TENAGA_MEDIS(no_tenaga_medis)
);

-- 9. DOKTER_HEWAN table
CREATE TABLE DOKTER_HEWAN (
no_dokter_hewan UUID PRIMARY KEY,
FOREIGN KEY (no_dokter_hewan) REFERENCES TENAGA_MEDIS(no_tenaga_medis)
);

-- 10. SERTIFIKAT_KOMPETENSI table
CREATE TABLE SERTIFIKAT_KOMPETENSI (
no_sertifikat_kompetensi VARCHAR(10),
no_tenaga_medis UUID,
nama_sertifikat VARCHAR(100) NOT NULL,
PRIMARY KEY (no_sertifikat_kompetensi, no_tenaga_medis),
FOREIGN KEY (no_tenaga_medis) REFERENCES TENAGA_MEDIS(no_tenaga_medis)
);

-- 11. JADWAL_PRAKTIK table
CREATE TABLE JADWAL_PRAKTIK (
no_dokter_hewan UUID,
hari VARCHAR(10),
jam VARCHAR(20),
PRIMARY KEY (no_dokter_hewan, hari, jam),
FOREIGN KEY (no_dokter_hewan) REFERENCES DOKTER_HEWAN(no_dokter_hewan)
);

-- 12. JENIS_HEWAN table
CREATE TABLE JENIS_HEWAN (
id UUID PRIMARY KEY,
nama_jenis VARCHAR(50) NOT NULL
);

-- 13. HEWAN table
CREATE TABLE HEWAN (
nama VARCHAR(50),
no_identitas_klien UUID,
tanggal_lahir DATE NOT NULL,
id_jenis UUID NOT NULL,
url_foto VARCHAR(255) NOT NULL,
PRIMARY KEY (nama, no_identitas_klien),
FOREIGN KEY (no_identitas_klien) REFERENCES KLIEN(no_identitas),
FOREIGN KEY (id_jenis) REFERENCES JENIS_HEWAN(id)
);

-- 14. OBAT table
CREATE TABLE OBAT (
kode VARCHAR(10) PRIMARY KEY,
nama VARCHAR(100) NOT NULL,
harga INT NOT NULL,
stok INT NOT NULL,
dosis TEXT NOT NULL
);

-- 15. VAKSIN table
CREATE TABLE VAKSIN (
kode VARCHAR(6) PRIMARY KEY,
nama VARCHAR(50) NOT NULL,
harga INT NOT NULL,
stok INT NOT NULL
);

-- 16. PERAWATAN table
CREATE TABLE PERAWATAN (
kode_perawatan VARCHAR(10) PRIMARY KEY,
nama_perawatan VARCHAR(100) NOT NULL,
biaya_perawatan INT NOT NULL
);

-- 17. PERAWATAN_OBAT table
CREATE TABLE PERAWATAN_OBAT (
kode_perawatan VARCHAR(10),
kode_obat VARCHAR(10),
kuantitas_obat INT NOT NULL,
PRIMARY KEY (kode_perawatan, kode_obat),
FOREIGN KEY (kode_perawatan) REFERENCES PERAWATAN(kode_perawatan),
FOREIGN KEY (kode_obat) REFERENCES OBAT(kode)
);


-- 18. KUNJUNGAN table
CREATE TABLE KUNJUNGAN (
id_kunjungan UUID,
nama_hewan VARCHAR(50) NOT NULL,
no_identitas_klien UUID NOT NULL,
no_front_desk UUID NOT NULL,
no_perawat_hewan UUID NOT NULL,
no_dokter_hewan UUID NOT NULL,
kode_vaksin VARCHAR(6),
tipe_kunjungan VARCHAR(10) NOT NULL,
timestamp_awal TIMESTAMP NOT NULL,
timestamp_akhir TIMESTAMP,
suhu INT,
berat_badan NUMERIC(5,2),
PRIMARY KEY (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan),
FOREIGN KEY (nama_hewan, no_identitas_klien) REFERENCES HEWAN(nama, no_identitas_klien),
FOREIGN KEY (no_front_desk) REFERENCES FRONT_DESK(no_front_desk),
FOREIGN KEY (no_perawat_hewan) REFERENCES PERAWAT_HEWAN(no_perawat_hewan),
FOREIGN KEY (no_dokter_hewan) REFERENCES DOKTER_HEWAN(no_dokter_hewan),
FOREIGN KEY (kode_vaksin) REFERENCES VAKSIN(kode)
);

-- 19. KUNJUNGAN_KEPERAWATAN table
CREATE TABLE KUNJUNGAN_KEPERAWATAN (
id_kunjungan UUID,
nama_hewan VARCHAR(50),
no_identitas_klien UUID,
no_front_desk UUID,
no_perawat_hewan UUID,
no_dokter_hewan UUID,
kode_perawatan VARCHAR(10),
catatan TEXT,
PRIMARY KEY (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan),
FOREIGN KEY (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan) 
REFERENCES KUNJUNGAN(id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan),
FOREIGN KEY (kode_perawatan) REFERENCES PERAWATAN(kode_perawatan)
);