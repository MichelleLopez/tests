from django.db.models import TextField
from django.forms import ModelForm, RegexField

from handler.models import Registration, Contact


class RegistrationForm(ModelForm):
    
    class Meta:
        model = Registration
        fields = '__all__'


class ContactForm(ModelForm):
    """
    Form for the Contact model.
    """
    class Meta:
        model = Contact
        fields = '__all__'
