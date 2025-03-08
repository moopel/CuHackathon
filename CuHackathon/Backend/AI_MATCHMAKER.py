import pandas as pd
import tensorflow as tf
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import sys
import random

sys.stdout.reconfigure(encoding='utf-8')

# helper fucntions
def parse_data():
    data = pd.read_csv('assets/Superheroes.csv', encoding='utf-8')

    #print("Columns after reading CSV:", data.columns)

    numerical_features = ['Combat', 'Durability', 'Intelligence', 'Power', 'Strength', 'Speed']
    for feature in numerical_features:
        data[feature] = pd.to_numeric(data[feature], errors='coerce')

    data[numerical_features] = data[numerical_features].fillna(data[numerical_features].mean())

    scaler = StandardScaler()
    data[numerical_features] = scaler.fit_transform(data[numerical_features])

    label_encoder = LabelEncoder()
    data['Alignment'] = label_encoder.fit_transform(data['Alignment'])
    data['Creator'] = label_encoder.fit_transform(data['Creator'])

    #print("Columns before encoding 'Character':", data.columns)

    categorical_features = ['Character']
    if 'Character' in data.columns:
        encoder = OneHotEncoder(sparse_output=False)
        encoded_features = encoder.fit_transform(data[categorical_features])

        encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out(categorical_features))
        data = pd.concat([data, encoded_df], axis=1)
        #print("Columns after encoding 'Character':", data.columns)
    else:
        print("Character column not found in data")

    return data

def process_batch(embedding_model, data_batch):#new function for chuncking
    embeddings = embedding_model.predict(data_batch)
    return tf.math.l2_normalize(embeddings, axis=1).numpy()


def initialize_ai():
    data = parse_data()

    feature_weights = {
    "Combat": 1.2,
    "Durability": 0.8,
    "Intelligence": 1.5,
    "Power": 1.1,
    "Strength": 1.0,
    "Speed": 1.0
    }

    # Apply weights to numerical features
    for feature, weight in feature_weights.items():
        if feature in data.columns:
            data[feature] *= weight

        if 'Character' in data.columns:
            data1 = data.drop(columns=['Character'])
        else:
            print("Character column not found in data")
            return

    embedding_model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32)  # Embedding size
    ])

    heroes_data = data1[data1['Alignment'] == 3]
    villain_data = data1[data1['Alignment'] == 2]

    if heroes_data.empty or villain_data.empty:
        print("No heroes or villains found in the data")
        return

    # Ensure we only select numeric columns and handle empty data gracefully
    heroes_data = heroes_data.select_dtypes(include=[np.number])
    villains_data = villain_data.select_dtypes(include=[np.number])

    if heroes_data.empty or villains_data.empty:
        print("Heroes or Villains data is empty after filtering for numeric columns")
        return

    # Sample a smaller batch for heroes and villains
    #heroes_data = heroes_data.sample(n=100)
    #villains_data = villains_data.sample(n=100)

    heroes_array = heroes_data.drop(columns=['Alignment'], errors='ignore').to_numpy(dtype=np.float32)
    villains_array = villains_data.drop(columns=['Alignment'], errors='ignore').to_numpy(dtype=np.float32)

    print("Shape of heroes_array:", heroes_array.shape)
    print("Shape of villains_array:", villains_array.shape)

    #heroes_data = heroes_data.sample(n=100)
    #villains_data = villains_data.sample(n=100)

    chunk_size = 100
    hero_embeddings = []
    villain_embeddings = []

    for i in range(0, len(heroes_array), chunk_size):
        hero_batch = heroes_array[i:i + chunk_size]
        hero_embeddings.append(process_batch(embedding_model, hero_batch))

    for i in range(0, len(villains_array), chunk_size):
        villain_batch = villains_array[i:i + chunk_size]
        villain_embeddings.append(process_batch(embedding_model, villain_batch))

    hero_embeddings = np.vstack(hero_embeddings)
    villain_embeddings = np.vstack(villain_embeddings)

    #embeddings_hero = tf.math.l2_normalize(embedding_model.predict(heroes_array), axis=1).numpy()
    #embeddings_villain = tf.math.l2_normalize(embedding_model.predict(villains_array), axis=1).numpy()

    hero_embeddings = np.vstack(hero_embeddings)
    villain_embeddings = np.vstack(villain_embeddings)

    # Compute cosine similarity with TensorFlow
    #similarities = tf.matmul(hero_embeddings, villain_embeddings, transpose_b=True).numpy()

    similarities = np.zeros((len(hero_embeddings), len(villain_embeddings)), dtype=np.float32)

    for i in range(0, len(hero_embeddings), 100):
        hero_batch = hero_embeddings[i:i+100]
        batch_similarities = tf.matmul(hero_batch, villain_embeddings, transpose_b=True).numpy()
        similarities[i:i+100] = batch_similarities

    top_k = 5  # Adjust as needed
    best_match_indices = np.argpartition(-similarities, kth=top_k, axis=0)[:top_k]

    print("Best match indices (sorted):", best_match_indices)
    print("Sorted cosine similarities:", similarities[best_match_indices])

    hero_list = []

    for i in range(min(3, len(best_match_indices))):
        hero_idx = best_match_indices[i][0]

        if hero_idx < 0 or hero_idx >= len(heroes_data):
            print(f'Index {hero_idx} out of bounds')
            continue

        hero_name = data.iloc[heroes_data.index[hero_idx]]['Character']

        if hero_name not in hero_list:
            hero_list.append(hero_name)

    print(f"The best heroes to fight are: {hero_list}")

def generate_villain():
    data = parse_data()
    villain_data = data[data['Alignment'] == 2]

    random_index = random.choice(villain_data.index)
    
    # Access the 'Alignment' value of the selected villain
    return str(villain_data.loc[random_index, 'Character'])

    
def return_villain_list():
    data = parse_data()

    villain_data = data[data['Alignment'] == 2]

    return villain_data['Character']
    
print(f"{generate_villain()}")
    
# Function which takes name of character as argument and returns that character's data
def get_character_from_name(name_of_character):
    data = parse_data() # get data

    # get character data by filtering by heroes / villain & the specified name
    char_data = data[data['Character'] == name_of_character]

    if char_data.empty: # if no character found with name, return error
        return f"No character found with the name {name_of_character}"
    else:
        return char_data

    