from django.shortcuts import render, redirect, get_object_or_404
from .models import Doctor, Category, Appointment, Patients
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings


def index(request):
    doctors = Doctor.objects.all()[:10]
    return render(request, 'index.html', {'doctors': doctors, })


def doctor(request, category_name):
    if category_name == 'all doctor':
        doctors = Doctor.objects.all()
    else:
        doctors = Doctor.objects.filter(category__name=category_name)
        
    return render(request, 'doctor.html', {'doctors': doctors, 'category_name': category_name})


def doctor_info(request, id):
    doctor = Doctor.objects.get(id=id)
    releted_doctor = Doctor.objects.filter(category=doctor.category)[:10]
    
    return render(request, 'doctor_info.html', {'doctor': doctor, 'releted_doctor': releted_doctor})

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')


def user_appointment(request):
    if 'login' in request.session:
        username = request.session['login']
        user = Patients.objects.get(username=username)
        appointments = Appointment.objects.filter(user=user)
        return render(request, 'user_appointment.html', {'appointments': appointments})
    else:
        messages.error(request, "Please login first!")
        return redirect('login')
    


# @login_required(login_url='login')
def book_appointment(request, doctor_id):
    # print(doctor_id)
    doctor = get_object_or_404(Doctor, id=doctor_id)
    # print(doctor)

    if 'login' in request.session:
        username = request.session['login']  
        user = Patients.objects.get(username=username)
        print(user)
        
        if request.method == 'POST':
            date = request.POST.get('date')
            time = request.POST.get('time')
            
            appointment = Appointment.objects.create(
                user = user,
                doctor = doctor,
                appointment_date = date,
                appointment_time = time,
                status='Pending'
            )
            
            send_mail(
                subject= 'Your Appointment is Confirmed',
                message=f"Dear {user.username}, \n\nYour appointment with {doctor.name} has been successfully booked on {date} at {time}",
                from_email= settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False
            )
        
            messages.success(request, "Appointment Booked!")
            return redirect('user_appointment')
            # return render(request, 'user_appointment.html', {'appointments': appointments})
    else:
        messages.error(request, "Please Login Requered!")
        return redirect('login')
        
    return render(request, 'doctor_info.html', {'doctor': doctor,})



def cancel_appointment(request, id):
    if 'login' in request.session:
        username = request.session['login']
        user = Patients.objects.get(username=username)

        appointment = get_object_or_404(Appointment, id=id, user=user)
        appointment.status = 'Cancelled'
        appointment.save()

        messages.success(request, "Appointment Cancelled Successfully!")
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, "Please login required!")
        return redirect('login')

  

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # user = authenticate(request, username=username, password=password)
        patient = Patients.objects.filter(username=username, password=password).first()
        
        if patient is not None:
            messages.success(request, "Login Successfully!")
            request.session['login'] = username
            return redirect(index)
        else:
            messages.error(request, "Username Or Password Invalid!")
            return redirect('login')
    
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        
        if Patients.objects.filter(username=username).exists():
            messages.error(request, "Username Already Exists")
            return redirect(register)
            
        if Patients.objects.filter(email=email).exists():
            messages.error(request, 'Email Allerdy Exixst!')
            return redirect(register)
        
        patient = Patients(username=username, email=email, password=password)
        patient.save()
        
        messages.success(request, 'User Created Succefully!')
        return redirect(login)
        
    return render(request, 'register.html')


def logout_user(request):
    request.session.flush()
    messages.success(request, "Logout Succefully!")
    return redirect('home')





# admin

def dash_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                auth_login(request, user)
                messages.success(request, "Login Successfully!")
                return redirect(dash_admin)
            else:
                messages.error(request, "Access denied. Admins only.")
        else:
            messages.error(request, "Invalid username or password")
        
    return render(request, 'dashboard/login.html')


def dash_logout(request):
    logout(request)
    messages.success(request, "LogOut Succefully!")
    return redirect(dash_login)


@login_required(login_url=('/dash_login'))
def dash_admin(request):
    if request.user.is_superuser:
        total_doctors = Doctor.objects.count()
        appointment_total = Appointment.objects.count()
        total_patients = User.objects.filter(is_staff=False).count()
        latest_appointments = Appointment.objects.all().order_by('-created_at')[:10]

        return render(request, 'dashboard/index.html', {'action': 'admin', 'total_doctors': total_doctors, 'appointment_total': appointment_total, 'total_patients': total_patients, 'appointments': latest_appointments})
    else:
        
        return render(request, 'dashboard/index.html')


@login_required(login_url=('/dash_login'))
@staff_member_required
def appointments(request):
    appointments = Appointment.objects.all()
    return render(request, 'dashboard/appointments.html', {'action': 'appointments', 'appointments': appointments})


@login_required(login_url=('/dash_login'))
@staff_member_required
def add_doctor(request):
    category = Category.objects.all()
    
    if request.method == "POST":
        image = request.FILES.get('image')
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        email = request.POST.get('email')
        degree = request.POST.get('degree')
        password = request.POST.get('password')
        address = request.POST.get('address')
        experience = request.POST.get('experience')
        fees = request.POST.get('fees')
        about = request.POST.get('about')

        category = Category.objects.get(id=category_id)      
        doctor = Doctor(image=image, name=name, email=email, password=password, experience=experience, fees=fees, category=category, degree=degree, about=about, address=address)
        
        doctor.save()
        messages.success(request, "Doctor Added Succefully!")
        
        return redirect('add_doctor')
    
    return render(request, 'dashboard/add_doctor.html', {'category': category, 'action': 'add_doctor'})


@login_required(login_url=('/dash_login'))
@staff_member_required
def doctor_list(request):
    doctors = Doctor.objects.all()
    return render(request, 'dashboard/doctor_list.html', {'doctors': doctors, 'action': 'doctor_list'})

