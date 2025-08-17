from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = (
        ('intern', 'Intern'),
        ('company', 'Company'),
    )
    role = models.CharField(max_length=20, choices=ROLES)
