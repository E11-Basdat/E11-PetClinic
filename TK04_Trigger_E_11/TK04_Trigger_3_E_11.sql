-- 1. Trigger untuk validasi timestamp
CREATE OR REPLACE FUNCTION PETCLINIC.validate_kunjungan_timestamp()
RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.timestamp_akhir <= NEW.timestamp_awal THEN
        RAISE EXCEPTION 'ERROR: Timestamp akhir kunjungan tidak boleh lebih awal dari timestamp awal.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_kunjungan_timestamp
BEFORE INSERT OR UPDATE ON PETCLINIC.KUNJUNGAN
FOR EACH ROW
EXECUTE FUNCTION PETCLINIC.validate_kunjungan_timestamp();

-- 2. Trigger untuk validasi kepemilikan hewan
CREATE OR REPLACE FUNCTION PETCLINIC.validate_hewan_ownership()
RETURNS TRIGGER AS
$$
DECLARE
    owner_name TEXT;
BEGIN
    -- Get owner name for error message
    SELECT 
        CASE 
            WHEN i.nama_depan IS NOT NULL THEN 
                CONCAT(i.nama_depan, ' ', COALESCE(i.nama_tengah, ''), ' ', i.nama_belakang)
            WHEN p.nama_perusahaan IS NOT NULL THEN p.nama_perusahaan
            ELSE k.no_identitas
        END
    INTO owner_name
    FROM PETCLINIC.KLIEN k
    LEFT JOIN PETCLINIC.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
    LEFT JOIN PETCLINIC.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
    WHERE k.no_identitas = NEW.no_identitas_klien;

    -- Check if animal exists and belongs to client
    IF NOT EXISTS (
        SELECT 1
        FROM PETCLINIC.HEWAN h
        WHERE h.nama = NEW.nama_hewan
        AND h.no_identitas_klien = NEW.no_identitas_klien
    ) THEN
        RAISE EXCEPTION 'ERROR: Hewan "%" tidak terdaftar atas nama pemilik "%".', 
                       NEW.nama_hewan, 
                       owner_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_hewan_ownership
BEFORE INSERT OR UPDATE ON PETCLINIC.KUNJUNGAN
FOR EACH ROW
EXECUTE FUNCTION PETCLINIC.validate_hewan_ownership();

-- Trigger untuk validasi kepemilikan hewan pada treatment
CREATE OR REPLACE FUNCTION PETCLINIC.validate_treatment_ownership()
RETURNS TRIGGER AS
$$
DECLARE
    owner_name TEXT;
BEGIN
    -- Get owner name for error message
    SELECT 
        CASE 
            WHEN i.nama_depan IS NOT NULL THEN 
                CONCAT(i.nama_depan, ' ', COALESCE(i.nama_tengah, ''), ' ', i.nama_belakang)
            WHEN p.nama_perusahaan IS NOT NULL THEN p.nama_perusahaan
            ELSE k.no_identitas
        END
    INTO owner_name
    FROM PETCLINIC.KLIEN k
    LEFT JOIN PETCLINIC.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
    LEFT JOIN PETCLINIC.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
    WHERE k.no_identitas = NEW.no_identitas_klien;

    -- Check if animal exists and belongs to client
    IF NOT EXISTS (
        SELECT 1
        FROM PETCLINIC.HEWAN h
        WHERE h.nama = NEW.nama_hewan
        AND h.no_identitas_klien = NEW.no_identitas_klien
    ) THEN
        RAISE EXCEPTION 'ERROR: Hewan "%" tidak terdaftar atas nama pemilik "%".', 
                       NEW.nama_hewan, 
                       owner_name;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_treatment_ownership
BEFORE INSERT OR UPDATE ON PETCLINIC.KUNJUNGAN_KEPERAWATAN
FOR EACH ROW
EXECUTE FUNCTION PETCLINIC.validate_treatment_ownership();