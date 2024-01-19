from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QTextBrowser, QPushButton
from PyQt5.QtCore import Qt
import csv
import os

class ReportDialog(QDialog):
    def __init__(self, attendance_data):
        super(ReportDialog, self).__init__()

        self.setWindowTitle("Attendance Report")
        self.setGeometry(100, 100, 600, 400)

        self.attendance_data = attendance_data

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        report_label = QLabel("Attendance Report:")
        layout.addWidget(report_label)

        self.text_browser = QTextBrowser()
        layout.addWidget(self.text_browser)

        generate_report_button = QPushButton("Generate Report")
        generate_report_button.clicked.connect(self.generate_report)
        layout.addWidget(generate_report_button)

        self.setLayout(layout)

    def generate_report(self):
        # Generate the report content
        report_content = self.generate_report_content()

        # Display the report in the QTextBrowser
        self.text_browser.setPlainText(report_content)

        # Save the report to a CSV file
        self.save_report_to_csv(report_content)

    def generate_report_content(self):
        report_content = "Name,Date/Time,Status\n"

        for entry in self.attendance_data:
            name, date_time, status = entry
            report_content += f"{name},{date_time},{status}\n"

        return report_content

    def save_report_to_csv(self, report_content):
        try:
            path = "AttendanceReport.csv"

            with open(path, "w", newline='') as csv_file:
                csv_file.write(report_content)

            print(f"Report saved to {path}")
        except Exception as e:
            print(f"Error saving report: {e}")