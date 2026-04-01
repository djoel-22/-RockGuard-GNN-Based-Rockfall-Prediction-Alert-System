import sys
import requests
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QStackedWidget, QFrame, QMessageBox,
    QGraphicsDropShadowEffect, QProgressBar
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


# =========================================================
# 🔹 FIREBASE MANAGER (Backend)
# =========================================================
class FirebaseManager:
    def __init__(self):
        self.database_url = "https://ai-rockfall-alert-system-default-rtdb.firebaseio.com/"

    def get_all_users(self):
        try:
            r = requests.get(f"{self.database_url}/users.json")
            return r.json() if r.status_code == 200 else {}
        except Exception as e:
            print(f"[Firebase] Fetch error: {e}")
            return {}

    def create_user(self, user_data):
        try:
            user_id = user_data['email'].replace('@', '_').replace('.', '_')
            r = requests.put(f"{self.database_url}/users/{user_id}.json", json=user_data)
            return r.status_code == 200
        except Exception as e:
            print(f"[Firebase] Create error: {e}")
            return False

    def update_user_last_login(self, user_id):
        try:
            r = requests.patch(
                f"{self.database_url}/users/{user_id}/last_login.json",
                json=datetime.now().isoformat()
            )
            return r.status_code == 200
        except Exception as e:
            print(f"[Firebase] Last login error: {e}")
            return False

    def validate_user_credentials(self, email, password):
        try:
            users = self.get_all_users()
            user_id = email.replace('@', '_').replace('.', '_')
            if user_id in users:
                user = users[user_id]
                if user.get('password') == password:
                    return True, user
            return False, None
        except Exception as e:
            print(f"[Firebase] Validation error: {e}")
            return False, None

    def check_email_exists(self, email):
        try:
            users = self.get_all_users()
            user_id = email.replace('@', '_').replace('.', '_')
            return user_id in users
        except Exception as e:
            print(f"[Firebase] Check email error: {e}")
            return False


# =========================================================
# 🔹 MODERN LOGIN WINDOW
# =========================================================
class ModernLoginWindow(QMainWindow):
    login_success = pyqtSignal(str, str)  # username, user_id

    def __init__(self):
        super().__init__()
        self.firebase_manager = FirebaseManager()
        self.setWindowTitle("AI Rockfall Alert System - Login")
        self.resize(950, 620)
        self.setMinimumSize(800, 500)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A192F, stop:1 #112240);
            }
        """)

        # Main layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        layout.addWidget(self.create_left_panel(), 2)
        layout.addWidget(self.create_right_panel(), 3)

    # ----------------- UI Layout -----------------
    def create_left_panel(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 25, 47, 0.85);
                border-radius: 20px;
                color: white;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("ROCKFALL\nALERT SYSTEM")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00f9ff; letter-spacing: 2px;")

        subtitle = QLabel("AI-Powered Geological Monitoring")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #bdc3c7;")

        features = QLabel("• Real-time Monitoring\n• AI Threat Detection\n• Multi-Site Coverage\n• Instant Alerts")
        features.setFont(QFont("Segoe UI", 11))
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features.setStyleSheet("color: #bdc3c7; margin-top: 20px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(features)
        layout.addStretch()
        return frame

    def create_right_panel(self):
        frame = QWidget()
        vbox = QVBoxLayout(frame)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget = QStackedWidget()
        self.login_form = self.create_login_form()
        self.register_form = self.create_register_form()
        self.stacked_widget.addWidget(self.login_form)
        self.stacked_widget.addWidget(self.register_form)
        vbox.addWidget(self.stacked_widget)
        return frame

    # ----------------- Utility -----------------
    def create_input_field(self, label, placeholder, is_pwd=False):
        box = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #00f9ff; font-weight: bold; font-size: 13px;")
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(42)
        field.setStyleSheet("""
            QLineEdit {
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: 10px;
                padding-left: 10px;
                background: rgba(255,255,255,0.05);
                color: white;
            }
            QLineEdit:focus {
                border-color: #00f9ff;
                background: rgba(255,255,255,0.1);
            }
        """)
        if is_pwd:
            field.setEchoMode(QLineEdit.EchoMode.Password)
        box.addWidget(lbl)
        box.addWidget(field)
        return box, field

    def apply_card_style(self, frame):
        frame.setStyleSheet("""
            QFrame {
                background: rgba(20, 30, 50, 0.95);
                border-radius: 20px;
                padding: 35px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 180))
        frame.setGraphicsEffect(shadow)

    def create_progress_bar(self):
        bar = QProgressBar()
        bar.setFixedHeight(6)
        bar.setVisible(False)
        bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 3px; background: rgba(255,255,255,0.1); }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00f9ff, stop:1 #00aaff); border-radius: 3px; }
        """)
        return bar

    # ----------------- Login Form -----------------
    def create_login_form(self):
        frame = QFrame()
        self.apply_card_style(frame)
        vbox = QVBoxLayout(frame)
        title = QLabel("Welcome Back 👋")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        vbox.addWidget(title)

        email_box, self.login_email = self.create_input_field("Email", "you@example.com")
        pwd_box, self.login_pwd = self.create_input_field("Password", "Enter your password", True)
        vbox.addLayout(email_box)
        vbox.addLayout(pwd_box)

        self.login_progress = self.create_progress_bar()
        vbox.addWidget(self.login_progress)

        login_btn = QPushButton("🚀 Sign In")
        login_btn.setFixedHeight(45)
        login_btn.setStyleSheet(self.primary_button_style())
        login_btn.clicked.connect(self.authenticate_user)
        vbox.addWidget(login_btn)

        switch = QPushButton("📝 Don't have an account? Register")
        switch.setStyleSheet(self.link_button_style())
        switch.clicked.connect(lambda: self.switch_form("register"))
        vbox.addWidget(switch, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    # ----------------- Register Form -----------------
    def create_register_form(self):
        frame = QFrame()
        self.apply_card_style(frame)
        vbox = QVBoxLayout(frame)
        title = QLabel("Create Your Account ✨")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 15px;")
        vbox.addWidget(title)

        fields = []
        for text, placeholder, pwd in [
            ("Full Name", "John Doe", False),
            ("Email", "you@example.com", False),
            ("Organization", "Your Company", False),
            ("Password", "Enter password", True),
            ("Confirm Password", "Re-enter password", True),
        ]:
            box, field = self.create_input_field(text, placeholder, pwd)
            vbox.addLayout(box)
            fields.append(field)
        self.reg_name, self.reg_email, self.reg_org, self.reg_pwd, self.reg_conf = fields

        self.register_progress = self.create_progress_bar()
        vbox.addWidget(self.register_progress)

        reg_btn = QPushButton("🚀 Register")
        reg_btn.setFixedHeight(45)
        reg_btn.setStyleSheet(self.success_button_style())
        reg_btn.clicked.connect(self.register_user)
        vbox.addWidget(reg_btn)

        back = QPushButton("← Back to Login")
        back.setStyleSheet(self.link_button_style())
        back.clicked.connect(lambda: self.switch_form("login"))
        vbox.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)
        return frame

    # ----------------- Authentication Logic -----------------
    def authenticate_user(self):
        email = self.login_email.text().strip()
        pwd = self.login_pwd.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self, "Error", "Enter both email and password.")
            return
        self.show_loading(True, True)
        QTimer.singleShot(1000, lambda: self.process_auth(email, pwd))

    def process_auth(self, email, pwd):
        valid, data = self.firebase_manager.validate_user_credentials(email, pwd)
        if valid:
            user_id = email.replace('@', '_').replace('.', '_')
            self.firebase_manager.update_user_last_login(user_id)
            self.store_session(email, user_id, data.get('username', 'User'), data.get('role', 'user'))
            self.login_success.emit(data.get('username', 'User'), user_id)
            QMessageBox.information(self, "Success", f"Welcome back, {data.get('username', 'User')}!")
        else:
            QMessageBox.warning(self, "Error", "Invalid email or password.")
        self.show_loading(False, True)

    def register_user(self):
        name, email, org = self.reg_name.text().strip(), self.reg_email.text().strip(), self.reg_org.text().strip()
        pwd, conf = self.reg_pwd.text().strip(), self.reg_conf.text().strip()
        if not all([name, email, org, pwd, conf]):
            QMessageBox.warning(self, "Error", "All fields required.")
            return
        if pwd != conf:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        self.show_loading(True, False)
        QTimer.singleShot(1000, lambda: self.process_reg(name, email, org, pwd))

    def process_reg(self, name, email, org, pwd):
        if self.firebase_manager.check_email_exists(email):
            QMessageBox.warning(self, "Error", "User already exists.")
        else:
            data = {
                "username": name, "email": email, "password": pwd,
                "organization": org, "role": "admin",
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat()
            }
            if self.firebase_manager.create_user(data):
                user_id = email.replace('@', '_').replace('.', '_')
                self.store_session(email, user_id, name, "admin")
                self.login_success.emit(name, user_id)
                QMessageBox.information(self, "Success", "Account created successfully!")
                self.switch_form("login")
            else:
                QMessageBox.warning(self, "Error", "Registration failed.")
        self.show_loading(False, False)

    def store_session(self, email, user_id, username, role):
        data = {
            "email": email, "user_id": user_id, "username": username,
            "role": role, "logged_in": True, "login_time": datetime.now().isoformat()
        }
        with open("session.json", "w") as f:
            json.dump(data, f)

    # ----------------- Helpers -----------------
    def show_loading(self, show=True, login=True):
        if login:
            self.login_progress.setVisible(show)
        else:
            self.register_progress.setVisible(show)

    def switch_form(self, mode):
        self.stacked_widget.setCurrentIndex(0 if mode == "login" else 1)

    def primary_button_style(self):
        return """QPushButton{background:#00aaff;color:white;border-radius:10px;font-weight:bold;}
                  QPushButton:hover{background:#00caff;}"""

    def success_button_style(self):
        return """QPushButton{background:#00cc88;color:white;border-radius:10px;font-weight:bold;}
                  QPushButton:hover{background:#00e699;}"""

    def link_button_style(self):
        return """QPushButton{background:transparent;color:#00f9ff;text-decoration:underline;}
                  QPushButton:hover{color:#00e5ff;}"""


# =========================================================
# 🔹 INTEGRATION FUNCTIONS FOR APPWINDOW.PY
# =========================================================
def check_existing_session():
    """Check if user is already logged in - for appwindow.py integration"""
    import os
    import json
    try:
        if os.path.exists('session.json'):
            with open('session.json', 'r') as f:
                session_data = json.load(f)
                if session_data.get('logged_in'):
                    return session_data
    except:
        pass
    return None


def show_login_window():
    """Show the login window - for appwindow.py integration"""
    login_window = ModernLoginWindow()
    return login_window


def launch_main_app_from_login(login_window, main_app_class):
    """Launch main app after successful login - for appwindow.py integration"""
    def handle_login_success(username, user_id):
        login_window.close()
        main_app = main_app_class(username, user_id)
        main_app.show()
        return main_app
    
    login_window.login_success.connect(handle_login_success)
    login_window.show()
    return login_window


# =========================================================
# 🔹 STANDALONE LAUNCHER (for testing)
# =========================================================
if __name__ == "__main__":
    class DummyMainApp(QMainWindow):
        """Simple dummy main app for testing login integration"""
        def __init__(self, username, user_id):
            super().__init__()
            self.username = username
            self.user_id = user_id
            self.setWindowTitle(f"Rockfall App - Welcome {username}")
            self.setGeometry(100, 100, 800, 600)
            
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            title = QLabel(f"🚀 Welcome to Rockfall Alert System, {username}!")
            title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            title.setStyleSheet("color: #00f9ff; margin: 50px;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            info = QLabel(f"User ID: {user_id}\n\nThis is the main application window.\n\nYour login system is working perfectly!")
            info.setFont(QFont("Arial", 12))
            info.setStyleSheet("color: white; margin: 20px;")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info)
            
            logout_btn = QPushButton("🚪 Logout")
            logout_btn.setStyleSheet("""
                QPushButton {
                    background: #ff6b6b;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    margin: 20px;
                }
                QPushButton:hover {
                    background: #ff5252;
                }
            """)
            logout_btn.clicked.connect(self.logout)
            layout.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
        def logout(self):
            import os
            if os.path.exists("session.json"):
                os.remove("session.json")
            self.close()
            # Restart login
            app = QApplication.instance()
            login_win = ModernLoginWindow()
            login_win.login_success.connect(lambda u, i: DummyMainApp(u, i).show())
            login_win.show()

    def main():
        """Main entry point for standalone login testing"""
        app = QApplication(sys.argv)
        
        # Check for existing session
        session = check_existing_session()
        if session:
            # Auto-login if session exists
            main_app = DummyMainApp(
                session.get('username', 'User'), 
                session.get('user_id', '001')
            )
            main_app.show()
        else:
            # Show login window
            login_window = ModernLoginWindow()
            login_window.login_success.connect(
                lambda username, user_id: DummyMainApp(username, user_id).show()
            )
            login_window.show()
        
        sys.exit(app.exec())

    main()