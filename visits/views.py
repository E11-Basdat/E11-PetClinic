from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

def generate_kunjungan_id():
    query = "SELECT id_kunjungan FROM petclinic.KUNJUNGAN ORDER BY id_kunjungan DESC LIMIT 1"
    last_id = execute_query(query, fetch_one=True)

    if last_id and last_id[0].startswith('VISIT') and last_id[0][5:].isdigit():
        # Ambil angka terakhir dari ID kunjungan sebelumnya
        last_number = int(last_id[0][5:])  # Mengambil angka setelah "VISIT"
        new_number = last_number + 1
    else:
        # Jika belum ada data atau format ID tidak sesuai, mulai dari 1
        new_number = 1

    # Format ID baru dengan prefix "VISIT" dan padding angka menjadi 2 digit
    return f"VISIT{new_number:02d}"

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()

def create_medical_record(request, id_kunjungan):
    # Validasi apakah user adalah Dokter Hewan
    if request.session.get('user_type') != 'dokter':
        messages.error(request, 'Hanya Dokter Hewan yang dapat membuat rekam medis.')
        return redirect('visits:list_visits')

    if request.method == 'POST':
        kode_perawatan = request.POST.get('kode_perawatan')
        suhu = request.POST.get('suhu')
        berat_badan = request.POST.get('berat_badan')
        catatan = request.POST.get('catatan')

        query = """
            INSERT INTO petclinic.KUNJUNGAN_KEPERAWATAN (
                id_kunjungan, kode_perawatan, catatan
            ) VALUES (%s, %s, %s)
        """
        params = [id_kunjungan, kode_perawatan, catatan]
        execute_query(query, params)
        messages.success(request, 'Rekam Medis berhasil dibuat.')
        return redirect('visits:list_visits')

    # Ambil data jenis perawatan untuk dropdown
    query_perawatan = "SELECT kode_perawatan, nama_perawatan FROM petclinic.PERAWATAN"
    jenis_perawatan = execute_query(query_perawatan, fetch_all=True)

    return render(request, 'visits/create_medical_record.html', {
        'id_kunjungan': id_kunjungan,
        'jenis_perawatan': jenis_perawatan
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
    return render(request, 'list.html', {'visits': visits})

import logging
logger = logging.getLogger(__name__)

def create_visit(request):
    logger.debug(f"POST Data: {request.POST}")
    if request.method == 'POST':
        no_identitas_klien = request.POST.get('no_identitas_klien')
        nama_hewan = request.POST.get('nama_hewan')
        tipe_kunjungan = request.POST.get('tipe_kunjungan')
        timestamp_awal = request.POST.get('timestamp_awal')
        timestamp_akhir = request.POST.get('timestamp_akhir')

        # Ambil no_front_desk dari session
        no_front_desk = request.session.get('no_front_desk')
        if not no_front_desk:
            messages.error(request, 'Anda tidak memiliki akses untuk membuat kunjungan.')
            return redirect('visits:list_visits')

        # Generate ID kunjungan baru
        id_kunjungan = generate_kunjungan_id()

        query = """
            INSERT INTO petclinic.KUNJUNGAN (
                id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                no_perawat_hewan, no_dokter_hewan, tipe_kunjungan, 
                timestamp_awal, timestamp_akhir
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
            request.POST.get('no_perawat_hewan'), request.POST.get('no_dokter_hewan'), 
            tipe_kunjungan, timestamp_awal, timestamp_akhir
        ]
        logger.debug(f"Query: {query}")
        logger.debug(f"Params: {params}")
        execute_query(query, params)
        messages.success(request, 'Kunjungan berhasil dibuat.')
        return redirect('visits:list_visits')

    # Ambil data klien dan hewan untuk dropdown
    query_klien = "SELECT no_identitas, email FROM petclinic.KLIEN"
    query_hewan = "SELECT nama, no_identitas_klien FROM petclinic.HEWAN"
    query_perawat = "SELECT no_perawat_hewan, nama FROM petclinic.PERAWAT_HEWAN"
    query_dokter = "SELECT no_dokter_hewan, nama FROM petclinic.DOKTER_HEWAN"
    perawat_hewan = execute_query(query_perawat, fetch_all=True)
    dokter_hewan = execute_query(query_dokter, fetch_all=True)
    klien = execute_query(query_klien, fetch_all=True)
    hewan = execute_query(query_hewan, fetch_all=True)
    
    return render(request, 'create.html', {
        'klien': klien,
        'hewan': hewan,
        'perawat_hewan': perawat_hewan,
        'dokter_hewan': dokter_hewan
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
    return render(request, 'visits/update.html', {'visit': visit})

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