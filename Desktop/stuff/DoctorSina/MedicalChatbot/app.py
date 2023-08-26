import json
import torch
import nltk
import pickle
import random
from datetime import datetime
import numpy as np
import pandas as pd

from nnet import NeuralNet
from nltk_utils import bag_of_words
from flask import Flask, request, jsonify

random.seed(datetime.now())

device = torch.device('cpu')
FILE = "models/data.pth"
model_data = torch.load(FILE)

input_size = model_data['input_size']
hidden_size = model_data['hidden_size']
output_size = model_data['output_size']
all_words = model_data['all_words']
tags = model_data['tags']
model_state = model_data['model_state']

nlp_model = NeuralNet(input_size, hidden_size, output_size).to(device)
nlp_model.load_state_dict(model_state)
nlp_model.eval()

diseases_description = pd.read_csv("data/symptom_Description.csv")
diseases_description['Disease'] = diseases_description['Disease'].apply(lambda x: x.lower().strip(" "))

disease_precaution = pd.read_csv("data/symptom_precaution.csv")
disease_precaution['Disease'] = disease_precaution['Disease'].apply(lambda x: x.lower().strip(" "))

symptom_severity = pd.read_csv("data/Symptom-severity.csv")
symptom_severity = symptom_severity.applymap(lambda s: s.lower().strip(" ").replace(" ", "") if type(s) == str else s)


with open('data/list_of_symptoms.pickle', 'rb') as data_file:
    symptoms_list = pickle.load(data_file)

with open('models/fitted_model.pickle', 'rb') as modelFile:
    prediction_model = pickle.load(modelFile)

user_symptoms = set()

app = Flask(__name__)

def get_symptom(sentence):
    sentence = nltk.word_tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X)

    output = nlp_model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    prob = prob.item()

    return tag, prob
@app.route('/api/predict_symptom', methods=['POST'])
def predict_symptom_api():
    try:
        print("Received POST request.")
        request_data = request.json
        print("Request data:", request_data)
        
        sentence = request_data['sentence']
        print("Received sentence:", sentence)
        
        response_data = predict_symptom(sentence)
        print("Response data:", response_data)
        
        return response_data
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({"error": "An error occurred"}), 500

def predict_symptom(sentence):
    print("Request json:", request.json)
    sentence = request.json['sentence']
    if sentence.replace(".", "").replace("!","").lower().strip() == "done":

        if not user_symptoms:
            response_sentence = "I can't know what disease you may have if you don't enter any symptoms :)"
        else:
            x_test = []
            
            for each in symptoms_list: 
                if each in user_symptoms:
                    x_test.append(1)
                else: 
                    x_test.append(0)

            x_test = np.asarray(x_test)            
            disease = prediction_model.predict(x_test.reshape(1,-1))[0]
            print(disease)

            description = diseases_description.loc[diseases_description['Disease'] == disease.strip(" ").lower(), 'Description'].iloc[0]
            precaution = disease_precaution[disease_precaution['Disease'] == disease.strip(" ").lower()]
            precautions = 'Precautions: ' + precaution.Precaution_1.iloc[0] + ", " + precaution.Precaution_2.iloc[0] + ", " + precaution.Precaution_3.iloc[0] + ", " + precaution.Precaution_4.iloc[0]
            response_sentence = "It looks to me like you have " + disease + ". <br><br> <i>Description: " + description + "</i>" + "<br><br><b>"+ precautions + "</b>"
            
            severity = []

            for each in user_symptoms: 
                severity.append(symptom_severity.loc[symptom_severity['Symptom'] == each.lower().strip(" ").replace(" ", ""), 'weight'].iloc[0])
                
            if np.mean(severity) > 4 or np.max(severity) > 5:
                response_sentence = response_sentence + "<br><br>Considering your symptoms are severe, and Meddy isn't a real doctor, you should consider talking to one. :)"

            user_symptoms.clear()
            severity.clear()
 
    else:
        symptom, prob = get_symptom(sentence)
        print("Symptom:", symptom, ", prob:", prob)
        if prob > .5:
            response_sentence = f"Hmm, I'm {(prob * 100):.2f}% sure this is " + symptom + "."
            user_symptoms.add(symptom)
        else:
            response_sentence = "I'm sorry, but I don't understand you."

        print("User symptoms:", user_symptoms)

    return jsonify({"response": response_sentence.replace("_", " ")})


if __name__ == '__main__':
    app.run()
