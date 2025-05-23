

-- 1. Memperbarui stok Vaksin saat membuat atau menghapus Vaksinasi
CREATE OR REPLACE FUNCTION check_or_update_vaccine_stock()
RETURNS TRIGGER AS $$
DECLARE
    vaccine_stok INT;
    vaccine_nama VARCHAR;
BEGIN
    IF OLD.kode_vaksin IS NULL AND NEW.kode_vaksin IS NOT NULL THEN
        SELECT stok, nama INTO vaccine_stok, vaccine_nama
        FROM PETCLINIC.VAKSIN
        WHERE kode = NEW.kode_vaksin;
        
        IF vaccine_stok <= 0 THEN
            RAISE EXCEPTION 'ERROR: Stok vaksin "%" tidak mencukupi untuk vaksinasi.', vaccine_nama;
        END IF;
        
        UPDATE PETCLINIC.VAKSIN 
        SET stok = stok - 1 
        WHERE kode = NEW.kode_vaksin;
    
    ELSIF OLD.kode_vaksin IS NOT NULL AND NEW.kode_vaksin IS NOT NULL 
          AND OLD.kode_vaksin != NEW.kode_vaksin THEN
        
        SELECT stok, nama INTO vaccine_stok, vaccine_nama
        FROM PETCLINIC.VAKSIN
        WHERE kode = NEW.kode_vaksin;
        
        IF vaccine_stok <= 0 THEN
            RAISE EXCEPTION 'ERROR: Stok vaksin "%" tidak mencukupi untuk vaksinasi.', vaccine_nama;
        END IF;
        
        UPDATE PETCLINIC.VAKSIN
        SET stok = stok + 1
        WHERE kode = OLD.kode_vaksin;
        
        UPDATE PETCLINIC.VAKSIN
        SET stok = stok - 1
        WHERE kode = NEW.kode_vaksin;
    
    ELSIF OLD.kode_vaksin IS NOT NULL AND NEW.kode_vaksin IS NULL THEN
        
        UPDATE PETCLINIC.VAKSIN
        SET stok = stok + 1
        WHERE kode = OLD.kode_vaksin;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigg_check_or_update_vaccine_stock
BEFORE UPDATE OF kode_vaksin ON PETCLINIC.KUNJUNGAN
FOR EACH ROW
EXECUTE FUNCTION check_or_update_vaccine_stock();


-- 2. Memeriksa penggunaan Vaksin pada Vaksinasi sebelum menghapus Vaksin
CREATE OR REPLACE FUNCTION check_if_vaccine_used()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM PETCLINIC.KUNJUNGAN
        WHERE kode_vaksin = OLD.kode
    ) THEN
        RAISE EXCEPTION 'ERROR: Vaksin tidak dapat dihapus dikarenakan telah digunakan untuk vaksinasi.';
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigg_check_if_vaccine_used
BEFORE DELETE ON PETCLINIC.VAKSIN
FOR EACH ROW
EXECUTE FUNCTION check_if_vaccine_used();