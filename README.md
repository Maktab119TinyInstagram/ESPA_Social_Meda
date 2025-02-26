# 🚀 ESPA Social Network Project

A modern and scalable social networking platform built with Django, PostgreSQL, and optimized database indexing. This project supports user authentication, media uploads, hashtags, likes, follows, and OTP-based authentication.

---

## 📌 Features

- **User Authentication**: Signup, login, logout, and password reset.
- **Soft Delete for Users**: Accounts can be deactivated and stored temporarily instead of being permanently removed.
- **OTP Authentication**: Custom OTP system using database storage, with automated cleanup for expired codes.
- **Post Management**: Users can create, edit, and manage posts.
- **Media Handling**: Upload multiple images/videos with size validation.
- **Hashtag System**: Unique hashtags that allow searching for related posts.
- **Likes & Dislikes**: Generic relation-based likes on posts and comments.
- **Following System**: Optimized with database indexing for efficient queries.
- **Optimized Database Queries**: Indexed fields for improved performance.

---

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript (to be expanded)
- **Styling**: Tailwind CSS / Bootstrap
- **Storage**: Cloud storage or local media files (configurable)

---

## 📂 Installation & Setup

### 🔧 Prerequisites
Ensure you have the following installed:
- Python 3.x
- PostgreSQL
- Pip & Virtual Environment

### 🏗️ Setup Steps

1️⃣ **Clone the Repository:**
```bash
git clone https://github.com/your-repo/social-network.git
cd social-network
```

2️⃣ **Create a Virtual Environment & Activate It:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3️⃣ **Install Dependencies:**
```bash
pip install -r requirements.txt
```

4️⃣ **Setup the Database:**
```bash
python manage.py migrate
```

5️⃣ **Run the Development Server:**
```bash
python manage.py runserver
```

6️⃣ **(Optional) Run Tests:**
```bash
python manage.py test
```

---

## 📜 API Endpoints

| Endpoint            | Method | Description                  |
|---------------------|--------|------------------------------|
| `/api/auth/login/`  | POST   | User login                   |
| `/api/auth/signup/` | POST   | User registration            |
| `/api/posts/`       | GET    | List all posts               |
| `/api/posts/<id>/`  | GET    | Retrieve a single post       |
| `/api/posts/create/` | POST  | Create a new post            |
| `/api/posts/<id>/like/` | POST | Like/unlike a post         |
| `/api/follow/<username>/` | POST | Follow/unfollow a user |

---

## ⚡ Contribution Guidelines

1. **Fork the repo** and create a feature branch.
2. Follow the **PEP8** coding style.
3. Submit a **pull request** with clear documentation.
4. Ensure all tests pass before requesting a merge.

---

## 📩 Contact
For any inquiries, feel free to reach out via [esmaeelzohari1382@gmail.com](mailto:esmaeelzohari1382@gmail.com).
