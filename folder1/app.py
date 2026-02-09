from flask import Flask,render_template,request,redirect,url_for,session,flash,jsonify,abort
from flask_sqlalchemy import SQLAlchemy
from models import PatientHistory,Appointment,Doctor,Patient,Department,DoctorAvailability,User
from extensions import db
from datetime import datetime,date
from sqlalchemy import event
from sqlalchemy.engine import Engine   
import sqlite3   
from dotenv import load_dotenv
import os 

load_dotenv('folder1/.env')
#creating the app
app=Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")  

#configuring the database
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///userdetails.db'
db.init_app(app)

#foreign key constraint turning on for sqlite
@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

# Create tables
with app.app_context():
   #db.drop_all() #for deleting the database
   db.create_all() #for creating the database
   if not User.query.filter_by(user_type='admin').first():
        admin = User(
            name='Admin',
            password='admin123',
            email='admin267@gmail.com',
            user_type='admin'
        )
        db.session.add(admin)
        db.session.commit()   

#route for Register page   
@app.route("/",methods=["GET", "POST"])
def Register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email=request.form["email"]

        existing = User.query.filter_by(email=email).first()
        if existing:
           flash("Email already registered!", "error")
           return redirect(url_for("Register"))            
        else:
            # Validate password match
            if password != confirm_password:
                return "Passwords do not match", 400
            
            # Create user object
            user = User(name=full_name, password=password,email=email)
            db.session.add(user)
            db.session.flush()     # Get user.id without committing
            # Step 2 — Create Patient entry
            patient = Patient(patient_id=user.id)
            db.session.add(patient)
            try:
               db.session.commit()
            except Exception as e:
               db.session.rollback()
               return f"Error: {str(e)}"

            # Redirect to login page
            return redirect(url_for("login"))       
    return render_template("Register.html")

#route for login page
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form['full_name']
        password = request.form['password']
        email=request.form['email']

        # Check if user is a doctor
        doctor = User.query.filter_by(name=username,password=password,email=email,user_type='doctor').first()
        if doctor:
            session["doct_id"]=doctor.id
            return redirect(url_for("doctor_dashboard"))

        # Check if user is a patient
        patient = User.query.filter_by(name=username,password=password,email=email,user_type='patient').first()
        if patient:
            session["patient_id"]=patient.id
            return redirect(url_for("patient_dashboard"))
        
        # Check if user is a admin
        admin = User.query.filter_by(name=username,password=password,email=email,user_type='admin').first()
        if admin:
            session['admin_id']=admin.id
            return redirect(url_for('admin'))
        
        # If not found
        flash("Invalid username or password", "error")
        return redirect(url_for("login"))             
    return render_template("login.html")  


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/admin",methods=["GET","POST"])
def admin():
    #rendering admin dashboard as per admin's request
    if 'admin_id' in session and request.method=='GET':
        doctors=Doctor.query.all()
        patients=Patient.query.all()
        appointments=Appointment.query.filter_by(status='upcoming').all()
        departments=Department.query.all()
        return render_template("admin.html",doctors=doctors,patients=patients,appointments=appointments,departments=departments) 
     
    #rendering admin dashboard as per admin's search request
    if 'admin_id' in session and request.method=='POST': 
        entity_name = request.form['search']
        doctors = Doctor.query.join(User).filter(User.name.ilike(f"%{entity_name}%")).all()
        patients=Patient.query.join(User).filter(User.name.ilike(f"%{entity_name}%")).all()
        appointments=Appointment.query.filter_by(status='upcoming').all()
        departments=Department.query.filter(Department.name.ilike(f"%{entity_name}%")).all()
        return render_template("admin.html",doctors=doctors,patients=patients,appointments=appointments,departments=departments)
    abort(403)
@app.route('/admin/delete-patient',methods=['POST'])
def deletepatient():
    if request.method=='POST':
       patient_id=request.form['patient_id']
       user=User.query.get_or_404(patient_id)
       patient_history=PatientHistory.query.filter_by(patient_id=patient_id).all()
       for appt in user.patient.appointments:
            availability = DoctorAvailability.query.filter_by(doctor_id=appt.doctor_id,date=appt.date).first()

            if availability:
                if appt.time == availability.morning_slot:
                    availability.morning_booked = "False"
                elif appt.time == availability.evening_slot:
                    availability.evening_booked = "False"

       for appt in list(user.patient.appointments):
            if appt.status == "upcoming":
                db.session.delete(appt)
            else:
                appt.patient_status=f'{user.name}, Deleted'  
       for his in patient_history:
           his.patient_status=f'{user.name,user.email}, Deleted'           
       db.session.delete(user)
       db.session.commit()
       return redirect(url_for('admin'))

@app.route("/admin/doctor", methods=["GET","POST"])
def create_doctor_page():
    if 'admin_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    #rendering create doctor page as per admin's request
    if request.method=="GET":
        return render_template(
        "adddoctor.html",
        btn_name="Create",
        url="createdoctor",
        header="Add a new Doctor"
        )

    #adding new doctor to database
    if request.method == "POST": 
        button_name='Create'     
        email=request.form['email']
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Email already registered!", "error")
            return redirect(url_for("create_doctor_page"))
        fullname=request.form['fullname']
        department_id=request.form['department_id']
        oexperience=request.form['oexperience']
        qualification=request.form["qualification"]
        role=request.form["role"]
        password=request.form["password"]
        sexperience=request.form['sexperience']
        user = User(name=fullname, password=password,email=email,user_type='doctor')
        db.session.add(user)

        db.session.flush()     # Get user.id without committing

        #create doctor object
        new_doctor = Doctor(doct_id=user.id,dept_id=department_id,qualification=qualification,role=role,oexperience=oexperience,sexperience=sexperience)
        db.session.add(new_doctor)

        # commit it to the database
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()   
            return "Create department first for the entered department id", 400
        return redirect(url_for("admin"))       
 

@app.route("/doctor-dashboard",methods=["GET"])
def doctor_dashboard():
    if request.method=="GET" and "doct_id" in session:
        doct_id=session["doct_id"]
        # Fetching doctor details 
        doctor = Doctor.query.filter_by(doct_id=doct_id).first()
        # Fetching appointments from Appointment table
        appointments = Appointment.query.filter_by(doctor_id=doct_id,status='upcoming').all() 
        uappointments=[]
        upatient_ids=[]
        for appt in appointments:
            if appt.patient_id not in upatient_ids:
                upatient_ids.append(appt.patient_id)
                uappointments.append(appt)    

        return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        appointments=appointments,
        uappointments=uappointments
        )
    else:
        abort(403)       

@app.route('/admin/editdoctor/',methods=["GET","POST"])
def editdoctor():
    button_name='Update'
    if request.method=='GET':
       doct_id=request.args.get('doct_id')
       doctor=Doctor.query.filter_by(doct_id=doct_id).first()
       return render_template("adddoctor.html",btn_name=button_name,doctor=doctor,url='editdoctor',doct_id=doct_id,header='Update Doctor Details') 
    if request.method=='POST':
        doct_id=request.form['doct_id']
        user=User.query.get_or_404(doct_id) #first updating 'User' table
        user.name=request.form['fullname']
        user.password=request.form["password"]
        user.email=request.form['email']
        doctor=Doctor.query.get_or_404(doct_id) #then updating 'Doctor' table
        doctor.name=request.form['fullname']
        doctor.password=request.form["password"]
        doctor.qualification=request.form["qualification"]
        doctor.role=request.form["role"]
        doctor.oexperience=request.form['oexperience']
        doctor.dept_id=request.form['department_id']
        doctor.sexperience=request.form['sexperience']
        doctor.email=request.form['email']

        #commit it to database
        db.session.commit()
        return redirect(url_for('admin'))
    
@app.route('/admin/deletedoctor', methods=['POST'])  
def deletedoctor():
    if request.method == 'POST':
        doct_id = request.form['doct_id']
        user = User.query.get_or_404(doct_id)
        patient_history=PatientHistory.query.filter_by(doctor_id=doct_id).all()
        doctor = Doctor.query.get_or_404(doct_id)

        # Free booked slots for this doctor
        for appt in list(doctor.appointments):
            if appt.status == "upcoming":
                availability = DoctorAvailability.query.filter_by(
                    doctor_id=doctor.doct_id,
                    date=appt.date
                ).first()

                if availability:
                    if appt.time == availability.morning_slot:
                        availability.morning_booked = "False"
                    elif appt.time == availability.evening_slot:
                        availability.evening_booked = "False"

        # Delete upcoming appointments only
        for appt in list(doctor.appointments):
            if appt.status == "upcoming":
                db.session.delete(appt)
            else:
                appt.doctor_status=f'{user.name}, Deleted'
        for his in patient_history:
            his.doctor_status=f'{user.name,user.email}, Deleted'            

        # Delete doctor (now safe)
        db.session.delete(user)
        db.session.commit()

        return redirect(url_for('admin'))
    

@app.route('/admin/create_department',methods=["POST","GET"])
def create_department():
    if request.method=='POST':
        name=request.form['name']
        description=request.form['description']
        existing = Department.query.filter_by(name=name).first()
        if existing:
            error='This department name already exists'
            return render_template("create_department.html",error=error,url='create_department',button='create')
        else:
            try:
              department=Department(name=name,description=description)
              db.session.add(department)
              db.session.commit()
            except Exception as e:
              db.session.rollback()
              return f'Error:{str(e)}'
            return redirect(url_for('admin'))   

    return render_template("create_department.html",header='Add a New Department',url='create_department',button='create')


@app.route('/admin/editdepartment', methods=['GET', 'POST'])
def editdepartment():
    if request.method == 'GET':
        dept_id = request.args.get('dept_id')
        department = Department.query.get_or_404(dept_id)
        return render_template('create_department.html', department=department,header='Update Department Details',url='editdepartment',button='Update')

    # for POST request
    dept_id = request.form['dept_id']
    department = Department.query.get_or_404(dept_id)
    department.name = request.form['name']
    department.description = request.form['description']
    db.session.commit()
    return redirect(url_for('admin')) 

@app.route('/admin/deletedepartment', methods=['POST'])  
def deletedepartment():
    if request.method=='POST':
       dept_id=request.form['dept_id']
       department=Department.query.get_or_404(dept_id)
       doctors = Doctor.query.filter_by(dept_id=dept_id).all()

       for doc in doctors:
           Appointment.query.filter(Appointment.doctor_id == doc.doct_id,Appointment.status == "upcoming").delete()
           user = User.query.get(doc.doct_id)
           if user:
               db.session.delete(user)
       #deleting doctor record
       db.session.delete(department)
       db.session.commit()
       return redirect(url_for('admin'))

@app.route('/doctor_dashboard/updatehistory',methods=['POST'])
def update_history():
    patient_id=request.form['patient_id']
    dept_id=request.form['dept_id'] 
    doct_id=request.form['doct_id']
    patient=Patient.query.filter_by(patient_id=patient_id).first()
    dept=Department.query.filter_by(dept_id=dept_id).first()
    return render_template('update_history.html',patient=patient,dept=dept,doct_id=doct_id) 


@app.route("/doctor-dashboard/provide-availability",methods=["GET","POST"]) #availability provided by a doctor
def provide_availability():   
    if request.method=='POST':
        doctor_id = request.form["doctor_id"]
        dates = request.form.getlist("date[]")  
        morning_times = request.form.getlist("morning_time[]")
        evening_times = request.form.getlist("evening_time[]")

        for i in range(len(dates)):
            d = date.fromisoformat(dates[i])
            morning = morning_times[i]
            evening = evening_times[i]
            
            existing=DoctorAvailability.query.filter_by(doctor_id=doctor_id,date=d).first()
            if existing: 
                return "These slots have been provided already",409
            else:
                #Save each record to DB
                availability = DoctorAvailability(doctor_id=doctor_id,date=d,morning_slot=morning,evening_slot=evening)
                db.session.add(availability)
                db.session.commit()
        return redirect(url_for("doctor_dashboard"))
    if request.method=='GET':
        doct_id=request.args.get('doct_id')
        return render_template('provide_availability.html',doctor_id=doct_id)
    abort(404)

@app.route('/doctor_dashboard/markcomplete',methods=['POST']) #endpoint for changing appointment status
def markcomplete():
    sr_no=request.form['sr_no']
    appt=Appointment.query.filter_by(sr_no=sr_no).first()
    appt.status='complete'
    db.session.commit()
    flash('Appointment marked as complete successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))


@app.route("/patient-dashboard/department-details/doctor-availability",methods=["GET"]) #availability of a doctor to a patient
def doctor_availability(): 
    try:
        patient_id=request.args.get("patient_id")
        doct_id=request.args.get("doct_id")
        availabilities=DoctorAvailability.query.filter_by(doctor_id=doct_id).all()
        return render_template("doctor_availability.html",patient_id=patient_id,doctor_id=doct_id,availabilities=availabilities)
    except:
        abort(404)  


@app.route("/patient_history",methods=["GET","POST"])
def patient_history():
    url=None
    #saving updated history of the patient by the doctor
    if request.method=="POST" and 'save' in request.form:
        # Handle save action
            patient_id=request.form["patient_id"]
            visit_type=request.form["visit_type"]
            tests_done=request.form["tests_done"]
            diagnosis=request.form["diagnosis"]
            prescription=request.form["prescription"]
            medicines=request.form["medicines"]
            doct_id=request.form['doct_id']

            # Get latest visit number
            patienthis = PatientHistory.query.filter_by(patient_id=patient_id).order_by(PatientHistory.visit_no.desc()).first()
            if patienthis:
                visit_no = patienthis.visit_no + 1
            else:
                visit_no = 1
            patient_object=PatientHistory(
            visit_type=visit_type,
            tests_done=tests_done,
            diagnosis=diagnosis,
            prescription=prescription,
            medicines=medicines,
            patient_id=patient_id,
            doctor_id=doct_id,
            visit_no=visit_no
                )
            db.session.add(patient_object)
            db.session.commit()
            return redirect(url_for('doctor_dashboard'))   

    if request.method=='POST':       
       #showing patient-history of the patient as per doctor's request
        if 'view' in request.form:
           url=url_for("doctor_dashboard")
        elif 'adview' in request.form: #patient_history as per admin request
           url=url_for("admin")
        else: #patient_history as per patient request
            url=url_for("patient_dashboard")

        patient_id=request.form["patient_id"]
       
        patient=Patient.query.filter_by(patient_id=patient_id).first()
        # Fetch all records
        histories = PatientHistory.query.filter_by(patient_id=patient_id).all()
        doctor=None
        if histories:
            doctor=histories[0].doctor         
        return render_template("patient_history.html", history=histories,patient_name=patient.user.name,doctor_name=doctor.user.name if doctor else None,patient_department=doctor.department.name if doctor else None,url=url)        
    else:
        abort(404)


@app.route('/patient_dashboard', methods=["GET", "POST"])
def patient_dashboard():
    # user login
    if request.method=='GET' and 'patient_id' in session:
        patient_id = session['patient_id']
        patient = db.session.get(Patient, patient_id)
        departments = Department.query.with_entities(Department.dept_id, Department.name).all()
        appointments = Appointment.query.filter_by(patient_id=patient_id,status='upcoming').all()

        return render_template("patient_dashboard.html",
                               patient=patient,
                               departments=departments,
                               appointments=appointments)

    else:
        abort(404)

   
@app.route('/patient-dashboard/department-details/doctor-profile',methods=['GET']) 
def doctor_profile(): #it receives request from the department_details page
    if 'patient_id' in session:
        patient_id=request.args.get('patient_id')
        doct_id=request.args.get('doct_id') 
        dept_id=request.args.get('dept_id')
        patient=Patient.query.filter_by(patient_id=patient_id).first()
        doctor=Doctor.query.filter_by(doct_id=doct_id).first()
        return render_template('doctor_profile.html',patient=patient,doctor=doctor,dept_id=dept_id)
    else:
        abort(404)

@app.route('/patients/edit', methods=['GET', 'POST'])
def editpatient():
    if request.method == 'GET':
        patient_id = request.args.get('patient_id')
        patient = Patient.query.get_or_404(patient_id)
        return render_template('editpatient.html', patient=patient)

    # for POST request
    if request.method=='POST':
       patient_id = request.form['patient_id']
       url=request.form['url']
       patient = Patient.query.get_or_404(patient_id)
       patient.user.name = request.form['name']
       patient.user.password = request.form['password']

       db.session.commit()
       return redirect(url_for(url))  
    

@app.route("/patient-dashboard/department_details",methods=["GET"])
def department_details():
    if request.method=="GET" and 'patient_id' in session: #rendering departments details as per patient request on patient-dashboard
        dept_id=request.args.get('dept_id')
        patient_id=request.args.get('patient_id')
        patient=Patient.query.filter_by(patient_id=patient_id).first()
        department=Department.query.filter_by(dept_id=dept_id).first()
        if department:
           return render_template("department_details.html",department_name=department.name,     department=department,patient=patient)
    else: #throw error for an unauthorized access
        abort(403)  
    

@app.route('/department-details/appointment',methods=['GET','POST'])
def appointment():
    if request.method=='POST':
     try:
        doct_id=request.form['doct_id'] 
        session['doct_id']=doct_id
        patient_id=request.form['patient_id'] 
        slot=request.form['slot']
        date,time=slot.split('|')
        patient_history=PatientHistory.query.filter_by(patient_id=patient_id).first()
        if patient_history:
            if patient_history.doctor_id==int(doct_id):
             appointment=Appointment(doctor_id=doct_id,patient_id=patient_id,date=date,time=time)  
             db.session.add(appointment)
             db.session.commit() 
             availability=DoctorAvailability.query.filter_by(doctor_id=doct_id,date=date).first()
             if availability.morning_slot==time:
                availability.morning_booked='True'
                db.session.commit()
             else:
               availability.evening_booked='True'
               db.session.commit()
             return redirect(url_for('patient_dashboard',doct_id=doct_id))
            else:
              flash("you can't book the appointment of another doctor") #---we are here
              return redirect(url_for('appointment',doct_id=doct_id,patient_id=patient_id))
        else:
            #patient's appointment with his first doctor
            appointment=Appointment(doctor_id=doct_id,patient_id=patient_id,date=date,time=time)  
            db.session.add(appointment)
            db.session.commit() 
            availability=DoctorAvailability.query.filter_by(doctor_id=doct_id,date=date).first()
            if availability.morning_slot==time:
                availability.morning_booked='True'
                db.session.commit()
            else:
               availability.evening_booked='True'
               db.session.commit()
            return redirect(url_for('patient_dashboard',doct_id=doct_id)) 
     except:
         return "Invalid request", 400        
    if request.method=='GET' and 'patient_id' in session: #rendering if patient is already assigned with another doctor
          patient_id=request.args.get("patient_id")
          doct_id=request.args.get("doct_id")
          availabilities=DoctorAvailability.query.filter_by(doctor_id=doct_id).all()
          return render_template("doctor_availability.html",patient_id=patient_id,doctor_id=doct_id,availabilities=availabilities)


@app.route("/cancel_appointment", methods=["POST"])
def cancel_appointment():
   sr_no=request.form['sr_no']
   appointment=Appointment.query.filter_by(sr_no=sr_no).first()
   db.session.delete(appointment)
   db.session.commit()
   date=appointment.date
   time=appointment.time
   doct_id=appointment.doctor_id
   if time=='08:00 - 12:00 PM': # checking if time is morning-slot
        availability=DoctorAvailability.query.filter_by(doctor_id=doct_id,date=date,morning_slot=time).first()
        availability.morning_booked='False'
        db.session.commit()
        if 'pcancel' in request.form:
            return redirect(url_for('patient_dashboard'))
        else:
            return redirect(url_for('doctor_dashboard'))
   else:
       # if time is evening-slot
       availability=DoctorAvailability.query.filter_by(doctor_id=doct_id,date=date,evening_slot=time).first()
       availability.evening_booked='False'
       db.session.commit()
       if 'pcancel' in request.form:
            return redirect(url_for('patient_dashboard'))
       else:
            return redirect(url_for('doctor_dashboard'))


#running the app
if __name__=="__main__":
    app.run(debug=True)