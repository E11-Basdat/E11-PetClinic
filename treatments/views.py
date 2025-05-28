from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from functools import wraps
from django.urls import reverse
from datetime import datetime
from django.core.paginator import Paginator
import uuid
import locale
from urllib.parse import unquote
from django.views.decorators.http import require_POST

def n_treatment_list(request):
    treatments = get_treatments_data()
    return render(request, 'n_treatment_list.html', {
        'user_role': 'else',
        'treatments': treatments
    })

def n_treatment_list_doctor(request):
    treatments = get_treatments_data()
    return render(request, 'n_treatment_list.html', {
        'user_role': 'doctor',
        'treatments': treatments
    })

def n_treatment_list_klien(request):
    treatments = get_treatments_data()
    return render(request, 'n_treatment_list.html', {
        'user_role': 'klien',
        'treatments': treatments
    })

def n_create_treatment(request):
    if request.method == 'POST':
        try:
            kunjungan_id = request.POST.get('kunjungan')
            kode_perawatan = request.POST.get('jenis_perawatan')
            catatan_medis = request.POST.get('catatan_medis')
            
            # Extract components from kunjungan compound key
            kunjungan_parts = kunjungan_id.split('|')
            if len(kunjungan_parts) != 6:
                messages.error(request, "Format kunjungan tidak valid")
                return redirect('treatments:n_treatment_list_doctor')
            
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan = kunjungan_parts
            
            with connection.cursor() as cursor:
                # Check if treatment already exists for this kunjungan and perawatan
                cursor.execute("""
                    SELECT COUNT(*) FROM petclinic.kunjungan_keperawatan 
                    WHERE id_kunjungan = %s AND nama_hewan = %s AND no_identitas_klien = %s 
                    AND no_front_desk = %s AND no_perawat_hewan = %s AND no_dokter_hewan = %s 
                    AND kode_perawatan = %s
                """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                      no_perawat_hewan, no_dokter_hewan, kode_perawatan])
                
                if cursor.fetchone()[0] > 0:
                    messages.error(request, "Treatment dengan jenis perawatan ini sudah ada untuk kunjungan tersebut")
                    return redirect('treatments:n_treatment_list_doctor')
                
                # Insert new treatment record
                cursor.execute("""
                    INSERT INTO petclinic.kunjungan_keperawatan 
                    (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                     no_perawat_hewan, no_dokter_hewan, kode_perawatan, catatan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                      no_perawat_hewan, no_dokter_hewan, kode_perawatan, catatan_medis])
            
            messages.success(request, "Treatment berhasil ditambahkan")
            return redirect('treatments:n_treatment_list_doctor')
            
        except Exception as e:
            messages.error(request, f"Gagal menambahkan treatment: {str(e)}")
            return redirect('treatments:n_treatment_list_doctor')
    
    # Get available kunjungan and perawatan for form
    context = get_form_choices()
    return render(request, 'n_treatment_form.html', {'mode': 'create', **context})

def n_delete_treatment(request, kunjungan_id):
    if request.method == 'POST':
        try:
            # URL decode the kunjungan_id to handle %7C -> |
            decoded_kunjungan_id = unquote(kunjungan_id)
            
            # Parse kunjungan_id to get compound key components
            kunjungan_parts = decoded_kunjungan_id.split('|')
            if len(kunjungan_parts) != 7:  # Including kode_perawatan for delete
                return JsonResponse({'status': 'error', 'message': 'Format kunjungan tidak valid'}, status=400)
            
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan = kunjungan_parts
            
            with connection.cursor() as cursor:
                # Delete treatment record
                cursor.execute("""
                    DELETE FROM petclinic.kunjungan_keperawatan 
                    WHERE id_kunjungan = %s AND nama_hewan = %s AND no_identitas_klien = %s 
                    AND no_front_desk = %s AND no_perawat_hewan = %s AND no_dokter_hewan = %s 
                    AND kode_perawatan = %s
                """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                      no_perawat_hewan, no_dokter_hewan, kode_perawatan])
                
                if cursor.rowcount == 0:
                    return JsonResponse({'status': 'error', 'message': 'Treatment tidak ditemukan'}, status=404)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def n_update_treatment(request, kunjungan_id):
    # URL decode the kunjungan_id
    decoded_kunjungan_id = unquote(kunjungan_id)
    
    if request.method == 'POST':
        try:
            kode_perawatan = request.POST.get('jenis_perawatan')
            catatan_medis = request.POST.get('catatan_medis')
            
            # Parse kunjungan_id to get compound key components
            kunjungan_parts = decoded_kunjungan_id.split('|')
            if len(kunjungan_parts) != 7:  # Including kode_perawatan for update
                messages.error(request, "Format kunjungan tidak valid")
                return redirect('treatments:n_treatment_list_doctor')
            
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, old_kode_perawatan = kunjungan_parts
            
            with connection.cursor() as cursor:
                # Update treatment record
                cursor.execute("""
                    UPDATE petclinic.kunjungan_keperawatan 
                    SET kode_perawatan = %s, catatan = %s
                    WHERE id_kunjungan = %s AND nama_hewan = %s AND no_identitas_klien = %s 
                    AND no_front_desk = %s AND no_perawat_hewan = %s AND no_dokter_hewan = %s 
                    AND kode_perawatan = %s
                """, [kode_perawatan, catatan_medis, id_kunjungan, nama_hewan, 
                      no_identitas_klien, no_front_desk, no_perawat_hewan, 
                      no_dokter_hewan, old_kode_perawatan])
                
                # Check if any rows were affected
                if cursor.rowcount == 0:
                    messages.error(request, "Treatment tidak ditemukan atau tidak dapat diupdate")
                    return redirect('treatments:n_treatment_list_doctor')
            
            messages.success(request, "Treatment berhasil diupdate")
            return redirect('treatments:n_treatment_list_doctor')
            
        except Exception as e:
            messages.error(request, f"Gagal mengupdate treatment: {str(e)}")
            return redirect('treatments:n_treatment_list_doctor')
    
    # Get current treatment data and form choices
    context = get_form_choices()
    treatment_data = get_treatment_data(decoded_kunjungan_id)
    
    if not treatment_data:
        messages.error(request, "Treatment tidak ditemukan")
        return redirect('treatments:n_treatment_list_doctor')
    
    return render(request, 'n_treatment_form.html', {
        'mode': 'update', 
        'kunjungan_id': kunjungan_id,  # Keep the original encoded version for URL
        'treatment_data': treatment_data,
        **context
    })

def get_treatments_data():
    """Get all treatments data for listing - ensuring unique records"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                kk.id_kunjungan, 
                kk.nama_hewan, 
                kk.no_identitas_klien, 
                kk.no_front_desk, 
                kk.no_perawat_hewan, 
                kk.no_dokter_hewan, 
                kk.kode_perawatan,
                kk.catatan,
                p.nama_perawatan,
                CONCAT(kk.id_kunjungan, '|', kk.nama_hewan, '|', kk.no_identitas_klien, '|', 
                       kk.no_front_desk, '|', kk.no_perawat_hewan, '|', kk.no_dokter_hewan, '|', kk.kode_perawatan) as compound_id,
                -- Simply show the UUID for staff for now, since there's no direct relation to INDIVIDU
                CAST(kk.no_perawat_hewan AS VARCHAR) as perawat,
                CAST(kk.no_dokter_hewan AS VARCHAR) as dokter,
                CAST(kk.no_front_desk AS VARCHAR) as front_desk,
                -- Get client name (handle both INDIVIDU and PERUSAHAAN)
                CASE 
                    WHEN i_klien.nama_depan IS NOT NULL THEN 
                        CONCAT(i_klien.nama_depan, ' ', 
                               COALESCE(i_klien.nama_tengah, ''), ' ', 
                               i_klien.nama_belakang)
                    ELSE pr.nama_perusahaan
                END as nama_klien
            FROM petclinic.kunjungan_keperawatan kk
            JOIN petclinic.perawatan p ON kk.kode_perawatan = p.kode_perawatan
            -- Join to get client name (both individual and company)
            LEFT JOIN petclinic.klien kl ON kk.no_identitas_klien = kl.no_identitas
            LEFT JOIN petclinic.individu i_klien ON kl.no_identitas = i_klien.no_identitas_klien
            LEFT JOIN petclinic.perusahaan pr ON kl.no_identitas = pr.no_identitas_klien
            ORDER BY kk.id_kunjungan DESC, kk.kode_perawatan ASC
        """)
        
        columns = [col[0] for col in cursor.description]
        treatments = []
        seen_compounds = set()  # Track unique compound IDs to prevent duplicates
        
        for row in cursor.fetchall():
            treatment_dict = dict(zip(columns, row))
            compound_id = treatment_dict['compound_id']
            
            # Only add if we haven't seen this compound ID before
            if compound_id not in seen_compounds:
                treatments.append(treatment_dict)
                seen_compounds.add(compound_id)
        
        return treatments

def get_treatment_data(kunjungan_id):
    """Get specific treatment data for update form"""
    try:
        kunjungan_parts = kunjungan_id.split('|')
        if len(kunjungan_parts) != 7:
            return None
        
        id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan = kunjungan_parts
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT kk.catatan, p.nama_perawatan, p.biaya_perawatan,
                       k.id_kunjungan, k.nama_hewan, k.timestamp_awal
                FROM petclinic.kunjungan_keperawatan kk
                JOIN petclinic.perawatan p ON kk.kode_perawatan = p.kode_perawatan
                JOIN petclinic.kunjungan k ON (kk.id_kunjungan = k.id_kunjungan 
                                              AND kk.nama_hewan = k.nama_hewan 
                                              AND kk.no_identitas_klien = k.no_identitas_klien
                                              AND kk.no_front_desk = k.no_front_desk
                                              AND kk.no_perawat_hewan = k.no_perawat_hewan
                                              AND kk.no_dokter_hewan = k.no_dokter_hewan)
                WHERE kk.id_kunjungan = %s AND kk.nama_hewan = %s 
                AND kk.no_identitas_klien = %s AND kk.no_front_desk = %s 
                AND kk.no_perawat_hewan = %s AND kk.no_dokter_hewan = %s 
                AND kk.kode_perawatan = %s
            """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                  no_perawat_hewan, no_dokter_hewan, kode_perawatan])
            
            row = cursor.fetchone()
            if row:
                return {
                    'catatan_medis': row[0],
                    'kode_perawatan': kode_perawatan,
                    'nama_perawatan': row[1],
                    'biaya_perawatan': row[2],
                    'id_kunjungan': row[3],
                    'nama_hewan': row[4],
                    'timestamp_awal': row[5]
                }
    except Exception as e:
        print(f"Error getting treatment data: {e}")
    
    return None

def get_form_choices():
    """Get available kunjungan and perawatan choices for forms"""
    with connection.cursor() as cursor:
        # Get kunjungan choices with client names
        cursor.execute("""
            SELECT 
                CONCAT(k.id_kunjungan, '|', k.nama_hewan, '|', k.no_identitas_klien, '|', 
                       k.no_front_desk, '|', k.no_perawat_hewan, '|', k.no_dokter_hewan) as compound_key,
                CONCAT(k.nama_hewan, ' - ', 
                       CASE 
                           WHEN i.nama_depan IS NOT NULL THEN 
                               CONCAT(i.nama_depan, ' ', COALESCE(i.nama_tengah, ''), ' ', i.nama_belakang)
                           ELSE pr.nama_perusahaan
                       END,
                       ' (', TO_CHAR(k.timestamp_awal, 'DD/MM/YYYY HH24:MI'), ')') as display_name
            FROM petclinic.kunjungan k
            LEFT JOIN petclinic.klien kl ON k.no_identitas_klien = kl.no_identitas
            LEFT JOIN petclinic.individu i ON kl.no_identitas = i.no_identitas_klien
            LEFT JOIN petclinic.perusahaan pr ON kl.no_identitas = pr.no_identitas_klien
            ORDER BY k.timestamp_awal DESC
        """)
        kunjungan_choices = []
        for row in cursor.fetchall():
            kunjungan_choices.append((row[0], row[1]))
        
        # Get perawatan choices with formatted pricing
        cursor.execute("""
            SELECT kode_perawatan, 
                   CONCAT(kode_perawatan, ' - ', nama_perawatan, ' (Rp ', 
                          TO_CHAR(biaya_perawatan, 'FM999,999,999'), ')')
            FROM petclinic.perawatan
            ORDER BY nama_perawatan
        """)
        perawatan_choices = []
        for row in cursor.fetchall():
            perawatan_choices.append((row[0], row[1]))
    
    return {
        'kunjungan_choices': kunjungan_choices,
        'perawatan_choices': perawatan_choices
    }
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------


# Import decorators from medications app
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

def clean_error_message(message):
    """Remove the CONTEXT part from database error messages"""
    if isinstance(message, str) and 'CONTEXT:' in message:
        message = message.split('CONTEXT:')[0].strip()
    return message

# =========================
# TREATMENT TYPE MANAGEMENT
# =========================

def get_treatment_types_list(search=None, sort_by=None):
    """Get list of all treatment types with usage information"""
    with connection.cursor() as cursor:
        query = """
            SELECT kode_perawatan, nama_perawatan, biaya_perawatan
            FROM PETCLINIC.PERAWATAN
        """
        
        params = []
        
        if search:
            query += " WHERE LOWER(nama_perawatan) LIKE LOWER(%s)"
            params.append(f'%{search}%')
        
        # Add sorting
        if sort_by == 'price_low_high':
            query += " ORDER BY biaya_perawatan ASC"
        elif sort_by == 'price_high_low':
            query += " ORDER BY biaya_perawatan DESC"
        else:
            query += " ORDER BY kode_perawatan DESC"
        
        cursor.execute(query, params)
        treatments = cursor.fetchall()
        treatment_list = []
        
        for row in treatments:
            try:
                original_biaya = row[2]
                formatted_biaya = f"Rp{locale.format_string('%d', float(original_biaya), grouping=True)}"
            except (ValueError, TypeError):
                formatted_biaya = f"Rp{row[2]}"
                
            # Check if this treatment is used (for delete functionality)
            can_delete = not is_treatment_type_used(row[0])
                
            treatment_list.append({
                'kode_perawatan': row[0],
                'nama_perawatan': row[1],
                'biaya_perawatan': formatted_biaya,
                'biaya_raw': original_biaya,  
                'can_delete': can_delete
            })
    
    return treatment_list

def get_treatment_type_by_id(kode_perawatan):
    """Get treatment type by ID"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode_perawatan, nama_perawatan, biaya_perawatan
            FROM PETCLINIC.PERAWATAN
            WHERE kode_perawatan = %s
        """, [kode_perawatan])
        
        result = cursor.fetchone()
        
        if result:
            return {
                'kode_perawatan': result[0],
                'nama_perawatan': result[1],
                'biaya_perawatan': result[2]
            }
        
        return None

def is_treatment_type_used(kode_perawatan):
    """Check if treatment type has been used in visits"""
    try:
        with connection.cursor() as cursor:
            # First try with exact table name from ERD
            cursor.execute("""
                SELECT COUNT(*)
                FROM PETCLINIC.KUNJUNGAN_PERAWATAN
                WHERE kode_perawatan = %s
            """, [kode_perawatan])
            
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        # If the table doesn't exist or has different name, return False
        return False

def generate_treatment_code():
    """Generate a new treatment code"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MAX(kode_perawatan) 
            FROM PETCLINIC.PERAWATAN
        """)
        
        max_code = cursor.fetchone()[0]
        
        if not max_code:
            return "TRM001"
        
        # Extract numeric part and increment
        try:
            code_num = int(max_code[3:])
            next_code = f"TRM{code_num + 1:03d}"
        except (ValueError, IndexError):
            # Fallback if code format is different
            return "TRM001"
        
        return next_code

@tenaga_medis_required
def treatment_type_list(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'none')
    
    treatments = get_treatment_types_list(search=search_query, sort_by=sort_by)
    
    context = {
        'treatments': treatments,
        'search_query': search_query,
        'sort_by': sort_by
    }
    return render(request, 'treatment_type_list.html', context)

@tenaga_medis_required
def add_treatment_type(request):
    if request.method == 'POST':
        try:
            nama_perawatan = request.POST.get('nama_perawatan')
            biaya_perawatan = int(request.POST.get('biaya_perawatan'))
            
            if biaya_perawatan < 0:
                messages.error(request, "Biaya tidak boleh bernilai negatif")
                return redirect('treatments:treatment_type_list')
            
            kode_perawatan = generate_treatment_code()
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO PETCLINIC.PERAWATAN (kode_perawatan, nama_perawatan, biaya_perawatan)
                    VALUES (%s, %s, %s)
                """, [kode_perawatan, nama_perawatan, biaya_perawatan])
            
            messages.success(request, f"Jenis perawatan {nama_perawatan} berhasil ditambahkan dengan kode {kode_perawatan}")
            return redirect('treatments:treatment_type_list')
            
        except Exception as e:
            messages.error(request, f"Gagal menambahkan jenis perawatan: {clean_error_message(str(e))}")
            return redirect('treatments:treatment_type_list')
    
    return redirect('treatments:treatment_type_list')

@tenaga_medis_required
def update_treatment_type(request, kode_perawatan):
    treatment = get_treatment_type_by_id(kode_perawatan)
    
    if not treatment:
        messages.error(request, "Data jenis perawatan tidak ditemukan")
        return redirect('treatments:treatment_type_list')
    
    if request.method == 'POST':
        try:
            nama_perawatan = request.POST.get('nama_perawatan')
            biaya_perawatan = int(request.POST.get('biaya_perawatan'))
            
            if biaya_perawatan < 0:
                messages.error(request, "Biaya tidak boleh bernilai negatif")
                return redirect('treatments:treatment_type_list')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE PETCLINIC.PERAWATAN 
                    SET nama_perawatan = %s, biaya_perawatan = %s
                    WHERE kode_perawatan = %s
                """, [nama_perawatan, biaya_perawatan, kode_perawatan])
            
            messages.success(request, f"Data jenis perawatan {nama_perawatan} berhasil diperbarui")
            return redirect('treatments:treatment_type_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data jenis perawatan: {clean_error_message(str(e))}")
            return redirect('treatments:treatment_type_list')
    
    return redirect('treatments:treatment_type_list')

@require_POST
@tenaga_medis_required
def delete_treatment_type(request, kode_perawatan):
    try:
        treatment = get_treatment_type_by_id(kode_perawatan)
        
        if not treatment:
            return JsonResponse({
                'success': False,
                'message': 'Data jenis perawatan tidak ditemukan'
            })

        # Check if treatment is used
        if is_treatment_type_used(kode_perawatan):
            return JsonResponse({
                'success': False,
                'message': 'Tidak dapat menghapus jenis perawatan yang sedang digunakan'
            })

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM PETCLINIC.PERAWATAN
                WHERE kode_perawatan = %s
            """, [kode_perawatan])
        
        return JsonResponse({
            'success': True,
            'message': f"Jenis perawatan {treatment['nama_perawatan']} berhasil dihapus"
        })
        
    except Exception as e:
        error_message = clean_error_message(str(e))
        return JsonResponse({
            'success': False,
            'message': f"Gagal menghapus jenis perawatan: {error_message}"
        })