from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
import uuid
from datetime import date

def clean_error_message(message):
    """Remove the CONTEXT part from database error messages"""
    if isinstance(message, str) and 'CONTEXT:' in message:
        message = message.split('CONTEXT:')[0].strip()
    return message

def execute_query(query, params=None):
    """Execute a database query and return results"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        try:
            return cursor.fetchall()
        except Exception:
            return None

def execute_update_query(query, params=None):
    """Execute a database query (INSERT, UPDATE, DELETE) that doesn't return results"""
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, params or [])
            
            notices = get_pg_notices(cursor)
            return notices
        except Exception as e:
            raise e

def get_pg_notices(cursor):
    """Get PostgreSQL notice messages if available"""
    notices = []
    if hasattr(cursor.connection, 'notices') and cursor.connection.notices:
        notices = [notice.replace('NOTICE:  ', '') for notice in cursor.connection.notices.copy()]
        cursor.connection.notices.clear()
    return notices

def get_sertifikat_data(no_tenaga_medis):
    """Get certificate data for medical staff"""
    query = """
        SELECT no_sertifikat_kompetensi, nama_sertifikat 
        FROM petclinic.SERTIFIKAT_KOMPETENSI
        WHERE no_tenaga_medis = %s
    """
    cert_data = execute_query(query, [no_tenaga_medis])
    if cert_data:
        return [
            {'no_sertifikat_kompetensi': cert[0], 'nama_sertifikat': cert[1]} 
            for cert in cert_data
        ]
    return []

def get_jadwal_data(no_dokter_hewan):
    """Get schedule data for a doctor"""
    query = """
        SELECT hari, jam 
        FROM petclinic.JADWAL_PRAKTIK
        WHERE no_dokter_hewan = %s
    """
    jadwal_data = execute_query(query, [no_dokter_hewan])
    if jadwal_data:
        return [
            {'hari': jadwal[0], 'jam': jadwal[1]} 
            for jadwal in jadwal_data
        ]
    return []


def get_user_type(email):
    """Determine user type based on email"""
    user_types = [
        ('front_desk', """
            SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
            JOIN petclinic.FRONT_DESK fd ON p.no_pegawai = fd.no_front_desk
            WHERE p.email_user = %s
        """),
        ('dokter', """
            SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
            JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
            WHERE p.email_user = %s
        """),
        ('perawat', """
            SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
            JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
            WHERE p.email_user = %s
        """),
        ('individu', """
            SELECT k.no_identitas FROM petclinic.KLIEN k 
            JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            WHERE k.email = %s
        """),
        ('perusahaan', """
            SELECT k.no_identitas FROM petclinic.KLIEN k 
            JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE k.email = %s
        """)
    ]
    
    for user_type, query in user_types:
        if execute_query(query, [email]):
            return user_type
    
    return None

def get_user_data(request):
    """Helper function to get user data based on session"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    if not user_email or not user_type:
        return None
    
    user_data = execute_query("""
        SELECT email, alamat, nomor_telepon FROM petclinic."USER" 
        WHERE email = %s
    """, [user_email])
    
    if not user_data:
        return None
        
    result = {
        'email': user_data[0][0],
        'alamat': user_data[0][1],
        'nomor_telepon': user_data[0][2],
        'user_type': user_type
    }
    
    if user_type == 'front_desk':
        emp_data = execute_query("""
            SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja 
            FROM petclinic.PEGAWAI p 
            JOIN petclinic.FRONT_DESK fd ON p.no_pegawai = fd.no_front_desk
            WHERE p.email_user = %s
        """, [user_email])
        
        if emp_data:
            result.update({
                'no_pegawai': emp_data[0][0],
                'tanggal_mulai_kerja': emp_data[0][1],
                'tanggal_akhir_kerja': emp_data[0][2]
            })
            
    elif user_type == 'dokter':
        emp_data = execute_query("""
            SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja, tm.no_izin_praktik 
            FROM petclinic.PEGAWAI p 
            JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
            WHERE p.email_user = %s
        """, [user_email])
        
        if emp_data:
            result.update({
                'no_pegawai': emp_data[0][0],
                'tanggal_mulai_kerja': emp_data[0][1],
                'tanggal_akhir_kerja': emp_data[0][2],
                'no_izin_praktik': emp_data[0][3]
            })
            
            result['sertifikat'] = get_sertifikat_data(emp_data[0][0])
            
            
            if not emp_data[0][2] or emp_data[0][2] >= date.today():
                result['jadwal'] = get_jadwal_data(emp_data[0][0])
            else:
                result['jadwal'] = []
            
    elif user_type == 'perawat':
        emp_data = execute_query("""
            SELECT p.no_pegawai, p.tanggal_mulai_kerja, p.tanggal_akhir_kerja, tm.no_izin_praktik 
            FROM petclinic.PEGAWAI p 
            JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
            JOIN petclinic.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
            WHERE p.email_user = %s
        """, [user_email])
        
        if emp_data:
            result.update({
                'no_pegawai': emp_data[0][0],
                'tanggal_mulai_kerja': emp_data[0][1],
                'tanggal_akhir_kerja': emp_data[0][2],
                'no_izin_praktik': emp_data[0][3]
            })
            
            result['sertifikat'] = get_sertifikat_data(emp_data[0][0])
            
    elif user_type == 'individu':
        client_data = execute_query("""
            SELECT k.no_identitas, k.tanggal_registrasi, i.nama_depan, i.nama_tengah, i.nama_belakang
            FROM petclinic.KLIEN k 
            JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            WHERE k.email = %s
        """, [user_email])
        
        if client_data:
            result.update({
                'no_identitas': client_data[0][0],
                'tanggal_registrasi': client_data[0][1],
                'nama_depan': client_data[0][2],
                'nama_tengah': client_data[0][3],
                'nama_belakang': client_data[0][4]
            })
            
    elif user_type == 'perusahaan':
        client_data = execute_query("""
            SELECT k.no_identitas, k.tanggal_registrasi, p.nama_perusahaan
            FROM petclinic.KLIEN k 
            JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE k.email = %s
        """, [user_email])
        
        if client_data:
            result.update({
                'no_identitas': client_data[0][0],
                'tanggal_registrasi': client_data[0][1],
                'nama_perusahaan': client_data[0][2]
            })
            
    return result


def show_pengguna(request):
    if request.session.get('user_email'):
        return redirect('authentication:dashboard')
    return render(request, 'pengguna.html')

def dashboard(request):
    """Unified dashboard for all user types"""
    
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    
    print("User data for dashboard:", user_data)
    
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
        
        user = execute_query("""
            SELECT email, password FROM petclinic."USER" 
            WHERE email = %s AND password = %s
        """, [email, password])
        
        if user:
            request.session['user_email'] = user[0][0]
            
            
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
    cert_data = execute_query("""
        SELECT no_sertifikat_kompetensi, nama_sertifikat 
        FROM petclinic.SERTIFIKAT_KOMPETENSI
        WHERE no_tenaga_medis = %s
    """, [no_tenaga_medis])
    
    for row in cert_data:
        existing_certs[row[0]] = row[1]
    
    
    for i in range(len(cert_numbers)):
        cert_number = cert_numbers[i]
        cert_name = cert_names[i]
        
        if cert_number in existing_certs:
            
            if existing_certs[cert_number] != cert_name:
                execute_update_query("""
                    UPDATE petclinic.SERTIFIKAT_KOMPETENSI 
                    SET nama_sertifikat = %s
                    WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s
                """, [cert_name, cert_number, no_tenaga_medis])
            
            del existing_certs[cert_number]
        else:
            
            execute_update_query("""
                INSERT INTO petclinic.SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat)
                VALUES (%s, %s, %s)
            """, [cert_number, no_tenaga_medis, cert_name])
    
    
    for cert_number in existing_certs:
        execute_update_query("""
            DELETE FROM petclinic.SERTIFIKAT_KOMPETENSI
            WHERE no_sertifikat_kompetensi = %s AND no_tenaga_medis = %s
        """, [cert_number, no_tenaga_medis])


def handle_schedules(no_dokter_hewan, days, hours):
    """Helper function to handle doctor schedule CRUD operations"""
    
    existing_schedules = {}
    schedule_data = execute_query("""
        SELECT hari, jam 
        FROM petclinic.JADWAL_PRAKTIK
        WHERE no_dokter_hewan = %s
    """, [no_dokter_hewan])
    
    for row in schedule_data:
        existing_schedules[row[0]] = row[1]
    
    
    processed_days = set()
    
    for i in range(len(days)):
        day = days[i]
        hour = hours[i]
        
        if day in existing_schedules:
            
            if existing_schedules[day] != hour:
                execute_update_query("""
                    UPDATE petclinic.JADWAL_PRAKTIK 
                    SET jam = %s
                    WHERE no_dokter_hewan = %s AND hari = %s
                """, [hour, no_dokter_hewan, day])
            processed_days.add(day)
        else:
            
            execute_update_query("""
                INSERT INTO petclinic.JADWAL_PRAKTIK (no_dokter_hewan, hari, jam)
                VALUES (%s, %s, %s)
            """, [no_dokter_hewan, day, hour])
            processed_days.add(day)
    
    
    for day in existing_schedules:
        if day not in processed_days:
            execute_update_query("""
                DELETE FROM petclinic.JADWAL_PRAKTIK
                WHERE no_dokter_hewan = %s AND hari = %s
            """, [no_dokter_hewan, day])


def register_user(request):
    """View function to handle user registration."""

    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        
        email = request.POST.get('email')
        password = request.POST.get('password')
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            
            execute_update_query("""
                INSERT INTO petclinic."USER" (email, password, alamat, nomor_telepon)
                VALUES (%s, %s, %s, %s)
            """, [email, password, alamat, nomor_telepon])
            
            
            if user_type == 'front_desk':
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                pegawai_id = str(uuid.uuid4())
                
                execute_update_query("""
                    INSERT INTO petclinic.PEGAWAI (no_pegawai, tanggal_mulai_kerja, email_user)
                    VALUES (%s, %s, %s)
                """, [pegawai_id, tanggal_mulai_kerja, email])
                
                execute_update_query("""
                    INSERT INTO petclinic.FRONT_DESK (no_front_desk)
                    VALUES (%s)
                """, [pegawai_id])
                
            elif user_type in ['dokter', 'perawat']:
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                no_izin_praktik = request.POST.get('no_izin_praktik')
                pegawai_id = str(uuid.uuid4())
                
                execute_update_query("""
                    INSERT INTO petclinic.PEGAWAI (no_pegawai, tanggal_mulai_kerja, email_user)
                    VALUES (%s, %s, %s)
                """, [pegawai_id, tanggal_mulai_kerja, email])
                
                execute_update_query("""
                    INSERT INTO petclinic.TENAGA_MEDIS (no_tenaga_medis, no_izin_praktik)
                    VALUES (%s, %s)
                """, [pegawai_id, no_izin_praktik])
                
                
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                handle_certificates(pegawai_id, cert_numbers, cert_names)
                
                if user_type == 'dokter':
                    execute_update_query("""
                        INSERT INTO petclinic.DOKTER_HEWAN (no_dokter_hewan)
                        VALUES (%s)
                    """, [pegawai_id])
                    
                    
                    days = request.POST.getlist('hari[]')
                    hours = request.POST.getlist('jam[]')
                    handle_schedules(pegawai_id, days, hours)
                            
                else:  
                    execute_update_query("""
                        INSERT INTO petclinic.PERAWAT_HEWAN (no_perawat_hewan)
                        VALUES (%s)
                    """, [pegawai_id])
                    
            elif user_type in ['individu', 'perusahaan']:
                klien_id = str(uuid.uuid4())
                
                execute_update_query("""
                    INSERT INTO petclinic.KLIEN (no_identitas, tanggal_registrasi, email)
                    VALUES (%s, %s, %s)
                """, [klien_id, date.today(), email])
                
                if user_type == 'individu':
                    nama_depan = request.POST.get('nama_depan')
                    nama_tengah = request.POST.get('nama_tengah')
                    nama_belakang = request.POST.get('nama_belakang')
                    
                    execute_update_query("""
                        INSERT INTO petclinic.INDIVIDU (no_identitas_klien, nama_depan, nama_tengah, nama_belakang)
                        VALUES (%s, %s, %s, %s)
                    """, [klien_id, nama_depan, nama_tengah, nama_belakang])
                    
                else:  
                    nama_perusahaan = request.POST.get('nama_perusahaan')
                    
                    execute_update_query("""
                        INSERT INTO petclinic.PERUSAHAAN (no_identitas_klien, nama_perusahaan)
                        VALUES (%s, %s)
                    """, [klien_id, nama_perusahaan])
            
            
            request.session['user_email'] = email
            request.session['user_type'] = user_type
            
            if user_type in ['front_desk', 'dokter', 'perawat']:
                request.session['employee_id'] = pegawai_id
            
            elif user_type in ['individu', 'perusahaan']:
                request.session['client_id'] = klien_id
        
            messages.success(request, 'Account created successfully!')
            
            return redirect('authentication:login') 
            
        except Exception as e:
            messages.error(request, clean_error_message(str(e)))
    
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
        
        user = execute_query("""
            SELECT email FROM petclinic."USER" 
            WHERE email = %s AND password = %s
        """, [request.session.get('user_email'), current_password])
        
        if not user:
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        
        execute_update_query("""
            UPDATE petclinic."USER" SET password = %s
            WHERE email = %s
        """, [new_password, request.session.get('user_email')])
            
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
    
    if user_type in ['front_desk', 'dokter', 'perawat'] and 'tanggal_akhir_kerja' in user_data and user_data['tanggal_akhir_kerja']:
        user_data['tanggal_akhir_kerja'] = user_data['tanggal_akhir_kerja'].isoformat()
    
    if request.method == 'POST':
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            
            fields_changed = False
            if alamat != user_data['alamat'] or nomor_telepon != user_data['nomor_telepon']:
                execute_update_query("""
                    UPDATE petclinic."USER" SET alamat = %s, nomor_telepon = %s
                    WHERE email = %s
                """, [alamat, nomor_telepon, user_email])
                fields_changed = True
            
            
            if user_type == 'individu':
                nama_depan = request.POST.get('nama_depan')
                nama_tengah = request.POST.get('nama_tengah', '')
                nama_belakang = request.POST.get('nama_belakang')
                
                if (nama_depan != user_data.get('nama_depan', '') or 
                    nama_tengah != user_data.get('nama_tengah', '') or 
                    nama_belakang != user_data.get('nama_belakang', '')):
                    
                    execute_update_query("""
                        UPDATE petclinic.INDIVIDU SET nama_depan = %s, nama_tengah = %s, nama_belakang = %s
                        WHERE no_identitas_klien = %s
                    """, [nama_depan, nama_tengah, nama_belakang, user_data['no_identitas']])
                    fields_changed = True
                
            elif user_type == 'perusahaan':
                nama_perusahaan = request.POST.get('nama_perusahaan')
                
                if nama_perusahaan != user_data.get('nama_perusahaan', ''):
                    execute_update_query("""
                        UPDATE petclinic.PERUSAHAAN SET nama_perusahaan = %s
                        WHERE no_identitas_klien = %s
                    """, [nama_perusahaan, user_data['no_identitas']])
                    fields_changed = True
                
            elif user_type in ['front_desk', 'dokter', 'perawat']:
                tanggal_akhir_kerja = request.POST.get('tanggal_akhir_kerja')
                
                
                current_end_date = user_data.get('tanggal_akhir_kerja')
                if tanggal_akhir_kerja != current_end_date:
                    if tanggal_akhir_kerja:
                        notices = execute_update_query("""
                            UPDATE petclinic.PEGAWAI SET tanggal_akhir_kerja = %s
                            WHERE no_pegawai = %s
                        """, [tanggal_akhir_kerja, user_data['no_pegawai']])
                        print(f"DEBUG: Notices received: {notices}")
                        
                        for notice in notices:
                            messages.success(request, notice)
                    else:
                        execute_update_query("""
                            UPDATE petclinic.PEGAWAI SET tanggal_akhir_kerja = NULL
                            WHERE no_pegawai = %s
                        """, [user_data['no_pegawai']])
                    
                    fields_changed = True
                    
                    if user_type == 'dokter':
                        user_data = get_user_data(request)
            
            
            if user_type in ['dokter', 'perawat']:
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                
                
                current_certs = {cert['no_sertifikat_kompetensi']: cert['nama_sertifikat'] 
                               for cert in user_data.get('sertifikat', [])}
                
                new_certs = {cert_numbers[i]: cert_names[i] for i in range(len(cert_numbers))}
                
                if current_certs != new_certs:
                    handle_certificates(user_data['no_pegawai'], cert_numbers, cert_names)
                    fields_changed = True
            
            
            if user_type == 'dokter':
                
                end_date = user_data.get('tanggal_akhir_kerja')
                today = date.today()
                is_active = False
                
                if not end_date:
                    is_active = True
                elif isinstance(end_date, str):
                    try:
                        is_active = date.fromisoformat(end_date) >= today
                    except ValueError:
                        is_active = False
                else:
                    is_active = end_date >= today
                
                if is_active:
                    days = request.POST.getlist('hari[]')
                    hours = request.POST.getlist('jam[]')
                    
                    
                    current_schedules = {schedule['hari']: schedule['jam'] 
                                       for schedule in user_data.get('jadwal', [])}
                    
                    new_schedules = {days[i]: hours[i] for i in range(len(days))}
                    
                    if current_schedules != new_schedules:
                        handle_schedules(user_data['no_pegawai'], days, hours)
                        fields_changed = True
            
            if user_type == 'dokter' and tanggal_akhir_kerja and tanggal_akhir_kerja != current_end_date:
                end_date = None
                try:
                    end_date = date.fromisoformat(tanggal_akhir_kerja) if isinstance(tanggal_akhir_kerja, str) else tanggal_akhir_kerja
                except ValueError:
                    pass
                
                if end_date and end_date <= date.today():
                    
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE petclinic.PEGAWAI SET tanggal_akhir_kerja = %s
                            WHERE no_pegawai = %s
                        """, [tanggal_akhir_kerja, user_data['no_pegawai']])
                    
                    
                    notices = []
                    with connection.cursor() as cursor:
                        notices = get_pg_notices(cursor)
                        
                    for notice in notices:
                        messages.success(request, notice)
                    
                    fields_changed = True
                    return redirect('authentication:dashboard')
            
            if fields_changed:
                messages.success(request, 'Profile updated successfully!')
            else:
                messages.info(request, 'No changes detected in your profile.')
                
            return redirect('authentication:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {clean_error_message(str(e))}')
    
    return render(request, 'update_profile.html', {'user_data': user_data})

def list_client(request):
    """View function to display all clients."""
    
    if not request.session.get('user_email') or request.session.get('user_type') != 'front_desk':
        messages.error(request, 'Only Front Desk officers can access this page.')
        return redirect('authentication:dashboard')
    
    user_data = get_user_data(request)
    
    
    individual_clients = execute_query("""
        SELECT k.no_identitas, k.email, u.alamat, 
               i.nama_depan, i.nama_tengah, i.nama_belakang, 
               'Individu' as jenis
        FROM petclinic.KLIEN k
        JOIN petclinic."USER" u ON k.email = u.email
        JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
    """)
    
    
    company_clients = execute_query("""
        SELECT k.no_identitas, k.email, u.alamat, 
               p.nama_perusahaan, 
               'Perusahaan' as jenis
        FROM petclinic.KLIEN k
        JOIN petclinic."USER" u ON k.email = u.email
        JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
    """)
    
    clients_list = []
    
    
    if individual_clients:
        for client in individual_clients:
            
            nama_lengkap = client[3]  
            if client[4]:  
                nama_lengkap += " " + client[4]
            if client[5]:  
                nama_lengkap += " " + client[5]
                
            clients_list.append({
                'no_identitas': client[0],
                'email': client[1],
                'alamat': client[2],
                'nama': nama_lengkap.strip(),
                'jenis': client[6],
            })
    
    
    if company_clients:
        for client in company_clients:
            clients_list.append({
                'no_identitas': client[0],
                'email': client[1],
                'alamat': client[2],
                'nama': client[3],  
                'jenis': client[4],
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
    
    
    client_type = execute_query("""
        SELECT 
            CASE 
                WHEN EXISTS (SELECT 1 FROM petclinic.INDIVIDU WHERE no_identitas_klien = %s) THEN 'Individu'
                WHEN EXISTS (SELECT 1 FROM petclinic.PERUSAHAAN WHERE no_identitas_klien = %s) THEN 'Perusahaan'
                ELSE 'Unknown'
            END
    """, [no_identitas, no_identitas])
    
    if not client_type:
        messages.error(request, 'Client not found.')
        return redirect('authentication:list_client')
    
    client_jenis = client_type[0][0]
    client = {}
    
    
    if client_jenis == 'Individu':
        individual_data = execute_query("""
            SELECT k.no_identitas, k.email, u.alamat, u.nomor_telepon, k.tanggal_registrasi,
                   i.nama_depan, i.nama_tengah, i.nama_belakang
            FROM petclinic.KLIEN k
            JOIN petclinic."USER" u ON k.email = u.email
            JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            WHERE k.no_identitas = %s
        """, [no_identitas])
        
        if individual_data:
            
            nama_lengkap = individual_data[0][5]  
            if individual_data[0][6]:  
                nama_lengkap += " " + individual_data[0][6]
            if individual_data[0][7]:  
                nama_lengkap += " " + individual_data[0][7]
            
            client = {
                'no_identitas': individual_data[0][0],
                'email': individual_data[0][1],
                'alamat': individual_data[0][2],
                'nomor_telepon': individual_data[0][3],
                'tanggal_registrasi': individual_data[0][4],
                'nama': nama_lengkap.strip(),
                'jenis': client_jenis
            }
    else:  
        company_data = execute_query("""
            SELECT k.no_identitas, k.email, u.alamat, u.nomor_telepon, k.tanggal_registrasi,
                   p.nama_perusahaan
            FROM petclinic.KLIEN k
            JOIN petclinic."USER" u ON k.email = u.email
            JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE k.no_identitas = %s
        """, [no_identitas])
        
        if company_data:
            client = {
                'no_identitas': company_data[0][0],
                'email': company_data[0][1],
                'alamat': company_data[0][2],
                'nomor_telepon': company_data[0][3],
                'tanggal_registrasi': company_data[0][4],
                'nama': company_data[0][5],
                'jenis': client_jenis
            }
    
    if not client:
        messages.error(request, 'Client details could not be retrieved.')
        return redirect('authentication:list_client')
    
    
    pets_query = """
        SELECT h.nama, h.tanggal_lahir, jh.nama_jenis
        FROM petclinic.HEWAN h
        JOIN petclinic.JENIS_HEWAN jh ON h.id_jenis = jh.id
        WHERE h.no_identitas_klien = %s
    """
    
    pets_data = execute_query(pets_query, [no_identitas])
    
    pets = []
    if pets_data:
        for pet in pets_data:
            pets.append({
                'nama': pet[0],
                'tanggal_lahir': pet[1],
                'jenis': pet[2]
            })
    
    context = {
        'user_data': user_data,
        'client': client,
        'pets': pets
    }
    
    return render(request, 'client_detail.html', context)

def my_client_data(request):
    """View function for clients to view their own data and pets."""
    
    if not request.session.get('user_email') or request.session.get('user_type') not in ['individu', 'perusahaan']:
        messages.error(request, 'Only clients can access this page.')
        return redirect('authentication:dashboard')
    
    user_data = get_user_data(request)
    no_identitas = user_data['no_identitas']
    
    
    client_type = execute_query("""
        SELECT 
            CASE 
                WHEN EXISTS (SELECT 1 FROM petclinic.INDIVIDU WHERE no_identitas_klien = %s) THEN 'Individu'
                WHEN EXISTS (SELECT 1 FROM petclinic.PERUSAHAAN WHERE no_identitas_klien = %s) THEN 'Perusahaan'
                ELSE 'Unknown'
            END
    """, [no_identitas, no_identitas])
    
    if not client_type:
        messages.error(request, 'Client data not found.')
        return redirect('authentication:dashboard')
    
    client_jenis = client_type[0][0]
    client = {}
    
    
    if client_jenis == 'Individu':
        individual_data = execute_query("""
            SELECT k.no_identitas, k.email, u.alamat, u.nomor_telepon, k.tanggal_registrasi,
                   i.nama_depan, i.nama_tengah, i.nama_belakang
            FROM petclinic.KLIEN k
            JOIN petclinic."USER" u ON k.email = u.email
            JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            WHERE k.no_identitas = %s
        """, [no_identitas])
        
        if individual_data:
            
            nama_lengkap = individual_data[0][5]  
            if individual_data[0][6]:  
                nama_lengkap += " " + individual_data[0][6]
            if individual_data[0][7]:  
                nama_lengkap += " " + individual_data[0][7]
            
            client = {
                'no_identitas': individual_data[0][0],
                'email': individual_data[0][1],
                'alamat': individual_data[0][2],
                'nomor_telepon': individual_data[0][3],
                'tanggal_registrasi': individual_data[0][4],
                'nama': nama_lengkap.strip(),
                'jenis': client_jenis
            }
    else:  
        company_data = execute_query("""
            SELECT k.no_identitas, k.email, u.alamat, u.nomor_telepon, k.tanggal_registrasi,
                   p.nama_perusahaan
            FROM petclinic.KLIEN k
            JOIN petclinic."USER" u ON k.email = u.email
            JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE k.no_identitas = %s
        """, [no_identitas])
        
        if company_data:
            client = {
                'no_identitas': company_data[0][0],
                'email': company_data[0][1],
                'alamat': company_data[0][2],
                'nomor_telepon': company_data[0][3],
                'tanggal_registrasi': company_data[0][4],
                'nama': company_data[0][5],
                'jenis': client_jenis
            }
    
    if not client:
        messages.error(request, 'Client details could not be retrieved.')
        return redirect('authentication:dashboard')
    
    
    pets_query = """
        SELECT h.nama, h.tanggal_lahir, jh.nama_jenis
        FROM petclinic.HEWAN h
        JOIN petclinic.JENIS_HEWAN jh ON h.id_jenis = jh.id
        WHERE h.no_identitas_klien = %s
    """
    
    pets_data = execute_query(pets_query, [no_identitas])
    
    pets = []
    if pets_data:
        for pet in pets_data:
            pets.append({
                'nama': pet[0],
                'tanggal_lahir': pet[1],
                'jenis': pet[2]
            })
    
    context = {
        'user_data': user_data,
        'client': client,
        'pets': pets
    }
    
    return render(request, 'my_client_data.html', context)
