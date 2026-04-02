DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

CREATE TABLE companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    website VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    notes TEXT
);

CREATE TABLE jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_type ENUM('Full-time','Part-time','Contract','Internship'),
    salary_min INT,
    salary_max INT,
    job_url VARCHAR(300),
    date_posted DATE,
    requirements JSON,
    CONSTRAINT fk_jobs_companies
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn') NOT NULL,
    resume_version VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data JSON,
    CONSTRAINT fk_applications_jobs
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE contacts (
    contact_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes TEXT,
    CONSTRAINT fk_contacts_companies
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp', 'Technology', 'https://techcorp.example.com', 'Miami', 'FL', 'Interested in software engineering roles.'),
('DataCo', 'Analytics', 'https://dataco.example.com', 'Orlando', 'FL', 'Strong fit for data analyst positions.'),
('CloudSphere', 'Cloud Computing', 'https://cloudsphere.example.com', 'Tampa', 'FL', 'Internship-friendly employer.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 75000, 95000, 'https://techcorp.example.com/jobs/software-developer', '2026-03-20', JSON_ARRAY('Python', 'SQL', 'Flask')),
(2, 'Data Analyst', 'Full-time', 65000, 82000, 'https://dataco.example.com/jobs/data-analyst', '2026-03-18', JSON_ARRAY('SQL', 'Tableau', 'Excel')),
(3, 'Backend Intern', 'Internship', 20, 28, 'https://cloudsphere.example.com/jobs/backend-intern', '2026-03-15', JSON_ARRAY('Python', 'Flask', 'Git'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-03-21', 'Applied', 'v3', TRUE, JSON_OBJECT('rounds', 0, 'notes', 'Submitted through company website')),
(2, '2026-03-22', 'Screening', 'v2', FALSE, JSON_OBJECT('rounds', 1, 'next_step', 'Phone screen next week')),
(3, '2026-03-24', 'Interview', 'v3', TRUE, JSON_OBJECT('rounds', 2, 'format', 'Virtual interview'));

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Ava Thompson', 'Technical Recruiter', 'ava.thompson@techcorp.example.com', '305-555-0123', 'https://linkedin.com/in/avathompson', 'Reached out after application.'),
(2, 'Daniel Perez', 'Hiring Manager', 'daniel.perez@dataco.example.com', '407-555-0184', 'https://linkedin.com/in/danielperez', 'Interested in analytics portfolio.'),
(3, 'Sophia Lee', 'Engineering Recruiter', 'sophia.lee@cloudsphere.example.com', '813-555-0199', 'https://linkedin.com/in/sophialee', 'Met at career fair.');