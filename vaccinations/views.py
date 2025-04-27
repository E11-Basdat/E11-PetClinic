from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from datetime import datetime
import uuid

# In-memory data storage
VACCINATIONS = [
    {
        'id_kunjungan': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'nama_hewan': 'Beyyi',
        'tanggal_kunjungan': datetime(2025, 4, 20, 14, 30),
        'nama_vaksin': 'Rabies Vaccine',
        'no_identitas_klien': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'kode_vaksin': 'VAC001'
    },
    {
        'id_kunjungan': 'd4e5f6a7-b8c9-0123-defg-456789012345',
        'nama_hewan': 'Aci',
        'tanggal_kunjungan': datetime(2025, 4, 22, 10, 15),
        'nama_vaksin': 'Distemper Vaccine',
        'no_identitas_klien': 'e5f6a7b8-c9d0-1234-efgh-567890123456',
        'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'kode_vaksin': 'VAC002'
    },
    {
        'id_kunjungan': 'f6a7b8c9-d0e1-2345-fghi-678901234567',
        'nama_hewan': 'Acu',
        'tanggal_kunjungan': datetime(2025, 4, 23, 16, 45),
        'nama_vaksin': 'Parvovirus Vaccine',
        'no_identitas_klien': 'g7h8i9j0-k1l2-3456-ghij-789012345678',
        'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'kode_vaksin': 'VAC003'
    }
]

VACCINES = [
    {
        'kode': 'VAC001',
        'nama': 'Rabies Vaccine',
        'harga': 150000,
        'stok': 25,
        'can_delete': False  # Used in vaccinations
    },
    {
        'kode': 'VAC002',
        'nama': 'Distemper Vaccine',
        'harga': 120000,
        'stok': 15,
        'can_delete': False  # Used in vaccinations
    },
    {
        'kode': 'VAC003',
        'nama': 'Parvovirus Vaccine',
        'harga': 135000,
        'stok': 20,
        'can_delete': False  # Used in vaccinations
    },
    {
        'kode': 'VAC004',
        'nama': 'Feline Leukemia Vaccine',
        'harga': 180000,
        'stok': 10,
        'can_delete': True  # Not used in vaccinations
    }
]

OPEN_VISITS = [
    {
        'id_kunjungan': 'h8i9j0k1-l2m3-4567-hijk-890123456789',
        'nama_hewan': 'Max',
        'no_identitas_klien': 'i9j0k1l2-m3n4-5678-ijkl-901234567890',
        'no_front_desk': 'j0k1l2m3-n4o5-6789-jklm-012345678901',
        'no_perawat_hewan': 'k1l2m3n4-o5p6-7890-klmn-123456789012',
        'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'kode_vaksin': None,
        'tipe_kunjungan': 'Regular',
        'timestamp_awal': datetime(2025, 4, 25, 9, 30),
        'timestamp_akhir': None,  # Null timestamp_akhir indicates an open visit
        'suhu': 38,
        'berat_badan': 12.5
    },
    {
        'id_kunjungan': 'l2m3n4o5-p6q7-8901-lmno-234567890123',
        'nama_hewan': 'Charlie',
        'no_identitas_klien': 'm3n4o5p6-q7r8-9012-mnop-345678901234',
        'no_front_desk': 'j0k1l2m3-n4o5-6789-jklm-012345678901',
        'no_perawat_hewan': 'n4o5p6q7-r8s9-0123-nopq-456789012345',
        'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'kode_vaksin': None,
        'tipe_kunjungan': 'Regular',
        'timestamp_awal': datetime(2025, 4, 26, 11, 15),
        'timestamp_akhir': None,  # Null timestamp_akhir indicates an open visit
        'suhu': 39,
        'berat_badan': 8.2
    }
]

DOCTORS = {
    'doctor@petclinic.com': 'c3d4e5f6-a7b8-9012-cdef-345678901234'
}

NURSES = {
    'nurse@petclinic.com': 'k1l2m3n4-o5p6-7890-klmn-123456789012'
}

# Decorator functions
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

# Helper functions
def get_doctor_id(request):
    """Get doctor ID from session"""
    user_email = request.session.get('user_email', 'doctor@petclinic.com')
    return DOCTORS.get(user_email, 'c3d4e5f6-a7b8-9012-cdef-345678901234')  # Default for testing

def get_nurse_id(request):
    """Get nurse ID from session"""
    user_email = request.session.get('user_email', 'nurse@petclinic.com')
    return NURSES.get(user_email, 'k1l2m3n4-o5p6-7890-klmn-123456789012')  # Default for testing

def get_list_vaccinations(request):
    doctor_id = get_doctor_id(request)
    return [v for v in VACCINATIONS if v['no_dokter_hewan'] == doctor_id]

def get_open_visits(request):
    # Return visits where timestamp_akhir is None (open visits)
    return [v for v in OPEN_VISITS if v['timestamp_akhir'] is None]

def get_vaccines_with_stock():
    return [{
        'kode': v['kode'],
        'nama': v['nama'],
        'stok': v['stok'],
        'display': f"{v['kode']} - {v['nama']} [{v['stok']}]"
    } for v in VACCINES]

def get_vaccines_list(search=None):
    if search:
        return [v for v in VACCINES if search.lower() in v['nama'].lower()]
    return VACCINES

def get_vaccine_by_id(kode):
    for v in VACCINES:
        if v['kode'] == kode:
            return v
    return None

def is_vaccine_used(kode):
    for v in VACCINATIONS:
        if v['kode_vaksin'] == kode:
            return True
    return False

def generate_vaccine_code():
    existing_codes = [v['kode'] for v in VACCINES]
    if not existing_codes:
        return "VAC001"
    
    max_code = max(existing_codes)
    code_num = int(max_code[3:])
    next_code = f"VAC{code_num + 1:03d}"
    return next_code

# View functions
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
            
            # Check if visit already has a vaccination
            for vacc in VACCINATIONS:
                if vacc['id_kunjungan'] == id_kunjungan:
                    messages.error(request, "Kunjungan ini sudah memiliki vaksinasi")
                    return redirect('add_vaccination')
            
            # Check vaccine stock
            vaccine = get_vaccine_by_id(kode_vaksin)
            if not vaccine or vaccine['stok'] <= 0:
                messages.error(request, "Stok Vaksin yang dipilih sudah habis")
                return redirect('add_vaccination')
            
            # Find the visit
            visit = None
            for v in OPEN_VISITS:
                if v['id_kunjungan'] == id_kunjungan:
                    visit = v
                    break
            
            if not visit:
                messages.error(request, "Data kunjungan tidak ditemukan")
                return redirect('add_vaccination')
            
            # Add new vaccination
            new_vaccination = {
                'id_kunjungan': id_kunjungan,
                'nama_hewan': visit['nama_hewan'],
                'tanggal_kunjungan': visit['timestamp_awal'],  # Use timestamp_awal from visit
                'nama_vaksin': vaccine['nama'],
                'no_identitas_klien': visit['no_identitas_klien'],
                'no_dokter_hewan': get_doctor_id(request),
                'kode_vaksin': kode_vaksin
            }
            
            VACCINATIONS.append(new_vaccination)
            
            # Update vaccine stock
            for v in VACCINES:
                if v['kode'] == kode_vaksin:
                    v['stok'] -= 1
                    v['can_delete'] = False
                    break
            
            # Remove from open visits
            OPEN_VISITS[:] = [v for v in OPEN_VISITS if v['id_kunjungan'] != id_kunjungan]
            
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
    # Find vaccination
    vaccination = None
    for v in VACCINATIONS:
        if v['id_kunjungan'] == id_kunjungan:
            vaccination = v
            break
    
    if not vaccination:
        messages.error(request, "Data vaksinasi tidak ditemukan")
        return redirect('vaccination_list')
    
    if request.method == 'POST':
        try:
            kode_vaksin = request.POST.get('kode_vaksin')
            old_vaccine_code = vaccination['kode_vaksin']
            
            # If vaccine is changed
            if old_vaccine_code != kode_vaksin:
                # Check new vaccine stock
                new_vaccine = get_vaccine_by_id(kode_vaksin)
                if not new_vaccine or new_vaccine['stok'] <= 0:
                    messages.error(request, "Stok Vaksin yang dipilih sudah habis")
                    return redirect('update_vaccination', id_kunjungan=id_kunjungan)
                
                # Update vaccination
                vaccination['kode_vaksin'] = kode_vaksin
                vaccination['nama_vaksin'] = new_vaccine['nama']
                
                # Return stock to old vaccine
                for v in VACCINES:
                    if v['kode'] == old_vaccine_code:
                        v['stok'] += 1
                        v['can_delete'] = not is_vaccine_used(old_vaccine_code)
                        break
                
                # Decrease stock of new vaccine
                for v in VACCINES:
                    if v['kode'] == kode_vaksin:
                        v['stok'] -= 1
                        v['can_delete'] = False
                        break
            
            messages.success(request, "Data vaksinasi berhasil diperbarui")
            return redirect('vaccination_list')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data vaksinasi: {str(e)}")
            return redirect('vaccination_list')
    
    vaccines = get_vaccines_with_stock()
    
    context = {
        'vaccination': vaccination,
        'vaccines': vaccines
    }
    
    return render(request, 'vaccinations/update_vaccination.html', context)

@dokter_required
def delete_vaccination(request, id_kunjungan):
    try:
        # Find vaccination
        vaccination = None
        for i, v in enumerate(VACCINATIONS):
            if v['id_kunjungan'] == id_kunjungan:
                vaccination = v
                vaccination_index = i
                break
        
        if not vaccination:
            messages.error(request, "Data vaksinasi tidak ditemukan")
            return redirect('vaccination_list')
        
        vaccine_code = vaccination['kode_vaksin']
        vaccine_name = vaccination['nama_vaksin']
        
        # Remove vaccination
        del VACCINATIONS[vaccination_index]
        
        # Return stock to vaccine
        for v in VACCINES:
            if v['kode'] == vaccine_code:
                v['stok'] += 1
                v['can_delete'] = not is_vaccine_used(vaccine_code)
                break
        
        # Add back to open visits
        OPEN_VISITS.append({
            'id_kunjungan': id_kunjungan,
            'nama_hewan': vaccination['nama_hewan'],
            'no_identitas_klien': vaccination['no_identitas_klien'],
            'no_front_desk': 'j0k1l2m3-n4o5-6789-jklm-012345678901',  # Updated to UUID format
            'no_perawat_hewan': 'k1l2m3n4-o5p6-7890-klmn-123456789012',  # Updated to UUID format
            'no_dokter_hewan': vaccination['no_dokter_hewan'],
            'kode_vaksin': None,
            'tipe_kunjungan': 'Regular',
            'timestamp_awal': vaccination['tanggal_kunjungan'],
            'timestamp_akhir': None,  # Set to None to mark as open visit
            'suhu': 38,  # Default
            'berat_badan': 10.0  # Default
        })
        
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
            
            new_vaccine = {
                'kode': kode,
                'nama': nama,
                'harga': harga,
                'stok': stok,
                'can_delete': True
            }
            
            VACCINES.append(new_vaccine)
            
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
            
            # Update vaccine
            vaccine['nama'] = nama
            vaccine['harga'] = harga
            
            # Update any vaccinations using this vaccine
            for v in VACCINATIONS:
                if v['kode_vaksin'] == kode:
                    v['nama_vaksin'] = nama
            
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
            
            # Update stock
            vaccine['stok'] = stok
            
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
        
        # Delete vaccine
        VACCINES[:] = [v for v in VACCINES if v['kode'] != kode]
        
        messages.success(request, f"Vaksin {vaccine['nama']} berhasil dihapus")
        
    except Exception as e:
        messages.error(request, f"Gagal menghapus data vaksin: {str(e)}")
    
    return redirect('vaccine_list')
