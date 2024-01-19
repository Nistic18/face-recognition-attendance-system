from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate
from PyQt5.QtWidgets import QDialog, QMessageBox, QInputDialog, QPushButton, QTableWidget, QTableWidgetItem, \
    QVBoxLayout, QLabel, QFormLayout, QDialogButtonBox, QTextEdit, QFileDialog
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv
import sqlite3
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import QTime
from menu import menu_Bar
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import json

class Ui_Admin(QDialog):
    def __init__(self):
        super(Ui_Admin, self).__init__()
        loadUi("adminportal.ui", self)

        self.backButton.clicked.connect(self.goBack)
        # Update time
        self.update_time()  # Initial update
        self.timer_time = QTimer(self)  # Create Timer for time update
        self.timer_time.timeout.connect(self.update_time)  # Connect timeout to the update_time function
        self.timer_time.start(1000)  # Update time every 1000 milliseconds (1 second)
        self.image = None

        # Add a password input field
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setGeometry(1080, 120, 250, 40)
        self.password_input.setStyleSheet("QLineEdit { background-color: white; color: black; }")

        # Connect the button click signal to the registerFace method
        # self.RegisterFaceButton.clicked.connect(self.registerFace)
        self.RegisterFaceButton.clicked.connect(self.check_password)


        self.DisplayReportButton = QPushButton(self)
        self.DisplayReportButton.setText("Display Attendance Report")
        self.DisplayReportButton.setGeometry(900, 180, 240, 240)
        self.DisplayReportButton.clicked.connect(self.display_attendance_report)
        self.DisplayReportButton.setStyleSheet(
            "QPushButton { border-radius: 20px; background-color: grey; color: white; font-size: 14px; border: 3px solid black; transition: background-color 0.3s;}"
            "QPushButton:hover { background-color: gold; color: black; font-size: 18px; border: 3px solid black;}"
        )

        # Connect the button click signal to the registerMultipleSchedules method
        self.RegisterMultipleSchedulesButton = QPushButton(self)
        self.RegisterMultipleSchedulesButton.setText("Register Multiple Schedules")
        self.RegisterMultipleSchedulesButton.setGeometry(900, 430, 240, 240)
        self.RegisterMultipleSchedulesButton.clicked.connect(self.registerMultipleSchedules)
        self.RegisterMultipleSchedulesButton.setStyleSheet(
            "QPushButton { border-radius: 20px; background-color: grey; color: white; font-size: 14px; border: 3px solid black; transition: background-color 0.3s;}"
            "QPushButton:hover { background-color: gold; color: black; font-size: 18px; border: 3px solid black;}"
        )

        # Add a registration button
        self.RegisterUserButton = QPushButton(self)
        self.RegisterUserButton.setText("Register User")
        self.RegisterUserButton.setGeometry(1200, 180, 240, 240)
        self.RegisterUserButton.clicked.connect(self.registerUser)
        self.RegisterUserButton.setStyleSheet(
            "QPushButton { border-radius: 20px; background-color: grey; color: white; font-size: 14px; border: 3px solid black; transition: background-color 0.3s;}"
            "QPushButton:hover { background-color: gold; color: black; font-size: 18px; border: 3px solid black;}"
        )

        self.PrintReportButton = QPushButton(self)
        self.PrintReportButton.setText("Print Specific Date of Attendance Report")
        self.PrintReportButton.setGeometry(1200, 430, 240, 240)
        self.PrintReportButton.clicked.connect(self.print_attendance_report)
        self.PrintReportButton.setStyleSheet(
            "QPushButton { border-radius: 20px; background-color: grey; color: white; font-size: 14px; border: 3px solid black; transition: background-color 0.3s;}"
            "QPushButton:hover { background-color: gold; color: black; font-size: 18px; border: 3px solid black;}"
        )

        self.PrintReportButton = QPushButton(self)
        self.PrintReportButton.setText("Print All Attendance Report")
        self.PrintReportButton.setGeometry(1500, 430, 240, 240)
        self.PrintReportButton.clicked.connect(self.print_all_attendance_report)
        self.PrintReportButton.setStyleSheet(
            "QPushButton { border-radius: 20px; background-color: grey; color: white; font-size: 14px; border: 3px solid black; transition: background-color 0.3s;}"
            "QPushButton:hover { background-color: gold; color: black; font-size: 18px; border: 3px solid black;}"
        )

        self.showFullScreen()

    def goBack(self):
        self.close()
        self.new_window = menu_Bar()
        self.new_window.show()

    def print_all_attendance_report(self):
        # Connect to the database
        connection = sqlite3.connect("attendance_database.db")
        cursor = connection.cursor()

        # Retrieve all attendance data from the database
        cursor.execute('''
            SELECT name, datetime, status, subject, classroom_number, start_time, subject_code
            FROM attendance
        ''')

        all_attendance_data = cursor.fetchall()

        connection.close()

        # Get the name of the user for whom the attendance report should be displayed
        user_name, okPressed = QInputDialog.getText(self, "Search Attendance",
                                                    "Enter the name to search attendance: (if all data want to be printed leave the input empty)")

        if okPressed:
            if user_name:
                # Filter attendance data for the specific user
                specific_user_data = [row for row in all_attendance_data if row[0] == user_name]

                if specific_user_data:
                    # Create a formatted table for the specific user
                    report_text = f"Attendance Report for {user_name}\n\n"
                    report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(
                        "Name", "Date/Time", "Status", "Subject", "Classroom Number", "Start Time", "Subject Code"
                    )

                    for row in specific_user_data:
                        report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(*row)

                    self.print_or_save_all_report(report_text)
                else:
                    QMessageBox.warning(self, "Data Not Found", f"Attendance data for {user_name} not found.")
            else:
                # User didn't specify a particular name, print all data
                all_report_text = "Attendance Report for All Users\n\n"
                all_report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(
                    "Name", "Date/Time", "Status", "Subject", "Classroom Number", "Start Time", "Subject Code"
                )

                for row in all_attendance_data:
                    all_report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(*row)

                self.print_or_save_all_report(all_report_text)
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid name.")

    def print_or_save_all_report(self, report_text):
        text_edit = QTextEdit()
        text_edit.setPlainText(report_text)

        # Create a print dialog
        print_dialog = QPrintDialog(self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            # User selected to print
            printer = print_dialog.printer()
            text_edit.print_(printer)
            print("Printing completed.")
        else:
            # User canceled the print dialog
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf);;All Files (*)")

            if file_path:
                # Save the PDF using QPrinter
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)

                text_edit.print_(printer)

                print("PDF saved successfully.")
            else:
                # User canceled the save dialog
                print("Operation canceled.")
    def print_attendance_report(self):
        # Connect to the database
        connection = sqlite3.connect("attendance_database.db")
        cursor = connection.cursor()

        # Retrieve all attendance data from the database
        cursor.execute('''
            SELECT name, datetime, status, subject, classroom_number, start_time, subject_code
            FROM attendance
        ''')

        all_attendance_data = cursor.fetchall()

        connection.close()

        # Get the name of the user for whom the attendance report should be displayed
        user_name, okPressed = QInputDialog.getText(self, "Search Attendance",
                                                    "Enter the name to search attendance: (if all data want to be printed leave the input empty)")

        if okPressed:
            if user_name:
                # Filter attendance data for the specific user
                specific_user_data = [row for row in all_attendance_data if row[0] == user_name]

                # Get the date range from the user
                start_date, ok_start = QInputDialog.getText(self, "Enter Start Date",
                                                            "Enter the start date (MM/DD/YY):")
                end_date, ok_end = QInputDialog.getText(self, "Enter End Date", "Enter the end date (MM/DD/YY):")

                if ok_start and ok_end:
                    # Convert the input date range to the format of the data in the database (without the time)
                    start_date = datetime.datetime.strptime(start_date, "%m/%d/%y").strftime("%y/%m/%d")
                    end_date = datetime.datetime.strptime(end_date, "%m/%d/%y").strftime("%y/%m/%d")

                    # Filter attendance data based on the date range
                    specific_user_data = [row for row in specific_user_data if start_date <= row[1][:8] <= end_date]

                if specific_user_data:
                    # Create a formatted table for the specific user
                    report_text = f"Attendance Report for {user_name}\n\n"
                    report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(
                        "Name", "Date/Time", "Status", "Subject", "Classroom Number", "Start Time", "Subject Code"
                    )

                    for row in specific_user_data:
                        report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(*row)

                    self.print_or_save_report(report_text)
                else:
                    QMessageBox.warning(self, "Data Not Found", f"Attendance data for {user_name} not found.")
            else:
                # User didn't specify a particular name, print all data
                all_report_text = "Attendance Report for All Users\n\n"
                all_report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(
                    "Name", "Date/Time", "Status", "Subject", "Classroom Number", "Start Time", "Subject Code"
                )

                # Get the date range from the user
                start_date, ok_start = QInputDialog.getText(self, "Enter Start Date",
                                                            "Enter the start date (MM/DD/YY):")
                end_date, ok_end = QInputDialog.getText(self, "Enter End Date", "Enter the end date (MM/DD/YY):")

                if ok_start and ok_end:
                    # Convert the input date range to the format of the data in the database (without the time)
                    start_date = datetime.datetime.strptime(start_date, "%m/%d/%y").strftime("%y/%m/%d")
                    end_date = datetime.datetime.strptime(end_date, "%m/%d/%y").strftime("%y/%m/%d")

                    # Filter attendance data based on the date range
                    all_attendance_data = [row for row in all_attendance_data if start_date <= row[1][:8] <= end_date]

                for row in all_attendance_data:
                    all_report_text += "{:<20} {:<30} {:<15} {:<35} {:<20} {:<20} {:<20}\n".format(*row)

                self.print_or_save_report(all_report_text)
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid name.")
    def print_or_save_report(self, report_text):
        text_edit = QTextEdit()
        text_edit.setPlainText(report_text)

        # Create a print dialog
        print_dialog = QPrintDialog(self)
        if print_dialog.exec_() == QPrintDialog.Accepted:
            # User selected to print
            printer = print_dialog.printer()
            text_edit.print_(printer)
            print("Printing completed.")
        else:
            # User canceled the print dialog
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf);;All Files (*)")

            if file_path:
                # Save the PDF using QPrinter
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)

                text_edit.print_(printer)

                print("PDF saved successfully.")
            else:
                # User canceled the save dialog
                print("Operation canceled.")
    def registerUser(self):
        # Display the registration dialog
        register_dialog = RegisterUserDialog()
        if register_dialog.exec_() == QDialog.Accepted:
            username, password = register_dialog.getUserInfo()

            # Save the user information in the SQLite database
            connection = sqlite3.connect("attendance_database.db")
            cursor = connection.cursor()

            # Insert user information into the users table
            cursor.execute('''
                INSERT INTO users (username, password)
                VALUES (?, ?)
            ''', (username, password))

            connection.commit()
            connection.close()

            # Show a message box indicating successful registration
            QMessageBox.information(self, "Registration Successful", f"User {username} registered successfully.")
    def registerMultipleSchedules(self):
        try:
            # Get the entered password
            entered_password = self.password_input.text()

            # Check if the password is correct
            if entered_password == "perpetual":
                # Password is correct, proceed with registering multiple schedules

                # Get the number of schedules to register
                register_dialog = RegisterMultipleSchedulesDialog()
                num_schedules = register_dialog.getScheduleInformation()

                if num_schedules:
                    # Save the schedule information in the database
                    connection = sqlite3.connect("attendance_database.db")
                    cursor = connection.cursor()

                    for schedule_info in num_schedules:
                        cursor.execute('''
                             INSERT INTO schedule (subject_code, professor_id, day, subject, start_time, end_time, 
                             classroom_number)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                         ''', schedule_info)

                    connection.commit()
                    connection.close()

                    QMessageBox.information(self, "Registration Success",
                                            f"{len(num_schedules)} schedules registered successfully!")
                else:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a valid number of schedules.")
            else:
                # Password is incorrect, show a message
                QMessageBox.warning(self, "Incorrect Password", "The entered password is incorrect.")
        except Exception as e:
            print(f"Exception in registerMultipleSchedules: {e}")

    def display_attendance_report(self):
        # Get the name of the user for whom the attendance report should be displayed
        user_name, okPressed = QInputDialog.getText(self, "Search Attendance", "Enter the name to search attendance:")

        if okPressed and user_name:
            # Connect to the database
            connection = sqlite3.connect("attendance_database.db")
            cursor = connection.cursor()

            # Retrieve attendance data from the database
            cursor.execute('''
                SELECT name, datetime, status, subject, classroom_number, start_time, subject_code
                FROM attendance
                WHERE name = ?
            ''', (user_name,))

            attendance_data = cursor.fetchall()

            connection.close()

            # Display the attendance report
            if attendance_data:
                report_form = AttendanceReportForm(attendance_data)
                report_form.exec_()
            else:
                QMessageBox.warning(self, "Data Not Found", f"Attendance data for {user_name} not found.")
        else:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid name.")

    def update_time(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()

        time_str = current_time.toString("hh:mm AP")
        date_str = current_date.toString('ddd dd MMMM yyyy')

        self.Time_Label.setText(time_str)
        self.Date_Label.setText(date_str)
    @pyqtSlot()
    def startVideo(self, camera_name):
        """
        :param camera_name: link of camera or usb camera
        :return:
        """
        if len(camera_name) == 1:
            self.capture = cv2.VideoCapture(int(camera_name), cv2.CAP_DSHOW)
        else:
            self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)  # Create Timer
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)

        # known face encoding and known face name list
        self.class_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []

        # Retrieve face encodings from the database
        connection = sqlite3.connect("attendance_database.db")
        cursor = connection.cursor()
        cursor.execute('SELECT name, encoding FROM face_encodings')
        face_encodings_data = cursor.fetchall()
        connection.close()

        for name, encoding_json in face_encodings_data:
            # Convert JSON string to numpy array for encoding
            encoding = np.array(json.loads(encoding_json))
            self.encode_list.append(encoding)
            self.class_names.append(name)

        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(40)  # emit the timeout() signal at x=40ms

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: frame from camera
        :param encode_list_known: known face encoding
        :param class_names: known face names
        :return:
        """
        # csv
        def initialize_schedule():
            connection = sqlite3.connect("attendance_database.db")
            cursor = connection.cursor()

            # Create the schedule table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER,
                    day TEXT,
                    subject TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    classroom_number TEXT,
                    subject_code TEXT
                )
            ''')

            # Create the faces table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    image_path TEXT
                )
            ''')
            connection.commit()
            connection.close()

        # Call this method when initializing the application
        initialize_schedule()
        # csv
        def initialize_database():
            connection = sqlite3.connect("attendance_database.db")
            cursor = connection.cursor()

            # Create the table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    datetime TEXT,
                    status TEXT,
                    subject TEXT,
                    classroom_number TEXT,
                    start_time TEXT,
                    subject_code TEXT
                )
            ''')

            connection.commit()
            connection.close()


        # csv

        def mark_attendance(name, confidence):
            """
            :param name: detected face known or unknown one
            :param confidence: confidence level for the detected face
            :return:
            """
            # Modify the file name to include the person's name
            file_name = f'Attendance_{name}.csv'

            # Check if the file exists
            file_exists = os.path.exists(file_name)

            with open(file_name, 'a') as f:
                writer = csv.writer(f)

                # If the file does not exist, write the header
                if not file_exists:
                    writer.writerow(['Name', 'Date/Time', 'Status'])

                if self.ClockInButton.isChecked():
                    self.ClockInButton.setEnabled(False)
                    if name != 'unknown' and confidence >= 0.6:  # Adjust the confidence threshold as needed
                        buttonReply = QMessageBox.question(self, 'Welcome ' + name, 'Are you Clocking In?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            writer.writerow([name, date_time_string, 'Clock In'])
                            self.ClockInButton.setChecked(False)

                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked In')
                            self.HoursLabel.setText('Measuring')
                            self.MinLabel.setText('')

                            # self.CalculateElapse(name)
                            # print('Yes clicked and detected')
                            self.Time1 = datetime.datetime.now()
                            # print(self.Time1)
                            self.ClockInButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                        self.ClockInButton.setEnabled(True)

                elif self.ClockOutButton.isChecked():
                    self.ClockOutButton.setEnabled(False)
                    if name != 'unknown' and confidence >= 0.6:  # Adjust the confidence threshold as needed
                        buttonReply = QMessageBox.question(self, 'Cheers ' + name, 'Are you Clocking Out?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            writer.writerow([name, date_time_string, 'Clock Out'])
                            self.ClockOutButton.setChecked(False)


                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked Out')
                            self.Time2 = datetime.datetime.now()
                            # print(self.Time2)

                            self.ElapseList(name)
                            self.TimeList2.append(datetime.datetime.now())
                            CheckInTime = self.TimeList1[-1]
                            CheckOutTime = self.TimeList2[-1]
                            self.ElapseHours = (CheckOutTime - CheckInTime)
                            self.MinLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                            self.HoursLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')
                            self.ClockOutButton.setEnabled(True)
                        else:
                            print('Not clicked.')
                        self.ClockOutButton.setEnabled(True)

        # face recognition
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)
        # count = 0
        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)
            confidence = 1 - face_dis[best_match_index]

            if confidence >= 0.6:  # Adjust the confidence threshold as needed
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, f"{name} ({confidence:.2f})", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                            (255, 255, 255), 1)
            mark_attendance(name, confidence)

        return frame

    def showdialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


    def ElapseList(self,name):
        attendance_file_path = f'Attendance_{name}.csv'

        with open(attendance_file_path, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 2

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()
            for row in csv_reader:
                for field in row:
                    if field in row:
                        if field == 'Clock In':
                            if row[0] == name:
                                #print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time1 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList1.append(Time1)
                        if field == 'Clock Out':
                            if row[0] == name:
                                #print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time2 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList2.append(Time2)
                                #print(Time2)


    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
        :param image: frame from camera
        :param encode_list: known face encoding list
        :param class_names: known face names
        :param window: number of window
        :return:
        """
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

    @pyqtSlot()
    def registerFace(self):
        """
        Register a new face.
        """
        try:
            # Check if the camera is running
            if hasattr(self, 'capture') and self.capture.isOpened():
                face_name, okPressed = QInputDialog.getText(self, "Register Face",
                                                            "Enter the name and ID to register face:")

                if okPressed and face_name:
                    # Capture a frame for face registration
                    ret, frame = self.capture.read()
                    if ret:
                        # Detect face in the frame
                        face_locations = face_recognition.face_locations(frame)
                        if face_locations:
                            # Assuming only one face is present in the frame for registration
                            top, right, bottom, left = face_locations[0]
                            face_image = frame[top:bottom, left:right]

                            # Save the face image with the provided name
                            path = f'ImagesAttendance/{face_name}.jpg'
                            cv2.imwrite(path, cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))

                            # Update the known face encoding and name list
                            img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
                            encode = face_recognition.face_encodings(img)[0]

                            # Convert the encoding to a JSON string for storage
                            encoding_json = json.dumps(encode.tolist())

                            # Save the face information in the database
                            connection = sqlite3.connect("attendance_database.db")
                            cursor = connection.cursor()

                            # Save the face image path in the database
                            cursor.execute('''
                                 INSERT INTO faces (name, image_path)
                                 VALUES (?, ?)
                             ''', (face_name, path))

                            # Save the face encoding in the database as a string
                            cursor.execute('''
                                 INSERT INTO face_encodings (name, encoding)
                                 VALUES (?, ?)
                             ''', (face_name, encoding_json))

                            connection.commit()
                            connection.close()

                            # Update the known face encoding and name list
                            self.encode_list.append(encode)
                            self.class_names.append(face_name)

                            QMessageBox.information(self, "Registration Success",
                                                    f"Face {face_name} registered successfully!")

                        else:
                            QMessageBox.warning(self, "Registration Failed", "No face detected for registration.")
                    else:
                        QMessageBox.warning(self, "Capture Error", "Failed to capture frame for registration.")
            else:
                QMessageBox.warning(self, "Camera not started", "Please start the camera before registering a face.")
        except Exception as e:
            print(f"Exception in registerFace: {e}")

    def check_password(self):
        # Define your password (change this to your actual password)
        correct_password = "perpetual"

        # Get the entered password
        entered_password = self.password_input.text()

        if entered_password == correct_password:
            # Password is correct, proceed with face registration
            self.registerFace()
        else:
            # Password is incorrect, show a message
            QMessageBox.warning(self, "Incorrect Password", "The entered password is incorrect.")

class AttendanceReportForm(QDialog):
    def __init__(self, attendance_data):
        super(AttendanceReportForm, self).__init__()

        self.setWindowTitle("Attendance Report")
        self.setGeometry(100, 100, 900, 600)

        # Create a QTableWidget for displaying attendance data
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(10, 60, 880, 500)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(['Name', 'Date/Time', 'Status', 'Subject', 'Classroom Number',
                                                    'Subject Time', 'Subject Code'])

        # Add a search box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Enter search term")
        self.search_box.setGeometry(10, 10, 200, 30)

        # Add a search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setGeometry(220, 10, 80, 30)
        self.search_button.clicked.connect(self.search_attendance)

        # Populate the table with attendance data
        self.original_attendance_data = attendance_data
        self.filtered_attendance_data = attendance_data
        self.populate_table(attendance_data)

    def populate_table(self, attendance_data):
        self.tableWidget.setRowCount(0)
        for row_num, row_data in enumerate(attendance_data):
            self.tableWidget.insertRow(row_num)
            for col_num, col_data in enumerate(row_data):
                item = QTableWidgetItem(col_data)
                self.tableWidget.setItem(row_num, col_num, item)

    def search_attendance(self):
        search_term = self.search_box.text().strip().lower()
        if search_term:
            # Filter the attendance data based on the search term
            filtered_data = [row for row in self.original_attendance_data if
                             any(search_term in col.lower() for col in row)]
            self.filtered_attendance_data = filtered_data
            self.populate_table(filtered_data)
        else:
            # If the search term is empty, display the original data
            self.filtered_attendance_data = self.original_attendance_data
            self.populate_table(self.original_attendance_data)
class RegisterMultipleSchedulesDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Register Multiple Schedules")

        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        self.num_schedules_label = QLabel("Enter the number of schedules to register:")
        self.num_schedules_input = QLineEdit(self)
        self.form_layout.addRow(self.num_schedules_label, self.num_schedules_input)

        self.layout.addLayout(self.form_layout)

        self.button_box = self.createButtonBox()
        self.layout.addWidget(self.button_box)

    def createButtonBox(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box

    def getScheduleInformation(self):
        num_schedules = int(self.num_schedules_input.text()) if self.exec_() == QDialog.Accepted else 0

        schedules = []

        for _ in range(num_schedules):
            schedule_dialog = ScheduleInputDialog(self)
            if schedule_dialog.exec_() == QDialog.Accepted:
                schedule_info = schedule_dialog.getScheduleInfo()
                schedules.append(schedule_info)

        return schedules


class ScheduleInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Schedule Information")

        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        self.subject_code_input = QLineEdit(self)
        self.professor_id_input = QLineEdit(self)
        self.day_input = QLineEdit(self)
        self.subject_input = QLineEdit(self)
        self.start_time_input = QLineEdit(self)
        self.end_time_input = QLineEdit(self)
        self.classroom_number_input = QLineEdit(self)

        self.form_layout.addRow("Subject Code:", self.subject_code_input)
        self.form_layout.addRow("Professor Name and ID:", self.professor_id_input)
        self.form_layout.addRow("Day:", self.day_input)
        self.form_layout.addRow("Subject:", self.subject_input)
        self.form_layout.addRow("Start Time (HH:MM):", self.start_time_input)
        self.form_layout.addRow("End Time (HH:MM):", self.end_time_input)
        self.form_layout.addRow("Classroom Number:", self.classroom_number_input)

        self.layout.addLayout(self.form_layout)

        self.button_box = self.createButtonBox()
        self.layout.addWidget(self.button_box)

    def createButtonBox(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        return button_box

    def getScheduleInfo(self):
        return (
            self.subject_code_input.text(),
            self.professor_id_input.text(),
            self.day_input.text(),
            self.subject_input.text(),
            self.start_time_input.text(),
            self.end_time_input.text(),
            self.classroom_number_input.text(),
        )
class RegisterUserDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Register User")

        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        self.form_layout.addRow("Username:", self.username_input)
        self.form_layout.addRow("Password:", self.password_input)

        self.layout.addLayout(self.form_layout)

        self.button_box = self.createButtonBox()
        self.layout.addWidget(self.button_box)

    def createButtonBox(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)


        return button_box

    def getUserInfo(self):
        return self.username_input.text(), self.password_input.text()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWin = Ui_Admin()
    mainWin.show()
    sys.exit(app.exec_())