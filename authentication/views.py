from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.db import connection
import uuid
from datetime import date
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
    
    # Get role-specific data
    if user_type == 'front_desk':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.no_pegawai, p.tanggal_mulai_kerja FROM petclinic.PEGAWAI p 
                JOIN petclinic.FRONT_DESK fd ON p.no_pegawai = fd.no_front_desk
                WHERE p.email_user = %s
            """, [user_email])
            emp_data = cursor.fetchall()
            if emp_data:
                result.update({
                    'no_pegawai': emp_data[0][0],
                    'tanggal_mulai_kerja': emp_data[0][1]
                })
            
    elif user_type == 'dokter':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.no_pegawai, p.tanggal_mulai_kerja, tm.no_izin_praktek 
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
                
                # Get certificates
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT no_sertifikat_kompetensi, nama_sertifikat 
                        FROM petclinic.SERTIFIKAT_KOMPETENSI
                        WHERE no_tenaga_medis = %s
                    """, [emp_data[0][0]])
                    cert_data = cursor.fetchall()
                    if cert_data:
                        result['sertifikat'] = [
                            {'no_sertifikat_kompetensi': cert[0], 'nama_sertifikat': cert[1]} 
                            for cert in cert_data
                        ]
            
    elif user_type == 'perawat':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.no_pegawai, p.tanggal_mulai_kerja, tm.no_izin_praktik 
                FROM petclinic.PEGAWAI p 
                JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                JOIN petclinic.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
                WHERE p.email_user = %s
            """, [user_email])
            emp_data = cursor.fetchall()
            if emp_data:
                result.update({
                    'no_pegawai': emp_data[0][0],
                    'tanggal_mulai_kerja': emp_data[0][1],
                    'no_izin_praktik': emp_data[0][2]
                })
                
                # Get certificates
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT no_sertifikat_kompetensi, nama_sertifikat 
                        FROM petclinic.SERTIFIKAT_KOMPETENSI
                        WHERE no_tenaga_medis = %s
                    """, [emp_data[0][0]])
                    cert_data = cursor.fetchall()
                    if cert_data:
                        result['sertifikat'] = [
                            {'no_sertifikat_kompetensi': cert[0], 'nama_sertifikat': cert[1]} 
                            for cert in cert_data
                        ]
            
    elif user_type == 'individu':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT k.no_identitas, k.tanggal_registrasi, i.nama_depan, i.nama_tengah, i.nama_belakang
                FROM petclinic.KLIEN k 
                JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
                WHERE k.email = %s
            """, [user_email])
            client_data = cursor.fetchall()
            if client_data:
                result.update({
                    'no_identitas': client_data[0][0],
                    'tanggal_registrasi': client_data[0][1],
                    'nama_depan': client_data[0][2],
                    'nama_tengah': client_data[0][3],
                    'nama_belakang': client_data[0][4]
                })
            
    elif user_type == 'perusahaan':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT k.no_identitas, k.tanggal_registrasi, p.nama_perusahaan
                FROM petclinic.KLIEN k 
                JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                WHERE k.email = %s
            """, [user_email])
            client_data = cursor.fetchall()
            if client_data:
                result.update({
                    'no_identitas': client_data[0][0],
                    'tanggal_registrasi': client_data[0][1],
                    'nama_perusahaan': client_data[0][2]
                })
            
    return result


def show_pengguna(request):
    return render(request, 'pengguna.html')


def dashboard(request):
    """Unified dashboard for all user types"""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_type = request.session.get('user_type')
    user_data = get_user_data(request)
    
    # Add debug printing to see what data is being retrieved
    print("User data for dashboard:", user_data)
    
    if not user_data:
        # If user data not found, clear session and redirect to login
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
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT email, password FROM petclinic."USER" 
                WHERE email = %s AND password = %s
            """, [email, password])
            user = cursor.fetchall()
        
        if user:
            # Set session data
            request.session['user_email'] = user[0][0]
            
            # Get user type by checking each table - use fully qualified names
            # Check if front desk
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
                    JOIN petclinic.FRONT_DESK fd ON p.no_pegawai = fd.no_front_desk
                    WHERE p.email_user = %s
                """, [email])
                front_desk = cursor.fetchall()
                if front_desk:
                    user_id = front_desk[0]
                    request.session['user_type'] = 'front_desk'
            
            # Check if doctor
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
                    JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                    JOIN petclinic.DOKTER_HEWAN dh ON tm.no_tenaga_medis = dh.no_dokter_hewan
                    WHERE p.email_user = %s
                """, [email])
                dokter = cursor.fetchall()
                if dokter:
                    request.session['user_type'] = 'dokter'
            
            # Check if nurse
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.no_pegawai FROM petclinic.PEGAWAI p 
                    JOIN petclinic.TENAGA_MEDIS tm ON p.no_pegawai = tm.no_tenaga_medis
                    JOIN petclinic.PERAWAT_HEWAN ph ON tm.no_tenaga_medis = ph.no_perawat_hewan
                    WHERE p.email_user = %s
                """, [email])
                perawat = cursor.fetchall()
                if perawat:
                    request.session['user_type'] = 'perawat'
            
            # Check if individual client
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT k.no_identitas FROM petclinic.KLIEN k 
                    JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
                    WHERE k.email = %s
                """, [email])
                individu = cursor.fetchall()
                if individu:
                    request.session['user_type'] = 'individu'
            
            # Check if company client
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT k.no_identitas FROM petclinic.KLIEN k 
                    JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                    WHERE k.email = %s
                """, [email])
                perusahaan = cursor.fetchall()
                if perusahaan:
                    request.session['user_type'] = 'perusahaan'
            
            # Redirect to the unified dashboard
            return redirect('authentication:dashboard')
        else:
            messages.info(request, 'Username or password is incorrect!')
    return render(request, 'login.html')


def logout_user(request):
    """View function to handle user logout."""
    # Clear the session
    if 'user_email' in request.session:
        del request.session['user_email']
    if 'user_type' in request.session:
        del request.session['user_type']
    
    return redirect('authentication:pengguna')


def register_user(request):
    """View function to handle user registration."""
    form = UserCreationForm()
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        # Common user data for all user types
        email = request.POST.get('email')
        password = request.POST.get('password')
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            # Start with inserting into USER table with fully qualified name
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO petclinic."USER" (email, password, alamat, nomor_telepon)
                    VALUES (%s, %s, %s, %s)
                """, [email, password, alamat, nomor_telepon])
            
            # Process based on user type
            if user_type == 'front_desk':
                # Front desk registration
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                pegawai_id = str(uuid.uuid4())
                
                # Insert into PEGAWAI table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO petclinic.PEGAWAI (no_pegawai, tanggal_mulai_kerja, email_user)
                        VALUES (%s, %s, %s)
                    """, [pegawai_id, tanggal_mulai_kerja, email])
                
                # Insert into FRONT_DESK table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO petclinic.FRONT_DESK (no_front_desk)
                        VALUES (%s)
                    """, [pegawai_id])
                
            elif user_type in ['dokter', 'perawat']:
                # Common fields for medical staff
                tanggal_mulai_kerja = request.POST.get('tanggal_mulai_kerja')
                no_izin_praktik = request.POST.get('no_izin_praktik')
                pegawai_id = str(uuid.uuid4())
                
                # Insert into PEGAWAI table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO petclinic.PEGAWAI (no_pegawai, tanggal_mulai_kerja, email_user)
                        VALUES (%s, %s, %s)
                    """, [pegawai_id, tanggal_mulai_kerja, email])
                
                # Insert into TENAGA_MEDIS table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO petclinic.TENAGA_MEDIS (no_tenaga_medis, no_izin_praktik)
                        VALUES (%s, %s)
                    """, [pegawai_id, no_izin_praktik])
                
                # Process certificates
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                
                for i in range(len(cert_numbers)):
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat)
                            VALUES (%s, %s, %s)
                        """, [cert_numbers[i], pegawai_id, cert_names[i]])
                
                if user_type == 'dokter':
                    # Insert into DOKTER_HEWAN table
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.DOKTER_HEWAN (no_dokter_hewan)
                            VALUES (%s)
                        """, [pegawai_id])
                    
                    # Process schedules
                    days = request.POST.getlist('hari[]')
                    hours = request.POST.getlist('jam[]')
                    
                    for i in range(len(days)):
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO petclinic.JADWAL_PRAKTIK (no_dokter_hewan, hari, jam)
                                VALUES (%s, %s, %s)
                            """, [pegawai_id, days[i], hours[i]])
                            
                else:  # user_type == 'perawat'
                    # Insert into PERAWAT_HEWAN table
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.PERAWAT_HEWAN (no_perawat_hewan)
                            VALUES (%s)
                        """, [pegawai_id])
                    
            elif user_type in ['individu', 'perusahaan']:
                # Common fields for clients
                klien_id = str(uuid.uuid4())
                
                # Insert into KLIEN table
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO petclinic.KLIEN (no_identitas, tanggal_registrasi, email)
                        VALUES (%s, %s, %s)
                    """, [klien_id, date.today(), email])
                
                if user_type == 'individu':
                    # Individual client registration
                    nama_depan = request.POST.get('nama_depan')
                    nama_tengah = request.POST.get('nama_tengah')
                    nama_belakang = request.POST.get('nama_belakang')
                    
                    # Insert into INDIVIDU table
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.INDIVIDU (no_identitas_klien, nama_depan, nama_tengah, nama_belakang)
                            VALUES (%s, %s, %s, %s)
                        """, [klien_id, nama_depan, nama_tengah, nama_belakang])
                    
                else:  # user_type == 'perusahaan'
                    # Company client registration
                    nama_perusahaan = request.POST.get('nama_perusahaan')
                    
                    # Insert into PERUSAHAAN table
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.PERUSAHAAN (no_identitas_klien, nama_perusahaan)
                            VALUES (%s, %s)
                        """, [klien_id, nama_perusahaan])
            
            # After successful registration, store data in session
            request.session['user_email'] = email
            request.session['user_type'] = user_type
            
            # For employee types (front desk, doctor, nurse), store employee ID
            if user_type in ['front_desk', 'dokter', 'perawat']:
                request.session['employee_id'] = pegawai_id
            # For client types (individual, company), store client ID
            elif user_type in ['individu', 'perusahaan']:
                request.session['client_id'] = klien_id
        
            messages.success(request, 'Account created successfully!')
            
            return redirect('authentication:login') 
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
    
    context = {'form': form}
    return render(request, 'register.html', context)


def update_password(request):
    """View function to handle password updates."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to update your password.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password with fully qualified table name
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT email FROM petclinic."USER" 
                WHERE email = %s AND password = %s
            """, [request.session.get('user_email'), current_password])
            user = cursor.fetchall()
        
        if not user:
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'update_password.html', {'user_data': user_data})
        
        # Update password with fully qualified table name
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE petclinic."USER" SET password = %s
                WHERE email = %s
            """, [new_password, request.session.get('user_email')])
            
        messages.success(request, 'Password updated successfully.')
        return redirect('authentication:dashboard')
    
    return render(request, 'update_password.html', {'user_data': user_data})


def update_profile(request):
    """View function to handle profile updates."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to update your profile.')
        return redirect('authentication:login')
    
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    # Get user data from database including role-specific data
    user_data = get_user_data(request)
    
    # Get additional information based on user type
    if user_type == 'dokter':
        # Get doctor's certificates
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_sertifikat_kompetensi, nama_sertifikat 
                FROM petclinic.SERTIFIKAT_KOMPETENSI
                WHERE no_tenaga_medis = %s
            """, [user_data['no_pegawai']])
            sertifikats = cursor.fetchall()
            user_data['sertifikat'] = [
                {'no_sertifikat_kompetensi': row[0], 'nama_sertifikat': row[1]} 
                for row in sertifikats
            ]
        
        # Get doctor's schedule
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT hari, jam 
                FROM petclinic.JADWAL_PRAKTIK
                WHERE no_dokter_hewan = %s
            """, [user_data['no_pegawai']])
            jadwals = cursor.fetchall()
            user_data['jadwal'] = [
                {'hari': row[0], 'jam': row[1]} 
                for row in jadwals
            ]
    
    elif user_type == 'perawat':
        # Get nurse's certificates
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_sertifikat_kompetensi, nama_sertifikat 
                FROM petclinic.SERTIFIKAT_KOMPETENSI
                WHERE no_tenaga_medis = %s
            """, [user_data['no_pegawai']])
            sertifikats = cursor.fetchall()
            user_data['sertifikat'] = [
                {'no_sertifikat_kompetensi': row[0], 'nama_sertifikat': row[1]} 
                for row in sertifikats
            ]
    
    if request.method == 'POST':
        # Common fields for all users
        alamat = request.POST.get('alamat')
        nomor_telepon = request.POST.get('nomor_telepon')
        
        try:
            # Update common user data with fully qualified table name
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic."USER" SET alamat = %s, nomor_telepon = %s
                    WHERE email = %s
                """, [alamat, nomor_telepon, user_email])
            
            # Process role-specific updates
            if user_type == 'individu':
                # Individual client updates
                nama_depan = request.POST.get('nama_depan')
                nama_tengah = request.POST.get('nama_tengah', '')
                nama_belakang = request.POST.get('nama_belakang')
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE petclinic.INDIVIDU SET nama_depan = %s, nama_tengah = %s, nama_belakang = %s
                        WHERE no_identitas_klien = %s
                    """, [nama_depan, nama_tengah, nama_belakang, user_data['no_identitas']])
                
            elif user_type == 'perusahaan':
                # Company client updates
                nama_perusahaan = request.POST.get('nama_perusahaan')
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE petclinic.PERUSAHAAN SET nama_perusahaan = %s
                        WHERE no_identitas_klien = %s
                    """, [nama_perusahaan, user_data['no_identitas']])
                
            elif user_type in ['front_desk', 'dokter', 'perawat']:
                # Employee common updates - end date
                tanggal_akhir_kerja = request.POST.get('tanggal_akhir_kerja')
                
                if tanggal_akhir_kerja:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE petclinic.PEGAWAI SET tanggal_akhir_kerja = %s
                            WHERE no_pegawai = %s
                        """, [tanggal_akhir_kerja, user_data['no_pegawai']])
                else:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE petclinic.PEGAWAI SET tanggal_akhir_kerja = NULL
                            WHERE no_pegawai = %s
                        """, [user_data['no_pegawai']])
            
            # Process additional information for medical staff
            if user_type in ['dokter', 'perawat']:
                # Update certificates - first delete all existing ones
                with connection.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM petclinic.SERTIFIKAT_KOMPETENSI
                        WHERE no_tenaga_medis = %s
                    """, [user_data['no_pegawai']])
                
                # Then insert new values
                cert_numbers = request.POST.getlist('no_sertifikat_kompetensi[]')
                cert_names = request.POST.getlist('nama_sertifikat[]')
                
                for i in range(len(cert_numbers)):
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.SERTIFIKAT_KOMPETENSI (no_sertifikat_kompetensi, no_tenaga_medis, nama_sertifikat)
                            VALUES (%s, %s, %s)
                        """, [cert_numbers[i], user_data['no_pegawai'], cert_names[i]])
            
            # Process schedules for doctors
            if user_type == 'dokter':
                # Delete all existing schedules
                with connection.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM petclinic.JADWAL_PRAKTIK
                        WHERE no_dokter_hewan = %s
                    """, [user_data['no_pegawai']])
                
                # Insert new schedules
                days = request.POST.getlist('hari[]')
                hours = request.POST.getlist('jam[]')
                
                for i in range(len(days)):
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO petclinic.JADWAL_PRAKTIK (no_dokter_hewan, hari, jam)
                            VALUES (%s, %s, %s)
                        """, [user_data['no_pegawai'], days[i], hours[i]])
        
            messages.success(request, 'Profile updated successfully!')
            return redirect('authentication:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'update_profile.html', {'user_data': user_data})

