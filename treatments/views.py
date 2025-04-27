from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required
from .forms import TreatmentForm
from functools import wraps

def get_user_data(request):
    """Helper function to get user data based on session"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    if not user_email or not user_type:
        return None
    
    # Get basic user data with fully qualified table name
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT email, alamat, nomor_telepon FROM petclinic."USER" 
            WHERE email = %s
        """, [user_email])
        user_data = cursor.fetchall()
    
    if not user_data:
        return None
        
    result = {
        'email': user_data[0][0],
        'alamat': user_data[0][1],
        'nomor_telepon': user_data[0][2],
        'user_type': user_type
    }
    
    # Get additional data for dokter
    if user_type == 'dokter':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.no_pegawai, p.tanggal_mulai_kerja, tm.no_izin_praktik 
                FROM petclinic.PEGAWAI p 
                JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                JOIN petclinic.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
                WHERE p.email_user = %s
            """, [user_email])
            emp_data = cursor.fetchall()
            if emp_data:
                result.update({
                    'no_pegawai': emp_data[0][0],
                    'tanggal_mulai_kerja': emp_data[0][1],
                    'no_izin_praktik': emp_data[0][2]
                })
                
    return result

def dokter_required(view_func):
    """Decorator to ensure user is a dokter"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_type = request.session.get('user_type')
        if user_type != 'dokter':
            messages.error(request, 'Access denied. Only veterinarians can access this page.')
            return redirect('authentication:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@dokter_required
def list_treatments(request):
    """View function to list all treatments for a veterinarian"""
    user_data = get_user_data(request)
    if not user_data:
        messages.error(request, 'User data not found. Please login again.')
        return redirect('authentication:login')
    
    dokter_id = user_data.get('no_pegawai')
    
    # Get treatments data from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT k.id_kunjungan, k.nama_hewan, kl.email, 
                   p.email_user as perawat_email, d.no_dokter_hewan, fd.no_front_desk, 
                   kk.kode_perawatan, pr.nama_perawatan, kk.catatan
            FROM petclinic.KUNJUNGAN k
            JOIN petclinic.KLIEN kl ON k.no_identitas_klien = kl.no_identitas
            JOIN petclinic.DOKTER_HEWAN d ON k.no_dokter_hewan = d.no_dokter_hewan
            JOIN petclinic.PERAWAT_HEWAN p ON k.no_perawat_hewan = p.no_perawat_hewan
            JOIN petclinic.FRONT_DESK fd ON k.no_front_desk = fd.no_front_desk
            JOIN petclinic.PEGAWAI pe ON p.no_perawat_hewan = pe.no_pegawai
            LEFT JOIN petclinic.KUNJUNGAN_KEPERAWATAN kk ON 
                k.id_kunjungan = kk.id_kunjungan AND 
                k.nama_hewan = kk.nama_hewan AND 
                k.no_identitas_klien = kk.no_identitas_klien AND
                k.no_dokter_hewan = kk.no_dokter_hewan AND
                k.no_perawat_hewan = kk.no_perawat_hewan AND
                k.no_front_desk = kk.no_front_desk
            LEFT JOIN petclinic.PERAWATAN pr ON kk.kode_perawatan = pr.kode_perawatan
            WHERE k.no_dokter_hewan = %s
            ORDER BY k.id_kunjungan
        """, [dokter_id])
        treatments = cursor.fetchall()
    
    # Prepare the treatment data for display
    treatment_list = []
    for t in treatments:
        treatment_data = {
            'id_kunjungan': t[0],
            'nama_hewan': t[1],
            'klien': t[2],
            'perawat': t[3],
            'dokter': 'dr. ' + user_data.get('email'),
            'front_desk': t[5],
            'kode_perawatan': t[6],
            'nama_perawatan': t[7] if t[7] else '-',
            'catatan': t[8] if t[8] else '-'
        }
        treatment_list.append(treatment_data)
    
    context = {
        'user_data': user_data,
        'treatments': treatment_list
    }
    
    return render(request, 'treatments/list_treatments.html', context)

@dokter_required
def create_treatment(request):
    """View function to create a new treatment"""
    user_data = get_user_data(request)
    if not user_data:
        messages.error(request, 'User data not found. Please login again.')
        return redirect('authentication:login')
    
    dokter_id = user_data.get('no_pegawai')
    
    # Get available visits (kunjungan) for the doctor
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT k.id_kunjungan, k.nama_hewan 
            FROM petclinic.KUNJUNGAN k
            WHERE k.no_dokter_hewan = %s AND k.timestamp_akhir IS NULL
            ORDER BY k.id_kunjungan
        """, [dokter_id])
        kunjungan_data = cursor.fetchall()
    
    kunjungan_choices = [(k[0], f"{k[0]} - {k[1]}") for k in kunjungan_data]
    
    # Get available treatment types
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode_perawatan, nama_perawatan 
            FROM petclinic.PERAWATAN
            ORDER BY kode_perawatan
        """)
        perawatan_data = cursor.fetchall()
    
    perawatan_choices = [(p[0], f"{p[0]} - {p[1]}") for p in perawatan_data]
    
    form = TreatmentForm(
        request.POST or None, 
        kunjungan_choices=kunjungan_choices,
        perawatan_choices=perawatan_choices
    )
    
    if request.method == 'POST' and form.is_valid():
        kunjungan_id = form.cleaned_data['kunjungan']
        kode_perawatan = form.cleaned_data['jenis_perawatan']
        catatan_medis = form.cleaned_data['catatan_medis']
        
        try:
            # Get visit details
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan
                    FROM petclinic.KUNJUNGAN
                    WHERE id_kunjungan = %s
                """, [kunjungan_id])
                kunjungan = cursor.fetchone()
            
            if not kunjungan:
                messages.error(request, 'Selected visit not found.')
                return redirect('treatments:create_treatment')
            
            # Insert new treatment record
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO petclinic.KUNJUNGAN_KEPERAWATAN 
                    (id_kunjungan, nama_hewan, no_identitas_klien, no_front_desk, no_perawat_hewan, no_dokter_hewan, kode_perawatan, catatan)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    kunjungan_id, kunjungan[0], kunjungan[1], kunjungan[2], kunjungan[3], kunjungan[4], kode_perawatan, catatan_medis
                ])
            
            messages.success(request, 'Treatment record created successfully!')
            return redirect('treatments:list_treatments')
            
        except Exception as e:
            messages.error(request, f'Error creating treatment record: {str(e)}')
    
    context = {
        'user_data': user_data,
        'form': form
    }
    
    return render(request, 'treatments/create_treatment.html', context)

@dokter_required
def update_treatment(request, kunjungan_id, kode_perawatan):
    """View function to update an existing treatment"""
    user_data = get_user_data(request)
    if not user_data:
        messages.error(request, 'User data not found. Please login again.')
        return redirect('authentication:login')
    
    dokter_id = user_data.get('no_pegawai')
    
    # Get the treatment record from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kk.id_kunjungan, kk.nama_hewan, kk.no_identitas_klien, 
                   kk.no_front_desk, kk.no_perawat_hewan, kk.no_dokter_hewan, 
                   kk.kode_perawatan, kk.catatan, pr.nama_perawatan
            FROM petclinic.KUNJUNGAN_KEPERAWATAN kk
            JOIN petclinic.PERAWATAN pr ON kk.kode_perawatan = pr.kode_perawatan
            WHERE kk.id_kunjungan = %s AND kk.kode_perawatan = %s AND kk.no_dokter_hewan = %s
        """, [kunjungan_id, kode_perawatan, dokter_id])
        treatment = cursor.fetchone()
    
    if not treatment:
        messages.error(request, 'Treatment record not found or you do not have permission to edit it.')
        return redirect('treatments:list_treatments')
    
    # Get all available treatment types
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode_perawatan, nama_perawatan 
            FROM petclinic.PERAWATAN
            ORDER BY kode_perawatan
        """)
        perawatan_data = cursor.fetchall()
    
    perawatan_choices = [(p[0], f"{p[0]} - {p[1]}") for p in perawatan_data]
    
    # Set up initial form data
    kunjungan_choices = [(treatment[0], f"{treatment[0]} - {treatment[1]}")]
    
    initial_data = {
        'kunjungan': treatment[0],
        'jenis_perawatan': treatment[6],
        'catatan_medis': treatment[7] or ''
    }
    
    form = TreatmentForm(
        request.POST or None, 
        kunjungan_choices=kunjungan_choices,
        perawatan_choices=perawatan_choices,
        initial=initial_data
    )
    
    # Disable form fields that cannot be changed
    form.fields['kunjungan'].widget.attrs['readonly'] = True
    form.fields['kunjungan'].widget.attrs['disabled'] = True
    form.fields['jenis_perawatan'].widget.attrs['readonly'] = True
    form.fields['jenis_perawatan'].widget.attrs['disabled'] = True
    
    if request.method == 'POST' and form.is_valid():
        catatan_medis = form.cleaned_data['catatan_medis']
        
        try:
            # Update treatment record
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.KUNJUNGAN_KEPERAWATAN 
                    SET catatan = %s
                    WHERE id_kunjungan = %s AND kode_perawatan = %s AND no_dokter_hewan = %s
                """, [catatan_medis, kunjungan_id, kode_perawatan, dokter_id])
            
            messages.success(request, 'Treatment record updated successfully!')
            return redirect('treatments:list_treatments')
            
        except Exception as e:
            messages.error(request, f'Error updating treatment record: {str(e)}')
    
    context = {
        'user_data': user_data,
        'form': form,
        'treatment': {
            'id_kunjungan': treatment[0],
            'nama_hewan': treatment[1],
            'kode_perawatan': treatment[6],
            'nama_perawatan': treatment[8]
        }
    }
    
    return render(request, 'treatments/update_treatment.html', context)

@dokter_required
def delete_treatment(request, kunjungan_id, kode_perawatan):
    """View function to delete a treatment record"""
    user_data = get_user_data(request)
    if not user_data:
        messages.error(request, 'User data not found. Please login again.')
        return redirect('authentication:login')
    
    dokter_id = user_data.get('no_pegawai')
    
    # Get treatment details for confirmation
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kk.id_kunjungan, kk.nama_hewan, pr.nama_perawatan
            FROM petclinic.KUNJUNGAN_KEPERAWATAN kk
            JOIN petclinic.PERAWATAN pr ON kk.kode_perawatan = pr.kode_perawatan
            WHERE kk.id_kunjungan = %s AND kk.kode_perawatan = %s AND kk.no_dokter_hewan = %s
        """, [kunjungan_id, kode_perawatan, dokter_id])
        treatment = cursor.fetchone()
    
    if not treatment:
        messages.error(request, 'Treatment record not found or you do not have permission to delete it.')
        return redirect('treatments:list_treatments')
    
    if request.method == 'POST':
        try:
            # Delete the treatment record
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM petclinic.KUNJUNGAN_KEPERAWATAN
                    WHERE id_kunjungan = %s AND kode_perawatan = %s AND no_dokter_hewan = %s
                """, [kunjungan_id, kode_perawatan, dokter_id])
            
            messages.success(request, 'Treatment record deleted successfully!')
            return redirect('treatments:list_treatments')
            
        except Exception as e:
            messages.error(request, f'Error deleting treatment record: {str(e)}')
    
    context = {
        'user_data': user_data,
        'treatment': {
            'id_kunjungan': treatment[0],
            'nama_hewan': treatment[1],
            'kode_perawatan': kode_perawatan,
            'nama_perawatan': treatment[2]
        }
    }
    
    return render(request, 'treatments/delete_treatment.html', context)