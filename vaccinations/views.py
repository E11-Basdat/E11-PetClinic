from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from functools import wraps
from datetime import datetime
import uuid
import locale


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
                
                cursor.execute("""
                    SELECT stok FROM PETCLINIC.VAKSIN
                    WHERE kode = %s
                """, [kode_vaksin])
                
                result = cursor.fetchone()
                if not result or result[0] <= 0:
                    messages.error(request, "Stok Vaksin yang dipilih sudah habis")
                    return redirect('add_vaccination')
                
                
                cursor.execute("""
                    SELECT nama_hewan, no_identitas_klien, no_front_desk, 
                           no_perawat_hewan, no_dokter_hewan,
                           timestamp_awal, timestamp_akhir, suhu, berat_badan
                    FROM PETCLINIC.KUNJUNGAN
                    WHERE id_kunjungan = %s
                """, [id_kunjungan])
                
                visit_data = cursor.fetchone()
                if not visit_data:
                    messages.error(request, "Data kunjungan tidak ditemukan")
                    return redirect('add_vaccination')
                
                
                cursor.execute("""
                    UPDATE PETCLINIC.KUNJUNGAN 
                    SET kode_vaksin = %s
                    WHERE id_kunjungan = %s
                """, [kode_vaksin, id_kunjungan])
                
                
                cursor.execute("""
                    UPDATE PETCLINIC.VAKSIN 
                    SET stok = stok - 1
                    WHERE kode = %s
                """, [kode_vaksin])
                
            messages.success(request, "Vaksinasi berhasil ditambahkan")
            return redirect('vaccination_list')
        
        except Exception as e:
            messages.error(request, f"Gagal menambahkan vaksinasi: {str(e)}")
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
                
                
                if old_vaccine != kode_vaksin:
                    cursor.execute("""
                        SELECT stok FROM PETCLINIC.VAKSIN
                        WHERE kode = %s
                    """, [kode_vaksin])
                    
                    result = cursor.fetchone()
                    if not result or result[0] <= 0:
                        messages.error(request, "Stok Vaksin yang dipilih sudah habis")
                        return redirect('update_vaccination', id_kunjungan=id_kunjungan)
                    
                    
                    cursor.execute("""
                        UPDATE PETCLINIC.KUNJUNGAN
                        SET kode_vaksin = %s
                        WHERE id_kunjungan = %s
                    """, [kode_vaksin, id_kunjungan])
                    
                    
                    cursor.execute("""
                        UPDATE PETCLINIC.VAKSIN
                        SET stok = stok + 1
                        WHERE kode = %s
                    """, [old_vaccine])
                    
                    
                    cursor.execute("""
                        UPDATE PETCLINIC.VAKSIN
                        SET stok = stok - 1
                        WHERE kode = %s
                    """, [kode_vaksin])
            
            messages.success(request, "Data vaksinasi berhasil diperbarui")
            return redirect('vaccination_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data vaksinasi: {str(e)}")
            return redirect('vaccination_list')
    
    
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
                
            vaccine_code = result[0]
            vaccine_name = result[1]
            
            
            cursor.execute("""
                UPDATE PETCLINIC.KUNJUNGAN
                SET kode_vaksin = NULL
                WHERE id_kunjungan = %s
            """, [id_kunjungan])
            
            
            cursor.execute("""
                UPDATE PETCLINIC.VAKSIN
                SET stok = stok + 1
                WHERE kode = %s
            """, [vaccine_code])
        
        messages.success(request, f"Vaksinasi {vaccine_name} untuk kunjungan {id_kunjungan} berhasil dihapus")
    except Exception as e:
        messages.error(request, f"Gagal menghapus data vaksinasi: {str(e)}")
    
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
            messages.error(request, f"Gagal menambahkan vaksin: {str(e)}")
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
            messages.error(request, f"Gagal memperbarui data vaksin: {str(e)}")
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
            messages.error(request, f"Gagal memperbarui stok vaksin: {str(e)}")
            return redirect('update_stock', kode=kode)
    
    context = {'vaccine': vaccine}
    return render(request, 'vaccinations/update_stock.html', context)

@perawat_required
def delete_vaccine(request, kode):
    try:
        vaccine = get_vaccine_by_id(kode)
        
        if not vaccine:
            messages.error(request, "Data vaksin tidak ditemukan")
            return redirect('vaccine_list')
        
        if is_vaccine_used(kode):
            messages.error(request, "Vaksin tidak dapat dihapus karena sudah digunakan dalam vaksinasi")
            return redirect('vaccine_list')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM PETCLINIC.VAKSIN
                WHERE kode = %s
            """, [kode])
        
        messages.success(request, f"Vaksin {vaccine['nama']} berhasil dihapus")
        
    except Exception as e:
        messages.error(request, f"Gagal menghapus data vaksin: {str(e)}")
    
    return redirect('vaccine_list')