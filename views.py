from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from .models import User
from .models import Complaint  # Import the Complaint model
from .models import Contact
import uuid

# Home view
def welcome(request):
    return render(request, 'frontend/welcome.html')

# Sign-in view
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User

def signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if the user exists with the provided credentials
        user = User.objects.filter(email=email, password=password).first()

        if user:
            # Store user info in session
            request.session['user_id'] = user.id
            # Redirect to NGO interface on successful sign-in
            return redirect('ngo_interface')
        else:
            messages.error(request, "Invalid email or password")

    return render(request, 'frontend/signin.html')


# Create account view
def create_account(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Account already exists")
        else:
            # Create new user
            User.objects.create(email=email, password=password)
            messages.success(request, "Account created successfully")
            return redirect('signin')

    return render(request, 'frontend/create_account.html')

# NGO Interface view (protected by sign-in)
def ngo_interface(request):
    if not request.session.get('user_id'):
        return redirect('signin')  # Redirect to sign-in if not authenticated
    return render(request, 'frontend/ngo_interface.html')
# User Interface view for the public

def user_interface(request):
    return render(request, 'frontend/user_interface.html')

def user_interface1(request):
    data = None
    query = None

    if request.method == 'GET':
        lake_name = request.GET.get('lake_name', '').strip()
        query = lake_name

        # Find the matching lake from the main dataset
        lake_info = lake_data[lake_data['Lake_Name'].str.contains(lake_name, case=False, na=False)]

        if not lake_info.empty:
            # Extract the relevant data from the first match
            lake_row = lake_info.iloc[0]
            data = {
                'lake_name': lake_row['Lake_Name'],
                'pollution_status': 'Polluted',  # Example static data
                'pollution_level': 'High',  # Example static data
                'cause_of_pollution': 'Industrial Waste',  # Example static data
                'effects_of_pollution': 'Harmful to Aquatic Life'  # Example static data
            }
    return render(request, 'frontend/user_interface.html', {'data': data, 'query': query})

def map_data(request):
    # Fetch all lakes from the database
    lakes = Lake.objects.all()
    # Prepare data to be returned as JSON
    lake_data = [
        {
            'name': lake.name,
            'latitude': lake.latitude,
            'longitude': lake.longitude,
            'pollution_level': lake.pollution_level,
            'cause_of_pollution': lake.cause_of_pollution,
            'effects_of_pollution': lake.effects_of_pollution,
        } for lake in lakes
    ]
    return JsonResponse(lake_data, safe=False)

# Forgot password view
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            reset_token = str(uuid.uuid4())
            user.reset_token = reset_token
            user.save()

            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{reset_token}/"
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Reset link sent to your email.')
            return redirect('signin')
        except User.DoesNotExist:
            messages.error(request, 'Email not found.')
            return redirect('signin')

# Reset password view
def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)
        if request.method == 'POST':
            new_password = request.POST.get('password')
            user.password = new_password
            user.reset_token = None  # Clear the token after use
            user.save()
            messages.success(request, 'Password reset successfully.')
            return redirect('signin')
        return render(request, 'frontend/reset_password.html', {'token': token})
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired token.')
        return redirect('signin')

# Logout view (for both Logout and Home buttons)
def user_logout(request):
    request.session.flush()  # Clear the session
    return redirect('welcome')  # Redirect to the welcome page after logout

# frontend/views.py
# frontend/views.py

# frontend/views.py
import os
import pandas as pd
import pickle
from django.shortcuts import render
from django.http import JsonResponse

# Load your ML models
def load_model(model_path):
    with open(model_path, 'rb') as file:
        return pickle.load(file)

# Paths to your models
CAUSE_OF_POLLUTION_MODEL_PATH = 'frontend/models/nammajal_cause_of_pollution_model.pkl'
EFFECTS_MODEL_PATH = 'frontend/models/nammajal_effects_model.pkl'
POLLUTION_LEVEL_MODEL_PATH = 'frontend/models/Pollution_Level_model.pkl'
POLLUTION_PREDICTION_MODEL_PATH = 'frontend/models/Pollution_Prediction_model.pkl'

cause_of_pollution_model = load_model(CAUSE_OF_POLLUTION_MODEL_PATH)
effects_model = load_model(EFFECTS_MODEL_PATH)
pollution_level_model = load_model(POLLUTION_LEVEL_MODEL_PATH)
pollution_prediction_model = load_model(POLLUTION_PREDICTION_MODEL_PATH)

# Build the path to the CSV file
csv_file_path = os.path.join(os.path.dirname(__file__), 'synthetic_waterquality_data_final.csv')

# Load the main dataset
lake_data = pd.read_csv(csv_file_path)

from django.shortcuts import render

def insights_view(request):
    data = None
    query = None

    if request.method == 'GET':
        lake_name = request.GET.get('lake_name', '').strip()
        query = lake_name

        # Find the matching lake from the main dataset
        lake_info = lake_data[lake_data['Lake_Name'].str.contains(lake_name, case=False, na=False)]

        if not lake_info.empty:
            # Extract the relevant data from the first match
            lake_row = lake_info.iloc[0]
            data = {
                'lake_name': lake_row['Lake_Name'],
                'pollution_status': 'Polluted',  # Example static data
                'pollution_level': 'High',  # Example static data
                'cause_of_pollution': 'Industrial Waste',  # Example static data
                'effects_of_pollution': 'Harmful to Aquatic Life'  # Example static data
            }

    return render(request, 'frontend/ngo_interface.html', {'data': data, 'query': query})

def submit_complaint(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        place = request.POST.get('place')
        issue = request.POST.get('issue')
        description = request.POST.get('description')
        
        # Check if all required fields are provided
        if name and place and issue and description:
            # Create a new Complaint object and save it to the database
            Complaint.objects.create(name=name, place=place, issue=issue, description=description)
            
            messages.success(request, 'Your complaint has been submitted successfully!')
        else:
            messages.error(request, 'Please fill out all fields before submitting.')
        
        return redirect('user_interface')  # Redirect to the user interface after submission
    else:
        return render(request, 'complaint.html')  # Render the complaint form if not a POST request
    
def submit_contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        location = request.POST['location']
        comments = request.POST['comments']
        rating = request.POST.get('rating')  # Use .get() to avoid KeyError if no rating is selected

        # Save to database
        contact = Contact(name=name, location=location, comments=comments, rating=rating)
        contact.save()

        # Add a success message
        messages.success(request, 'Your feedback has been submitted successfully!')

        # Redirect to the user interface page
        return redirect('user_interface')

    return render(request, 'contact.html')