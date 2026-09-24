import os
import graphviz

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'figures')

def generate_eccos_architecture(output_dir=None, view=True):
    # Configuración original Top-to-Bottom
    dot = graphviz.Digraph('ECCOS_Architecture', format='pdf')
    dot.attr(rankdir='TB', splines='ortho', nodesep='1.0', ranksep='0.8', fontname='Arial')

    color_primary = "#2c3e50"   # Azul oscuro
    color_secondary = "#34495e" # Azul grisáceo
    color_accent = "#2980b9"    # Azul claro vibrante
    color_bg = "#ecf0f1"        # Gris muy claro para fondos
    color_file = "#f39c12"      # Naranja para archivos
    color_external = "#27ae60"  # Verde para integraciones ML

    dot.attr('node', shape='box', style='filled,rounded', fontname='Arial', 
             fontsize='12', fontcolor='white', color=color_primary, fillcolor=color_primary)
    dot.attr('edge', fontname='Arial', fontsize='10', color=color_secondary, arrowhead='vee')

    # ==========================================
    # 1. ENTRADAS / INICIALIZACIÓN
    # ==========================================
    with dot.subgraph(name='cluster_init') as c_init:
        c_init.attr(label='Initialization Phase', style='dashed', color='gray', fontname='Arial', bgcolor='#fdfdfd')
        
        c_init.node('Config', 'YAML Config\n(Topology, Policies, Profiles)', shape='note', fillcolor=color_file, fontcolor='black')
        c_init.node('Architect', 'Ecco-Architect\n[Context Configuration Engine]', fillcolor=color_accent)
        
        c_init.edge('Config', 'Architect', label=' Parses parameters')

    # ==========================================
    # 2. BUCLE PRINCIPAL DE SIMULACIÓN
    # ==========================================
    with dot.subgraph(name='cluster_loop') as c_loop:
        c_loop.attr(label='Simulation Loop (Discrete-Time)', style='solid', color=color_primary, penwidth='2', bgcolor=color_bg)
        
        c_loop.node('Generator', 'Ecco-Generator\n[Discrete-Event Stochastic Engine]', fillcolor=color_secondary)
        c_loop.node('State', 'Ecco-State\n[System State Manager]', fillcolor=color_secondary)
        c_loop.node('Solver', 'Ecco-Solver\n[Decoupled Optimization Engine]', fillcolor=color_secondary)

        c_loop.edge('Generator', 'State', label=' 1. Pops Event\n(t = t + Δt)')
        c_loop.edge('State', 'Solver', label=' 2. Evaluates Policy &\nSends System State')
        c_loop.edge('Solver', 'State', label=' 3. Solves ILP &\nReturns Optimal Placement')
        c_loop.edge('State', 'Generator', label=' 4. Schedules\nFuture Events', style='dashed')

    # ==========================================
    # 3. SALIDAS E INTEGRACIÓN ML
    # ==========================================
    with dot.subgraph(name='cluster_output') as c_out:
        c_out.attr(label='Output & Integration Phase', style='dashed', color='gray', fontname='Arial', bgcolor='#fdfdfd')
        
        c_out.node('Bridge', 'Ecco-Bridge\n[Data Integration & ML Interface]', fillcolor=color_accent)
        c_out.node('JSON', 'ML-Ready Datasets\n(JSONL / CSV)', shape='cylinder', fillcolor=color_file, fontcolor='black')
        c_out.node('Gym', 'OpenAI Gymnasium\n(RL Environment Interface)', shape='hexagon', fillcolor=color_external)

    # ==========================================
    # CONEXIONES Y ESTABILIZACIÓN ESTRUCTURAL
    # ==========================================
    dot.edge('Architect', 'Generator', label=' Seeds DES\nEvent Queue')
    
    # Desvinculamos esta flecha de la estructura para no deformar el bucle vertical
    dot.edge('Architect', 'State', label=' Instantiates Graph,\nUsers & Apps', constraint='false')

    # ================= THE FIX =================
    # 1. Quitamos el "constraint" de las flechas reales hacia el Output para que Graphviz 
    #    no obligue al Output a irse a la parte inferior del documento.
    dot.edge('State', 'Bridge', label=' Streams Telemetry\n& Observations', constraint='false')
    dot.edge('Solver', 'Bridge', label=' Streams Actions\n& Rewards (Cost)', constraint='false')

    # 2. Andamiaje invisible: Forzamos una columna paralela que baje un escalón (Spacer) 
    #    antes de pintar el Bridge. Esto crea el efecto de "a la derecha y un poco más abajo".
    dot.node('Spacer', '', style='invis', width='0', height='0', margin='0')
    dot.edge('Architect', 'Spacer', style='invis')
    dot.edge('Spacer', 'Bridge', style='invis')
    # ===========================================

    # Conexiones finales
    dot.edge('Bridge', 'JSON', label=' Exports Traces')
    dot.edge('Bridge', 'Gym', label=' Exposes step() & reset()', dir='both')

    # Guardar y renderizar
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'eccos_architecture_fixed')
    dot.render(output_path, view=view, cleanup=True)
    print(f"Gráfico generado con éxito: {output_path}.pdf")

if __name__ == '__main__':
    generate_eccos_architecture(view=True)