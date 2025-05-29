from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from functools import wraps
from datetime import datetime
import uuid
import locale
import re
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection, transaction

def dokter_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        if request.session.get('user_type') != 'dokter':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def perawat_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        if request.session.get('user_type') != 'perawat':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def tenaga_medis_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        user_type = request.session.get('user_type')
        if user_type != 'dokter' and user_type != 'perawat':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def klien_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        user_type = request.session.get('user_type')
        if user_type != 'individu' and user_type != 'perusahaan':
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
            FROM petclinic.pegawai p 
            JOIN petclinic.tenaga_medis tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.dokter_hewan dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
            WHERE p.email_user = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

def get_nurse_id(request):
    """Get nurse ID from session"""
    user_email = request.session.get('user_email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.no_pegawai
            FROM petclinic.pegawai p 
            JOIN petclinic.tenaga_medis tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.perawat_hewan ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
            WHERE p.email_user = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

def get_client_id(request):
    """Get client ID from session"""
    user_email = request.session.get('user_email')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT no_identitas
            FROM petclinic.klien
            WHERE email = %s
        """, [user_email])
        result = cursor.fetchone()
    
    return result[0] if result else None

# =========================
# MEDICINE MANAGEMENT (TENAGA MEDIS - DOKTER & PERAWAT)
# =========================

def get_medicines_list(search=None):
    """Get list of all medicines with usage information"""
    with connection.cursor() as cursor:
        if search:
            cursor.execute("""
                SELECT o.kode, o.nama, o.harga, o.stok, o.dosis,
                       CASE WHEN COUNT(po.kode_obat) > 0 THEN false ELSE true END as can_delete
                FROM petclinic.obat o
                LEFT JOIN petclinic.perawatan_obat po ON o.kode = po.kode_obat
                WHERE LOWER(o.nama) LIKE LOWER(%s)
                GROUP BY o.kode, o.nama, o.harga, o.stok, o.dosis
                ORDER BY o.kode DESC
            """, [f'%{search}%'])
        else:
            cursor.execute("""
                SELECT o.kode, o.nama, o.harga, o.stok, o.dosis,
                       CASE WHEN COUNT(po.kode_obat) > 0 THEN false ELSE true END as can_delete
                FROM petclinic.obat o
                LEFT JOIN petclinic.perawatan_obat po ON o.kode = po.kode_obat
                GROUP BY o.kode, o.nama, o.harga, o.stok, o.dosis
                ORDER BY o.kode DESC
            """)
        
        medicines = cursor.fetchall()
        medicine_list = []
        
        for row in medicines:
            try:
                original_harga = row[2]
                formatted_harga = f"Rp{locale.format_string('%d', float(original_harga), grouping=True)}"
            except (ValueError, TypeError):
                formatted_harga = f"Rp{row[2]}"
                
            medicine_list.append({
                'kode': row[0],
                'nama': row[1],
                'harga': formatted_harga,
                'harga_raw': original_harga,  
                'stok': row[3],
                'dosis': row[4],
                'can_delete': row[5]
            })
    
    return medicine_list

def get_medicine_by_id(kode):
    """Get medicine by ID"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.kode, o.nama, o.harga, o.stok, o.dosis
            FROM petclinic.obat o
            WHERE o.kode = %s
        """, [kode])
        
        result = cursor.fetchone()
        
        if result:
            return {
                'kode': result[0],
                'nama': result[1],
                'harga': result[2],  
                'stok': result[3],
                'dosis': result[4]
            }
        
        return None

def is_medicine_used(kode):
    """Check if medicine has been used in treatments"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM petclinic.perawatan_obat po
            WHERE po.kode_obat = %s
        """, [kode])
        
        count = cursor.fetchone()[0]
        return count > 0

def generate_medicine_code():
    """Generate a new medicine code"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MAX(kode) 
            FROM petclinic.obat
        """)
        
        max_code = cursor.fetchone()[0]
        
        if not max_code:
            return "MED001"
        
        code_num = int(max_code[3:])
        next_code = f"MED{code_num + 1:03d}"
        
        return next_code

def clean_error_message(message):
    """Remove the CONTEXT part from database error messages"""
    if isinstance(message, str) and 'CONTEXT:' in message:
        message = message.split('CONTEXT:')[0].strip()
    return message

@tenaga_medis_required
def medicine_list(request):
    search_query = request.GET.get('search', '')
    medicines = get_medicines_list(search=search_query)
    context = {
        'medicines': medicines,
        'search_query': search_query
    }
    return render(request, 'medicine_list.html', context)

@tenaga_medis_required
def add_medicine(request):
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = int(request.POST.get('harga'))
            stok = int(request.POST.get('stok'))
            dosis = request.POST.get('dosis')
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('medications:add_medicine')
                
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('medications:add_medicine')
            
            kode = generate_medicine_code()
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO petclinic.obat (kode, nama, harga, stok, dosis)
                    VALUES (%s, %s, %s, %s, %s)
                """, [kode, nama, harga, stok, dosis])
            
            messages.success(request, f"Obat {nama} berhasil ditambahkan dengan kode {kode}")
            return redirect('medications:medicine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal menambahkan obat: {clean_error_message(str(e))}")
            return redirect('medications:add_medicine')
    
    return render(request, 'add_medicine.html')

@tenaga_medis_required
def update_medicine(request, medicine_id):  
    medicine = get_medicine_by_id(medicine_id)  
    
    if not medicine:
        messages.error(request, "Data obat tidak ditemukan")
        return redirect('medications:medicine_list')
    
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = int(request.POST.get('harga'))
            dosis = request.POST.get('dosis')
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('medications:update_medicine', medicine_id=medicine_id)  # Ubah parameter
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.obat 
                    SET nama = %s, harga = %s, dosis = %s
                    WHERE kode = %s
                """, [nama, harga, dosis, medicine_id])  
            
            messages.success(request, f"Data obat {nama} berhasil diperbarui")
            return redirect('medications:medicine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data obat: {clean_error_message(str(e))}")
            return redirect('medications:update_medicine', medicine_id=medicine_id)  
    
    context = {'medicine': medicine}
    return render(request, 'update_medicine.html', context)

def update_medicine_stock(request, medicine_id):  
    medicine = get_medicine_by_id(medicine_id)  
    
    if not medicine:
        messages.error(request, "Data obat tidak ditemukan")
        return redirect('medications:medicine_list')
    
    if request.method == 'POST':
        try:
            stok = int(request.POST.get('stok'))
            
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('medications:update_medicine_stock', medicine_id=medicine_id)  
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.obat 
                    SET stok = %s
                    WHERE kode = %s
                """, [stok, medicine_id])  
            
            messages.success(request, f"Stok obat {medicine['nama']} berhasil diperbarui")
            return redirect('medications:medicine_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui stok obat: {clean_error_message(str(e))}")
            return redirect('medications:update_medicine_stock', medicine_id=medicine_id)  
    
    context = {'medicine': medicine}
    return render(request, 'update_medicine_stock.html', context)

@require_POST
@tenaga_medis_required
def delete_medicine(request, medicine_id):  
    try:
        medicine = get_medicine_by_id(medicine_id)  
        
        if not medicine:
            messages.error(request, "Data obat tidak ditemukan")
            return redirect('medications:medicine_list')

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM petclinic.obat
                WHERE kode = %s
            """, [medicine_id])  
        
        messages.success(request, f"Obat {medicine['nama']} berhasil dihapus")
        return redirect('medications:medicine_list')
        
    except Exception as e:
        error_message = str(e)
        if "ERROR:" in error_message:
            messages.error(request, clean_error_message(error_message))
        else:
            messages.error(request, f"Gagal menghapus obat: {clean_error_message(error_message)}")
        return redirect('medications:medicine_list')


# =========================
# PRESCRIPTION MANAGEMENT 
# =========================


def clean_error_message(error_msg):
    """Clean up error messages for better user experience - ENHANCED"""
    if not error_msg:
        return "Terjadi kesalahan yang tidak diketahui"
    
    error_str = str(error_msg).strip()
    
    if "ERROR:" in error_str:
        error_match = re.search(r'ERROR:\s*(.+?)(?:\n|$)', error_str, re.IGNORECASE)
        if error_match:
            return error_match.group(1).strip()
    
    # Handle RAISE EXCEPTION messages directly
    if "RAISE EXCEPTION" in error_str.upper():
        # Extract message from RAISE EXCEPTION format
        raise_match = re.search(r'RAISE EXCEPTION\s*[\'"](.+?)[\'"]', error_str, re.IGNORECASE)
        if raise_match:
            return raise_match.group(1).strip()
    
    
    cleaned = re.sub(r'CONTEXT:.*$', '', error_str, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r'LINE \d+:.*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r'DETAIL:.*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r'HINT:.*$', '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned if cleaned else "Terjadi kesalahan database"

def get_treatment_types():
    """Get list of all treatment types (Jenis Perawatan) - SUPABASE FIXED"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT kode_perawatan, nama_perawatan, biaya_perawatan
                FROM petclinic.perawatan
                ORDER BY nama_perawatan
            """)
        except Exception as e:
            try:
                cursor.execute("""
                    SELECT kode_perawatan, nama_perawatan, biaya_perawatan
                    FROM perawatan
                    ORDER BY nama_perawatan
                """)
            except Exception as e2:
                print(f"Both treatment queries failed: {str(e)}, {str(e2)}")
                return []
        
        treatments = cursor.fetchall()
        treatment_list = []
        
        for row in treatments:
            # Include biaya_perawatan for frontend validation
            treatment_list.append({
                'kode': row[0],
                'nama': row[1],
                'biaya': row[2] if len(row) > 2 else 0,
                'display': f"{row[0]} - {row[1]}"
            })
    
    return treatment_list

def get_medicines_with_stock():
    """Get list of medicines with their stock information - SUPABASE FIXED"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT kode, nama, harga, stok, dosis
                FROM petclinic.obat
                WHERE stok > 0
                ORDER BY nama
            """)
        except Exception as e:
            try:
                cursor.execute("""
                    SELECT kode, nama, harga, stok, dosis
                    FROM obat
                    WHERE stok > 0
                    ORDER BY nama
                """)
            except Exception as e2:
                print(f"Both medicine queries failed: {str(e)}, {str(e2)}")
                return []
        
        medicines = cursor.fetchall()
        medicine_list = []
        
        for row in medicines:
            medicine_list.append({
                'kode': row[0],
                'nama': row[1],
                'harga': row[2],
                'stok': row[3],
                'dosis': row[4],
                'display': f"{row[0]} - {row[1]} [Stok: {row[3]}]"
            })
    
    return medicine_list

def get_list_prescriptions(request):
    """Get list of prescriptions - SUPABASE SCHEMA FIXED"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT 
                    po.kode_perawatan, 
                    po.kode_obat, 
                    po.kuantitas_obat,
                    p.nama_perawatan, 
                    o.nama as nama_obat, 
                    o.harga,
                    (po.kuantitas_obat * o.harga) as total_harga
                FROM petclinic.perawatan_obat po
                JOIN petclinic.perawatan p ON po.kode_perawatan = p.kode_perawatan
                JOIN petclinic.obat o ON po.kode_obat = o.kode
                ORDER BY po.kode_perawatan, po.kode_obat
            """)
            
            prescriptions = cursor.fetchall()
            
        except Exception as e:
            print(f"Schema query failed: {str(e)}")
            try:
                cursor.execute("""
                    SELECT 
                        po.kode_perawatan, 
                        po.kode_obat, 
                        po.kuantitas_obat,
                        p.nama_perawatan, 
                        o.nama as nama_obat, 
                        o.harga,
                        (po.kuantitas_obat * o.harga) as total_harga
                    FROM perawatan_obat po
                    JOIN perawatan p ON po.kode_perawatan = p.kode_perawatan
                    JOIN obat o ON po.kode_obat = o.kode
                    ORDER BY po.kode_perawatan, po.kode_obat
                """)
                
                prescriptions = cursor.fetchall()
                
            except Exception as e2:
                print(f"No schema query also failed: {str(e2)}")
                try:
                    cursor.execute("""
                        SELECT 
                            kode_perawatan, 
                            kode_obat, 
                            kuantitas_obat
                        FROM perawatan_obat
                        ORDER BY kode_perawatan, kode_obat
                    """)
                    
                    prescriptions = cursor.fetchall()
                    
                    prescription_list = []
                    for row in prescriptions:
                        prescription_list.append({
                            'kode_perawatan': row[0],
                            'kode_obat': row[1],
                            'kuantitas_obat': row[2],
                            'nama_perawatan': f'Treatment {row[0]}',
                            'nama_obat': f'Medicine {row[1]}',
                            'harga': 'Rp0',
                            'total_harga': 'Rp0'
                        })
                    
                    return prescription_list
                    
                except Exception as e3:
                    print(f"All queries failed: {str(e)}, {str(e2)}, {str(e3)}")
                    return []
        
        prescription_list = []
        
        for row in prescriptions:
            try:
                harga = float(row[5]) if row[5] else 0
                total_harga = float(row[6]) if row[6] else 0
                formatted_harga = f"Rp{harga:,.0f}"
                formatted_total = f"Rp{total_harga:,.0f}"
            except (ValueError, TypeError):
                formatted_harga = f"Rp{row[5]}"
                formatted_total = f"Rp{row[6]}"
                
            prescription_list.append({
                'kode_perawatan': row[0],
                'kode_obat': row[1],
                'kuantitas_obat': row[2],
                'nama_perawatan': row[3],
                'nama_obat': row[4],
                'harga': formatted_harga,
                'total_harga': formatted_total
            })
        
        return prescription_list

@csrf_exempt
def prescription_list(request):
    """Display list of prescriptions"""
    try:
        prescriptions = get_list_prescriptions(request)
        treatments = get_treatment_types()
        medicines = get_medicines_with_stock()
        
        print(f"Found {len(prescriptions)} prescriptions")
        print(f"Found {len(treatments)} treatments")
        print(f"Found {len(medicines)} medicines")
        
        context = {
            'prescriptions': prescriptions,
            'treatments': treatments,
            'medicines': medicines
        }
        return render(request, 'prescription_list.html', context)
    except Exception as e:
        print(f"Error in prescription_list view: {str(e)}")
        error_message = clean_error_message(str(e))
        messages.error(request, f"Error loading data: {error_message}")
        return render(request, 'prescription_list.html', {
            'prescriptions': [],
            'treatments': [],
            'medicines': []
        })

@csrf_exempt
def add_prescription(request):
    """Add new prescription - FULLY DYNAMIC ERROR HANDLING"""
    if request.method == 'POST':
        try:
            # Get form data
            kode_perawatan = request.POST.get('kode_perawatan', '').strip()
            kode_obat = request.POST.get('kode_obat', '').strip()
            kuantitas_obat_str = request.POST.get('kuantitas_obat', '').strip()
            
            if not all([kode_perawatan, kode_obat, kuantitas_obat_str]):
                messages.error(request, "Semua field harus diisi")
                return redirect('medications:prescription_list')
            
            try:
                kuantitas_obat = int(kuantitas_obat_str)
                if kuantitas_obat <= 0:
                    messages.error(request, "Kuantitas obat harus lebih dari 0")
                    return redirect('medications:prescription_list')
            except ValueError:
                messages.error(request, "Kuantitas obat harus berupa angka yang valid")
                return redirect('medications:prescription_list')
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    try:
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM petclinic.perawatan_obat
                            WHERE kode_perawatan = %s AND kode_obat = %s
                        """, [kode_perawatan, kode_obat])
                    except Exception:
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM perawatan_obat
                            WHERE kode_perawatan = %s AND kode_obat = %s
                        """, [kode_perawatan, kode_obat])
                    
                    if cursor.fetchone()[0] > 0:
                        messages.error(request, "Resep untuk kombinasi perawatan dan obat ini sudah ada")
                        return redirect('medications:prescription_list')
                    
                    try:
                        cursor.execute("""
                            INSERT INTO petclinic.perawatan_obat (kode_perawatan, kode_obat, kuantitas_obat)
                            VALUES (%s, %s, %s)
                        """, [kode_perawatan, kode_obat, kuantitas_obat])
                        
                    except Exception as db_error:
                        if any(keyword in str(db_error).lower() for keyword in ['does not exist', 'relation', 'schema']):
                            try:
                                cursor.execute("""
                                    INSERT INTO perawatan_obat (kode_perawatan, kode_obat, kuantitas_obat)
                                    VALUES (%s, %s, %s)
                                """, [kode_perawatan, kode_obat, kuantitas_obat])
                                
                            except Exception as db_error2:
                                error_message = clean_error_message(str(db_error2))
                                print(f"Database trigger error (no schema): {str(db_error2)}")
                                messages.error(request, error_message)
                                return redirect('medications:prescription_list')
                        else:
                            error_message = clean_error_message(str(db_error))
                            print(f"Database trigger error (with schema): {str(db_error)}")
                            messages.error(request, error_message)
                            return redirect('medications:prescription_list')
            
            messages.success(request, "Resep obat berhasil ditambahkan")
            return redirect('medications:prescription_list')
        
        except Exception as e:
            error_message = clean_error_message(str(e))
            print(f"Unexpected error in add_prescription: {str(e)}")
            messages.error(request, f"Gagal menambahkan resep obat: {error_message}")
            return redirect('medications:prescription_list')
    
    return redirect('medications:prescription_list')

@require_POST
@csrf_exempt
def delete_prescription(request, kode_perawatan, kode_obat):
    """Delete prescription - FULLY DYNAMIC ERROR HANDLING"""
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                prescription_info = None
                try:
                    cursor.execute("""
                        SELECT po.kuantitas_obat, p.nama_perawatan, o.nama
                        FROM petclinic.perawatan_obat po
                        LEFT JOIN petclinic.perawatan p ON po.kode_perawatan = p.kode_perawatan
                        LEFT JOIN petclinic.obat o ON po.kode_obat = o.kode
                        WHERE po.kode_perawatan = %s AND po.kode_obat = %s
                    """, [kode_perawatan, kode_obat])
                    prescription_info = cursor.fetchone()
                except Exception:
                    try:
                        cursor.execute("""
                            SELECT po.kuantitas_obat, p.nama_perawatan, o.nama
                            FROM perawatan_obat po
                            LEFT JOIN perawatan p ON po.kode_perawatan = p.kode_perawatan
                            LEFT JOIN obat o ON po.kode_obat = o.kode
                            WHERE po.kode_perawatan = %s AND po.kode_obat = %s
                        """, [kode_perawatan, kode_obat])
                        prescription_info = cursor.fetchone()
                    except Exception:
                        cursor.execute("""
                            SELECT kuantitas_obat
                            FROM perawatan_obat
                            WHERE kode_perawatan = %s AND kode_obat = %s
                        """, [kode_perawatan, kode_obat])
                        result = cursor.fetchone()
                        if result:
                            prescription_info = (result[0], f'Treatment {kode_perawatan}', f'Medicine {kode_obat}')
                
                if not prescription_info:
                    messages.error(request, 'Resep yang akan dihapus tidak ditemukan')
                    return redirect('medications:prescription_list')
                
                treatment_name = prescription_info[1] if len(prescription_info) >= 2 and prescription_info[1] else f'Treatment {kode_perawatan}'
                medicine_name = prescription_info[2] if len(prescription_info) >= 3 and prescription_info[2] else f'Medicine {kode_obat}'
                
                try:
                    cursor.execute("""
                        DELETE FROM petclinic.perawatan_obat
                        WHERE kode_perawatan = %s AND kode_obat = %s
                    """, [kode_perawatan, kode_obat])
                    
                except Exception as db_error:
                    if any(keyword in str(db_error).lower() for keyword in ['does not exist', 'relation', 'schema']):
                        try:
                            cursor.execute("""
                                DELETE FROM perawatan_obat
                                WHERE kode_perawatan = %s AND kode_obat = %s
                            """, [kode_perawatan, kode_obat])
                            
                        except Exception as db_error2:
                            error_message = clean_error_message(str(db_error2))
                            print(f"Delete trigger error (no schema): {str(db_error2)}")
                            messages.error(request, f"Gagal menghapus resep: {error_message}")
                            return redirect('medications:prescription_list')
                    else:
                        error_message = clean_error_message(str(db_error))
                        print(f"Delete trigger error (with schema): {str(db_error)}")
                        messages.error(request, f"Gagal menghapus resep: {error_message}")
                        return redirect('medications:prescription_list')
                
                if cursor.rowcount == 0:
                    messages.error(request, 'Resep tidak ditemukan atau sudah dihapus')
                    return redirect('medications:prescription_list')
        
        messages.success(request, f"Resep {treatment_name} - {medicine_name} berhasil dihapus")
        return redirect('medications:prescription_list')
        
    except Exception as e:
        error_message = clean_error_message(str(e))
        print(f"Unexpected error in delete_prescription: {str(e)}")
        messages.error(request, f"Gagal menghapus resep: {error_message}")
        return redirect('medications:prescription_list')
    
def delete_prescription_ajax(request, kode_perawatan, kode_obat):
    """AJAX version for better UX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT po.kuantitas_obat, p.nama_perawatan, o.nama
                    FROM petclinic.perawatan_obat po
                    LEFT JOIN petclinic.perawatan p ON po.kode_perawatan = p.kode_perawatan
                    LEFT JOIN petclinic.obat o ON po.kode_obat = o.kode
                    WHERE po.kode_perawatan = %s AND po.kode_obat = %s
                """, [kode_perawatan, kode_obat])
            except:
                cursor.execute("""
                    SELECT kuantitas_obat
                    FROM perawatan_obat
                    WHERE kode_perawatan = %s AND kode_obat = %s
                """, [kode_perawatan, kode_obat])
            
            result = cursor.fetchone()
            if not result:
                return JsonResponse({'success': False, 'message': 'Data resep tidak ditemukan'})
                
            kuantitas_obat = result[0]
            
            try:
                cursor.execute("""
                    DELETE FROM petclinic.perawatan_obat
                    WHERE kode_perawatan = %s AND kode_obat = %s
                """, [kode_perawatan, kode_obat])
            except:
                cursor.execute("""
                    DELETE FROM perawatan_obat
                    WHERE kode_perawatan = %s AND kode_obat = %s
                """, [kode_perawatan, kode_obat])
            
            try:
                cursor.execute("""
                    UPDATE petclinic.obat 
                    SET stok = stok + %s 
                    WHERE kode = %s
                """, [kuantitas_obat, kode_obat])
            except:
                cursor.execute("""
                    UPDATE obat 
                    SET stok = stok + %s 
                    WHERE kode = %s
                """, [kuantitas_obat, kode_obat])
        
        return JsonResponse({
            'success': True, 
            'message': 'Resep berhasil dihapus'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Gagal menghapus resep: {str(e)}'
        })