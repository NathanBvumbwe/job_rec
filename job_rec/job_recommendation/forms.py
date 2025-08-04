from django import forms
from .models import User, JobCleaned, Recruiter
from django.contrib.auth.hashers import make_password

class ProfileForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'})
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your address'})
    )
    academic_qualification = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your academic qualification'})
    )
    experience = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your experience'})
    )
    skills = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your skills (comma-separated)'})
    )
    about = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    def clean_skills(self):
        skills = self.cleaned_data['skills']
        return [skill.strip() for skill in skills.split(',') if skill.strip()]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        user = User(
            email=cleaned_data['email'],
            name=cleaned_data['name'],
            address=cleaned_data['address'],
            academic_qualification=cleaned_data['academic_qualification'],
            experience=cleaned_data['experience'],
            skills=cleaned_data['skills'],
            about=cleaned_data['about'],
            password=make_password(cleaned_data['password'])
        )
        user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))

class JobCleanedForm(forms.ModelForm):
    url = forms.URLField(required=False)
    class Meta:
        model = JobCleaned
        fields = ['title', 'company', 'location', 'job_type', 'date_posted', 'url', 'source', 'description', 'category']

class RecruiterForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    company_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name'
        })
    )
    industry = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Technology, Healthcare, Finance'
        })
    )
    position = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., HR Manager, Recruiter, Talent Acquisition'
        })
    )
    contact_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    address = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address'
        })
    )
    hiring_needs = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe your current hiring needs and requirements'
        })
    )
    about_company = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about your company'
        })
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company website (optional)'
        })
    )
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'LinkedIn profile (optional)'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        recruiter = Recruiter(
            email=cleaned_data['email'],
            name=cleaned_data['name'],
            company_name=cleaned_data['company_name'],
            industry=cleaned_data['industry'],
            position=cleaned_data['position'],
            contact_phone=cleaned_data['contact_phone'],
            address=cleaned_data['address'],
            hiring_needs=cleaned_data['hiring_needs'],
            about_company=cleaned_data['about_company'],
            website=cleaned_data.get('website'),
            linkedin=cleaned_data.get('linkedin'),
            password=make_password(cleaned_data['password'])
        )
        recruiter.save()
        return recruiter

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'address', 'academic_qualification', 'experience', 'skills', 'about']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your address'}),
            'academic_qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your academic qualification'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your experience'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your skills (comma separated)'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself'}),
        }