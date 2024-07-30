from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Document, OfficerDocument, DocumentTest

class DocumentFormOfficer(forms.ModelForm):

    class Meta:
        model = OfficerDocument
        fields = ('pdf_file', 'client_email')

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('pdf_file',)


class DocumentFormTest(forms.ModelForm):
    signer_name = forms.CharField(max_length=255)
    signer_email = forms.EmailField()

    class Meta:
        model = DocumentTest
        fields = ['file', 'signer_name', 'signer_email']