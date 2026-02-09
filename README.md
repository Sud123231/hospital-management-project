# Hospital Management System

A lightweight Hospital Management System built with **Flask**, designed for educational and demo purposes. It supports role‑based access for **Admin**, **Doctor**, and **Patient**, and provides core features like appointment booking, doctor availability tracking, and patient history management.

---

## Features

### Admin

* Create and manage doctors and departments
* View all registered patients
* Monitor upcoming appointments
* Search through doctors, departments, and patients

### Doctor

* View scheduled appointments
* Add and update availability (morning/evening)
* Update patient medical history after consultations
* Mark appointments as completed

### Patient

* Register and log in
* Browse departments and doctor profiles
* Book or cancel appointments
* View full appointment history

---

## Project Structure

```
MAD1_PROJECT/
├── folder1/
│   ├── static/
│   ├── templates/
│   ├── .env
│   ├── app.py
│   ├── extensions.py
│   └── models.py
├── instance
└── .gitignore
```

---

## Installation & Setup

1. Clone or download the repository.
2. Install dependencies:

   ```bash
   pip install flask flask_sqlalchemy python-dotenv
   ```
3. Inside `folder1/`, make sure you have a `.env` file with:

   ```env
   SECRET_KEY=your_secret_key
   ```
4. Start the application:

   ```bash
   python folder1/app.py
   ```
5. Open in your browser:

   ```
   http://127.0.0.1:5000/
   ```

---

## Default Admin Credentials

```
Email: admin267@gmail.com
Password: admin123
```

---

## How It Works

### Authentication

Patients sign up directly. Admins create doctor accounts. Sessions are used for login tracking.

### Appointment Flow

* Doctors define available dates and time slots.
* Patients book based on availability.
* Doctors complete appointments and record visit details.

### Patient History

Doctors maintain medical history entries including diagnosis, medication, tests, and notes.

---

## Database

The application uses **SQLite**, with tables for users, doctors, patients, departments, appointments, history, and availability. Foreign key constraints are enabled.

---

## Basic Workflow Test

1. Register a patient
2. Log in as Admin → add a department and doctor
3. Log in as Doctor → add availability
4. Log in as Patient → book an appointment
5. Doctor completes appointment
6. Patient checks visit history

---

## Contributing

Suggestions and improvements are welcome. This project is intended for learning Flask structure, routing, and database modeling.
