from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStackedWidget, QFrame, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QPointF
from ui.sidebar import CollapsibleSidebar
from ui.gauges import FuturisticGauge, AnimatedRiskMeter
from pages.home import HomePage
from pages.dashboard import DashboardPage
from pages.stress import StressAnalysisPage
from pages.simulation import SimulationPage
from pages.employee import EmployeePage
from core.alertsystem import AlertSystem
from core.toolbar import MainToolbar

# Import your login window
from pages.login import ModernLoginWindow


class RockfallApp(QMainWindow):
    def __init__(self, username="Admin", user_id="user_001"):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"⚡ Futuristic Rockfall Detection System - Welcome {self.username}")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a1520;
                color: white;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ✅ Integrated COC-style Toolbar (initially hidden)
        self.main_toolbar = MainToolbar(self)
        self.main_toolbar.toolDropped.connect(self.on_tool_dropped)
        self.main_toolbar.hide()  # Start hidden
        main_layout.addWidget(self.main_toolbar)

        # Content area
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = CollapsibleSidebar()
        content_layout.addWidget(self.sidebar)

        # Right content area
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #0f2027;")
        right_content_layout = QVBoxLayout(content_widget)
        right_content_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 30, 48, 0.7);
                border-bottom: 1px solid #1a2a3a;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.header_title = QLabel("Home")
        self.header_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.header_title.setStyleSheet("color: #00f9ff;")
        header_layout.addWidget(self.header_title)

        header_layout.addStretch(1)

        # Toolbar status (only show when toolbar is visible)
        self.toolbar_status = QLabel("")
        self.toolbar_status.setFont(QFont("Arial", 10))
        self.toolbar_status.setStyleSheet("color: #FFD700; background: transparent;")
        header_layout.addWidget(self.toolbar_status)

        header_layout.addStretch(1)

        # User info - Updated with actual username
        user_info = QLabel(f"👤 {self.username}")
        user_info.setStyleSheet("color: #00f9ff; font-weight: bold;")
        header_layout.addWidget(user_info)

        # Logout button
        logout_btn = QLabel("🚪")  # Using label as button for simplicity
        logout_btn.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                font-size: 16px;
                padding: 8px;
                background: rgba(255,107,107,0.1);
                border-radius: 5px;
            }
            QLabel:hover {
                background: rgba(255,107,107,0.2);
                cursor: pointer;
            }
        """)
        logout_btn.mousePressEvent = self.logout
        header_layout.addWidget(logout_btn)

        right_content_layout.addWidget(header)

        # Sensors + Risk meter
        self.risk_meter = AnimatedRiskMeter()
        self.sensors = {
            "Temperature_C": (FuturisticGauge("Temperature", "°C"), (0, 60)),
            "Humidity_%": (FuturisticGauge("Humidity", "%"), (0, 100)),
            "GroundPressure_kPa": (FuturisticGauge("Ground Pressure", "kPa"), (80, 120)),
            "Vibration_mm_s": (FuturisticGauge("Vibration", "mm/s"), (0, 10)),
            "CrackWidth_mm": (FuturisticGauge("Crack Width", "mm"), (0, 5)),
            "Rainfall_mm": (FuturisticGauge("Rainfall", "mm"), (0, 200))
        }

        # Pages - Pass user info if needed
        self.home_page = HomePage()
        self.dashboard_page = DashboardPage(self.sensors, self.risk_meter)
        self.stress_page = StressAnalysisPage()
        self.simulation_page = SimulationPage()
        self.employee_page = EmployeePage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.stress_page)
        self.stack.addWidget(self.simulation_page)
        self.stack.addWidget(self.employee_page)

        right_content_layout.addWidget(self.stack)
        content_layout.addWidget(content_widget, 1)
        main_layout.addWidget(content_area, 1)

        # Connect sidebar buttons
        self.sidebar.btn_home.clicked.connect(self.show_home)
        self.sidebar.btn_dashboard.clicked.connect(self.show_dashboard)
        self.sidebar.btn_stress.clicked.connect(self.show_stress)
        self.sidebar.btn_simulation.clicked.connect(self.show_simulation)
        self.sidebar.btn_employee.clicked.connect(self.show_employee)

        # ---------------- Alert System Integration ----------------
        self.alert_system = AlertSystem()
        self.alert_system.alert_triggered.connect(self.on_alert_triggered)
        self.alert_system.call_initiated.connect(self.on_call_initiated)
        self.alert_system.error_occurred.connect(self.on_alert_error)
        self.alert_system.start_monitoring()

    def logout(self, event=None):
        """Logout and return to login screen"""
        # Clear session
        import os
        if os.path.exists("session.json"):
            os.remove("session.json")
        
        # Stop monitoring
        if hasattr(self, 'alert_system'):
            self.alert_system.stop_monitoring()
        
        # Close current window and show login
        self.close()
        show_login_window()

    def on_tool_dropped(self, tool, global_position: QPointF):
        """Handle tool drop events from toolbar"""
        # Forward to simulation page if active
        if self.stack.currentWidget() == self.simulation_page:
            if hasattr(self.simulation_page, 'handle_tool_drop'):
                self.simulation_page.handle_tool_drop(tool, global_position)
        
        print(f"Tool {tool.tool_type} dropped at {global_position}")

    def show_toolbar(self):
        """Show and expand the toolbar"""
        self.main_toolbar.show()
        self.main_toolbar.expand_toolbar()
        self.toolbar_status.setText("🔧 Tools: Click ⚡ to open/close")

    def hide_toolbar(self):
        """Hide the toolbar"""
        self.main_toolbar.hide()
        self.toolbar_status.setText("")

    # ----------------- UI Pages -----------------
    def show_home(self):
        self.stack.setCurrentIndex(0)
        self.header_title.setText("Home")
        self.hide_toolbar()

    def show_dashboard(self):
        self.stack.setCurrentIndex(1)
        self.header_title.setText("Dashboard")
        self.hide_toolbar()

    def show_stress(self):
        self.stack.setCurrentIndex(2)
        self.header_title.setText("Real-time Monitoring")
        self.hide_toolbar()

    def show_simulation(self):
        self.stack.setCurrentIndex(3)
        self.header_title.setText("Simulation")
        self.show_toolbar()

    def show_employee(self):
        self.stack.setCurrentIndex(4)
        self.header_title.setText("Employee Management")
        self.hide_toolbar()

    # ----------------- Alert System Signal Handlers -----------------
    def on_alert_triggered(self, region, employee_name, risk):
        QMessageBox.information(
            self, "Alert Triggered",
            f"High risk detected in {region} ({risk}%)\nEmployee: {employee_name}"
        )

    def on_call_initiated(self, employee_name, phone, call_sid):
        print(f"[ALERT] Voice call sent to {employee_name} ({phone}), SID: {call_sid}")

    def on_alert_error(self, error_type, message):
        print(f"[ALERT ERROR] {error_type}: {message}")

    def closeEvent(self, event):
        """Cleanup on application close"""
        if hasattr(self, 'alert_system'):
            self.alert_system.stop_monitoring()
        event.accept()


# =========================================================
# 🔹 APPLICATION LAUNCHER & SESSION MANAGEMENT
# =========================================================
def check_existing_session():
    """Check if user is already logged in"""
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
    """Show the login window"""
    login_window = ModernLoginWindow()
    login_window.login_success.connect(launch_main_app)
    login_window.show()
    return login_window


def launch_main_app(username, user_id):
    """Launch the main RockfallApp after successful login"""
    main_app = RockfallApp(username, user_id)
    main_app.show()
    return main_app


def main():
    """Main application entry point"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Check for existing session
    session = check_existing_session()
    if session:
        # Auto-login if session exists
        main_app = RockfallApp(
            session.get('username', 'Admin'),
            session.get('user_id', 'user_001')
        )
        main_app.show()
    else:
        # Show login window
        login_window = show_login_window()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()