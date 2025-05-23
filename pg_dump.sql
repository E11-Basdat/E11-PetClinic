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
INSERT INTO "USER" (email, password, alamat, nomor_telepon) VALUES
	('budi.pratama@gmail.com', 'Bud1Pr4t4m4#', 'Jl. Merdeka No. 27, Jakarta Pusat', '81234567890'),
	('dian.safitri@gmail.com', 'D14nS4f1tr1*', 'Jl. Sudirman No. 45, Surabaya', '85712345678'),
	('ahmad.rizal@yahoo.com', 'R1z4l2023!', 'Jl. Pemuda No. 12, Bandung', '87812345678'),
	('ratna.dewi@gmail.com', 'R4tn4D3w1@', 'Jl. Diponegoro No. 56, Semarang', '81398765432'),
	('anwar.ibrahim@hotmail.com', '4nw4rIbr4h1m#', 'Jl. Ahmad Yani No. 23, Yogyakarta', '85867890123'),
	('siti.rahayu@gmail.com', 'S1t1R4h4yu$', 'Jl. Pahlawan No. 8, Malang', '87712345678'),
	('joko.widodo@yahoo.com', 'J0k0W1d0d0#', 'Jl. Gajah Mada No. 19, Solo', '81345678901'),
	('mega.wati@gmail.com', 'M3g4W4t1*', 'Jl. Imam Bonjol No. 34, Medan', '85698765432'),
	('hendra.susilo@gmail.com', 'H3ndr4Sus1l0@', 'Jl. Juanda No. 67, Makassar', '81987654321'),
	('indah.permata@yahoo.com', 'Ind4hP3rm4t4!', 'Jl. Hasanudin No. 15, Denpasar', '85812345678'),
	('agus.santoso@gmail.com', '4gusS4nt0s0#', 'Jl. Veteran No. 29, Palembang', '87898765432'),
	('sri.wahyuni@hotmail.com', 'Sr1W4hyun1$', 'Jl. Gatot Subroto No. 51, Padang', '81287654321'),
	('bambang.sutomo@gmail.com', 'B4mb4ngSut0m0@', 'Jl. Cendrawasih No. 7, Balikpapan', '85787654321'),
	('rina.fitriani@yahoo.com', 'R1n4F1tr14n1#', 'Jl. Sisingamangaraja No. 42, Manado', '87754321678'),
	('eko.prasetyo@gmail.com', '3k0Pr4s3ty0*', 'Jl. Thamrin No. 31, Samarinda', '81376543210'),
	('dewi.lestari@gmail.com', 'D3w1L3st4r1$', 'Jl. Kartini No. 18, Banjarmasin', '85743215678'),
	('irfan.hakim@yahoo.com', '1rf4nH4k1m@', 'Jl. Asia Afrika No. 65, Ambon', '87865432109'),
	('maya.anggraini@gmail.com', 'M4y44nggr41n1#', 'Jl. Supratman No. 24, Jayapura', '81254321098'),
	('surya.pratama@hotmail.com', 'Sury4Pr4t4m4!', 'Jl. Yos Sudarso No. 47, Mataram', '85698712345'),
	('desi.ratnasari@gmail.com', 'D3s1R4tn4s4r1$', 'Jl. Urip Sumoharjo No. 39, Pekanbaru', '87712349876'),
	('wawan.setiawan@yahoo.com', 'W4w4nS3t14w4n@', 'Jl. MT Haryono No. 72, Jambi', '81398761234'),
	('yuni.safitri@gmail.com', 'Yun1S4f1tr1#', 'Jl. Sam Ratulangi No. 11, Kupang', '85732145678'),
	('hendrik.wijaya@gmail.com', 'H3ndr1kW1j4y4$', 'Jl. Lambung Mangkurat No. 53, Pontianak', '87898123456'),
	('lia.kusuma@yahoo.com', 'L14Kus4m4@', 'Jl. Antasari No. 16, Bengkulu', '81387651234'),
	('fajar.ramadhan@gmail.com', 'F4j4rR4m4dh4n!', 'Jl. Pangeran Diponegoro No. 28, Palangkaraya', '85712398745'),
	('nova.susanti@hotmail.com', 'N0v4Sus4nt1#', 'Jl. RE Martadinata No. 49, Kendari', '87732165498'),
	('bagus.purnomo@gmail.com', 'B4gusPurn0m0$', 'Jl. KH Wahid Hasyim No. 33, Gorontalo', '81254789632'),
	('lina.mariani@yahoo.com', 'L1n4M4r14n1@', 'Jl. A Yani No. 61, Serang', '85787456321'),
	('tono.wibowo@gmail.com', 'T0n0W1b0w0#', 'Jl. Pasar Baru No. 37, Ternate', '87798765432'),
	('nita.susanto@gmail.com', 'N1t4Sus4nt0!', 'Jl. Dr Sutomo No. 59, Palu', '81376598214'),
	('arief.hidayat@yahoo.com', '4r13fH1d4y4t$', 'Jl. Letjen Suprapto No. 17, Bandung', '85723416789'),
	('fitri.handayani@gmail.com', 'F1tr1H4nd4y4n1@', 'Jl. Hayam Wuruk No. 22, Cirebon', '87712387456'),
	('donny.kusuma@hotmail.com', 'D0nnyKusum4#', 'Jl. Wahidin No. 41, Sukabumi', '81398745612'),
	('rini.anggraeni@gmail.com', 'R1n14nggr43n1$', 'Jl. Sultan Agung No. 26, Tasikmalaya', '85787654123'),
	('wahyu.nugroho@yahoo.com', 'W4hyuNugr0h0!', 'Jl. Cipto Mangunkusumo No. 13, Purwokerto', '87798123456');

INSERT INTO PEGAWAI (no_pegawai, tanggal_mulai_kerja, tanggal_akhir_kerja, email_user) VALUES
    ('f47ac10b-58cc-4372-a567-0e02b2c3d479', '2021-03-15', NULL, 'budi.pratama@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d480', '2020-05-21', NULL, 'dian.safitri@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d481', '2019-11-10', NULL, 'ahmad.rizal@yahoo.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d482', '2022-01-05', NULL, 'ratna.dewi@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d483', '2018-09-18', '2023-06-30', 'anwar.ibrahim@hotmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d484', '2020-07-01', NULL, 'siti.rahayu@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d485', '2021-10-25', NULL, 'joko.widodo@yahoo.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d486', '2019-04-16', NULL, 'mega.wati@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d487', '2022-03-01', NULL, 'hendra.susilo@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d488', '2020-12-15', NULL, 'indah.permata@yahoo.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d489', '2021-05-03', NULL, 'agus.santoso@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d490', '2018-11-20', '2023-10-15', 'sri.wahyuni@hotmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d491', '2022-02-14', NULL, 'bambang.sutomo@gmail.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d492', '2019-08-07', NULL, 'rina.fitriani@yahoo.com'),
    ('f47ac10b-58cc-4372-a567-0e02b2c3d493', '2020-10-12', NULL, 'eko.prasetyo@gmail.com');

INSERT INTO KLIEN (no_identitas, tanggal_registrasi, email) VALUES
	('6ba7b82c-9dad-11d1-80b4-00c04fd430c8', '2022-03-10', 'dewi.lestari@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-00c04fd430c9', '2022-04-15', 'irfan.hakim@yahoo.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c10', '2022-05-20', 'maya.anggraini@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c11', '2022-06-25', 'surya.pratama@hotmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c12', '2022-07-12', 'desi.ratnasari@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c13', '2022-08-18', 'wawan.setiawan@yahoo.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c14', '2022-09-05', 'yuni.safitri@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c15', '2022-10-22', 'hendrik.wijaya@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c16', '2022-11-14', 'lia.kusuma@yahoo.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c17', '2022-12-07', 'fajar.ramadhan@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c18', '2023-01-19', 'nova.susanti@hotmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c19', '2023-02-28', 'bagus.purnomo@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c20', '2023-03-16', 'lina.mariani@yahoo.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c21', '2023-04-21', 'tono.wibowo@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c22', '2023-05-09', 'nita.susanto@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c23', '2023-06-12', 'arief.hidayat@yahoo.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c24', '2023-07-25', 'fitri.handayani@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c25', '2023-08-30', 'donny.kusuma@hotmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c26', '2023-09-11', 'rini.anggraeni@gmail.com'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c27', '2023-10-19', 'wahyu.nugroho@yahoo.com');

INSERT INTO INDIVIDU (no_identitas_klien, nama_depan, nama_tengah, nama_belakang) VALUES
    ('6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'Dewi', 'Ayu', 'Lestari'),
    ('6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'Irfan', NULL, 'Hakim'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'Maya', 'Putri', 'Anggraini'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'Surya', 'Adi', 'Pratama'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'Desi', NULL, 'Ratnasari'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c13', 'Wawan', 'Kurniawan', 'Setiawan'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c14', 'Yuni', NULL, 'Safitri'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c15', 'Hendrik', 'Budi', 'Wijaya'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c16', 'Lia', 'Kartika', 'Kusuma'),
    ('6ba7b82c-9dad-11d1-80b4-0c04fd430c17', 'Fajar', NULL, 'Ramadhan');

INSERT INTO INDIVIDU (no_identitas_klien, nama_perusahaan) VALUES
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c18', 'PT Sejahtera Abadi'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c19', 'CV Maju Bersama'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c20', 'PT Cinta Satwa Indonesia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c21', 'Yayasan Peduli Hewan'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c22', 'PT Veterinaria Nusantara'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c23', 'CV Animal Care Indonesia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c24', 'PT Sehat Satwa Tercinta'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c25', 'Koperasi Peternak Bahagia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c26', 'PT Fauna Sejahtera'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c27', 'Yayasan Konservasi Hewan Indonesia');

INSERT INTO PERUSAHAAN (no_identitas_klien, nama_perusahaan) VALUES
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c18', 'PT Sejahtera Abadi'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c19', 'CV Maju Bersama'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c20', 'PT Cinta Satwa Indonesia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c21', 'Yayasan Peduli Hewan'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c22', 'PT Veterinaria Nusantara'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c23', 'CV Animal Care Indonesia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c24', 'PT Sehat Satwa Tercinta'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c25', 'Koperasi Peternak Bahagia'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c26', 'PT Fauna Sejahtera'),
	('6ba7b82c-9dad-11d1-80b4-0c04fd430c27', 'Yayasan Konservasi Hewan Indonesia');

INSERT INTO FRONT_DESK (no_front_desk) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d479'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d480'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d481'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d482'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d483');

INSERT INTO TENAGA_MEDIS (no_tenaga_medis, no_izin_praktik) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d484', 'SIP-123456789'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d485', 'SIP-234567890'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d486', 'SIP-345678901'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d487', 'SIP-456789012'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d488', 'SIP-567890123'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d489', 'SIP-678901234'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d490', 'SIP-789012345'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d491', 'SIP-890123456'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d492', 'SIP-901234567'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d493', 'SIP-012345678');

INSERT INTO PERAWAT_HEWAN (no_perawat_hewan) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d484'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d485'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d486'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d487'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d488');

INSERT INTO DOKTER_HEWAN (no_dokter_hewan) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d489'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d490'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d491'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d492'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d493');

INSERT INTO SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat) VALUES
	('123/PH/456', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'Sertifikat Perawat Hewan Tersertifikasi'),
	('234/PH/578', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'Sertifikat Ahli Perawatan Intensif Hewan'),
	('345/PH/689', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'Sertifikat Perawat Spesialis Geriatri Hewan'),
	('456/PH/123', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'Sertifikat Teknisi Radiologi Hewan'),
	('567/PH/234', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'Sertifikat Perawat Anestesi Hewan'),
	('678/DH/345', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'Sertifikat Dokter Hewan Spesialis Penyakit Kucing'),
	('789/DH/456', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'Sertifikat Ahli Bedah Hewan Kecil'),
	('890/DH/567', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'Sertifikat Spesialis Nutrisi Hewan Peliharaan'),
	('901/DH/678', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'Sertifikat Dokter Hewan Spesialis Onkologi'),
	('012/DH/789', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'Sertifikat Spesialis Dermatologi Hewan');

INSERT INTO JENIS_HEWAN (id, nama_jenis) VALUES
	('8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'Mamalia'),
	('5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'Aves'),
	('2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'Reptil'),
	('4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'Pisces'),
	('b8a1e79a-0cfa-4de3-9d3b-1c2e825d0b0e', 'Amfibi');

INSERT INTO HEWAN (nama, no_identitas_klien, tanggal_lahir, id_jenis, url_foto) VALUES
	('Blacky', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', '2020-05-12', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?dog'),
	('Snowy', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', '2021-11-03', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?bird'),
	('Coco', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', '2019-04-09', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?gecko'),
	('Luna', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', '2022-02-14', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?cat'),
	('Bubbles', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', '2021-08-01', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?fish'),
	('Spike', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', '2020-12-25', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?snake'),
	('Bella', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', '2018-10-18', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?golden_retriever'),
	('Sky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', '2021-07-06', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?parrot'),
	('Rocky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', '2022-03-30', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?rottweiler'),
	('Kiwi', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', '2023-01-04', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?cockatiel'),
	('Nemo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', '2022-09-15', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?clownfish'),
	('Axel', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', '2021-06-05', 'b8a1e79a-0cfa-4de3-9d3b-1c2e825d0b0e', 'https://source.unsplash.com/100x100?axolotl'),
	('Milo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', '2020-02-27', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?beagle'),
	('Polly', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', '2019-09-10', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?macaw'),
	('Draco', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', '2018-11-02', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?iguana'),
	('Puffy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', '2022-04-21', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?pufferfish'),
	('Ginger', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', '2021-03-08', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?cat-orange'),
	('Quack', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', '2020-05-22', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?duck'),
	('Shadow', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', '2019-07-14', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?black-cat'),
	('Rango', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', '2022-10-09', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?chameleon'),
	('Cookie', '6ba7b82c-9dad-11d1-80b4-0c04fd430c18', '2020-01-19', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?corgi'),
	('Fin', '6ba7b82c-9dad-11d1-80b4-0c04fd430c18', '2023-02-11', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?betta'),
	('Tiger', '6ba7b82c-9dad-11d1-80b4-0c04fd430c19', '2021-12-25', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?cat-tiger'),
	('Skippy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c19', '2022-06-13', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?budgie'),
	('Flash', '6ba7b82c-9dad-11d1-80b4-0c04fd430c20', '2019-09-01', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?turtle'),
	('Blinky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c20', '2023-03-14', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?goldfish'),
	('Bruno', '6ba7b82c-9dad-11d1-80b4-0c04fd430c21', '2020-04-30', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?labrador'),
	('Chirpy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c21', '2022-11-11', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?sparrow'),
	('Sally', '6ba7b82c-9dad-11d1-80b4-0c04fd430c22', '2021-02-17', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?poodle'),
	('Rex', '6ba7b82c-9dad-11d1-80b4-0c04fd430c22', '2018-12-05', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?monitor-lizard'),
	('Buddy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c23', '2023-01-07', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?beagle-puppy'),
	('Sal', '6ba7b82c-9dad-11d1-80b4-0c04fd430c23', '2022-05-28', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?salmon'),
	('Nala', '6ba7b82c-9dad-11d1-80b4-0c04fd430c24', '2020-06-16', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?ragdoll-cat'),
	('Echo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c24', '2019-01-03', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?cockatoo'),
	('Mojo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c25', '2021-05-11', '2a70af9e-72b6-4c16-8f62-9c6e5b99bd05', 'https://source.unsplash.com/100x100?python-snake'),
	('Gill', '6ba7b82c-9dad-11d1-80b4-0c04fd430c25', '2022-07-22', '4d9e780e-8613-4e33-843f-3f43d1a9f9c7', 'https://source.unsplash.com/100x100?guppy'),
	('Misty', '6ba7b82c-9dad-11d1-80b4-0c04fd430c26', '2019-03-06', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?persian-cat'),
	('Hopper', '6ba7b82c-9dad-11d1-80b4-0c04fd430c26', '2021-09-19', 'b8a1e79a-0cfa-4de3-9d3b-1c2e825d0b0e', 'https://source.unsplash.com/100x100?frog'),
	('Charlie', '6ba7b82c-9dad-11d1-80b4-0c04fd430c27', '2020-08-13', '8e76c095-b156-4fd4-bc1d-19e4f74c461a', 'https://source.unsplash.com/100x100?shiba'),
	('Zazu', '6ba7b82c-9dad-11d1-80b4-0c04fd430c27', '2022-10-30', '5a1f8ac2-6d03-4f54-9283-1cf4c7f4c8aa', 'https://source.unsplash.com/100x100?hornbill');

INSERT INTO PERAWATAN (kode_perawatan, nama_perawatan, biaya_perawatan) VALUES
	('TRM001', 'Perawatan Gigi', '325000'),
	('TRM002', 'Grooming', '600000'),
	('TRM003', 'Pembersihan Telinga', '140000'),
	('TRM004', 'Perawatan Kulit dan Bulu', '150000'),
	('TRM005', 'Perawatan Luka Ringan', '125000');

INSERT INTO OBAT (kode, nama, harga, stok, dosis) VALUES
	('MED001', 'Amoxicillin ', '25000', '50', '10–20 mg/kg, 2x sehari'),
	('MED002', 'Dexamethasone ', '15000', '30', '0,1–0,5 mg/kg, 1x sehari'),
	('MED003', 'Ketoconazole', '35000', '20', '5–10 mg/kg, 1x sehari'),
	('MED004', 'Metronidazole ', '20000', '40', '10–25 mg/kg, 2x sehari'),
	('MED005', 'Ivermectin ', '50000', '25', '0,2–0,4 mg/kg'),
	('MED006', 'Antiparasit Topikal', '45000', '35', 'Oleskan 1x/bulan (sesuai berat badan)'),
	('MED007', 'Antibiotik Telinga', '30000', '15', '2–3 tetes, 2x sehari'),
	('MED008', 'Ear Cleaner', '40000', '50', '3–5 tetes, 1–2x/minggu'),
	('MED009', 'Enrofloxacin', '60000', '10', '5–10 mg/kg, 1x sehari'),
	('MED010', 'Clindamycin', '55000', '18', '5–10 mg/kg, 2x sehari');

INSERT INTO PERAWATAN_OBAT (kode_perawatan, kode_obat, kuantitas_obat) VALUES
	('TRM001', 'MED001', '100'),
	('TRM002', 'MED002', '75'),
	('TRM003', 'MED003', '250'),
	('TRM004', 'MED004', '30'),
	('TRM005', 'MED005', '150'),
	('TRM001', 'MED006', '200'),
	('TRM002', 'MED007', '60'),
	('TRM003', 'MED008', '40'),
	('TRM004', 'MED009', '25'),
	('TRM005', 'MED010', '90');

INSERT INTO KUNJUNGAN (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_vaksin, tipe_kunjungan, timestamp_awal, timestamp_akhir, suhu, berat_badan) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d479', 'Blacky', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'VAC002', 'Janji Temu', '2024-01-05 9:30', '2024-01-05 10:00', '38', '25.5'),
	('550e8400-e29b-41d4-a716-446655440000', 'Snowy', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'VAC009', 'Janji Temu', '2024-02-18 14:10', '2024-02-18 14:40', '40', '1.2'),
	('d3973b2a-5fc2-47d6-8358-1912ad4c4442', 'Coco', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', NULL, 'Janji Temu', '2024-03-22 10:05', '2024-03-22 10:50', '37', '0.3'),
	('9a33b35c-f3c8-4ca0-8c8c-dcc21e3d15e2', 'Luna', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'VAC003', 'Janji Temu', '2024-04-03 11:20', '2024-04-03 11:45', '38', '4.1'),
	('b5f8c3d2-e87a-4a1f-bc19-3c6a01837a8b', 'Bubbles', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', NULL, 'Walk-In', '2024-05-07 9:00', '2024-05-07 9:35', '26', '0.15'),
	('67c6697c-5e3e-4f0a-8d84-b9ffb8302a36', 'Spike', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', NULL, 'Darurat', '2024-06-11 15:40', '2024-06-11 16:30', '35', '4.8'),
	('01234567-89ab-cdef-0123-456789abcdef', 'Bella', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'VAC004', 'Janji Temu', '2024-07-19 13:15', '2024-07-19 13:45', '39', '29'),
	('98765432-10fe-dcba-9876-543210fedcba', 'Sky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'VAC009', 'Janji Temu', '2024-08-02 8:25', '2024-08-02 8:50', '41', '0.95'),
	('a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6', 'Rocky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', NULL, 'Darurat', '2024-09-10 10:10', '2024-09-15 10:00', '39', '28.75'),
	('87654321-fedc-ba98-7654-3210fedcba98', 'Kiwi', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'VAC009', 'Janji Temu', '2024-10-03 9:05', '2024-10-03 9:25', '40', '0.09'),
	('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'Nemo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', NULL, 'Walk-In', '2024-11-08 11:00', '2024-11-08 11:20', '26', '0.12'),
	('6ba7b811-9dad-11d1-80b4-00c04fd430c8', 'Axel', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'VAC007', 'Janji Temu', '2024-12-20 16:30', '2024-12-20 17:00', '25', '0.23'),
	('6ba7b812-9dad-11d1-80b4-00c04fd430c8', 'Milo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', NULL, 'Janji Temu', '2025-01-14 13:50', '2025-01-14 14:25', '38', '20'),
	('6ba7b813-9dad-11d1-80b4-00c04fd430c8', 'Polly', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'VAC009', 'Janji Temu', '2025-02-02 10:40', '2025-02-02 11:05', '41', '0.75'),
	('6ba7b814-9dad-11d1-80b4-00c04fd430c8', 'Draco', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', NULL, 'Darurat', '2025-03-18 9:20', '2025-03-18 10:50', '33', '6.4'),
	('6ba7b815-9dad-11d1-80b4-00c04fd430c8', 'Puffy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'VAC004', 'Janji Temu', '2025-04-27 8:45', '2025-04-27 9:10', '37', '0.3'),
	('6ba7b816-9dad-11d1-80b4-00c04fd430c8', 'Ginger', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', NULL, 'Walk-In', '2025-05-09 14:00', '2025-05-09 14:50', '37', '3.4'),
	('6ba7b817-9dad-11d1-80b4-00c04fd430c8', 'Quack', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'VAC006', 'Janji Temu', '2025-06-17 9:25', '2025-06-17 9:50', '40', '1.9'),
	('6ba7b818-9dad-11d1-80b4-00c04fd430c8', 'Shadow', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', NULL, 'Janji Temu', '2025-07-28 11:35', '2025-07-28 12:10', '38', '24.1'),
	('6ba7b819-9dad-11d1-80b4-00c04fd430c8', 'Rango', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', NULL, 'Darurat', '2025-08-11 10:45', NULL, '34', '0.45');

INSERT INTO KUNJUNGAN_KEPERAWATAN (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan, catatan) VALUES
	('f47ac10b-58cc-4372-a567-0e02b2c3d479', 'Blacky', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM001', 'Hewan nya dijaga terus ya!'),
	('550e8400-e29b-41d4-a716-446655440000', 'Snowy', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM002', 'Pastikan hewan mendapatkan cukup air dan makanan!'),
	('d3973b2a-5fc2-47d6-8358-1912ad4c4442', 'Coco', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM003', 'Jangan lupa beri obat sesuai jadwal!'),
	('9a33b35c-f3c8-4ca0-8c8c-dcc21e3d15e2', 'Luna', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM004', 'Jaga kebersihan tempat tidur hewan ya!'),
	('b5f8c3d2-e87a-4a1f-bc19-3c6a01837a8b', 'Bubbles', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM005', 'Perhatikan tanda-tanda perubahan perilaku hewan!'),
	('67c6697c-5e3e-4f0a-8d84-b9ffb8302a36', 'Spike', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM001', 'Cek kesehatan gigi hewan secara rutin, ya!'),
	('01234567-89ab-cdef-0123-456789abcdef', 'Bella', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM002', 'Hewan perlu istirahat yang cukup setelah perawatan.'),
	('98765432-10fe-dcba-9876-543210fedcba', 'Sky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM003', 'Pastikan hewan tetap aktif dan bergerak!'),
	('a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6', 'Rocky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM004', 'Jangan biarkan hewan terkena cuaca ekstrem!'),
	('87654321-fedc-ba98-7654-3210fedcba98', 'Kiwi', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM005', 'Pantau selalu perkembangan kondisi kesehatan hewan yaa'),
	('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'Nemo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM001', 'Hewan perlu pemeriksaan rutin setiap 3 bulan sekali.'),
	('6ba7b811-9dad-11d1-80b4-00c04fd430c8', 'Axel', '6ba7b82c-9dad-11d1-80b4-0c04fd430c13', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM002', 'Jangan biarkan hewan menggaruk tubuhnya terlalu keras yaa'),
	('6ba7b812-9dad-11d1-80b4-00c04fd430c8', 'Milo', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM003', 'Jaga kebersihan kulit dan bulu hewan!'),
	('6ba7b813-9dad-11d1-80b4-00c04fd430c8', 'Polly', '6ba7b82c-9dad-11d1-80b4-0c04fd430c14', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM004', 'Pastikan hewan mendapat vaksinasi yang diperlukan yaa'),
	('6ba7b814-9dad-11d1-80b4-00c04fd430c8', 'Draco', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM005', 'Hindari makanan yang dapat menyebabkan alergi pada hewan!'),
	('6ba7b815-9dad-11d1-80b4-00c04fd430c8', 'Puffy', '6ba7b82c-9dad-11d1-80b4-0c04fd430c15', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM001', 'Periksa kuku hewan secara rutin agar hewan tidak melukai dirinya ketika menggaruk tubuhnya.'),
	('6ba7b816-9dad-11d1-80b4-00c04fd430c8', 'Ginger', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM002', 'Jangan biarkan hewan terlalu lama di luar rumah!'),
	('6ba7b817-9dad-11d1-80b4-00c04fd430c8', 'Quack', '6ba7b82c-9dad-11d1-80b4-0c04fd430c16', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM003', 'Pastikan kandang hewan selalu bersih dan kering!'),
	('6ba7b818-9dad-11d1-80b4-00c04fd430c8', 'Shadow', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM004', 'Perhatikan tanda-tanda stress pada hewan!'),
	('6ba7b819-9dad-11d1-80b4-00c04fd430c8', 'Rango', '6ba7b82c-9dad-11d1-80b4-0c04fd430c17', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM005', 'Berikan makanan yang sesuai dengan usia hewan!'),
	('f47ac10b-58cc-4372-a567-0e02b2c3d479', 'Blacky', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM005', 'Lakukan pemeriksaan kesehatan mata hewan secara berkala!'),
	('550e8400-e29b-41d4-a716-446655440000', 'Snowy', '6ba7b82c-9dad-11d1-80b4-00c04fd430c8', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM004', 'Hewan perlu mendapatkan cukup waktu untuk bermain!'),
	('d3973b2a-5fc2-47d6-8358-1912ad4c4442', 'Coco', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM001', 'Jangan biarkan hewan bermain dengan benda berbahaya!'),
	('9a33b35c-f3c8-4ca0-8c8c-dcc21e3d15e2', 'Luna', '6ba7b82c-9dad-11d1-80b4-00c04fd430c9', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM002', 'Periksa telinga hewan secara rutin!'),
	('b5f8c3d2-e87a-4a1f-bc19-3c6a01837a8b', 'Bubbles', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM001', 'Ketika hewan memiliki luka lagi nantinya, kamu segera bawa ke pet clinic yaa'),
	('67c6697c-5e3e-4f0a-8d84-b9ffb8302a36', 'Spike', '6ba7b82c-9dad-11d1-80b4-0c04fd430c10', 'f47ac10b-58cc-4372-a567-0e02b2c3d479', 'f47ac10b-58cc-4372-a567-0e02b2c3d484', 'f47ac10b-58cc-4372-a567-0e02b2c3d489', 'TRM005', 'Hindari kontak hewan dengan hewan lain yang sakit!'),
	('01234567-89ab-cdef-0123-456789abcdef', 'Bella', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d480', 'f47ac10b-58cc-4372-a567-0e02b2c3d485', 'f47ac10b-58cc-4372-a567-0e02b2c3d490', 'TRM004', 'Pastikan hewan mendapatkan perawatan medis jika perlu!'),
	('98765432-10fe-dcba-9876-543210fedcba', 'Sky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c11', 'f47ac10b-58cc-4372-a567-0e02b2c3d481', 'f47ac10b-58cc-4372-a567-0e02b2c3d486', 'f47ac10b-58cc-4372-a567-0e02b2c3d491', 'TRM004', 'Perhatikan tanda-tanda kelelahan pada hewan!'),
	('a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6', 'Rocky', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d482', 'f47ac10b-58cc-4372-a567-0e02b2c3d487', 'f47ac10b-58cc-4372-a567-0e02b2c3d492', 'TRM002', 'Jangan lupa memberikan perawatan gigi hewan secara teratur!'),
	('87654321-fedc-ba98-7654-3210fedcba98', 'Kiwi', '6ba7b82c-9dad-11d1-80b4-0c04fd430c12', 'f47ac10b-58cc-4372-a567-0e02b2c3d483', 'f47ac10b-58cc-4372-a567-0e02b2c3d488', 'f47ac10b-58cc-4372-a567-0e02b2c3d493', 'TRM001', 'Jaga kesehatan mental hewan dengan memberikan stimulasi yang cukup!');