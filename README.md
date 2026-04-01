<div align="center">

# 🪨 RockGuard — GNN-Based Rockfall Prediction & Alert System

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/PyQt6-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white"/>
<img src="https://img.shields.io/badge/PyTorch-GNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
<img src="https://img.shields.io/badge/VTK-3D Rendering-blue?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Firebase-Realtime DB-FFCA28?style=for-the-badge&logo=firebase&logoColor=black"/>
<img src="https://img.shields.io/badge/Twilio-Alerts-F22F46?style=for-the-badge&logo=twilio&logoColor=white"/>

**A desktop-based, AI-assisted terrain monitoring system that analyzes 3D mesh stress patterns, simulates rockfall risk using a Graph Neural Network, and triggers emergency alerts with automated phone calls.**

> Built for mining, tunneling, construction, and geological hazard industries.

</div>

---

## 📸 Screenshots

| Real-Time Monitoring | Simulation Module |
|---|---|
| ![Realtime Monitoring](https://github.com/user-attachments/assets/1a69a4ad-2fd0-42e9-9f69-7a37f7e747fd) | ![Simulation](https://github.com/user-attachments/assets/80aaebfe-e7a5-4c67-996b-bc12561dbb3f) |

| Employee Management | Alert System |
|---|---|
| ![Employee Management](https://github.com/user-attachments/assets/7c32af4b-a23a-42ae-96e3-bbf6bf0949a1) | ![Alert](https://github.com/user-attachments/assets/df67314c-b74a-4941-971c-01f82d52b047) |

---

## 🚀 Features

### 🧠 GNN Stress Inference
- `StabilityGNN` — a Graph Convolutional Network with a custom **Global Attention Layer** that evaluates every node against every other node on the mesh
- Trained model stored as `stability_gnn.pth` (~73KB)
- Falls back gracefully to rule-based scoring if model is unavailable
- Uses PyTorch Geometric (`GraphConv`) + `trimesh` for mesh-to-graph conversion

### 📡 Real-Time Stress Analysis
- Upload any 3D terrain model (OBJ, GLB, STL)
- Upload a sensor CSV with environmental readings per node
- GNN scores each vertex; color-coded heatmap overlaid on VTK mesh
  - 🔴 Red → High risk | 🟡 Yellow → Moderate | 🔵 Blue → Low
- Side gauges display: Temperature, Humidity, Ground Pressure, Vibration, Crack Width, Rainfall

### 🛰️ Interactive Simulation
- Full 3D VTK viewport — rotate, zoom, pan the terrain
- Click any node → **Node Info Panel** opens
- Manually adjust sensor values with `+` / `–` buttons
- Risk recalculates live via graph propagation (`NodeConnection` with decay factor)
- **Drag-and-drop dynamite tool**: place blast simulations anywhere on terrain; affected nodes update automatically

### 🚨 Alert System
- Monitors Firebase Realtime Database every 10 seconds
- If any node risk exceeds threshold → alert popup with risk %, region, and responsible employee
- Parallel Twilio calls to employees in the affected region
- Region-specific evacuation messages (Central, North, South, East, West, etc.)

### 👷 Employee Management
- Full CRUD for employees stored in Firebase
- Region assignment: Central, North, South, East, West, Northeast, Northwest, Southeast, Southwest
- Department field
- Region-wise animated employee count meters
- Automatic link: region risk → responsible employee contact

### 🔐 Authentication
- Firebase-backed login/signup
- Email + password validation
- Last-login timestamp tracking

---

## 🗂️ Project Structure

```
rockguard/
├── main.py                        # Entry point — launches PyQt6 app
│
├── core/
│   ├── __init__.py
│   ├── app_window.py              # Main application window (QMainWindow)
│   ├── alertsystem.py             # Firebase polling + Twilio call dispatch
│   ├── stressinference.py         # StabilityGNN model + GNNAnalyzer class
│   ├── toolbar.py                 # COC-style drag-and-drop dynamite toolbar
│   └── clickable_mesh.py          # VTK interactor for clickable mesh nodes
│
├── pages/
│   ├── __init__.py
│   ├── home.py                    # Dashboard home with feature cards
│   ├── dashboard.py               # Overview dashboard page
│   ├── login.py                   # Login / signup page (Firebase auth)
│   ├── stress.py                  # Stress analysis page (GNN + VTK heatmap)
│   ├── simulation.py              # 3D simulation with dynamite tool
│   ├── employee.py                # Employee management (CRUD + Firebase)
│   ├── nodeconnection.py          # Graph propagation engine (BFS + decay)
│   ├── circular_meter.py          # Circular progress meter widget
│   └── stability_gnn.pth          # Pre-trained GNN model weights
│
└── ui/
    ├── __init__.py
    ├── sidebar.py                 # Collapsible navigation sidebar
    ├── gauges.py                  # FuturisticGauge + AnimatedRiskMeter widgets
    └── loading_overlay.py         # Loading spinner overlay widget
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or newer
- CUDA-capable GPU *(optional, falls back to CPU)*
- Windows / Linux / macOS

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/rockguard.git
cd rockguard
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure secrets
Copy the example config and fill in your credentials:
```bash
cp config.example.env config.env
```

Edit `config.env`:
```env
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_DB_URL=https://your-project-default-rtdb.firebaseio.com/
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### 5. Run the app
```bash
python main.py
```

---

## 📋 Requirements

```
PyQt6>=6.5.0
torch>=2.0.0
torch-geometric>=2.3.0
vtk>=9.2.0
trimesh>=4.0.0
scipy>=1.10.0
numpy>=1.24.0
pandas>=2.0.0
pyrebase4>=4.6.0
twilio>=8.0.0
requests>=2.31.0
```

> **Note:** `torch-geometric` installation depends on your CUDA version. See the [official install guide](https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html).

---

## 📄 Sensor CSV Format

The system expects a CSV with the following columns:

```csv
node_id,temperature,humidity,ground_pressure,vibration,crack_width,rainfall
0,28.5,72.3,1.04,0.23,0.5,12.1
1,31.2,68.0,1.12,0.45,1.1,15.3
...
```

| Column | Unit | Description |
|---|---|---|
| `node_id` | — | Mesh vertex ID (0-indexed) |
| `temperature` | °C | Surface temperature |
| `humidity` | % | Relative humidity |
| `ground_pressure` | kPa | Subsurface pressure |
| `vibration` | m/s² | Seismic vibration level |
| `crack_width` | mm | Surface crack measurement |
| `rainfall` | mm/hr | Rainfall intensity |

---

## 🧪 Supported 3D Model Formats

| Format | Extension | Notes |
|---|---|---|
| Wavefront OBJ | `.obj` | Most tested |
| GL Transmission Format | `.glb` / `.gltf` | Binary preferred |
| STL | `.stl` | ASCII or binary |

> Models should be pre-cleaned (manifold, no degenerate faces). Use [MeshLab](https://www.meshlab.net/) or [Blender](https://www.blender.org/) to clean raw terrain scans.

---

## 🧠 GNN Architecture

```
Input: 3D vertex coordinates (x, y, z) per node
       + k-NN graph edges (k=8 neighbors)

GraphConv(3 → 128)  →  ReLU
GraphConv(128 → 128) →  ReLU
GraphConv(128 → 128) →  ReLU
        │
        └─── GlobalAttentionLayer(128)
               Q·Kᵀ / √d  →  Softmax  →  ·V
        │
Concat(local_128, global_128) → Linear(256→128) → ReLU
Linear(128 → 64) → ReLU → Dropout(0.1)
Linear(64 → 1) → Risk Score (0–1 per node)
```

The `GlobalAttentionLayer` allows every node to attend to every other node, giving the model terrain-wide context — not just local neighbor information.

---

## 🔧 Configuration

### Firebase Setup
1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable **Realtime Database**
3. Set database rules to allow authenticated read/write
4. Copy your web app credentials into `config.env`

### Twilio Setup
1. Create an account at [twilio.com](https://www.twilio.com)
2. Purchase a phone number
3. Copy `Account SID`, `Auth Token`, and your Twilio number into `config.env`

---

## 🗺️ Roadmap

- [ ] IoT real-time sensor ingestion (MQTT / WebSocket)
- [ ] SMS and WhatsApp alerts via Twilio Messaging API
- [ ] Physics-based rockfall trajectory simulation
- [ ] GNN model retraining UI inside the app
- [ ] Cloud dashboard with multi-user / multi-site support
- [ ] Export risk reports as PDF
- [ ] Android / iOS companion alert app

---

## ⚠️ Known Limitations

- Desktop-only (no web version yet)
- 3D models must be pre-processed and clean
- CSV sensor values must be numeric with no missing data
- Firebase and Twilio require active accounts and internet connection
- The GNN was trained on synthetic terrain data — results on novel terrains may require fine-tuning

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/) — GNN framework
- [VTK](https://vtk.org/) — 3D visualization toolkit
- [Trimesh](https://trimesh.org/) — Mesh processing
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Desktop GUI
- [Firebase](https://firebase.google.com/) — Realtime database & auth
- [Twilio](https://www.twilio.com/) — Voice call API

---

<div align="center">
Made with ❤️ for safer mining and construction operations
</div>
