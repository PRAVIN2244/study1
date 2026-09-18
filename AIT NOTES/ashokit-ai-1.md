==================================
What is Artificial Intelligence?
==================================
** Artificial Intelligence is a branch of Data Science and Computer Science.
** AI aims to create machines or systems that can think and act like humans.
** AI is used to create intelligent machines and intelligent software systems.
** AI means making computers perform tasks that normally require human intelligence.**
########## AI Real-Life Examples ##########
** Artificial Intelligence is used in many real-time applications, such as:
1. Self-driving cars
2. Fraud detection systems in banks
3. Spam detection in emails
4. ChatGPT answering questions and generating images
5. GitHub Copilot generating code
6. Voice assistants like Siri, Alexa, and Google Assistant
7. Product recommendations in Amazon and Flipkart
8. Movie recommendations in Netflix and YouTube
===========================
What is Machine Learning?
===========================
** Machine Learning is a subset of Artificial Intelligence.
** Machine Learning allows computers to learn patterns from data without writing programs 
explicitly for every condition.
## Simple Definition
**Machine Learning is a technique where the computer learns from data and makes predictions or 
decisions.**
### Traditional Programming:
Input + Rules -> Output
### Machine Learning:
Input + Output Data -> Learning Algorithm -> Model New Input -> Trained Model -> Prediction
## Example
===> Suppose we want to calculate whether a student will pass.
if attendance > 75 and marks > 40: 
PASS 
else: FAIL
Here, we manually create the rules.
** In Machine Learning, we provide historical student data:
--- Hours studied
--- Attendance
--- Preious Marks
--- Assignments reports
** The algorithm learns patterns from the historical data.
New Student Data ---> ML Model --> PASS/FAIL
=======================
Why Machine Learning? 
=======================
** Traditional software requires developers to define rules.
** For some problems, rules are very difficult to define.
Example:
Spam Email Detection
It is difficult to write rules such as:
if email contains "offer" or "buy back":
    spam
**  instead of writing these conditions manually, we can provide historical emails for ML 
algorithm then it will learn patterns from the data and it can identify SPAM emails easily.
============================
Types of Machine Learning
============================
1) Supervised learning
2) Unsupervised learning
3) Reinforcement learning
======================
Supervised Learning
======================
=> In supervised learning, the training data contains both:
input + Correct Output
Example:
Student Information -> Pass/Fail 
House Features -> House Price 
Email -> Spam/Not Spam
** The inputs are called FEATURES.
** The output is called the TARGET.
=> Supervised learning is mainly divided into:
1) Regression
2) Classification
** Regression is used when the target is a continuous numerical value.
Ex: house price, salary, temperature, sales, revenue, stock price prediction
** Classification is used when the output belongs to a category.
Ex: spam or not spam, pass or fail, Fradu or Not Fraud, Disease or No Diesase
========================
Unsupervised Learning
========================
** In unsupervised learning, we do not have a target/output column.
** The algorithm tries to discover patterns or groups in the data.
Example:
Customer data:
Age
Income
Spending Score
The algorithm may discover:
Group 1 -> Low spending customers 
Group 2 -> Medium spending customers 
Group 3 -> High spending customers
=========================
Reinforcement Learning
=========================
** In Reinforcement Learning, an agent/model learns by interacting with an environment.
** The agent performs an action and receives:
Reward or Penalty
** A Reward is feedback given to the agent after it performs an action.
** A Penalty is negative feedback to the agent / model.
===========================
Machine Learning Workflow
===========================
1) Understand business problem
2) Collect Data
3) Understand Data
4) Clean Data
5) EDA (Exploratory Data Analsyis)
6) Feature Engineering (Data Transformation)
7) Train and Test Split (Seperate training data 80% and testing data 20%)
8) Pre Processing (convert data into numerical format 0 and 1)
9) Select Algorithm
10) Train Model
11) Make Predictions
12) Evaluate Model
13) Tune Model
14) Save model (ex : house_price_model.pkl)
15) Deploy Model
==========================
Important ML terminology
==========================
###### 1) Data Set ######
=> Collection of data used for analysis and used for training & testing
Ex: 
=> Below is the students data set
Study hours
Attendance
Previous marks
Result (Pass or Fail)
Syntax : 
import pandas as pd
df = pd.read_csv("students.csv")
=> Here dataset is the complete table
    Features = Study Hours, Attendance, Previous marks
    Target = Result
=> Features are input variables used by the Machine Learning model.
=> Target is the value that we want the model to predict.
    Features = Area, Bedrooms, Age
    Target = Price
=> In Dataset, X represents input values and Y represents Output values

############ 2) Training Data and Testing data ############
=> We should not train and test the model using the same data.
=> Why because the model could simply memorize the data.
=> We divide data into 80 - 20 formula
Training data 80%
Testing data 20%
Example:
Dataset = 1000 records
800 records -> Training
200 records -> Testing
=> The model learns patterns from the training data.

############ 3) random_state  ############
=> When we split the dataset, records are randomly selected.
=> If we execute the program multiple times, the split can change.
random_state = 10
Note : The important point is that we use a fixed value for reproducibility.

explanation:
random_state controls randomness in machine learning tasks such as splitting data into training and testing sets.
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=10
)
When you split data, train_test_split() randomly chooses records for train and test datasets.
Without random_state:
train_test_split(X, y, test_size=0.2)
Each execution may select different records. Therefore, model accuracy can also change.
With a fixed random_state:
train_test_split(X, y, test_size=0.2, random_state=10)
The same records are selected every time you run the program.
random_state = 10

Run 1 → Same train/test split
Run 2 → Same train/test split
Run 3 → Same train/test split
The number 10 has no special meaning. You can use 1, 42, 100, or any fixed integer. The important point is using the same value when you want reproducible results.

suppose has a file with 100 records of students
then how it works

Suppose your student file has 100 records.
from sklearn.model_selection import train_test_split

X = student_data[["marks", "attendance", "study_hours"]]
y = student_data["result"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=10
)
Here:
Total records = 100

test_size = 0.2

Test records = 20
Training records = 80
random_state=10 first creates a fixed random order of the 100 student records. From that order:
80 records → Training data
20 records → Testing data
For example:
Training student IDs:
[7, 15, 42, 3, 89, ...]  → 80 students

Testing student IDs:
[10, 56, 91, 24, 68, ...] → 20 students
Every time you run the same code using random_state=10, the same 80 students go to training and the same 20 students go to testing.
If you change it:
random_state=20
a different—but still repeatable—set of 80 training and 20 testing student records is chosen.

############ 4) Data Preprocessing ############
=> Real-world data is usually not clean.
Examples : 
    1) Missing Values
    2) Duplicate Records
    3) Incorrect Values
Therefore, we need preprocessing.
############ 5) Mean vs Median ############
Mean = sum_of_values / total_num_of_values
Median = Middle value after sorting the data
############ 6) Categorical Data ############
=> Machine Learning algorithms generally require numerical inputs.
Example:
Gender
Male
Female
=> We can convert categorical data into numerical representation.
############ 7) Encoding ############
Label Encoding
    Low ----> 0
    Medium ---> 1
    High ----> 2
=================
ML Algorithms
=================
** Regression : It is used when we want to predict continuous numeric value
Ex :
1) House Price Prediction
2) Salary Prediction
3) Sales Prediction
4) Temperature Prediction
5) Stock Price Prediction
6) Revenue Prediction

** Common Regression Algorithms
1) Linear Regression
2) Multiple Linear Regression
3) Polynomial Regression
4) Decision Tree Regression
5) Random Forest Regression
6) Support Vector Regression (SVR)

** Classification : It is used when we want to predict a category
Ex:
1) Spam Detection
2) Disease Detection
3) Fraud Detection
4) Loan Approval
5) Sentiment Analysis
6) Image Classification
7) Student Pass/Fail prediction

** Common Classification Algorithms
1) Logistic
2) Decision Tree Classifier
3) Random Forest Classifier
4) Support Vector Machine (SVM)
5) KNN (Nearest Neighbors)
6) Niave Bayes

==============================================================
Assignment 1: Develop an ML Model using Linear Regression
==============================================================
 Objective: 
Build a Machine Learning model using Linear Regression to predict a continuous numerical value 
based on one or more input features.

Suggested Project:
House Price Prediction using Linear Regression
Develop a model that predicts the price of a house based on features such as:
** Area / Square Feet
** Number of Bedrooms
** Number of Bathrooms
** Number of Floors
** Age of House
** Location-related features
Tasks: 
1) Understand the business problem.
2) Collect or download a suitable dataset.
3) Load the dataset using Pandas.
4) Perform basic data understanding:
head()
shape
info()
describe()
Check missing values
5) Perform Exploratory Data Analysis (EDA).
6) Identify:
Independent variables (X)
Dependent/Target variable (y)
7) Handle missing values and unnecessary columns.
8) Split the dataset into:
80% Training
20% Testing
9) Build a Linear Regression model using Scikit-learn.
10) Train the model using the training data.
11) Make predictions on the test data.
12) Evaluate the model using:

MAE
MSE
RMSE
RÂ² Score
13) Compare Actual vs Predicted values.
14) Visualize the regression results.
15) Test the model with new/unseen input data.
16) Write a short conclusion about model performance.
ðŸ’» Technologies
** Python
** NumPy
** Pandas
** Matplotlib
** Seaborn
** Scikit-learn
===================================
Step 1: Install Required Libraries
===================================
numpy
pandas 
matplotlib 
seaborn 
scikit-learn
==========================================
Step-2 : Create Data set (dataset.csv)
==========================================
area,bedrooms,bathrooms,age,price
1000,2,2,10,5000000
1200,2,2,8,6000000
1500,3,2,7,7500000
1800,3,3,5,9000000
2000,4,3,6,10000000
2200,4,3,4,11000000
2500,4,4,3,13000000
2800,5,4,2,15000000
3000,5,4,1,17000000
3500,5,5,1,20000000
=============================================
Step-3 : create main.py and implement logic
=============================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression
df = pd.read_csv("dataset.csv")
print(df)
# Understand data
print(df.head())
print(df.tail())
print(df.shape)
print(df.columns)
print(df.info())
print(df.describe())
# check missing values
print(df.isnull().sum())
# Check Duplicate records
print(df.duplicated().sum())
df = df.drop_duplicates()
print(df)
# Create EDA (understanding relationships between our features and house price.)
plt.figure(figsize=(8,5))
plt.scatter(df["area"], df["price"])
plt.xlabel("area")
plt.ylabel("price")
plt.title("Area vs House Price")
# plt.show()
# Define independent and dependent variables
# x = input and y = output
x = df[["area", "bedrooms", "bathrooms", "age"]]
y = df["price"]
# Split DataSet (80-20 formula)
x_train, x_test, y_train, y_test = train_test_split(x,
                                                    y,
                                                    test_size=0.2,
                                                    random_state=42
                                                )
# check train and test data frame shapes
print("X_Train:", x_train.shape)
print("X_Test:", x_test.shape)
print("Y_Train:", y_train.shape)
print("Y_Test:", y_test.shape)
# Create model
model = LinearRegression()
# Model Training
model.fit(x_train, y_train)

# Make Predications
y_predict = model.predict(x_test)
print(y_predict)
df = pd.DataFrame({
    "Actual Price": y_test,
    "Predicted Price": y_predict
})
print(df)
# Test with new data
new_house = pd.DataFrame({
    "area": [5000],
    "bedrooms": [7],
    "bathrooms": [7],
    "age": [1]
})
predicted_price = model.predict(new_house)
print("Predicated House Price : ", predicted_price)
## save model
with open("house_price_model.pkl", "wb") as file:
    pickle.dump(model, file)
print("*********** Model Saved to Pickle file ************")    

Step-4: Create app.py and implement UI logic for Model Demo purpose.
import streamlit as st
import pandas as pd
import pickle


# Load trained model
with open("house_price_model.pkl", "rb") as file:
    model = pickle.load(file)


# Streamlit page configuration
st.set_page_config(
    page_title="House Price Prediction",
    page_icon="🏠",
    layout="centered"
)


# Title
st.title("🏠 House Price Prediction")
st.write("Enter the house details below to predict the price.")


# Input fields
area = st.number_input(
    "Area (Square Feet)",
    min_value=100,
    max_value=10000,
    value=2000,
    step=100
)

bedrooms = st.number_input(
    "Number of Bedrooms",
    min_value=1,
    max_value=20,
    value=3,
    step=1
)

bathrooms = st.number_input(
    "Number of Bathrooms",
    min_value=1,
    max_value=20,
    value=2,
    step=1
)

age = st.number_input(
    "House Age (Years)",
    min_value=0,
    max_value=100,
    value=5,
    step=1
)


if st.button("Predict Price"):

    # Create DataFrame
    new_house = pd.DataFrame({
        "area": [area],
        "bedrooms": [bedrooms],
        "bathrooms": [bathrooms],
        "age": [age]
    })

    # Make prediction
    predicted_price = model.predict(new_house)

    # Display result
    st.success(
        f"Predicted House Price: ₹{predicted_price[0]:,.2f}"
    )


# Footer
st.markdown("---")
st.write("Machine Learning Model: Linear Regression")
Run the Streamlit application:
streamlit run app.py
Summary

1) Created project and installed required libraries
2) Created dataset (.csv file)
3) Loaded dataset using Pandas
4) Performed basic data-understanding operations
5) Performed data cleaning
6) Performed EDA
7) Data pre-processing (features and target)
8) Train and test split (80 - 20)
9) Created model (LinearRegression)
10) Model training
11) Model predictions
12) Model saved as a Pickle file (.pkl)
13) Streamlit UI page creation
14) Loaded the model from pickle file
15) Took inputs from the user and sent them for model prediction
16) Displayed the result in the UI page

Explanation:

This project trains a Linear Regression model to predict a house price from:
- area
- bedrooms
- bathrooms
- age
The project has three main files:
dataset.csv                → House data
main.py                    → Train and save the ML model
house_price_model.pkl      → Saved trained model
app.py                     → Streamlit user interface
1. Dataset
dataset.csv
area,bedrooms,bathrooms,age,price
1000,2,2,10,5000000
1200,2,2,8,6000000
1500,3,2,7,7500000
1800,3,3,5,9000000
2000,4,3,6,10000000
2200,4,3,4,11000000
2500,4,4,3,13000000
2800,5,4,2,15000000
3000,5,4,1,17000000
3500,5,5,1,20000000
Each row represents one house.
area       → House size in square feet
bedrooms   → Number of bedrooms
bathrooms  → Number of bathrooms
age        → Age of the house in years
price      → House price; this is what the model predicts
2. main.py — complete explained code
# NumPy is useful for numerical operations.
import numpy as np

# Pandas is used to read and work with CSV data.
import pandas as pd

# Matplotlib and Seaborn are used to create charts.
import matplotlib.pyplot as plt
import seaborn as sns

# Pickle saves the trained model into a file.
import pickle

# train_test_split divides data into training and testing data.
from sklearn.model_selection import train_test_split

# LinearRegression is the machine learning algorithm.
from sklearn.linear_model import LinearRegression

# Metrics are used to evaluate the model.
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# Read the CSV file and store it in a DataFrame.
df = pd.read_csv("dataset.csv")

print(df)

#    area  bedrooms  bathrooms  age     price
# 0  1000         2          2   10   5000000
# 1  1200         2          2    8   6000000
# 2  1500         3          2    7   7500000
# ...
# 9  3500         5          5    1  20000000
pd.read_csv() reads dataset.csv and converts it into a Pandas DataFrame.
# Show the first five records.
print(df.head())

# Show the last five records.
print(df.tail())

# Show the number of rows and columns.
print(df.shape)
# (10, 5)

# Show all column names.
print(df.columns)
# Index(['area', 'bedrooms', 'bathrooms', 'age', 'price'], dtype='object')

# Show DataFrame details: rows, columns, data types, and non-null values.
df.info()

# Show statistics for numeric columns.
print(df.describe())
df.shape returns:
(10, 5)

10 rows    → 10 houses
5 columns  → area, bedrooms, bathrooms, age, price
Use df.info() directly. Avoid this:
print(df.info())
Because df.info() already prints details, and print() adds an extra None.
# Check missing values in every column.
print(df.isnull().sum())

# area         0
# bedrooms     0
# bathrooms    0
# age          0
# price        0
# dtype: int64
This confirms that the dataset has no missing values.
# Count duplicate rows.
print(df.duplicated().sum())

# 0
# Remove duplicate rows, if any exist.
df = df.drop_duplicates()
Even though the result is 0 here, this is a good cleaning step for real-world datasets.
# Create a scatter plot to understand the relationship
# between area and house price.
plt.figure(figsize=(8, 5))

plt.scatter(df["area"], df["price"])

plt.xlabel("Area")
plt.ylabel("Price")
plt.title("Area vs House Price")

plt.show()
This graph helps us see whether larger houses generally have higher prices. In this dataset, the house price increases as area increases.
# X contains input columns, also called independent variables or features.
X = df[["area", "bedrooms", "bathrooms", "age"]]

# y contains the output column, also called the target variable.
y = df["price"]
X → Features used to predict price
y → Actual house price
# Split the data into 80% training data and 20% testing data.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)
Total records    → 10
Training records → 8
Testing records  → 2
random_state=42 fixes the random split. Therefore, the same records will be selected for training and testing every time the code runs.
print("X_train:", X_train.shape)
# X_train: (8, 4)

print("X_test:", X_test.shape)
# X_test: (2, 4)

print("y_train:", y_train.shape)
# y_train: (8,)

print("y_test:", y_test.shape)
# y_test: (2,)
# Create an empty Linear Regression model.
model = LinearRegression()
At this stage, the model does not know anything about the house data.
# Train the model using training data.
model.fit(X_train, y_train)
During training, the model learns the relationship between features and price:
area, bedrooms, bathrooms, age → price
# Predict prices for the testing records.
y_pred = model.predict(X_test)

print(y_pred)
# Example output: [predicted_price_1 predicted_price_2]
The predicted values can differ from actual values because the model learns only from the 8 training records.
# Create a comparison table.
# to_numpy() avoids index-alignment issues.
comparison_df = pd.DataFrame({
    "Actual Price": y_test.to_numpy(),
    "Predicted Price": y_pred
})

print(comparison_df)
Example format:
   Actual Price  Predicted Price
0      17000000     16500000.00
1       6000000      6200000.00
The exact prediction values depend on the trained model.
# Calculate model evaluation values.
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print("MAE:", mae)
print("MSE:", mse)
print("RMSE:", rmse)
print("R2 Score:", r2)
MAE  → Average prediction error in rupees
MSE  → Squared error; large errors receive more penalty
RMSE → Error in the same unit as price
R²   → How well the model explains the price variation
For R²:
1.0  → Perfect prediction
0.0  → Model is no better than a simple baseline
< 0  → Model performs poorly
With only 10 records, evaluation values may not be reliable. A real project should use many more house records.
# Create a new, unseen house record.
new_house = pd.DataFrame({
    "area": [5000],
    "bedrooms": [7],
    "bathrooms": [7],
    "age": [1]
})

# Predict the price of the new house.
predicted_price = model.predict(new_house)

print("Predicted House Price:", predicted_price[0])
# Example: Predicted House Price: 28000000.0
The model has never seen this exact house before. It uses the relationship learned during training to estimate its price.
# Save the trained model in a Pickle file.
with open("house_price_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("Model saved to Pickle file.")
# Model saved to Pickle file.
"wb" → Write Binary mode
pickle.dump() → Saves the trained model
house_price_model.pkl → Saved model file
3. app.py — Streamlit interface
import streamlit as st
import pandas as pd
import pickle
# Load the saved model.
with open("house_price_model.pkl", "rb") as file:
    model = pickle.load(file)
"rb" → Read Binary mode
pickle.load() → Loads the saved trained model
This lets the UI predict prices without training the model again.
st.set_page_config(
    page_title="House Price Prediction",
    page_icon="🏠",
    layout="centered"
)
This configures the browser tab title, icon, and layout.
st.title("🏠 House Price Prediction")

st.write("Enter the house details below to predict the price.")
This displays a heading and instruction in the Streamlit page.
area = st.number_input(
    "Area (Square Feet)",
    min_value=100,
    max_value=10000,
    value=2000,
    step=100
)
This creates an input field for house area.
min_value → Smallest allowed value
max_value → Largest allowed value
value     → Default value
step      → Increase/decrease amount
The fields for bedrooms, bathrooms, and age work the same way.
if st.button("Predict Price"):
The prediction code inside this block runs only when the user clicks the Predict Price button.
    new_house = pd.DataFrame({
        "area": [area],
        "bedrooms": [bedrooms],
        "bathrooms": [bathrooms],
        "age": [age]
    })
The square brackets are important:
"area": [area]
A DataFrame requires column values as a list. This creates one row, matching the format used to train the model.
    predicted_price = model.predict(new_house)
The model receives the new house data and returns the predicted price.
    st.success(
        f"Predicted House Price: ₹{predicted_price[0]:,.2f}"
    )
Example output in Streamlit:
Predicted House Price: ₹28,000,000.00
st.markdown("---")
st.write("Machine Learning Model: Linear Regression")
This creates a horizontal line and footer text.
4. Run the project
First train and save the model:
python main.py
Then start the Streamlit UI:
streamlit run app.py
The browser normally opens this page:
http://localhost:8501


--------------------------------

ASSIGNMENT 2
Loan Approval Prediction Using Classification

Objective:
Build, train, evaluate, and test a classification model that predicts whether a loan application is likely to be Approved or Rejected.

Business Problem:
A bank receives loan applications from customers. Use historical application data to predict whether a new application will be Approved or Rejected.

Input Features:

- Gender
- Married
- Dependents
- Education
- Self Employed
- Applicant Income
- Coapplicant Income
- Loan Amount / Loan Term
- Credit History / Property Area

Target:

Loan Status
Y = Approved
N = Rejected

Recommended Algorithm:

Primary Algorithm:
Logistic Regression — implement this as the main classification model.

Optional comparison:
Decision Tree or Random Forest.

Technology Stack:

- Python
- NumPy
- Pandas
- Matplotlib
- Seaborn
- Scikit-learn

Project Flow:

Loan Data → Preprocessing → Classification Model → Approved / Rejected

Assignment Tasks:

1) Understand the business problem.
2) Collect or download a suitable Loan Approval dataset.
3) Load the dataset using Pandas.
4) Perform data understanding using head(), shape, info(), describe(), and missing-value checks.
5) Perform EDA for income, loan amount, credit history, education, property area, and target distribution.
6) Identify independent variables X and target y = Loan_Status.
7) Handle missing values.
8) Remove identifiers or irrelevant columns.
9) Encode categorical data into numerical form.
10) Split data: 80% training and 20% testing.
11) Build a LogisticRegression() model.
12) Train the model using training data.
13) Predict Approved or Rejected for test applications.
14) Calculate Accuracy, Precision, Recall, F1-Score, and create a Confusion Matrix.
15) Create visualizations for target distribution, feature relationships, and confusion matrix.
16) Create a new applicant record and predict Approved or Rejected.
17) Write a conclusion with performance, observations, limitations, and improvements.

EDA and Data Understanding:

head()         → First records
shape          → Rows and columns
info()         → Columns and data types
describe()     → Numerical summary
Missing values → Identify and handle null values

Recommended Visualizations:

Loan Status                 → Count plot / Bar chart
Applicant Income            → Histogram
Loan Amount                 → Histogram / Box plot
Credit History vs Status    → Count plot
Numerical relationships     → Correlation heatmap

Classification Metrics:

Accuracy         → Overall correct predictions
Precision        → Correct approved predictions among all predicted approvals
Recall           → Correctly identified actual approvals
F1-Score         → Balance between precision and recall
Confusion Matrix → Correct and incorrect classification counts

New Loan Application Example:

Gender             → Male
Married            → Yes
Dependents         → 0
Education          → Graduate
Applicant Income   → ₹50,000
Loan Amount        → ₹2,00,000
Credit History     → 1
Property Area      → Urban

Prediction Flow:

New Applicant → Trained Model → Loan Approved / Rejected

Important:

This is an educational project only. Real lending systems require fairness, explainability, regulatory compliance, and human oversight.

Student Challenge:

Be ready to explain:

- Why is this a classification problem?
- Why is Logistic Regression suitable?
- What does Credit History contribute?

Goal:

Explain the project from:

Business Problem → Data → Preprocessing → Model → Prediction → Evaluation

D:\AIT NOTES\loan-approval-classification

Created the complete one-file ML project structure.
- [main.py](D:\Data Science\loan-approval-classification\main.py)
- [loan_approval_dataset.csv](D:\Data Science\loan-approval-classification\loan_approval_dataset.csv)
- [requirements.txt](D:\Data Science\loan-approval-classification\requirements.txt)
- [README.md](D:\Data Science\loan-approval-classification\README.md)
The README includes setup steps, expected command outputs using #, metric explanations, code-section explanations, and conclusion guidance.
Run:
cd "D:\Data Science\loan-approval-classification"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
main.py passed syntax validation. After installing libraries and running it, it creates loan_approval_model.pkl and a charts folder.


