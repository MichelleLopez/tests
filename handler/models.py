from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Registration(models.Model):
    """
    Model for saving a Registration Form
    """
    # Data types
    name = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    email = models.EmailField()
    depto = models.CharField(max_length=50)


class Contact(models.Model):
    """
    Model for a contact form.
    """
    email_address = models.EmailField()
    name = models.CharField(max_length=100)
    
