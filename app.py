import os
from flask import Flask, render_template, request, flash, redirect
from email_validator import validate_email, EmailNotValidError
from google_images_search import GoogleImagesSearch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import zipfile
import shutil
import requests

app = Flask(__name__)
app.secret_key = 'f8db7b96015ad6ef63c10fd706ee70e99a1dddd878d82eac'

# Email configuration
EMAIL_ADDRESS = 'aakshit_be22@thapar.edu'
EMAIL_PASSWORD = 'ecgh cuwj ksbx iczn'

# Google API configuration
GOOGLE_API_KEY = 'AIzaSyDC6bV6SWAi7CdXnrDY8GoaY2f9GBvYssA'
GOOGLE_CSE_ID = '12434ceecca724a49'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        # Get form data
        image_count = int(request.form.get('image_count'))
        email = request.form.get('email')
        attribute = request.form.get('attribute')

        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError as e:
            flash(str(e))
            return redirect('/')

        # Initialize Google Images Search client
        gis = GoogleImagesSearch(GOOGLE_API_KEY, GOOGLE_CSE_ID)

        # Fetch images
        image_urls = fetch_images(gis, attribute, image_count)

        # Download images and zip them
        zip_file = create_zip(attribute, image_urls)

        # Send the email with the images attached
        send_email(email, zip_file)

        # Clean up downloaded files
        shutil.rmtree('downloads')
        os.makedirs('downloads', exist_ok=True)

        flash('Images downloaded and sent to your email successfully!')
        return render_template('success.html')
    except Exception as e:
        flash(f'Error: {e}')
        return redirect('/')
        pass 


def fetch_images(gis, query, count):
    image_urls = []
    search_params = {
        'q': query,
        'num': count,
        'safe': 'medium',
        'fileType': 'jpg',
        'imgType': 'photo',
        'imgSize': 'medium'
    }
    
    gis.search(search_params)
    for image in gis.results()[:count]:
        image_urls.append(image.url)
    
    return image_urls

def create_zip(attribute, image_urls):
    os.makedirs('downloads', exist_ok=True)
    
    # Download images and save them
    for i, url in enumerate(image_urls):
        response = requests.get(url, stream=True)
        file_path = f"downloads/{attribute}_{i + 1}.jpg"
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

    # Zip the images
    zip_file = f"downloads/{attribute}_images.zip"
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for root, _, files in os.walk('downloads'):
            for file in files:
                if file.endswith('.jpg'):
                    zipf.write(os.path.join(root, file), file)
    
    return zip_file

def send_email(to_email, zip_file):
    # Prepare the email
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = 'Your Requested Images'

    # Email body
    body = 'Please find the requested images attached.'
    msg.attach(MIMEText(body, 'plain'))

    # Attach zip file
    attachment = open(zip_file, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(zip_file)}')
    msg.attach(part)

    # Send email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    app.run(debug=True)

