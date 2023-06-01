from django.shortcuts import render
from django.http import HttpResponse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pyexpat import model
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.impute import KNNImputer
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

def predictHeart(request):
    return render(request,'predictHeart.html')

def InfoMaladieChronique(request):
    return render(request,'InfoMaladieChronique.html')

def Apropos(request):
    return render(request,'Apropos.html')

def info_Heart(request):
    return render(request,'info_Heart.html')

def info_Anemie(request):
    return render(request,'info_Anemie.html')

def info_Avc(request):
    return render(request,'info_Avc.html')

def info_Diabete(request):
    return render(request,'info_Diabete.html')

def info_Kidney(request):
    return render(request,'info_Kidney.html')

def info_Hypothyroid(request):
    return render(request,'info_Hypothyroid.html')

def predictHypothyroid(request):
    return render(request,'predictHypothyroid.html')

def predictKidney(request):
    return render(request,'predictKidney.html')

def predictDiabete(request):
    return render(request,'predictDiabete.html')

def predictAnemie(request):
    return render(request,'predictAnemie.html')

def predictAvc(request):
    return render(request,'predictAvc.html')
def resultHeart(request):
    heart_data = pd.read_csv("C:/Users/salma/OneDrive/Documents/Exemple/heart.csv")
    X = heart_data.drop(columns='target', axis=1)
    Y = heart_data['target']
    X_train,X_test,Y_train,Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)
    lin_model = LogisticRegression()
    # training the LogisticRegression model with Training data
    lin_model.fit(X_train, Y_train)
    age = float(request.GET['age'])
    sex = float(request.GET['sex'])
    chest_pain_type = float(request.GET['chest-pain-type'])
    resting_bp = float(request.GET['resting-bp'])
    cholesterol = float(request.GET['cholesterol'])
    fasting_bs =float( request.GET['fasting-bs'])
    resting_ecg = float(request.GET['resting-ecg'])
    max_hr = float(request.GET['max-hr'])
    exang = float(request.GET['exang'])
    oldpeak = float(request.GET['oldpeak'])
    st_slope = float(request.GET['st-slope'])
    num_vessels = float(request.GET['num-vessels'])
    thal = float(request.GET['thal'])
    input_data= np.array([age,sex,chest_pain_type,resting_bp,cholesterol,fasting_bs,resting_ecg,max_hr,exang,oldpeak,st_slope,num_vessels,thal]).reshape(1,-1)
    pred = lin_model.predict(input_data)
    result2 = ""
    if pred ==[1]:
        result1="Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires,"\
               " veuillez cliquer sur le lien suivant "


    else:
        result1="Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                " pour maintenir votre bien-être." \
        "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires,"\
               " veuillez cliquer sur le lien suivant "

    return render(request, 'predictHeart.html',{"result2":result1})
def resultHypothyroid(request):
    hypothroid_data = pd.read_csv("C:/Users/salma/OneDrive/Documents/Exemple/thyroid.csv")
    hypothroid_data.drop("other", axis=1, inplace=True)
    feature_cols = ["age",
                    "sex",
                    "on_thyroxine",
                    "query_on_thyroxine",
                    "on_antithyroid_medication",
                    "sick",
                    "pregnant",
                    "thyroid_surgery",
                    "I131_treatment",
                    "query_hypothyroid",
                    "query_hyperthyroid",
                    "lithium",
                    "goitre",
                    "tumor",
                    "hypopituitary",
                    "psych",
                    "TSH measured",
                    "TSH",
                    "T3_measured",
                    "T3",
                    "TT4_measured",
                    "TT4",
                    "T4U_measured",
                    "T4U",
                    "FTI_measured",
                    "FTI",
                    "TBG_measured",
                    "TBG",
                    "target"]
    hypothroid_data.columns = feature_cols

    target = hypothroid_data.target
    create = target.str.split('([A-Za-z]+)', expand=True)
    create = create[1]
    target = create.replace({None: 'Z'})  # here z is none type
    hypothroid_data.target = target
    hypothroid_data = hypothroid_data.replace(['?'], np.nan)

    # here we can see the TBG has more null observations it will tremendously occur problem so we can remove and some of the other
    # feautre rows which is not useful

    hypothroid_data.drop(
        ['TBG_measured', 'TBG', 'T3_measured', 'TSH measured', 'TT4_measured', 'T4U_measured', 'FTI_measured'], axis=1,
        inplace=True)
    hypothroid_data.sex.replace({'F': 0, 'M': 1}, inplace=True)
    round_Values = round(hypothroid_data.sex.mean())
    hypothroid_data.sex.fillna(round_Values, inplace=True)
    # now we will impute the null values with knn imputer
    knnimp = KNNImputer(n_neighbors=3)

    cols = ['TSH', 'T3', 'TT4', 'T4U', 'FTI']
    for i in cols:
        hypothroid_data[i] = knnimp.fit_transform(hypothroid_data[[i]])
    le = LabelEncoder()
    cols = hypothroid_data.select_dtypes(include=['object'])

    for i in cols.columns:
        try:
            hypothroid_data[i] = le.fit_transform(hypothroid_data[i])
        except:
            continue
    # X and Y split

    X = hypothroid_data.drop('target', axis=1)
    Y = hypothroid_data.target

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.33, random_state=42)
    tree_model = DecisionTreeClassifier()
    tree_model.fit(X_train, Y_train)
    age = float(request.GET['age'])
    sex = str(request.GET['sex'])
    on_thyroxine = str(request.GET['thyroide'])
    query_on_thyroxine = str(request.GET['surthyroide'])
    on_antithyroid_medication = str(request.GET['antithyroidien'])
    sick = str(request.GET['sick'])
    pregnant = str(request.GET['enceinte'])
    thyroid_surgery = str(request.GET['thyroid_surgery'])
    I131_treatment = str(request.GET['I131_treatment'])
    query_hypothyroid = str(request.GET['query_hypothyroid'])
    query_hyperthyroid = str(request.GET['query_hyperthyroid'])
    lithium = str(request.GET['lithium'])
    goitre = str(request.GET['goitre'])
    tumor = str(request.GET['tumor'])
    hypopituitary = str(request.GET['Hypopituitary'])
    psych = str(request.GET['psych'])
    TSH = float(request.GET['TSH'])
    T3 = float(request.GET['T3'])
    TT4 = float(request.GET['TT4'])
    T4U = float(request.GET['T4U'])
    FTI = float(request.GET['FTI'])



    # Préparer les données d'entrée pour la prédiction
    input_data = np.array(
        [age, sex, on_thyroxine, query_on_thyroxine, on_antithyroid_medication, sick, pregnant, thyroid_surgery,
         I131_treatment, query_hypothyroid, query_hyperthyroid, lithium, goitre, tumor, hypopituitary, psych, TSH, T3,
         TT4, T4U, FTI]).reshape(1, -1)

    # Faire la prédiction
    pred = tree_model.predict(input_data)

    result2 = ""
    if pred ==[1]:
        result1 = "Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                  " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "

    else:
        result1 = "Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                  " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                  " pour maintenir votre bien-être." \
                  "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    return render(request, 'predictHypothyroid.html',{"result2":result1})

def resultAnemie(request):
    data = pd.read_csv(r"C:\Users\salma\OneDrive\Documents\datasets\anemia.csv")

    x = data.drop(columns='Result', axis=1)
    y = data['Result']
    # partionner les données en test set et training set
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20, random_state=2)

    dtc = DecisionTreeClassifier(max_depth=3)
    dtc.fit(x_train, y_train)

    val1 = float(request.GET['n1'])
    val2 = float(request.GET['n2'])
    val3 = float(request.GET['n3'])
    val4 = float(request.GET['n4'])
    val5 = float(request.GET['n5'])

    input_data = np.array([val1, val2, val3, val4, val5]).reshape(1, -1)

    pred = dtc.predict(input_data)
    resultan = ""
    if pred == [1]:
        resultan = "Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                  " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    else:
        resultan = "Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                  " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                  " pour maintenir votre bien-être." \
                  "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    return render(request, "predictAnemie.html", {"result": resultan})

def resultKidney(request):
    maladies_rénales_data = pd.read_csv("C:/Users/salma/OneDrive/Documents/Exemple/kidney_disease.csv")
    maladies_rénales_data.drop('id', axis=1, inplace=True)
    # renommer les noms de colonne pour le rendre plus convivial
    maladies_rénales_data.columns = ['age', 'pression_sanguine', 'gravité_spécifique', 'albumine', 'sucre',
                                     'globules_rouges', 'cellule_pus',
                                     'agrégats de cellules de pus', 'bactéries', 'glycémie aléatoire', 'urée sanguine',
                                     'créatinine sérique', 'sodium',
                                     'potassium', 'hémoglobine', 'hématocrite', 'numération_des_globules_blancs',
                                     'numération_des_globules_rouges',
                                     'hypertension', 'diabète_sucré', 'maladie_coronarienne', 'appétit',
                                     'œdème_pédiatrique',
                                     'anémie', 'classe']
    # converting necessary columns to numerical type

    maladies_rénales_data['hématocrite'] = pd.to_numeric(maladies_rénales_data['hématocrite'], errors='coerce')
    maladies_rénales_data['numération_des_globules_blancs'] = pd.to_numeric(
        maladies_rénales_data['numération_des_globules_blancs'], errors='coerce')
    maladies_rénales_data['numération_des_globules_rouges'] = pd.to_numeric(
        maladies_rénales_data['numération_des_globules_rouges'], errors='coerce')
    # Extracting categorical and numerical columns

    categorie_cols = [col for col in maladies_rénales_data.columns if maladies_rénales_data[col].dtype == 'object']
    numerique_cols = [col for col in maladies_rénales_data.columns if maladies_rénales_data[col].dtype != 'object']

    # replace incorrect values

    maladies_rénales_data['diabète_sucré'].replace(to_replace={'\tno': 'no', '\tyes': 'yes', ' yes': 'yes'},
                                                   inplace=True)

    maladies_rénales_data['maladie_coronarienne'] = maladies_rénales_data['maladie_coronarienne'].replace(
        to_replace='\tno', value='no')

    maladies_rénales_data['classe'] = maladies_rénales_data['classe'].replace(
        to_replace={'ckd\t': 'ckd', 'notckd': 'not ckd'})

    maladies_rénales_data['classe'] = maladies_rénales_data['classe'].map({'ckd': 0, 'not ckd': 1})
    maladies_rénales_data['classe'] = pd.to_numeric(maladies_rénales_data['classe'], errors='coerce')

    # filling null values, we will use two methods, random sampling for higher null values and
    # mean/mode sampling for lower null values

    def random_value_imputation(feature):
        random_sample = maladies_rénales_data[feature].dropna().sample(maladies_rénales_data[feature].isna().sum())
        random_sample.index = maladies_rénales_data[maladies_rénales_data[feature].isnull()].index
        maladies_rénales_data.loc[maladies_rénales_data[feature].isnull(), feature] = random_sample

    def impute_mode(feature):
        mode = maladies_rénales_data[feature].mode()[0]
        maladies_rénales_data[feature] = maladies_rénales_data[feature].fillna(mode)

    # filling num_cols null values using random sampling method

    for col in numerique_cols:
        random_value_imputation(col)
    # filling "red_blood_cells" and "pus_cell" using random sampling method and rest of cat_cols using mode imputation

    random_value_imputation('globules_rouges')
    random_value_imputation('cellule_pus')

    for col in categorie_cols:
        impute_mode(col)

        # codage

    le = LabelEncoder()

    for col in categorie_cols:
        maladies_rénales_data[col] = le.fit_transform(maladies_rénales_data[col])
# model
    X = maladies_rénales_data.drop(columns='classe', axis=1)
    Y = maladies_rénales_data['classe']
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.30, random_state=0)


    ada = AdaBoostClassifier()
    ada.fit(X_train, Y_train)

    age = float(request.GET['age'])
    tension_arterielle = float(request.GET['tension_arterielle'])
    gravite_specifique = float(request.GET['gravite_specifique'])
    albumine = float(request.GET['albumine'])
    sucre = float(request.GET['sucre'])
    globules_rouges = float(request.GET['globules_rouges'])
    cellule_pus = float(request.GET['cellule_pus'])
    amas_cellules_pus = float(request.GET['amas_cellules_pus'])
    bacteries = float(request.GET['bacteries'])
    glycemie_aleatoire = float(request.GET['glycemie_aleatoire'])
    Uree_sanguine = float(request.GET['Uree_sanguine'])
    Creatinine_serique = float(request.GET['Creatinine_serique'])
    sodium = float(request.GET['sodium'])
    Potassium = float(request.GET['potassium'])
    Hémoglobine = float(request.GET['hemoglobine'])
    Volume_hematocrite = float(request.GET['Volume_hematocrite'])
    Numeration_des_globules_blancs = float(request.GET['Numeration_des_globules_blancs'])
    Numeration_des_globules_rouges = float(request.GET['Numeration_des_globules_rouges'])
    Hypertension = str(request.GET['Hypertension'])
    Diabete_sucre = str(request.GET['Diabete_sucre'])
    Maladie_coronarienne = str(request.GET['Maladie_coronarienne'])
    appétit = str(request.GET['Appétit'])
    Œdème_de_la_pédale = str(request.GET['Œdème_de_la_pédale'])
    Anémie = str(request.GET['Anémie'])
    input_data = np.array(
        [age, tension_arterielle, gravite_specifique, albumine, sucre, globules_rouges, cellule_pus, amas_cellules_pus, bacteries, glycemie_aleatoire, Uree_sanguine,
         Creatinine_serique, sodium,Potassium,Hémoglobine,Volume_hematocrite,Numeration_des_globules_blancs,Numeration_des_globules_rouges, Hypertension,
         Diabete_sucre,Maladie_coronarienne,appétit,Œdème_de_la_pédale,Anémie]).reshape(1, -1)
    pred = ada.predict(input_data)
    result2 = ""
    if pred ==[1]:
        result1 = "Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                  " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    else:
        result1 = "Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                  " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                  " pour maintenir votre bien-être." \
                  "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    return render(request, 'predictKidney.html',{"result2":result1})


def resultDiabete(request):
    data = pd.read_csv(r"C:\Users\salma\OneDrive\Documents\datasets\diabetes (1).csv")
    x = data.drop(columns='Outcome', axis=1)
    y = data['Outcome']
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=2)

    lr_c = LogisticRegression()
    lr_c.fit(x_train, y_train)

    val1 = float(request.GET['n1'])
    val2 = float(request.GET['n2'])
    val3 = float(request.GET['n3'])
    val4 = float(request.GET['n4'])
    val5 = float(request.GET['n5'])
    val6 = float(request.GET['n6'])
    val7 = float(request.GET['n7'])
    val8 = float(request.GET['n8'])

    input_data = np.array([val1, val2, val3, val4, val5, val6, val7, val8]).reshape(1, -1)

    pred = lr_c.predict(input_data)
    result1 = ""
    if pred == [1]:
        result1 = "Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                  " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    else:
        result1 = "Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                  " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                  " pour maintenir votre bien-être." \
                  "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "

    return render(request, "predictDiabete.html", {"result2": result1})


def resultAvc(request):
    data = pd.read_csv(r"C:\Users\salma\OneDrive\Documents\datasets\healthcare-dataset-stroke-data.csv")
    # replacer les valeurs abérantes avec la moyenne de bmi
    data["bmi"] = data["bmi"].apply(lambda x: data.bmi.mean() if x > 50 else x)
    # remplaer les valeur null de la colonne bmi par la moyenne .
    data.bmi.replace(to_replace=np.nan, value=data.bmi.mean(), inplace=True)
    # numero de 'other' est petit,on va convertir la valeur on 'Male'
    data['sexe'] = data['sexe'].replace('Other', 'Male')
    data.replace({'sexe': {'Male': 1, 'Female': 0}}, inplace=True)
    data.replace({'ever_married': {'No': 0, 'Yes': 1}}, inplace=True)
    data.replace({'Residence_type': {'Rural': 0, 'Urban': 1}}, inplace=True)
    data.replace({'smoking_status': {'Unknown': 0, 'never smoked': 1, 'formerly smoked': 2, 'smokes': 3}}, inplace=True)
    data.replace({'work_type': {'Private': 0, 'Self-employed': 1, 'children': 2, 'Govt_job': 3, 'Never_worked': 4}},
                 inplace=True)
    data['age'] = data['age'].astype(int)

    # definition de x et y
    data.drop(columns='id', inplace=True)
    x = data.drop(['stroke'], axis=1)
    y = data['stroke']
    # creation de dataset split pour la  prediction
    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    # LogisticRegression
    rf_c = RandomForestClassifier(n_estimators=100, criterion='entropy')
    rf_c.fit(x_train, y_train)
    rf_c.feature_names_ = None

    val1 = float(request.GET['n1'])
    val2 = float(request.GET['n2'])
    val3 = float(request.GET['n3'])
    val4 = float(request.GET['n4'])
    val5 = float(request.GET['n5'])
    val6 = float(request.GET['n6'])
    val7 = float(request.GET['n7'])
    val8 = float(request.GET['n8'])
    val9 = float(request.GET['n9'])
    val10 = float(request.GET['n10'])

    input_data = np.array([val1, val2, val3, val4, val5, val6, val7, val8, val9,val10]).reshape(1, -1)

    pred = rf_c.predict(input_data)
    result1 = ""
    if pred == [1]:
        result1 = "Je suis désolé(e) de devoir vous dire que les résultats indiquent que vous êtes malade. Il est crucial que vous ayez une idée claire de cette maladie spécifique," \
                  " mais surtout, il est essentiel de consulter un médecin dès que possible pour vous  proposer un plan de traitement adapté à votre situation . Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    else:
        result1 = "Je suis heureux de vous informer que les résultats indiquent que vous ne présentez pas de signes de maladie. C'est une excellente nouvelle et cela suggère que votre état de santé est favorable." \
                  " Cependant, il est toujours important de continuer à surveiller votre santé régulièrement et de prendre des mesures préventives" \
                  " pour maintenir votre bien-être." \
                  "Si vous avez d'autres questions ou préoccupations, n'hésitez pas à les poser a notre chatbot Si non Pour obtenir plus d'informations détaillées sur les maladies cardiovasculaires," \
                  " veuillez cliquer sur le lien suivant "
    return render(request, "predictAvc.html", {"resultan": result1})