import pandas as pd
import joblib
import csv
import json
from datetime import datetime

# Load the model and vectorizer
model = joblib.load('models/random_forest_model.pkl')
vectorizer = joblib.load('models/vectorizer.pkl')

def predict(text, model, vectorizer):
    # Preprocess the text
    text = vectorizer.transform([text])
    # Make predictions
    predictions = model.predict(text)
    
    # Map probabilities to category labels
    categories = ['Biological and Chemical Sciences',
                  'Biomedical Sciences',
                  'General',
                  'Genetics/Genomics/Epigenetics',
                  'Humanities/Social Sciences', 
                  'Immunology',
                  'Medical Sciences'  
                  'Molecular and Cell Biology',
                  'Pathology/Laboratory Medicine',
                  'Physical Sciences',
                  'Physical Sciences & Engineering',
                  'Public Health',
                  'Virology']
    
    prediction = dict(zip(categories, predictions[0]))
    return prediction

# Initialize dictionaries to store results for each team
team1_results = []
team2_results = []
team3_results = []

def classify_team(prediction, link, date, title, authors, abstract):
    # Create a CSV file for each team, columns are Link/DOI,Publication Date,Title,Authors,Abstract
    # team1_file = open('results/team1_results.csv', 'w', newline='', encoding='utf-8')
    # team1_writer = csv.writer(team1_file)
    # team1_writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])
    # team2_file = open('results/team2_results.csv', 'w', newline='', encoding='utf-8')
    # team2_writer = csv.writer(team2_file)
    # team2_writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])
    # team3_file = open('results/team3_results.csv', 'w', newline='', encoding='utf-8')
    # team3_writer = csv.writer(team3_file)
    # team3_writer.writerow(['Link/DOI', 'Publication Date', 'Title', 'Authors', 'Abstract'])

    team1_categories = ['Public Health', 'Humanities/Social Sciences', 'General']
    team2_categories = ['Medical Sciences', 'Immunology', 'Virology', 'Pathology/Laboratory Medicine', 'Biomedical Sciences', 'Biological and Chemical Sciences', 'Genetics/Genomics/Epigenetics']
    team3_categories = ['Biological and Chemical Sciences', 'Physical Sciences & Engineering', 'Molecular and Cell Biology', 'Pathology/Laboratory Medicine', 'Genetics/Genomics/Epigenetics', 'Physical Sciences']

    # Add results to corresponding list based on prediction
    if any(prediction.get(category) for category in team1_categories):
        team1_results.append([link, date, title, authors, abstract])
    if any(prediction.get(category) for category in team2_categories):
        team2_results.append([link, date, title, authors, abstract])
    if any(prediction.get(category) for category in team3_categories):
        team3_results.append([link, date, title, authors, abstract])
    
    print("Classified: ", title, " by ", authors, " on ", date, " with link ", link)

# Load and combine data
df = pd.concat([
    pd.read_csv('results/biorxiv_results.csv'),
    pd.read_csv('results/chemrxiv_results.csv'),
    pd.read_csv('results/medrxiv_results.csv')
    # pd.read_csv('results/arxiv_results.csv'),
    # pd.read_csv('results/nber_results.csv'),
    # pd.read_csv('results/psyarxiv_results.csv')
], ignore_index=True)
# Replace NaN values in the 'Abstract' column with empty strings
df['Abstract'] = df['Abstract'].fillna('')


# Classify each abstract
for index, row in df.iterrows():
    prediction = predict(row['Abstract'], model, vectorizer)
    classify_team(prediction, row['Link/DOI'], row['Publication Date'], row['Title'], row['Authors'], row['Abstract'])

# Function to sort data by date and write to JSON
def sort_and_write_to_json(file_name, data):
    # Convert each row into a dictionary and ensure the date is in a sortable format
    formatted_data = [
        {
            'Link/DOI': row[0],
            'Publication Date': datetime.strptime(row[1], '%Y-%m-%d'), # Assuming the date format is 'YYYY-MM-DD'
            'Title': row[2],
            'Authors': row[3],
            'Abstract': row[4]
        } for row in data
    ]
    
    # Sort the data by 'Publication Date'
    sorted_data = sorted(formatted_data, key=lambda x: x['Publication Date'], reverse=True)
    
    # Convert the sorted data to JSON
    json_data = json.dumps(sorted_data, default=str) # Using default=str to handle datetime objects
    
    # Write the JSON data to a file
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(json_data)

# Convert and write each team's results to a JSON file
sort_and_write_to_json('results/team1_results.json', team1_results)
sort_and_write_to_json('results/team2_results.json', team2_results)
sort_and_write_to_json('results/team3_results.json', team3_results)

print("Results for each team have been sorted by date and converted to JSON format.")

print("Classification complete!")
