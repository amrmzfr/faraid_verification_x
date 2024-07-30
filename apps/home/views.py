from django.http import JsonResponse, HttpResponse, FileResponse, Http404, HttpResponseRedirect
from django import template
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.contrib import messages
from .forms import DocumentForm, DocumentFormOfficer
from .models import Document, UserRole, OfficerDocument, UserProfile
from .utils import process_pdf
from .dropbox_sign_service import DropboxSignService
from django.core.mail import send_mail
import json, os
from django.template import loader, TemplateDoesNotExist
from django.conf import settings
from django.core.files.storage import default_storage
import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import google.auth
from googleapiclient.discovery import build
from google.oauth2 import service_account
from django.conf import settings
from django.contrib.auth import get_user_model
import os
from email.mime.text import MIMEText
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model

from .forms import DocumentForm

SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'client_secret_947111274534-snr7bvo97hril4edigrhd7q7ieah3ms4.apps.googleusercontent.com')
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


# ------------------------ GENERAL VIEWS ------------------------ #

@never_cache
@login_required(login_url="/login/")
def pages(request):
    context = {}
    load_template = request.path.split('/')[-1]

    if load_template == 'admin':
        return HttpResponseRedirect(reverse('admin:index'))

    context['segment'] = load_template

    try:
        html_template = loader.get_template(f'home/{load_template}')
        return HttpResponse(html_template.render(context, request))
    
    except TemplateDoesNotExist:
        return HttpResponse(loader.get_template('home/page-404.html').render(context, request))
    
    except Exception:
        return HttpResponse(loader.get_template('home/page-500.html').render(context, request))


@never_cache
@login_required
def index(request):
    context = {'segment': 'index'}
    html_template = template.loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@never_cache
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                
                user_role = user.user_role.role
                return redirect('officer_dashboard' if user_role == 'Officer' else 'home')
            else:
                messages.error(request, "Invalid credentials. Please try again.")

    form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@never_cache
@login_required
def home(request):
    username = request.session.get('username')
    user_id = request.session.get('user_id')
    return render(request, 'home/index.html', {'username': username, 'user_id': user_id})


@login_required
def user_profile_view(request):
    user_profile = get_object_or_404(UserProfile, user_id=request.user.id)
    return render(request, 'home/user.html', {'user_profile': user_profile})

@login_required
def user_profile_officer_view(request):
    user_profile = get_object_or_404(UserProfile, user_id=request.user.id)
    return render(request, 'home/user_officer.html', {'user_profile_officer': user_profile})


# ------------------------ OFFICER VIEWS ------------------------ #

# view the officer dashboard page for officer
@never_cache
@login_required
def officer_dashboard_view(request):
    return render(request, 'home/officer_dashboard.html')



# the table that show the document list
@never_cache
@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id, department=request.user.user_role.department)
    return render(request, 'home/verify_document.html', {'document': document})

@never_cache
@login_required
def uploaded_documents_view(request):
    current_user_email = request.user.email

    # Fetch documents uploaded by the current user
    documents_list = Document.objects.filter(issuer_email=current_user_email)

    # Log the number of documents found for debugging
    print(f"Found {documents_list.count()} documents for user {current_user_email}")

    # Set up pagination
    paginator = Paginator(documents_list, 6)  # Show 6 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Debugging: Print page object details
    print(f"Page number: {page_number}, Page object: {page_obj}")

    return render(request, 'home/uploaded_documents.html', {'page_obj': page_obj})



@never_cache
@login_required
def officer_documents_view(request):
    current_user_email = request.user.email
    department_name = request.user.user_role.department

    # Fetch documents uploaded by the officer
    officer_documents_list = OfficerDocument.objects.filter(
        department=department_name
    )

    # Fetch documents uploaded by users in the officer's department
    user_documents_list = Document.objects.filter(
        department=department_name
    )

    officer_paginator = Paginator(officer_documents_list, 6)
    user_paginator = Paginator(user_documents_list, 6)

    officer_page_number = request.GET.get('officer_page')
    user_page_number = request.GET.get('user_page')
    
    officer_page_obj = officer_paginator.get_page(officer_page_number)
    user_page_obj = user_paginator.get_page(user_page_number)

    return render(request, 'home/uploaded_documents_officer.html', {
        'officer_documents': officer_page_obj,
        'user_documents': user_page_obj
    })

# approve document based on the match/mismatch
@never_cache
@login_required
def approve_document(request):
    title = request.POST.get('title')
    document = get_object_or_404(Document, title=title, status='pending')
    document.status = 'approved'
    document.save()
    return redirect('compare_all_documents', issuer_email=document.issuer_email)

# vice versa
@never_cache
@login_required
def reject_document(request):
    title = request.POST.get('title')
    document = get_object_or_404(Document, title=title, status='pending')
    document.status = 'rejected'
    document.save()
    return redirect('compare_all_documents', issuer_email=document.issuer_email)

# restrict normal user accessing the upload document for officer
@never_cache
@login_required
def upload_documents_officer(request):
    if request.user.user_role.role != 'Officer':
        return redirect('index')

    department_name = request.user.user_role.department
    department_template_mapping = {
        'Pejabat Tanah': 'home/upload_documents_officer_pt.html',
        'JPJ': 'home/upload_documents_officer_jpj.html',
        'KWSP': 'home/upload_documents_officer_kwsp.html',
        'JPN': 'home/upload_documents_officer_jpn.html',
    }

    template_name = department_template_mapping.get(department_name, 'upload_documents_officer_pt.html')

    return handle_uploaded_documents_officer(request, template_name)

# ------------------ DROPDOWN SIGN API --------------------#

# request for the officer signature send to email
@never_cache
def send_officer_signature_view(request):
    if request.method == 'POST':
        officer_email = request.user.email
        service = DropboxSignService()
        document_path = 'documents/Aknowledgement_Form.pdf'

        signer = [
            {
                'email_address': officer_email,
                'name': request.user.get_full_name(),
                'order': 0
            }
        ]

        signature_request = service.send_signature_request(document_path, signer)

        return JsonResponse({'message': 'Signature request sent', 'signature_request_id': signature_request['signature_request_id']})

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# didnt test yet trials end
@never_cache
def signature_completed(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        signature_request_id = data['signature_request_id']
        service = DropboxSignService()
        signed_document = service.get_signed_document(signature_request_id)

        issuer_email = data['issuer_email']
        send_signed_document_to_issuer(issuer_email, signed_document)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid method'}, status=405)


def send_signed_document_to_issuer(email, signed_document):
    subject = "Your Document has been Signed"
    message = "The document has been successfully signed and is attached."
    send_mail(
        subject,
        message,
        'from@example.com',
        [email],
        fail_silently=False,
        html_message="<p>The document has been successfully signed and is attached.</p>",
        attachments=[('signed_document.pdf', signed_document, 'application/pdf')],
    )


# ------------------------ DOCUMENT HANDLING VIEWS ------------------------ #

@never_cache
@login_required
def handle_uploaded_documents_officer(request, template_name):
    if request.method == 'POST':
        form = DocumentFormOfficer(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            user_email = request.user.email
            client_email = request.POST.get('client_email', '')
            doc_type = request.POST.get('doc_type', '')
            new_filename = f"{doc_type}_{client_email}.pdf"

            # Fetch the officer's department
            department_name = request.user.user_role.department
            document.department = department_name  # Assign department to the document

            # Define the directory for officer documents
            officer_directory = os.path.join(settings.MEDIA_ROOT, 'Documents', 'officer')
            if not os.path.exists(officer_directory):
                os.makedirs(officer_directory)

            document.pdf_file.name = os.path.join('Documents', 'officer', new_filename)
            document.title = new_filename
            document.issuer_email = user_email
            document.client_email = client_email

            document.save()
            process_document(request, document)

            return JsonResponse({'success': True, 'message': 'The PDFs are successfully uploaded.'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    form = DocumentFormOfficer()
    return render(request, template_name, {'form': form})

import os
from email.mime.text import MIMEText
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import DocumentForm

SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'client_secret_947111274534-snr7bvo97hril4edigrhd7q7ieah3ms4.apps.googleusercontent.com')
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print(f"Message Id: {message['id']}")
        return message
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

def send_email_to_officer():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('gmail', 'v1', credentials=credentials)

    officer_email = 'unlucky139913@gmail.com'  # Replace with the actual officer's email address
    email_message = create_message(
        sender='muzaffaramir99@gmail.com',  # Replace with your email address
        to=officer_email,
        subject='New Document Uploaded',
        message_text='A new document has been uploaded.'
    )
    send_message(service, 'me', email_message)

@never_cache
@login_required
def handle_uploaded_document(request, template_name, department_name):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            user_email = request.user.email
            doc_type = request.POST.get('doc_type', '')
            new_filename = f"{doc_type}_{user_email}.pdf"

            # Define the directory for user documents
            user_directory = os.path.join(settings.MEDIA_ROOT, 'Documents', 'user')
            if not os.path.exists(user_directory):
                os.makedirs(user_directory)

            document.pdf_file.name = os.path.join('Documents', 'user', new_filename)
            document.title = new_filename
            document.issuer_email = user_email
            document.department = department_name

            document.save()
            process_document(request, document)

            send_email_to_officer()

            return JsonResponse({'success': True, 'message': 'The PDF is successfully uploaded.'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    form = DocumentForm()
    return render(request, template_name, {'form': form})

    
@never_cache
@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    document.delete()
    return redirect('uploaded_documents')  # Redirect to the appropriate page


@never_cache
@login_required
def compare_all_documents(request, issuer_email):
    pending_documents = Document.objects.filter(issuer_email=issuer_email)
    officer_documents = OfficerDocument.objects.filter(client_email=issuer_email)

    comparison_results = []
    officer_docs_dict = {doc.title: doc for doc in officer_documents}

    for index, doc in enumerate(pending_documents, start=1):
        off_doc = officer_docs_dict.get(doc.title)
        status = "Match" if off_doc and doc.hashed_text == off_doc.hashed_text else "Mismatch"
        
        comparison_results.append({
            'number': index,
            'title': doc.title,
            'status': doc.status,
            'hash_value': doc.hashed_text,
            'comparison_status': status,
        })

    return render(request, 'home/verify_document.html', {'issuer_email': issuer_email, 'comparison_results': comparison_results})


# ------------------------ PDF VIEWING VIEWS ------------------------ #

@never_cache
@login_required
def get_pdf(request, document_title):
    document = get_object_or_404(Document, title=document_title)
    response = FileResponse(open(document.pdf_file.path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
    return response


@never_cache
@login_required
def get_officer_pdf(request, document_title):
    officer_document = get_object_or_404(OfficerDocument, title=document_title)
    response = FileResponse(open(officer_document.pdf_file.path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{officer_document.title}.pdf"'
    return response


# ------------------------ VERIFICATION PAGE ------------------------ #

@never_cache
@login_required
def verification_page(request):
    # Get the officer's department
    user_department = request.user.user_role.department

    # Filter pending documents by the officer's department
    pending_emails = Document.objects.filter(
        status='pending',
        department=user_department
    ).values('issuer_email').annotate(pending_count=Count('id'))

    return render(request, 'home/verification_page.html', {'pending_emails': pending_emails})

@never_cache
@login_required
def evaluate_document(request, document_title):
    user_document_url = f"/media/user_documents/{document_title}.pdf"
    officer_document_url = f"/media/officer_documents/{document_title}.pdf"
    
    return render(request, 'home/evaluate_document.html', {
        'document_title': document_title,
        'user_document_url': user_document_url,
        'officer_document_url': officer_document_url,
    })


#----------------------------OTHER VIEW-------------------------#

@never_cache
@login_required
def pendaftaran_negara_view(request):
    return render(request, 'home/pendaftaran_negara.html')


@never_cache
@login_required
def kwsp_view(request):
    return handle_uploaded_document(request, 'home/kwsp.html', 'KWSP')


@never_cache
@login_required
def pejabat_tanah_view(request):
    return handle_uploaded_document(request, 'home/pejabat_tanah.html', 'Pejabat Tanah')


@never_cache
@login_required
def jpj_view(request):
    return handle_uploaded_document(request, 'home/jpj.html', 'JPJ')


# ------------------------ DOCUMENT PROCESSING ------------------------ #

@never_cache
@login_required
def process_document(request, document):
    normalized_text, hashed_text = process_pdf(document.pdf_file)
    document.normalized_text = normalized_text
    document.hashed_text = hashed_text
    document.save()
