
```
# 🐦 Twitter Sentiment Analysis Dashboard

A Flask-based web application that analyzes the sentiment of tweets in real-time using **Hugging Face Transformers** and **Tweepy**, with results visualized in an interactive dashboard.

---

## 🚀 Features
- 🔐 **Twitter OAuth 2.0 Authentication**
- 📡 **Real-time Tweet Fetching** using Tweepy
- 🤖 **Sentiment Analysis** powered by Hugging Face Transformers
- 📊 **Interactive Charts** for sentiment distribution and trends
- 🎥 **Animated Background Video** for a modern UI
- 🗄 **MongoDB Integration** to store tweet data

---

## 🛠 Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, Chart.js
- **Database:** MongoDB
- **APIs & Libraries:** Tweepy, Transformers, dotenv, PapaParse

---

## 📂 Project Structure
```

├── static/               # CSS, JS, video background
├── templates/            # HTML templates
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation

````

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Aniketdhankar/Trend-analysis-using-X-twitter.git
cd Trend-analysis-using-X-twitter
````

### 2️⃣ Create a Virtual Environment & Install Dependencies

```bash
python -m venv venv
source venv/bin/activate    # On Mac/Linux
venv\Scripts\activate       # On Windows

pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables

Create a `.env` file in the root directory and add:

```
API_KEY=your_twitter_api_key
API_SECRET=your_twitter_api_secret
BEARER_TOKEN=your_twitter_bearer_token
ACCESS_TOKEN=your_twitter_access_token
ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
MONGO_URI=your_mongodb_connection_string
```

### 4️⃣ Run the Application

```bash
flask run
```

Open your browser at **`http://127.0.0.1:5000/`**.

---

## 📸 Screenshots
<img width="1918" height="985" alt="Screenshot 2025-08-15 114446" src="https://github.com/user-attachments/assets/ec2adfaf-c453-41b4-a0f7-67b05fa40638" />

<img width="1891" height="951" alt="Screenshot 2025-08-15 114649" src="https://github.com/user-attachments/assets/3abf2eae-89fb-4f2d-ae75-c23ad613c94a" />

<img width="1508" height="280" alt="Screenshot 2025-08-15 114918" src="https://github.com/user-attachments/assets/4902f17e-ba35-4a57-93ab-17cfc001d970" />

---

## 🌟 Future Improvements

* 📅 Historical sentiment tracking
* 🔍 Advanced search filters
* 📌 Export sentiment reports as PDF

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---



Made with ❤️ by **Aniket Singh Dhankar**


