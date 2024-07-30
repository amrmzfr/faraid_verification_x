from dropbox_sign import ApiClient, ApiException, Configuration, apis,models
from django.conf import settings

class DropboxSignService:
    def __init__(self):
        configuration = Configuration(
            username="2e684460fda4a69c81b191865a382ee73056c057b8c1b77df40778dca5e0ba9d",
        )
        self.client = ApiClient(configuration)
        self.signature_request_api = apis.SignatureRequestApi(self.client)

    def send_signature_request(self, file_path, signers):
        signer_models = [
            models.SubSignatureRequestSigner(
                email_address=signer['email_address'],
                name=signer['name'],
                order=i,
            )
            for i, signer in enumerate(signers)
        ]

        data = models.SignatureRequestSendRequest(
            title="Document for Signature",
            subject="Please sign this document",
            message="Let me know if you have any questions.",
            signers=signer_models,
            files=[open(file_path, "rb")],
            test_mode=True,
        )

        response = self.signature_request_api.signature_request_send(data)
        return response