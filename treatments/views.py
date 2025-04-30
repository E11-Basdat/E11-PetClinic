from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from django.http import JsonResponse
from django.urls import reverse

def n_treatment_list(request):
    return render(request, 'n_treatment_list.html', {'user_role': 'else'})

def n_treatment_list_doctor(request):
    return render(request, 'n_treatment_list.html', {'user_role': 'doctor'})

def n_treatment_list_klien(request):
    return render(request, 'n_treatment_list.html', {'user_role': 'klien'})

def n_create_treatment(request):
    if request.method == 'POST':
        return redirect('treatments:n_treatment_list_doctor')
    return render(request, 'n_treatment_form.html', {'mode': 'create'})

def n_update_treatment(request, kunjungan_id):
    if request.method == 'POST':
        return redirect('treatments:n_treatment_list_doctor')
    
    return render(request, 'n_treatment_form.html', {'mode': 'update', 'kunjungan_id': kunjungan_id})

def n_delete_treatment(request, kunjungan_id):
    if request.method == 'POST':
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------
# ------------------------------------------Batas wilayah ---------------------------------------------------------------


TREATMENTS = [
    {
        'kode': 'TRM001',
        'nama': 'Dental Care',
        'biaya': 300000,
        'can_delete': True
    },
    {
        'kode': 'TRM002',
        'nama': 'Parasite Control',
        'biaya': 200000,
        'can_delete': True
    },
    {
        'kode': 'TRM003',
        'nama': 'Flea Treatment',
        'biaya': 180000,
        'can_delete': True
    },
    {
        'kode': 'TRM004',
        'nama': 'Wound Cleaning',
        'biaya': 150000,
        'can_delete': True
    },
    {
        'kode': 'TRM005',
        'nama': 'Eye Treatment',
        'biaya': 175000,
        'can_delete': True
    }
]

def medical_staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_email'):
            messages.error(request, "Silakan login terlebih dahulu.")
            return redirect('login')
        
        if request.session.get('user_type') not in ['dokter', 'perawat']:
            messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_treatments_list(search=None):
    if search:
        return [t for t in TREATMENTS if search.lower() in t['nama'].lower()]
    return TREATMENTS

def get_treatment_by_id(kode):
    for t in TREATMENTS:
        if t['kode'] == kode:
            return t
    return None

def generate_treatment_code():
    existing_codes = [t['kode'] for t in TREATMENTS]
    if not existing_codes:
        return "TRM001"
    
    max_code = max(existing_codes)
    code_num = int(max_code[3:])
    next_code = f"TRM{code_num + 1:03d}"
    return next_code

@medical_staff_required
def treatment_list(request):
    """View function to display list of treatments."""
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'add':
            return add_treatment(request)
        elif action == 'update':
            return update_treatment(request)
        elif action == 'delete':
            return delete_treatment(request)
    
    search_query = request.GET.get('search', '')
    treatments = get_treatments_list(search=search_query)
    
    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'price_low_high':
        treatments = sorted(treatments, key=lambda x: x['biaya'])
    elif sort_by == 'price_high_low':
        treatments = sorted(treatments, key=lambda x: x['biaya'], reverse=True)
    
    context = {
        'treatments': treatments,
        'search_query': search_query,
        'sort_by': sort_by
    }
    
    return render(request, 'treatment_list.html', context)

@medical_staff_required
def add_treatment(request):
    """Function to add a new treatment."""
    if request.method == 'POST':
        try:
            nama = request.POST.get('nama')
            biaya = int(request.POST.get('biaya'))
            
            if not nama:
                messages.error(request, "Nama perawatan tidak boleh kosong")
                return redirect('treatments:treatment_list')
            
            if biaya < 0:
                messages.error(request, "Biaya tidak boleh bernilai negatif")
                return redirect('treatments:treatment_list')
            
            kode = generate_treatment_code()
            
            new_treatment = {
                'kode': kode,
                'nama': nama,
                'biaya': biaya,
                'can_delete': True
            }
            
            TREATMENTS.append(new_treatment)
            
            messages.success(request, f"Jenis perawatan {nama} berhasil ditambahkan dengan kode {kode}")
            
        except ValueError:
            messages.error(request, "Biaya harus berupa angka")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan jenis perawatan: {str(e)}")
    
    return redirect('treatments:treatment_list')

@medical_staff_required
def update_treatment(request):
    """Function to update an existing treatment."""
    if request.method == 'POST':
        try:
            kode = request.POST.get('kode')
            nama = request.POST.get('nama')
            biaya = int(request.POST.get('biaya'))
            
            treatment = get_treatment_by_id(kode)
            if not treatment:
                messages.error(request, "Data jenis perawatan tidak ditemukan")
                return redirect('treatments:treatment_list')
            
            if not nama:
                messages.error(request, "Nama perawatan tidak boleh kosong")
                return redirect('treatments:treatment_list')
            
            if biaya < 0:
                messages.error(request, "Biaya tidak boleh bernilai negatif")
                return redirect('treatments:treatment_list')
            
            treatment['nama'] = nama
            treatment['biaya'] = biaya
            
            messages.success(request, f"Data jenis perawatan {nama} berhasil diperbarui")
            
        except ValueError:
            messages.error(request, "Biaya harus berupa angka")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data jenis perawatan: {str(e)}")
    
    return redirect('treatments:treatment_list')

@medical_staff_required
def delete_treatment(request):
    """Function to delete a treatment."""
    if request.method == 'POST':
        try:
            kode = request.POST.get('kode')
            
            treatment = get_treatment_by_id(kode)
            if not treatment:
                messages.error(request, "Data jenis perawatan tidak ditemukan")
                return redirect('treatments: treatment_list')
            
            if not treatment.get('can_delete', True):
                messages.error(request, "Jenis perawatan tidak dapat dihapus karena sedang digunakan")
                return redirect('treatments: treatment_list')
            
            TREATMENTS[:] = [t for t in TREATMENTS if t['kode'] != kode]
            
            messages.success(request, f"Jenis perawatan {treatment['nama']} berhasil dihapus")
            
        except Exception as e:
            messages.error(request, f"Gagal menghapus data jenis perawatan: {str(e)}")
    
    return redirect('treatments:treatment_list')