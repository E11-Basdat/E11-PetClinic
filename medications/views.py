from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from functools import wraps
from datetime import datetime

MEDICINES = [
    {
        'kode': 'MED001',
        'nama': 'Amoxicillin',
        'harga': 25000,
        'stok': 50,
        'dosis': '10-20 mg/kg, 2x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED002',
        'nama': 'Dexamethasone',
        'harga': 15000,
        'stok': 30,
        'dosis': '0,1-0,5    mg/kg, 1x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED003',
        'nama': 'Ketoconazole',
        'harga': 35000,
        'stok': 20,
        'dosis': '5-10 mg/kg, 1x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED004',
        'nama': 'Metronidazole',
        'harga': 20000,
        'stok': 40,
        'dosis': '10-25 mg/kg, 2x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED005',
        'nama': 'Ivermectin',
        'harga': 50000,
        'stok': 25,
        'dosis': '0,2-0,4 mg/kg',
        'can_delete': True
    },
    {
        'kode': 'MED006',
        'nama': 'Antiparasit Topikal',
        'harga': 45000,
        'stok': 35,
        'dosis': 'Oleskan 1x/bulan (sesuai berat badan)',
        'can_delete': True
    },
    {
        'kode': 'MED007',
        'nama': 'Antibiotik Telinga',
        'harga': 30000,
        'stok': 15,
        'dosis': '2-3 tetes, 2x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED008',
        'nama': 'Ear Cleaner',
        'harga': 40000,
        'stok': 50,
        'dosis': '3-5 tetes, 1-2x/minggu',
        'can_delete': True
    },
    {
        'kode': 'MED009',
        'nama': 'Enrofloxacin',
        'harga': 60000,
        'stok': 10,
        'dosis': '5-10 mg/kg, 1x sehari',
        'can_delete': True
    },
    {
        'kode': 'MED010',
        'nama': 'Clindamycin',
        'harga': 55000,
        'stok': 18,
        'dosis': '5-10 mg/kg, 2x sehari',
        'can_delete': True
    }
]

TREATMENTS = [
    {
        'kode_perawatan': 'TRM001',
        'nama_perawatan': 'Perawatan Gigi',
        'biaya_perawatan': 325000
    },
    {
        'kode_perawatan': 'TRM002',
        'nama_perawatan': 'Grooming',
        'biaya_perawatan': 600000
    },
    {
        'kode_perawatan': 'TRM003',
        'nama_perawatan': 'Pembersihan Telinga',
        'biaya_perawatan': 140000
    },
    {
        'kode_perawatan': 'TRM004',
        'nama_perawatan': 'PPerawatan Kulit dan Bulu',
        'biaya_perawatan': 150000
    },
    {
        'kode_perawatan': 'TRM005',
        'nama_perawatan': 'Perawatan Luka Ringan',
        'biaya_perawatan': 125000
    }
]

PRESCRIPTIONS = [
    {
        'kode_perawatan': 'TRM001',
        'kode_obat': 'MED001',
        'kuantitas_obat': 2
    },
    {
        'kode_perawatan': 'TRM002',
        'kode_obat': 'MED002',
        'kuantitas_obat': 3
    },
    {
        'kode_perawatan': 'TRM003',
        'kode_obat': 'MED007',
        'kuantitas_obat': 1
    },
    {
        'kode_perawatan': 'TRM004',
        'kode_obat': 'MED004',
        'kuantitas_obat': 2
    },
    {
        'kode_perawatan': 'TRM005',
        'kode_obat': 'MED004',
        'kuantitas_obat': 1
    }
]

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        if request.session.get('user_type') not in ['dokter', 'perawat']:
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_medicine_by_id(kode):
    """Get medicine by ID - simple lookup in hardcoded list"""
    for med in MEDICINES:
        if med['kode'] == kode:
            return med
    return None

def is_medicine_used(kode):
    """Check if a medicine is used in prescriptions"""
    return any(p['kode_obat'] == kode for p in PRESCRIPTIONS)

def get_treatment_by_id(kode):
    """Get treatment by ID - simple lookup in hardcoded list"""
    for t in TREATMENTS:
        if t['kode_perawatan'] == kode:
            return t
    return None

def generate_medicine_code():
    
    """Generate a new medicine code for hardcoded data"""
    existing_codes = [m['kode'] for m in MEDICINES]
    
    if not existing_codes:
        return "MED001"
    
    max_num = max(int(code[3:]) for code in existing_codes)
    next_num = max_num + 1
    
    return f"MED{next_num:03d}"

@staff_required
def medicine_list(request):
    """View function to display list of medicines."""
    search_query = request.GET.get('search', '')

    if search_query:
        medicines = [m for m in MEDICINES if search_query.lower() in m['nama'].lower()]
    else:
        medicines = MEDICINES
    
    medicines_for_template = [
        {
            'id': int(med['kode'][3:]),  
            'code': med['kode'],
            'name': med['nama'],
            'price': med['harga'],
            'stock': med['stok'],
            'dosage': med['dosis'],
            'canDelete': med['can_delete']
        } for med in medicines
    ]
    
    context = {
        'medicines': medicines_for_template,
        'search_query': search_query
    }
    
    return render(request, 'medicine_list.html', context)

@staff_required
def add_medicine(request):
    """View function to add a new medicine to hardcoded data."""
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = request.POST.get('harga_satuan')
            dosis = request.POST.get('dosis')
            stok = request.POST.get('stok_awal')
            
            if not all([nama, harga, dosis, stok]):
                messages.error(request, 'Semua field harus diisi')
                return render(request, 'add_medicine.html')
            
            try:
                harga = int(harga)
                stok = int(stok)
            except ValueError:
                messages.error(request, 'Harga dan stok harus berupa angka')
                return render(request, 'add_medicine.html')
            
            if harga < 0 or stok < 0:
                messages.error(request, "Harga dan stok tidak boleh bernilai negatif")
                return render(request, 'add_medicine.html')
            
            new_code = generate_medicine_code()
            new_medicine = {
                'kode': new_code,
                'nama': nama,
                'harga': harga,
                'stok': stok,
                'dosis': dosis,
                'can_delete': True
            }
            
            MEDICINES.append(new_medicine)
            
            messages.success(request, f'Obat {nama} berhasil ditambahkan dengan kode {new_code}')
            return redirect('medications:list')
            
        except Exception as e:
            messages.error(request, f'Gagal menambahkan obat: {str(e)}')
    
    return render(request, 'add_medicine.html')

@staff_required
def update_medicine(request, kode):
    """View function to update an existing medicine in hardcoded data."""
    medicine = get_medicine_by_id(kode)
    
    if not medicine:
        messages.error(request, f'Obat dengan kode {kode} tidak ditemukan')
        return redirect('medications:list')
    
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = request.POST.get('harga_satuan')
            dosis = request.POST.get('dosis')
            
            if not all([nama, harga, dosis]):
                messages.error(request, 'Semua field harus diisi')
                return redirect('medications:list')
            
            try:
                harga = int(harga)
            except ValueError:
                messages.error(request, 'Harga harus berupa angka')
                return redirect('medications:list')
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('medications:list')
            
            medicine['nama'] = nama
            medicine['harga'] = harga
            medicine['dosis'] = dosis
            
            messages.success(request, f'Obat {nama} berhasil diperbarui')
            return redirect('medications:list')
            
        except Exception as e:
            messages.error(request, f'Gagal memperbarui obat: {str(e)}')
    
    return redirect('medications:list')

@staff_required
def update_stock(request, kode):
    """View function to update medicine stock in hardcoded data."""
    medicine = get_medicine_by_id(kode)
    
    if not medicine:
        messages.error(request, f'Obat dengan kode {kode} tidak ditemukan')
        return redirect('medications:list')
    
    if request.method == 'POST':
        try:
            stok = request.POST.get('stok')

            if not stok:
                messages.error(request, 'Field stok harus diisi')
                return redirect('medications:list')

            try:
                stok = int(stok)
            except ValueError:
                messages.error(request, 'Stok harus berupa angka')
                return redirect('medications:list')
            
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('medications:list')

            medicine['stok'] = stok
            
            messages.success(request, f'Stok untuk {medicine["nama"]} berhasil diperbarui')
            
        except Exception as e:
            messages.error(request, f'Gagal memperbarui stok: {str(e)}')
    
    return redirect('medications:list')

@staff_required
def delete_medicine(request, kode):
    """View function to delete a medicine from hardcoded data."""
    medicine = get_medicine_by_id(kode)
    
    if not medicine:
        messages.error(request, f'Obat dengan kode {kode} tidak ditemukan')
        return redirect('medications:list')
    
    if is_medicine_used(kode):
        messages.error(request, 'Obat tidak dapat dihapus karena sedang digunakan dalam resep')
        return redirect('medications:list')
    
    if request.method == 'POST':
        try:
            MEDICINES[:] = [m for m in MEDICINES if m['kode'] != kode]
            
            messages.success(request, f'Obat {medicine["nama"]} berhasil dihapus')
        except Exception as e:
            messages.error(request, f'Gagal menghapus obat: {str(e)}')
    
    return redirect('medications:list')

@staff_required
def prescription_list(request):
    """View function to display list of prescriptions with related data."""
    
    search_query = request.GET.get('search', '')
    
    medicines_list = [m for m in MEDICINES if m['stok'] > 0]

    prescriptions_list = []
    for p in PRESCRIPTIONS:
        medicine = get_medicine_by_id(p['kode_obat'])
        treatment = get_treatment_by_id(p['kode_perawatan'])
        
        if medicine and treatment:
            total_harga = p['kuantitas_obat'] * medicine['harga']
            
            prescriptions_list.append({
                'kode_perawatan': p['kode_perawatan'],
                'nama_perawatan': treatment['nama_perawatan'],
                'kode_obat': p['kode_obat'],
                'nama_obat': medicine['nama'],
                'kuantitas_obat': p['kuantitas_obat'],
                'total_harga': total_harga
            })
    
    if search_query:
        prescriptions_list = [p for p in prescriptions_list if 
                             search_query.lower() in p['nama_perawatan'].lower() or
                             search_query.lower() in p['kode_perawatan'].lower() or
                             search_query.lower() in p['nama_obat'].lower() or
                             search_query.lower() in p['kode_obat'].lower()]
    
    context = {
        'prescriptions': prescriptions_list,
        'medicines': medicines_list,
        'treatments': TREATMENTS,
        'search_query': search_query  
    }
    
    return render(request, 'prescription_list.html', context)

@staff_required
def add_prescription(request):
    """View function to add a new prescription to hardcoded data."""
    if request.method == 'POST':
        try:
            kode_perawatan = request.POST.get('jenis_perawatan')
            kode_obat = request.POST.get('obat')
            kuantitas = request.POST.get('kuantitas')

            if not all([kode_perawatan, kode_obat, kuantitas]):
                messages.error(request, 'Semua field harus diisi')
                return redirect('medications:prescription_list')

            try:
                kuantitas = int(kuantitas)
            except ValueError:
                messages.error(request, 'Kuantitas harus berupa angka')
                return redirect('medications:prescription_list')

            medicine = get_medicine_by_id(kode_obat)
            if not medicine:
                messages.error(request, 'Obat tidak ditemukan')
                return redirect('medications:prescription_list')
            
            if medicine['stok'] < kuantitas:
                messages.error(request, 'Stok obat tidak mencukupi')
                return redirect('medications:prescription_list')

            treatment = get_treatment_by_id(kode_perawatan)
            if not treatment:
                messages.error(request, 'Jenis perawatan tidak ditemukan')
                return redirect('medications:prescription_list')

            if any(p['kode_perawatan'] == kode_perawatan and p['kode_obat'] == kode_obat for p in PRESCRIPTIONS):
                messages.error(request, 'Resep untuk perawatan dan obat ini sudah ada')
                return redirect('medications:prescription_list')

            new_prescription = {
                'kode_perawatan': kode_perawatan,
                'kode_obat': kode_obat,
                'kuantitas_obat': kuantitas
            }
            
            PRESCRIPTIONS.append(new_prescription)

            medicine['stok'] -= kuantitas
            medicine['can_delete'] = False
            
            messages.success(request, 'Resep berhasil ditambahkan')
            
        except Exception as e:
            messages.error(request, f'Gagal menambahkan resep: {str(e)}')
    
    return redirect('medications:prescription_list')

@staff_required
def delete_prescription(request):
    """View function to delete a prescription from hardcoded data."""
    if request.method == 'POST':
        try:
            kode_perawatan = request.POST.get('kode_perawatan')
            kode_obat = request.POST.get('kode_obat')
            
            prescription = None
            prescription_index = -1
            
            for i, p in enumerate(PRESCRIPTIONS):
                if p['kode_perawatan'] == kode_perawatan and p['kode_obat'] == kode_obat:
                    prescription = p
                    prescription_index = i
                    break
            
            if not prescription:
                messages.error(request, f'Resep untuk jenis perawatan {kode_perawatan} dengan obat {kode_obat} tidak ditemukan')
                return redirect('medications:prescription_list')

            treatment = get_treatment_by_id(kode_perawatan)
            medicine = get_medicine_by_id(kode_obat)

            del PRESCRIPTIONS[prescription_index]

            if medicine:
                medicine['stok'] += prescription['kuantitas_obat']
                
                if not is_medicine_used(kode_obat):
                    medicine['can_delete'] = True
            
            treatment_name = treatment['nama_perawatan'] if treatment else kode_perawatan
            medicine_name = medicine['nama'] if medicine else kode_obat
            
            messages.success(request, f'Resep untuk perawatan {treatment_name} dengan obat {medicine_name} berhasil dihapus')
            
        except Exception as e:
            messages.error(request, f'Gagal menghapus resep: {str(e)}')
    
    return redirect('medications:prescription_list')

def client_required(view_func):
    """Decorator to restrict access to clients only."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('authentication:login')
        
        if request.session.get('user_type') != 'klien':
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

USER_CLIENTS = {
    'johndoe@example.com': 'c3073b2a-9fc2-47b6-b358-1912aefc4442',
    'janedoe@example.com': '550e8400-e29b-41d4-a716-446655440000',
    'bobsmith@example.com': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    'alicejones@example.com': '6a33b35c-9c8f-4ca0-9cf6-dce21e3d19a2',
    'mikelee@example.com': 'b6f8c3d2-e87a-4a1f-bc16-3c0a01837a8b'
}

# Mock Client Pets
# Maps client IDs to their pets
CLIENT_PETS = {
    'c3073b2a-9fc2-47b6-b358-1912aefc4442': ['Coco', 'Max'],
    '550e8400-e29b-41d4-a716-446655440000': ['Snowy', 'Luna'],
    'f47ac10b-58cc-4372-a567-0e02b2c3d479': ['Blacky', 'Rex'],
    '6a33b35c-9c8f-4ca0-9cf6-dce21e3d19a2': ['Luna', 'Charlie'],
    'b6f8c3d2-e87a-4a1f-bc16-3c0a01837a8b': ['Bubbles', 'Rocky'],
}

# Mock Prescription Data
# A list of all prescriptions in the system
PRESCRIPTIONS = [
    {
        'id': '001',
        'client_id': 'c3073b2a-9fc2-47b6-b358-1912aefc4442',
        'pet_name': 'Coco',
        'perawatan': {'kode': 'TRM003', 'nama_perawatan': 'TRM003 - Pemeriksaan Telinga'},
        'obat': {'kode': 'MED003', 'nama': 'MED003 - Amitraz'},
        'kuantitas_obat': 2,
        'visit_date': '2025-04-15'
    },
    {
        'id': '002',
        'client_id': 'c3073b2a-9fc2-47b6-b358-1912aefc4442',
        'pet_name': 'Max',
        'perawatan': {'kode': 'TRM001', 'nama_perawatan': 'TRM001 - Perawatan Gigi'},
        'obat': {'kode': 'MED001', 'nama': 'MED001 - Penicillin'},
        'kuantitas_obat': 3,
        'visit_date': '2025-04-10'
    },
    {
        'id': '003',
        'client_id': '550e8400-e29b-41d4-a716-446655440000',
        'pet_name': 'Snowy',
        'perawatan': {'kode': 'TRM002', 'nama_perawatan': 'TRM002 - Parasite Control'},
        'obat': {'kode': 'MED002', 'nama': 'MED002 - Aminophyllin'},
        'kuantitas_obat': 4,
        'visit_date': '2025-04-20'
    },
    {
        'id': '004',
        'client_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
        'pet_name': 'Blacky',
        'perawatan': {'kode': 'TRM001', 'nama_perawatan': 'TRM001 - Perawatan Gigi'},
        'obat': {'kode': 'MED001', 'nama': 'MED001 - Penicillin'},
        'kuantitas_obat': 3,
        'visit_date': '2025-04-18'
    },
    {
        'id': '005',
        'client_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
        'pet_name': 'Rex',
        'perawatan': {'kode': 'TRM002', 'nama_perawatan': 'TRM002 - Parasite Control'},
        'obat': {'kode': 'MED002', 'nama': 'MED002 - Aminophyllin'},
        'kuantitas_obat': 4,
        'visit_date': '2025-04-12'
    },
    {
        'id': '006',
        'client_id': '6a33b35c-9c8f-4ca0-9cf6-dce21e3d19a2',
        'pet_name': 'Luna',
        'perawatan': {'kode': 'TRM004', 'nama_perawatan': 'TRM004 - Perawatan Kulit dan Bulu'},
        'obat': {'kode': 'MED004', 'nama': 'MED004 - Chlorhexidine'},
        'kuantitas_obat': 1,
        'visit_date': '2025-04-25'
    },
    {
        'id': '007',
        'client_id': 'b6f8c3d2-e87a-4a1f-bc16-3c0a01837a8b',
        'pet_name': 'Bubbles',
        'perawatan': {'kode': 'TRM005', 'nama_perawatan': 'TRM005 - Perawatan Luka Ringan'},
        'obat': {'kode': 'MED005', 'nama': 'MED005 - Betadine'},
        'kuantitas_obat': 2,
        'visit_date': '2025-04-22'
    }
]

def client_prescription(request):
    """
    View to display prescription data for the logged-in client using mock data.
    In a real application, this would query the database instead.
    """
    
    # Get the user's email
    user_email = request.user.email
    
    # For testing without a real logged-in user
    # Uncomment the line below and set an email to test
    # user_email = 'johndoe@example.com'
    
    # Get the client ID for this user from our mock data
    client_id = USER_CLIENTS.get(user_email)
    
    if not client_id:
        # If user not found in our mock data, return empty context
        return render(request, 'client_prescription.html', {'prescriptions': []})
    
    # Filter prescriptions for this client
    client_prescriptions = [
        prescription for prescription in PRESCRIPTIONS
        if prescription['client_id'] == client_id
    ]
    
    # Sort by visit date (newest first)
    client_prescriptions.sort(key=lambda x: x['visit_date'], reverse=True)
    
    context = {
        'prescriptions': client_prescriptions,
        'client_id': client_id,
        'pets': CLIENT_PETS.get(client_id, [])
    }
    
    return render(request, 'client_prescription.html', context)