-- 1. Pengecekan email (case insensitive)
CREATE OR REPLACE FUNCTION petclinic.check_if_email_exists()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM petclinic."USER" WHERE LOWER(email) = LOWER(NEW.email)) THEN
        RAISE EXCEPTION 'ERROR: Email "%" sudah terdaftar, gunakan email lain.', NEW.email;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER check_email_before_insert
BEFORE INSERT ON petclinic."USER"
FOR EACH ROW
EXECUTE FUNCTION petclinic.check_if_email_exists();

-- 2. Menghapus jadwal praktik dokter jika sudah tidak bekerja
CREATE OR REPLACE FUNCTION petclinic.delete_dokter_schedules()
RETURNS TRIGGER AS $$
DECLARE 
    dokter_email VARCHAR(50);
BEGIN
    IF NEW.tanggal_akhir_kerja IS NOT NULL AND 
       (OLD.tanggal_akhir_kerja IS NULL OR OLD.tanggal_akhir_kerja != NEW.tanggal_akhir_kerja) THEN
        
        IF EXISTS (
            SELECT 1 
            FROM petclinic.DOKTER_HEWAN d 
            WHERE d.no_dokter_hewan = NEW.no_pegawai
        ) THEN
            SELECT u.email INTO dokter_email
            FROM petclinic."USER" u
            WHERE u.email = NEW.email_user;
            
            DELETE FROM petclinic.JADWAL_PRAKTIK
            WHERE no_dokter_hewan = NEW.no_pegawai;
            
            RAISE NOTICE 'INFO: Semua jadwal praktik dokter dengan email "%" telah dihapus karena dokter sudah tidak aktif.', dokter_email;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigg_delete_dokter_schedules
AFTER UPDATE OF tanggal_akhir_kerja ON petclinic.PEGAWAI
FOR EACH ROW
EXECUTE FUNCTION petclinic.delete_dokter_schedules();
