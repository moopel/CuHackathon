import pandas as pd
import tensorflow as tf
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import random

def parse_data():
    data = pd.read_csv('assets/Superheroes.csv')

    # Print the columns of the DataFrame to check if 'Character' exists
    print("Columns after reading CSV:", data.columns)

    # Ensure the columns contain only numeric data
    numerical_features = ['Combat', 'Durability', 'Intelligence', 'Power', 'Strength', 'Speed']
    for feature in numerical_features:
        data[feature] = pd.to_numeric(data[feature], errors='coerce')  # Convert columns to numeric, coercing errors to NaN

    # Handle missing values (e.g., fill with the mean of the column)
    data[numerical_features] = data[numerical_features].fillna(data[numerical_features].mean())  # Fill NaN values with the mean of each column

    scaler = StandardScaler()  # Initialize the StandardScaler
    data[numerical_features] = scaler.fit_transform(data[numerical_features])  # Scale the numerical features

    # Encode 'Alignment' and 'Creator' with LabelEncoder
    label_encoder = LabelEncoder()
    data['Alignment'] = label_encoder.fit_transform(data['Alignment'])  # Encode 'Alignment' with unique numerical values
    data['Creator'] = label_encoder.fit_transform(data['Creator'])  # Encode 'Creator' with unique numerical values

    # Print the columns of the DataFrame to check if 'Character' exists before encoding
    print("Columns before encoding 'Character':", data.columns)

    # Encode 'Character' with OneHotEncoder
    categorical_features = ['Character']
    if 'Character' in data.columns:
        encoder = OneHotEncoder(sparse_output=False)
        encoded_features = encoder.fit_transform(data[categorical_features])

        # Convert encoded features to DataFrame
        encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out(categorical_features))

        # Concatenate numerical, encoded categorical, and encoded 'Alignment' and 'Creator' features
        data = pd.concat([data, encoded_df], axis=1)
        print("Columns after encoding 'Character':", data.columns)
    else:
        print("Character column not found in data")

    return data

def initialize_ai():
    data = parse_data()
    
    # Check if 'Character' column exists before dropping
    if 'Character' in data.columns:
        data1 = data.drop(columns=['Character'])
    else:
        print("Character column not found in data")
        return

    # Define the model
    embedding_model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32)  # Embedding size
    ])

    # Separate heroes and villains
    heroes_data = data1[data1['Alignment'] == 3]
    villain_data = data1[data1['Alignment'] == 2]

    if heroes_data.empty or villain_data.empty:
        print("No heroes or villains found in the data")
        return

    # Ensure all columns are numeric before converting to NumPy array
    heroes_data = heroes_data.select_dtypes(include=[np.number])
    villains_data = villain_data.select_dtypes(include=[np.number])

    # Convert to NumPy arrays (ensuring float32)
    heroes_array = heroes_data.drop(columns=['Alignment']).to_numpy(dtype=np.float32)
    villains_array = villains_data.drop(columns=['Alignment']).to_numpy(dtype=np.float32)

    # Debugging: Print shapes and data types
    print("Shape of heroes_array:", heroes_array.shape)
    print("Data type of heroes_array:", heroes_array.dtype)
    print("Shape of villains_array:", villains_array.shape)
    print("Data type of villains_array:", villains_array.dtype)

    # Compute embeddings
    embeddings_hero = tf.math.l2_normalize(embedding_model.predict(heroes_array), axis=1)
    embeddings_villain = tf.math.l2_normalize(embedding_model.predict(villains_array), axis=1)

    embeddings_hero = tf.convert_to_tensor(embeddings_hero, dtype=tf.float32)
    embeddings_villain = tf.convert_to_tensor(embeddings_villain, dtype=tf.float32)

    # Compute cosine similarity
    similarities = cosine_similarity(embeddings_hero, embeddings_villain)

    # Find best hero for each villain
    best_match_indices = tf.argsort(cosine_similarity, direction='ASCENDING')

    sorted_distances = tf.gather(cosine_similarity, best_match_indices) # get the sorted matches

    print(f"Sorted Indicies: {sorted_distances.numpy()}")
    print(f"Sorted cosine similarities: {sorted_distances.numpy()}")

    # Ensure the index is within bounds
    if len(villain_data) > 10:
        villain_name = data.iloc[villain_data.index[10]]['Character']
    else:
        villain_name = data.iloc[villain_data.index[0]]['Character']

    hero_list = []
    count = 0

    for i in range(min(len(best_match_indices), 3)):
        hero_idx = best_match_indices[i]

        existing_heros = []

        if hero_idx < 0 or hero_idx >= len(heroes_data):
            print(f'Index out of bounds at {i}')
            count += 1
            continue



        hero_name = data.iloc[heroes_data.index[hero_idx]]['Character']

        if hero_name in hero_list:
            existing_heros.append(hero_name)
            continue

        if hero_name not in existing_heros:
            hero_list.append(hero_name)

    print(f"The best heroes to fight {villain_name} are {hero_list}")
    print(f"Number of out-of-bounds indices: {count}")

initialize_ai()