from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import requests, uuid, json
import time
from multiprocessing.pool import ThreadPool
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.storage.blob import ContentSettings, ContainerClient
import numpy as np
import os
from datetime import datetime, timedelta
app = Flask(__name__)
from pydub import AudioSegment
from pydub.utils import make_chunks
def get_translation(input_file):
    # Add your subscription key and endpoint
    subscription_key = "4c93fdb701864d15821d71b05f28000c"
    endpoint = "https://api.cognitive.microsofttranslator.com"
    # Add your location, also known as region. The default ise.
    location = "global"
    # This is required if using a Cognitive Services resourc
    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': ['ar']
            }
    constructed_url = endpoint + path

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
                }
    with open(input_file) as f:
        lines=f.read()
    outname = "TranslatedScripts/" + str(input_file[:-7]) + "ar.vtt"
    List_path = outname.split("/")
    path = '/'.join(List_path[:-1])
    isExist = os.path.exists(path)
    a=[]
    if not isExist:
        os.makedirs(path)
    out=open(outname,"w",encoding="utf-8")

    if input_file.split(".")[-1]=="vtt":
        out.write("WEBVTT\n")
    else:
        out.write("")
    out = open(outname, "a+", encoding="utf-8")
    body = [{
        'text': lines
    }]
    request = requests.post(constructed_url, params=params, headers=headers, json=body)

    response = request.json()
    # print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))
    json_object = json.loads(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))
    print(json_object[0].get("translations")[0]["text"])
    out.write("".join(json_object[0].get("translations")[0]["text"]))
    print(json_object[0]['translations'][0]['text'])
    a.append(str(json_object[0].get("translations")[0]["text"]))



    print(a)
    upload_fileblob(outname)

    return a
# IMPORTANT: Replace connection string with your storage account connection string
# Usually starts with DefaultEndpointsProtocol=https;...
MY_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=mlpoc013710750505;AccountKey=f3EPu+3a0Y1GI+ur2tQMxr6e7dhQiSEmkDY+/LgdxdSKJbiK9EC5F1z82dD8X9dV0uMFl77ABfhKfuNwts67Dw==;EndpointSuffix=core.windows.net"

# Replace with blob container
MY_IMAGE_CONTAINER = "vtts"

# Replace with the local folder which contains the image files for upload
LOCAL_IMAGE_PATH = ""

blob_service_client = BlobServiceClient.from_connection_string(MY_CONNECTION_STRING)



def upload_fileblob(file_name):
        # Create blob with same name as local file name
        blob_client = blob_service_client.get_blob_client(container=MY_IMAGE_CONTAINER,
                                                               blob=file_name)
        # Get full path to the file
        upload_file_path =file_name
        # Create blob on storage
        # Overwrite if it already exists!
        image_content_setting = ContentSettings(content_type='image/jpeg')
        print(f"uploading file - {file_name.split('/')[-1]}")
        with open(upload_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True, content_settings=image_content_setting)

import azure.cognitiveservices.speech as speechsdk


def get_text(input_file):
    outname="RecognizedScripts/"+str(input_file[:-4])+".txt"
    List_path=outname.split("/")
    path ='/'.join(List_path[:-1])
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    out = open(outname, "w+")
    a=[]
    speech_recognize_continuous_from_file(input_file,a)
    print(" ".join(a))
    for b in a:
        out.write(b + "\n")
    out.close()
    return outname

def speech_recognize_continuous_from_file(input_file,a):
    """performs continuous speech recognition with input from an audio file"""
    # <SpeechContinuousRecognitionWithFile>
    speech_config = speechsdk.SpeechConfig(subscription="6e265f482cdd4adcab8f1901bf572cfa", region="uaenorth")
    speech_config.speech_recognition_language = "en-US"

    # To recognize speech from an audio file, use `filename` instead of `use_default_microphone`:
    audio_config = speechsdk.audio.AudioConfig(filename=input_file)
    #audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    done = False

    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        speech_recognizer.stop_continuous_recognition()
        nonlocal done
        done = True
    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    speech_recognizer.recognized.connect(lambda evt: a.append(evt.result.text))
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    #stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)
    # </SpeechContinuousRecognitionWithFile>

def process_sudio(file_name):
    myaudio = AudioSegment.from_file(file_name, "wav")
    chunk_length_ms = 10000 # pydub calculates in millisec
    chunks = make_chunks(myaudio,chunk_length_ms) #Make chunks of one sec
    chunks_name_list=[]
    for i, chunk in enumerate(chunks):
        try:
            os.makedirs('chunked/'+file_name[:-4])  # creating a folder named chunked
        except:
            pass
        chunk_name = './chunked/'+file_name[:-4]+ "/"+ file_name + "_{0}.wav".format(i)
        chunks_name_list.append(chunk_name)
        chunk.export(chunk_name, bitrate="192kHz",format="wav")
    return chunks_name_list
# Initialize class and upload files
@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        print(f.filename)
        chunk_name_list = process_sudio(f.filename)
        print(chunk_name_list)
        txt_name_list = []
        for name in chunk_name_list:
            path = get_text(name)
            txt_name_list.append(path.replace("./", ""))
        print(txt_name_list)
        p = "/".join(txt_name_list[0].split("/")[:-1])
        if not os.path.exists(p):
            os.makedirs(p)

        scriptTextVtt = str(p) + "/" + str(f.filename[:-4]) + "_eng.vtt"
        scriptText = str(p) + "/" + str(f.filename[:-4]) + "_eng.txt"
        with open(scriptTextVtt, 'w') as outfile:

            # Iterate through list
            count = 0
            outfile.write("WEBVTT\n")
            t = 0
            for c in txt_name_list:
                # Open each file in read mode
                with open(c) as infile:
                    outfile.write(str(timedelta(milliseconds=t)))
                    t = t + 10000
                    outfile.write("-->")
                    outfile.write(str(timedelta(milliseconds=t)) + "\n")
                    outfile.write(infile.read() + "\n")

                # Add '\n' to enter data of file2
                # from next line
                outfile.write("\n")
        upload_fileblob(scriptTextVtt)
        with open(scriptText, 'w') as englishtext:
            for c in txt_name_list:
                # Open each file in read mode
                with open(c) as infile:
                    englishtext.write(infile.read() + "\n")
                # Add '\n' to enter data of file2
                # from next line
                englishtext.write("\n")

        # scripttext=SpeechRecognizer.get_text(f.filename)
        text = get_translation(scriptText)
        get_translation(scriptTextVtt)
        return "\n".join(text)
    else:
        return "Hello World"


if __name__ == '__main__':
   app.run()