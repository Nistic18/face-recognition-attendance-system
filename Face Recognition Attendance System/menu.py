from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSlot
from PyQt5.uic import loadUi
import sys
import sqlite3
class LoginDialog(QDialog):
    def __init__(self, db_path="users.db"):
        super(LoginDialog, self).__init__()
        self.setWindowTitle("Login")
        self.setGeometry(800, 400, 300, 150)

        self.db_path = db_path

        layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)

        self.password_label = QLabel("Password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def try_login(self):
        entered_username = self.username_edit.text().strip()
        entered_password = self.password_edit.text().strip()


        # Authenticate against the SQLite database
        try:
            connection = sqlite3.connect("attendance_database.db")
            cursor = connection.cursor()

            query = "SELECT * FROM users WHERE username=? AND password=?"

            cursor.execute(query, (entered_username, entered_password))
            user = cursor.fetchone()

            if user:
                self.accept()  # Close the dialog if the login is successful
            else:
                # Display an error message for unsuccessful login
                print("Incorrect username or password")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            connection.close()
class menu_Bar(QWidget):
    def __init__(self):
        super(menu_Bar, self).__init__()
        loadUi("menu.ui", self)

        self.showFullScreen()

        self.userButton.clicked.connect(self.runSlot)
        self.adminButton.clicked.connect(self.runSlotAdmin)

        self._new_window_output = None
        self._new_window_admin = None
        self.Videocapture_ = None


    def refreshAll(self):
        self.Videocapture_ = "0"

    @pyqtSlot()
    def runSlot(self):
        from out_window import Ui_OutputDialog
        try:
            print("Clicked Run")
            self.refreshAll()
            print(self.Videocapture_)
            self._new_window_output = Ui_OutputDialog()
            self._new_window_output.show()
            self._new_window_output.startVideo(self.Videocapture_)
            print("Video Played")
        except Exception as e:
            print(f"Error in runSlot: {e}")

    def runSlotAdmin(self):
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
                #The login was successful, proceed to open the admin portal
            from adminportal import Ui_Admin
            try:
                print("Clicked Run")
                self.refreshAll()
                print(self.Videocapture_)
                self._new_window_admin = Ui_Admin()
                self._new_window_admin.show()
                self._new_window_admin.startVideo(self.Videocapture_)
                print("Video Played")
            except Exception as e:
                print(f"Error in runSlotAdmin: {e}")
    @pyqtSlot()
    def childClosed(self):
        sender = self.sender()
        if sender == self._new_window_output:
            self._new_window_output = None
        elif sender == self._new_window_admin:
            self._new_window_admin = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = menu_Bar()
    ui.show()
    sys.exit(app.exec_())
