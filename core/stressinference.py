# ============================================
# stressinference.py — GNN with Global Attention for Full Mesh Analysis
# ============================================

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GraphConv, global_add_pool, global_mean_pool
import trimesh
import numpy as np
import os
import math

# ============================================
# Model definition with Global Attention
# ============================================

class GlobalAttentionLayer(torch.nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.query = torch.nn.Linear(hidden_dim, hidden_dim)
        self.key = torch.nn.Linear(hidden_dim, hidden_dim)
        self.value = torch.nn.Linear(hidden_dim, hidden_dim)
        self.softmax = torch.nn.Softmax(dim=-1)
        
    def forward(self, x):
        # x: [num_nodes, hidden_dim]
        Q = self.query(x)  # [num_nodes, hidden_dim]
        K = self.key(x)    # [num_nodes, hidden_dim]  
        V = self.value(x)  # [num_nodes, hidden_dim]
        
        # Compute attention scores: every node with every other node
        attention_scores = torch.matmul(Q, K.transpose(0, 1)) / math.sqrt(self.hidden_dim)
        attention_weights = self.softmax(attention_scores)  # [num_nodes, num_nodes]
        
        # Apply attention to values
        global_context = torch.matmul(attention_weights, V)  # [num_nodes, hidden_dim]
        
        return global_context

class StabilityGNN(torch.nn.Module):
    def __init__(self, hidden_dim=128):
        super().__init__()
        # Local feature extraction
        self.conv1 = GraphConv(3, hidden_dim)
        self.conv2 = GraphConv(hidden_dim, hidden_dim)
        self.conv3 = GraphConv(hidden_dim, hidden_dim)
        
        # Global attention mechanism
        self.global_attention = GlobalAttentionLayer(hidden_dim)
        
        # Feature fusion and output
        self.fusion = torch.nn.Linear(hidden_dim * 2, hidden_dim)  # Local + Global
        self.lin1 = torch.nn.Linear(hidden_dim, hidden_dim // 2)
        self.lin2 = torch.nn.Linear(hidden_dim // 2, 1)
        
        self.dropout = torch.nn.Dropout(0.1)

    def forward(self, x, edge_index, batch=None):
        # Extract local features
        local_feat1 = F.relu(self.conv1(x, edge_index))
        local_feat2 = F.relu(self.conv2(local_feat1, edge_index))
        local_feat3 = F.relu(self.conv3(local_feat2, edge_index))
        
        # Get global context for each node
        global_context = self.global_attention(local_feat3)
        
        # Combine local and global features
        combined = torch.cat([local_feat3, global_context], dim=-1)
        fused = F.relu(self.fusion(combined))
        
        # Final prediction
        out = F.relu(self.lin1(fused))
        out = self.dropout(out)
        out = self.lin2(out)
        
        return out.squeeze()

# ============================================
# Enhanced GNN Analyzer Class
# ============================================

class GNNAnalyzer:
    def __init__(self, model_path="stability_gnn.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.model_loaded = self.load_model(model_path)
        print(f"🚀 Using device: {self.device}")
    
    def load_model(self, model_path):
        """Load the trained GNN model"""
        try:
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return False
            
            print(f"✅ Loading model from: {model_path}")
            self.model = StabilityGNN(hidden_dim=128).to(self.device)
            
            # Handle both full model and state_dict saving
            if model_path.endswith('.pth'):
                checkpoint = torch.load(model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)
            else:
                self.model = torch.load(model_path, map_location=self.device)
            
            self.model.eval()
            print("✅ GNN model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load GNN model: {e}")
            self.model = None
            return False

    def build_complete_graph_edges(self, vertices, k_neighbors=8):
        """Build edges using k-nearest neighbors for complete graph connectivity"""
        from sklearn.neighbors import NearestNeighbors
        
        vertices_np = vertices.cpu().numpy() if isinstance(vertices, torch.Tensor) else vertices
        
        # Use k-nearest neighbors to build edges
        nbrs = NearestNeighbors(n_neighbors=k_neighbors, algorithm='ball_tree').fit(vertices_np)
        distances, indices = nbrs.kneighbors(vertices_np)
        
        # Create edge list
        edges = []
        for i in range(len(vertices_np)):
            for j in indices[i]:
                if i != j:  # Avoid self-loops
                    edges.append([i, j])
        
        edges = torch.tensor(edges, dtype=torch.long).t().contiguous()
        return edges

    def load_mesh_as_graph(self, file_path, k_neighbors=8):
        """Load mesh and convert to graph with enhanced connectivity"""
        try:
            mesh = trimesh.load(file_path, force='mesh')
            vertices = torch.tensor(mesh.vertices, dtype=torch.float)
            
            # Build edges from faces if available
            if hasattr(mesh, 'faces') and len(mesh.faces) > 0:
                faces = torch.tensor(mesh.faces, dtype=torch.long)
                edges_from_faces = torch.cat([
                    faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]
                ], dim=0)
                edges_from_faces = torch.unique(edges_from_faces, dim=0)
                
                # Add k-nearest neighbors for better connectivity
                edges_from_knn = self.build_complete_graph_edges(vertices, k_neighbors)
                
                # Combine both edge sets
                all_edges = torch.cat([edges_from_faces, edges_from_knn], dim=1)
                all_edges = torch.unique(all_edges, dim=1)
                
                edge_index = all_edges
            else:
                # Fallback to k-nearest neighbors only
                edge_index = self.build_complete_graph_edges(vertices, k_neighbors)
            
            print(f"📊 Mesh graph: {len(vertices)} vertices, {edge_index.shape[1]} edges")
            return Data(x=vertices, edge_index=edge_index), mesh
            
        except Exception as e:
            print(f"❌ Error loading mesh: {e}")
            return None, None

    def analyze_complete_mesh_stress(self, mesh_data, stress_threshold=0.7):
        """Analyze stress across entire mesh without clustering"""
        if self.model is None:
            raise ValueError("GNN model not loaded")
        
        self.model.eval()
        mesh_data = mesh_data.to(self.device)
        
        with torch.no_grad():
            # Get stress predictions for ALL nodes
            stress_predictions = self.model(mesh_data.x, mesh_data.edge_index)
        
        # Convert to numpy
        stress_np = stress_predictions.cpu().numpy()
        vertices_np = mesh_data.x.cpu().numpy()
        
        # Normalize stress scores to 0-1 range
        stress_normalized = (stress_np - stress_np.min()) / (stress_np.max() - stress_np.min() + 1e-8)
        
        # Identify high stress nodes
        high_stress_mask = stress_normalized > stress_threshold
        high_stress_indices = np.where(high_stress_mask)[0]
        high_stress_points = vertices_np[high_stress_indices]
        high_stress_scores = stress_normalized[high_stress_indices]
        
        print(f"🔍 Stress analysis: {len(high_stress_indices)} high-stress nodes found "
              f"(threshold: {stress_threshold})")
        
        return {
            'all_stress': stress_normalized,
            'all_vertices': vertices_np,
            'high_stress_points': high_stress_points,
            'high_stress_indices': high_stress_indices,
            'high_stress_scores': high_stress_scores,
            'stress_range': (stress_np.min(), stress_np.max())
        }

    def get_top_stress_points(self, mesh_data, top_k=200):
        """Get top k highest stress points"""
        if self.model is None:
            raise ValueError("GNN model not loaded")
        
        self.model.eval()
        mesh_data = mesh_data.to(self.device)
        
        with torch.no_grad():
            preds = self.model(mesh_data.x, mesh_data.edge_index)
        
        preds = preds.cpu().numpy()
        vertices = mesh_data.x.cpu().numpy()

        # Get top k points with highest stress scores
        top_indices = np.argsort(-preds)[:top_k]  # Sort descending
        top_points = vertices[top_indices]
        top_scores = preds[top_indices]
        
        return top_points, top_scores, top_indices

    def analyze_mesh(self, mesh_file_path, top_k=200, analysis_type="top_points"):
        """Main function: analyze mesh and return results"""
        if self.model is None:
            return None, "GNN model not loaded"
        
        try:
            # Load mesh as graph
            mesh_data, mesh = self.load_mesh_as_graph(mesh_file_path)
            if mesh_data is None:
                return None, "Failed to load mesh"
            
            if analysis_type == "complete_analysis":
                # Full mesh stress analysis
                results = self.analyze_complete_mesh_stress(mesh_data)
                return results, "Complete analysis success"
            else:
                # Top points analysis (original functionality)
                top_points, top_scores, top_indices = self.get_top_stress_points(mesh_data, top_k)
                return {
                    'top_points': top_points,
                    'top_scores': top_scores,
                    'top_indices': top_indices
                }, "Top points analysis success"
            
        except Exception as e:
            return None, f"Analysis failed: {str(e)}"

    def analyze_vertices(self, vertices, faces=None, top_k=200, k_neighbors=8):
        """Analyze vertices directly without loading from file"""
        if self.model is None:
            return None, None, None, "GNN model not loaded"
        
        try:
            # Convert vertices to tensor
            vertices_tensor = torch.tensor(vertices, dtype=torch.float)
            
            # Build enhanced edge connectivity
            if faces is not None and len(faces) > 0:
                faces_tensor = torch.tensor(faces, dtype=torch.long)
                edges_from_faces = torch.cat([
                    faces_tensor[:, [0, 1]], faces_tensor[:, [1, 2]], faces_tensor[:, [2, 0]]
                ], dim=0)
                edges_from_faces = torch.unique(edges_from_faces, dim=0)
                
                # Add k-nearest neighbors
                edges_from_knn = self.build_complete_graph_edges(vertices_tensor, k_neighbors)
                
                # Combine edges
                all_edges = torch.cat([edges_from_faces, edges_from_knn], dim=1)
                edge_index = torch.unique(all_edges, dim=1)
            else:
                # Use k-nearest neighbors only
                edge_index = self.build_complete_graph_edges(vertices_tensor, k_neighbors)
            
            mesh_data = Data(x=vertices_tensor, edge_index=edge_index)
            
            # Get top stress points
            top_points, top_scores, top_indices = self.get_top_stress_points(mesh_data, top_k)
            
            return top_points, top_scores, top_indices, "Success"
            
        except Exception as e:
            return None, None, None, f"Vertex analysis failed: {str(e)}"

    def visualize_stress_distribution(self, analysis_results):
        """Simple visualization of stress distribution"""
        try:
            import matplotlib.pyplot as plt
            
            stress_scores = analysis_results['all_stress']
            
            plt.figure(figsize=(10, 6))
            plt.hist(stress_scores, bins=50, alpha=0.7, color='red', edgecolor='black')
            plt.xlabel('Stress Score')
            plt.ylabel('Frequency')
            plt.title('Stress Distribution Across Mesh')
            plt.grid(True, alpha=0.3)
            plt.show()
            
            print(f"📈 Stress stats: Min={stress_scores.min():.3f}, "
                  f"Max={stress_scores.max():.3f}, Mean={stress_scores.mean():.3f}")
                  
        except ImportError:
            print("📊 Matplotlib not available for visualization")
        except Exception as e:
            print(f"❌ Visualization error: {e}")

# ============================================
# Utility functions
# ============================================

def create_gnn_analyzer(model_path="stability_gnn.pth"):
    """Factory function to create and initialize GNN analyzer"""
    return GNNAnalyzer(model_path)

def save_stress_analysis(results, output_path="stress_analysis.json"):
    """Save analysis results to JSON file"""
    import json
    
    try:
        # Convert numpy arrays to lists for JSON serialization
        save_data = {
            'high_stress_points': results['high_stress_points'].tolist(),
            'high_stress_indices': results['high_stress_indices'].tolist(),
            'high_stress_scores': results['high_stress_scores'].tolist(),
            'stress_range': results['stress_range'],
            'total_high_stress_nodes': len(results['high_stress_indices'])
        }
        
        with open(output_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"💾 Analysis results saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Failed to save analysis: {e}")

# ============================================
# Example usage
# ============================================

if __name__ == "__main__":
    # Example usage
    analyzer = create_gnn_analyzer("stability_gnn.pth")
    
    if analyzer.model_loaded:
        # Analyze complete mesh
        results, message = analyzer.analyze_mesh(
            "your_mesh.obj", 
            analysis_type="complete_analysis"
        )
        
        if results:
            print(f"✅ {message}")
            print(f"🔴 Found {len(results['high_stress_indices'])} high-stress nodes")
            
            # Visualize distribution
            analyzer.visualize_stress_distribution(results)
            
            # Save results
            save_stress_analysis(results, "mesh_stress_analysis.json")