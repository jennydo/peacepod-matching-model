# -*- coding: utf-8 -*-
"""Matching Model Testing.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12LxWBWUILsfw3Yd14jNkRiJp3IenGAAl
"""

pip install pymongo

pip install Flask

import pandas as pd
from pymongo import MongoClient
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

from collections import defaultdict
import random
from datetime import datetime, timedelta

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
# Retrieve interests and chatMatchedUsers from users and add to matchUsers
match_users_df = pd.merge(match_users, users[['_id', 'interests', 'chatMatchedUsers']], left_on='userId', right_on='_id', how='left')

print(match_users_df)


# Extract five elements from the 'interests' column of matchUsers
for i in range(5):
    column_name = f'interest{i+1}'
    match_users_df[column_name] = match_users_df['interests'].map(
        lambda interests: interests[i]
    )

print(match_users_df)

# Preprocessing
interests_feature = [f'interest{i+1}' for i in range(5)]
categorical_features = ['ageRange', 'coreValue', 'feeling', 'gratefulFor', 'motivation', 'practice'] + interests_feature
categorical_transformer = OneHotEncoder()  # transform categorical features into a numerical format
preprocessor = ColumnTransformer(
    transformers=[
        ('columnTransformer', categorical_transformer, categorical_features)
    ])

# Create a pipeline that includes scaling and k-means clustering
# read more about StandardScaler: https://poe.com/s/aHkYpxG4bfmSzuQ27o9w
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('scaler', StandardScaler(with_mean=False)),
    ('kmeans', KMeans(n_clusters=3, random_state=42, n_init=10))
])

# Fit the pipeline to the user data
pipeline.fit(match_users_df)

# Get the cluster labels
match_users_df['cluster'] = pipeline.named_steps['kmeans'].labels_
print(match_users_df)

# Function to pair users within each cluster
def pair_users_within_clusters(df):
    cluster_groups = df.groupby('cluster') # groups df by the column 'cluster'
    pairings = defaultdict(list) # dict to store pairs of users within each cluster

    for cluster, group in cluster_groups:
        users = list(group.to_dict(orient='records')) # converts the group data into a list of dictionaries where each dictionary represents a user within the cluster.
        random.shuffle(users)  # Shuffle to randomize pairings

        while users:
            user = users.pop()
            user_id = user['userId']
            user_matched = False

            for potential_match in users: # Iterate through the remaining users to find a potential match
                potential_match_id = potential_match['userId']

                # Check if the users have not been previously matched
                if potential_match_id not in user.get('chatMatchedUsers', []) and user_id not in potential_match.get('chatMatchedUsers', []):
                    pairings[user_id] = potential_match_id
                    pairings[potential_match_id] = user_id

                    # Update the users in the database (simulated here as updating the local data)
                    match_users_collection.update_one(
                        {'_id': user_id},
                        {'$push': {'chatMatchedUsers': potential_match_id}}
                    )
                    match_users_collection.update_one(
                        {'_id': potential_match_id},
                        {'$push': {'chatMatchedUsers': user_id}}
                    )

                    users.remove(potential_match)
                    user_matched = True
                    break

            if not user_matched:
                pairings[user_id] = None  # No valid pair found for this user

    return pairings

# Execute pairing function
pairings = pair_users_within_clusters(match_users_df)

# Print the pairings
for user, paired_user in pairings.items():
    print(f"User {user} paired with {paired_user}")

# Using flask to make an api
# import necessary libraries and functions
from flask import Flask, jsonify, request

# creating the flask app
app = Flask(__name__)

@app.route('/matchPairs', methods=['GET'])
def get_match_pairs():
    return jsonify(pairings)

@app.route('/matchPairs', methods=['POST'])
def add_match_pair():
    data = request.get_json()
    if 'key' in data and 'value' in data:
        pairings[data['key']] = data['value']
        return jsonify({"message": "Pair added successfully"}), 201
    else:
        return jsonify({"error": "Invalid data"}), 400


# driver function
if __name__ == '__main__':
    app.run(debug=True)