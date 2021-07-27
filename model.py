from google.api_core.client_options import ClientOptions
import googleapiclient.discovery
from google.cloud import vision
import numpy as np
from PIL import Image

#import os
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"

def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

class InstaPredLikeModel():
    def __init__(self, model, version):
        endpoint = 'https://ml.googleapis.com'
        client_options = ClientOptions(api_endpoint=endpoint)
        self.service = googleapiclient.discovery.build('ml', 'v1', client_options= client_options)
        self.name = 'projects/{}/models/{}/versions/{}'.format("instapred", model, version)

    def predict(self, img):
        width, height = 200, 200
        temp = img.resize((width, height), Image.ANTIALIAS)
        np_img = np.array(temp)
        np_img = np_img.reshape((1, width, height, 3))
        pred = self.service.projects().predict(name= self.name, body={'instances': np_img.tolist()}).execute()
        pred = int(pred["predictions"][0]["dense_1"][0])
        if pred > 0:
            return pred
        else:
            return 0

class InstaPredLabelModel():
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def predict(self, img):
        image = vision.Image(content=img)
        response = self.client.label_detection(image=image)
        labels = [label.description.lower().split(" ") for label in response.label_annotations]
        labels = [item for sublist in labels for item in sublist]
        labels = f7(labels)
        labels = ["#"+ label for label in labels]
        return labels[:4]


#model = InstaPredLabelModel()
#path= './model_dev/webdev_ig/Bl6SGdZg2FT.jpg'
#with io.open(path, 'rb') as image_file:
#    content = image_file.read()
#model.predict(content)