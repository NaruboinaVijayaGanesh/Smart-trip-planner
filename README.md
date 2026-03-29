
# ✈️ AI Trip Planner

## 📌 Overview

AI Trip Planner is an intelligent travel planning system that automates itinerary generation, budget estimation, and booking management. It uses Machine Learning and real-time data to provide users with accurate, efficient, and personalized travel plans.

---

## 🚀 Features

* 🧭 Automatic day-wise itinerary generation
* 💰 Budget prediction using Machine Learning (Random Forest)
* 🍽️ Food cost estimation
* 🌦️ Real-time weather updates
* 🏨 Hotel recommendations
* 🔄 Dynamic itinerary regeneration
* 📍 Multi-destination trip planning
* 👤 User authentication and profile management
* 🧾 Booking and payment tracking

---

## 🧠 Machine Learning

The system uses a **Random Forest Regressor** for budget prediction.

* Handles both categorical and numerical data
* Uses **OneHotEncoder** for feature transformation
* Built using **Scikit-learn Pipeline**
* Model is trained on travel dataset
* Saved and loaded using **Joblib**

---

## 🛠️ Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Flask)
* **Database:** SQLite / MySQL
* **ML Libraries:** Scikit-learn, Pandas, NumPy
* **APIs:** Weather API, Maps API
* **Tools:** VS Code, Jupyter Notebook

---

## 📂 Project Structure

```id="7f9d0g"
AI-Trip-Planner/
│── app/
│── ml/
│   │── ml_model.py
│   │── food_model.py
│── data/
│   │── budget_dataset.csv
│── templates/
│── static/
│── config.py
│── run.py
```

---

## ⚙️ Installation

1. Clone the repository

```id="9d0lfi"
git clone https://github.com/your-username/ai-trip-planner.git
```

2. Navigate to project folder

```id="kp5d8y"
cd ai-trip-planner
```

3. Install dependencies

```id="r2l1bf"
pip install -r requirements.txt
```

4. Run the application

```id="x2c8sh"
python run.py
```

---

## ▶️ Usage

* Register or Login
* Enter travel details (destination, days, people, travel mode)
* Generate itinerary
* View predicted budget and food cost
* Modify itinerary if needed
* Book and manage trips

---

## 📊 Future Scope

* Advanced AI-based recommendations
* Mobile app development
* More accurate prediction models
* Integration with more travel services

---

## 📚 References

* Machine Learning with Scikit-learn
* Flask Documentation
* Travel and Weather APIs

---
