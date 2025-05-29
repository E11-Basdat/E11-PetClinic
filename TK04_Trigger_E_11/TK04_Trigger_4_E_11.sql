-- 1. Trigger untuk validasi total harga prescription tidak melebihi total harga perawatan
CREATE OR REPLACE FUNCTION petclinic.validate_prescription_cost() 
RETURNS TRIGGER AS $$
DECLARE 
    treatment_price INT;
    medicine_price INT;
    current_total_prescription INT := 0;
    new_prescription_cost INT;
BEGIN
    -- Get treatment price from perawatan table
    SELECT biaya_perawatan INTO treatment_price 
    FROM petclinic.perawatan 
    WHERE kode_perawatan = NEW.kode_perawatan;
    
    -- If treatment not found
    IF treatment_price IS NULL THEN
        RAISE EXCEPTION 'ERROR: Treatment code % not found', NEW.kode_perawatan;
    END IF;
    
    -- Get medicine price from obat table
    SELECT harga INTO medicine_price 
    FROM petclinic.obat 
    WHERE kode = NEW.kode_obat;
    
    -- If medicine not found
    IF medicine_price IS NULL THEN
        RAISE EXCEPTION 'ERROR: Medicine code % not found', NEW.kode_obat;
    END IF;
    
    -- Calculate new prescription cost
    new_prescription_cost := medicine_price * NEW.kuantitas_obat;
    
    -- Get current total prescription cost for this treatment (excluding current record if UPDATE)
    SELECT COALESCE(SUM(o.harga * po.kuantitas_obat), 0) INTO current_total_prescription
    FROM petclinic.perawatan_obat po
    JOIN petclinic.obat o ON po.kode_obat = o.kode
    WHERE po.kode_perawatan = NEW.kode_perawatan
    AND (TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND po.kode_obat != OLD.kode_obat));
    
    -- Validate total prescription cost doesn't exceed treatment cost
    IF (current_total_prescription + new_prescription_cost) > treatment_price THEN
        RAISE EXCEPTION 'ERROR: Total harga obat (%) melebihi total harga perawatan (%). Mohon sesuaikan resep obat.', 
                       (current_total_prescription + new_prescription_cost), treatment_price;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on perawatan_obat table
CREATE TRIGGER check_prescription_cost
    BEFORE INSERT OR UPDATE ON petclinic.perawatan_obat
    FOR EACH ROW EXECUTE FUNCTION petclinic.validate_prescription_cost();

-- 2. Trigger untuk validasi dan update stok obat otomatis
CREATE OR REPLACE FUNCTION petclinic.validate_and_update_medicine_stock() 
RETURNS TRIGGER AS $$
DECLARE 
    current_stock INT;
    medicine_name VARCHAR(100);
    stock_difference INT := 0;
BEGIN
    -- Get current stock and medicine name from obat table
    SELECT stok, nama INTO current_stock, medicine_name 
    FROM petclinic.obat 
    WHERE kode = NEW.kode_obat;
    
    -- Check if medicine exists
    IF current_stock IS NULL THEN
        RAISE EXCEPTION 'ERROR: Medicine code % not found', NEW.kode_obat;
    END IF;
    
    -- Calculate stock difference needed
    IF TG_OP = 'INSERT' THEN
        stock_difference := NEW.kuantitas_obat;
    ELSIF TG_OP = 'UPDATE' THEN
        stock_difference := NEW.kuantitas_obat - OLD.kuantitas_obat;
    END IF;
    
    -- Validate stock availability
    IF current_stock < stock_difference THEN
        RAISE EXCEPTION 'ERROR: Stok obat "%" tidak mencukupi untuk jumlah % unit. Stok tersedia: % unit.', 
                       medicine_name, stock_difference, current_stock;
    END IF;
    
    -- Update stock automatically
    UPDATE petclinic.obat 
    SET stok = stok - stock_difference 
    WHERE kode = NEW.kode_obat;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_update_medicine_stock
    BEFORE INSERT OR UPDATE ON petclinic.perawatan_obat
    FOR EACH ROW EXECUTE FUNCTION petclinic.validate_and_update_medicine_stock();

-- 3. Trigger untuk restore stok obat saat prescription dihapus
CREATE OR REPLACE FUNCTION petclinic.restore_medicine_stock() 
RETURNS TRIGGER AS $$
BEGIN
    -- Restore stock when prescription is deleted
    UPDATE petclinic.obat 
    SET stok = stok + OLD.kuantitas_obat 
    WHERE kode = OLD.kode_obat;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER restore_medicine_stock_on_delete
    AFTER DELETE ON petclinic.perawatan_obat
    FOR EACH ROW EXECUTE FUNCTION petclinic.restore_medicine_stock();