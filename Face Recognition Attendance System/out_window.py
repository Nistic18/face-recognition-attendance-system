from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, pyqtSignal
from PyQt5.QtWidgets import QDialog, QMessageBox
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv
import sqlite3
from PyQt5.QtCore import QTime
from menu import menu_Bar
import json

class Ui_OutputDialog(QDialog):
    closed = pyqtSignal()
    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("outputwindow.ui", self)

        # Update time
        self.update_time()  # Initial update
        self.timer_time = QTimer(self)  # Create Timer for time update
        self.timer_time.timeout.connect(self.update_time)  # Connect timeout to the update_time function
        self.timer_time.start(1000)  # Update time every 1000 milliseconds (1 second)
        self.image = None

        self.backButton.clicked.connect(self.goBack)

    def goBack(self):
        self.close()
        self.new_window = menu_Bar()
        self.new_window.show()
    def get_schedule_info(self, professor_id):
        """
        Retrieve schedule information for the given professor_id.
        """
        connection = sqlite3.connect("attendance_database.db")
        cursor = connection.cursor()

        # Retrieve schedule data from the database
        cursor.execute('''
            SELECT subject, start_time, classroom_number, subject_code
            FROM schedule
            WHERE professor_id = ? AND day = ? AND
                  start_time <= ? AND end_time >= ?
        ''', (professor_id, datetime.datetime.now().strftime("%A"),
              datetime.datetime.now().strftime("%H:%M"),
              datetime.datetime.now().strftime("%H:%M")))
        schedule_data = cursor.fetchone()

        connection.close()

        return schedule_data
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

        # Show the window in full-screen mode when the video starts
        self.showFullScreen()

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: frame from camera
        :param encode_list_known: known face encoding
        :param class_names: known face names
        :return:
        """
        # Add a new method to initialize the schedule table in your database
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

        def mark_attendance(name, confidence, subject, classroom_number, start_time, subject_code):
            """
            :param name: detected face known or unknown one
            :param confidence: confidence level for the detected face
            :return:
            """
            if self.ClockInButton.isChecked():
                # Initialize the database
                initialize_database()

                # Connect to the database
                connection = sqlite3.connect("attendance_database.db")
                cursor = connection.cursor()
                connection.commit()

                # Check the user's schedule if they are clocked in
                cursor.execute('''
                    SELECT subject, start_time, end_time
                    FROM schedule
                    WHERE professor_id = ? AND day = ? AND
                          start_time <= ? AND end_time >= ?
                ''', (name, datetime.datetime.now().strftime("%A"),
                      datetime.datetime.now().strftime("%H:%M"),
                      datetime.datetime.now().strftime("%H:%M")))
                schedule_data = cursor.fetchone()

                if schedule_data:
                    # Schedule data is available
                    subject, start_time, end_time = schedule_data

                    # Parse the start and end times to datetime objects
                    start_datetime = datetime.datetime.strptime(start_time, '%H:%M')
                    end_datetime = datetime.datetime.strptime(end_time, '%H:%M')

                    # Calculate a datetime object representing 30 minutes before the scheduled start time
                    buffer_time = datetime.timedelta(minutes=30)
                    buffer_start_time = start_datetime - buffer_time

                    # Get the current time
                    current_time = datetime.datetime.now().time()

                    # Check if the current time is within the scheduled time range
                    if buffer_start_time.time() <= current_time <= end_datetime.time():
                        message_text = f"You are currently scheduled for {subject} from {start_time} to {end_time}."

                        # Show the message in a QMessageBox
                        QMessageBox.information(self, "Schedule Information", message_text)

                        # Enable the ClockInButton
                        self.ClockInButton.setEnabled(True)
                    else:
                        # Show a message indicating the user is not currently within the scheduled time range
                        message_text = f"You are not within the scheduled time range for {subject} at the moment."

                        # Show the message in a QMessageBox
                        QMessageBox.warning(self, "Schedule Information", message_text)

                        # Disable the ClockInButton
                        self.ClockInButton.setEnabled(False)
                else:
                    message_text = "You are not scheduled at the moment."

                    # Show the message in a QMessageBox
                    QMessageBox.warning(self, "Schedule Information", message_text)

                    # Disable the ClockInButton
                    self.ClockInButton.setEnabled(False)

                connection.close()
            # Modify the file name to include the person's name
            file_name = f'Attendance_{name}.csv'

            # Check if the file exists
            file_exists = os.path.exists(file_name)

            with open(file_name, 'a') as f:
                writer = csv.writer(f)

                # If the file does not exist, write the header
                if not file_exists:
                    writer.writerow(['Name', 'Date/Time', 'Status', 'Subject', 'Classroom Number', 'Start Time', 'Subject Code'])

                if self.ClockInButton.isChecked():
                    self.ClockInButton.setEnabled(False)
                    if name != 'unknown' and confidence >= 0.6:  # Adjust the confidence threshold as needed
                        buttonReply = QMessageBox.question(self, 'Welcome ' + name, 'Are you Clocking In?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            writer.writerow([name, date_time_string, 'Clock In', subject, classroom_number, start_time,
                                             subject_code])
                            self.ClockInButton.setChecked(False)

                            # Get the schedule information
                            schedule_data = self.get_schedule_info(name)
                            if schedule_data:
                                subject, start_time, classroom_number, subject_code = schedule_data
                                # Update other QLabel widgets as needed
                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Clocked In')
                                self.HoursLabel.setText('Measuring')
                                self.MinLabel.setText('')
                                # Display information in the QLabel widgets
                                self.classroomnumber.setText(f"{classroom_number}")
                                self.subject.setText(f"{subject}")
                                self.subject_time.setText(f"{start_time}")
                                self.subject_code.setText(f"{subject_code}")
                            else:
                                # Handle the case when schedule data is not available
                                self.classroomnumber.setText("N/A")
                                self.subject.setText("N/A")
                                self.subject_time.setText("N/A")
                                self.NameLabel.setText(name)
                                self.StatusLabel.setText('Clocked In')
                                self.HoursLabel.setText('Measuring')
                                self.MinLabel.setText('')
                            # Initialize the database
                            initialize_database()

                            # Connect to the database
                            connection = sqlite3.connect("attendance_database.db")
                            cursor = connection.cursor()

                            # Insert data into the database
                            cursor.execute('''
                            INSERT INTO attendance (name, datetime, status, subject, classroom_number, start_time, 
                            subject_code)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (name, datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), 'Clock In',
                                self.subject.text(),
                                self.classroomnumber.text(), self.subject_time.text(), self.subject_code.text()))
                            connection.commit()
                            connection.close()
                            # self.CalculateElapse(name)
                            # print('Yes clicked and detected')
                            self.Time1 = datetime.datetime.now()
                            # print(self.Time1)
                        else:
                            print('Not clicked.')
                        self.ClockInButton.setChecked(False)  # Move this line outside the if-else block
                        self.ClockInButton.setEnabled(True)  # Move this line outside the if-else block

                elif self.ClockOutButton.isChecked():
                    self.ClockOutButton.setEnabled(False)
                    if name != 'unknown' and confidence >= 0.6:  # Adjust the confidence threshold as needed
                        buttonReply = QMessageBox.question(self, 'Cheers ' + name, 'Are you Clocking Out?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            writer.writerow([name, date_time_string, 'Clock Out', subject, classroom_number, start_time,
                                             subject_code])
                            self.ClockOutButton.setChecked(False)
                            self.NameLabel.setText(name)
                            self.StatusLabel.setText('Clocked Out')
                            self.Time2 = datetime.datetime.now()
                            # print(self.Time2)
                            # Initialize the database
                            initialize_database()

                            # Connect to the database
                            connection = sqlite3.connect("attendance_database.db")
                            cursor = connection.cursor()

                            # Insert data into the database
                            cursor.execute('''
                                INSERT INTO attendance (name, datetime, status, subject, classroom_number, start_time, 
                                subject_code)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                name, datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"), 'Clock Out', subject,
                                classroom_number,
                                start_time, subject_code))
                            connection.commit()
                            connection.close()
                            self.ElapseList(name)
                            self.TimeList2.append(datetime.datetime.now())
                            CheckInTime = self.TimeList1[-1]
                            CheckOutTime = self.TimeList2[-1]
                            self.ElapseHours = (CheckOutTime - CheckInTime)
                            self.MinLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                            self.HoursLabel.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')
                        else:
                            print('Not clicked.')
                        self.ClockOutButton.setChecked(False)  # Move this line outside the if-else block
                        self.ClockOutButton.setEnabled(True)  # Move this line outside the if-else block

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
            mark_attendance(name, confidence, self.subject.text(), self.classroomnumber.text(),
                            self.subject_time.text(), self.subject_code.text())

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
