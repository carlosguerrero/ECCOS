import os
import graphviz

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'figures')

def generate_eccos_uml_ecosystem(output_dir=None, view=True):
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Función centralizada para construir los diagramas (Total o Parciales)
    def build_diagram(filename, allowed_nodes=None, is_subgraph=False):
        dot = graphviz.Digraph(filename, format='pdf')
        
        # 🌟 CONFIGURACIÓN TIPOGRÁFICA
        if is_subgraph:
            title_size = "96"   
            field_size = "82"   
            edge_size = "74"    
            cell_pad = "26"     
            
            dot.attr(rankdir='LR', splines='ortho', nodesep='1.4', ranksep='2.0')
            dot.attr(size='24,11!', ratio='fill')
        else:
            title_size = "46"
            field_size = "32"
            edge_size = "26"
            cell_pad = "14"
            
            dot.attr(rankdir='TB', splines='ortho', nodesep='1.2', ranksep='1.8')
            dot.attr(size='16,16!', ratio='fill')
            
        dot.attr('node', fontname='Arial', shape='none')
        dot.attr('edge', fontname='Arial', fontsize=edge_size)

        # Paleta de colores académicos
        C_ROOT = "#D5D8DC"
        C_MODULE = "#D4E6F1"
        C_ENTITY = "#AED6F1"
        C_ACTION = "#D1F2EB"
        C_TYPE = "#FCF3CF"
        C_ILP = "#E8DAEF"
        C_SPECIFIC = "#FADBD8"
        C_ENUM = "#EBDEF0"

        # Generador de clases HTML
        def add_class(name, title, fields, bg_color):
            if allowed_nodes is not None and name not in allowed_nodes:
                return
            
            rows = ""
            for f in fields:
                f = f.replace('<', '&lt;').replace('>', '&gt;')
                rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="{field_size}">{f}</FONT></TD></TR>'
            
            if not fields:
                rows = f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="{field_size}">Container</FONT></I></TD></TR>'

            label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="{cell_pad}" FONTNAME="Arial">
                <TR><TD BGCOLOR="{bg_color}"><B><FONT POINT-SIZE="{title_size}">{title}</FONT></B></TD></TR>
                {rows}
                </TABLE>>'''
            dot.node(name, label=label)

        def add_edge(source, target, **kwargs):
            if allowed_nodes is not None:
                if source not in allowed_nodes or target not in allowed_nodes:
                    return
            dot.edge(source, target, **kwargs)

        # ==========================================
        # 0. ENUMERACIONES
        # ==========================================
        add_class('EnumSetup', '&lt;&lt;enumeration&gt;&gt;<BR/>SetupMode', ['random', 'manual'], C_ENUM)
        add_class('EnumObjective', '&lt;&lt;enumeration&gt;&gt;<BR/>ObjectiveType', ['single-objective', 'multi-objective'], C_ENUM)
        add_class('EnumTrigger', '&lt;&lt;enumeration&gt;&gt;<BR/>TriggerType', ['solve_all', 'solve_random_prob', '...'], C_ENUM)
        add_class('EnumArch', '&lt;&lt;enumeration&gt;&gt;<BR/>AppArchitecture', ['microservice', 'monolithic'], C_ENUM)
        add_class('EnumAppTopo', '&lt;&lt;enumeration&gt;&gt;<BR/>TopologyModel', ['sfc', 'directed_scale_free'], C_ENUM)
        add_class('EnumInfra', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraModelType', ['erdos_renyi', 'scale_free', 'spatial', 'fat_tree', 'tree', 'multi_tier'], C_ENUM)
        add_class('EnumDist', '&lt;&lt;enumeration&gt;&gt;<BR/>DistributionType', ['uniform', 'pareto', 'exponential', '...'], C_ENUM)
        add_class('EnumAttrMode', '&lt;&lt;enumeration&gt;&gt;<BR/>AttributeMode', ['homogenic', 'centrality_based', 'centrality_based_layer', 'depth_based_layer', 'layered'], C_ENUM)
        add_class('EnumCent', '&lt;&lt;enumeration&gt;&gt;<BR/>CentralityType', ['direct_proportional', 'inverted_proportional'], C_ENUM)
        add_class('EnumLayer', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraLayer', ['cloud', 'fog', 'edge'], C_ENUM)
        add_class('EnumLayerMapping', '&lt;&lt;enumeration&gt;&gt;<BR/>LayerMappingMode', ['centrality_based', 'depth_based'], C_ENUM)
        add_class('EnumSpatial', '&lt;&lt;enumeration&gt;&gt;<BR/>SpatialModel', ['random_uniform', 'thomas_cluster'], C_ENUM)
        add_class('EnumMobility', '&lt;&lt;enumeration&gt;&gt;<BR/>MobilityModel', ['static', 'random', 'manhattan'], C_ENUM)
        
        add_class('EnumInfraAction', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraActionType', ['disable_node', 'disable_edge', 'degrade_node', 'congest_node'], C_ENUM)
        add_class('EnumAppAction', '&lt;&lt;enumeration&gt;&gt;<BR/>AppActionType', ['remove_app', 'update_app_footprint', 'update_app_network', 'update_app_topology', 'surge_popularity', 'geo_demand_shift'], C_ENUM)
        add_class('EnumUserAction', '&lt;&lt;enumeration&gt;&gt;<BR/>UserActionType', ['remove_user', 'suspend_user', 'change_request_ratio', 'move_user'], C_ENUM)
        add_class('EnumGlobalAction', '&lt;&lt;enumeration&gt;&gt;<BR/>GlobalActionType', ['new_user', 'new_app'], C_ENUM)
        add_class('EnumDomain', '&lt;&lt;enumeration&gt;&gt;<BR/>EntityDomainType', ['infrastructure', 'app', 'user', 'global'], C_ENUM)

        # ==========================================
        # 1. ROOT Y CONFIGURACIÓN BASE
        # ==========================================
        add_class('Root', '&lt;&lt;Root&gt;&gt;<BR/>ECCOS_Scenario', [
            '+ setup : SetupConfig',
            '+ trigger_policy : TriggerPolicy',
            '+ app : App',
            '+ user : User',
            '+ global_spawner : GlobalSpawner',
            '+ infrastructure : Infrastructure'
        ], C_ROOT)

        add_class('SetupConfig', 'SetupConfig', ['+ mode : SetupMode', '+ ilp_solver : ILPSolverConfig'], C_MODULE)
        add_class('ILPSolverConfig', 'ILPSolverConfig', ['+ timeLimit : int', '+ gapRel : float', '+ objective : ObjectiveType', '+ weights : Map&lt;String, float&gt;'], C_ILP)
        add_class('TriggerPolicy', 'TriggerPolicy', ['+ type : TriggerType', '+ probability : float', '+ windows : List&lt;Tuple&lt;float, float&gt;&gt;', '+ ranges : List&lt;Tuple&lt;int, int&gt;&gt;', '+ pattern : List&lt;boolean&gt;', '+ interval_seconds : float', '+ batch_size : int', '+ critical_events : List&lt;String&gt;'], C_MODULE)

        # ==========================================
        # 2. SUPERCLASE ENTITY Y DOMINIO
        # ==========================================
        add_class('Entity', '&lt;&lt;Abstract&gt;&gt;<BR/>Entity', ['+ actions : Map&lt;String, ActionItem&gt; [0..*]'], C_ENTITY)
        add_class('App', 'App', ['+ num_apps : int', '+ architecture : AppArchitecture', '+ popularity : PopularityConfig', '+ num_new_users : DistributionDef'], C_MODULE)
        add_class('User', 'User', ['+ num_users : int', '+ spatial_distribution : SpatialDistConfig', '+ spatial_region : SpatialRegionConfig', '+ mobility : MobilityConfig', '+ request_ratio : DistributionDef'], C_MODULE)
        add_class('Infrastructure', 'Infrastructure', ['+ num_nodes : int', '+ node : Map&lt;String, AttributeDef&gt;', '+ edge : Map&lt;String, AttributeDef&gt;'], C_MODULE)
        add_class('GlobalSpawner', 'GlobalSpawner', ['+ new_user : ActionItem', '+ new_app : ActionItem'], C_MODULE)

        # ==========================================
        # 3. CONFIGURACIONES ESPECÍFICAS
        # ==========================================
        add_class('TopologyConfig', 'TopologyConfig', [], C_SPECIFIC)
        add_class('TopologyNode', 'TopologyNode', ['+ id : String | int', '+ custom_attributes : Map&lt;String, Any&gt;'], C_SPECIFIC)
        add_class('TopologyEdge', 'TopologyEdge', ['+ source : String | int', '+ target : String | int', '+ custom_attributes : Map&lt;String, Any&gt;'], C_SPECIFIC)
        add_class('InfraModelConfig', 'InfraModelConfig', ['+ name : InfraModelType', '+ layer : InfraLayer', '+ layer_mapping_mode : LayerMappingMode'], C_SPECIFIC)
        
        add_class('AppServicesConfig', 'AppServicesConfig', ['+ topology_model : TopologyModel', '+ scale_free_settings : Map&lt;String, int&gt;', '+ num_service_range : Tuple&lt;int, int&gt;'], C_SPECIFIC)
        add_class('ProfileDef', 'ProfileDef', ['+ prob : float', '+ attributes : Map&lt;String, AttributeDef&gt;'], C_SPECIFIC)
        add_class('PopularityConfig', 'PopularityConfig', ['+ distribution : DistributionDef', '+ model : String', '+ alpha : float', '+ local_app_ratio : float', '+ local_radius_influence : float'], C_SPECIFIC)
        
        add_class('SpatialDistConfig', 'SpatialDistConfig', ['+ model : SpatialModel', '+ hotspots : int', '+ spread : float'], C_SPECIFIC)
        add_class('SpatialRegionConfig', 'SpatialRegionConfig', ['+ width : float', '+ height : float', '+ num_vertical_streets : int', '+ num_horizontal_streets : int'], C_SPECIFIC)
        add_class('MobilityConfig', 'MobilityConfig', ['+ model : MobilityModel', '+ turn_probabilities : Map&lt;String, float&gt;', '+ speed : float | DistributionDef', '+ coverage_radius : float | DistributionDef'], C_SPECIFIC)

        add_class('ImpactConfig', 'ImpactConfig', [
            '+ target_id : String | int [0..1]',
            '+ severity : float | DistributionDef [0..1]',
            '+ duration_seconds : float | DistributionDef [0..1]',
            '+ custom_payload : Map&lt;String, Any&gt;'
        ], C_SPECIFIC)

        # ==========================================
        # 4. DEFINICIONES ABSTRACTAS
        # ==========================================
        add_class('DistributionDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>DistributionDef', ['+ type : DistributionType', '+ low / high : float', '+ a / b / scale : float', '+ mean / sigma : float'], C_TYPE)
        add_class('AttributeDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>AttributeDef', ['+ mode : AttributeMode', '+ distribution : DistributionDef', '+ min / max : float', '+ centrality_type : CentralityType', '+ cloud : Map&lt;String, Any&gt;', '+ thresholds : Map&lt;String, number&gt;', '+ distributions : Map&lt;String, DistributionDef&gt;'], C_TYPE)
        
        add_class('ActionItem', '&lt;&lt;StochasticEvent&gt;&gt;<BR/>ActionItem', [
            '+ frequency : DistributionDef',
            '+ domain : EntityDomainType [0..1]',
            '+ composed_of : List&lt;ActionItem&gt; [0..*]'
        ], C_ACTION)

        # ==========================================
        # RELACIONES UML (EDGES)
        # ==========================================
        # 🌟 EL TRUCO TRIGONOMÉTRICO: 
        # labeldistance='6.0' empuja la letra FUERA de la caja hacia el centro de la línea
        # labelangle='25' la mantiene rotada justo al lado de la línea para no tacharse
        COMPOSITION = {'arrowtail': 'diamond', 'dir': 'back', 'color': '#2C3E50', 'penwidth': '16.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
        ASSOCIATION = {'arrowhead': 'vee', 'color': '#7F8C8D', 'style': 'dashed', 'penwidth': '12.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
        AGGREGATION = {'arrowtail': 'odiamond', 'dir': 'back', 'color': '#5D6D7E', 'style': 'dashed', 'penwidth': '14.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'} 
        INHERITANCE = {'arrowhead': 'empty', 'color': '#2C3E50', 'penwidth': '22.0', 'arrowsize': '2.0', 'minlen': '2'} 
        DEPENDENCY = {'arrowhead': 'vee', 'color': '#95A5A6', 'style': 'dotted', 'penwidth': '9.0', 'arrowsize': '2.0', 'minlen': '2'} 

        # Dependencias de Enumeraciones (No llevan etiqueta de texto)
        add_edge('SetupConfig', 'EnumSetup', **DEPENDENCY)
        add_edge('ILPSolverConfig', 'EnumObjective', **DEPENDENCY)
        add_edge('TriggerPolicy', 'EnumTrigger', **DEPENDENCY)
        add_edge('App', 'EnumArch', **DEPENDENCY)
        add_edge('AppServicesConfig', 'EnumAppTopo', **DEPENDENCY)
        add_edge('InfraModelConfig', 'EnumInfra', **DEPENDENCY)
        add_edge('AttributeDef', 'EnumAttrMode', **DEPENDENCY)
        add_edge('AttributeDef', 'EnumCent', **DEPENDENCY)
        add_edge('InfraModelConfig', 'EnumLayer', **DEPENDENCY)
        add_edge('InfraModelConfig', 'EnumLayerMapping', **DEPENDENCY)
        add_edge('DistributionDef', 'EnumDist', **DEPENDENCY)
        add_edge('SpatialDistConfig', 'EnumSpatial', **DEPENDENCY)
        add_edge('MobilityConfig', 'EnumMobility', **DEPENDENCY)
        
        add_edge('ActionItem', 'EnumInfraAction', **DEPENDENCY)
        add_edge('ActionItem', 'EnumAppAction', **DEPENDENCY)
        add_edge('ActionItem', 'EnumUserAction', **DEPENDENCY)
        add_edge('GlobalSpawner', 'EnumGlobalAction', **DEPENDENCY)
        add_edge('ActionItem', 'EnumDomain', **DEPENDENCY)

        # 🌟 Volvemos a 'headlabel' para anclar matemáticamente, pero desplazadas por los sliders de arriba
        # Composiciones desde el Root
        add_edge('Root', 'SetupConfig', headlabel='  setup  ', **COMPOSITION)
        add_edge('Root', 'TriggerPolicy', headlabel='  trigger_policy  ', **COMPOSITION)
        add_edge('Root', 'App', headlabel='  app  ', **COMPOSITION)
        add_edge('Root', 'User', headlabel='  user  ', **COMPOSITION)
        add_edge('Root', 'Infrastructure', headlabel='  infrastructure  ', **COMPOSITION)
        add_edge('Root', 'GlobalSpawner', headlabel='  global_spawner  ', **COMPOSITION)

        # Herencia hacia Entity
        add_edge('App', 'Entity', **INHERITANCE)
        add_edge('User', 'Entity', **INHERITANCE)
        add_edge('Infrastructure', 'Entity', **INHERITANCE)
        add_edge('GlobalSpawner', 'Entity', **INHERITANCE)

        # Composiciones internas
        add_edge('SetupConfig', 'ILPSolverConfig', headlabel='  ilp_solver  ', **COMPOSITION)
        add_edge('App', 'AppServicesConfig', headlabel='  services  ', **COMPOSITION)
        add_edge('App', 'PopularityConfig', headlabel='  popularity  ', **COMPOSITION)
        add_edge('User', 'SpatialDistConfig', headlabel='  spatial_distribution  ', **COMPOSITION)
        add_edge('User', 'SpatialRegionConfig', headlabel='  spatial_region  ', **COMPOSITION)
        add_edge('User', 'MobilityConfig', headlabel='  mobility  ', **COMPOSITION)
        add_edge('Infrastructure', 'TopologyConfig', headlabel='  topology (manual)  ', **COMPOSITION)
        add_edge('Infrastructure', 'InfraModelConfig', headlabel='  model (random)  ', **COMPOSITION)
        
        add_edge('TopologyConfig', 'TopologyNode', headlabel='  nodes [0..*]  ', **COMPOSITION)
        add_edge('TopologyConfig', 'TopologyEdge', headlabel='  edges [0..*]  ', **COMPOSITION)
        add_edge('AppServicesConfig', 'ProfileDef', headlabel='  profiles [0..*]  ', **COMPOSITION)
        add_edge('ActionItem', 'ImpactConfig', headlabel='  impact [0..1]  ', **COMPOSITION)

        # Asociaciones Estocásticas
        add_edge('Entity', 'ActionItem', headlabel='  actions  ', **ASSOCIATION)
        add_edge('GlobalSpawner', 'ActionItem', headlabel='  new_user / app  ', **ASSOCIATION)
        add_edge('AttributeDef', 'DistributionDef', headlabel='  uses  ', **ASSOCIATION)
        add_edge('ActionItem', 'DistributionDef', headlabel='  frequency  ', **ASSOCIATION)
        add_edge('PopularityConfig', 'DistributionDef', headlabel='  distribution  ', **ASSOCIATION)
        add_edge('App', 'DistributionDef', headlabel='  num_new_users  ', **ASSOCIATION)
        add_edge('User', 'DistributionDef', headlabel='  request_ratio  ', **ASSOCIATION)
        add_edge('MobilityConfig', 'DistributionDef', headlabel='  speed / radius  ', **ASSOCIATION)
        add_edge('ProfileDef', 'ProfileDef', headlabel='  service_flow\n(SFC / DAG)  ', **ASSOCIATION)
        add_edge('ImpactConfig', 'DistributionDef', headlabel='  severity / duration  ', **ASSOCIATION)

        # Oferta vs Demanda
        add_edge('Infrastructure', 'AttributeDef', headlabel='  node/edge attrs  ', **ASSOCIATION)
        add_edge('ProfileDef', 'AttributeDef', headlabel='  node attributes\n(cpu, ram...)  ', **ASSOCIATION)
        add_edge('AppServicesConfig', 'AttributeDef', headlabel='  network attributes\n(bw, delay...)  ', **ASSOCIATION)

        # Recursividad
        add_edge('ActionItem', 'ActionItem', headlabel='  composed_of\n(Macro-Events)  ', **AGGREGATION)

        output_path = os.path.join(output_dir, filename)
        dot.render(output_path, view=view, cleanup=True)
        print(f"Gráfico generado con éxito: {output_path}.pdf")


    # =========================================================================
    # EJECUCIÓN
    # =========================================================================

    build_diagram('eccos_schema_full_uml', is_subgraph=False)

    infra_subset = [
        'Root', 'Infrastructure', 'InfraModelConfig', 'TopologyConfig', 
        'TopologyNode', 'TopologyEdge', 'EnumInfra', 'AttributeDef', 
        'EnumAttrMode', 'EnumCent', 'Entity', 'EnumLayer', 
        'EnumLayerMapping', 'DistributionDef', 'EnumDist', 'ActionItem', 'EnumInfraAction', 'ImpactConfig', 'EnumDomain'
    ]
    build_diagram('eccos_schema_infra_subset', allowed_nodes=infra_subset, is_subgraph=True)

    user_subset = [
        'Root', 'Entity', 'User', 'MobilityConfig', 'DistributionDef', 
        'EnumDist', 'EnumMobility', 'SpatialDistConfig', 'EnumSpatial', 'SpatialRegionConfig', 'ActionItem', 'EnumUserAction', 'ImpactConfig', 'EnumDomain'
    ]
    build_diagram('eccos_schema_user_subset', allowed_nodes=user_subset, is_subgraph=True)

    app_subset = [
        'Root', 'Entity', 'App', 'EnumArch', 'AppServicesConfig', 
        'EnumAppTopo', 'ProfileDef', 'PopularityConfig', 'AttributeDef', 
        'EnumAttrMode', 'DistributionDef', 'EnumDist', 'ActionItem', 'EnumAppAction', 'ImpactConfig', 'EnumDomain'
    ]
    build_diagram('eccos_schema_app_subset', allowed_nodes=app_subset, is_subgraph=True)

    global_subset = [
        'Root', 'Entity', 'GlobalSpawner', 'DistributionDef', 'EnumDist', 
        'ActionItem', 'ImpactConfig', 'EnumInfraAction', 'EnumAppAction', 
        'EnumUserAction', 'EnumGlobalAction', 'EnumDomain'
    ]
    build_diagram('eccos_schema_global_subset', allowed_nodes=global_subset, is_subgraph=True)


if __name__ == '__main__':
    generate_eccos_uml_ecosystem()