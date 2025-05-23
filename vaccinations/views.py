from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from functools import wraps
from datetime import datetime
import uuid
import locale
from django.views.decorators.http import require_POST


def dokter_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('login')
        
        if request.session.get('user_type') != 'dokter':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_doctor_id(request):
    """Get doctor ID from session"""
    user_email = request.session.get('user_email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.no_pegawai
            FROM PETCLINIC.PEGAWAI p 
            JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN PETCLINIC.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
            WHERE p.email_user = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

def get_list_vaccinations(request):
    doctor_id = get_doctor_id(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT k.id_kunjungan, k.nama_hewan, k.timestamp_awal, v.nama as nama_vaksin, 
                   k.no_identitas_klien, k.no_dokter_hewan, v.kode as kode_vaksin
            FROM PETCLINIC.KUNJUNGAN k
            LEFT JOIN PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
            WHERE k.kode_vaksin IS NOT NULL
            AND k.no_dokter_hewan = %s
            ORDER BY k.timestamp_awal DESC
        """, [doctor_id])
        vaccinations = cursor.fetchall()
        
        vaccination_list = []
        for row in vaccinations:
            vaccination_list.append({
                'id_kunjungan': row[0],
                'nama_hewan': row[1],
                'tanggal_kunjungan': row[2],
                'nama_vaksin': row[3],
                'no_identitas_klien': row[4],
                'no_dokter_hewan': row[5],
                'kode_vaksin': row[6]
            })
    
    return vaccination_list

def get_open_visits(request):
    """Get list of open visits (timestamp_akhir is NULL)"""
    doctor_id = get_doctor_id(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT k.id_kunjungan, k.nama_hewan, k.timestamp_awal, 
                   k.no_identitas_klien, k.no_front_desk, k.no_perawat_hewan
            FROM PETCLINIC.KUNJUNGAN k
            WHERE k.timestamp_akhir IS NULL
            AND k.no_dokter_hewan = %s
            ORDER BY k.timestamp_awal DESC
        """, [doctor_id])
        
        visits = cursor.fetchall()
        visit_list = []
        
        for row in visits:
            visit_list.append({
                'id_kunjungan': row[0],
                'nama_hewan': row[1],
                'tanggal_kunjungan': row[2],
                'no_identitas_klien': row[3],
                'no_front_desk': row[4],
                'no_perawat_hewan': row[5]
            })
    
    return visit_list

def get_vaccines_with_stock():
    """Get list of vaccines with their stock information"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama, stok 
            FROM PETCLINIC.VAKSIN
            ORDER BY nama
        """)
        
        vaccines = cursor.fetchall()
        vaccine_list = []
        
        for row in vaccines:
            vaccine_list.append({
                'kode': row[0],
                'nama': row[1],
                'stok': row[2],
                'display': f"{row[0]} - {row[1]} [{row[2]}]"
            })
    
    return vaccine_list

def perawat_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('login')
        
        if request.session.get('user_type') != 'perawat':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_nurse_id(request):
    """Get nurse ID from session"""
    user_email = request.session.get('user_email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.no_pegawai
            FROM PETCLINIC.PEGAWAI p 
            JOIN PETCLINIC.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN PETCLINIC.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
            WHERE p.email_user = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

def get_vaccines_list(search=None):
    """Get list of all vaccines with usage information"""
    with connection.cursor() as cursor:
        if search:
            cursor.execute("""
                SELECT v.kode, v.nama, v.harga, v.stok,
                       CASE WHEN COUNT(k.id_kunjungan) > 0 THEN false ELSE true END as can_delete
                FROM PETCLINIC.VAKSIN v
                LEFT JOIN PETCLINIC.KUNJUNGAN k ON v.kode = k.kode_vaksin
                WHERE LOWER(v.nama) LIKE LOWER(%s)
                GROUP BY v.kode, v.nama, v.harga, v.stok
                ORDER BY v.kode DESC
            """, [f'%{search}%'])
        else:
            cursor.execute("""
                SELECT v.kode, v.nama, v.harga, v.stok,
                       CASE WHEN COUNT(k.id_kunjungan) > 0 THEN false ELSE true END as can_delete
                FROM PETCLINIC.VAKSIN v
                LEFT JOIN PETCLINIC.KUNJUNGAN k ON v.kode = k.kode_vaksin
                GROUP BY v.kode, v.nama, v.harga, v.stok
                ORDER BY v.kode DESC
            """)
        
        vaccines = cursor.fetchall()
        vaccine_list = []
        
        for row in vaccines:
            try:
                original_harga = row[2]
                formatted_harga = f"Rp{locale.format_string('%d', float(original_harga), grouping=True)}"
            except (ValueError, TypeError):
                formatted_harga = f"Rp{row[2]}"
                
            vaccine_list.append({
                'kode': row[0],
                'nama': row[1],
                'harga': formatted_harga,
                'harga_raw': original_harga,  
                'stok': row[3],
                'can_delete': row[4]
            })
    
    return vaccine_list


def get_vaccine_by_id(kode):
    """Get vaccine by ID"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT v.kode, v.nama, v.harga, v.stok
            FROM PETCLINIC.VAKSIN v
            WHERE v.kode = %s
        """, [kode])
        
        result = cursor.fetchone()
        
        if result:

            return {
                'kode': result[0],
                'nama': result[1],
                'harga': result[2],  
                'stok': result[3]
            }
        
        return None

def is_vaccine_used(kode):
    """Check if vaccine has been used in vaccinations"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM PETCLINIC.KUNJUNGAN k
            WHERE k.kode_vaksin = %s
        """, [kode])
        
        count = cursor.fetchone()[0]
        return count > 0

def generate_vaccine_code():
    """Generate a new vaccine code"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MAX(kode) 
            FROM PETCLINIC.VAKSIN
        """)
        
        max_code = cursor.fetchone()[0]
        
        if not max_code:
            return "VAC001"
        
        code_num = int(max_code[3:])
        next_code = f"VAC{code_num + 1:03d}"
        
        return next_code

def clean_error_message(message):
    """Remove the CONTEXT part from database error messages"""
    if isinstance(message, str) and 'CONTEXT:' in message:
        message = message.split('CONTEXT:')[0].strip()
    return message

@dokter_required
def vaccination_list(request):
    vaccinations = get_list_vaccinations(request)
    context = {'vaccinations': vaccinations}
    return render(request, 'vaccinations/vaccination_list.html', context)

@dokter_required
def add_vaccination(request):
    if request.method == 'POST':
        try:
            id_kunjungan = request.POST.get('id_kunjungan')
            kode_vaksin = request.POST.get('kode_vaksin')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT kode_vaksin
                    FROM PETCLINIC.KUNJUNGAN
                    WHERE id_kunjungan = %s
                """, [id_kunjungan])
                
                existing_vaccine = cursor.fetchone()
                if existing_vaccine and existing_vaccine[0] is not None:
                    messages.error(request, "Kunjungan ini sudah memiliki vaksinasi")
                    return redirect('add_vaccination')
                
                # Tambahkan vaksinasi - trigger akan menangani stok
                cursor.execute("""
                    UPDATE PETCLINIC.KUNJUNGAN 
                    SET kode_vaksin = %s
                    WHERE id_kunjungan = %s
                """, [kode_vaksin, id_kunjungan])
                
            messages.success(request, "Vaksinasi berhasil ditambahkan")
            return redirect('vaccination_list')
        
        except Exception as e:
            error_message = str(e)
            if "ERROR:" in error_message:
                messages.error(request, clean_error_message(error_message))
            else:
                messages.error(request, f"Gagal menambahkan vaksinasi: {clean_error_message(error_message)}")
            return redirect('add_vaccination')
    
    
    visits = get_open_visits(request)
    vaccines = get_vaccines_with_stock()
    
    context = {
        'visits': visits,
        'vaccines': vaccines
    }
    
    return render(request, 'vaccinations/add_vaccination.html', context)

@dokter_required
def update_vaccination(request, id_kunjungan):
    if request.method == 'POST':
        try:
            kode_vaksin = request.POST.get('kode_vaksin')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT k.nama_hewan, k.no_identitas_klien, k.no_front_desk, 
                           k.no_perawat_hewan, k.no_dokter_hewan, k.tipe_kunjungan,
                           k.timestamp_awal, k.timestamp_akhir, k.suhu, k.berat_badan,
                           k.kode_vaksin
                    FROM PETCLINIC.KUNJUNGAN k
                    WHERE k.id_kunjungan = %s
                """, [id_kunjungan])
                
                visit_data = cursor.fetchone()
                if not visit_data:
                    messages.error(request, "Data vaksinasi tidak ditemukan")
                    return redirect('vaccination_list')
                
                old_vaccine = visit_data[10]
                
                # Jika vaksin berbeda, update - trigger akan menangani stok
                if old_vaccine != kode_vaksin:
                    cursor.execute("""
                        UPDATE PETCLINIC.KUNJUNGAN
                        SET kode_vaksin = %s
                        WHERE id_kunjungan = %s
                    """, [kode_vaksin, id_kunjungan])
            
            messages.success(request, "Data vaksinasi berhasil diperbarui")
            return redirect('vaccination_list')
            
        except Exception as e:
            error_message = str(e)
            if "ERROR:" in error_message:
                messages.error(request, clean_error_message(error_message))
            else:
                messages.error(request, f"Gagal memperbarui data vaksinasi: {clean_error_message(error_message)}")
            return redirect('update_vaccination', id_kunjungan=id_kunjungan)
    
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT k.id_kunjungan, k.nama_hewan, k.no_identitas_klien, k.timestamp_awal, 
                   k.kode_vaksin, v.nama as nama_vaksin
            FROM PETCLINIC.KUNJUNGAN k
            JOIN PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
            WHERE k.id_kunjungan = %s
        """, [id_kunjungan])
        vaccination = cursor.fetchone()
        
        if not vaccination:
            messages.error(request, "Data vaksinasi tidak ditemukan")
            return redirect('vaccination_list')
    
    
    vaccines = get_vaccines_with_stock()
    
    context = {
        'vaccination': {
            'id_kunjungan': vaccination[0],
            'nama_hewan': vaccination[1],
            'no_identitas_klien': vaccination[2],
            'tanggal_kunjungan': vaccination[3],
            'kode_vaksin': vaccination[4],
            'nama_vaksin': vaccination[5]
        },
        'vaccines': vaccines
    }
    
    return render(request, 'vaccinations/update_vaccination.html', context)

@dokter_required
def delete_vaccination(request, id_kunjungan):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT k.kode_vaksin, v.nama
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.VAKSIN v ON k.kode_vaksin = v.kode
                WHERE k.id_kunjungan = %s
            """, [id_kunjungan])
            
            result = cursor.fetchone()
            if not result:
                messages.error(request, "Data vaksinasi tidak ditemukan")
                return redirect('vaccination_list')
                
            vaccine_name = result[1]
            
            # Set kode_vaksin ke NULL - trigger akan menangani stok
            cursor.execute("""
                UPDATE PETCLINIC.KUNJUNGAN
                SET kode_vaksin = NULL
                WHERE id_kunjungan = %s
            """, [id_kunjungan])
        
        messages.success(request, f"Vaksinasi {vaccine_name} untuk kunjungan {id_kunjungan} berhasil dihapus")
    except Exception as e:
        error_message = str(e)
        if "ERROR:" in error_message:
            messages.error(request, clean_error_message(error_message))
        else:
            messages.error(request, f"Gagal menghapus data vaksinasi: {clean_error_message(error_message)}")
    
    return redirect('vaccination_list')

@perawat_required
def vaccine_list(request):
    search_query = request.GET.get('search', '')
    vaccines = get_vaccines_list(search=search_query)
    context = {
        'vaccines': vaccines,
        'search_query': search_query
    }
    return render(request, 'vaccinations/vaccine_list.html', context)

@perawat_required
def add_vaccine(request):
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = int(request.POST.get('harga'))
            stok = int(request.POST.get('stok'))
            
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('add_vaccine')
                
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('add_vaccine')
            
            kode = generate_vaccine_code()
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO PETCLINIC.VAKSIN (kode, nama, harga, stok)
                    VALUES (%s, %s, %s, %s)
                """, [kode, nama, harga, stok])
            
            messages.success(request, f"Vaksin {nama} berhasil ditambahkan dengan kode {kode}")
            return redirect('vaccine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal menambahkan vaksin: {clean_error_message(str(e))}")
            return redirect('add_vaccine')
    
    return render(request, 'vaccinations/add_vaccine.html')

@perawat_required
def update_vaccine(request, kode):
    vaccine = get_vaccine_by_id(kode)
    
    if not vaccine:
        messages.error(request, "Data vaksin tidak ditemukan")
        return redirect('vaccine_list')
    
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = int(request.POST.get('harga'))
            
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('update_vaccine', kode=kode)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE PETCLINIC.VAKSIN 
                    SET nama = %s, harga = %s
                    WHERE kode = %s
                """, [nama, harga, kode])
            
            messages.success(request, f"Data vaksin {nama} berhasil diperbarui")
            return redirect('vaccine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data vaksin: {clean_error_message(str(e))}")
            return redirect('update_vaccine', kode=kode)
    
    context = {'vaccine': vaccine}
    return render(request, 'vaccinations/update_vaccine.html', context)

@perawat_required
def update_stock(request, kode):
    vaccine = get_vaccine_by_id(kode)
    
    if not vaccine:
        messages.error(request, "Data vaksin tidak ditemukan")
        return redirect('vaccine_list')
    
    if request.method == 'POST':
        try:
            stok = int(request.POST.get('stok'))
            
            
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('update_stock', kode=kode)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE PETCLINIC.VAKSIN 
                    SET stok = %s
                    WHERE kode = %s
                """, [stok, kode])
            
            messages.success(request, f"Stok vaksin {vaccine['nama']} berhasil diperbarui")
            return redirect('vaccine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui stok vaksin: {clean_error_message(str(e))}")
            return redirect('update_stock', kode=kode)
    
    context = {'vaccine': vaccine}
    return render(request, 'vaccinations/update_stock.html', context)

@require_POST
@perawat_required
def delete_vaccine(request, kode):
    try:
        vaccine = get_vaccine_by_id(kode)
        
        if not vaccine:
            return JsonResponse({'success': False, 'message': 'Data vaksin tidak ditemukan'})

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM PETCLINIC.VAKSIN
                WHERE kode = %s
            """, [kode])
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        error_message = str(e)
        if "ERROR:" in error_message:
            return JsonResponse({'success': False, 'message': clean_error_message(error_message)})
        return JsonResponse({'success': False, 'message': f"Gagal menghapus vaksin: {clean_error_message(error_message)}"})

def klien_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('login')
        
        user_type = request.session.get('user_type')
        if user_type != 'individu' and user_type != 'perusahaan':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            print(f"User type: {user_type}")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_client_id(request):
    """Get client ID from session"""
    user_email = request.session.get('user_email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT no_identitas
            FROM PETCLINIC.KLIEN
            WHERE email = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

def get_client_pets(client_id):
    """Get list of pets owned by the client"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama
            FROM PETCLINIC.HEWAN
            WHERE no_identitas_klien = %s
            ORDER BY nama
        """, [client_id])
        
        pets = cursor.fetchall()
        pet_list = []
        
        for row in pets:
            pet_list.append({
                'nama': row[0]
            })
    
    return pet_list

def get_all_vaccines():
    """Get list of all vaccines"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama
            FROM PETCLINIC.VAKSIN
            ORDER BY nama
        """)
        
        vaccines = cursor.fetchall()
        vaccine_list = []
        
        for row in vaccines:
            vaccine_list.append({
                'kode': row[0],
                'nama': row[1]
            })
    
    return vaccine_list

def get_client_vaccinations(request):
    """Get vaccinations for a client's pets with optional filters"""
    client_id = get_client_id(request)
    pet_filter = request.GET.get('pet_filter')
    vaccine_filter = request.GET.get('vaccine_filter')
    
    query = """
    """
    
    params = [client_id]
    
    if pet_filter:
        query += " AND k.nama_hewan = %s"
        params.append(pet_filter)
    
    if vaccine_filter:
        query += " AND v.kode = %s"
        params.append(vaccine_filter)
    
    query += " ORDER BY k.timestamp_awal DESC"
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        vaccinations = cursor.fetchall()
        
        vaccination_list = []
        for row in vaccinations:
            try:
                harga = row[4]
                formatted_harga = f"Rp{locale.format_string('%d', float(harga), grouping=True)}"
            except (ValueError, TypeError):
                formatted_harga = f"Rp{row[4]}"
                
            vaccination_list.append({
                'id_kunjungan': row[0],
                'nama_hewan': row[1],
                'nama_vaksin': row[2],
                'id_vaksin': row[3],
                'harga': formatted_harga,
                'tanggal_kunjungan': row[5]
            })
    
    return vaccination_list

@klien_required
def client_vaccination_list(request):
    client_id = get_client_id(request)
    
    if not client_id:
        messages.error(request, "Data klien tidak ditemukan")
        return redirect('authentication:dashboard')
    
    vaccinations = get_client_vaccinations(request)
    pets = get_client_pets(client_id)
    vaccines = get_all_vaccines()
    
    context = {
        'vaccinations': vaccinations,
        'pets': pets,
        'vaccines': vaccines,
        'pet_filter': request.GET.get('pet_filter', ''),
        'vaccine_filter': request.GET.get('vaccine_filter', '')
    }
    return render(request, 'vaccinations/client_vaccination_list.html', context)