from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json

def dictfetchall(cursor):
    """Convert cursor fetchall() to list of dictionaries"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def client_prescription(request):
    """View for clients to see their own prescriptions based on treatments from their visits"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    if not user_email or user_type not in ['individu', 'perusahaan']:
        messages.error(request, 'Silakan login sebagai klien untuk melihat resep obat')
        return redirect('authentication:login')
        
    try:
        with connection.cursor() as cursor:
            # Get client's prescriptions - hanya dari perawatan yang benar-benar dilakukan saat kunjungan
            cursor.execute("""
                SELECT 
                    k.id_kunjungan,
                    k.nama_hewan,
                    k.timestamp_awal,
                    k.timestamp_akhir,
                    
                    -- Treatment information dari kunjungan keperawatan
                    p.kode_perawatan,
                    p.nama_perawatan,
                    p.biaya_perawatan,
                    
                    -- Medicine information dari perawatan yang dipilih
                    o.kode as kode_obat,
                    o.nama as nama_obat,
                    o.harga as harga_obat,
                    o.stok as stok_obat,
                    o.dosis,
                    po.kuantitas_obat,
                    
                    -- Calculate total cost per medicine
                    (o.harga * po.kuantitas_obat) as total_obat,
                    
                    -- Doctor information
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
                    END as nama_dokter,
                    
                    -- Visit status untuk memastikan kunjungan sudah selesai
                    CASE 
                        WHEN k.timestamp_akhir IS NOT NULL THEN 'selesai'
                        ELSE 'berlangsung'
                    END as status_kunjungan
                    
                FROM PETCLINIC.KUNJUNGAN k
                
                -- Join dengan klien untuk filter berdasarkan email
                JOIN PETCLINIC.KLIEN kl ON k.no_identitas_klien = kl.no_identitas
                
                -- Join dengan kunjungan keperawatan (perawatan yang dipilih klien)
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk 
                    ON k.id_kunjungan = kk.id_kunjungan
                    AND k.nama_hewan = kk.nama_hewan
                    AND k.no_identitas_klien = kk.no_identitas_klien
                
                -- Join dengan perawatan untuk mendapatkan detail perawatan
                JOIN PETCLINIC.PERAWATAN p
                    ON kk.kode_perawatan = p.kode_perawatan
                
                -- Join dengan perawatan_obat untuk mendapatkan obat yang terkait dengan perawatan tersebut
                JOIN PETCLINIC.PERAWATAN_OBAT po
                    ON p.kode_perawatan = po.kode_perawatan
                
                -- Join dengan obat untuk mendapatkan detail obat
                JOIN PETCLINIC.OBAT o
                    ON po.kode_obat = o.kode
                
                -- Joins untuk informasi dokter
                LEFT JOIN PETCLINIC.DOKTER_HEWAN dh ON k.no_dokter_hewan = dh.no_dokter_hewan
                LEFT JOIN PETCLINIC.TENAGA_MEDIS tm_dh ON dh.no_dokter_hewan = tm_dh.no_tenaga_medis
                LEFT JOIN PETCLINIC.PEGAWAI p_dh ON tm_dh.no_tenaga_medis = p_dh.no_pegawai
                LEFT JOIN PETCLINIC."USER" u_dokter ON p_dh.email_user = u_dokter.email
                LEFT JOIN PETCLINIC.INDIVIDU i_dokter ON p_dh.no_pegawai = i_dokter.no_identitas_klien
                LEFT JOIN PETCLINIC.PERUSAHAAN per_dokter ON p_dh.no_pegawai = per_dokter.no_identitas_klien
                
                -- Filter: hanya klien yang login dan kunjungan yang sudah selesai
                WHERE kl.email = %s 
                  AND k.timestamp_akhir IS NOT NULL  -- hanya kunjungan yang sudah selesai
                  AND o.stok >= po.kuantitas_obat    -- pastikan stok obat mencukupi
                
                ORDER BY k.timestamp_awal DESC, p.nama_perawatan, o.nama
            """, [user_email])
            
            prescriptions = dictfetchall(cursor)
            
            # Group prescriptions by visit and treatment
            grouped_prescriptions = {}
            for prescription in prescriptions:
                visit_key = f"{prescription['id_kunjungan']}-{prescription['nama_hewan']}"
                treatment_key = prescription['kode_perawatan']
                
                if visit_key not in grouped_prescriptions:
                    grouped_prescriptions[visit_key] = {
                        'visit_info': {
                            'id_kunjungan': prescription['id_kunjungan'],
                            'nama_hewan': prescription['nama_hewan'],
                            'timestamp_awal': prescription['timestamp_awal'],
                            'timestamp_akhir': prescription['timestamp_akhir'],
                            'nama_dokter': prescription['nama_dokter'],
                            'status_kunjungan': prescription['status_kunjungan']
                        },
                        'treatments': {}
                    }
                
                if treatment_key not in grouped_prescriptions[visit_key]['treatments']:
                    grouped_prescriptions[visit_key]['treatments'][treatment_key] = {
                        'treatment_info': {
                            'kode_perawatan': prescription['kode_perawatan'],
                            'nama_perawatan': prescription['nama_perawatan'],
                            'biaya_perawatan': prescription['biaya_perawatan']
                        },
                        'medicines': []
                    }
                
                # Add medicine to treatment
                grouped_prescriptions[visit_key]['treatments'][treatment_key]['medicines'].append({
                    'kode_obat': prescription['kode_obat'],
                    'nama_obat': prescription['nama_obat'],
                    'harga_obat': prescription['harga_obat'],
                    'kuantitas_obat': prescription['kuantitas_obat'],
                    'dosis': prescription['dosis'],
                    'total_obat': prescription['total_obat'],
                    'stok_tersedia': prescription['stok_obat']
                })
            
            # Convert to list for template dengan perhitungan total yang benar
            prescription_list = []
            for visit_key, visit_data in grouped_prescriptions.items():
                visit_total = 0
                treatments_list = []
                
                for treatment_key, treatment_data in visit_data['treatments'].items():
                    # Hitung total biaya treatment (biaya perawatan + biaya obat)
                    treatment_cost = treatment_data['treatment_info']['biaya_perawatan']
                    medicine_total = sum(med['total_obat'] for med in treatment_data['medicines'])
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
            
            # Sort by most recent visits first
            prescription_list.sort(key=lambda x: x['visit_info']['timestamp_awal'], reverse=True)
            
            # Convert to JSON for template
            prescriptions_json = json.dumps(prescription_list, cls=DjangoJSONEncoder)
            
            return render(request, 'client_prescription.html', {
                'prescriptions': prescriptions_json,
                'user_email': user_email,
                'user_type': user_type
            })

    except Exception as e:
        messages.error(request, f'Error loading prescriptions: {str(e)}')
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
            # Verify user owns this visit dan dapatkan detail lengkap
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
                    
                    -- Petunjuk penggunaan obat (bisa ditambahkan field ini di database)
                    CASE 
                        WHEN o.dosis IS NOT NULL THEN 
                            CONCAT('Dosis: ', o.dosis, ' per hari')
                        ELSE 'Ikuti petunjuk dokter'
                    END as petunjuk_penggunaan
                    
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.KLIEN kl ON k.no_identitas_klien = kl.no_identitas
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk ON k.id_kunjungan = kk.id_kunjungan
                JOIN PETCLINIC.PERAWATAN p ON kk.kode_perawatan = p.kode_perawatan
                JOIN PETCLINIC.PERAWATAN_OBAT po ON p.kode_perawatan = po.kode_perawatan
                JOIN PETCLINIC.OBAT o ON po.kode_obat = o.kode
                
                WHERE k.id_kunjungan = %s 
                  AND kl.email = %s
                  AND k.timestamp_akhir IS NOT NULL
                
                ORDER BY p.nama_perawatan, o.nama
            """, [visit_id, user_email])
            
            results = dictfetchall(cursor)
            
            if not results:
                return JsonResponse({'error': 'Data tidak ditemukan atau akses ditolak'}, status=404)
            
            # Group by treatment
            treatments = {}
            visit_info = {
                'id_kunjungan': results[0]['id_kunjungan'],
                'nama_hewan': results[0]['nama_hewan'],
                'timestamp_awal': results[0]['timestamp_awal'],
                'timestamp_akhir': results[0]['timestamp_akhir']
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
        return JsonResponse({'error': f'Terjadi kesalahan: {str(e)}'}, status=500)

def get_prescription_summary(request):
    """API endpoint to get prescription summary statistics for client"""
    user_email = request.session.get('user_email')
    
    if not user_email:
        return JsonResponse({'error': 'User tidak terautentikasi'}, status=401)
    
    try:
        with connection.cursor() as cursor:
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT k.id_kunjungan) as total_kunjungan,
                    COUNT(DISTINCT kk.kode_perawatan) as total_perawatan,
                    COUNT(po.kode_obat) as total_obat_diresepkan,
                    COALESCE(SUM(p.biaya_perawatan + (o.harga * po.kuantitas_obat)), 0) as total_biaya
                    
                FROM PETCLINIC.KUNJUNGAN k
                JOIN PETCLINIC.KLIEN kl ON k.no_identitas_klien = kl.no_identitas
                JOIN PETCLINIC.KUNJUNGAN_KEPERAWATAN kk ON k.id_kunjungan = kk.id_kunjungan
                JOIN PETCLINIC.PERAWATAN p ON kk.kode_perawatan = p.kode_perawatan
                JOIN PETCLINIC.PERAWATAN_OBAT po ON p.kode_perawatan = po.kode_perawatan
                JOIN PETCLINIC.OBAT o ON po.kode_obat = o.kode
                
                WHERE kl.email = %s 
                  AND k.timestamp_akhir IS NOT NULL
            """, [user_email])
            
            summary = dictfetchall(cursor)[0]
            
            return JsonResponse({
                'summary': summary,
                'success': True
            })
    
    except Exception as e:
        return JsonResponse({'error': f'Terjadi kesalahan: {str(e)}'}, status=500)