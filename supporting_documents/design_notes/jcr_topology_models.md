# Network Topology Generation and Tier Assignment Models

The simulation framework supports five distinct network topology generation models, designed to replicate the structural heterogeneity of modern Cloud-to-Edge continuums. Each model employs specific graph theory principles to establish connections and a logical mapping strategy to classify nodes into the three fundamental tiers: *Cloud*, *Fog*, and *Edge*.

### 1. Scale-Free Topology (Barabási-Albert)
* **Graph Model:** Barabási-Albert (BA) preferential attachment model.
* **Description:** This model simulates the growth of networks where new nodes are more likely to attach to existing nodes that already have a high degree of connections. It closely resembles the structural properties of the Internet and large-scale wide-area networks (WANs), characterized by a few highly connected hubs and many loosely connected peripheral nodes.
* **Tier Mapping (`centrality_based_layer`):** Nodes are mapped to tiers based on their *Betweenness Centrality*. Nodes with the highest centrality values (acting as major routing hubs) are classified as the **Cloud** tier. Nodes with intermediate centrality fall into the **Fog** tier, while the vast majority of peripheral nodes with minimal centrality represent the **Edge** tier.

### 2. Erdős-Rényi Random Topology
* **Graph Model:** Erdős-Rényi (ER) random graph model.
* **Description:** An unstructured topology where each pair of nodes is connected with a fixed independent probability $p$. This model is useful for establishing theoretical baselines or simulating highly chaotic, non-hierarchical peer-to-peer (P2P) environments without preferential hubs.
* **Tier Mapping (`centrality_based_layer`):** Similar to the Scale-Free model, the structural hierarchy is inferred *a posteriori* by calculating the Betweenness Centrality of the resulting graph, applying predefined threshold values to partition the nodes into Cloud, Fog, and Edge tiers.

### 3. Spatial Topology (Random Geometric Graph)
* **Graph Model:** Random Geometric Graph (RGG).
* **Description:** Nodes are uniformly distributed within a continuous two-dimensional metric space. An edge is created between any two nodes if the Euclidean distance between them is strictly less than a configurable radius $r$. This model accurately represents physical proximity constraints, making it ideal for simulating IoT sensor networks, vehicular ad-hoc networks (VANETs), and wireless far-edge deployments.
* **Tier Mapping (`centrality_based_layer`):** Despite its physical nature, the logical hierarchy is established via Betweenness Centrality. Nodes located at geographical bottlenecks or central clusters naturally route more shortest-paths, acquiring higher centrality and thereby acting as Cloud or Fog nodes, while isolated clusters act as the Edge.

### 4. Hierarchical Tree Topology (Tree / Fat-Tree)
* **Graph Model:** Balanced Tree graph.
* **Description:** Generates a strictly hierarchical, perfectly balanced tree defined by a constant branching factor ($r$) and a maximum height ($h$). This deterministic topology models traditional datacenter architectures, telecommunication backhauls, and strict Edge-to-Cloud hierarchical routing paths where cross-communication between peer nodes is absent without traversing higher-level switches.
* **Tier Mapping (`depth_based_layer`):** Node classification is determined directly by their topological depth relative to the root node (Depth 0). The root and its immediate descendants are designated as the **Cloud** tier. Intermediate layers constitute the **Fog** tier, while the leaf nodes at the maximum depth ($h$) form the **Edge** tier.

### 5. Multi-Tier Composite Topology
* **Graph Model:** Stitched Multi-Graph (Complete + Scale-Free + RGG).
* **Description:** A highly realistic, composite approach that bypasses *a posteriori* inference by generating each tier using the mathematical model that best represents its real-world counterpart. The architecture is explicitly divided into three independent subgraphs:
  - **Cloud:** Modeled as a *Complete Graph* (all nodes interconnected), guaranteeing extreme redundancy and mimicking ultra-connected core datacenters.
  - **Fog:** Modeled as a *Scale-Free Graph* (Barabási-Albert), representing decentralized regional hubs and metropolitan area networks (MANs).
  - **Edge:** Modeled as a *Spatial Graph* (RGG), accurately reflecting the physical and wireless proximity of edge devices.
* **Tier Mapping:** Tiers are assigned deterministically at the moment of creation. After the internal generation of each layer, the subgraphs are algorithmically "stitched" together by establishing vertical inter-tier links (Edge $\leftrightarrow$ Fog, and Fog $\leftrightarrow$ Cloud), ensuring full network connectivity while preserving the explicit architectural constraints of each computational paradigm.
