# Newspaper Site

A full-featured online newspaper platform built with Django 6.0 for creating, editing, publishing, and viewing news articles.

## Features

### 1. User Authentication (15 Marks)
- **User Registration** with email verification
  - Users receive a verification email after registration
  - Accounts are activated only after clicking the verification link
- **Login/Logout System** with email-based authentication
- **User Profiles** for both subscribers (viewers) and editors
- Two user types:
  - **Viewers/Subscribers**: Can browse the site and rate articles
  - **Editors/Admins**: Can create, edit, and publish articles

### 2. Admin Dashboard - Article Management (15 Marks)
- **Create Articles**: Editors can create new news articles
- **Edit Articles**: Modify existing articles
- **Delete Articles**: Remove articles from the system
- **Article Fields**:
  - Headline
  - Body (full content)
  - Category
  - Publishing Time
  - Featured Image
  - Status (Draft/Published/Archived)
  - Featured flag
  - Breaking news flag
- **Categories**: Latest, Politics, Crime, Opinion, Business, Sports, Entertainment, Jobs, Tech

### 3. User Ratings for Articles (10 Marks)
- Viewers can rate articles from 0 to 4
- **Average Rating** displayed for each article
- **Email Notification** sent to users after providing ratings
- Users can update their existing ratings

### 4. Homepage (10 Marks)
- Articles display **headline** and **first 50 characters** of the body
- Featured articles section
- Breaking news ticker
- Paginated article listing

### 5. Category Page (10 Marks)
- Articles display **headline** and **first 150 characters** of the body
- Articles **sorted by ratings** (highest rated first)
- Category tabs for easy navigation
- Paginated listing

### 6. Article Details Page (10 Marks)
- Full **headline and complete body** content
- **2 Related articles** from the same category shown below
- Social sharing buttons
- Rating system integrated
- View count displayed

### 7. Premium Subscription Placeholder
- Premium subscription UI placeholder
- Database fields ready for future payment integration
- Premium badge display for premium users

### 8. Deployment Ready
- Production-ready settings with environment variables
- Static files handling with WhiteNoise
- PostgreSQL support via dj-database-url
- Procfile for Heroku/Railway deployment
- Security settings for production

## Installation

### Prerequisites
- Python 3.12+
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   cd Newspaper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate virtual environment**
   - Windows: `env\Scripts\activate`
   - macOS/Linux: `source env/bin/activate`

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Seed categories**
   ```bash
   python manage.py seed_categories
   ```

7. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the site**
    - Homepage: http://127.0.0.1:8000/
    - Admin Panel: http://127.0.0.1:8000/admin/

## Default Test Credentials
- **Admin Email**: admin@newspaper.com
- **Password**: admin123

## Project Structure

```
Newspaper/
├── accounts/           # User authentication app
│   ├── models.py      # CustomUser, EmailVerificationToken
│   ├── views.py       # Register, Login, Logout, Profile
│   ├── forms.py       # Registration, Login, Profile forms
│   └── urls.py        # Authentication URLs
├── articles/          # Articles management app
│   ├── models.py      # Category, Article, Rating
│   ├── views.py       # Homepage, Category, Detail, Dashboard
│   ├── forms.py       # Article, Category, Rating forms
│   ├── urls.py        # Article URLs
│   └── management/    # Custom management commands
├── templates/         # HTML templates
│   ├── base.html      # Base template
│   ├── accounts/      # Auth templates
│   └── articles/      # Article templates
├── static/            # Static files (CSS, JS)
├── media/             # User uploaded files
├── newspaper/         # Project settings
├── requirements.txt   # Python dependencies
├── Procfile          # Deployment configuration
└── runtime.txt       # Python version for deployment
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@host:port/dbname
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Deployment

### Heroku

1. Create Heroku app
2. Set environment variables in Heroku dashboard
3. Add PostgreSQL addon
4. Push to Heroku

```bash
heroku create your-app-name
heroku config:set DJANGO_SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py seed_categories
```

### Railway

1. Connect GitHub repository
2. Set environment variables
3. Railway will auto-detect Django and deploy

## Features Summary

| Feature | Implementation |
|---------|---------------|
| User Registration | ✅ Email verification |
| User Login/Logout | ✅ Email-based auth |
| User Profiles | ✅ Viewer & Editor profiles |
| Article CRUD | ✅ Create, Edit, Delete |
| Categories | ✅ 9 default categories |
| Article Ratings | ✅ 0-4 scale with comments |
| Email on Rating | ✅ Confirmation email |
| Homepage | ✅ 50 chars truncation |
| Category Page | ✅ 150 chars, sorted by rating |
| Article Detail | ✅ Full content + 2 related |
| Premium Placeholder | ✅ UI ready |
| Deployment | ✅ Heroku/Railway ready |

## Technologies Used

- **Backend**: Django 6.0
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Static Files**: WhiteNoise
- **Email**: Django Email Backend

## License

This project is created for educational purposes.

## Author

Built with Django 6.0.3