# Deep Learning

## What is Deep Learning?

- Deep Learning is a subset of Machine Learning.
- It uses artificial neural networks to learn from large amounts of data.
- Its algorithms are inspired by the human brain.
- It is particularly powerful for solving complex problems.

## Machine Learning vs Deep Learning

| Machine Learning | Deep Learning |
| --- | --- |
| A subset of Artificial Intelligence | A subset of Machine Learning |
| Learns from data using algorithms | Uses neural networks with many layers |
| Works well with small to medium datasets | Usually needs large amounts of data |
| Mostly works with structured data | Works well with images, audio, video, and text |
| Usually trains faster | Usually trains more slowly |
| Easier to understand and explain | Can be more accurate for complex problems |

## Real-life Examples

1. YouTube recommending videos you may like.
2. Google Photos recognizing a face.
3. ChatGPT understanding questions.
4. A self-driving car identifying a person, road, or vehicle.

These systems handle large amounts of data and identify complex patterns, which is where Deep Learning becomes important.

## Hierarchy

```text
Artificial Intelligence -> Machine Learning -> Deep Learning -> Neural Networks
```

## Why Do We Need Deep Learning?

For a cat-versus-dog image problem, traditional programming would require difficult manual rules:

```text
IF ears are like this
AND eyes are like this
AND nose is like this
AND body is like this
THEN CAT
ELSE DOG
```

With Deep Learning:

```text
Thousands of images -> Neural network -> Learns patterns -> Cat / Dog
```

The programmer does not manually define every rule. The neural network learns patterns from data.

## ML vs DL Workflow

```text
Machine Learning: Dataset -> Feature Engineering -> ML Algorithm -> Prediction
Deep Learning:    Dataset -> Neural Networks -> Automatically learn patterns -> Prediction
```

Traditional ML often depends heavily on manually selected features. Deep Learning can automatically learn useful representations from raw or less-processed data.

## Where is Deep Learning Used?

### Computer Vision

- Face recognition
- Object detection
- Medical image analysis
- Self-driving cars

### Natural Language Processing

- ChatGPT
- Language translation
- Text classification
- Sentiment analysis

### Recommendation Systems

- YouTube
- Netflix
- Amazon
- Spotify

### Speech

- Voice assistants
- Speech to text
- Voice recognition

### Generative AI

- Text generation
- Image generation
- Code generation
- Audio generation

## What is a Neural Network?

Deep Learning learns through neural networks. A neural network has multiple layers:

1. **Input layer**: receives input data.
2. **Hidden layer(s)**: learns patterns.
3. **Output layer**: produces the final prediction.

```text
  -> Input 
  -> Hidden Layer 1
  -> Hidden Layer 2
  -> Hidden Layer 3
  -> Output
```

Multiple hidden layers make a network *deep*. Therefore, Deep Learning is learning using deep, multi-layer neural networks.

## Deep Learning Model Execution Flow

```text
Input
  -> Neural Network
  -> Prediction
  -> Compare with actual value
  -> Calculate loss
  -> Backpropagation
  -> Update weights
  -> Train again
```

## Important Terminology

1. Deep Learning
2. Neural Network
3. Neuron
4. Weight
5. Bias
6. Activation Function
7. Loss Function
8. Backpropagation
9. Optimizer
10. Epoch

## Deep Learning Example: Cat or Dog

Given thousands of images, a Deep Learning model gradually learns patterns in this order:

```text
  -> Pixels
  -> Edges
  -> Shapes
  -> Eyes / Ears / Nose
  -> Face
  -> Cat or Dog
```

## Neural Network

A Neural Network is a computational model inspired by the structure of the human brain. It contains interconnected neurons arranged in layers.

```text
     -> Input Layer
     -> Hidden Layer
     -> Hidden Layer
     -> Output Layer
```

- **Input layer** receives input data.
- **Hidden layer(s)** learn patterns from input.
- **Output layer** produces the final prediction.

A neural network with multiple hidden layers is called a **Deep Neural Network**.

## Neuron

A neuron is the basic processing unit of a neural network: a small mathematical calculation unit. A neuron:

- Receives inputs
- Applies weights
- Adds bias
- Calculates a value
- Applies an activation function
- Produces output

```text
Output = Activation Function(Input *  Weight + Bias)
```

## Weight

A weight represents the importance of an input in a neural network.

Example: predicting whether a student will pass or fail.

| Input | Example weight |
| --- | ---: |
| Study hours | 0.8 |
| Attendance | 0.3 |
| Previous marks | 0.5 |

A higher weight generally means an input has a stronger influence on the neuron's calculation. Weights are learned from training data, not manually chosen by programmers.

```text
Random weights -> Prediction -> Calculate error -> Update weights -> Better prediction
```

## Bias

Bias is an additional value added to the weighted sum, helping the neural network adjust its prediction.

```text
Input = 5
Weight = 2
Weighted input = 5 * 2 = 10
Bias = 3
Result = 10 + 3 = 13
```

- **Weight** controls the importance of an input.
- **Bias** shifts or adjusts the result.

## Activation Function

An activation function determines whether and how strongly a neuron should be activated. It is applied after calculating the weighted sum plus bias.
"weighted sum + bias"
```text
Inputs -> Weights -> Weighted Sum -> Bias -> Activation Function -> Output
```
Inputs
   ↓
Weights
   ↓
Weighted Sum
   ↓
Bias
   ↓
Activation Function
   ↓
Output


** Some important ActivationFunctions are

    -- ReLu (Rectified Linear Unit) (convert negative values to 0)

    -- SigMoid (Provides output between 0 and 1)

    -- Tanh (can represent both negative and positive values)

    -- Softmax (converts multiple outputs into probabilities)

Ex : layers.Dense(128, activation="relu")


Note: Activation Function = Helps a neural network learn non-linear and complex patterns.


It acts as the decision or transformation function of a neuron.

## Loss Function

A loss function measures the difference between the actual output and the predicted output.

Example:

```text
Actual value = 100
Predicted value = 80
Difference = 100 - 80 = 20
```
# The difference
100 - 80 = 20

** Lower Loss = Better Prediction

** Higher Loss = Poor Prediction


Ex : loss="binary_crossentropy"


** Several Loss Function Names

1) categorical_crossentropy

2) binary_crossentropy

3) Mean Squared Error (mse)

4) Mean Absolute Error (Mae)

5) sparse_categorical_crossentropy

Note: Loss Function = Measures the difference between the actual value and the predicted value.  

If the actual answer is *Cat* and the model predicts *Dog*, the loss function measures how wrong the model was.

## Backpropagation

Backpropagation calculates how much each weight contributed to an error and using that information to improve the neural network.

1. Input data goes to the neural network.
2. The neural network makes a prediction.
3. The prediction is compared with the actual value to calculate loss.
4. Error information is propagated backward through the n etwork.
5. Gradients calculate how a small change in a weight affects the loss.
6. after calculating gradients, The optimizer updates the weights.

## Optimizer

An optimizer is an algorithm that updates weights and biases to reduce loss.

- Backpropagation calculates gradients.
- The optimizer uses gradients to update parameters.

Example:

```text
Current weight = 0.8
Gradient = 0.2
Learning rate = 0.1

New weight = Old weight - Learning rate * Gradient
New weight = 0.8 - (0.1 * 0.2)
New weight = 0.78
```

** The optimizer looks at the loss and decides how to adjust the weights to improve the model.

** Below are the some common optimizers we are having

1) Gradient Descent (basic optimizer to reduce the loss)

2) Adam (Adaptive Moment Estimation) (smart and fast)

3) SGD (Stochastic Gradient Descent) (batch by batch update)


** Gradient Descent is used to find the direction in which the loss decreases.

** Instead of calculating the gradient using the entire training dataset at once, SGD updates
   the weights using a smaller portion of the data (typically a batch).

** Adam is the most advanced optimizer. It automatically adjusts the learning rate for
   different weights based on information from previous gradients.

Ex :

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

## Epoch

An epoch is one complete pass through the entire training dataset.

For 10,000 training images:

- Processing all 10,000 images once = 1 epoch.
- Processing them twice = 2 epochs.
- Processing them three times = 3 epochs.

## Summary

A Neural Network takes inputs, combines them using weights and bias, applies activation functions to produce a prediction, calculates loss, uses backpropagation to calculate gradients, and uses an optimizer to update weights and reduce loss over multiple epochs.
-------------------
ANN : Artificial Neural Network ==> Good for structured data/tabular data

CNN : Convolutional Neural Network ==> Good for images

RNN : Recurrent Neural Network ==> Good for sequential data

LSTM : Long Short-Term Memory ==> Improved form of RNN

GRU : Gated Recurrent Unit

GNN : Graph Neural Network
--------------
## Assignment 1

**Develop a Deep Learning Model to predict whether a student will Pass or Fail.**


Assignment-1: Develop Deep Learning Model to Predict Student Pass or Fail
Objective
Develop a Deep Learning classification model using TensorFlow/Keras to predict whether a student will Pass or Fail based on the student's academic information.
Problem Statement
You are given a dataset containing student information such as:
- Study Hours
- Attendance
- Previous Marks
The objective is to develop and train a Deep Learning Neural Network that learns patterns from the given data and predicts the student's result as:
- 0 → Fail
- 1 → Pass
Requirements
1. Create or use a student dataset containing appropriate input features and the target variable.
2. Perform necessary data preprocessing.
3. Separate the dataset into:
   - Input features X
   - Target variable y
4. Split the dataset into training and testing data.
5. Develop a Deep Learning Neural Network using TensorFlow/Keras.
6. Compile the model using an appropriate:
   - Optimizer
   - Loss function
   - Evaluation metric
7. Train the model using the training data.
8. Evaluate the trained model using the test data.
9. Save the trained model to a file.
10. Create a simple Streamlit UI that:
    - Accepts student details from the user.
    - Loads the trained model.
    - Predicts whether the student will Pass or Fail.
    - Displays the prediction clearly.
Sample Input
Study Hours    : 7
Attendance     : 85
Previous Marks : 72
Expected Output
Prediction: PASS
Technologies to Use
- Python
- Pandas
- NumPy
- TensorFlow / Keras
- Scikit-learn
- Streamlit
Learning Outcomes
After completing this assignment, you should be able to:
- Understand Deep Learning classification.
- Build a basic Artificial Neural Network (ANN).
- Train a model using TensorFlow/Keras.
- Evaluate a classification model.
- Save and load a trained Deep Learning model.
- Integrate a Deep Learning model with Streamlit.
- Build a simple end-to-end Machine Learning application.

------------------------------
students.csv
study_hours,attendance,result
1,50,0
2,55,0
3,60,0
4,65,0
5,70,0
6,75,1
7,80,1
8,85,1
9,90,1
10,95,1

requirements.txt
numpy
pandas
tensorflow
scikit-learn
streamlit

main.py
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split


# ============================================================
# 1. Read CSV Dataset
# ============================================================

df = pd.read_csv("students.csv")

print(df)


# ============================================================
# 2. Separate Input and Output
# ============================================================

# Input features
X = df[["study_hours", "attendance"]]

# Target / Output
y = df["result"]

# Convert to NumPy Arrays
X = X.values
y = y.values


# ============================================================
# 3. Split Dataset into Training and Testing Data
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\n========= DATA SPLIT =========")
print("Training Data:", len(X_train))
print("Testing Data :", len(X_test))

# ============================================================
# 3.a Feature Scaling
# ============================================================

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Save scaler for future predictions
joblib.dump(scaler, "student_scaler.pkl")

print("\n========= DATA SCALING =========")
print("Training data scaled successfully")

# ============================================================
# 4. Create Neural Network
# ============================================================

model = tf.keras.Sequential([

    # Hidden Layer
    tf.keras.layers.Dense(
        4,
        activation="relu",
        input_shape=(2,)
    ),

    # Output Layer
    tf.keras.layers.Dense(
        1,
        activation="sigmoid"
    )
])

# ============================================================
# 5. Compile Model
# ============================================================

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)


# ============================================================
# 6. Display Model Structure
# ============================================================

print("\n========= MODEL STRUCTURE =========")

model.summary()


# ============================================================
# 7. Train Neural Network
# ============================================================

print("\n========= TRAINING =========")

model.fit(X_train, y_train, epochs=100, verbose=1)


# ============================================================
# 8. Evaluate Model
# ============================================================

print("\n========= MODEL EVALUATION =========")

loss, accuracy = model.evaluate(X_test, y_test, verbose=0)

print("Loss     :", loss)
print("Accuracy :", accuracy)


# ============================================================
# 9. Save Trained Model
# ============================================================

model.save("student_pass_fail_model.keras")

print("\n========= MODEL SAVED =========")
print("Model saved as: student_model.keras")


# ============================================================
# 10. Predict a New Student
# ============================================================

print("\n========= NEW STUDENT PREDICTION =========")

# Example:
# Study Hours = 8
# Attendance  = 85%

student = np.array([[8, 85]])

prediction = model.predict(student)

probability = prediction[0][0]

print("Study Hours :", student[0][0])
print("Attendance  :", student[0][1])
print("Probability :", probability)


# ============================================================
# 11. Convert Probability into PASS / FAIL
# ============================================================

if probability >= 0.5:
    print("Result     : PASS")
else:
    print("Result     : FAIL")

pass main.py file ask chat gpt to create streamlit ui for making dl prediction

Assignment-2: Develop Image Classification Model Using DL
Project Title
🐱🐶 Cat vs Dog Image Classification using TensorFlow and Streamlit
Assignment Question
Develop a Cat vs Dog Image Classification application using Python, TensorFlow/Keras, and Streamlit.
The application should be divided into two Python files:
1) Model Training — train_model.py
Create a Python program that:
- Loads the Cat and Dog image dataset from folders.
- Performs image preprocessing and normalization.
- Splits the dataset into training and validation datasets.
- Builds a CNN (Convolutional Neural Network) model using TensorFlow/Keras.
- Trains the model to classify images as Cat or Dog.
- Evaluates the model using validation data.
- Displays the model accuracy and loss.
- Saves the trained model as image_classifier.keras.
2) User Interface — app.py
Create a Streamlit web application that:
- Loads the saved image_classifier.keras model.
- Provides an option to upload a .jpg, .jpeg, or .png image.
- Displays the uploaded image.
- Preprocesses the uploaded image in the same way as the training images.
- Uses the trained CNN model to predict the image.
- Displays:
Predicted Class: Cat 🐱 / Dog 🐶
Prediction Confidence: Percentage


==================
What is Kaggle?
==================

** Kaggle is an online platform mainly used for Data Science, Machine Learning, and AI.

** Kaggle is very useful because it provides

1) Data Sets : ready-made datasets for ML projects

2) Models : pre-trained models and AI resources

3) Courses : beginner-friendly learning material

4) Community : students can see other people's notebooks and projects

5) Notebooks : run Python/ML code in the browser

===============
Kaggle Setup
===============

Step-1 : Create Kaggle account (free of cost)

Step-2 : Download Legacy API key (ex : kaggle.json)

Step-3 : keep this kaggle.json file in your machine (below location)

        Location : C://Users/<your-name>/.kaggle/kaggle.json


$ python -m pip install --upgrade kaggle

$ kaggle datasets list

$ kaggle datasets list --search dogs

$ kaggle datasets list --search ecommerce

requirements.txt
kagglehub

download_dataset.py — Example 1

import kagglehub

kagglehub.dataset_download(
    "shaunthesheep/microsoft-catsvsdogs-dataset"
)
print("DataSet Downloaded to : ")
print(path)

download_dataset.py — Example 2
import kagglehub

path = kagglehub.dataset_download(
    "harishvutukuri/dogs-vs-wolves"
)

print("DataSet Downloaded to : ")
print(path)

Output shown in the screenshot
Downloading to C:\Users\admin\.cache\kagglehub\datasets\harishvutukuri\dogs-vs-wolves\2.archive...
100% 222M/222M

Extracting files...

DataSet Downloaded to :
C:\Users\admin\.cache\kagglehub\datasets\harishvutukuri\dogs-vs-wolves\versions\2

assignement 2

-----------
requirements.txt

tensorflow
kagglehub
numpy
pandas
matplotlib
pillow
streamlit

------------------
main.py — Imports and Dataset Download
import kagglehub
import tensorflow as tf

from tensorflow.keras import layers, models


# ============================================================
# 1. DOWNLOAD DATASET
# ============================================================

path = kagglehub.dataset_download(
    "aleemaparakkatta/cats-and-dogs-mini-dataset"
)

print("Dataset downloaded to:")
print(path)


# ============================================================
# 2. Check DATASET PATH
# ============================================================

# Check the printed path and update this if necessary.
dataset_path = path

print("Dataset path:")
print(dataset_path)


# ============================================================
# 3. LOAD IMAGES (Train Test Split)
# ============================================================

img_height = 128
img_width = 128
batch_size = 32


```Approach 1 — Using validation_split
train_dataset = tf.keras.utils.image_dataset_from_directory(
    dataset_path,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size,
    shuffle=True,
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    dataset_path,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size
)```

Approach 2 — Load First, Then Split Manually
The later screenshots show an alternative version:
dataset = tf.keras.utils.image_dataset_from_directory(
    dataset_path,
    image_size=(img_height, img_width),
    batch_size=batch_size,
    shuffle=True,
    seed=123
)

train_size = int(0.8 * len(dataset))

print("Train Size : ", train_size)

train_dataset = dataset.take(train_size)
validation_dataset = dataset.skip(train_size)


# ============================================================
# 4. CHECK CLASSES
# ============================================================

print("Classes:")
print(train_dataset.class_names)

# ============================================================
# 5. CREATE CNN MODEL with Hidden Layers
# ============================================================

model = models.Sequential([

    # input image
    layers.Input(shape=(img_height, img_width, 3)),

    # Convert pixels from 0-255 to 0-1
    layers.Rescaling(1.0 / 255),

    # Create CNN Layer - 1
    layers.Conv2D(32, (3, 3), activation='relu'),

    layers.MaxPooling2D(),

    # Create CNN Layer - 2
    layers.Conv2D(64, (3, 3), activation='relu'),

    layers.MaxPooling2D(),

    # Convert features maps into one-dimensional data
    layers.Flatten(),

    # Fully Connected input layer with 64 neuron
    layers.Dense(64, activation='relu'),

    # Output Layer with Dense as 1 (Cat or Dog)
    layers.Dense(1, activation='sigmoid'),

])

# ============================================================
# 6. DISPLAY MODEL Summary
# ============================================================

model.summary()


# ============================================================
# 7. COMPILE MODEL (Optimizer + loss function + metrics)
# ============================================================

model.compile(
    optimizer='adam',
    loss="binary_crossentropy",
    metrics=["accuracy"]
)


# ============================================================
# 8. TRAIN MODEL (train_dataset, test_dataset, epochs)
# ============================================================

model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=5
)


# ============================================================
# 9. EVALUATE MODEL with validation_dataset (loss + accuracy)
# ============================================================

loss, accuracy = model.evaluate(validation_dataset)

print("Validation Accuracy : ", accuracy)


# ============================================================
# 10. SAVE MODEL as cat_dog_cnn.keras
# ============================================================

model.save("cat_do_cnn.keras")

print()
print("====================================")
print("Model saved successfully!")
print("File: cat_dog_cnn.keras")
print("====================================")


ask chat gpt to create app.py
pass main.py
create beautiful ui page for this model keep it it very simple
