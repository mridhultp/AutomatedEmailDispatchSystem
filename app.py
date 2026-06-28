
from flask import Flask, render_template, request, send_file, redirect, flash
import os
import pandas as pd
import smtplib

from datetime import datetime

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

app.secret_key = "company_contact_secret"

UPLOAD_FOLDER = "uploads"

FILE_NAME = "Company_Contact.xlsx"
EMAIL_TEMPLATE = "email_template.txt"
RESUME_FILE = "Resume.pdf"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# DOWNLOAD CONTACT FILE
# --------------------------------------------------

@app.route("/download")
def download_file():

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        FILE_NAME
    )

    if os.path.exists(file_path):

        return send_file(
            file_path,
            as_attachment=True
        )

    flash("Contact file not found!")

    return redirect("/")


# --------------------------------------------------
# UPLOAD CONTACT FILE
# --------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:

        flash("No file selected")

        return redirect("/")

    file = request.files["file"]

    if file.filename == "":

        flash("Please select a file")

        return redirect("/")

    if not file.filename.endswith(".xlsx"):

        flash("Only Excel files allowed")

        return redirect("/")

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        FILE_NAME
    )

    file.save(filepath)

    flash("Contact file uploaded successfully!")

    return redirect("/")


# --------------------------------------------------
# CLEAR CONTACT FILE
# --------------------------------------------------

@app.route("/clear_file", methods=["POST"])
def clear_file():

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        FILE_NAME
    )

    if os.path.exists(file_path):

        os.remove(file_path)

        flash("Contact file deleted!")

    else:

        flash("No contact file found!")

    return redirect("/")


# --------------------------------------------------
# UPLOAD RESUME
# --------------------------------------------------

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    if "resume" not in request.files:

        flash("No resume selected")

        return redirect("/")

    file = request.files["resume"]

    if file.filename == "":

        flash("Please select resume")

        return redirect("/")

    if not file.filename.lower().endswith(".pdf"):

        flash("Only PDF resumes allowed")

        return redirect("/")

    resume_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        RESUME_FILE
    )

    file.save(resume_path)

    flash("Resume uploaded successfully!")

    return redirect("/")


# --------------------------------------------------
# CLEAR RESUME
# --------------------------------------------------

@app.route("/clear_resume", methods=["POST"])
def clear_resume():

    resume_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        RESUME_FILE
    )

    if os.path.exists(resume_path):

        os.remove(resume_path)

        flash("Resume deleted!")

    else:

        flash("Resume not found!")

    return redirect("/")


# --------------------------------------------------
# UPLOAD EMAIL TEMPLATE
# --------------------------------------------------

@app.route("/upload_template", methods=["POST"])
def upload_template():

    if "template" not in request.files:

        flash("No email template selected")
        return redirect("/")

    file = request.files["template"]

    if file.filename == "":

        flash("Please select an email template")
        return redirect("/")

    if not file.filename.lower().endswith(".txt"):

        flash("Only .txt template files allowed")
        return redirect("/")

    template_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        EMAIL_TEMPLATE
    )

    file.save(template_path)

    flash("Email template uploaded successfully!")

    return redirect("/")


# --------------------------------------------------
# CLEAR EMAIL TEMPLATE
# --------------------------------------------------

@app.route("/clear_template", methods=["POST"])
def clear_template():

    template_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        EMAIL_TEMPLATE
    )

    if os.path.exists(template_path):

        os.remove(template_path)
        flash("Email template deleted!")

    else:

        flash("Email template not found!")

    return redirect("/")

# --------------------------------------------------
# SEND EMAILS
# --------------------------------------------------

@app.route("/send_email", methods=["POST"])
def send_email():

    gmail_id = request.form.get(
        "email_address"
    )

    gmail_password = request.form.get(
        "email_password"
    )

    if not gmail_id or not gmail_password:

        flash(
            "Email ID and App Password required"
        )

        return redirect("/")

    contact_file = os.path.join(
        app.config["UPLOAD_FOLDER"],
        FILE_NAME
    )

    if not os.path.exists(contact_file):

        flash(
            "Please upload contact file first"
        )

        return redirect("/")

    resume_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        RESUME_FILE
    )

    if not os.path.exists(resume_path):

        flash(
            "Please upload resume first"
        )

        return redirect("/")

    try:

        template = load_email_template()

        df = pd.read_excel(
            contact_file,
            dtype=str
        )

        if "Status" not in df.columns:
            df["Status"] = ""

        if "Time" not in df.columns:
            df["Time"] = ""

        df["Status"] = (
            df["Status"]
            .fillna("")
            .astype(str)
        )

        df["Time"] = (
            df["Time"]
            .fillna("")
            .astype(str)
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            gmail_id,
            gmail_password
        )

        sent_count = 0
        failed_count = 0

        for index, row in df.iterrows():

            try:

                status = str(
                    row.get(
                        "Status",
                        ""
                    )
                ).lower()

                if status == "sent":
                    continue

                company_name = str(
                    row["Company_Name"]
                )

                role = str(
                    row["Role"]
                )

                hr_name = str(
                    row["HR_Firstname"]
                )

                recipient = str(
                    row["Company_Mail_id"]
                ).strip()

                email_body = template.format(
                    hr_name=hr_name,
                    role=role,
                    company_name=company_name
                )

                msg = MIMEMultipart()

                msg["From"] = gmail_id

                msg["To"] = recipient

                msg["Subject"] = (
                    f"Application for {role}"
                )

                msg.attach(
                    MIMEText(
                        email_body,
                        "plain"
                    )
                )

                with open(
                    resume_path,
                    "rb"
                ) as attachment:

                    part = MIMEBase(
                        "application",
                        "octet-stream"
                    )

                    part.set_payload(
                        attachment.read()
                    )

                encoders.encode_base64(
                    part
                )

                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(resume_path)}"
                )

                msg.attach(part)

                server.sendmail(
                    gmail_id,
                    recipient,
                    msg.as_string()
                )

                df.loc[
                    index,
                    "Status"
                ] = "Sent"

                df.loc[
                    index,
                    "Time"
                ] = datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                )

                sent_count += 1

            except Exception as e:

                df.loc[
                    index,
                    "Status"
                ] = "Failed"

                df.loc[
                    index,
                    "Time"
                ] = datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                )

                print(
                    f"Failed sending to {recipient}: {e}"
                )

                failed_count += 1

        server.quit()

        df.to_excel(
            contact_file,
            index=False
        )

        flash(
            f"{sent_count} email(s) sent successfully. "
            f"{failed_count} failed."
        )

    except Exception as e:

        flash(
            f"Error: {str(e)}"
        )

    return redirect("/")


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=5000)
