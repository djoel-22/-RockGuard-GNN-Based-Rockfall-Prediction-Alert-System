# employee_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton,
    QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QComboBox, QScrollArea
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal
import pyrebase
import time

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "your-api-key",
    "authDomain": "ai-rockfall-alert-system.firebaseapp.com",
    "databaseURL": "https://ai-rockfall-alert-system-default-rtdb.firebaseio.com",
    "projectId": "ai-rockfall-alert-system",
    "storageBucket": "ai-rockfall-alert-system.appspot.com",
    "messagingSenderId": "your-sender-id",
    "appId": "your-app-id"
}

class AnimatedEmployeeMeter(QWidget):
    def __init__(self, title="Employee Count"):
        super().__init__()
        self.value = 0
        self.setMinimumSize(180, 180)
        
        # Use layout for better positioning
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #00f9ff;")
        layout.addWidget(self.title_label)
        
        self.count_label = QLabel("0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 24px;")
        self.count_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(self.count_label)

    def setValue(self, count):
        self.value = count
        self.count_label.setText(f"{count}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        size = min(rect.width(), rect.height()) - 20
        center = rect.center()

        painter.setPen(QPen(QColor(50, 50, 80), 6))
        painter.setBrush(QBrush(QColor(10, 10, 30)))
        painter.drawEllipse(center, size // 2, size // 2)

        # Calculate angle based on employee count (max 50 employees for visualization)
        max_employees = 50
        angle_span = min(360, int(360 * (self.value / max_employees)))
        grad_color = QColor.fromHsv(int(120 - (self.value * 1.2)), 255, 255)
        painter.setPen(QPen(grad_color, 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        arc_radius = size // 2 - 8
        painter.drawArc(center.x() - arc_radius, center.y() - arc_radius,
                        arc_radius * 2, arc_radius * 2, 90 * 16, -angle_span * 16)

        painter.setPen(QPen(QColor(0, 249, 255, 80), 3))
        painter.drawEllipse(center, size // 2 + 5, size // 2 + 5)

class EmployeeFormDialog(QDialog):
    def __init__(self, parent=None, employee_data=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.setWindowTitle("Add Employee" if not employee_data else "Edit Employee")
        self.setFixedSize(400, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(20,30,48,0.95);
                border-radius: 10px;
                border: 1px solid #1a2a3a;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Employee Details")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #00f9ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Form Fields
        self.fields = {}
        field_config = [
            ("name", "Full Name", "text"),
            ("phone", "Phone Number", "tel"),
            ("region", "Region", "combo"),
            ("department", "Department", "text"),
            ("position", "Position", "text")
        ]

        regions = ["North", "South", "East", "West", "Central", "Northeast", "Northwest", "Southeast", "Southwest"]

        for field_id, label, field_type in field_config:
            field_layout = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #ffffff;")
            field_layout.addWidget(lbl)

            if field_type == "combo":
                widget = QComboBox()
                widget.addItems(regions)
                widget.setStyleSheet("""
                    QComboBox {
                        background-color: rgba(30,40,60,0.8);
                        color: white;
                        border: 1px solid #2a3a4a;
                        border-radius: 5px;
                        padding: 10px;
                        font-size: 12px;
                        min-height: 20px;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 30px;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 5px solid #00f9ff;
                        width: 10px;
                        height: 10px;
                    }
                    QComboBox QAbstractItemView {
                        background-color: rgba(30,40,60,0.9);
                        color: white;
                        border: 1px solid #2a3a4a;
                        selection-background-color: #00f9ff;
                        selection-color: black;
                    }
                """)
            else:
                widget = QLineEdit()
                widget.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(30,40,60,0.8);
                        color: white;
                        border: 1px solid #2a3a4a;
                        border-radius: 5px;
                        padding: 10px;
                        font-size: 12px;
                        min-height: 20px;
                    }
                    QLineEdit:focus {
                        border: 1px solid #00f9ff;
                    }
                """)
                if field_type == "tel":
                    widget.setInputMask("+99 99999 99999;_")
                    widget.setPlaceholderText("+12 34567 89012")

            self.fields[field_id] = widget
            field_layout.addWidget(widget)
            layout.addLayout(field_layout)

        # Pre-fill data if editing
        if self.employee_data:
            self.fields['name'].setText(self.employee_data.get('name', ''))
            self.fields['phone'].setText(self.employee_data.get('phone', ''))
            self.fields['region'].setCurrentText(self.employee_data.get('region', ''))
            self.fields['department'].setText(self.employee_data.get('department', ''))
            self.fields['position'].setText(self.employee_data.get('position', ''))

        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Employee")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a2a2a;
                color: #00f9ff;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2a3a4a;
            }
        """)
        save_btn.clicked.connect(self.accept)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

    def get_employee_data(self):
        return {
            'name': self.fields['name'].text().strip(),
            'phone': self.fields['phone'].text().strip(),
            'region': self.fields['region'].currentText(),
            'department': self.fields['department'].text().strip(),
            'position': self.fields['position'].text().strip()
        }

class EmployeePage(QWidget):
    def __init__(self):
        super().__init__()
        self.firebase = self.initialize_firebase()
        self.employees = {}
        self.setup_ui()
        self.load_employees()

    def initialize_firebase(self):
        try:
            firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
            return firebase.database()
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            return None

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Left Panel - Employee List
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # Control Frame
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20,30,48,0.7);
                border-radius: 8px;
                border: 1px solid #1a2a3a;
            }
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(12, 12, 12, 12)

        # Add Employee Button
        self.add_btn = QPushButton("➕ Add Employee")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a2a2a;
                color: #00f9ff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2a3a4a;
            }
            QPushButton:pressed {
                background-color: #3a4a5a;
            }
        """)
        self.add_btn.clicked.connect(self.add_employee)

        # Refresh Button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a3a2a;
                color: #00ff99;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2a4a3a;
            }
            QPushButton:pressed {
                background-color: #3a5a4a;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_employees)

        control_layout.addWidget(self.add_btn)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addStretch()

        left_panel.addWidget(control_frame)

        # Employee Table
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20,30,48,0.7);
                border-radius: 8px;
                border: 1px solid #1a2a3a;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(8, 8, 8, 8)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(6)
        self.employee_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Region", "Department", "Actions"])
        
        # Better table styling and behavior
        self.employee_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.employee_table.horizontalHeader().setStretchLastSection(True)
        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.employee_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30,40,60,0.6);
                border: none;
                border-radius: 6px;
                color: white;
                gridline-color: #2a3a4a;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #2a3a4a;
            }
            QTableWidget::item:selected {
                background-color: rgba(0, 249, 255, 0.3);
                color: white;
            }
            QHeaderView::section {
                background-color: #1a2a3a;
                color: #00f9ff;
                font-weight: bold;
                padding: 8px;
                border: none;
                font-size: 11px;
            }
            QTableWidget::item:hover {
                background-color: rgba(0, 249, 255, 0.1);
            }
        """)
        
        # Set column widths
        self.employee_table.setColumnWidth(0, 80)   # ID
        self.employee_table.setColumnWidth(1, 150)  # Name
        self.employee_table.setColumnWidth(2, 120)  # Phone
        self.employee_table.setColumnWidth(3, 100)  # Region
        self.employee_table.setColumnWidth(4, 120)  # Department
        
        table_layout.addWidget(self.employee_table)
        left_panel.addWidget(table_frame, 1)

        layout.addLayout(left_panel, 2)

        # Right Panel - Stats and Info
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Employee Count Meter
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20,30,48,0.7);
                border-radius: 8px;
                border: 1px solid #1a2a3a;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        
        self.employee_meter = AnimatedEmployeeMeter("Total Employees")
        stats_layout.addWidget(self.employee_meter, alignment=Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(stats_frame)

        # Region Distribution
        region_frame = QFrame()
        region_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20,30,48,0.7);
                border-radius: 8px;
                border: 1px solid #1a2a3a;
            }
        """)
        region_layout = QVBoxLayout(region_frame)
        region_layout.setContentsMargins(12, 12, 12, 12)
        
        region_title = QLabel("Region Distribution")
        region_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        region_title.setStyleSheet("color: #00f9ff;")
        region_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        region_layout.addWidget(region_title)

        self.region_label = QLabel("No data available")
        self.region_label.setFont(QFont("Arial", 10))
        self.region_label.setStyleSheet("color: #ffffff; line-height: 1.4;")
        self.region_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.region_label.setWordWrap(True)
        region_layout.addWidget(self.region_label)

        right_panel.addWidget(region_frame)

        # Status Label
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20,30,48,0.7);
                border-radius: 8px;
                border: 1px solid #1a2a3a;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 12, 12, 12)
        
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #00ff99;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        right_panel.addWidget(status_frame)

        layout.addLayout(right_panel, 1)

    def add_employee(self):
        dialog = EmployeeFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            employee_data = dialog.get_employee_data()
            if self.validate_employee_data(employee_data):
                self.save_employee(employee_data)

    def validate_employee_data(self, data):
        if not data['name']:
            QMessageBox.warning(self, "Validation Error", "Please enter employee name")
            return False
        if not data['phone']:
            QMessageBox.warning(self, "Validation Error", "Please enter phone number")
            return False
        # Basic phone validation
        if len(data['phone'].replace(' ', '').replace('+', '')) < 10:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid phone number")
            return False
        return True

    def save_employee(self, employee_data):
        try:
            if self.firebase:
                self.status_label.setText("Saving employee...")
                self.status_label.setStyleSheet("color: #ffcc00;")
                
                # Generate unique ID
                employee_id = f"emp_{int(time.time() * 1000)}"
                
                # Save to Firebase
                self.firebase.child("employees").child(employee_id).set(employee_data)
                
                self.status_label.setText("Employee saved successfully!")
                self.status_label.setStyleSheet("color: #00ff99;")
                
                QMessageBox.information(self, "Success", "Employee added successfully!")
                self.load_employees()
            else:
                QMessageBox.warning(self, "Error", "Database connection failed")
        except Exception as e:
            self.status_label.setText("Error saving employee")
            self.status_label.setStyleSheet("color: #ff4444;")
            QMessageBox.critical(self, "Error", f"Failed to save employee: {str(e)}")

    def load_employees(self):
        try:
            self.status_label.setText("Loading employees...")
            self.status_label.setStyleSheet("color: #ffcc00;")
            
            if self.firebase:
                employees_data = self.firebase.child("employees").get().val()
                self.employees = employees_data or {}
                self.update_employee_table()
                self.update_stats()
                
                self.status_label.setText(f"Loaded {len(self.employees)} employees")
                self.status_label.setStyleSheet("color: #00ff99;")
            else:
                self.employees = {}
                self.status_label.setText("Database connection failed")
                self.status_label.setStyleSheet("color: #ff4444;")
        except Exception as e:
            print(f"Error loading employees: {e}")
            self.employees = {}
            self.status_label.setText("Error loading data")
            self.status_label.setStyleSheet("color: #ff4444;")

    def update_employee_table(self):
        self.employee_table.setRowCount(0)
        
        for emp_id, emp_data in self.employees.items():
            row = self.employee_table.rowCount()
            self.employee_table.insertRow(row)
            
            # Employee ID (shortened for display)
            short_id = emp_id[:8] + "..." if len(emp_id) > 8 else emp_id
            self.employee_table.setItem(row, 0, QTableWidgetItem(short_id))
            self.employee_table.item(row, 0).setToolTip(emp_id)  # Show full ID on hover
            
            # Employee Data
            self.employee_table.setItem(row, 1, QTableWidgetItem(emp_data.get('name', '')))
            self.employee_table.setItem(row, 2, QTableWidgetItem(emp_data.get('phone', '')))
            self.employee_table.setItem(row, 3, QTableWidgetItem(emp_data.get('region', '')))
            self.employee_table.setItem(row, 4, QTableWidgetItem(emp_data.get('department', '')))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a5c2a;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 6px;
                    font-size: 10px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background-color: #3a6c3a;
                }
            """)
            edit_btn.clicked.connect(lambda checked, eid=emp_id: self.edit_employee(eid))
            
            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5c2a2a;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 6px;
                    font-size: 10px;
                    min-width: 50px;
                }
                QPushButton:hover {
                    background-color: #6c3a3a;
                }
            """)
            delete_btn.clicked.connect(lambda checked, eid=emp_id: self.delete_employee(eid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.employee_table.setCellWidget(row, 5, actions_widget)
            self.employee_table.setRowHeight(row, 40)  # Consistent row height

    def update_stats(self):
        # Update employee count
        count = len(self.employees)
        self.employee_meter.setValue(count)
        
        # Update region distribution
        regions = {}
        for emp_data in self.employees.values():
            region = emp_data.get('region', 'Unknown')
            regions[region] = regions.get(region, 0) + 1
        
        if regions:
            region_text = ""
            for region, count in sorted(regions.items()):
                region_text += f"• {region}: {count} employee(s)\n"
            self.region_label.setText(region_text.strip())
        else:
            self.region_label.setText("No employees found")

    def edit_employee(self, employee_id):
        employee_data = self.employees.get(employee_id)
        if employee_data:
            dialog = EmployeeFormDialog(self, employee_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_employee_data()
                if self.validate_employee_data(updated_data):
                    self.update_employee(employee_id, updated_data)

    def update_employee(self, employee_id, employee_data):
        try:
            if self.firebase:
                self.status_label.setText("Updating employee...")
                self.status_label.setStyleSheet("color: #ffcc00;")
                
                self.firebase.child("employees").child(employee_id).update(employee_data)
                
                self.status_label.setText("Employee updated successfully!")
                self.status_label.setStyleSheet("color: #00ff99;")
                
                QMessageBox.information(self, "Success", "Employee updated successfully!")
                self.load_employees()
            else:
                QMessageBox.warning(self, "Error", "Database connection failed")
        except Exception as e:
            self.status_label.setText("Error updating employee")
            self.status_label.setStyleSheet("color: #ff4444;")
            QMessageBox.critical(self, "Error", f"Failed to update employee: {str(e)}")

    def delete_employee(self, employee_id):
        employee_name = self.employees.get(employee_id, {}).get('name', 'this employee')
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {employee_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.firebase:
                    self.status_label.setText("Deleting employee...")
                    self.status_label.setStyleSheet("color: #ffcc00;")
                    
                    self.firebase.child("employees").child(employee_id).remove()
                    
                    self.status_label.setText("Employee deleted successfully!")
                    self.status_label.setStyleSheet("color: #00ff99;")
                    
                    QMessageBox.information(self, "Success", "Employee deleted successfully!")
                    self.load_employees()
                else:
                    QMessageBox.warning(self, "Error", "Database connection failed")
            except Exception as e:
                self.status_label.setText("Error deleting employee")
                self.status_label.setStyleSheet("color: #ff4444;")
                QMessageBox.critical(self, "Error", f"Failed to delete employee: {str(e)}")