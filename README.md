# Job Application Tracker

This project is a job application tracker that I built for my COP4751 course. It helps users keep track of companies, jobs, applications, and contacts in one place. It also includes a Job Match feature that compares user skills to job requirements and shows a match percentage.

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS

## Features

- Dashboard with summary statistics
- CRUD for companies
- CRUD for jobs
- CRUD for applications
- CRUD for contacts
- Job Match feature
- Basic form validation
- Sample data included in `schema.sql`

## Project Files

- `app.py` - main Flask application
- `database.py` - database connection and query helpers
- `schema.sql` - creates the database and tables
- `templates/` - HTML pages
- `static/style.css` - CSS styling
- `README.md` - setup instructions
- `AI_USAGE.md` - AI usage documentation
- `requirements.txt` - Python dependencies

## How to Set Up the Project

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd job_tracker
```

### 2. Install dependencies

Make sure Python and MySQL are installed first.

Then run:

```bash
pip install -r requirements.txt
```

If that does not work, try:

```bash
pip3 install -r requirements.txt
```

### 3. Set your MySQL connection

Open the `database.py` file and update the database connection with your MySQL information.

Example:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "job_tracker",
}
```

If the class uses a shared password from the professor, replace the password with that value.

### 4. Create the database

Open MySQL Workbench and run the `schema.sql` file.

You can also run:

```bash
mysql -u root -p < schema.sql
```

Then enter your MySQL password when prompted.

This will:
- create the `job_tracker` database
- create all 4 tables
- insert sample data

### 5. Run the Flask app

In the project folder, run:

```bash
python app.py
```

If that does not work, try:

```bash
python3 app.py
```

### 6. Open the project in your browser

Go to:

```text
http://127.0.0.1:5000
```

## Notes

- Make sure MySQL is running before starting the app.
- The database name must be `job_tracker`.
- The `requirements` field in jobs stores JSON data.
- The `interview_data` field in applications stores JSON data.
- If a company is deleted, related jobs and contacts may also be deleted because of foreign key relationships.

## Job Match Feature

On the Job Match page, enter skills in a comma-separated format such as:

```text
Python, SQL, Flask
```

The app compares those skills with the job requirements stored in the database and shows a match percentage for each job.

## Submission Files Included

This project includes:
- `app.py`
- `database.py`
- `schema.sql`
- `templates/`
- `static/`
- `README.md`
- `AI_USAGE.md`
- `requirements.txt`

## Author

Laura Vasquez  
COP4751 Course Project
