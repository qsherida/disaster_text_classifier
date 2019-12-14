import sys

import nltk
import pickle
import pandas as pd
import numpy as np
# db connection 
from sqlalchemy import create_engine
# text processing
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
# pipeline and feature tranformation
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
# classifiers
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
# testing
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, f1_score
from sklearn.datasets import make_multilabel_classification

# nltk downloads
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')



def load_data(database_filepath):
    """Function that returns data from sqlite db for model training.
    Args:
        database_filepath (str): path to sqlite db
    Returns:
        X ([str]): numpy array with disaster messages
        Y ([[bool]]): 2d numpy array with message labels
    """
    # load data from database
    try:
        conn = create_engine(database_filepath)
    except Exception as e:
        print(f'''The following exception occured while trying to make a sqlite db connection: {e}''')
        
    df = pd.read_sql('SELECT * FROM InsertTableName', conn)
    
    # retrieve features and lables from df 
    X = df['message'].values 
    Y = df.drop(['id', 'original', 'message','genre'], axis =1)
    
    # drop any labels with no occurences
    Y=Y.drop('child_alone', axis=1).values
    Y.sum(axis=0)
    
    return X, Y


def tokenize(text):
    """Function that tokenizes and lemmatizes sentiences
    Args:
        text (str): disaster text message
    Returns 
        tokens ([str]): np array of text tokens
    """
    tokens = word_tokenize(text.lower().strip())
    lemmatizer = WordNetLemmatizer()
    tokens = list(lemmatizer.lemmatize(w) for w in tokens if w not in stopwords.words("english") and w.isalpha())
    return tokens
    


def build_model():
    """Function that build classifier ml pipeline
    Args:
        None
    Returns
        pipeline (Pipeline): sklearn ml pipeline for multioutput multiclass classigfication
    """
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer = tokenize)),
        ('tfidf', TfidfTransformer()),
        ('mclsf', MultiOutputClassifier(estimator=RandomForestClassifier()))
    ])
    
    return pipeline



def evaluate_model(model, X_test, Y_test, category_names):
    """Function that evaluates model on test data printing f1 score for each label
    Args:
        model (estimator): sklearn multiclass multi output classifier
        X_test ([[int]]): 2d np array with test data
        Y_test ([[bool]]): 2d np array of test labels 
        category_names
    Returns:
        None
    """
    #fit model and make predictions on X_test
    model.fit(X_train, y=Y_train)
    Y_pred = pipeline.predict(X_test)

    # evaluate f1 score for each label
    for i in range(len(category_names)):
        pred_label = Y_pred[:,i]
        test_label = Y_test[:,i]
        label_f1 = f1_score(y_true = test_label, y_pred = pred_label)
        report = classification_report(y_true = test_label, y_pred = pred_label)
        print(report)
        
        

def save_model(model, model_filepath):
    """Function that saves model as a pickle file
    Args:
        model (estimator): fitted sklearn estimator"
        model_filepath (str): relative file path for saving model
    Returns:
        None
    """
    # save the model to disk
    pickle.dump(pipeline, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()
