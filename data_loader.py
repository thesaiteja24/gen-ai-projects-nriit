import pandas as pd
from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection details and default password from environment variables
MONGO_URI = os.environ.get('MONGO_URI_2')
DEFAULT_PASSWORD = os.environ.get('PASSWORD')

# Step 1: Read the CSV file
d = pd.read_csv('./data.csv')

# Step 2: Establish a connection with MongoDB
client = MongoClient(MONGO_URI)

# Step 3: Access the desired database and collection
db = client['gen-ai-projects']  # Replace with your database name if different
collection = db['students']  # Replace 'students' with your collection name

# Step 4: Clear the collection
collection.delete_many({})
print("All existing data has been deleted from the collection.")

# Step 5: Hash the default password
hashed_password = bcrypt.hashpw(
    DEFAULT_PASSWORD.encode('utf-8'), bcrypt.gensalt())

# Step 6: Insert data from CSV into MongoDB
for _, row in d.iterrows():
    # Create a document for MongoDB
    document = {
        # Ensure column names match your CSV file
        "student_id": row['student_id'],
        # Ensure column names match your CSV file
        "fullname": row['fullname'],
        # Store the hashed default password
        "password": hashed_password.decode('utf-8'),
    }
    # Insert the document into the collection
    collection.insert_one(document)
    print(f"Inserted: {document}")

print("All data from the CSV file has been successfully inserted into MongoDB.")
