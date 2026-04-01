# alert_system_rest.py - Fully debug-ready with parallel calls and boosted Twilio audio volume
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from twilio.rest import Client
import requests
from concurrent.futures import ThreadPoolExecutor

FIREBASE_DB_URL = "https://ai-rockfall-alert-system-default-rtdb.firebaseio.com/"
TWILIO_CONFIG = {
    "account_sid": "hidden",
    "auth_token": "hidden",
    "phone_number": "hidden"
}

# Default per-region messages
REGION_MESSAGES = {
    "Central": "Attention! Central region alert! Please evacuate fastly!",
    "East": "Attention! East region alert! Please evacuate fastly!",
    "North": "Attention! North region alert! Please evacuate fastly!",
    "Northeast": "Attention! Northeast region alert! Please evacuate fastly!",
    "Northwest": "Attention! Northwest region alert! Please evacuate fastly!",
    "South": "Attention! South region alert! Please evacuate fastly!",
    "Southeast": "Attention! Southeast region alert! Please evacuate fastly!",
    "Southwest": "Attention! Southwest region alert! Please evacuate fastly!",
    "West": "Attention! West region alert! Please evacuate fastly!",
    "Unknown": "Attention! Unknown region alert! Please evacuate fastly!"
}


class AlertSystem(QObject):
    alert_triggered = pyqtSignal(str, str, float)
    call_initiated = pyqtSignal(str, str, str)
    error_occurred = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        try:
            self.firebase = FirebaseManager(FIREBASE_DB_URL)
        except Exception as e:
            print(f"Failed to initialize FirebaseManager: {e}")
            self.firebase = None

        try:
            self.twilio = TwilioManager()
        except Exception as e:
            print(f"Failed to initialize TwilioManager: {e}")
            self.twilio = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alerts)
        self.is_monitoring = False
        self.sent_alerts = set()
        self.current_risks = {}

    def start_monitoring(self):
        try:
            self.is_monitoring = True
            self.timer.start(10000)
            print("Alert system started - monitoring every second")
        except Exception as e:
            print(f"Failed to start monitoring: {e}")

    def stop_monitoring(self):
        try:
            self.is_monitoring = False
            self.timer.stop()
            print("Alert system stopped")
        except Exception as e:
            print(f"Failed to stop monitoring: {e}")

    def check_alerts(self):
        if not self.is_monitoring:
            return
        if not self.firebase or not self.twilio:
            print("Alert system not fully initialized.")
            return
        try:
            regions = self.firebase.get_regions_data()
            if not regions:
                print("No regions data found in Firebase")
                return

            for region, data in regions.items():
                try:
                    risk = float(data.get('risk_percentage', 0))
                except (ValueError, TypeError) as e:
                    print(f"Error parsing risk for region {region}: {e}")
                    risk = 0

                self.current_risks[region] = risk
                print(f"[CHECK] Region: {region}, Risk: {risk}")

                if risk > 80 and region not in self.sent_alerts:
                    print(f"[ALERT] Triggering alert for {region} with risk {risk}")
                    try:
                        self.trigger_alert(region, risk)
                        self.sent_alerts.add(region)
                    except Exception as e:
                        print(f"Error triggering alert for {region}: {e}")

                elif risk <= 5 and region in self.sent_alerts:
                    print(f"[INFO] Risk for {region} dropped to {risk}%, resetting alert status")
                    self.sent_alerts.discard(region)

        except Exception as e:
            print(f"Error in check_alerts: {e}")
            self.error_occurred.emit("Check Alerts", str(e))

    def trigger_alert(self, region, risk):
        if not self.firebase or not self.twilio:
            print("Cannot trigger alert, managers not initialized.")
            return

        try:
            employees = self.firebase.get_employees_by_region(region)
            if not employees:
                print(f"No employees found for region: {region}")
                return
        except Exception as e:
            print(f"Failed to fetch employees for region {region}: {e}")
            return

        def call_employee(emp):
            name = emp.get('name', 'Employee')
            phone = emp.get('phone', '')
            if phone:
                print(f"Calling {name} at {phone} for region {region}")
                self.alert_triggered.emit(region, name, risk)
                try:
                    message = self.firebase.get_custom_message(region) or REGION_MESSAGES.get(region, f"Attention {name}, {region} is at risk! Please evacuate fastly!")
                    call_sid = self.twilio.make_call(phone, message)
                    if call_sid:
                        self.call_initiated.emit(name, phone, call_sid)
                except Exception as e:
                    print(f"Twilio call failed for {name} ({phone}): {e}")
            else:
                print(f"No phone number for employee {name} in region {region}")

        # Call employees in parallel (up to 4 simultaneous calls)
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(call_employee, employees)

    def reset_alerts(self):
        self.sent_alerts.clear()
        print("All alerts reset - system will send new alerts for high-risk regions")


class FirebaseManager:
    def __init__(self, db_url):
        self.db_url = db_url if db_url.endswith('/') else db_url + '/'
        print("FirebaseManager initialized.")

    def get_employees_by_region(self, region):
        try:
            url = f"{self.db_url}employees.json"
            params = {"orderBy": '"region"', "equalTo": f'"{region}"'}
            print(f"[DEBUG] Firebase request URL: {url} with params {params}")
            res = requests.get(url, params=params)
            res.raise_for_status()
            data = res.json()
            return list(data.values()) if data else []
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Firebase request failed for region {region}: {e}")
            return []

    def get_regions_data(self):
        try:
            url = f"{self.db_url}regions.json"
            res = requests.get(url)
            res.raise_for_status()
            return res.json() or {}
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Regions fetch failed: {e}")
            return {}

    def get_custom_message(self, region):
        try:
            url = f"{self.db_url}messages/{region}.json"
            res = requests.get(url)
            res.raise_for_status()
            msg = res.json()
            print(f"[DEBUG] Custom message for {region}: {msg}")
            return msg
        except Exception as e:
            print(f"[ERROR] Failed to fetch custom message for {region}: {e}")
            return None

    def log_alert(self, data):
        try:
            data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            url = f"{self.db_url}alert_logs.json"
            res = requests.post(url, json=data)
            res.raise_for_status()
            print(f"[DEBUG] Logged alert to Firebase: {data}")
        except Exception as e:
            print(f"[ERROR] Failed to log alert: {e}")


class TwilioManager:
    def __init__(self):
        try:
            self.client = Client(TWILIO_CONFIG["account_sid"], TWILIO_CONFIG["auth_token"])
            self.from_number = TWILIO_CONFIG["phone_number"]
            print("TwilioManager initialized.")
        except Exception as e:
            print(f"Failed to initialize TwilioManager: {e}")
            self.client = None

    def make_call(self, to, message):
        if not self.client:
            print("Twilio client not initialized.")
            return None
        try:
            # Use SSML for maximum volume (+6dB) and strong emphasis
            twiml = f'''
<Response>
    <Say voice="Polly.Matthew">
        <prosody volume="+6dB" rate="95%">
            <emphasis level="strong">Attention!</emphasis> {message}
        </prosody>
    </Say>
</Response>
'''
            call = self.client.calls.create(
                to=to,
                from_=self.from_number,
                twiml=twiml
            )
            FirebaseManager(FIREBASE_DB_URL).log_alert({
                "type": "voice_call",
                "phone_number": to,
                "message": message,
                "call_sid": call.sid
            })
            print(f"[DEBUG] Call initiated successfully: {call.sid}")
            return call.sid
        except Exception as e:
            print(f"[ERROR] Call failed for {to}: {e}")
            return None

