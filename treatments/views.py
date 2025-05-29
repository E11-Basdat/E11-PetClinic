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
            
            # Extract components from kunjungan compound key
            kunjungan_parts = kunjungan_id.split('|')
            if len(kunjungan_parts) != 6:
                messages.error(request, "Format kunjungan tidak valid")
                return redirect('treatments:n_treatment_list_doctor')
            
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan = kunjungan_parts
            
            with connection.cursor() as cursor:
                # Check if treatment already exists
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
                
                # Insert new treatment record (without catatan)
                cursor.execute("""
                    INSERT INTO petclinic.kunjungan_keperawatan 
                    (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                     no_perawat_hewan, no_dokter_hewan, kode_perawatan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                      no_perawat_hewan, no_dokter_hewan, kode_perawatan])
            
            messages.success(request, "Treatment berhasil ditambahkan")
            # Add highlight parameter to URL
            return redirect(f"{reverse('treatments:n_treatment_list_doctor')}?highlight={kunjungan_id}")
            
        except Exception as e:
            messages.error(request, f"Gagal menambahkan treatment: {str(e)}")
            return redirect('treatments:n_treatment_list_doctor')
    
    # Get available kunjungan and perawatan for form
    context = get_form_choices()
    return render(request, 'n_treatment_form.html', {'mode': 'create', **context})

def n_delete_treatment(request, kunjungan_id):
    if request.method == 'POST':
        try:
            decoded_kunjungan_id = unquote(kunjungan_id)
            
            kunjungan_parts = decoded_kunjungan_id.split('|')
            if len(kunjungan_parts) != 7:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Format kunjungan tidak valid'
                }, status=400)
            
            id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan = kunjungan_parts
            
            with connection.cursor() as cursor:
                # Delete the treatment record from kunjungan_keperawatan table
                cursor.execute("""
                    DELETE FROM petclinic.kunjungan_keperawatan 
                    WHERE id_kunjungan = %s 
                    AND nama_hewan = %s 
                    AND no_identitas_klien = %s 
                    AND no_front_desk = %s 
                    AND no_perawat_hewan = %s 
                    AND no_dokter_hewan = %s 
                    AND kode_perawatan = %s
                """, [id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, 
                      no_perawat_hewan, no_dokter_hewan, kode_perawatan])
                
                if cursor.rowcount == 0:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Treatment tidak ditemukan'
                    }, status=404)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Gagal menghapus treatment: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request method'
    }, status=400)
    
def n_update_treatment(request, kunjungan_id):
    decoded_kunjungan_id = unquote(kunjungan_id)
    kunjungan_parts = decoded_kunjungan_id.split('|')
    
    if len(kunjungan_parts) != 7:
        messages.error(request, "Format kunjungan tidak valid")
        return redirect('treatments:n_treatment_list_doctor')
    
    id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, old_kode_perawatan = kunjungan_parts

    # Handle POST request (when form is submitted)
    if request.method == 'POST':
        try:
            new_kode_perawatan = request.POST.get('jenis_perawatan')
            
            with connection.cursor() as cursor:
                # Update treatment with new kode_perawatan
                cursor.execute("""
                    UPDATE petclinic.kunjungan_keperawatan 
                    SET kode_perawatan = %s
                    WHERE id_kunjungan = %s 
                    AND nama_hewan = %s 
                    AND no_identitas_klien = %s 
                    AND no_front_desk = %s 
                    AND no_perawat_hewan = %s 
                    AND no_dokter_hewan = %s 
                    AND kode_perawatan = %s
                """, [new_kode_perawatan, id_kunjungan, nama_hewan, 
                      no_identitas_klien, no_front_desk, no_perawat_hewan, 
                      no_dokter_hewan, old_kode_perawatan])
                
                if cursor.rowcount > 0:
                    messages.success(request, "Treatment berhasil diupdate")
                    # Add highlight parameter to URL
                    return redirect(f"{reverse('treatments:n_treatment_list_doctor')}?highlight={kunjungan_id}")
                else:
                    messages.error(request, "Gagal mengupdate treatment")
                    return redirect('treatments:n_treatment_list_doctor')
                
        except Exception as e:
            messages.error(request, f"Gagal mengupdate treatment: {str(e)}")
            return redirect('treatments:n_treatment_list_doctor')

    # GET request - show the form with current data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                k.id_kunjungan,
                k.nama_hewan,
                k.no_identitas_klien,
                INITCAP(p_fd.email_user) as front_desk_email,
                INITCAP(p_dh.email_user) as dokter_email,
                INITCAP(p_ph.email_user) as perawat_email,
                p.kode_perawatan,
                p.nama_perawatan
            FROM petclinic.kunjungan_keperawatan k
            JOIN petclinic.perawatan p ON k.kode_perawatan = p.kode_perawatan
            LEFT JOIN petclinic.front_desk fd ON k.no_front_desk = fd.no_front_desk
            LEFT JOIN petclinic.pegawai p_fd ON fd.no_front_desk = p_fd.no_pegawai
            LEFT JOIN petclinic.tenaga_medis tm_dh ON k.no_dokter_hewan = tm_dh.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_dh ON tm_dh.no_tenaga_medis = p_dh.no_pegawai
            LEFT JOIN petclinic.tenaga_medis tm_ph ON k.no_perawat_hewan = tm_ph.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_ph ON tm_ph.no_tenaga_medis = p_ph.no_pegawai
            WHERE k.id_kunjungan = %s 
            AND k.nama_hewan = %s 
            AND k.no_identitas_klien = %s
            AND k.kode_perawatan = %s
        """, [id_kunjungan, nama_hewan, no_identitas_klien, old_kode_perawatan])
        
        current_treatment = cursor.fetchone()
    
    if not current_treatment:
        messages.error(request, "Treatment tidak ditemukan")
        return redirect('treatments:n_treatment_list_doctor')
    
    # Get form choices for dropdowns
    context = get_form_choices()
    
    # Add current treatment data to context
    treatment_data = {
        'id_kunjungan': current_treatment[0],
        'nama_hewan': current_treatment[1],
        'no_identitas_klien': current_treatment[2],
        'front_desk_email': current_treatment[3],
        'dokter_email': current_treatment[4],
        'perawat_email': current_treatment[5],
        'kode_perawatan': current_treatment[6],
        'nama_perawatan': current_treatment[7]
    }
    
    return render(request, 'n_treatment_form.html', {
        'mode': 'update',
        'kunjungan_id': kunjungan_id,
        'treatment_data': treatment_data,
        **context
    })
    
def get_treatments_data(user_email=None):
    """Get treatments data with optional filtering for client"""
    with connection.cursor() as cursor:
        base_query = """
            SELECT DISTINCT
                kk.id_kunjungan, 
                kk.nama_hewan, 
                kk.no_identitas_klien,
                INITCAP(LEFT(p_ph.email_user, STRPOS(p_ph.email_user, '.') - 1)) AS perawat_email,
                'dr. ' || INITCAP(LEFT(p_dh.email_user, STRPOS(p_dh.email_user, '.') - 1)) AS dokter_email,
                INITCAP(LEFT(p_fd.email_user, STRPOS(p_fd.email_user, '.') - 1)) AS front_desk_email,
                kk.kode_perawatan,
                p.nama_perawatan,
                CONCAT(kk.id_kunjungan, '|', kk.nama_hewan, '|', kk.no_identitas_klien, '|', 
                       kk.no_front_desk, '|', kk.no_perawat_hewan, '|', kk.no_dokter_hewan, '|', 
                       kk.kode_perawatan) as compound_id
            FROM petclinic.kunjungan_keperawatan kk
            JOIN petclinic.perawatan p ON kk.kode_perawatan = p.kode_perawatan
            JOIN petclinic.klien k ON kk.no_identitas_klien = k.no_identitas
            LEFT JOIN petclinic.tenaga_medis tm_ph ON kk.no_perawat_hewan = tm_ph.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_ph ON tm_ph.no_tenaga_medis = p_ph.no_pegawai
            LEFT JOIN petclinic.tenaga_medis tm_dh ON kk.no_dokter_hewan = tm_dh.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_dh ON tm_dh.no_tenaga_medis = p_dh.no_pegawai
            LEFT JOIN petclinic.front_desk fd ON kk.no_front_desk = fd.no_front_desk
            LEFT JOIN petclinic.pegawai p_fd ON fd.no_front_desk = p_fd.no_pegawai
        """
        
        if user_email:
            # Add WHERE clause for client filtering
            base_query += " WHERE k.email = %s"
            cursor.execute(base_query + " ORDER BY kk.id_kunjungan DESC", [user_email])
        else:
            cursor.execute(base_query + " ORDER BY kk.id_kunjungan DESC")
        
        columns = [col[0] for col in cursor.description]
        treatments = []
        seen_compounds = set()
        
        for row in cursor.fetchall():
            treatment_dict = dict(zip(columns, row))
            compound_id = treatment_dict['compound_id']
            
            if compound_id not in seen_compounds:
                treatment_dict['jenis_perawatan'] = f"{treatment_dict['kode_perawatan']} - {treatment_dict['nama_perawatan']}"
                treatments.append(treatment_dict)
                seen_compounds.add(compound_id)
        
        return treatments

def n_treatment_list_klien(request):
    """View for clients to see their own treatments"""
    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, "Please login first")
        return redirect('authentication:login')
        
    treatments = get_treatments_data(user_email=user_email)
    return render(request, 'n_treatment_list.html', {
        'user_role': 'client',
        'treatments': treatments
    })

def get_form_choices():
    """Get available kunjungan and perawatan choices for forms"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                CONCAT(k.id_kunjungan, '|', k.nama_hewan, '|', k.no_identitas_klien, '|', 
                       k.no_front_desk, '|', k.no_perawat_hewan, '|', k.no_dokter_hewan) as compound_key,
                k.id_kunjungan,
                k.nama_hewan,
                k.no_identitas_klien,
                INITCAP(SPLIT_PART(p_fd.email_user, '.', 1)) AS front_desk_email,
                INITCAP(SPLIT_PART(p_dh.email_user, '.', 1)) AS dokter_email,
                INITCAP(SPLIT_PART(p_ph.email_user, '.', 1)) AS perawat_email
            FROM petclinic.kunjungan k
            -- Join for Front Desk email
            LEFT JOIN petclinic.front_desk fd ON k.no_front_desk = fd.no_front_desk
            LEFT JOIN petclinic.pegawai p_fd ON fd.no_front_desk = p_fd.no_pegawai
            -- Join for Dokter Hewan & Perawat through TENAGA_MEDIS and PEGAWAI
            LEFT JOIN petclinic.tenaga_medis tm_dh ON k.no_dokter_hewan = tm_dh.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_dh ON tm_dh.no_tenaga_medis = p_dh.no_pegawai
            LEFT JOIN petclinic.tenaga_medis tm_ph ON k.no_perawat_hewan = tm_ph.no_tenaga_medis
            LEFT JOIN petclinic.pegawai p_ph ON tm_ph.no_tenaga_medis = p_ph.no_pegawai
            ORDER BY k.timestamp_awal DESC
        """)
        
        kunjungan_choices = []
        for row in cursor.fetchall():
            compound_key = row[0]
            id_kunjungan = row[1]
            nama_hewan = row[2]
            no_identitas_klien = row[3]
            front_desk_email = row[4] or 'N/A'
            dokter_email = row[5] or 'N/A'
            perawat_email = row[6] or 'N/A'
            
            # Format display dengan line breaks yang benar untuk HTML
            display_name = f"""ID Kunjungan: {id_kunjungan}
Nama Hewan: {nama_hewan}
ID Klien: {no_identitas_klien}
Front Desk: {front_desk_email}
Dokter Hewan: dr. {dokter_email}
Perawat Hewan: {perawat_email}"""
            
            kunjungan_choices.append((compound_key, display_name))
        
        # Get perawatan choices (unchanged)
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

        with connection.cursor() as cursor:
            # Check if treatment is referenced in perawatan_obat table
            cursor.execute("""
                SELECT COUNT(*) 
                FROM PETCLINIC.PERAWATAN_OBAT 
                WHERE kode_perawatan = %s
            """, [kode_perawatan])
            
            obat_count = cursor.fetchone()[0]
            
            if obat_count > 0:
                return JsonResponse({
                    'success': False,
                    'message': f'Tidak dapat menghapus jenis perawatan "{treatment["nama_perawatan"]}" karena masih terdapat {obat_count} obat yang terkait dengan perawatan ini'
                })
            
            # Check if treatment is used in other tables (if any)
            # You might need to add more checks here based on your complete schema
            
            # If no dependencies found, proceed with deletion
            cursor.execute("""
                DELETE FROM PETCLINIC.PERAWATAN
                WHERE kode_perawatan = %s
            """, [kode_perawatan])
            
            if cursor.rowcount == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Data jenis perawatan tidak ditemukan atau sudah terhapus'
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Jenis perawatan "{treatment["nama_perawatan"]}" berhasil dihapus'
            })
                
    except Exception as e:
        error_message = clean_error_message(str(e))
        
        # Handle specific foreign key constraint errors
        if 'foreign key constraint' in error_message.lower():
            return JsonResponse({
                'success': False,
                'message': f'Tidak dapat menghapus jenis perawatan "{treatment["nama_perawatan"] if treatment else ""}" karena masih digunakan oleh data lain dalam sistem'
            })
        
        return JsonResponse({
            'success': False,
            'message': f"Gagal menghapus jenis perawatan: {error_message}"
        })


# Alternative: If you want to update your existing is_treatment_type_used function
def is_treatment_type_used(kode_perawatan):
    """
    Check if a treatment type is being used in any related table
    """
    with connection.cursor() as cursor:
        # Check perawatan_obat table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM PETCLINIC.PERAWATAN_OBAT 
            WHERE kode_perawatan = %s
        """, [kode_perawatan])
        
        if cursor.fetchone()[0] > 0:
            return True
        
        # Add more checks for other tables that might reference perawatan
        # For example, if there's a table for treatment records, appointments, etc.
        
        return False