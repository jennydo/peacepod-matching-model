# pairing_model.py
import pandas as pd
from pymongo import MongoClient
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from collections import defaultdict
import random

# Connect to MongoDB
client = MongoClient('mongodb+srv://peacepod:peacepod@cluster0.cxattxq.mongodb.net/')
db = client['test']
match_users_collection = db['matchusers']
users_collection = db['users']

# Fetch data from MongoDB
match_users_cursor = match_users_collection.find()
match_users_data = list(match_users_cursor)

users_cursor = users_collection.find()
users_data = list(users_cursor)

# Convert MongoDB data to DataFrame
match_users = pd.DataFrame(match_users_data)
users = pd.DataFrame(users_data)

# Merging the DataFrames on 'user_id'
match_users_df = pd.merge(match_users, users[['_id', 'interests', 'chatMatchedUsers']], left_on='userId', right_on='_id', how='left')

# Extract five elements from the 'interests' column of matchUsers
for i in range(5):
    column_name = f'interest{i+1}'
    match_users_df[column_name] = match_users_df['interests'].map(
        lambda interests: interests[i]
    )

# Preprocessing
interests_feature = [f'interest{i+1}' for i in range(5)]
categorical_features = ['ageRange', 'coreValue', 'feeling', 'gratefulFor', 'motivation', 'practice'] + interests_feature
categorical_transformer = OneHotEncoder()  # transform categorical features into a numerical format
preprocessor = ColumnTransformer(
    transformers=[
        ('columnTransformer', categorical_transformer, categorical_features)
    ])

# Create a pipeline that includes scaling and k-means clustering
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('scaler', StandardScaler(with_mean=False)),
    ('kmeans', KMeans(n_clusters=3, random_state=42, n_init=10))
])

# Fit the pipeline to the user data
pipeline.fit(match_users_df)

# Get the cluster labels
match_users_df['cluster'] = pipeline.named_steps['kmeans'].labels_

# Function to pair users within each cluster
def pair_users_within_clusters(df):
    cluster_groups = df.groupby('cluster') # groups df by the column 'cluster'
    pairings = defaultdict(list) # dict to store pairs of users within each cluster

    for cluster, group in cluster_groups:
        users = list(group.to_dict(orient='records')) # converts the group data into a list of dictionaries where each dictionary represents a user within the cluster.
        random.shuffle(users)  # Shuffle to randomize pairings
        # print("NEW CLUSTER")

        while len(users) > 1:
            user = users.pop()
            user_id = user['userId']

            for potential_match in users: # Iterate through the remaining users to find a potential match
                potential_match_id = potential_match['userId']

                # Check if the users have not been previously matched
                if (str(potential_match_id) not in user['chatMatchedUsers'] and str(user_id) not in potential_match['chatMatchedUsers']):
                    pairings[str(user_id)] = str(potential_match_id)
                    pairings[str(potential_match_id)] = str(user_id)
                    # print("--> matched: " + user['username'] + " x " +  potential_match['username'])

                    # # Update the "chatMatchedUsers" field for users on MongoDB
                    # users_collection.update_one(
                    #     {'_id': user_id},
                    #     {'$push': {'chatMatchedUsers': str(potential_match_id)}}
                    # )
                    # users_collection.update_one(
                    #     {'_id': potential_match_id},
                    #     {'$push': {'chatMatchedUsers': str(user_id)}}
                    # )

                    users.remove(potential_match)

                    break

    return pairings

# Execute pairing function
pairings = pair_users_within_clusters(match_users_df)

# Function to get pairings
def get_pairings():
    return pairings