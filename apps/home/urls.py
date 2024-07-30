from django.urls import path, re_path
from apps.home import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),  # Redirect root URL to login

    # Home page after login
    path('home/', views.index, name='home'),
    path('profile/', views.user_profile_view, name='user_profile'),
    path('profile_officer/', views.user_profile_officer_view, name='user_profile_officer'),

    # Document Management
    path('uploaded-documents/', views.uploaded_documents_view, name='uploaded_documents'),
    path('pejabat-tanah/', views.handle_uploaded_document, kwargs={'template_name': 'home/pejabat_tanah.html', 'department_name': 'Pejabat Tanah'}, name='pejabat_tanah'),
    path('upload-documents-officer/', views.upload_documents_officer, name='upload_documents_officer'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('view-document/<int:document_id>/', views.view_document, name='view_document'),
    path('officer-documents/', views.officer_documents_view, name='officer_documents'),
    path('verification/', views.verification_page, name='verification_page'),

    # Officer Actions
    path('officer-dashboard/', views.officer_dashboard_view, name='officer_dashboard'),
    path('approve-document/', views.approve_document, name='approve_document'),
    path('reject-document/', views.reject_document, name='reject_document'),
    path('send-officer-signature/', views.send_officer_signature_view, name='send_officer_signature'),
    path('signature-completed/', views.signature_completed, name='signature_completed'),

    # Document Retrieval
    path('get-pdf/<str:document_title>/', views.get_pdf, name='get_pdf'),
    path('get-officer-pdf/<str:document_title>/', views.get_officer_pdf, name='get_officer_pdf'),

    # Document Comparison
    path('compare-all-documents/<str:issuer_email>/', views.compare_all_documents, name='compare_all_documents'),

    # Specific Paths
    path('pendaftaran-negara/', views.pendaftaran_negara_view, name='pendaftaran_negara'),
    path('pejabat-tanah/', views.pejabat_tanah_view, name='pejabat_tanah'),
    path('kwsp/', views.kwsp_view, name='kwsp'),
    path('jpj/', views.jpj_view, name='jpj'),

    # Catch-all for any .html files
    re_path(r'^.*\.*', views.pages, name='pages'),
]
