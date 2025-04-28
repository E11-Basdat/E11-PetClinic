from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

def generate_kunjungan_id():
    # Menghasilkan UUID baru untuk ID kunjungan
    return str(uuid.uuid4())

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    try:
        with connection.cursor() as cursor:
            logger.debug(f"Executing SQL: {query}")
            logger.debug(f"With parameters: {params}")
            cursor.execute(query, params or [])
            
            if cursor.rowcount >= 0:
                logger.debug(f"Query affected {cursor.rowcount} rows")
            
            if fetch_one:
                result = cursor.fetchone()
                logger.debug(f"Fetched one result: {result}")
                return result
            if fetch_all:
                result = cursor.fetchall()
                logger.debug(f"Fetched {len(result)} results")
                return result
            
            # Pastikan transaksi di-commit
            connection.commit()
            logger.debug("Transaction committed successfully")
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        # Log stack trace juga
        import traceback
        logger.error(traceback.format_exc())
        # Rollback transaksi jika terjadi error
        connection.rollback()
        logger.debug("Transaction rolled back due to error")
        raise
    
def test_connection(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_schema()")
            result = cursor.fetchone()
            return JsonResponse({
                'status': 'connected',
                'database': result[0],
                'schema': result[1],
                'connection_details': str(connection)
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def create_medical_record(request, id_kunjungan):
    # Validasi apakah user adalah Dokter Hewan
    if request.session.get('user_type') != 'dokter':
        messages.error(request, 'Hanya Dokter Hewan yang dapat membuat rekam medis.')
        return redirect('visits:list_visits')

    if request.method == 'POST':
        suhu = request.POST.get('suhu')
        berat_badan = request.POST.get('berat_badan')
        kode_vaksin = request.POST.get('kode_vaksin')  # Jika ada input kode vaksin
        catatan = request.POST.get('catatan')

        try:
            # Perbarui data suhu, berat badan, kode vaksin, dan catatan di tabel KUNJUNGAN
            query_update = """
                UPDATE petclinic.KUNJUNGAN
                SET suhu = %s, berat_badan = %s, kode_vaksin = %s, catatan = %s
                WHERE id_kunjungan = %s
            """
            params_update = [suhu, berat_badan, kode_vaksin, catatan, id_kunjungan]
            execute_query(query_update, params_update)

            messages.success(request, 'Rekam Medis berhasil dibuat dan data kunjungan diperbarui.')
            return redirect('visits:list_visits')

        except Exception as e:
            messages.error(request, f'Gagal membuat rekam medis: {str(e)}')
            return redirect('visits:create_medical_record', id_kunjungan=id_kunjungan)

    # Ambil data kode vaksin untuk dropdown
    query_vaksin = "SELECT kode, nama FROM petclinic.VAKSIN"
    daftar_vaksin = execute_query(query_vaksin, fetch_all=True)

    return render(request, 'create_medical_record.html', {
        'id_kunjungan': id_kunjungan,
        'daftar_vaksin': daftar_vaksin
    })
    
def list_visits(request):
    query = """
        SELECT 
            id_kunjungan, 
            no_identitas_klien, 
            nama_hewan, 
            tipe_kunjungan, 
            timestamp_awal, 
            timestamp_akhir
        FROM petclinic.KUNJUNGAN
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        visits = cursor.fetchall()
    return render(request, 'list.html', {'visits': visits})  #
import uuid
import logging
logger = logging.getLogger(__name__)
def create_visit(request):
    logger.debug(f"Session data")
    if request.method == 'POST':
        try:
            # Ambil data dari form
            no_identitas_klien = request.POST.get('no_identitas_klien')
            nama_hewan = request.POST.get('nama_hewan')
            tipe_kunjungan = request.POST.get('tipe_kunjungan')
            timestamp_awal = request.POST.get('timestamp_awal')
            timestamp_akhir = request.POST.get('timestamp_akhir')
            no_dokter = request.POST.get('dokter')
            no_perawat = request.POST.get('perawat')

            # Ambil no_front_desk dari session
            no_front_desk = request.session.get('employee_id')
            if not no_front_desk:
                messages.error(request, 'Anda tidak memiliki akses untuk membuat kunjungan.')
                return redirect('visits:list_visits')

            # Generate ID kunjungan
            id_kunjungan = generate_kunjungan_id()

            # Buat query dan parameters
            query = """
                INSERT INTO petclinic.KUNJUNGAN (
                    id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                    no_dokter_hewan, no_perawat_hewan, tipe_kunjungan, timestamp_awal, timestamp_akhir
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = [
                id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk,
                no_dokter, no_perawat, tipe_kunjungan, timestamp_awal, timestamp_akhir
            ]

            # Eksekusi query
            execute_query(query, params)
            messages.success(request, 'Kunjungan berhasil dibuat.')
            return redirect('visits:list_visits')

        except Exception as e:
            logger.error(f"Gagal membuat kunjungan: {str(e)}")
            messages.error(request, f'Gagal membuat kunjungan: {str(e)}')
            return redirect('visits:create_visit')

    # GET request: tampilkan form
    try:
        query_klien = "SELECT no_identitas, email FROM petclinic.KLIEN"
        query_hewan = "SELECT nama, no_identitas_klien FROM petclinic.HEWAN"
        query_dokter = """
            SELECT d.no_dokter_hewan, pg.email_user 
            FROM petclinic.DOKTER_HEWAN d
            JOIN petclinic.PEGAWAI pg ON d.no_dokter_hewan = pg.no_pegawai
        """
        query_perawat = """
            SELECT p.no_perawat_hewan, pg.email_user 
            FROM petclinic.PERAWAT_HEWAN p
            JOIN petclinic.PEGAWAI pg ON p.no_perawat_hewan = pg.no_pegawai
        """

        klien = execute_query(query_klien, fetch_all=True)
        hewan = execute_query(query_hewan, fetch_all=True)
        dokter = execute_query(query_dokter, fetch_all=True)
        perawat = execute_query(query_perawat, fetch_all=True)

    except Exception as e:
        logger.error(f"Error fetching data for dropdowns: {str(e)}")
        messages.error(request, f"Gagal memuat data: {str(e)}")
        return redirect('visits:list_visits')

    return render(request, 'create.html', {
        'klien': klien,
        'hewan': hewan,
        'dokter': dokter,
        'perawat': perawat
    })
    
# Update an existing visit
def update_visit(request, visit_id):
    if request.method == 'POST':
        nama_hewan = request.POST.get('nama_hewan')
        tipe_kunjungan = request.POST.get('tipe_kunjungan')
        timestamp_awal = request.POST.get('timestamp_awal')
        timestamp_akhir = request.POST.get('timestamp_akhir')
        suhu = request.POST.get('suhu')
        berat_badan = request.POST.get('berat_badan')

        query = """
            UPDATE petclinic.KUNJUNGAN
            SET nama_hewan = %s, tipe_kunjungan = %s, timestamp_awal = %s, 
                timestamp_akhir = %s, suhu = %s, berat_badan = %s
            WHERE id_kunjungan = %s
        """
        params = [nama_hewan, tipe_kunjungan, timestamp_awal, timestamp_akhir, suhu, berat_badan, visit_id]
        execute_query(query, params)
        messages.success(request, 'Kunjungan berhasil diperbarui.')
        return redirect('visits:list_visits')

    query = "SELECT * FROM petclinic.KUNJUNGAN WHERE id_kunjungan = %s"
    visit = execute_query(query, [visit_id], fetch_one=True)
    return render(request, 'update.html', {'visit': visit})

# Delete a visit
def delete_visit(request, visit_id):
    if request.method == 'POST':
        query = "DELETE FROM petclinic.KUNJUNGAN WHERE id_kunjungan = %s"
        execute_query(query, [visit_id])
        messages.success(request, 'Kunjungan berhasil dihapus.')
        return redirect('visits:list_visits')

    query = "SELECT * FROM petclinic.KUNJUNGAN WHERE id_kunjungan = %s"
    visit = execute_query(query, [visit_id], fetch_one=True)
    return render(request, 'visits/delete_confirmation.html', {'visit': visit})

# List all medical records
def list_medical_records(request):
    query = """
        SELECT id_kunjungan, kode_perawatan, catatan
        FROM petclinic.KUNJUNGAN_KEPERAWATAN
    """
    medical_records = execute_query(query, fetch_all=True)
    return render(request, 'visits/medical_records/list.html', {'medical_records': medical_records})

from django.http import JsonResponse

def check_medical_record(request, id_kunjungan):
    query = """
        SELECT id_kunjungan, kode_perawatan, catatan
        FROM petclinic.KUNJUNGAN_KEPERAWATAN
        WHERE id_kunjungan = %s
    """
    medical_record = execute_query(query, [id_kunjungan], fetch_one=True)

    if medical_record:
        return JsonResponse({
            'exists': True,
            'data': {
                'id_kunjungan': medical_record[0],
                'kode_perawatan': medical_record[1],
                'catatan': medical_record[2],
            }
        })
    else:
        return JsonResponse({'exists': False})