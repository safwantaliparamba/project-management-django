import os
import uuid
from PIL import Image
from io import BytesIO

from django.db import models
from django.core.files import File
from django.http.request import HttpRequest
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group

from general.models import BaseModel
from general.encryptions import encrypt
from general.middlewares import RequestMiddleware
from general.functions import random_password, get_auto_id, generate_unique_id, resize



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError(_('The Email field must be set.'))
        email = self.normalize_email(email)
        user: User = self.model(email=email, **extra_fields)
        encrypted_password = encrypt(password)

        user.set_password(password)
        user.encrypted_password = encrypted_password
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        encrypted_password = encrypt(password)

        return self.create_user(email, password,encrypted_password=encrypted_password, **extra_fields)
    

USER_PRONOUNS = [
    ("he/him",          "He/Him"),
    ("she/her",         "She/Her"),
    ("other",           "Other")
]

PROFILE_TYPE = [
    ("project_manager",     "Project Manager"),
    ("ui_ux_designer",      "Ui Ux Designer"),
    ("graphic_designer",    "Graphic Designer"),
    ("frontend_developer",  "Frontend Developer"),
    ("backend_developer",   "Backend Developer"),
    ("quality_analyst",     "Quality Analyst"),
]


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # mandatory fields
    email = models.EmailField(unique=True)
    encrypted_password = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=128,null=True,blank=True)
    
    profile_type = models.CharField(max_length=255,choices=PROFILE_TYPE, default='project_manager')
   
    # optional fields
    age = models.CharField(max_length=2,null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=999,null=True, blank=True)
    employee_id = models.CharField(max_length=999,null=True, blank=True)
    id_proof = models.FileField(upload_to="accounts/id-proof",null=True,blank=True)
    is_deleted = models.BooleanField(default=False)
    gender = models.CharField(max_length=255, null=True, blank=True,choices=USER_PRONOUNS,default="he/him")
    image = models.ImageField(upload_to="accounts/profile/", null=True, blank=True)
    thumbnail_image = models.ImageField(upload_to="accounts/thumb/", null=True, blank=True)
    date_updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ('-date_joined',)

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):

        if not self._state.adding and self.image:
            old_instance: User = User.objects.get(pk=self.pk)
            old_image = old_instance.image

            if self.image != old_image:
                name,file = resize(self.image,(30,30))
                self.thumbnail_image.save(name, file, save=False)

        return super(User, self).save(*args, **kwargs)
    
