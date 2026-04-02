import json
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error

from database import fetch_all, fetch_one, execute_query, to_json_text

app = Flask(__name__)
app.secret_key = "job_tracker_secret_key"

# Lists used for dropdown values/validation

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
APPLICATION_STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]


@app.context_processor
def inject_current_year():
    # Sends the current year to all templates for the footer
    return {"current_year": datetime.now().year}


def clean_text(value):
    return (value or "").strip()


def parse_int(value):
    value = clean_text(value)
    return int(value) if value else None


def parse_bool(value):
    return value in ["on", "true", "1", "yes"]


def split_skills(skills_text):
    skills = []
    for item in (skills_text or "").split(","):
        item = item.strip().lower()
        if item:
            skills.append(item)
    return skills


def parse_requirements_input(raw_value):
    raw_value = clean_text(raw_value)
    if not raw_value:
        return []

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "skills" in parsed and isinstance(parsed["skills"], list):
            return parsed["skills"]
        return [str(parsed)]
    except json.JSONDecodeError:
        return [item.strip() for item in raw_value.split(",") if item.strip()]


def parse_interview_input(raw_value):
    raw_value = clean_text(raw_value)
    if not raw_value:
        return {}

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except json.JSONDecodeError:
        return {"notes": raw_value}


def get_job_skills(requirements):
    if not requirements:
        return []

    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except json.JSONDecodeError:
            return [item.strip().lower() for item in requirements.split(",") if item.strip()]

    if isinstance(requirements, list):
        return [str(skill).strip().lower() for skill in requirements if str(skill).strip()]

    if isinstance(requirements, dict):
        skills = requirements.get("skills", [])
        if isinstance(skills, list):
            return [str(skill).strip().lower() for skill in skills if str(skill).strip()]

    return []


def format_requirements_text(requirements):
    skills = get_job_skills(requirements)
    return ", ".join(skills) if skills else "N/A"


# converts inteview JSON into text for display
def format_interview_text(interview_data):
    if not interview_data:
        return "N/A"

    if isinstance(interview_data, str):
        return interview_data

    try:
        return json.dumps(interview_data)
    except TypeError:
        return str(interview_data)


def calculate_job_matches(user_skills_text):
    user_skills = split_skills(user_skills_text)

    jobs = fetch_all(
        """
        SELECT j.job_id, j.job_title, j.requirements, c.company_name
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.company_id
        ORDER BY j.job_title ASC
        """
    )

    matches = []

    for job in jobs:
        job_skills = get_job_skills(job["requirements"])
        matched_skills = sorted(set(user_skills) & set(job_skills))
        missing_skills = sorted(set(job_skills) - set(user_skills))

        if user_skills:
            match_percentage = round((len(matched_skills) / len(user_skills)) * 100)
        else:
            match_percentage = 0

        matches.append(
            {
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "company_name": job["company_name"] or "No Company",
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "match_percentage": match_percentage,
            }
        )

    matches.sort(key=lambda item: (-item["match_percentage"], item["job_title"].lower()))
    return matches


@app.route("/")
# dashboard summary
def dashboard():
    stats = {
        "companies": fetch_one("SELECT COUNT(*) AS count FROM companies")["count"],
        "jobs": fetch_one("SELECT COUNT(*) AS count FROM jobs")["count"],
        "applications": fetch_one("SELECT COUNT(*) AS count FROM applications")["count"],
        "contacts": fetch_one("SELECT COUNT(*) AS count FROM contacts")["count"],
    }

    status_counts = fetch_all(
        """
        SELECT status, COUNT(*) AS total
        FROM applications
        GROUP BY status
        ORDER BY total DESC, status ASC
        """
    )

    recent_applications = fetch_all(
        """
        SELECT a.application_id, a.application_date, a.status, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        LIMIT 5
        """
    )

    return render_template(
        "dashboard.html",
        stats=stats,
        status_counts=status_counts,
        recent_applications=recent_applications,
    )


@app.route("/companies")
def companies():
    companies_list = fetch_all("SELECT * FROM companies ORDER BY company_name ASC")
    return render_template("companies.html", companies=companies_list, edit_company=None)


@app.route("/companies/add", methods=["POST"])
def add_company():
    company_name = clean_text(request.form.get("company_name"))

    if not company_name:
        flash("Company name is required.", "danger")
        return redirect(url_for("companies"))

    execute_query(
        """
        INSERT INTO companies (company_name, industry, website, city, state, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            company_name,
            clean_text(request.form.get("industry")) or None,
            clean_text(request.form.get("website")) or None,
            clean_text(request.form.get("city")) or None,
            clean_text(request.form.get("state")) or None,
            clean_text(request.form.get("notes")) or None,
        ),
    )

    flash("Company added successfully.", "success")
    return redirect(url_for("companies"))


@app.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):
    company = fetch_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    if not company:
        flash("Company not found.", "danger")
        return redirect(url_for("companies"))

    if request.method == "POST":
        company_name = clean_text(request.form.get("company_name"))

        if not company_name:
            flash("Company name is required.", "danger")
            return redirect(url_for("edit_company", company_id=company_id))

        execute_query(
            """
            UPDATE companies
            SET company_name=%s, industry=%s, website=%s, city=%s, state=%s, notes=%s
            WHERE company_id=%s
            """,
            (
                company_name,
                clean_text(request.form.get("industry")) or None,
                clean_text(request.form.get("website")) or None,
                clean_text(request.form.get("city")) or None,
                clean_text(request.form.get("state")) or None,
                clean_text(request.form.get("notes")) or None,
                company_id,
            ),
        )

        flash("Company updated successfully.", "success")
        return redirect(url_for("companies"))

    companies_list = fetch_all("SELECT * FROM companies ORDER BY company_name ASC")
    return render_template("companies.html", companies=companies_list, edit_company=company)


@app.route("/companies/delete/<int:company_id>", methods=["POST"])
def delete_company(company_id):
    execute_query("DELETE FROM companies WHERE company_id = %s", (company_id,))
    flash("Company deleted successfully.", "success")
    return redirect(url_for("companies"))


@app.route("/jobs")
def jobs():
    jobs_list = fetch_all(
        """
        SELECT j.*, c.company_name
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.company_id
        ORDER BY j.date_posted DESC, j.job_title ASC
        """
    )

    for job in jobs_list:
        job["requirements_text"] = format_requirements_text(job.get("requirements"))

    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name ASC")
    return render_template("jobs.html", jobs=jobs_list, companies=companies_list, edit_job=None)


@app.route("/jobs/add", methods=["POST"])
def add_job():
    job_title = clean_text(request.form.get("job_title"))
    company_id = request.form.get("company_id")

    if not job_title or not company_id:
        flash("Job title and company are required.", "danger")
        return redirect(url_for("jobs"))

    execute_query(
        """
        INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            int(company_id),
            job_title,
            clean_text(request.form.get("job_type")) or None,
            parse_int(request.form.get("salary_min")),
            parse_int(request.form.get("salary_max")),
            clean_text(request.form.get("job_url")) or None,
            clean_text(request.form.get("date_posted")) or None,
            json.dumps(parse_requirements_input(request.form.get("requirements"))),
        ),
    )

    flash("Job added successfully.", "success")
    return redirect(url_for("jobs"))


@app.route("/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    job = fetch_one("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    if not job:
        flash("Job not found.", "danger")
        return redirect(url_for("jobs"))

    if request.method == "POST":
        job_title = clean_text(request.form.get("job_title"))
        company_id = request.form.get("company_id")

        if not job_title or not company_id:
            flash("Job title and company are required.", "danger")
            return redirect(url_for("edit_job", job_id=job_id))

        execute_query(
            """
            UPDATE jobs
            SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s, salary_max=%s, job_url=%s, date_posted=%s, requirements=%s
            WHERE job_id=%s
            """,
            (
                int(company_id),
                job_title,
                clean_text(request.form.get("job_type")) or None,
                parse_int(request.form.get("salary_min")),
                parse_int(request.form.get("salary_max")),
                clean_text(request.form.get("job_url")) or None,
                clean_text(request.form.get("date_posted")) or None,
                json.dumps(parse_requirements_input(request.form.get("requirements"))),
                job_id,
            ),
        )

        flash("Job updated successfully.", "success")
        return redirect(url_for("jobs"))

    jobs_list = fetch_all(
        """
        SELECT j.*, c.company_name
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.company_id
        ORDER BY j.date_posted DESC, j.job_title ASC
        """
    )

    for row in jobs_list:
        row["requirements_text"] = format_requirements_text(row.get("requirements"))

    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name ASC")
    job["requirements_input"] = to_json_text(job.get("requirements"))

    return render_template("jobs.html", jobs=jobs_list, companies=companies_list, edit_job=job)


@app.route("/jobs/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    execute_query("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    flash("Job deleted successfully.", "success")
    return redirect(url_for("jobs"))


@app.route("/applications")
def applications():
    applications_list = fetch_all(
        """
        SELECT a.*, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        """
    )

    for application in applications_list:
        application["interview_data_text"] = format_interview_text(application.get("interview_data"))

    jobs_list = fetch_all(
        """
        SELECT j.job_id, j.job_title, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name ASC, j.job_title ASC
        """
    )

    return render_template(
        "applications.html",
        applications=applications_list,
        jobs=jobs_list,
        edit_application=None,
    )


@app.route("/applications/add", methods=["POST"])
def add_application():
    job_id = request.form.get("job_id")
    application_date = clean_text(request.form.get("application_date"))
    status = clean_text(request.form.get("status"))

    if not job_id or not application_date or not status:
        flash("Job, application date, and status are required.", "danger")
        return redirect(url_for("applications"))

    execute_query(
        """
        INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            int(job_id),
            application_date,
            status,
            clean_text(request.form.get("resume_version")) or None,
            parse_bool(request.form.get("cover_letter_sent")),
            json.dumps(parse_interview_input(request.form.get("interview_data"))),
        ),
    )

    flash("Application added successfully.", "success")
    return redirect(url_for("applications"))


@app.route("/applications/edit/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):
    application = fetch_one("SELECT * FROM applications WHERE application_id = %s", (application_id,))
    if not application:
        flash("Application not found.", "danger")
        return redirect(url_for("applications"))

    if request.method == "POST":
        job_id = request.form.get("job_id")
        application_date = clean_text(request.form.get("application_date"))
        status = clean_text(request.form.get("status"))

        if not job_id or not application_date or not status:
            flash("Job, application date, and status are required.", "danger")
            return redirect(url_for("edit_application", application_id=application_id))

        execute_query(
            """
            UPDATE applications
            SET job_id=%s, application_date=%s, status=%s, resume_version=%s, cover_letter_sent=%s, interview_data=%s
            WHERE application_id=%s
            """,
            (
                int(job_id),
                application_date,
                status,
                clean_text(request.form.get("resume_version")) or None,
                parse_bool(request.form.get("cover_letter_sent")),
                json.dumps(parse_interview_input(request.form.get("interview_data"))),
                application_id,
            ),
        )

        flash("Application updated successfully.", "success")
        return redirect(url_for("applications"))

    applications_list = fetch_all(
        """
        SELECT a.*, j.job_title, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
        """
    )

    for row in applications_list:
        row["interview_data_text"] = format_interview_text(row.get("interview_data"))

    jobs_list = fetch_all(
        """
        SELECT j.job_id, j.job_title, c.company_name
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY c.company_name ASC, j.job_title ASC
        """
    )

    application["interview_data_input"] = to_json_text(application.get("interview_data"))

    return render_template(
        "applications.html",
        applications=applications_list,
        jobs=jobs_list,
        edit_application=application,
    )


@app.route("/applications/delete/<int:application_id>", methods=["POST"])
def delete_application(application_id):
    execute_query("DELETE FROM applications WHERE application_id = %s", (application_id,))
    flash("Application deleted successfully.", "success")
    return redirect(url_for("applications"))


@app.route("/contacts")
def contacts():
    contacts_list = fetch_all(
        """
        SELECT ct.*, c.company_name
        FROM contacts ct
        JOIN companies c ON ct.company_id = c.company_id
        ORDER BY ct.contact_name ASC
        """
    )

    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name ASC")
    return render_template("contacts.html", contacts=contacts_list, companies=companies_list, edit_contact=None)


@app.route("/contacts/add", methods=["POST"])
def add_contact():
    company_id = request.form.get("company_id")
    contact_name = clean_text(request.form.get("contact_name"))

    if not company_id or not contact_name:
        flash("Company and contact name are required.", "danger")
        return redirect(url_for("contacts"))

    execute_query(
        """
        INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            int(company_id),
            contact_name,
            clean_text(request.form.get("title")) or None,
            clean_text(request.form.get("email")) or None,
            clean_text(request.form.get("phone")) or None,
            clean_text(request.form.get("linkedin_url")) or None,
            clean_text(request.form.get("notes")) or None,
        ),
    )

    flash("Contact added successfully.", "success")
    return redirect(url_for("contacts"))


@app.route("/contacts/edit/<int:contact_id>", methods=["GET", "POST"])
def edit_contact(contact_id):
    contact = fetch_one("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    if not contact:
        flash("Contact not found.", "danger")
        return redirect(url_for("contacts"))

    if request.method == "POST":
        company_id = request.form.get("company_id")
        contact_name = clean_text(request.form.get("contact_name"))

        if not company_id or not contact_name:
            flash("Company and contact name are required.", "danger")
            return redirect(url_for("edit_contact", contact_id=contact_id))

        execute_query(
            """
            UPDATE contacts
            SET company_id=%s, contact_name=%s, title=%s, email=%s, phone=%s, linkedin_url=%s, notes=%s
            WHERE contact_id=%s
            """,
            (
                int(company_id),
                contact_name,
                clean_text(request.form.get("title")) or None,
                clean_text(request.form.get("email")) or None,
                clean_text(request.form.get("phone")) or None,
                clean_text(request.form.get("linkedin_url")) or None,
                clean_text(request.form.get("notes")) or None,
                contact_id,
            ),
        )

        flash("Contact updated successfully.", "success")
        return redirect(url_for("contacts"))

    contacts_list = fetch_all(
        """
        SELECT ct.*, c.company_name
        FROM contacts ct
        JOIN companies c ON ct.company_id = c.company_id
        ORDER BY ct.contact_name ASC
        """
    )

    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name ASC")
    return render_template("contacts.html", contacts=contacts_list, companies=companies_list, edit_contact=contact)


@app.route("/contacts/delete/<int:contact_id>", methods=["POST"])
def delete_contact(contact_id):
    execute_query("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
    flash("Contact deleted successfully.", "success")
    return redirect(url_for("contacts"))


@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    matches = []
    entered_skills = ""

    if request.method == "POST":
        entered_skills = clean_text(request.form.get("skills"))
        matches = calculate_job_matches(entered_skills)

    return render_template("job_match.html", matches=matches, entered_skills=entered_skills)


@app.errorhandler(Error)
def handle_database_error(error):
    flash(f"Database error: {error}", "danger")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
