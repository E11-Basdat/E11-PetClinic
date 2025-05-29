from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)

def dictfetchall(cursor):
    """Convert cursor fetchall() to list of dictionaries"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def client_prescription(request):
    """Fixed version of client prescription view"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    if not user_email or user_type not in ['individu', 'perusahaan']:
        messages.error(request, 'Silakan login sebagai klien untuk melihat resep obat')
        return redirect('authentication:login')
    
    try:
        with connection.cursor() as cursor:
            # Get client ID
            cursor.execute("SELECT no_identitas FROM PETCLINIC.KLIEN WHERE email = %s", [user_email])
            client_result = cursor.fetchone()
            
            if not client_result:
                messages.error(request, 'Data klien tidak ditemukan')
                return render(request, 'client_prescription.html', {
                    'prescriptions': '[]',
                    'user_email': user_email,
                    'user_type': user_type
                })
            
            client_no_identitas = client_result[0]
            
            cursor.execute("""
                SELECT DISTINCT
                    k.id_kunjungan,
                    k.nama_hewan,
                    k.timestamp_awal,
                    k.timestamp_akhir,
                    k.no_identitas_klien,
                    kk.kode_perawatan,
                    p.nama_perawatan,
                    p.biaya_perawatan,
                    -- Doctor info (simplified)
                    COALESCE(
                        CONCAT('dr. ', i_dokter.nama_depan, ' ', COALESCE(i_dokter.nama_belakang, '')),
                        CONCAT('dr. ', per_dokter.nama_perusahaan),
                        'dr. Unknown'
                    ) as nama_dokter
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                    AND k.nama_hewan = kk.nama_hewan
                    AND k.no_identitas_klien = kk.no_identitas_klien
                JOIN PETCLINIC.PERAWATAN p
                    ON kk.kode_perawatan = p.kode_perawatan
                -- Simplified doctor joins
                LEFT JOIN PETCLINIC.DOKTER_HEWAN dh ON k.no_dokter_hewan = dh.no_dokter_hewan
                LEFT JOIN PETCLINIC.TENAGA_MEDIS tm ON dh.no_dokter_hewan = tm.no_tenaga_medis
                LEFT JOIN PETCLINIC.PEGAWAI peg ON tm.no_tenaga_medis = peg.no_pegawai
                LEFT JOIN PETCLINIC.INDIVIDU i_dokter ON peg.no_pegawai = i_dokter.no_identitas_klien
                LEFT JOIN PETCLINIC.PERUSAHAAN per_dokter ON peg.no_pegawai = per_dokter.no_identitas_klien
                WHERE k.no_identitas_klien = %s 
                ORDER BY k.timestamp_awal DESC, p.nama_perawatan
            """, [client_no_identitas])
            
            treatments_data = dictfetchall(cursor)
            
            if not treatments_data:
                return render(request, 'client_prescription.html', {
                    'prescriptions': '[]',
                    'user_email': user_email,
                    'user_type': user_type
                })
            
            prescription_dict = {}
            
            for treatment in treatments_data:
                visit_key = f"{treatment['id_kunjungan']}-{treatment['nama_hewan']}"
                treatment_key = treatment['kode_perawatan']
                
                if visit_key not in prescription_dict:
                    prescription_dict[visit_key] = {
                        'visit_info': {
                            'id_kunjungan': treatment['id_kunjungan'],
                            'nama_hewan': treatment['nama_hewan'],
                            'timestamp_awal': treatment['timestamp_awal'],
                            'timestamp_akhir': treatment['timestamp_akhir'],
                            'nama_dokter': treatment['nama_dokter'],
                            'no_identitas_klien': treatment['no_identitas_klien']
                        },
                        'treatments': {}
                    }
                
                if treatment_key not in prescription_dict[visit_key]['treatments']:
                    prescription_dict[visit_key]['treatments'][treatment_key] = {
                        'treatment_info': {
                            'kode_perawatan': treatment['kode_perawatan'],
                            'nama_perawatan': treatment['nama_perawatan'],
                            'biaya_perawatan': treatment['biaya_perawatan']
                        },
                        'medicines': []
                    }
                
                cursor.execute("""
                    SELECT 
                        po.kode_obat,
                        po.kuantitas_obat,
                        o.nama as nama_obat,
                        o.harga as harga_obat,
                        o.dosis,
                        o.stok as stok_tersedia,
                        (o.harga * po.kuantitas_obat) as total_obat
                    FROM PETCLINIC.PERAWATAN_OBAT po
                    JOIN PETCLINIC.OBAT o ON po.kode_obat = o.kode
                    WHERE po.kode_perawatan = %s
                    ORDER BY o.nama
                """, [treatment_key])
                
                medicines = dictfetchall(cursor)
                prescription_dict[visit_key]['treatments'][treatment_key]['medicines'] = medicines
            
            prescription_list = []
            for visit_key, visit_data in prescription_dict.items():
                visit_total = 0
                treatments_list = []
                
                for treatment_key, treatment_data in visit_data['treatments'].items():
                    treatment_cost = treatment_data['treatment_info']['biaya_perawatan'] or 0
                    medicine_total = sum(med['total_obat'] or 0 for med in treatment_data['medicines'])
                    treatment_total = treatment_cost + medicine_total
                    
                    treatments_list.append({
                        'treatment_info': treatment_data['treatment_info'],
                        'medicines': treatment_data['medicines'],
                        'treatment_total': treatment_total,
                        'medicine_total': medicine_total,
                        'treatment_cost': treatment_cost
                    })
                    
                    visit_total += treatment_total
                
                prescription_list.append({
                    'visit_info': visit_data['visit_info'],
                    'treatments': treatments_list,
                    'visit_total': visit_total
                })
            
            prescription_list.sort(key=lambda x: x['visit_info']['timestamp_awal'], reverse=True)
            
            prescriptions_json = json.dumps(prescription_list, cls=DjangoJSONEncoder)
            
            logger.info(f"Successfully processed {len(prescription_list)} visits for client {user_email}")
            
            return render(request, 'client_prescription.html', {
                'prescriptions': prescriptions_json,
                'user_email': user_email,
                'user_type': user_type
            })
    
    except Exception as e:
        logger.error(f'Error loading prescriptions for {user_email}: {str(e)}')
        messages.error(request, f'Terjadi kesalahan saat memuat data resep obat: {str(e)}')
        return render(request, 'client_prescription.html', {
            'prescriptions': '[]',
            'user_email': user_email,
            'user_type': user_type
        })

def get_prescription_detail(request):
    """API endpoint to get detailed prescription info for a specific visit"""
    visit_id = request.GET.get('visit_id')
    user_email = request.session.get('user_email')
    
    if not all([visit_id, user_email]):
        return JsonResponse({'error': 'Parameter tidak lengkap'}, status=400)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_identitas FROM PETCLINIC.KLIEN WHERE email = %s
            """, [user_email])
            
            client_result = cursor.fetchone()
            if not client_result:
                return JsonResponse({'error': 'Data klien tidak ditemukan'}, status=404)
            
            client_no_identitas = client_result[0]
            
            cursor.execute("""
                SELECT 
                    k.id_kunjungan,
                    k.nama_hewan,
                    k.timestamp_awal,
                    k.timestamp_akhir,
                    
                    p.nama_perawatan,
                    p.kode_perawatan,
                    p.biaya_perawatan,
                    
                    o.nama as nama_obat,
                    o.kode as kode_obat,
                    o.dosis,
                    o.harga as harga_obat,
                    po.kuantitas_obat,
                    (o.harga * po.kuantitas_obat) as total_obat,
                    
                    -- Usage instructions
                    CASE 
                        WHEN o.dosis IS NOT NULL AND o.dosis != '' THEN 
                            CONCAT('Dosis: ', o.dosis)
                        ELSE 'Ikuti petunjuk dokter'
                    END as petunjuk_penggunaan,
                    
                    -- Doctor name
                    CASE 
                        WHEN i_dokter.nama_depan IS NOT NULL THEN 
                            CONCAT('dr. ', TRIM(CONCAT(
                                COALESCE(i_dokter.nama_depan, ''), ' ', 
                                COALESCE(i_dokter.nama_tengah, ''), ' ', 
                                COALESCE(i_dokter.nama_belakang, '')
                            )))
                        WHEN per_dokter.nama_perusahaan IS NOT NULL THEN 
                            CONCAT('dr. ', per_dokter.nama_perusahaan)
                        ELSE CONCAT('dr. ', SPLIT_PART(u_dokter.email, '@', 1))
                    END as nama_dokter
                    
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                JOIN PETCLINIC.PERAWATAN p 
                    ON kk.kode_perawatan = p.kode_perawatan
                JOIN PETCLINIC.PERAWATAN_OBAT po 
                    ON p.kode_perawatan = po.kode_perawatan
                JOIN PETCLINIC.OBAT o 
                    ON po.kode_obat = o.kode
                
                -- Doctor information joins
                LEFT JOIN PETCLINIC.DOKTER_HEWAN dh 
                    ON k.no_dokter_hewan = dh.no_dokter_hewan
                LEFT JOIN PETCLINIC.TENAGA_MEDIS tm_dh 
                    ON dh.no_dokter_hewan = tm_dh.no_tenaga_medis
                LEFT JOIN PETCLINIC.PEGAWAI p_dh 
                    ON tm_dh.no_tenaga_medis = p_dh.no_pegawai
                LEFT JOIN PETCLINIC."USER" u_dokter 
                    ON p_dh.email_user = u_dokter.email
                LEFT JOIN PETCLINIC.INDIVIDU i_dokter 
                    ON p_dh.no_pegawai = i_dokter.no_identitas_klien
                LEFT JOIN PETCLINIC.PERUSAHAAN per_dokter 
                    ON p_dh.no_pegawai = per_dokter.no_identitas_klien
                
                WHERE k.id_kunjungan = %s 
                  AND k.no_identitas_klien = %s
                  AND k.timestamp_akhir IS NOT NULL
                
                ORDER BY p.nama_perawatan, o.nama
            """, [visit_id, client_no_identitas])
            
            results = dictfetchall(cursor)
            
            if not results:
                return JsonResponse({'error': 'Data tidak ditemukan atau akses ditolak'}, status=404)
            
            treatments = {}
            visit_info = {
                'id_kunjungan': results[0]['id_kunjungan'],
                'nama_hewan': results[0]['nama_hewan'],
                'timestamp_awal': results[0]['timestamp_awal'],
                'timestamp_akhir': results[0]['timestamp_akhir'],
                'nama_dokter': results[0]['nama_dokter']
            }
            
            for row in results:
                treatment_code = row['kode_perawatan']
                if treatment_code not in treatments:
                    treatments[treatment_code] = {
                        'nama_perawatan': row['nama_perawatan'],
                        'biaya_perawatan': row['biaya_perawatan'],
                        'medicines': []
                    }
                
                treatments[treatment_code]['medicines'].append({
                    'nama_obat': row['nama_obat'],
                    'kode_obat': row['kode_obat'],
                    'dosis': row['dosis'],
                    'kuantitas_obat': row['kuantitas_obat'],
                    'harga_obat': row['harga_obat'],
                    'total_obat': row['total_obat'],
                    'petunjuk_penggunaan': row['petunjuk_penggunaan']
                })
            
            return JsonResponse({
                'visit_info': visit_info,
                'treatments': treatments,
                'success': True
            })
    
    except Exception as e:
        logger.error(f'Error getting prescription detail: {str(e)}')
        return JsonResponse({'error': f'Terjadi kesalahan: {str(e)}'}, status=500)

def get_prescription_summary(request):
    """API endpoint to get prescription summary statistics for client"""
    user_email = request.session.get('user_email')
    
    if not user_email:
        return JsonResponse({'error': 'User tidak terautentikasi'}, status=401)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT no_identitas FROM PETCLINIC.KLIEN WHERE email = %s
            """, [user_email])
            
            client_result = cursor.fetchone()
            if not client_result:
                return JsonResponse({'error': 'Data klien tidak ditemukan'}, status=404)
            
            client_no_identitas = client_result[0]
            
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT k.id_kunjungan) as total_kunjungan,
                    COUNT(DISTINCT kk.kode_perawatan) as total_perawatan,
                    COUNT(po.kode_obat) as total_obat_diresepkan,
                    COALESCE(SUM(p.biaya_perawatan + (o.harga * po.kuantitas_obat)), 0) as total_biaya
                    
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                JOIN PETCLINIC.PERAWATAN p 
                    ON kk.kode_perawatan = p.kode_perawatan
                JOIN PETCLINIC.PERAWATAN_OBAT po 
                    ON p.kode_perawatan = po.kode_perawatan
                JOIN PETCLINIC.OBAT o 
                    ON po.kode_obat = o.kode
                
                WHERE k.no_identitas_klien = %s 
                  AND k.timestamp_akhir IS NOT NULL
            """, [client_no_identitas])
            
            summary = dictfetchall(cursor)[0]
            
            return JsonResponse({
                'summary': summary,
                'success': True
            })
    
    except Exception as e:
        logger.error(f'Error getting prescription summary: {str(e)}')
        return JsonResponse({'error': f'Terjadi kesalahan: {str(e)}'}, status=500)