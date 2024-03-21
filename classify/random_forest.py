import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load the data form the json file
df = pd.read_json('top_level_RR_reviews.json')

# Instantiate the binarizer
mlb = MultiLabelBinarizer()

# Fit and transform the 'categories' column
df = df.join(pd.DataFrame(mlb.fit_transform(df.pop('categories')),
                          columns=mlb.classes_,
                          index=df.index))

vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(df.text)
y = df[mlb.classes_]

# Configure RandomForestClassifier with the best parameters
optimized_rf = RandomForestClassifier(
    n_estimators=200,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features='sqrt',
    max_depth=40,
    random_state=42
)

# Wrap the optimized RandomForestClassifier with MultiOutputClassifier
optimized_ovr_rf = MultiOutputClassifier(optimized_rf, n_jobs=-1)

# Fit the model
optimized_ovr_rf.fit(X, y)

# Save the model
joblib.dump(optimized_ovr_rf, 'models/random_forest_model.pkl')
joblib.dump(vectorizer, 'models/vectorizer.pkl')

# # Make predictions
# text = "the cholesterol affinities of many integral plasma membrane proteins have been estimated by molecular computation. however, these values lack experimental confirmation. we therefore developed a simple mathematical model to extract sterol affinity constants and stoichiometries from published isotherms for the dependence of the activity of such proteins on membrane cholesterol concentration. the binding curves for these proteins are sigmoidal with strongly-lagged thresholds attributable to competition for the cholesterol by bilayer phospholipids. the model provided isotherms that matched the experimental data using published values for the sterol association constants and stoichiometries of the phospholipids. three oligomeric transporters were found to bind cholesterol without cooperativity with dimensionless association constants of 35 for kir3.4* and 100 for both kir2 and a gat transporter. (the corresponding {rho}g{degrees} values were -8.8, -11.4 and -11.4 kj/mol, respectively.) these association constants are significantly lower than those for the phospholipids which range from [~]100 to 6,000. the bk channel, the nicotinic acetylcholine receptor and the m192i mutant of kir3.4* appear to bind multiple cholesterol molecules cooperatively (n = 2 or 4) with subunit affinities of 563, 950 and 700, respectively. the model predicts that the three less avid transporters are approximately half-saturated in their native plasma membranes; hence, sensitive to variations in cholesterol in vivo. the more avid proteins would be nearly saturated in vivo. the method can be applied to any integral protein or other ligand in any bilayer for which there are reasonable estimates of the sterol affinities and stoichiometries of the phospholipids."
# predictions = optimized_ovr_rf.predict(vectorizer.transform([text]))
# print(predictions)


