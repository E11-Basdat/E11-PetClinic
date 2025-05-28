from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from functools import wraps
from datetime import datetime
import uuid
import locale
from django.views.decorators.http import require_POST

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