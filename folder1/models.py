from extensions import db

class Department(db.Model):
    dept_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    # Relationship to Doctor
    doctors = db.relationship('Doctor',backref=db.backref('department'),cascade="all, delete-orphan",passive_deletes=True,lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # doctor / patient / admin
    user_type = db.Column(db.String(20), default='patient', nullable=False)

    # Relationships
    doctor = db.relationship("Doctor", back_populates="user", uselist=False,cascade="all, delete-orphan",passive_deletes=True)
    patient = db.relationship("Patient", back_populates="user", uselist=False,cascade="all, delete-orphan",passive_deletes=True)


class Doctor(db.Model):
    doct_id = db.Column(db.Integer,db.ForeignKey('user.id',ondelete="CASCADE"),primary_key=True)
    qualification = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    oexperience = db.Column(db.Integer, nullable=False)
    sexperience = db.Column(db.Integer, nullable=False)
    dept_id = db.Column(db.Integer,db.ForeignKey('department.dept_id', ondelete="CASCADE"),nullable=False )
    user = db.relationship("User", back_populates="doctor")
    appointments = db.relationship( 'Appointment', back_populates='doctor', lazy=True)
    availability = db.relationship( 'DoctorAvailability', backref='doctor', cascade="all, delete-orphan", passive_deletes=True)
    histories = db.relationship("PatientHistory",back_populates="doctor")


class Patient(db.Model):
    patient_id = db.Column(db.Integer,db.ForeignKey('user.id',ondelete="CASCADE"),primary_key=True)
    user = db.relationship("User", back_populates="patient")
    appointments = db.relationship('Appointment',back_populates='patient',lazy=True)
    histories = db.relationship("PatientHistory",back_populates="patient")


class Appointment(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    patient_status = db.Column(db.String(50), default="Active") # backend need to be changed regarding this
    doctor_status = db.Column(db.String(50), default="Active")   #backend need to be changed regarding this
    doctor_id = db.Column(db.Integer,db.ForeignKey('doctor.doct_id', ondelete="SET NULL"),nullable=True)
    patient_id = db.Column(db.Integer,db.ForeignKey('patient.patient_id', ondelete="SET NULL"),
    nullable=True)
    status = db.Column(db.String(20), default='upcoming')
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String(20), nullable=False)
    # relationships
    doctor = db.relationship('Doctor',back_populates='appointments')
    patient = db.relationship('Patient',back_populates='appointments')


class PatientHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # unique identifier for each record
    patient_status = db.Column(db.String(20), default="Active") # backend need to be changed regarding this
    doctor_status = db.Column(db.String(20), default="Active")   #backend need to be changed regarding this
    visit_no = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.Integer,db.ForeignKey('patient.patient_id', ondelete="SET NULL"),nullable=True)
    doctor_id = db.Column( db.Integer, db.ForeignKey('doctor.doct_id', ondelete="SET NULL"), nullable=True)
    visit_type = db.Column(db.String(50), nullable=False)
    tests_done = db.Column(db.String(100))
    diagnosis = db.Column(db.String(200))
    prescription = db.Column(db.String(200))
    medicines = db.Column(db.Text)

    # Relationship to Patient
    patient = db.relationship("Patient", back_populates="histories")
    # Relationship to Doctor
    doctor = db.relationship("Doctor", back_populates="histories")

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doct_id',ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    morning_slot = db.Column(db.String, nullable=False)
    evening_slot = db.Column(db.String, nullable=False)
    morning_booked=db.Column(db.String(20),default='False')
    evening_booked=db.Column(db.String(20),default='False')
