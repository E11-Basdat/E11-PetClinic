from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
import uuid

def medicine_list(request):
    """View function to display list of medicines."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    # Get all medicines from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama, harga, stok, dosis 
            FROM petclinic.OBAT
            ORDER BY kode
        """)
        medicines = cursor.fetchall()
    
    # Format the medicines as a list of dictionaries for easier template rendering
    medicines_list = []
    for medicine in medicines:
        medicines_list.append({
            'kode': medicine[0],
            'nama': medicine[1],
            'harga': medicine[2],
            'stok': medicine[3],
            'dosis': medicine[4],
        })
    
    return render(request, 'medicine_list.html', {'medicines': medicines_list})

def add_medicine(request):
    """View function to add a new medicine."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        # Get form data
        nama = request.POST.get('nama')
        harga = request.POST.get('harga_satuan')
        dosis = request.POST.get('dosis')
        stok = request.POST.get('stok_awal')
        
        # Validate form data
        if not nama or not harga or not dosis or not stok:
            messages.error(request, 'All fields are required')
            return render(request, 'add_medicine.html')
        
        try:
            # Convert harga and stok to integers
            harga = int(harga)
            stok = int(stok)
            
            # Get the latest medicine code
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT kode FROM petclinic.OBAT
                    ORDER BY kode DESC
                    LIMIT 1
                """)
                last_code = cursor.fetchone()
            
            # Generate a new code based on the pattern "MEDXXX"
            if last_code:
                # Extract the numeric part and increment
                num = int(last_code[0][3:]) + 1
                new_code = f"MED{num:03d}"
            else:
                # First medicine code
                new_code = "MED001"
            
            # Insert new medicine
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO petclinic.OBAT (kode, nama, harga, stok, dosis)
                    VALUES (%s, %s, %s, %s, %s)
                """, [new_code, nama, harga, stok, dosis])
            
            messages.success(request, f'Medicine {nama} added successfully with code {new_code}')
            return redirect('medications:list')
        
        except ValueError:
            messages.error(request, 'Price and stock must be numbers')
        except Exception as e:
            messages.error(request, f'Error adding medicine: {str(e)}')
    
    return render(request, 'add_medicine.html')

def update_medicine(request, code):
    """View function to update an existing medicine."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    # Get medicine data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama, harga, stok, dosis 
            FROM petclinic.OBAT
            WHERE kode = %s
        """, [code])
        medicine = cursor.fetchone()
    
    if not medicine:
        messages.error(request, f'Medicine with code {code} not found')
        return redirect('medications:list')
    
    # Format medicine data
    medicine_data = {
        'kode': medicine[0],
        'nama': medicine[1],
        'harga': medicine[2],
        'stok': medicine[3],
        'dosis': medicine[4],
    }
    
    if request.method == 'POST':
        # Get form data
        nama = request.POST.get('nama')
        harga = request.POST.get('harga_satuan')
        dosis = request.POST.get('dosis')
        
        # Validate form data
        if not nama or not harga or not dosis:
            messages.error(request, 'All fields are required')
            return render(request, 'update_medicine.html', {'medicine': medicine_data})
        
        try:
            # Convert harga to integer
            harga = int(harga)
            
            # Update medicine
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.OBAT
                    SET nama = %s, harga = %s, dosis = %s
                    WHERE kode = %s
                """, [nama, harga, dosis, code])
            
            messages.success(request, f'Medicine {nama} updated successfully')
            return redirect('medications:list')
        
        except ValueError:
            messages.error(request, 'Price must be a number')
        except Exception as e:
            messages.error(request, f'Error updating medicine: {str(e)}')
    
    return render(request, 'update_medicine.html', {'medicine': medicine_data})

def update_stock(request, code):
    """View function to update medicine stock."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    # Get medicine data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama, stok 
            FROM petclinic.OBAT
            WHERE kode = %s
        """, [code])
        medicine = cursor.fetchone()
    
    if not medicine:
        messages.error(request, f'Medicine with code {code} not found')
        return redirect('medications:list')
    
    # Format medicine data
    medicine_data = {
        'kode': medicine[0],
        'nama': medicine[1],
        'stok': medicine[2]
    }
    
    if request.method == 'POST':
        # Get form data
        stok = request.POST.get('stok')
        
        # Validate form data
        if not stok:
            messages.error(request, 'Stock field is required')
            return render(request, 'update_stock.html', {'medicine': medicine_data})
        
        try:
            # Convert stok to integer
            stok = int(stok)
            
            # Update medicine stock
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.OBAT
                    SET stok = %s
                    WHERE kode = %s
                """, [stok, code])
            
            messages.success(request, f'Stock for {medicine_data["nama"]} updated successfully')
            return redirect('medications:list')
        
        except ValueError:
            messages.error(request, 'Stock must be a number')
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
    
    return render(request, 'update_stock.html', {'medicine': medicine_data})

def delete_medicine(request, code):
    """View function to delete a medicine."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    # Get medicine data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode, nama 
            FROM petclinic.OBAT
            WHERE kode = %s
        """, [code])
        medicine = cursor.fetchone()
    
    if not medicine:
        messages.error(request, f'Medicine with code {code} not found')
        return redirect('medications:list')
    
    # Format medicine data
    medicine_data = {
        'kode': medicine[0],
        'nama': medicine[1]
    }
    
    if request.method == 'POST':
        try:
            # Delete medicine
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM petclinic.OBAT
                    WHERE kode = %s
                """, [code])
            
            messages.success(request, f'Medicine {medicine_data["nama"]} deleted successfully.')
            
            # Redirect to the medicine list page
            return redirect('medications:list')
            
        except Exception as e:
            messages.error(request, f'Error deleting medicine: {str(e)}')
            return render(request, 'delete_medicine.html', {'medicine': medicine_data})
    
    return render(request, 'delete_medicine.html', {'medicine': medicine_data})

def get_user_data(request):
    """Helper function to get user data based on session"""
    user_email = request.session.get('user_email')
    user_type = request.session.get('user_type')
    
    print(f"Checking session: user_email={user_email}, user_type={user_type}")
    
    if not user_email or not user_type:
        print("Session data missing, returning None")
        return None
    
    # Get basic user data with fully qualified table name
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT email, alamat, nomor_telepon FROM petclinic."USER" 
                WHERE email = %s
            """, [user_email])
            user_data = cursor.fetchall()
        
        print(f"User query result: {user_data}")
        
        if not user_data:
            print("No user found with this email")
            return None
        
        # Return the user data
        return {
            'email': user_data[0][0],
            'alamat': user_data[0][1],
            'nomor_telepon': user_data[0][2],
            'user_type': user_type
        }
    except Exception as e:
        print(f"Error in get_user_data: {str(e)}")
        return None
    
def treatment_list(request):
    """View function to display list of treatments."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        messages.error(request, 'Please log in to access this page.')
        return redirect('authentication:login')
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('authentication:dashboard')
    
    # Get all treatments from database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kode_perawatan, nama_perawatan, biaya_perawatan 
            FROM petclinic.JENIS_PERAWATAN
            ORDER BY kode_perawatan
        """)
        treatments = cursor.fetchall()
    
    # Format the treatments as a list of dictionaries for easier template rendering
    treatments_list = []
    for treatment in treatments:
        treatments_list.append({
            'kode': treatment[0],
            'nama': treatment[1],
            'biaya': treatment[2],
        })
    
    return render(request, 'treatment_list.html', {'treatments': treatments_list})

def add_treatment(request):
    """AJAX function to add a new treatment."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        return JsonResponse({'status': 'error', 'message': 'Please log in to access this feature.'})
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        return JsonResponse({'status': 'error', 'message': 'You do not have permission to access this feature.'})
    
    if request.method == 'POST':
        # Get form data
        nama = request.POST.get('nama')
        biaya = request.POST.get('biaya')
        
        # Validate form data
        if not nama or not biaya:
            return JsonResponse({'status': 'error', 'message': 'All fields are required'})
        
        try:
            # Convert biaya to integer
            biaya = int(biaya)
            
            # Get the latest treatment code
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT kode_perawatan FROM petclinic.JENIS_PERAWATAN
                    ORDER BY kode_perawatan DESC
                    LIMIT 1
                """)
                last_code = cursor.fetchone()
            
            # Generate a new code based on the pattern "TRMXXX"
            if last_code:
                # Extract the numeric part and increment
                num = int(last_code[0][3:]) + 1
                new_code = f"TRM{num:03d}"
            else:
                # First treatment code
                new_code = "TRM001"
            
            # Insert new treatment
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO petclinic.JENIS_PERAWATAN (kode_perawatan, nama_perawatan, biaya_perawatan)
                    VALUES (%s, %s, %s)
                """, [new_code, nama, biaya])
            
            # Return success response with the new treatment data
            return JsonResponse({
                'status': 'success', 
                'message': f'Treatment {nama} added successfully with code {new_code}',
                'treatment': {
                    'kode': new_code,
                    'nama': nama,
                    'biaya': biaya
                }
            })
        
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Cost must be a number'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error adding treatment: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def update_treatment(request):
    """AJAX function to update an existing treatment."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        return JsonResponse({'status': 'error', 'message': 'Please log in to access this feature.'})
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        return JsonResponse({'status': 'error', 'message': 'You do not have permission to access this feature.'})
    
    if request.method == 'POST':
        # Get form data
        code = request.POST.get('kode')
        nama = request.POST.get('nama')
        biaya = request.POST.get('biaya')
        
        # Validate form data
        if not code or not nama or not biaya:
            return JsonResponse({'status': 'error', 'message': 'All fields are required'})
        
        try:
            # Convert biaya to integer
            biaya = int(biaya)
            
            # Update treatment
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE petclinic.JENIS_PERAWATAN
                    SET nama_perawatan = %s, biaya_perawatan = %s
                    WHERE kode_perawatan = %s
                """, [nama, biaya, code])
            
            # Return success response
            return JsonResponse({
                'status': 'success', 
                'message': f'Treatment {nama} updated successfully',
                'treatment': {
                    'kode': code,
                    'nama': nama,
                    'biaya': biaya
                }
            })
        
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Cost must be a number'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error updating treatment: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def delete_treatment(request):
    """AJAX function to delete a treatment."""
    # Check if user is logged in
    if not request.session.get('user_email'):
        return JsonResponse({'status': 'error', 'message': 'Please log in to access this feature.'})
    
    # Check if user is a medical staff (dokter or perawat)
    user_type = request.session.get('user_type')
    if user_type not in ['dokter', 'perawat']:
        return JsonResponse({'status': 'error', 'message': 'You do not have permission to access this feature.'})
    
    if request.method == 'POST':
        # Get form data
        code = request.POST.get('kode')
        
        # Validate form data
        if not code:
            return JsonResponse({'status': 'error', 'message': 'Treatment code is required'})
        
        try:
            # Get treatment name before deletion for the success message
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT nama_perawatan FROM petclinic.JENIS_PERAWATAN
                    WHERE kode_perawatan = %s
                """, [code])
                treatment = cursor.fetchone()
            
            if not treatment:
                return JsonResponse({'status': 'error', 'message': f'Treatment with code {code} not found'})
            
            treatment_name = treatment[0]
            
            # Delete treatment
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM petclinic.JENIS_PERAWATAN
                    WHERE kode_perawatan = %s
                """, [code])
            
            # Return success response
            return JsonResponse({
                'status': 'success', 
                'message': f'Treatment {treatment_name} deleted successfully',
                'code': code
            })
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error deleting treatment: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})