from django.contrib import admin
from django.urls import path
from . import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('create-profile/', views.create_profile, name='create_profile'),
    path('create-recruiter-profile/', views.create_recruiter_profile, name='create_recruiter_profile'),
    path('login/', views.login_view, name='login'),
    path('recruiter-login/', views.recruiter_login, name='recruiter_login'),
    path('recruiter-dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('job-list/', views.job_list, name='job-list'),
    path('job-detail/<int:job_id>/', views.job_detail, name='job-detail'),
    path('category/', views.category, name='category'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('contact/', views.contact, name='contact'),
    path('404/', views.error_404, name='404'),
    path('post-job/', views.post_job, name='post_job'),
    path('recruiter/', views.recruiter_options, name='recruiter_options'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('recommend-job/', views.recommend_job, name='recommend_job'),
]
