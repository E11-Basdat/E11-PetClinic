from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from functools import wraps
from datetime import datetime

MEDICINES = [
    {
        'kode': 'MED001',
        'nama': 'Penicillin',
        'harga': 45000,
        'stok': 50,
        'dosis': '500mg/day',
        'can_delete': True
    },
    {
        'kode': 'MED002',
        'nama': 'Amoxicillin',
        'harga': 65000,
        'stok': 30,
        'dosis': '100mg/day',
        'can_delete': True  
    },
    {
        'kode': 'MED003',
        'nama': 'Antizol',
        'harga': 35000,
        'stok': 40,
        'dosis': '10mg/day',
        'can_delete': True  
    }
]

TREATMENTS = [
    {
        'kode_perawatan': 'TRM001',
        'nama_perawatan': 'Dental Care'
    },
    {
        'kode_perawatan': 'TRM002',
        'nama_perawatan': 'Parasite Control'
    },
    {
        'kode_perawatan': 'TRM003',
        'nama_perawatan': 'Flea Treatment'
    }
]

# In-memory data storage untuk resep (PERAWATAN_OBAT)
PRESCRIPTIONS = [
    {
        'kode_perawatan': 'TRM001',
        'kode_obat': 'MED001',
        'kuantitas_obat': 3
    },
    {
        'kode_perawatan': 'TRM002',
        'kode_obat': 'MED002',
        'kuantitas_obat': 4
    },
    {
        'kode_perawatan': 'TRM003',
        'kode_obat': 'MED003',
        'kuantitas_obat': 2
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
    """Get medicine by ID"""
    for med in MEDICINES:
        if med['kode'] == kode:
            return med
    return None

def is_medicine_used(kode):
    """Check if a medicine is used in prescriptions"""
    for p in PRESCRIPTIONS:
        if p['kode_obat'] == kode:
            return True
    return False

def get_treatment_by_id(kode):
    """Get treatment by ID"""
    for t in TREATMENTS:
        if t['kode_perawatan'] == kode:
            return t
    return None

def generate_medicine_code():
    """Generate a new medicine code"""
    existing_codes = [m['kode'] for m in MEDICINES]
    if not existing_codes:
        return "MED001"
    
    max_code = max(existing_codes)
    code_num = int(max_code[3:])
    next_code = f"MED{code_num + 1:03d}"
    return next_code

def calculate_prescription_total(prescription):
    """Calculate total price for a prescription"""
    medicine = get_medicine_by_id(prescription['kode_obat'])
    if medicine:
        return prescription['kuantitas_obat'] * medicine['harga']
    return 0

@staff_required
def medicine_list(request):
    """View function to display list of medicines."""
    search_query = request.GET.get('search', '')

    if search_query:
        medicines = [m for m in MEDICINES if search_query.lower() in m['nama'].lower()]
    else:
        medicines = MEDICINES
    
    medicines_for_template = []
    for med in medicines:
        medicines_for_template.append({
            'id': int(med['kode'][3:]),  
            'code': med['kode'],
            'name': med['nama'],
            'price': med['harga'],
            'stock': med['stok'],
            'dosage': med['dosis'],
            'canDelete': med['can_delete']
        })
    
    context = {
        'medicines': medicines_for_template,
        'search_query': search_query
    }
    
    return render(request, 'medicine_list.html', context)

@staff_required
def add_medicine(request):
    """View function to add a new medicine."""
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = request.POST.get('harga_satuan')
            dosis = request.POST.get('dosis')
            stok = request.POST.get('stok_awal')
            
            if not nama or not harga or not dosis or not stok:
                messages.error(request, 'Semua field harus diisi')
                return render(request, 'add_medicine.html')
            
            harga = int(harga)
            stok = int(stok)
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return render(request, 'add_medicine.html')
            
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
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
            
        except ValueError:
            messages.error(request, 'Harga dan stok harus berupa angka')
        except Exception as e:
            messages.error(request, f'Gagal menambahkan obat: {str(e)}')
    
    return render(request, 'add_medicine.html')

@staff_required
def update_medicine(request, kode):
    """View function to update an existing medicine."""
    medicine = get_medicine_by_id(kode)
    
    if not medicine:
        messages.error(request, f'Obat dengan kode {kode} tidak ditemukan')
        return redirect('medications:list')
    
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            harga = request.POST.get('harga_satuan')  
            dosis = request.POST.get('dosis')

            if not nama or not harga or not dosis:
                messages.error(request, 'Semua field harus diisi')
                return redirect('medications:list')

            harga = int(harga)
            
            if harga < 0:
                messages.error(request, "Harga tidak boleh bernilai negatif")
                return redirect('medications:list')

            medicine['nama'] = nama
            medicine['harga'] = harga
            medicine['dosis'] = dosis
            
            messages.success(request, f'Obat {nama} berhasil diperbarui')
            return redirect('medications:list')
            
        except ValueError:
            messages.error(request, 'Harga harus berupa angka')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui obat: {str(e)}')
    
    return redirect('medications:list')

@staff_required
def update_stock(request, kode):
    """View function to update medicine stock."""
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

            stok = int(stok)
            
            if stok < 0:
                messages.error(request, "Stok tidak boleh bernilai negatif")
                return redirect('medications:list')

            medicine['stok'] = stok
            
            messages.success(request, f'Stok untuk {medicine["nama"]} berhasil diperbarui')
            return redirect('medications:list')
            
        except ValueError:
            messages.error(request, 'Stok harus berupa angka')
            return redirect('medications:list')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui stok: {str(e)}')
            return redirect('medications:list')
    
    return redirect('medications:list')

@staff_required
def delete_medicine(request, kode):
    """View function to delete a medicine."""
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
            return redirect('medications:list')
            
        except Exception as e:
            messages.error(request, f'Gagal menghapus obat: {str(e)}')
    
    return render(request, 'delete_medicine.html', {'medicine': medicine})

@staff_required
def prescription_list(request):
    """View function to display list of prescriptions."""
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
    
    context = {
        'prescriptions': prescriptions_list,
        'medicines': medicines_list,
        'treatments': TREATMENTS
    }
    
    return render(request, 'prescription_list.html', context)

@staff_required
def add_prescription(request):
    """View function to add a new prescription."""
    if request.method == 'POST':
        try:
            kode_perawatan = request.POST.get('jenis_perawatan')
            kode_obat = request.POST.get('obat')
            kuantitas = request.POST.get('kuantitas')

            if not kode_perawatan or not kode_obat or not kuantitas:
                messages.error(request, 'Semua field harus diisi')
                return redirect('medications:prescription_list')

            kuantitas = int(kuantitas)

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

            for p in PRESCRIPTIONS:
                if p['kode_perawatan'] == kode_perawatan and p['kode_obat'] == kode_obat:
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
            
        except ValueError:
            messages.error(request, 'Kuantitas harus berupa angka')
        except Exception as e:
            messages.error(request, f'Gagal menambahkan resep: {str(e)}')
    
    return redirect('medications:prescription_list')

@staff_required
def delete_prescription(request):
    """View function to delete a prescription."""
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