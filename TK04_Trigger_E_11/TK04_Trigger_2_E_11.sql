-- 1.  Trigger untuk mencegah duplikasi nama jenis pada Jenis Hewan
CREATE OR REPLACE FUNCTION petclinic.f_check_unique_jenis_hewan()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_id UUID;
BEGIN
    /* Cari baris lain (case-insensitive) yang sudah punya nama sama */
    SELECT id
      INTO v_id
      FROM petclinic.jenis_hewan                 -- ← pakai skema
     WHERE LOWER(nama_jenis) = LOWER(NEW.nama_jenis)
     LIMIT 1;

    /*  INSERT : tolak jika ada baris mana pun      */
    /*  UPDATE : tolak jika id baris lain ≠ NEW.id  */
    IF v_id IS NOT NULL AND (TG_OP = 'INSERT' OR v_id <> NEW.id) THEN
        RAISE EXCEPTION USING
          MESSAGE = format(
            'ERROR: Jenis hewan "%s" sudah terdaftar dengan ID %s.',
            NEW.nama_jenis, v_id
          ),
          ERRCODE = 'unique_violation';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_check_unique_jenis_hewan
  ON petclinic.jenis_hewan;

CREATE TRIGGER trg_check_unique_jenis_hewan
BEFORE INSERT OR UPDATE
ON petclinic.jenis_hewan
FOR EACH ROW
EXECUTE FUNCTION petclinic.f_check_unique_jenis_hewan();

-- 2.  Trigger untuk mencegah penghapusan Hewan Peliharaan jika masih memiliki kunjungan aktif
CREATE OR REPLACE FUNCTION petclinic.f_prevent_delete_active_pet()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_jumlah   INTEGER;
    v_pemilik  TEXT;
BEGIN
    /* Hitung kunjungan aktif (timestamp_akhir = NULL) */
    SELECT COUNT(*)
      INTO v_jumlah
      FROM petclinic.kunjungan
     WHERE nama_hewan         = OLD.nama
       AND no_identitas_klien = OLD.no_identitas_klien
       AND timestamp_akhir   IS NULL;

    IF v_jumlah > 0 THEN
        /* Ambil nama lengkap / perusahaan pemilik */
        SELECT COALESCE(
                 i.nama_depan || ' ' ||
                 COALESCE(i.nama_tengah || ' ', '') ||
                 i.nama_belakang,
                 p.nama_perusahaan
               )
          INTO v_pemilik
          FROM petclinic.klien k
     LEFT JOIN petclinic.individu   i ON k.no_identitas = i.no_identitas_klien
     LEFT JOIN petclinic.perusahaan p ON k.no_identitas = p.no_identitas_klien
         WHERE k.no_identitas = OLD.no_identitas_klien;

        RAISE EXCEPTION USING
          MESSAGE = format('ERROR: Hewan "%s" milik "%s" masih memiliki kunjungan aktif sehingga tidak dapat dihapus.', OLD.nama, v_pemilik),
          ERRCODE = 'modifying_sql_data_not_permitted';
    END IF;

    RETURN OLD;   -- row-level BEFORE DELETE wajib RETURN OLD
END;
$$;

DROP TRIGGER IF EXISTS trg_prevent_delete_active_pet
  ON petclinic.hewan;

CREATE TRIGGER trg_prevent_delete_active_pet
BEFORE DELETE
ON petclinic.hewan
FOR EACH ROW
EXECUTE FUNCTION petclinic.f_prevent_delete_active_pet();