from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
import uuid
from authentication.views import get_user_data
from django.http import JsonResponse
from django.db import IntegrityError


# ===== JENIS HEWAN =====
def jenis_hewan_list(request):
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    user_type = user_data['user_type']
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT j.id, j.nama_jenis, 
                   (SELECT COUNT(*) FROM petclinic.HEWAN h WHERE h.id_jenis = j.id) as jumlah_hewan
            FROM petclinic.JENIS_HEWAN j
            ORDER BY j.id ASC
        """)
        jenis_hewan_list = cursor.fetchall()
    
    context = {
        'user_data': user_data,
        'jenis_hewan_list': [{
            'id': row[0], 
            'nama_jenis': row[1],
            'can_delete': row[2] == 0
        } for row in jenis_hewan_list],
        'is_front_desk': user_type == 'front_desk',
        'is_dokter': user_type == 'dokter'
    }
    return render(request, 'jenis_hewan_list.html', context)

def jenis_hewan_create(request):
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    if user_data['user_type'] != 'front_desk':
        messages.error(request, 'Anda tidak memiliki akses untuk menambah jenis hewan.')
        return redirect('animals:jenis_hewan_list')
    
    if request.method == 'POST':
        nama_jenis = request.POST.get('nama_jenis')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO petclinic.JENIS_HEWAN (id, nama_jenis) VALUES (%s, %s)",
                    [str(uuid.uuid4()), nama_jenis]
                )
            messages.success(request, 'Jenis hewan berhasil ditambahkan!')
            return redirect('animals:jenis_hewan_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'jenis_hewan_form.html', {
        'user_data': user_data,
        'action': 'Tambah'
    })

def jenis_hewan_update(request, id):
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    if user_data['user_type'] != 'front_desk':
        messages.error(request, 'Anda tidak memiliki akses untuk mengubah jenis hewan.')
        return redirect('animals:jenis_hewan_list')
    
    if request.method == 'POST':
        nama_jenis = request.POST.get('nama_jenis')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE petclinic.JENIS_HEWAN SET nama_jenis = %s WHERE id = %s",
                    [nama_jenis, id]
                )
            messages.success(request, 'Jenis hewan berhasil diperbarui!')
            return redirect('animals:jenis_hewan_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nama_jenis FROM petclinic.JENIS_HEWAN WHERE id = %s", [id])
        jenis_hewan = cursor.fetchone()
    
    if not jenis_hewan:
        messages.error(request, 'Jenis hewan tidak ditemukan!')
        return redirect('animals:jenis_hewan_list')
    
    return render(request, 'jenis_hewan_form.html', {
        'user_data': user_data,
        'jenis_hewan': {'id': jenis_hewan[0], 'nama_jenis': jenis_hewan[1]},
        'action': 'Edit'
    })

def jenis_hewan_delete(request, id):
    if request.method != 'POST':
        return redirect('animals:jenis_hewan_list')

    # hanya front-desk
    user = get_user_data(request)
    if user['user_type'] != 'front_desk':
        msg = {'error': 'Unauthorized'}
        return JsonResponse(msg, status=403) if request.GET.get('modal') else redirect('animals:jenis_hewan_list')

    # masih dipakai?
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM petclinic.HEWAN WHERE id_jenis=%s", [id])
        if cur.fetchone()[0]:
            txt = 'Tidak dapat menghapus, masih ada hewan dengan jenis ini.'
            if request.GET.get('modal'):
                return JsonResponse({'error': txt}, status=400)
            messages.error(request, txt)
            return redirect('animals:jenis_hewan_list')

        cur.execute("DELETE FROM petclinic.JENIS_HEWAN WHERE id=%s", [id])

    if request.GET.get('modal'):
        return JsonResponse({'message': 'success'})
    messages.success(request, 'Jenis hewan berhasil dihapus!')
    return redirect('animals:jenis_hewan_list')

def jenis_hewan_confirm_delete(request, id):
    if not request.session.get('user_email'):
        if request.GET.get('modal'):
            return JsonResponse({'error': 'Unauthenticated'}, status=403)
        return redirect('authentication:login')

    with connection.cursor() as cur:
        cur.execute("SELECT id, nama_jenis FROM petclinic.JENIS_HEWAN WHERE id=%s", [id])
        row = cur.fetchone()
    if not row:
        msg = {'error': 'Data tidak ditemukan'}
        return JsonResponse(msg, status=404) if request.GET.get('modal') else redirect('animals:jenis_hewan_list')

    ctx = {'jenis_hewan': {'id': row[0], 'nama_jenis': row[1]}}

    # ── kalau dipanggil via fetch modal ──
    if request.GET.get('modal'):
        return render(request, 'jenis_hewan_confirm_delete.html', ctx)

# ===== HEWAN PELIHARAAN =====
def hewan_list(request):
    # ──────────── 1. Autentikasi ────────────
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')

    # ──────────── 2. Data pengguna ────────────
    user_data  = get_user_data(request)
    user_type  = user_data['user_type']
    is_client  = user_type in ('individu', 'perusahaan')
    is_fdesk   = user_type == 'front_desk'

    # ──────────── 3. Query berbeda untuk klien & petugas ────────────
    if is_client:
        query = """
            SELECT
                h.nama,
                h.no_identitas_klien,
                h.tanggal_lahir,
                h.id_jenis,
                h.url_foto,
                j.nama_jenis,
                /* nama pemilik */
                CASE
                    WHEN i.nama_depan IS NOT NULL
                    THEN i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang
                    ELSE p.nama_perusahaan
                END               AS nama_pemilik,
                /* kunjungan aktif */
                (SELECT COUNT(*) FROM petclinic.KUNJUNGAN k
                   WHERE k.nama_hewan        = h.nama
                     AND k.no_identitas_klien = h.no_identitas_klien
                     AND k.timestamp_akhir IS NULL) AS active_visits
            FROM petclinic.HEWAN h
            JOIN petclinic.JENIS_HEWAN  j ON h.id_jenis = j.id
            JOIN petclinic.KLIEN        k ON h.no_identitas_klien = k.no_identitas
            LEFT JOIN petclinic.INDIVIDU    i ON k.no_identitas = i.no_identitas_klien
            LEFT JOIN petclinic.PERUSAHAAN  p ON k.no_identitas = p.no_identitas_klien
            WHERE h.no_identitas_klien = %s
            ORDER BY h.nama ASC;
        """
        params = [user_data['no_identitas']]
    else:
        query = """
            SELECT
                h.nama,
                h.no_identitas_klien,
                h.tanggal_lahir,
                h.id_jenis,
                h.url_foto,
                j.nama_jenis,
                /* nama pemilik */
                CASE
                    WHEN i.nama_depan IS NOT NULL
                    THEN i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang
                    ELSE p.nama_perusahaan
                END               AS nama_pemilik,
                /* kunjungan aktif */
                (SELECT COUNT(*) FROM petclinic.KUNJUNGAN k
                   WHERE k.nama_hewan        = h.nama
                     AND k.no_identitas_klien = h.no_identitas_klien
                     AND k.timestamp_akhir IS NULL) AS active_visits
            FROM petclinic.HEWAN h
            JOIN petclinic.JENIS_HEWAN  j ON h.id_jenis = j.id
            JOIN petclinic.KLIEN        k ON h.no_identitas_klien = k.no_identitas
            LEFT JOIN petclinic.INDIVIDU    i ON k.no_identitas = i.no_identitas_klien
            LEFT JOIN petclinic.PERUSAHAAN  p ON k.no_identitas = p.no_identitas_klien
            ORDER BY nama_pemilik ASC, j.nama_jenis ASC, h.nama ASC;
        """
        params = []

    # ──────────── 4. Eksekusi query ────────────
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    # ──────────── 5. Susun context list ────────────
    hewan_data = []
    for row in rows:
        hewan_data.append({
            'nama'               : row[0],
            'no_identitas_klien' : row[1],
            'tanggal_lahir'      : row[2],
            'id_jenis'           : row[3],
            'url_foto'           : row[4],
            'nama_jenis'         : row[5],
            'nama_pemilik'       : row[6],          # tersedia untuk semua cabang sekarang
            'can_delete'         : row[7] == 0,     # 0 = tidak ada kunjungan aktif
            'is_client'          : is_client,
        })

    # ──────────── 6. Render ────────────
    context = {
        'user_data'    : user_data,
        'hewan_list'   : hewan_data,
        'is_front_desk': user_type == 'front_desk',
        'is_client'    : user_type in ('individu', 'perusahaan'),
    }
    return render(request, 'hewan_list.html', context)

def hewan_create(request):
    # ---------- 1. Autentikasi ----------
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')

    user_data = get_user_data(request)
    is_client = user_data['user_type'] in ('individu', 'perusahaan')

    # ---------- 2. Jika POST, simpan data ----------
    if request.method == 'POST':
        nama           = request.POST.get('nama')
        tanggal_lahir  = request.POST.get('tanggal_lahir')
        id_jenis       = request.POST.get('id_jenis')
        url_foto       = request.POST.get('url_foto')

        # tentukan pemilik
        if is_client:
            no_identitas_klien = user_data['no_identitas']
        else:
            no_identitas_klien = request.POST.get('no_identitas_klien')

        # validasi super-singkat
        if not (nama and tanggal_lahir and id_jenis and no_identitas_klien):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('animals:hewan_create')

        try:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO petclinic.HEWAN
                        (nama, no_identitas_klien, tanggal_lahir, id_jenis, url_foto)
                    VALUES (%s, %s, %s, %s, %s)
                """, [nama, no_identitas_klien, tanggal_lahir, id_jenis, url_foto])
            messages.success(request, 'Hewan peliharaan berhasil ditambahkan!')
            return redirect('animals:hewan_list')

        except IntegrityError as e:
            messages.error(request, f'Data duplikat atau tidak valid: {e}')
            return redirect('animals:hewan_create')

        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('animals:hewan_create')

    # ---------- 3. Jika GET, tampilkan form ----------
    with connection.cursor() as cur:
        cur.execute("SELECT id, nama_jenis FROM petclinic.JENIS_HEWAN ORDER BY nama_jenis")
        jenis_rows = cur.fetchall()

    context = {
        'user_data'        : user_data,
        'is_client'        : is_client,
        'jenis_hewan_list' : [{'id': r[0], 'nama_jenis': r[1]} for r in jenis_rows],
    }

    if is_client:
        nama_pemilik = (f"{user_data['nama_depan']} "
                        f"{user_data.get('nama_tengah','')} "
                        f"{user_data['nama_belakang']}"
                        ).replace('  ', ' ')
        if user_data['user_type'] == 'perusahaan':
            nama_pemilik = user_data['nama_perusahaan']
        context['nama_pemilik'] = nama_pemilik
    else:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT k.no_identitas,
                       COALESCE(i.nama_depan || ' ' || COALESCE(i.nama_tengah||' ','')|| i.nama_belakang,
                                p.nama_perusahaan)
                FROM petclinic.KLIEN k
                LEFT JOIN petclinic.INDIVIDU   i ON k.no_identitas = i.no_identitas_klien
                LEFT JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                ORDER BY 2
            """)
            klien_rows = cur.fetchall()
        context['klien_list'] = [{'no_identitas': r[0], 'nama_pemilik': r[1]} for r in klien_rows]

    return render(request, 'hewan_create_form.html', context)


# === FUNGSI UPDATE UNTUK MODAL ===
def hewan_update(request, nama, no_identitas_klien):
    if not request.session.get('user_email'):
        if request.GET.get('modal'):
            return JsonResponse({'error': 'Unauthenticated'}, status=403)
        return redirect('authentication:login')

    user_data = get_user_data(request)
    is_client = user_data['user_type'] in ['individu', 'perusahaan']

    if request.method == 'POST':
        new_nama           = request.POST.get('nama')
        tanggal_lahir      = request.POST.get('tanggal_lahir')
        id_jenis           = request.POST.get('id_jenis')
        url_foto           = request.POST.get('url_foto')
        new_no_identitas   = request.POST.get('no_identitas_klien', no_identitas_klien)

        # Jika user adalah klien, pastikan dia tak mengubah pemilik ke milik orang lain
        if is_client and new_no_identitas != user_data['no_identitas']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE petclinic.HEWAN
                    SET nama               = %s,
                        tanggal_lahir      = %s,
                        id_jenis           = %s,
                        url_foto           = %s,
                        no_identitas_klien = %s      -- ⇐ ikut di-update
                    WHERE nama               = %s
                    AND no_identitas_klien = %s      -- pemilik lama
                    """,
                    [
                        new_nama, tanggal_lahir, id_jenis, url_foto,
                        new_no_identitas,          # value SET
                        nama, no_identitas_klien   # value WHERE
                    ]
                )

            if request.GET.get('modal'):
                return JsonResponse({'message': 'Data berhasil diperbarui'})
            messages.success(request, 'Hewan peliharaan berhasil diperbarui!')
            return redirect('animals:hewan_list')

        except Exception as e:
            if request.GET.get('modal'):
                return JsonResponse({'error': str(e)}, status=500)
            messages.error(request, f'Error: {str(e)}')
            return redirect('animals:hewan_list')


    # Get data for form
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nama_jenis FROM petclinic.JENIS_HEWAN ORDER BY nama_jenis ASC")
        jenis_hewan_list = cursor.fetchall()

        cursor.execute("""
            SELECT h.nama, h.no_identitas_klien, h.tanggal_lahir, h.id_jenis, h.url_foto, j.nama_jenis,
                   CASE 
                       WHEN i.nama_depan IS NOT NULL THEN i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang
                       ELSE p.nama_perusahaan
                   END as nama_pemilik
            FROM petclinic.HEWAN h
            JOIN petclinic.JENIS_HEWAN j ON h.id_jenis = j.id
            JOIN petclinic.KLIEN k ON h.no_identitas_klien = k.no_identitas
            LEFT JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            LEFT JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE h.nama = %s AND h.no_identitas_klien = %s
        """, [nama, no_identitas_klien])
        hewan = cursor.fetchone()

    if not hewan:
        if request.GET.get('modal'):
            return JsonResponse({'error': 'Data tidak ditemukan'}, status=404)
        messages.error(request, 'Hewan peliharaan tidak ditemukan!')
        return redirect('animals:hewan_list')

    context = {
        'hewan': {
            'nama': hewan[0],
            'no_identitas_klien': hewan[1],
            'tanggal_lahir': hewan[2],
            'id_jenis': hewan[3],
            'url_foto': hewan[4],
            'nama_jenis': hewan[5],
            'nama_pemilik': hewan[6],
        },
        'jenis_hewan_list': [{'id': row[0], 'nama_jenis': row[1]} for row in jenis_hewan_list],
        'is_client': is_client
    }

    if not is_client:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT k.no_identitas,
                    CASE
                        WHEN i.nama_depan IS NOT NULL
                        THEN i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang
                        ELSE p.nama_perusahaan
                    END AS nama_pemilik
                FROM petclinic.KLIEN k
                LEFT JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
                LEFT JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
                ORDER BY nama_pemilik ASC
            """)
            klien_rows = cursor.fetchall()
        context['klien_list'] = [{'no_identitas': r[0], 'nama_pemilik': r[1]} for r in klien_rows]
    else:
        context['nama_pemilik'] = hewan[6]  # tampilkan di input readonly

    if request.GET.get('modal'):
        return render(request, 'hewan_update_form.html', context)
    
    return render(request, 'hewan_create_form.html', context)

def hewan_delete(request, nama, no_identitas_klien):
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    if user_data['user_type'] != 'front_desk':
        messages.error(request, 'Anda tidak memiliki akses untuk menghapus hewan peliharaan.')
        return redirect('animals:hewan_list')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM petclinic.KUNJUNGAN 
                WHERE nama_hewan = %s AND no_identitas_klien = %s AND timestamp_akhir IS NULL
            """, [nama, no_identitas_klien])
            active_visits = cursor.fetchone()[0]
        
        if active_visits > 0:
            messages.error(request, 'Tidak dapat menghapus hewan peliharaan karena memiliki kunjungan aktif.')
            return redirect('animals:hewan_list')
        
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM petclinic.HEWAN WHERE nama = %s AND no_identitas_klien = %s",
                [nama, no_identitas_klien]
            )
        messages.success(request, 'Hewan peliharaan berhasil dihapus!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('animals:hewan_list')

def hewan_confirm_delete(request, nama, no_identitas_klien):
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    user_data = get_user_data(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.nama, 
                   CASE 
                       WHEN i.nama_depan IS NOT NULL THEN i.nama_depan || ' ' || COALESCE(i.nama_tengah || ' ', '') || i.nama_belakang
                       ELSE p.nama_perusahaan
                   END as nama_pemilik
            FROM petclinic.HEWAN h
            JOIN petclinic.KLIEN k ON h.no_identitas_klien = k.no_identitas
            LEFT JOIN petclinic.INDIVIDU i ON k.no_identitas = i.no_identitas_klien
            LEFT JOIN petclinic.PERUSAHAAN p ON k.no_identitas = p.no_identitas_klien
            WHERE h.nama = %s AND h.no_identitas_klien = %s
        """, [nama, no_identitas_klien])
        hewan = cursor.fetchone()
    
    if not hewan:
        messages.error(request, 'Hewan peliharaan tidak ditemukan!')
        return redirect('animals:hewan_list')
    
    return render(request, 'hewan_confirm_delete.html', {
        'user_data': user_data,
        'hewan': {'nama': hewan[0], 'nama_pemilik': hewan[1]}
    })