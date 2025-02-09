import os
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone




app = Flask(__name__)
# Azure Blob Storage credentials
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
BLOB_CONTAINER_NAME = 'weez-file-webview'

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)


# **1. Upload File Automatically when Opened**
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        username = request.form.get('username')
        file = request.files.get('file')  # File received from the client

        if not username or not file:
            return jsonify({'error': 'Username or file missing'}), 400

        filename = file.filename  # Get the filename
        blob_path = f"{username}/{filename}"  # Store under username directory

        # Get container client & upload file to Azure Blob Storage
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_path)

        blob_client.upload_blob(file, overwrite=True)  # Upload file

        return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# **2. Generate SAS Token for File**
@app.route('/generate-sas', methods=['POST'])
def generate_sas():
    try:
        data = request.get_json()
        username = data.get('username')
        filename = data.get('filename')

        if not username or not filename:
            return jsonify({'error': 'Username or filename missing'}), 400

        blob_path = f"{username}/{filename}"  # File path inside the container
        blob_client = blob_service_client.get_blob_client(BLOB_CONTAINER_NAME, blob_path)

        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=BLOB_CONTAINER_NAME,
            blob_name=blob_path,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=1)  # Token expires in 1 hour
        )

        # Create full SAS URL
        sas_url = f"{blob_client.url}?{sas_token}"

        return jsonify({'sasUrl': sas_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
