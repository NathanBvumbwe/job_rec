# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Job,User, Recruiter, JobCleaned
from collections import defaultdict
from django.shortcuts import render, redirect
from .forms import ProfileForm, LoginForm, JobCleanedForm, RecruiterForm, ProfileUpdateForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.backends.db import SessionStore
from django.core.paginator import Paginator
from django.db.models import Q
from job_recommendation.model.recommender import recommend_category
from django.db import models


# Define categories and keywords for grouping
from django.shortcuts import render
from .models import Job
from collections import defaultdict

# Define categories and keywords for grouping
CATEGORY_KEYWORDS = {
    "Agriculture & Environment": ["agriculture", "environment", "farming", "forestry"],
    "Health & Education": ["nurse", "doctor", "health", "teacher", "education"],
    "Business & Administration": ["finance", "account", "business", "admin", "secretary"],
    "Technical & Engineering": ["mechanic", "electric", "engineer", "plumber", "technician"],
    "IT & Innovation": ["IT", "developer", "software", "data", "programmer"],
    "Services & Informal Sector": ["driver", "cleaner", "cook", "gardener", "maid"],
    "Government & NGOs": ["government", "ngo", "project", "officer", "policy"],
    "Creative & Media": ["graphic", "media", "journalist", "video", "design"],
}

def home(request):
    from job_recommendation.models import JobCleaned
    # Get all unique categories from jobs_cleaned and their job counts
    categories = JobCleaned.objects.values('category').annotate(count=models.Count('id')).order_by('-count')[:6]
    category_data = []
    for cat in categories:
        icon = get_job_icon('', cat['category'])
        category_data.append({'name': cat['category'], 'icon': icon, 'count': cat['count']})
    jobs = JobCleaned.objects.all()
    for job in jobs:
        job.icon_class = get_job_icon(job.title, getattr(job, 'category', None))
    return render(request, 'job_recommendation/index.html', {
        'jobs': jobs,
        'category_data': category_data
    })

    

def category_icon(category):
    icons = {
        "Agriculture & Environment": "fa-seedling",
        "Health & Education": "fa-stethoscope",
        "Business & Administration": "fa-briefcase",
        "Technical & Engineering": "fa-cogs",
        "IT & Innovation": "fa-laptop-code",
        "Services & Informal Sector": "fa-tools",
        "Government & NGOs": "fa-university",
        "Creative & Media": "fa-paint-brush",
    }
    return icons.get(category, "fa-briefcase")


def job_detail(request, job_id):
    job = Job.objects.get(id=job_id)
    return render(request, 'job_recommendation/job-detail.html', {'job': job})



def about(request):
    return render(request, 'job_recommendation/about.html')


def create_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Run matching for the new user so matches are available on first login
            from job_recommendation.model2_reccomender.eish import save_matches_to_db
            save_matches_to_db(user.id, top_n=6)
            messages.success(request, 'Profile created successfully! Please login.')
            return redirect('login')
    else:
        form = ProfileForm()
    return render(request, 'job_recommendation/create_profile.html', {'form': form})

def get_job_icon(job_title, job_category=None):
    """
    Determine the appropriate icon for a job based on title or category
    """
    title_lower = job_title.lower()
    
    # Technology/IT jobs
    if any(word in title_lower for word in ['developer', 'programmer', 'software', 'engineer', 'coding', 'web', 'app', 'mobile', 'frontend', 'backend', 'fullstack', 'devops', 'data', 'ai', 'machine learning']):
        return 'fa-laptop-code'
    
    # Design/Creative jobs
    elif any(word in title_lower for word in ['designer', 'design', 'creative', 'graphic', 'ui', 'ux', 'art', 'visual', 'illustrator', 'animator']):
        return 'fa-paint-brush'
    
    # Marketing/Sales jobs
    elif any(word in title_lower for word in ['marketing', 'sales', 'business', 'account', 'manager', 'executive', 'representative', 'consultant']):
        return 'fa-chart-line'
    
    # Healthcare jobs
    elif any(word in title_lower for word in ['nurse', 'doctor', 'medical', 'health', 'care', 'therapist', 'physician', 'dentist', 'pharmacist']):
        return 'fa-stethoscope'
    
    # Education jobs
    elif any(word in title_lower for word in ['teacher', 'professor', 'instructor', 'educator', 'tutor', 'lecturer', 'academic']):
        return 'fa-graduation-cap'
    
    # Finance/Accounting jobs
    elif any(word in title_lower for word in ['accountant', 'finance', 'financial', 'banking', 'auditor', 'bookkeeper', 'analyst']):
        return 'fa-calculator'
    
    # Customer Service jobs
    elif any(word in title_lower for word in ['customer', 'support', 'service', 'representative', 'assistant', 'help', 'care']):
        return 'fa-headset'
    
    # Engineering/Technical jobs
    elif any(word in title_lower for word in ['engineer', 'technical', 'technician', 'mechanic', 'electrician', 'plumber', 'construction']):
        return 'fa-cogs'
    
    # Administrative jobs
    elif any(word in title_lower for word in ['admin', 'administrative', 'secretary', 'assistant', 'coordinator', 'clerk']):
        return 'fa-briefcase'
    
    # Legal jobs
    elif any(word in title_lower for word in ['lawyer', 'attorney', 'legal', 'paralegal', 'law']):
        return 'fa-balance-scale'
    
    # Science/Research jobs
    elif any(word in title_lower for word in ['scientist', 'researcher', 'analyst', 'laboratory', 'research', 'phd']):
        return 'fa-flask'
    
    # Transportation/Logistics jobs
    elif any(word in title_lower for word in ['driver', 'delivery', 'logistics', 'transport', 'shipping', 'warehouse']):
        return 'fa-truck'
    
    # Hospitality/Tourism jobs
    elif any(word in title_lower for word in ['hotel', 'restaurant', 'chef', 'cook', 'waiter', 'tourism', 'travel']):
        return 'fa-utensils'
    
    # Media/Entertainment jobs
    elif any(word in title_lower for word in ['journalist', 'reporter', 'writer', 'editor', 'media', 'entertainment', 'actor', 'musician']):
        return 'fa-microphone'
    
    # Government/Public Service jobs
    elif any(word in title_lower for word in ['government', 'public', 'officer', 'policy', 'civil', 'service']):
        return 'fa-university'
    
    # Agriculture/Environment jobs
    elif any(word in title_lower for word in ['agriculture', 'farming', 'environment', 'conservation', 'forestry']):
        return 'fa-seedling'
    
    # Default icon for other jobs
    else:
        return 'fa-briefcase'

def job_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    from job_recommendation.models import JobCleaned
    jobs = JobCleaned.objects.all()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__icontains=query) |
            Q(description__icontains=query)
        )
    if category:
        jobs = jobs.filter(category__iexact=category)
    for job in jobs:
        job.icon_class = get_job_icon(job.title, getattr(job, 'category', None))
    paginator = Paginator(jobs, 6)  # Show 6 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'job_recommendation/job-list.html', {
        'page_obj': page_obj,
        'jobs': page_obj,
        'query': query,
        'selected_category': category,
    })

def category(request):
    from job_recommendation.models import JobCleaned
    # Get all unique categories from jobs_cleaned
    categories = JobCleaned.objects.values_list('category', flat=True).distinct()
    # For each category, get jobs in that category
    category_jobs = []
    for cat in categories:
        jobs = JobCleaned.objects.filter(category=cat)
        for job in jobs:
            job.icon_class = get_job_icon(job.title, getattr(job, 'category', None))
        category_jobs.append({
            'name': cat,
            'jobs': jobs,
            'count': jobs.count(),
            'icon': get_job_icon('', cat)
        })
    return render(request, 'job_recommendation/category.html', {
        'category_jobs': category_jobs
    })

def testimonial(request):
    return render(request, 'job_recommendation/testimonial.html')

def contact(request):
    return render(request, 'job_recommendation/contact.html')

def error_404(request):
    return render(request, 'job_recommendation/404.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    messages.success(request, 'Login successful!')
                    return redirect('profile')
                else:
                    messages.error(request, 'Invalid password!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
    else:
        form = LoginForm()
    return render(request, 'job_recommendation/login.html', {'form': form})

def profile_view(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to view your profile!')
        return redirect('login')
    
    user = User.objects.get(id=request.session['user_id'])
    from job_recommendation.models import MatchedJob, JobCleaned
    # Get matched job IDs for this user, ordered by similarity
    matched = MatchedJob.objects.filter(user_id=user.id).order_by('-similarity_score')[:6]
    job_ids = [m.job_id for m in matched]
    # Get jobs from JobCleaned with those IDs
    jobs = list(JobCleaned.objects.filter(id__in=job_ids))
    # Sort jobs to match the order of job_ids
    jobs = sorted(jobs, key=lambda job: job_ids.index(job.id))
    for job in jobs:
        job.icon_class = get_job_icon(job.title, getattr(job, 'category', None))
    category_data = [
        {'name': 'Design & Creative', 'icon': 'fa-paint-brush', 'count': 100},
        {'name': 'Marketing & Sales', 'icon': 'fa-chart-line', 'count': 150},
        {'name': 'Development', 'icon': 'fa-code', 'count': 200},
        {'name': 'Customer Support', 'icon': 'fa-headset', 'count': 80},
    ]
    return render(request, 'job_recommendation/profile.html', {
        'user': user,
        'jobs': jobs,
        'category_data': category_data
    })

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

def post_job(request):
    if request.method == 'POST':
        form = JobCleanedForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('job-list')
    else:
        form = JobCleanedForm()
    return render(request, 'job_recommendation/post_job.html', {'form': form})

def create_recruiter_profile(request):
    if request.method == 'POST':
        form = RecruiterForm(request.POST)
        if form.is_valid():
            recruiter = form.save()
            messages.success(request, 'Recruiter profile created successfully! Please login.')
            return redirect('recruiter_login')
    else:
        form = RecruiterForm()
    return render(request, 'job_recommendation/create_recruiter_profile.html', {'form': form})

def recruiter_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            recruiter = Recruiter.objects.get(email=email)
            if check_password(password, recruiter.password):
                request.session['recruiter_id'] = recruiter.id
                messages.success(request, 'Login successful!')
                return redirect('recruiter_dashboard')
            else:
                messages.error(request, 'Invalid password!')
        except Recruiter.DoesNotExist:
            messages.error(request, 'Recruiter not found!')
    return render(request, 'job_recommendation/recruiter_login.html')

def recruiter_dashboard(request):
    if 'recruiter_id' not in request.session:
        messages.error(request, 'Please login to view your dashboard!')
        return redirect('recruiter_login')
    
    recruiter = Recruiter.objects.get(id=request.session['recruiter_id'])
    # Get jobs posted by this recruiter (you can add this functionality later)
    return render(request, 'job_recommendation/recruiter_dashboard.html', {
        'recruiter': recruiter
    })

def recruiter_options(request):
    return render(request, 'job_recommendation/recruiter_options.html')

def update_profile(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to update your profile!')
        return redirect('login')
    user = User.objects.get(id=request.session['user_id'])
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Refresh job recommendations for this user
            from job_recommendation.model2_reccomender.eish import save_matches_to_db
            save_matches_to_db(user.id, top_n=6)
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, 'job_recommendation/update_profile.html', {'form': form})

def recommend_job(request):
    jobs = None
    category = None
    user_input = ''
    profile_used = False
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        # Combine relevant profile fields
        profile_fields = [
            user.name,
            user.academic_qualification,
            user.experience,
            ', '.join(user.skills) if hasattr(user, 'skills') else '',
            user.about
        ]
        user_input = ' '.join([str(f) for f in profile_fields if f])
        profile_used = True
        if user_input:
            category = recommend_category(user_input)
            jobs = JobCleaned.objects.filter(category__iexact=category)
    elif request.method == 'POST':
        user_input = request.POST.get('skills', '')
        if user_input:
            category = recommend_category(user_input)
            jobs = JobCleaned.objects.filter(category__iexact=category)
    return render(request, 'job_recommendation/recommend_job.html', {
        'jobs': jobs,
        'category': category,
        'user_input': user_input,
        'profile_used': profile_used
    })