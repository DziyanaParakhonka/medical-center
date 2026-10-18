from datetime import datetime
from decimal import Decimal
from urllib.parse import quote_plus

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

app.secret_key = "medical-center-demo-key"


# =========================================================
# POŁĄCZENIE Z MICROSOFT SQL SERVER
# =========================================================

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=.\SQLEXPRESS;"
    "DATABASE=medical_center;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

connection_url = (
    "mssql+pyodbc:///?odbc_connect="
    + quote_plus(connection_string)
)

app.config["SQLALCHEMY_DATABASE_URI"] = connection_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# MODEL PACJENTA
# =========================================================

class Patient(db.Model):

    __tablename__ = "Patients"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        "Id",
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        "FirstName",
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        "LastName",
        db.String(100),
        nullable=False
    )

    birth_date = db.Column(
        "BirthDate",
        db.Date
    )

    phone = db.Column(
        "Phone",
        db.String(30)
    )

    email = db.Column(
        "Email",
        db.String(150),
        unique=True
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="patient"
    )


# =========================================================
# MODEL SPECJALIZACJI
# =========================================================

class Specialization(db.Model):

    __tablename__ = "Specializations"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        "Id",
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        "Name",
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        "Description",
        db.String(250)
    )

    doctors = db.relationship(
        "Doctor",
        back_populates="specialization"
    )

    services = db.relationship(
        "Service",
        back_populates="specialization"
    )


# =========================================================
# MODEL LEKARZA
# =========================================================

class Doctor(db.Model):

    __tablename__ = "Doctors"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        "Id",
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        "FirstName",
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        "LastName",
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        "Phone",
        db.String(30)
    )

    email = db.Column(
        "Email",
        db.String(150),
        unique=True
    )

    specialization_id = db.Column(
        "SpecializationId",
        db.Integer,
        db.ForeignKey("dbo.Specializations.Id"),
        nullable=False
    )

    is_active = db.Column(
        "IsActive",
        db.Boolean,
        nullable=False,
        default=True
    )

    specialization = db.relationship(
        "Specialization",
        back_populates="doctors"
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="doctor"
    )


# =========================================================
# MODEL USŁUGI
# =========================================================

class Service(db.Model):

    __tablename__ = "Services"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        "Id",
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        "Name",
        db.String(150),
        nullable=False,
        unique=True
    )

    description = db.Column(
        "Description",
        db.String(500)
    )

    duration_minutes = db.Column(
        "DurationMinutes",
        db.Integer,
        nullable=False
    )

    price = db.Column(
        "Price",
        db.Numeric(10, 2),
        nullable=False
    )

    specialization_id = db.Column(
        "SpecializationId",
        db.Integer,
        db.ForeignKey("dbo.Specializations.Id"),
        nullable=False
    )

    is_active = db.Column(
        "IsActive",
        db.Boolean,
        nullable=False,
        default=True
    )

    specialization = db.relationship(
        "Specialization",
        back_populates="services"
    )

    appointments = db.relationship(
        "Appointment",
        back_populates="service"
    )


# =========================================================
# MODEL WIZYTY
# =========================================================

class Appointment(db.Model):

    __tablename__ = "Appointments"
    __table_args__ = {"schema": "dbo"}

    id = db.Column(
        "Id",
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        "PatientId",
        db.Integer,
        db.ForeignKey("dbo.Patients.Id"),
        nullable=False
    )

    doctor_id = db.Column(
        "DoctorId",
        db.Integer,
        db.ForeignKey("dbo.Doctors.Id"),
        nullable=False
    )

    service_id = db.Column(
        "ServiceId",
        db.Integer,
        db.ForeignKey("dbo.Services.Id"),
        nullable=False
    )

    appointment_datetime = db.Column(
        "AppointmentDateTime",
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        "Status",
        db.String(30),
        nullable=False,
        default="Zaplanowana"
    )

    notes = db.Column(
        "Notes",
        db.String(500)
    )

    created_at = db.Column(
        "CreatedAt",
        db.DateTime,
        nullable=False
    )

    patient = db.relationship(
        "Patient",
        back_populates="appointments"
    )

    doctor = db.relationship(
        "Doctor",
        back_populates="appointments"
    )

    service = db.relationship(
        "Service",
        back_populates="appointments"
    )


# =========================================================
# PANEL GŁÓWNY
# =========================================================

@app.route("/")
def home():

    patients_count = Patient.query.count()

    doctors_count = Doctor.query.filter_by(
        is_active=True
    ).count()

    services_count = Service.query.filter_by(
        is_active=True
    ).count()

    appointments_count = Appointment.query.count()

    upcoming_appointments = (
        Appointment.query
        .filter(
            Appointment.status == "Zaplanowana",
            Appointment.appointment_datetime >= datetime.now()
        )
        .order_by(
            Appointment.appointment_datetime.asc()
        )
        .limit(5)
        .all()
    )

    return render_template(
        "index.html",
        patients_count=patients_count,
        doctors_count=doctors_count,
        services_count=services_count,
        appointments_count=appointments_count,
        upcoming_appointments=upcoming_appointments
    )


# =========================================================
# PACJENCI
# =========================================================

@app.route("/patients", methods=["GET", "POST"])
def patients():

    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        birth_date_text = request.form.get(
            "birth_date",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        birth_date = None

        if birth_date_text:

            birth_date = datetime.strptime(
                birth_date_text,
                "%Y-%m-%d"
            ).date()

        new_patient = Patient(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            phone=phone if phone else None,
            email=email if email else None
        )

        try:

            db.session.add(new_patient)
            db.session.commit()

            flash(
                "Pacjent został dodany.",
                "success"
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Nie można dodać pacjenta. "
                "Adres e-mail może już istnieć.",
                "error"
            )

        return redirect(
            url_for("patients")
        )

    patient_list = (
        Patient.query
        .order_by(Patient.id.desc())
        .all()
    )

    return render_template(
        "patients.html",
        patients=patient_list
    )


# =========================================================
# LEKARZE
# =========================================================

@app.route("/doctors", methods=["GET", "POST"])
def doctors():

    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        specialization_id = int(
            request.form["specialization_id"]
        )

        new_doctor = Doctor(
            first_name=first_name,
            last_name=last_name,
            phone=phone if phone else None,
            email=email if email else None,
            specialization_id=specialization_id,
            is_active=True
        )

        try:

            db.session.add(new_doctor)
            db.session.commit()

            flash(
                "Lekarz został dodany.",
                "success"
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Nie można dodać lekarza. "
                "Adres e-mail może już istnieć.",
                "error"
            )

        return redirect(
            url_for("doctors")
        )

    doctor_list = (
        Doctor.query
        .order_by(Doctor.id.desc())
        .all()
    )

    specialization_list = (
        Specialization.query
        .order_by(Specialization.name)
        .all()
    )

    return render_template(
        "doctors.html",
        doctors=doctor_list,
        specializations=specialization_list
    )


# =========================================================
# USŁUGI
# =========================================================

@app.route("/services", methods=["GET", "POST"])
def services():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        duration_minutes = int(
            request.form["duration_minutes"]
        )

        price = Decimal(
            request.form["price"]
        )

        specialization_id = int(
            request.form["specialization_id"]
        )

        new_service = Service(
            name=name,
            description=description if description else None,
            duration_minutes=duration_minutes,
            price=price,
            specialization_id=specialization_id,
            is_active=True
        )

        try:

            db.session.add(new_service)
            db.session.commit()

            flash(
                "Usługa została dodana.",
                "success"
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Nie można dodać usługi. "
                "Usługa o tej nazwie może już istnieć.",
                "error"
            )

        return redirect(
            url_for("services")
        )

    service_list = (
        Service.query
        .order_by(Service.id.desc())
        .all()
    )

    specialization_list = (
        Specialization.query
        .order_by(Specialization.name)
        .all()
    )

    return render_template(
        "services.html",
        services=service_list,
        specializations=specialization_list
    )


# =========================================================
# WIZYTY
# =========================================================

@app.route("/appointments", methods=["GET", "POST"])
def appointments():

    if request.method == "POST":

        patient_id = int(
            request.form["patient_id"]
        )

        doctor_id = int(
            request.form["doctor_id"]
        )

        service_id = int(
            request.form["service_id"]
        )

        appointment_datetime_text = request.form[
            "appointment_datetime"
        ]

        status = request.form.get(
            "status",
            "Zaplanowana"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        appointment_datetime = datetime.strptime(
            appointment_datetime_text,
            "%Y-%m-%dT%H:%M"
        )

        doctor = db.session.get(
            Doctor,
            doctor_id
        )

        service = db.session.get(
            Service,
            service_id
        )

        if doctor is None or service is None:

            flash(
                "Nie znaleziono lekarza lub usługi.",
                "error"
            )

            return redirect(
                url_for("appointments")
            )

        if (
            doctor.specialization_id
            != service.specialization_id
        ):

            flash(
                "Wybrany lekarz nie wykonuje "
                "usług z tej specjalizacji.",
                "error"
            )

            return redirect(
                url_for("appointments")
            )

        existing_appointment = (
            Appointment.query
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_datetime
                == appointment_datetime,
                Appointment.status != "Anulowana"
            )
            .first()
        )

        if existing_appointment:

            flash(
                "Wybrany lekarz ma już wizytę "
                "w tym terminie.",
                "error"
            )

            return redirect(
                url_for("appointments")
            )

        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            service_id=service_id,
            appointment_datetime=appointment_datetime,
            status=status,
            notes=notes if notes else None,
            created_at=datetime.now()
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash(
            "Wizyta została utworzona.",
            "success"
        )

        return redirect(
            url_for("appointments")
        )

    appointment_list = (
        Appointment.query
        .order_by(
            Appointment.appointment_datetime.desc()
        )
        .all()
    )

    patient_list = (
        Patient.query
        .order_by(
            Patient.last_name,
            Patient.first_name
        )
        .all()
    )

    doctor_list = (
        Doctor.query
        .filter_by(is_active=True)
        .order_by(
            Doctor.last_name,
            Doctor.first_name
        )
        .all()
    )

    service_list = (
        Service.query
        .filter_by(is_active=True)
        .order_by(Service.name)
        .all()
    )

    return render_template(
        "appointments.html",
        appointments=appointment_list,
        patients=patient_list,
        doctors=doctor_list,
        services=service_list
    )


# =========================================================
# TEST BAZY
# =========================================================

@app.route("/test-db")
def test_db():

    return (
        "Połączenie z bazą działa. "
        f"Pacjenci: {Patient.query.count()}. "
        f"Lekarze: {Doctor.query.count()}. "
        f"Usługi: {Service.query.count()}. "
        f"Wizyty: {Appointment.query.count()}."
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)