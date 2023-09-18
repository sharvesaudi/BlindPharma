from flask import Flask, request, jsonify
from PIL import Image
import uuid
import os
import base64
import openpyxl
from io import BytesIO
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import re
import time
import os
from PIL import Image
import pandas as pd
import time

app = Flask(__name__)

def extract(image_path):
    # Azure stuffs
    subscription_key = ''
    endpoint = ''
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
    print("======== DEBUG START ========")
    print(f"File: {image_path}")
    with open(image_path, "rb") as read_image:
        read_response = computervision_client.read_in_stream(read_image, raw=True)
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]
    print("Operation ID:", operation_id)
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)
    print("Response received from server")
    string = ""
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            string += "\n".join([line.text for line in text_result.lines])
    print("String created")
    
    # Search for the medicine name
    print(string)
    flag = False
    string = string.lower()
    df = pd.read_excel('med.xlsx', engine='openpyxl')
    df.iloc[:, 1] = df.iloc[:, 1].str.lower()
    for i, row in df.iterrows():
        words = row[1].split()
        words = [word.lower() for word in words]
        if any(word in string for word in words):
            flag = True
            name = row[1].capitalize()
            desc = row[2].capitalize()
            print("Name and description found", name, desc)
    if (flag != True):
        name = "Name not found"
        desc = "Please take the picture again"
        print("Name and description not found")

    # Search for the expiry date
    regex_pattern = r'\b(\d{2}/\d{4}|(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\.\d{4}|\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{4}|\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\.\d{2})\b'
    dates = re.findall(regex_pattern, string, re.IGNORECASE)
    print("Dates found:", dates)
    if len(dates) > 0:
        result = ' '.join([date[0] for date in dates])
        print(result)
        return {'date':result, 'name':name, 'desc':desc}
    print("Date not found")
    return {'date':"Date not found", 'name':name, 'desc':desc}
 

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/text', methods=['POST'])
def text():
    print("Testtt")
    file = request.files['keyname']
    print("error")
    return "Image Received"

@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.get_json()
    image_bytes = base64.b64decode(data['image'])
    image_buffer = BytesIO(image_bytes)
    img = Image.open(image_buffer)
    print("image")
    filename = str(uuid.uuid4()) + '.jpeg'
    image_path = os.path.join('pre_process','input', filename)
    print("image path", image_path)
    img.save(image_path)
    print("Saved image")
    temp = jsonify(extract(image_path))
    return temp

@app.route('/test', methods=['POST'])
def test():
    print("Testing...")
    image = request.files['image']
    filename = str(uuid.uuid4()) + ".jpeg"
    image_path = os.path.join('pre_process','input', filename)
    image.save(image_path)
    print("Image saved: ", image_path)
    print("Image processed")
    temp = jsonify(extract(image_path))
    return temp

# @app.route('/test', methods=['POST'])
# def test():
#     print("Testing...")
#     image = request.files['image']
#     filename = str(uuid.uuid4()) + '.jpeg'
#     image_path = os.path.join('pre_process','input', filename)
#     print(image_path)
#     image.save(image_path)
#     print("Image saved: ", image_path)
#     print("Image processed")
#     temp = jsonify(extract(image_path))
#     return temp

if __name__ == '__main__':
    app.run(debug=False)
