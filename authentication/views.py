from django.shortcuts import render, redirect
from django.contrib import messages
import uuid
from datetime import date


USERS = {
    'front_desk@petclinic.com': {
        'email': 'front_desk@petclinic.com',
        'password': 'password123',
        'alamat': 'Jl. Front Desk No. 1',
        'nomor_telepon': '081234567890'
    },
    'dokter@petclinic.com': {
        'email': 'dokter@petclinic.com',
        'password': 'password123',
        'alamat': 'Jl. Dokter No. 2',
        'nomor_telepon': '081234567891'
    },
    'perawat@petclinic.com': {
        'email': 'perawat@petclinic.com',
        'password': 'password123',
        'alamat': 'Jl. Perawat No. 3',
        'nomor_telepon': '081234567892'
    },
    'individu@petclinic.com': {
        'email': 'individu@petclinic.com',
        'password': 'password123',
        'alamat': 'Jl. Individu No. 4',
        'nomor_telepon': '081234567893'
    },
    'perusahaan@petclinic.com': {
        'email': 'perusahaan@petclinic.com',
        'password': 'password123',
        'alamat': 'Jl. Perusahaan No. 5',
        'nomor_telepon': '081234567894'
    }
}

PEGAWAI = {
    'j0k1l2m3-n4o5-6789-jklm-012345678901': {
        'no_pegawai': 'j0k1l2m3-n4o5-6789-jklm-012345678901',
        'tanggal_mulai_kerja': '2022-01-01',
        'tanggal_akhir_kerja': None,
        'email_user': 'front_desk@petclinic.com'
    },
    'c3d4e5f6-a7b8-9012-cdef-345678901234': {
        'no_pegawai': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'tanggal_mulai_kerja': '2022-01-02',
        'tanggal_akhir_kerja': None,
        'email_user': 'dokter@petclinic.com'
    },
    'k1l2m3n4-o5p6-7890-klmn-123456789012': {
        'no_pegawai': 'k1l2m3n4-o5p6-7890-klmn-123456789012',
        'tanggal_mulai_kerja': '2022-01-03',
        'tanggal_akhir_kerja': None,
        'email_user': 'perawat@petclinic.com'
    }
}

FRONT_DESK = {
    'j0k1l2m3-n4o5-6789-jklm-012345678901': {'no_front_desk': 'j0k1l2m3-n4o5-6789-jklm-012345678901'}
}

TENAGA_MEDIS = {
    'c3d4e5f6-a7b8-9012-cdef-345678901234': {
        'no_tenaga_medis': 'c3d4e5f6-a7b8-9012-cdef-345678901234',
        'no_izin_praktik': 'IP-DOC-001'
    },
    'k1l2m3n4-o5p6-7890-klmn-123456789012': {
        'no_tenaga_medis': 'k1l2m3n4-o5p6-7890-klmn-123456789012',
        'no_izin_praktik': 'IP-NURSE-001'
    }
}

DOKTER_HEWAN = {
    'c3d4e5f6-a7b8-9012-cdef-345678901234': {'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234'}
}

PERAWAT_HEWAN = {
    'k1l2m3n4-o5p6-7890-klmn-123456789012': {'no_perawat_hewan': 'k1l2m3n4-o5p6-7890-klmn-123456789012'}
}

SERTIFIKAT_KOMPETENSI = [
    {'no_sertifikat_kompetensi': 'CERT-001', 'no_tenaga_medis': 'c3d4e5f6-a7b8-9012-cdef-345678901234', 'nama_sertifikat': 'Sertifikat Dokter Hewan'},
    {'no_sertifikat_kompetensi': 'CERT-002', 'no_tenaga_medis': 'c3d4e5f6-a7b8-9012-cdef-345678901234', 'nama_sertifikat': 'Sertifikat Bedah Hewan'},
    {'no_sertifikat_kompetensi': 'CERT-003', 'no_tenaga_medis': 'k1l2m3n4-o5p6-7890-klmn-123456789012', 'nama_sertifikat': 'Sertifikat Perawat Hewan'}
]

JADWAL_PRAKTIK = [
    {'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234', 'hari': 'Senin', 'jam': '08:00-12:00'},
    {'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234', 'hari': 'Rabu', 'jam': '13:00-17:00'},
    {'no_dokter_hewan': 'c3d4e5f6-a7b8-9012-cdef-345678901234', 'hari': 'Jumat', 'jam': '08:00-15:00'}
]

KLIEN = {
    'b2c3d4e5-f6a7-8901-bcde-f23456789012': {
        'no_identitas': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        'tanggal_registrasi': '2022-02-01',
        'email': 'individu@petclinic.com'
    },
    'e5f6a7b8-c9d0-1234-efgh-567890123456': {
        'no_identitas': 'e5f6a7b8-c9d0-1234-efgh-567890123456',
        'tanggal_registrasi': '2022-02-02',
        'email': 'perusahaan@petclinic.com'
    }
}

INDIVIDU = {
    'b2c3d4e5-f6a7-8901-bcde-f23456789012': {
        'no_identitas_klien': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        'nama_depan': 'Hanni',
        'nama_tengah': '',
        'nama_belakang': 'Pham'
    }
}

PERUSAHAAN = {
    'e5f6a7b8-c9d0-1234-efgh-567890123456': {
        'no_identitas_klien': 'e5f6a7b8-c9d0-1234-efgh-567890123456',
        'nama_perusahaan': 'PT Newjeans'
    }
}

HEWAN = [
    {
        'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'nama': 'Acu',
        'tanggal_lahir': '2020-05-15',  
        'id_jenis': 'f6a7b8c9-d0e1-2345-fghi-678901234567',
        'no_identitas_klien': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        'url_foto': 'https://example.com/Acu.jpg'  
    },
    {
        'id': 'd4e5f6a7-b8c9-0123-defg-456789012345',
        'nama': 'Aci',
        'tanggal_lahir': '2019-10-20',  
        'id_jenis': 'h8i9j0k1-l2m3-4567-hijk-890123456789',
        'no_identitas_klien': 'b2c3d4e5-f6a7-8901-bcde-f23456789012',
        'url_foto': 'https://example.com/Aci.jpg'  
    },
    {
        'id': 'l2m3n4o5-p6q7-8901-lmno-234567890123',
        'nama': 'Beyyi',
        'tanggal_lahir': '2021-03-10',  
        'id_jenis': 'h8i9j0k1-l2m3-4567-hijk-890123456789',
        'no_identitas_klien': 'e5f6a7b8-c9d0-1234-efgh-567890123456',
        'url_foto': 'https://example.com/Beyyi.jpg'  
    }
]

JENIS_HEWAN = {
    'f6a7b8c9-d0e1-2345-fghi-678901234567': {'id': 'f6a7b8c9-d0e1-2345-fghi-678901234567', 'nama_jenis': 'Kucing'},
    'h8i9j0k1-l2m3-4567-hijk-890123456789': {'id': 'h8i9j0k1-l2m3-4567-hijk-890123456789', 'nama_jenis': 'Anjing'}
}


def get_sertifikat_data(no_tenaga_medis):
    """Get certificate data for medical staff"""
    cert_data = []
    for cert in SERTIFIKAT_KOMPETENSI:
        if cert['no_tenaga_medis'] == no_tenaga_medis:
            cert_data.append({
                'no_sertifikat_kompetensi': cert['no_sertifikat_kompetensi'], 
                'nama_sertifikat': cert['nama_sertifikat']
            })
    return cert_data

def get_jadwal_data(no_dokter_hewan):
    """Get schedule data for a doctor"""
    jadwal_data = []
    for jadwal in JADWAL_PRAKTIK:
        if jadwal['no_dokter_hewan'] == no_dokter_hewan:
            jadwal_data.append({
                'hari': jadwal['hari'], 
                'jam': jadwal['jam']
            })
    return jadwal_data

def get_user_type(email):
    """Determine user type based on email"""
    
    for fd_id, fd in FRONT_DESK.items():
        if PEGAWAI[fd_id]['email_user'] == email:
            return 'front_desk'
    
    
    for doc_id, doc in DOKTER_HEWAN.items():
        if PEGAWAI[doc_id]['email_user'] == email:
            return 'dokter'
    
    
    for nurse_id, nurse in PERAWAT_HEWAN.items():
        if PEGAWAI[nurse_id]['email_user'] == email:
            return 'perawat'
    
    
    for client_id, client in INDIVIDU.items():
        if KLIEN[client_id]['email'] == email:
            return 'individu'
    
    
    for client_id, client in PERUSAHAAN.items():
        if KLIEN[client_id]['email'] == email:
            return 'perusahaan'
    
    return None

def get_user_data(request):
    """Helper function to get user data based on session"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    if not user_email or not user_type or user_email not in USERS:
        return None
    
    user = USERS[user_email]
    result = {
        'email': user['email'],
        'alamat': user['alamat'],
        'nomor_telepon': user['nomor_telepon'],
        'user_type': user_type
    }
    
    if user_type == 'front_desk':
        for no_pegawai, pegawai in PEGAWAI.items():
            if pegawai['email_user'] == user_email:
                result.update({
                    'no_pegawai': no_pegawai,
                    'tanggal_mulai_kerja': pegawai['tanggal_mulai_kerja'],
                    'tanggal_akhir_kerja': pegawai['tanggal_akhir_kerja']
                })
                break
                
    elif user_type == 'dokter':
        for no_pegawai, pegawai in PEGAWAI.items():
            if pegawai['email_user'] == user_email and no_pegawai in TENAGA_MEDIS:
                result.update({
                    'no_pegawai': no_pegawai,
                    'tanggal_mulai_kerja': pegawai['tanggal_mulai_kerja'],
                    'tanggal_akhir_kerja': pegawai['tanggal_akhir_kerja'],
                    'no_izin_praktik': TENAGA_MEDIS[no_pegawai]['no_izin_praktik']
                })
                result['sertifikat'] = get_sertifikat_data(no_pegawai)
                result['jadwal'] = get_jadwal_data(no_pegawai)
                break
                
    elif user_type == 'perawat':
        for no_pegawai, pegawai in PEGAWAI.items():
            if pegawai['email_user'] == user_email and no_pegawai in TENAGA_MEDIS:
                result.update({
                    'no_pegawai': no_pegawai,
                    'tanggal_mulai_kerja': pegawai['tanggal_mulai_kerja'],
                    'tanggal_akhir_kerja': pegawai['tanggal_akhir_kerja'],
                    'no_izin_praktik': TENAGA_MEDIS[no_pegawai]['no_izin_praktik']
                })
                result['sertifikat'] = get_sertifikat_data(no_pegawai)
                break
                
    elif user_type == 'individu':
        for no_identitas, klien in KLIEN.items():
            if klien['email'] == user_email and no_identitas in INDIVIDU:
                individu = INDIVIDU[no_identitas]
                result.update({
                    'no_identitas': no_identitas,
                    'tanggal_registrasi': klien['tanggal_registrasi'],
                    'nama_depan': individu['nama_depan'],
                    'nama_tengah': individu['nama_tengah'],
                    'nama_belakang': individu['nama_belakang']
                })
                break
                
    elif user_type == 'perusahaan':
        for no_identitas, klien in KLIEN.items():
            if klien['email'] == user_email and no_identitas in PERUSAHAAN:
                perusahaan = PERUSAHAAN[no_identitas]
                result.update({
                    'no_identitas': no_identitas,
                    'tanggal_registrasi': klien['tanggal_registrasi'],
                    'nama_perusahaan': perusahaan['nama_perusahaan']
                })
                break
                
    return result

def show_pengguna(request):
    return render(request, 'pengguna.html')

def dashboard(request):
    """Unified dashboard for all user types"""
    
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    
    if not user_data:
        if 'user_email' in request.session:
            del request.session['user_email']
        if 'user_type' in request.session:
            del request.session['user_type']
        messages.error(request, 'User data not found. Please login again.')
        return redirect('authentication:login')
    
    return render(request, 'dashboard.html', {'user_data': user_data})

def login_user(request):
    """View function to handle user login."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email in USERS and USERS[email]['password'] == password:
            request.session['user_email'] = email
            
            user_type = get_user_type(email)
            if user_type:
                request.session['user_type'] = user_type
            
            return redirect('authentication:dashboard')
        else:
            messages.info(request, 'Username or password is incorrect!')
    return render(request, 'login.html')

def logout_user(request):
    """View function to handle user logout."""
    
    if 'user_email' in request.session:
        del request.session['user_email']
    if 'user_type' in request.session:
        del request.session['user_type']
    
    return redirect('authentication:pengguna')

def handle_certificates(no_tenaga_medis, cert_numbers, cert_names):
    """Helper function to handle certificate CRUD operations"""
    
    
    existing_certs = {}
    for cert in SERTIFIKAT_KOMPETENSI:
        if cert['no_tenaga_medis'] == no_tenaga_medis:
            existing_certs[cert['no_sertifikat_kompetensi']] = cert['nama_sertifikat']
    
    
    processed_certs = set()
    for i in range(len(cert_numbers)):
        cert_number = cert_numbers[i]
        cert_name = cert_names[i]
        
        if cert_number in existing_certs:
            
            for cert in SERTIFIKAT_KOMPETENSI:
                if cert['no_sertifikat_kompetensi'] == cert_number and cert['no_tenaga_medis'] == no_tenaga_medis:
                    cert['nama_sertifikat'] = cert_name
                    break
        else:
            
            SERTIFIKAT_KOMPETENSI.append({
                'no_sertifikat_kompetensi': cert_number,
                'no_tenaga_medis': no_tenaga_medis,
                'nama_sertifikat': cert_name
            })
        
        processed_certs.add(cert_number)
    
    
    for cert_number in existing_certs:
        if cert_number not in processed_certs:
            for i, cert in enumerate(SERTIFIKAT_KOMPETENSI):
                if cert['no_sertifikat_kompetensi'] == cert_number and cert['no_tenaga_medis'] == no_tenaga_medis:
                    del SERTIFIKAT_KOMPETENSI[i]
                    break

def handle_schedules(no_dokter_hewan, days, hours):
    """Helper function to handle doctor schedule CRUD operations"""
    
    
    existing_schedules = {}
    for schedule in JADWAL_PRAKTIK:
        if schedule['no_dokter_hewan'] == no_dokter_hewan:
            existing_schedules[schedule['hari']] = schedule['jam']
    
    
    processed_days = set()
    for i in range(len(days)):
        day = days[i]
        hour = hours[i]
        
        if day in existing_schedules:
            
            for schedule in JADWAL_PRAKTIK:
                if schedule['no_dokter_hewan'] == no_dokter_hewan and schedule['hari'] == day:
                    schedule['jam'] = hour
                    break
        else:
            
            JADWAL_PRAKTIK.append({
                'no_dokter_hewan': no_dokter_hewan,
                'hari': day,
                'jam': hour
            })
        
        processed_days.add(day)
    
    
    for day in existing_schedules:
        if day not in processed_days:
            for i, schedule in enumerate(JADWAL_PRAKTIK):
                if schedule['no_dokter_hewan'] == no_dokter_hewan and schedule['hari'] == day:
                    del JADWAL_PRAKTIK[i]
                    break

def register_user(request):
    """View function to handle user registration."""

    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            
            if email in USERS:
                messages.error(request, 'Email already exists!')
                return render(request, 'register.html')
            
            
            USERS[email] = {
                'email': email,
                'password': password,
                'alamat': alamat,
                'nomor_telepon': nomor_telepon
            }
            
            if user_type == 'front_desk':
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                pegawai_id = str(uuid.uuid4())
                
                PEGAWAI[pegawai_id] = {
                    'no_pegawai': pegawai_id,
                    'tanggal_mulai_kerja': tanggal_mulai_kerja,
                    'tanggal_akhir_kerja': None,
                    'email_user': email
                }
                
                FRONT_DESK[pegawai_id] = {'no_front_desk': pegawai_id}
                
            elif user_type in ['dokter', 'perawat']:
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                no_izin_praktik = request.POST.get('no_izin_praktik')
                pegawai_id = str(uuid.uuid4())
                
                PEGAWAI[pegawai_id] = {
                    'no_pegawai': pegawai_id,
                    'tanggal_mulai_kerja': tanggal_mulai_kerja,
                    'tanggal_akhir_kerja': None,
                    'email_user': email
                }
                
                TENAGA_MEDIS[pegawai_id] = {
                    'no_tenaga_medis': pegawai_id,
                    'no_izin_praktik': no_izin_praktik
                }
                
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                handle_certificates(pegawai_id, cert_numbers, cert_names)
                
                if user_type == 'dokter':
                    DOKTER_HEWAN[pegawai_id] = {'no_dokter_hewan': pegawai_id}
                    
                    days = request.POST.getlist('hari[]')
                    hours = request.POST.getlist('jam[]')
                    handle_schedules(pegawai_id, days, hours)
                            
                else:  
                    PERAWAT_HEWAN[pegawai_id] = {'no_perawat_hewan': pegawai_id}
                    
            elif user_type in ['individu', 'perusahaan']:
                klien_id = str(uuid.uuid4())
                today = date.today().strftime('%Y-%m-%d')
                
                KLIEN[klien_id] = {
                    'no_identitas': klien_id,
                    'tanggal_registrasi': today,
                    'email': email
                }
                
                if user_type == 'individu':
                    nama_depan = request.POST.get('nama_depan')
                    nama_tengah = request.POST.get('nama_tengah', '')
                    nama_belakang = request.POST.get('nama_belakang')
                    
                    INDIVIDU[klien_id] = {
                        'no_identitas_klien': klien_id,
                        'nama_depan': nama_depan,
                        'nama_tengah': nama_tengah,
                        'nama_belakang': nama_belakang
                    }
                    
                else:  
                    nama_perusahaan = request.POST.get('nama_perusahaan')
                    
                    PERUSAHAAN[klien_id] = {
                        'no_identitas_klien': klien_id,
                        'nama_perusahaan': nama_perusahaan
                    }
            
            request.session['user_email'] = email
            request.session['user_type'] = user_type
            
            messages.success(request, 'Account created successfully!')
            
            return redirect('authentication:login') 
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
    
    return render(request, 'register.html')

def update_password(request):
    """View function to handle password updates."""
    
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to update your password.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user_email = request.session.get('user_email')
        
        if user_email not in USERS or USERS[user_email]['password'] != current_password:
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        
        USERS[user_email]['password'] = new_password
            
        messages.success(request, 'Password updated successfully.')
        return redirect('authentication:dashboard')
    
    return render(request, 'update_password.html', {'user_data': user_data})

def update_profile(request):
    """View function to handle profile updates."""
    
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to update your profile.')
        return redirect('authentication:login')
    
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    user_data = get_user_data(request)
    
    if request.method == 'POST':
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            
            USERS[user_email]['alamat'] = alamat
            USERS[user_email]['nomor_telepon'] = nomor_telepon
            
            if user_type == 'individu':
                nama_depan = request.POST.get('nama_depan')
                nama_tengah = request.POST.get('nama_tengah', '')
                nama_belakang = request.POST.get('nama_belakang')
                
                for no_identitas, klien in KLIEN.items():
                    if klien['email'] == user_email and no_identitas in INDIVIDU:
                        INDIVIDU[no_identitas]['nama_depan'] = nama_depan
                        INDIVIDU[no_identitas]['nama_tengah'] = nama_tengah
                        INDIVIDU[no_identitas]['nama_belakang'] = nama_belakang
                        break
                
            elif user_type == 'perusahaan':
                nama_perusahaan = request.POST.get('nama_perusahaan')
                
                for no_identitas, klien in KLIEN.items():
                    if klien['email'] == user_email and no_identitas in PERUSAHAAN:
                        PERUSAHAAN[no_identitas]['nama_perusahaan'] = nama_perusahaan
                        break
                
            elif user_type in ['front_desk', 'dokter', 'perawat']:
                tanggal_akhir_kerja = request.POST.get('tanggal_akhir_kerja')
                
                for no_pegawai, pegawai in PEGAWAI.items():
                    if pegawai['email_user'] == user_email:
                        PEGAWAI[no_pegawai]['tanggal_akhir_kerja'] = tanggal_akhir_kerja if tanggal_akhir_kerja else None
                        break
            
            
            if user_type in ['dokter', 'perawat']:
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                
                for no_pegawai, pegawai in PEGAWAI.items():
                    if pegawai['email_user'] == user_email:
                        handle_certificates(no_pegawai, cert_numbers, cert_names)
                        break
            
            
            if user_type == 'dokter':
                days = request.POST.getlist('hari[]')
                hours = request.POST.getlist('jam[]')
                
                for no_pegawai, pegawai in PEGAWAI.items():
                    if pegawai['email_user'] == user_email:
                        handle_schedules(no_pegawai, days, hours)
                        break
        
            messages.success(request, 'Profile updated successfully!')
            return redirect('authentication:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'update_profile.html', {'user_data': user_data})

def list_client(request):
    """View function to display all clients."""
    
    if not request.session.get('user_email') or request.session.get('user_type') != 'front_desk':
        messages.error(request, 'Only Front Desk officers can access this page.')
        return redirect('authentication:dashboard')
    
    user_data = get_user_data(request)
    
    clients_list = []
    
    
    for client_id, client in INDIVIDU.items():
        if client_id in KLIEN:
            klien = KLIEN[client_id]
            user = USERS.get(klien['email'], {})
            
            nama_lengkap = client['nama_depan']
            if client['nama_tengah']:
                nama_lengkap += " " + client['nama_tengah']
            if client['nama_belakang']:
                nama_lengkap += " " + client['nama_belakang']
                
            clients_list.append({
                'no_identitas': client_id,
                'email': klien['email'],
                'alamat': user.get('alamat', ''),
                'nama': nama_lengkap.strip(),
                'jenis': 'Individu',
            })
    
    
    for client_id, client in PERUSAHAAN.items():
        if client_id in KLIEN:
            klien = KLIEN[client_id]
            user = USERS.get(klien['email'], {})
            
            clients_list.append({
                'no_identitas': client_id,
                'email': klien['email'],
                'alamat': user.get('alamat', ''),
                'nama': client['nama_perusahaan'],
                'jenis': 'Perusahaan',
            })
    
    context = {
        'user_data': user_data,
        'clients': clients_list
    }
    
    return render(request, 'list_client.html', context)

def client_detail(request, no_identitas):
    """View function to display client details and their pets."""
    
    if not request.session.get('user_email') or request.session.get('user_type') != 'front_desk':
        messages.error(request, 'Only Front Desk officers can access this page.')
        return redirect('authentication:dashboard')
    
    user_data = get_user_data(request)
    
    client = {}
    client_jenis = ""
    
    
    if no_identitas in INDIVIDU:
        client_jenis = 'Individu'
    elif no_identitas in PERUSAHAAN:
        client_jenis = 'Perusahaan'
    
    if not client_jenis:
        messages.error(request, 'Client not found.')
        return redirect('authentication:list_client')
    
    
    if client_jenis == 'Individu':
        individu = INDIVIDU[no_identitas]
        klien = KLIEN[no_identitas]
        user = USERS.get(klien['email'], {})
        
        nama_lengkap = individu['nama_depan']
        if individu['nama_tengah']:
            nama_lengkap += " " + individu['nama_tengah']
        if individu['nama_belakang']:
            nama_lengkap += " " + individu['nama_belakang']
        
        client = {
            'no_identitas': no_identitas,
            'email': klien['email'],
            'alamat': user.get('alamat', ''),
            'nomor_telepon': user.get('nomor_telepon', ''),
            'tanggal_registrasi': klien['tanggal_registrasi'],
            'nama': nama_lengkap.strip(),
            'jenis': client_jenis
        }
    else:  
        perusahaan = PERUSAHAAN[no_identitas]
        klien = KLIEN[no_identitas]
        user = USERS.get(klien['email'], {})
        
        client = {
            'no_identitas': no_identitas,
            'email': klien['email'],
            'alamat': user.get('alamat', ''),
            'nomor_telepon': user.get('nomor_telepon', ''),
            'tanggal_registrasi': klien['tanggal_registrasi'],
            'nama': perusahaan['nama_perusahaan'],
            'jenis': client_jenis
        }
    
    
    pets = []
    for pet in HEWAN:
        if pet['no_identitas_klien'] == no_identitas:
            jenis = JENIS_HEWAN.get(pet['id_jenis'], {}).get('nama_jenis', 'Unknown')
            
            pets.append({
                'id': pet['id'],
                'nama': pet['nama'],
                'tanggal_lahir': pet['tanggal_lahir'],
                'jenis': jenis
            })
    
    context = {
        'user_data': user_data,
        'client': client,
        'pets': pets
    }
    
    return render(request, 'client_detail.html', context)

