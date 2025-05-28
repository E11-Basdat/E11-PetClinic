# views.py
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.http import JsonResponse
import uuid
from datetime import datetime

# Add this to views.py

def get_perawatan_options(request):
    """API endpoint to get all perawatan options"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT kode_perawatan, nama_perawatan 
                FROM PETCLINIC.PERAWATAN
                ORDER BY nama_perawatan
            """)
            perawatan = dictfetchall(cursor)
        
        return JsonResponse(perawatan, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def visit_list_fd(request):
    user_role = request.GET.get('role', 'front-desk')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    k.id_kunjungan, 
                    k.no_identitas_klien, 
                    k.nama_hewan,
                    k.tipe_kunjungan, 
                    k.timestamp_awal, 
                    k.timestamp_akhir,
                    k.suhu, 
                    k.berat_badan,
                    k.catatan,
                    kk.kode_perawatan,
                    p.nama_perawatan
                FROM PETCLINIC.KUNJUNGAN k
                LEFT JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                    AND k.nama_hewan = kk.nama_hewan
                    AND k.no_identitas_klien = kk.no_identitas_klien
                LEFT JOIN PETCLINIC.PERAWATAN p
                    ON kk.kode_perawatan = p.kode_perawatan
                ORDER BY k.timestamp_awal DESC
            """)
            visits = dictfetchall(cursor)

        from django.core.serializers.json import DjangoJSONEncoder
        import json
        
        visits_json = json.dumps(visits, cls=DjangoJSONEncoder)

        return render(request, 'list.html', {
            'visits': visits_json,
            'user_role': user_role
        })

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return render(request, 'list.html', {
            'visits': '[]',
            'user_role': user_role
        })
        
def visit_list_doctor(request):
    user_role = request.GET.get('role', 'doctor')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    k.id_kunjungan, 
                    k.no_identitas_klien, 
                    k.nama_hewan,
                    k.tipe_kunjungan, 
                    k.timestamp_awal, 
                    k.timestamp_akhir,
                    k.suhu, 
                    k.berat_badan,
                    k.catatan,
                    p.nama_perawatan
                FROM PETCLINIC.KUNJUNGAN k
                LEFT JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                    AND k.nama_hewan = kk.nama_hewan
                    AND k.no_identitas_klien = kk.no_identitas_klien
                LEFT JOIN PETCLINIC.PERAWATAN p
                    ON kk.kode_perawatan = p.kode_perawatan
                ORDER BY k.timestamp_awal DESC
            """)
            visits = dictfetchall(cursor)

        from django.core.serializers.json import DjangoJSONEncoder
        import json
        
        visits_json = json.dumps(visits, cls=DjangoJSONEncoder)

        return render(request, 'list.html', {
            'visits': visits_json,
            'user_role': user_role
        })

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return render(request, 'list.html', {
            'visits': '[]',
            'user_role': user_role
        })

def update_visit(request, visit_id):
    if request.method == 'POST':
        try:
            nama_hewan = request.POST.get('nama_hewan')
            no_identitas_klien = request.POST.get('id_klien')
            tipe_kunjungan = request.POST.get('metode_kunjungan')
            timestamp_awal = request.POST.get('waktu_mulai')
            timestamp_akhir = request.POST.get('waktu_selesai')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE PETCLINIC.KUNJUNGAN
                    SET nama_hewan = %s, no_identitas_klien = %s, tipe_kunjungan = %s,
                        timestamp_awal = %s, timestamp_akhir = %s
                    WHERE id_kunjungan = %s
                """, [nama_hewan, no_identitas_klien, tipe_kunjungan, 
                      timestamp_awal, timestamp_akhir, visit_id])
                
            messages.success(request, 'Kunjungan berhasil diupdate!')
            return redirect('visits:list')
        
        except Exception as e:
            messages.error(request, f'Error updating visit: {str(e)}')
            return redirect('visits:update_visit', visit_id=visit_id)
    
    else:
        with connection.cursor() as cursor:
            # Get visit data
            cursor.execute("""
                SELECT id_kunjungan, no_identitas_klien, nama_hewan, tipe_kunjungan,
                       timestamp_awal, timestamp_akhir
                FROM PETCLINIC.KUNJUNGAN
                WHERE id_kunjungan = %s
            """, [visit_id])
            visit = dictfetchall(cursor)[0] if cursor.rowcount > 0 else None
            
            # Get all clients for dropdown
            cursor.execute("""
                SELECT no_identitas 
                FROM PETCLINIC.KLIEN
                ORDER BY no_identitas
            """)
            clients = dictfetchall(cursor)
            
            # Get animals for selected client
            cursor.execute("""
                SELECT DISTINCT nama 
                FROM PETCLINIC.HEWAN
                WHERE no_identitas_klien = %s
            """, [visit['no_identitas_klien']])
            animals = dictfetchall(cursor)
    
        return render(request, 'update.html', {
            'visit': visit,
            'clients': clients,
            'animals': animals
        })

from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
import uuid

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def create_visit(request):
    if request.method == 'POST':
        try:
            visit_id = str(uuid.uuid4())
            nama_hewan = request.POST.get('nama_hewan')
            no_identitas_klien = request.POST.get('id_klien')
            email_dokter = request.POST.get('email_dokter')
            email_perawat = request.POST.get('email_perawat')
            tipe_kunjungan = request.POST.get('metode_kunjungan')
            timestamp_awal = request.POST.get('waktu_mulai')
            timestamp_akhir = request.POST.get('waktu_selesai')
            catatan = request.POST.get('catatan', '')  # Optional field
            
            # Validate required fields
            if not all([nama_hewan, no_identitas_klien, email_dokter, email_perawat, 
                       tipe_kunjungan, timestamp_awal, timestamp_akhir]):
                messages.error(request, 'Semua field wajib harus diisi!')
                return redirect('visits:create_visit')
            
            # Validate time range
            try:
                start_time = datetime.fromisoformat(timestamp_awal.replace('T', ' '))
                end_time = datetime.fromisoformat(timestamp_akhir.replace('T', ' '))
                
                if end_time <= start_time:
                    messages.error(request, 'Waktu selesai harus setelah waktu mulai!')
                    return redirect('visits:create_visit')
                    
            except ValueError:
                messages.error(request, 'Format waktu tidak valid!')
                return redirect('visits:create_visit')
            
            with connection.cursor() as cursor:
                # Get front desk (first available)
                cursor.execute("""
                    SELECT fd.no_front_desk 
                    FROM PETCLINIC.FRONT_DESK fd
                    INNER JOIN PETCLINIC.PEGAWAI p ON fd.no_front_desk = p.no_pegawai
                    WHERE p.tanggal_akhir_kerja IS NULL
                    LIMIT 1
                """)
                front_desk_result = cursor.fetchone()
                if not front_desk_result:
                    messages.error(request, 'Tidak ada front desk yang tersedia!')
                    return redirect('visits:create_visit')
                front_desk = front_desk_result[0]
                
                # Get nurse by email (through USER table)
                cursor.execute("""
                    SELECT ph.no_perawat_hewan 
                    FROM PETCLINIC.PERAWAT_HEWAN ph
                    INNER JOIN PETCLINIC.TENAGA_MEDIS tm ON ph.no_perawat_hewan = tm.no_tenaga_medis
                    INNER JOIN PETCLINIC.PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
                    INNER JOIN PETCLINIC."USER" u ON p.email_user = u.email
                    WHERE u.email = %s AND p.tanggal_akhir_kerja IS NULL
                """, [email_perawat])
                nurse_result = cursor.fetchone()
                if not nurse_result:
                    messages.error(request, 'Perawat dengan email tersebut tidak ditemukan atau tidak aktif!')
                    return redirect('visits:create_visit')
                nurse = nurse_result[0]
                
                # Get doctor by email (through USER table)
                cursor.execute("""
                    SELECT dh.no_dokter_hewan 
                    FROM PETCLINIC.DOKTER_HEWAN dh
                    INNER JOIN PETCLINIC.TENAGA_MEDIS tm ON dh.no_dokter_hewan = tm.no_tenaga_medis
                    INNER JOIN PETCLINIC.PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
                    INNER JOIN PETCLINIC."USER" u ON p.email_user = u.email
                    WHERE u.email = %s AND p.tanggal_akhir_kerja IS NULL
                """, [email_dokter])
                doctor_result = cursor.fetchone()
                if not doctor_result:
                    messages.error(request, 'Dokter hewan dengan email tersebut tidak ditemukan atau tidak aktif!')
                    return redirect('visits:create_visit')
                doctor = doctor_result[0]
                
                # Check if client exists
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM PETCLINIC.KLIEN 
                    WHERE no_identitas = %s
                """, [no_identitas_klien])
                if cursor.fetchone()[0] == 0:
                    messages.error(request, 'Klien dengan ID tersebut tidak ditemukan!')
                    return redirect('visits:create_visit')
                
                # Check if animal belongs to client
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM PETCLINIC.HEWAN 
                    WHERE nama = %s AND no_identitas_klien = %s
                """, [nama_hewan, no_identitas_klien])
                if cursor.fetchone()[0] == 0:
                    messages.error(request, 'Hewan tersebut tidak terdaftar untuk klien yang dipilih!')
                    return redirect('visits:create_visit')
                
                # Check for scheduling conflicts for doctor
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM PETCLINIC.KUNJUNGAN 
                    WHERE no_dokter_hewan = %s 
                    AND (
                        (timestamp_awal <= %s AND timestamp_akhir > %s) OR
                        (timestamp_awal < %s AND timestamp_akhir >= %s) OR
                        (timestamp_awal >= %s AND timestamp_akhir <= %s)
                    )
                """, [doctor, timestamp_awal, timestamp_awal, timestamp_akhir, timestamp_akhir, 
                     timestamp_awal, timestamp_akhir])
                
                if cursor.fetchone()[0] > 0:
                    messages.warning(request, 'Dokter hewan sudah memiliki jadwal pada waktu tersebut!')
                    # You can choose to continue or return based on business rules
                
                # Insert the new visit with catatan
                cursor.execute("""
                    INSERT INTO PETCLINIC.KUNJUNGAN (
                        id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk,
                        no_perawat_hewan, no_dokter_hewan, tipe_kunjungan, 
                        timestamp_awal, timestamp_akhir, catatan
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    visit_id, nama_hewan, no_identitas_klien, front_desk,
                    nurse, doctor, tipe_kunjungan, timestamp_awal, timestamp_akhir, catatan
                ])
            
            messages.success(request, f'Kunjungan berhasil dibuat dengan ID: {visit_id}')
            return redirect('visits:list')
        
        except Exception as e:
            messages.error(request, f'Error creating visit: {str(e)}')
            return redirect('visits:create_visit')
    
    else:
        # GET request - show form
        with connection.cursor() as cursor:
            # Get all clients for dropdown
            cursor.execute("""
                SELECT no_identitas 
                FROM PETCLINIC.KLIEN
                ORDER BY no_identitas
            """)
            clients = dictfetchall(cursor)
            
            # Get all active doctors with email and name (through proper joins)
            cursor.execute("""
                SELECT u.email, 
                       CASE 
                           WHEN i.nama_depan IS NOT NULL THEN 
                               CONCAT(COALESCE(i.nama_depan, ''), ' ', 
                                     COALESCE(i.nama_tengah, ''), ' ', 
                                     COALESCE(i.nama_belakang, ''))
                           WHEN per.nama_perusahaan IS NOT NULL THEN per.nama_perusahaan
                           ELSE u.email
                       END as nama
                FROM PETCLINIC.DOKTER_HEWAN dh
                INNER JOIN PETCLINIC.TENAGA_MEDIS tm ON dh.no_dokter_hewan = tm.no_tenaga_medis
                INNER JOIN PETCLINIC.PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
                INNER JOIN PETCLINIC."USER" u ON p.email_user = u.email
                LEFT JOIN PETCLINIC.INDIVIDU i ON p.no_pegawai = i.no_identitas_klien
                LEFT JOIN PETCLINIC.PERUSAHAAN per ON p.no_pegawai = per.no_identitas_klien
                WHERE p.tanggal_akhir_kerja IS NULL
                ORDER BY nama
            """)
            doctors = dictfetchall(cursor)
            
            # Get all active nurses with email and name (through proper joins)
            cursor.execute("""
                SELECT u.email, 
                       CASE 
                           WHEN i.nama_depan IS NOT NULL THEN 
                               CONCAT(COALESCE(i.nama_depan, ''), ' ', 
                                     COALESCE(i.nama_tengah, ''), ' ', 
                                     COALESCE(i.nama_belakang, ''))
                           WHEN per.nama_perusahaan IS NOT NULL THEN per.nama_perusahaan
                           ELSE u.email
                       END as nama
                FROM PETCLINIC.PERAWAT_HEWAN ph
                INNER JOIN PETCLINIC.TENAGA_MEDIS tm ON ph.no_perawat_hewan = tm.no_tenaga_medis
                INNER JOIN PETCLINIC.PEGAWAI p ON tm.no_tenaga_medis = p.no_pegawai
                INNER JOIN PETCLINIC."USER" u ON p.email_user = u.email
                LEFT JOIN PETCLINIC.INDIVIDU i ON p.no_pegawai = i.no_identitas_klien
                LEFT JOIN PETCLINIC.PERUSAHAAN per ON p.no_pegawai = per.no_identitas_klien
                WHERE p.tanggal_akhir_kerja IS NULL
                ORDER BY nama
            """)
            nurses = dictfetchall(cursor)
            
        return render(request, 'create.html', {
            'clients': clients,
            'doctors': doctors,
            'nurses': nurses
        })


# Helper function for the AJAX endpoint to get animals
def get_animals_by_client(request):
    client_id = request.GET.get('client_id')
    
    if not client_id:
        return JsonResponse({'animals': []})
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT h.nama, jh.nama_jenis
                FROM PETCLINIC.HEWAN h
                INNER JOIN PETCLINIC.JENIS_HEWAN jh ON h.id_jenis = jh.id_jenis
                WHERE h.no_identitas_klien = %s
                ORDER BY h.nama
            """, [client_id])
            
            animals = []
            for row in cursor.fetchall():
                animals.append({
                    'nama': row[0],

                })
                
        return JsonResponse({'animals': animals})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
def delete_visit(request):
    try:
        data = json.loads(request.body)
        visit_id = data.get('visit_id')
        
        with connection.cursor() as cursor:
            # First delete associated medical records
            cursor.execute("""
                DELETE FROM PETCLINIC.KUNJUNGAN_KEPERAWATAN
                WHERE id_kunjungan = %s
            """, [visit_id])
            
            # Then delete the visit
            cursor.execute("""
                DELETE FROM PETCLINIC.KUNJUNGAN
                WHERE id_kunjungan = %s
            """, [visit_id])
            
            if cursor.rowcount > 0:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Visit not found'
                }, status=404)
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_medical_record(request):
    visit_id = request.GET.get('visit_id')
    animal_name = request.GET.get('animal_name')
    client_id = request.GET.get('client_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT k.suhu, k.berat_badan, k.catatan,
                       kk.kode_perawatan, p.nama_perawatan
                FROM PETCLINIC.KUNJUNGAN k
                LEFT JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                    AND k.nama_hewan = kk.nama_hewan
                    AND k.no_identitas_klien = kk.no_identitas_klien
                LEFT JOIN PETCLINIC.PERAWATAN p 
                    ON kk.kode_perawatan = p.kode_perawatan
                WHERE k.id_kunjungan = %s
                AND k.nama_hewan = %s
                AND k.no_identitas_klien = %s
            """, [visit_id, animal_name, client_id])
            
            results = dictfetchall(cursor)
            
            if results and (results[0]['suhu'] is not None or 
                           results[0]['berat_badan'] is not None or 
                           results[0]['catatan'] is not None):
                record = results[0]
                return JsonResponse({
                    'exists': True,
                    'data': {
                        'suhu': f"{record['suhu']}°C" if record['suhu'] else None,
                        'berat': f"{record['berat_badan']} kg" if record['berat_badan'] else None,
                        'catatan': record['catatan'],
                    }
                })
            else:
                return JsonResponse({'exists': False})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def create_record(request):
    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        animal_name = request.POST.get('animal_name')
        client_id = request.POST.get('client_id')
        suhu = request.POST.get('suhu')
        berat = request.POST.get('berat')
        catatan = request.POST.get('catatan')
        
        try:
            with connection.cursor() as cursor:
                # Update visit with medical data including catatan
                cursor.execute("""
                    UPDATE PETCLINIC.KUNJUNGAN
                    SET suhu = %s, berat_badan = %s, catatan = %s
                    WHERE id_kunjungan = %s
                    AND nama_hewan = %s
                    AND no_identitas_klien = %s
                """, [suhu, berat, catatan, visit_id, animal_name, client_id])
                
                # Add treatment record (without catatan since it's now in KUNJUNGAN)
                # Insert new treatment record (tanpa kolom kode_keperawatan)
                cursor.execute("""
                    INSERT INTO PETCLINIC.KUNJUNGAN_KEPERAWATAN (
                        id_kunjungan, nama_hewan, no_identitas_klien,
                        no_front_desk, no_perawat_hewan, no_dokter_hewan
                    )
                    SELECT %s, %s, %s, no_front_desk, no_perawat_hewan, no_dokter_hewan
                    FROM PETCLINIC.KUNJUNGAN
                    WHERE id_kunjungan = %s
                """, [visit_id, animal_name, client_id, visit_id])

            
            return JsonResponse({'success': True})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
def update_record(request):
    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        animal_name = request.POST.get('animal_name')
        client_id = request.POST.get('client_id')
        suhu = request.POST.get('suhu')
        berat = request.POST.get('berat')
        catatan = request.POST.get('catatan')
        
        try:
            with connection.cursor() as cursor:
                # Update visit with medical data including catatan
                cursor.execute("""
                    UPDATE PETCLINIC.KUNJUNGAN
                    SET suhu = %s, berat_badan = %s, catatan = %s
                    WHERE id_kunjungan = %s
                    AND nama_hewan = %s
                    AND no_identitas_klien = %s
                """, [suhu, berat, catatan, visit_id, animal_name, client_id])
                
                # Check if a treatment record already exists
                cursor.execute("""
                    SELECT 1 FROM PETCLINIC.KUNJUNGAN_KEPERAWATAN
                    WHERE id_kunjungan = %s
                    AND nama_hewan = %s
                    AND no_identitas_klien = %s
                """, [visit_id, animal_name, client_id])
                
            return JsonResponse({'success': True})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def doctor_view(request):
    return visit_list_doctor(request)

def get_animals(request):
    client_id = request.GET.get('client_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama 
                FROM PETCLINIC.HEWAN
                WHERE no_identitas_klien = %s
            """, [client_id])
            animals = dictfetchall(cursor)
        
        return JsonResponse({'animals': animals})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)