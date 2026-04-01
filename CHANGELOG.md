# Changelog

All notable changes to RockGuard will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2025-11-27

### Added
- `StabilityGNN` model with Global Attention Layer for per-node terrain risk scoring
- GNN Analyzer (`stressinference.py`) — loads `stability_gnn.pth`, builds k-NN graph from mesh vertices
- VTK-based 3D heatmap rendering on terrain meshes (OBJ, GLB, STL)
- Sensor CSV ingestion pipeline (temperature, humidity, ground pressure, vibration, crack width, rainfall)
- Interactive simulation page with draggable dynamite blast tool
- Node Info Panel — click any mesh node to inspect and manually adjust sensor values
- Graph propagation engine (`NodeConnection`) — BFS with exponential decay for blast effect spreading
- Employee Management page with Firebase CRUD and region assignment
- Alert System — Firebase polling every 10s + parallel Twilio voice calls
- Per-region evacuation messages
- Firebase-backed login / signup
- Collapsible sidebar navigation
- Futuristic gauge widgets and animated risk meters
- COC-style drag-and-drop toolbar with persistent dynamite placement
- Node numbering labels via `vtkFollower`

### Architecture
- PyQt6 desktop application with QStackedWidget page routing
- VTK embedded in PyQt6 via `QVTKRenderWindowInteractor`
- PyTorch Geometric `GraphConv` layers + custom `GlobalAttentionLayer`
- Firebase Realtime Database for employee data, auth, and risk telemetry
- Twilio REST API for emergency voice calls
- `scipy.spatial.cKDTree` for fast nearest-neighbor mesh queries
