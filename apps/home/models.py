from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    ic_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username

class UserRole(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('officer', 'Officer'),
        ('admin', 'Admin'),
    )

    DEPARTMENT_CHOICES = (
        (None, 'NULL'),
        ('Pejabat Tanah', 'Pejabat Tanah'),
        ('JPJ', 'JPJ'),
        ('KWSP', 'KWSP'),
        ('JPN', 'JPN'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal to automatically create UserRole when a new User is created
@receiver(post_save, sender=User)
def create_or_update_user_role(sender, instance, created, **kwargs):
    if created:
        # Assign default role to new user
        UserRole.objects.create(user=instance, role='user')
    else:
        # Ensure existing users have a UserRole instance
        if not hasattr(instance, 'user_role'):
            UserRole.objects.create(user=instance, role='user')
    
class OfficerDocument(models.Model):
    title = models.CharField(max_length=255)
    issuer_email = models.EmailField()
    pdf_file = models.FileField(upload_to='officer_uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    normalized_text = models.TextField(blank=True)
    hashed_text = models.TextField(blank=True)
    client_email = models.EmailField()  # Changed from user_email to client_email
    department = models.CharField(max_length=100, default='General') # Store department name directly as a string

    def __str__(self):
        return self.title

class Document(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    title = models.CharField(max_length=200)
    issuer_email = models.EmailField(max_length=254)
    pdf_file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    normalized_text = models.TextField(blank=True)
    hashed_text = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    department = models.CharField(max_length=100)  # Store department name directly as a string

    def __str__(self):
        return self.title


class DocumentTest(models.Model):
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)