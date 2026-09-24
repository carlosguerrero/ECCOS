import os
import graphviz

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'figures')

# ==============================================================================
# UMLSubdiagramsPlot.py
# 
# Generador independiente para cada uno de los submodelos de ECCOS:
#   1. Infraestructura (generate_infra_subdiagram)
#   2. Usuarios (generate_user_subdiagram)
#   3. Aplicaciones (generate_app_subdiagram)
#   4. Eventos / Acciones Globales (generate_global_subdiagram)
#
# Cada función es completamente autónoma: define su propia tipografía, paleta de
# colores, clases, enumeraciones y relaciones. Cualquier cambio en un submodelo
# no afectará en absoluto a los demás.
# ==============================================================================


def generate_infra_subdiagram(filename="eccos_schema_infra_subset", output_dir=None, view=True):
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    """
    Genera de forma independiente el subdiagrama del modelo de Infraestructura.
    """
    dot = graphviz.Digraph(filename, format='pdf')

    # Configuración tipográfica independiente
    title_size = "96"
    field_size = "82"
    edge_size = "74"
    cell_pad = "26"

    dot.attr(rankdir='LR', splines='ortho', nodesep='1.4', ranksep='2.0')
    dot.attr(size='18,13!', ratio='fill')
    dot.attr('node', fontname='Arial', shape='none')
    dot.attr('edge', fontname='Arial', fontsize=edge_size)

    # Paleta de colores
    C_ROOT = "#D5D8DC"
    C_MODULE = "#D4E6F1"
    C_ENTITY = "#AED6F1"
    C_ACTION = "#D1F2EB"
    C_TYPE = "#FCF3CF"
    C_SPECIFIC = "#FADBD8"
    C_ENUM = "#EBDEF0"

    def add_class(name, title, fields, bg_color):
        rows = ""
        for f in fields:
            f = f.replace('<', '&lt;').replace('>', '&gt;')
            rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="{field_size}">{f}</FONT></TD></TR>'

        if not fields:
            rows = f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="{field_size}">Container</FONT></I></TD></TR>'

        label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="{cell_pad}">
            <TR><TD BGCOLOR="{bg_color}"><B><FONT POINT-SIZE="{title_size}">{title}</FONT></B></TD></TR>
            {rows}
            </TABLE>>'''
        dot.node(name, label=label)

    # Estilos de relaciones
    COMPOSITION = {'arrowtail': 'diamond', 'dir': 'back', 'color': '#2C3E50', 'penwidth': '16.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    ASSOCIATION = {'arrowhead': 'vee', 'color': '#7F8C8D', 'style': 'dashed', 'penwidth': '12.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    AGGREGATION = {'arrowtail': 'odiamond', 'dir': 'back', 'color': '#5D6D7E', 'style': 'dashed', 'penwidth': '14.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    INHERITANCE = {'arrowhead': 'empty', 'color': '#2C3E50', 'penwidth': '22.0', 'arrowsize': '2.0', 'minlen': '2'}
    DEPENDENCY = {'arrowhead': 'vee', 'color': '#95A5A6', 'style': 'dotted', 'penwidth': '9.0', 'arrowsize': '2.0', 'minlen': '2'}

    # --- Enumeraciones ---
    add_class('EnumInfra', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraModelType', ['erdos_renyi', 'scale_free', 'spatial', 'fat_tree', 'tree', 'multi_tier'], C_ENUM)
    add_class('EnumAttrMode', '&lt;&lt;enumeration&gt;&gt;<BR/>AttributeMode', ['homogenic', 'centrality_based', 'centrality_based_layer', 'depth_based_layer', 'layered'], C_ENUM)
    add_class('EnumCent', '&lt;&lt;enumeration&gt;&gt;<BR/>CentralityType', ['direct_proportional', 'inverted_proportional'], C_ENUM)
    add_class('EnumLayer', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraLayer', ['cloud', 'fog', 'edge'], C_ENUM)
    add_class('EnumLayerMapping', '&lt;&lt;enumeration&gt;&gt;<BR/>LayerMappingMode', ['centrality_based', 'depth_based'], C_ENUM)
    add_class('EnumDist', '&lt;&lt;enumeration&gt;&gt;<BR/>DistributionType', ['uniform', 'pareto', 'exponential', '...'], C_ENUM)
    add_class('EnumInfraAction', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraActionType', ['disable_node', 'disable_edge', 'degrade_node', 'congest_node'], C_ENUM)
    add_class('EnumDomain', '&lt;&lt;enumeration&gt;&gt;<BR/>EntityDomainType', ['infrastructure', 'app', 'user', 'global'], C_ENUM)

    # --- Clases ---
    add_class('Root', '&lt;&lt;Root&gt;&gt;<BR/>ECCOS_Scenario', [
        '+ setup : SetupConfig',
        '+ trigger_policy : TriggerPolicy',
        '+ app : App',
        '+ user : User',
        '+ global_spawner : GlobalSpawner',
        '+ infrastructure : Infrastructure'
    ], C_ROOT)
    add_class('Entity', '&lt;&lt;Abstract&gt;&gt;<BR/>Entity', ['+ actions : Map&lt;String, ActionItem&gt; [0..*]'], C_ENTITY)
    add_class('Infrastructure', 'Infrastructure', ['+ num_nodes : int', '+ node : Map&lt;String, AttributeDef&gt;', '+ edge : Map&lt;String, AttributeDef&gt;'], C_MODULE)
    add_class('TopologyConfig', 'TopologyConfig', [], C_SPECIFIC)
    add_class('TopologyNode', 'TopologyNode', ['+ id : String | int', '+ custom_attributes : Map&lt;String, Any&gt;'], C_SPECIFIC)
    add_class('TopologyEdge', 'TopologyEdge', ['+ source : String | int', '+ target : String | int', '+ custom_attributes : Map&lt;String, Any&gt;'], C_SPECIFIC)
    add_class('InfraModelConfig', 'InfraModelConfig', ['+ name : InfraModelType', '+ layer : InfraLayer', '+ layer_mapping_mode : LayerMappingMode'], C_SPECIFIC)
    add_class('ImpactConfig', 'ImpactConfig', [
        '+ target_id : String | int [0..1]',
        '+ severity : float | DistributionDef [0..1]',
        '+ duration_seconds : float | DistributionDef [0..1]',
        '+ custom_payload : Map&lt;String, Any&gt;'
    ], C_SPECIFIC)
    add_class('DistributionDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>DistributionDef', ['+ type : DistributionType', '+ low / high : float', '+ a / b / scale : float', '+ mean / sigma : float'], C_TYPE)
    add_class('AttributeDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>AttributeDef', ['+ mode : AttributeMode', '+ distribution : DistributionDef', '+ min / max : float', '+ centrality_type : CentralityType', '+ cloud : Map&lt;String, Any&gt;', '+ thresholds : Map&lt;String, number&gt;', '+ distributions : Map&lt;String, DistributionDef&gt;'], C_TYPE)
    add_class('ActionItem', '&lt;&lt;StochasticEvent&gt;&gt;<BR/>ActionItem', [
        '+ frequency : DistributionDef',
        '+ domain : EntityDomainType [0..1]',
        '+ composed_of : List&lt;ActionItem&gt; [0..*]'
    ], C_ACTION)

    # --- Relaciones ---
    dot.edge('InfraModelConfig', 'EnumInfra', **DEPENDENCY)
    dot.edge('AttributeDef', 'EnumAttrMode', **DEPENDENCY)
    dot.edge('AttributeDef', 'EnumCent', **DEPENDENCY)
    dot.edge('InfraModelConfig', 'EnumLayer', **DEPENDENCY)
    dot.edge('InfraModelConfig', 'EnumLayerMapping', **DEPENDENCY)
    dot.edge('DistributionDef', 'EnumDist', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumInfraAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumDomain', **DEPENDENCY)

    dot.edge('Root', 'Infrastructure', headlabel='  infrastructure  ', **COMPOSITION)
    dot.edge('Infrastructure', 'Entity', **INHERITANCE)
    dot.edge('Infrastructure', 'TopologyConfig', headlabel='  topology (manual)  ', **COMPOSITION)
    dot.edge('Infrastructure', 'InfraModelConfig', headlabel='  model (random)                ', **{**COMPOSITION, 'labeldistance': '16.0', 'labelangle': '10'})
    dot.edge('TopologyConfig', 'TopologyNode', headlabel='\n  nodes [0..*]            ', **{**COMPOSITION, 'labeldistance': '13.0', 'labelangle': '5'})
    dot.edge('TopologyConfig', 'TopologyEdge', headlabel='\n  edges [0..*]            ', **{**COMPOSITION, 'labeldistance': '13.0', 'labelangle': '5'})
    dot.edge('ActionItem', 'ImpactConfig', headlabel='  impact [0..1]  ', **COMPOSITION)

    dot.edge('Entity', 'ActionItem', headlabel='  actions\n\n\n\n            ', **{**ASSOCIATION, 'labeldistance': '23.0', 'labelangle': '38'})
    dot.edge('AttributeDef', 'DistributionDef', headlabel='\n  uses  ', **{**ASSOCIATION, 'labeldistance': '6.0', 'labelangle': '10'})
    dot.edge('ActionItem', 'DistributionDef', headlabel='  frequency            ', **{**ASSOCIATION, 'labeldistance': '13.0', 'labelangle': '10'})
    dot.edge('ImpactConfig', 'DistributionDef', headlabel='  severity / duration\n\n', **{**ASSOCIATION, 'labeldistance': '7.5', 'labelangle': '35'})
    dot.edge('Infrastructure', 'AttributeDef', headlabel='  node/edge attrs                ', **{**ASSOCIATION, 'labeldistance': '16.0', 'labelangle': '10'})
    dot.edge('ActionItem', 'ActionItem', headlabel='                  composed_of\n                  (Macro-Events)  ', **{**AGGREGATION, 'labeldistance': '14.5', 'labelangle': '5'})

    # Alineaciones verticales en la misma columna (menos ancho, más altura)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('Root')
        s.node('Infrastructure')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('ImpactConfig')
        s.node('DistributionDef')
        s.node('EnumDist')

    output_path = os.path.join(output_dir, filename)
    dot.render(output_path, view=view, cleanup=True)
    print(f"[Infraestructura] Gráfico generado con éxito: {output_path}.pdf")
    return dot


def generate_user_subdiagram(filename="eccos_schema_user_subset", output_dir=None, view=True):
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    """
    Genera de forma independiente el subdiagrama del modelo de Usuarios y Movilidad.
    """
    dot = graphviz.Digraph(filename, format='pdf')

    title_size = "96"
    field_size = "82"
    edge_size = "74"
    cell_pad = "26"

    dot.attr(rankdir='LR', splines='ortho', nodesep='1.4', ranksep='2.0')
    dot.attr(size='18,13!', ratio='fill')
    dot.attr('node', fontname='Arial', shape='none')
    dot.attr('edge', fontname='Arial', fontsize=edge_size)

    C_ROOT = "#D5D8DC"
    C_MODULE = "#D4E6F1"
    C_ENTITY = "#AED6F1"
    C_ACTION = "#D1F2EB"
    C_TYPE = "#FCF3CF"
    C_SPECIFIC = "#FADBD8"
    C_ENUM = "#EBDEF0"

    def add_class(name, title, fields, bg_color):
        rows = ""
        for f in fields:
            f = f.replace('<', '&lt;').replace('>', '&gt;')
            rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="{field_size}">{f}</FONT></TD></TR>'

        if not fields:
            rows = f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="{field_size}">Container</FONT></I></TD></TR>'

        label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="{cell_pad}">
            <TR><TD BGCOLOR="{bg_color}"><B><FONT POINT-SIZE="{title_size}">{title}</FONT></B></TD></TR>
            {rows}
            </TABLE>>'''
        dot.node(name, label=label)

    COMPOSITION = {'arrowtail': 'diamond', 'dir': 'back', 'color': '#2C3E50', 'penwidth': '16.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    ASSOCIATION = {'arrowhead': 'vee', 'color': '#7F8C8D', 'style': 'dashed', 'penwidth': '12.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    AGGREGATION = {'arrowtail': 'odiamond', 'dir': 'back', 'color': '#5D6D7E', 'style': 'dashed', 'penwidth': '14.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    INHERITANCE = {'arrowhead': 'empty', 'color': '#2C3E50', 'penwidth': '22.0', 'arrowsize': '2.0', 'minlen': '2'}
    DEPENDENCY = {'arrowhead': 'vee', 'color': '#95A5A6', 'style': 'dotted', 'penwidth': '9.0', 'arrowsize': '2.0', 'minlen': '2'}

    # --- Enumeraciones ---
    add_class('EnumDist', '&lt;&lt;enumeration&gt;&gt;<BR/>DistributionType', ['uniform', 'pareto', 'exponential', '...'], C_ENUM)
    add_class('EnumMobility', '&lt;&lt;enumeration&gt;&gt;<BR/>MobilityModel', ['static', 'random', 'manhattan'], C_ENUM)
    add_class('EnumSpatial', '&lt;&lt;enumeration&gt;&gt;<BR/>SpatialModel', ['random_uniform', 'thomas_cluster'], C_ENUM)
    add_class('EnumUserAction', '&lt;&lt;enumeration&gt;&gt;<BR/>UserActionType', ['remove_user', 'suspend_user', 'change_request_ratio', 'move_user'], C_ENUM)
    add_class('EnumDomain', '&lt;&lt;enumeration&gt;&gt;<BR/>EntityDomainType', ['infrastructure', 'app', 'user', 'global'], C_ENUM)

    # --- Clases ---
    add_class('Root', '&lt;&lt;Root&gt;&gt;<BR/>ECCOS_Scenario', [
        '+ setup : SetupConfig',
        '+ trigger_policy : TriggerPolicy',
        '+ app : App',
        '+ user : User',
        '+ global_spawner : GlobalSpawner',
        '+ infrastructure : Infrastructure'
    ], C_ROOT)
    add_class('Entity', '&lt;&lt;Abstract&gt;&gt;<BR/>Entity', ['+ actions : Map&lt;String, ActionItem&gt; [0..*]'], C_ENTITY)
    add_class('User', 'User', ['+ num_users : int', '+ spatial_distribution : SpatialDistConfig', '+ spatial_region : SpatialRegionConfig', '+ mobility : MobilityConfig', '+ request_ratio : DistributionDef'], C_MODULE)
    add_class('MobilityConfig', 'MobilityConfig', ['+ model : MobilityModel', '+ turn_probabilities : Map&lt;String, float&gt;', '+ speed : float | DistributionDef', '+ coverage_radius : float | DistributionDef'], C_SPECIFIC)
    add_class('SpatialDistConfig', 'SpatialDistConfig', ['+ model : SpatialModel', '+ hotspots : int', '+ spread : float'], C_SPECIFIC)
    add_class('SpatialRegionConfig', 'SpatialRegionConfig', ['+ width : float', '+ height : float', '+ num_vertical_streets : int', '+ num_horizontal_streets : int'], C_SPECIFIC)
    add_class('ImpactConfig', 'ImpactConfig', [
        '+ target_id : String | int [0..1]',
        '+ severity : float | DistributionDef [0..1]',
        '+ duration_seconds : float | DistributionDef [0..1]',
        '+ custom_payload : Map&lt;String, Any&gt;'
    ], C_SPECIFIC)
    add_class('DistributionDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>DistributionDef', ['+ type : DistributionType', '+ low / high : float', '+ a / b / scale : float', '+ mean / sigma : float'], C_TYPE)
    add_class('ActionItem', '&lt;&lt;StochasticEvent&gt;&gt;<BR/>ActionItem', [
        '+ frequency : DistributionDef',
        '+ domain : EntityDomainType [0..1]',
        '+ composed_of : List&lt;ActionItem&gt; [0..*]'
    ], C_ACTION)

    # --- Relaciones ---
    dot.edge('DistributionDef', 'EnumDist', **DEPENDENCY)
    dot.edge('SpatialDistConfig', 'EnumSpatial', **DEPENDENCY)
    dot.edge('MobilityConfig', 'EnumMobility', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumUserAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumDomain', **DEPENDENCY)

    dot.edge('Root', 'User', headlabel='  user                ', **{**COMPOSITION, 'labeldistance': '16.0', 'labelangle': '10'})
    dot.edge('User', 'Entity', **INHERITANCE)
    dot.edge('User', 'SpatialDistConfig', headlabel='\n  spatial_distribution                ', **{**COMPOSITION, 'labeldistance': '16.0', 'labelangle': '5'})
    dot.edge('User', 'SpatialRegionConfig', headlabel='  spatial_region\n\n  ', **{**COMPOSITION, 'labeldistance': '6.0', 'labelangle': '35'})
    dot.edge('User', 'MobilityConfig', headlabel='               mobility  ', **{**COMPOSITION, 'labeldistance': '3.5', 'labelangle': '15'})
    dot.edge('ActionItem', 'ImpactConfig', headlabel='  impact [0..1]  ', **COMPOSITION)

    dot.edge('Entity', 'ActionItem', headlabel='  actions\n\n\n\n\n            ', **{**ASSOCIATION, 'labeldistance': '23.0', 'labelangle': '43'})
    dot.edge('ActionItem', 'DistributionDef', headlabel='  frequency                                    \n\n\n\n', **{**ASSOCIATION, 'labeldistance': '12.0', 'labelangle': '40'})
    dot.edge('User', 'DistributionDef', headlabel='  request_ratio                ', **{**ASSOCIATION, 'labeldistance': '16.0', 'labelangle': '10'})
    dot.edge('MobilityConfig', 'DistributionDef', headlabel='  speed / radius                ', **{**ASSOCIATION, 'labeldistance': '16.0', 'labelangle': '10'})
    dot.edge('ImpactConfig', 'DistributionDef', headlabel='  severity / duration\n\n', **{**ASSOCIATION, 'labeldistance': '7.5', 'labelangle': '35'})
    dot.edge('ActionItem', 'ActionItem', headlabel='\n\ncomposed_of                                                                           \n(Macro-Events)                                                                           ', **{**AGGREGATION, 'labeldistance': '10.0', 'labelangle': '-25'})

    # Alineaciones verticales en la misma columna (menos ancho, más altura)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('Root')
        s.node('User')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('ImpactConfig')
        s.node('DistributionDef')
        s.node('EnumDist')

    output_path = os.path.join(output_dir, filename)
    dot.render(output_path, view=view, cleanup=True)
    print(f"[Usuarios] Gráfico generado con éxito: {output_path}.pdf")
    return dot


def generate_app_subdiagram(filename="eccos_schema_app_subset", output_dir=None, view=True):
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    """
    Genera de forma independiente el subdiagrama del modelo de Aplicaciones y Servicios.
    """
    dot = graphviz.Digraph(filename, format='pdf')

    title_size = "96"
    field_size = "82"
    edge_size = "74"
    cell_pad = "26"

    dot.attr(rankdir='LR', splines='ortho', nodesep='1.4', ranksep='2.0')
    dot.attr(size='18,13!', ratio='fill')
    dot.attr('node', fontname='Arial', shape='none')
    dot.attr('edge', fontname='Arial', fontsize=edge_size)

    C_ROOT = "#D5D8DC"
    C_MODULE = "#D4E6F1"
    C_ENTITY = "#AED6F1"
    C_ACTION = "#D1F2EB"
    C_TYPE = "#FCF3CF"
    C_SPECIFIC = "#FADBD8"
    C_ENUM = "#EBDEF0"

    def add_class(name, title, fields, bg_color):
        rows = ""
        for f in fields:
            f = f.replace('<', '&lt;').replace('>', '&gt;')
            rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="{field_size}">{f}</FONT></TD></TR>'

        if not fields:
            rows = f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="{field_size}">Container</FONT></I></TD></TR>'

        label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="{cell_pad}">
            <TR><TD BGCOLOR="{bg_color}"><B><FONT POINT-SIZE="{title_size}">{title}</FONT></B></TD></TR>
            {rows}
            </TABLE>>'''
        dot.node(name, label=label)

    COMPOSITION = {'arrowtail': 'diamond', 'dir': 'back', 'color': '#2C3E50', 'penwidth': '16.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    ASSOCIATION = {'arrowhead': 'vee', 'color': '#7F8C8D', 'style': 'dashed', 'penwidth': '12.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    AGGREGATION = {'arrowtail': 'odiamond', 'dir': 'back', 'color': '#5D6D7E', 'style': 'dashed', 'penwidth': '14.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    INHERITANCE = {'arrowhead': 'empty', 'color': '#2C3E50', 'penwidth': '22.0', 'arrowsize': '2.0', 'minlen': '2'}
    DEPENDENCY = {'arrowhead': 'vee', 'color': '#95A5A6', 'style': 'dotted', 'penwidth': '9.0', 'arrowsize': '2.0', 'minlen': '2'}

    # --- Enumeraciones ---
    add_class('EnumArch', '&lt;&lt;enumeration&gt;&gt;<BR/>AppArchitecture', ['microservice', 'monolithic'], C_ENUM)
    add_class('EnumAppTopo', '&lt;&lt;enumeration&gt;&gt;<BR/>TopologyModel', ['sfc', 'directed_scale_free'], C_ENUM)
    add_class('EnumAttrMode', '&lt;&lt;enumeration&gt;&gt;<BR/>AttributeMode', ['homogenic', 'centrality_based', 'centrality_based_layer', 'depth_based_layer', 'layered'], C_ENUM)
    add_class('EnumDist', '&lt;&lt;enumeration&gt;&gt;<BR/>DistributionType', ['uniform', 'pareto', 'exponential', '...'], C_ENUM)
    add_class('EnumAppAction', '&lt;&lt;enumeration&gt;&gt;<BR/>AppActionType', ['remove_app', 'update_app_footprint', 'update_app_network', 'update_app_topology', 'surge_popularity', 'geo_demand_shift'], C_ENUM)
    add_class('EnumDomain', '&lt;&lt;enumeration&gt;&gt;<BR/>EntityDomainType', ['infrastructure', 'app', 'user', 'global'], C_ENUM)

    # --- Clases ---
    add_class('Root', '&lt;&lt;Root&gt;&gt;<BR/>ECCOS_Scenario', [
        '+ setup : SetupConfig',
        '+ trigger_policy : TriggerPolicy',
        '+ app : App',
        '+ user : User',
        '+ global_spawner : GlobalSpawner',
        '+ infrastructure : Infrastructure'
    ], C_ROOT)
    add_class('Entity', '&lt;&lt;Abstract&gt;&gt;<BR/>Entity', ['+ actions : Map&lt;String, ActionItem&gt; [0..*]'], C_ENTITY)
    add_class('App', 'App', ['+ num_apps : int', '+ architecture : AppArchitecture', '+ popularity : PopularityConfig', '+ num_new_users : DistributionDef'], C_MODULE)
    add_class('AppServicesConfig', 'AppServicesConfig', ['+ topology_model : TopologyModel', '+ scale_free_settings : Map&lt;String, int&gt;', '+ num_service_range : Tuple&lt;int, int&gt;'], C_SPECIFIC)
    add_class('ProfileDef', 'ProfileDef', ['+ prob : float', '+ attributes : Map&lt;String, AttributeDef&gt;'], C_SPECIFIC)
    add_class('PopularityConfig', 'PopularityConfig', ['+ distribution : DistributionDef', '+ model : String', '+ alpha : float', '+ local_app_ratio : float', '+ local_radius_influence : float'], C_SPECIFIC)
    add_class('ImpactConfig', 'ImpactConfig', [
        '+ target_id : String | int [0..1]',
        '+ severity : float | DistributionDef [0..1]',
        '+ duration_seconds : float | DistributionDef [0..1]',
        '+ custom_payload : Map&lt;String, Any&gt;'
    ], C_SPECIFIC)
    add_class('DistributionDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>DistributionDef', ['+ type : DistributionType', '+ low / high : float', '+ a / b / scale : float', '+ mean / sigma : float'], C_TYPE)
    add_class('AttributeDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>AttributeDef', ['+ mode : AttributeMode', '+ distribution : DistributionDef', '+ min / max : float', '+ centrality_type : CentralityType', '+ cloud : Map&lt;String, Any&gt;', '+ thresholds : Map&lt;String, number&gt;', '+ distributions : Map&lt;String, DistributionDef&gt;'], C_TYPE)
    add_class('ActionItem', '&lt;&lt;StochasticEvent&gt;&gt;<BR/>ActionItem', [
        '+ frequency : DistributionDef',
        '+ domain : EntityDomainType [0..1]',
        '+ composed_of : List&lt;ActionItem&gt; [0..*]'
    ], C_ACTION)

    # --- Relaciones ---
    dot.edge('App', 'EnumArch', **DEPENDENCY)
    dot.edge('AppServicesConfig', 'EnumAppTopo', **DEPENDENCY)
    dot.edge('AttributeDef', 'EnumAttrMode', **DEPENDENCY)
    dot.edge('EnumDist', 'DistributionDef', **{**DEPENDENCY, 'dir': 'back'})
    dot.edge('ActionItem', 'EnumAppAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumDomain', **DEPENDENCY)

    dot.edge('Root', 'App', headlabel='  app        ', **COMPOSITION)
    dot.edge('App', 'Entity', **INHERITANCE)
    dot.edge('App', 'AppServicesConfig', headlabel='  services                 ', **COMPOSITION)
    dot.edge('App', 'PopularityConfig', headlabel='  popularity                 ', **COMPOSITION)
    dot.edge('AppServicesConfig', 'ProfileDef', headlabel='  profiles [0..*]                  ', **COMPOSITION)
    dot.edge('ActionItem', 'ImpactConfig', headlabel='\n  impact        \n[ 0..1]        ', **COMPOSITION)

    dot.edge('Entity', 'ActionItem', headlabel='  actions                    \n\n\n', **ASSOCIATION)
    dot.edge('AttributeDef', 'DistributionDef', headlabel='         uses  ', **ASSOCIATION)
    dot.edge('ActionItem', 'DistributionDef', headlabel='  frequency                       ', **ASSOCIATION)
    dot.edge('PopularityConfig', 'DistributionDef', headlabel='  distribution                       ', **ASSOCIATION)
    dot.edge('App', 'DistributionDef', headlabel='  num_new_users                           ', **ASSOCIATION)
    dot.edge('ProfileDef', 'ProfileDef', headlabel='\n\n\n\n  service_flow                                              \n(SFC / DAG)                                                ', **ASSOCIATION)
    dot.edge('ImpactConfig', 'DistributionDef', headlabel='  severity / duration  \n\n\n\n', **ASSOCIATION)
    dot.edge('ProfileDef', 'AttributeDef', headlabel='  node attr.              \n(cpu,ram...)            ', **ASSOCIATION)
    dot.edge('AppServicesConfig', 'AttributeDef', headlabel='  network attributes                                   \n(bw, delay...)                                     ', **ASSOCIATION)
    dot.edge('ActionItem', 'ActionItem', headlabel='\n\n\n\n\n\n\n\n  composed_of                                              \n(Macro-Events)                                                ', **AGGREGATION)

    # Alineaciones verticales en la misma columna (menos ancho, más altura)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('Root')
        s.node('App')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('EnumDist')
        s.node('DistributionDef')

    output_path = os.path.join(output_dir, filename)
    dot.render(output_path, view=view, cleanup=True)
    print(f"[Aplicaciones] Gráfico generado con éxito: {output_path}.pdf")
    return dot


def generate_global_subdiagram(filename="eccos_schema_global_subset", output_dir=None, view=True):
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    """
    Genera de forma independiente el subdiagrama del modelo Global (Spawner y Acciones Globales).
    """
    dot = graphviz.Digraph(filename, format='pdf')

    title_size = "96"
    field_size = "82"
    edge_size = "74"
    cell_pad = "26"

    dot.attr(rankdir='LR', splines='ortho', nodesep='1.4', ranksep='1.1')
    dot.attr(size='18,13!', ratio='fill')
    dot.attr('node', fontname='Arial', shape='none')
    dot.attr('edge', fontname='Arial', fontsize=edge_size)

    C_ROOT = "#D5D8DC"
    C_MODULE = "#D4E6F1"
    C_ENTITY = "#AED6F1"
    C_ACTION = "#D1F2EB"
    C_TYPE = "#FCF3CF"
    C_SPECIFIC = "#FADBD8"
    C_ENUM = "#EBDEF0"

    def add_class(name, title, fields, bg_color):
        rows = ""
        for f in fields:
            f = f.replace('<', '&lt;').replace('>', '&gt;')
            rows += f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="{field_size}">{f}</FONT></TD></TR>'

        if not fields:
            rows = f'<TR><TD ALIGN="CENTER"><I><FONT POINT-SIZE="{field_size}">Container</FONT></I></TD></TR>'

        label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="{cell_pad}">
            <TR><TD BGCOLOR="{bg_color}"><B><FONT POINT-SIZE="{title_size}">{title}</FONT></B></TD></TR>
            {rows}
            </TABLE>>'''
        dot.node(name, label=label)

    COMPOSITION = {'arrowtail': 'diamond', 'dir': 'back', 'color': '#2C3E50', 'penwidth': '16.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    ASSOCIATION = {'arrowhead': 'vee', 'color': '#7F8C8D', 'style': 'dashed', 'penwidth': '12.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    AGGREGATION = {'arrowtail': 'odiamond', 'dir': 'back', 'color': '#5D6D7E', 'style': 'dashed', 'penwidth': '14.0', 'arrowsize': '2.8', 'minlen': '2', 'labeldistance': '6.0', 'labelangle': '25'}
    INHERITANCE = {'arrowhead': 'empty', 'color': '#2C3E50', 'penwidth': '22.0', 'arrowsize': '2.0', 'minlen': '2'}
    DEPENDENCY = {'arrowhead': 'vee', 'color': '#95A5A6', 'style': 'dotted', 'penwidth': '9.0', 'arrowsize': '2.0', 'minlen': '2'}

    # --- Enumeraciones ---
    add_class('EnumDist', '&lt;&lt;enumeration&gt;&gt;<BR/>DistributionType', ['uniform', 'pareto', 'exponential', '...'], C_ENUM)
    add_class('EnumInfraAction', '&lt;&lt;enumeration&gt;&gt;<BR/>InfraActionType', ['disable_node', 'disable_edge', 'degrade_node', 'congest_node'], C_ENUM)
    add_class('EnumAppAction', '&lt;&lt;enumeration&gt;&gt;<BR/>AppActionType', ['remove_app', 'update_app_footprint', 'update_app_network', 'update_app_topology', 'surge_popularity', 'geo_demand_shift'], C_ENUM)
    add_class('EnumUserAction', '&lt;&lt;enumeration&gt;&gt;<BR/>UserActionType', ['remove_user', 'suspend_user', 'change_request_ratio', 'move_user'], C_ENUM)
    add_class('EnumGlobalAction', '&lt;&lt;enumeration&gt;&gt;<BR/>GlobalActionType', ['new_user', 'new_app'], C_ENUM)
    add_class('EnumDomain', '&lt;&lt;enumeration&gt;&gt;<BR/>EntityDomainType', ['infrastructure', 'app', 'user', 'global'], C_ENUM)

    # --- Clases ---
    add_class('Root', '&lt;&lt;Root&gt;&gt;<BR/>ECCOS_Scenario', [
        '+ setup : SetupConfig',
        '+ trigger_policy : TriggerPolicy',
        '+ app : App',
        '+ user : User',
        '+ global_spawner : GlobalSpawner',
        '+ infrastructure : Infrastructure'
    ], C_ROOT)
    add_class('Entity', '&lt;&lt;Abstract&gt;&gt;<BR/>Entity', ['+ actions : Map&lt;String, ActionItem&gt; [0..*]'], C_ENTITY)
    add_class('GlobalSpawner', 'GlobalSpawner', ['+ new_user : ActionItem', '+ new_app : ActionItem'], C_MODULE)
    add_class('ImpactConfig', 'ImpactConfig', [
        '+ target_id : String | int [0..1]',
        '+ severity : float | DistributionDef [0..1]',
        '+ duration_seconds : float | DistributionDef [0..1]',
        '+ custom_payload : Map&lt;String, Any&gt;'
    ], C_SPECIFIC)
    add_class('DistributionDef', '&lt;&lt;AbstractType&gt;&gt;<BR/>DistributionDef', ['+ type : DistributionType', '+ low / high : float', '+ a / b / scale : float', '+ mean / sigma : float'], C_TYPE)
    add_class('ActionItem', '&lt;&lt;StochasticEvent&gt;&gt;<BR/>ActionItem', [
        '+ frequency : DistributionDef',
        '+ domain : EntityDomainType [0..1]',
        '+ composed_of : List&lt;ActionItem&gt; [0..*]'
    ], C_ACTION)

    # --- Relaciones ---
    dot.edge('EnumDist', 'DistributionDef', **{**DEPENDENCY, 'dir': 'back'})
    dot.edge('ActionItem', 'EnumInfraAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumAppAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumUserAction', **DEPENDENCY)
    dot.edge('GlobalSpawner', 'EnumGlobalAction', **DEPENDENCY)
    dot.edge('ActionItem', 'EnumDomain', **DEPENDENCY)

    dot.edge('Root', 'GlobalSpawner', headlabel='                                 global_spawner  ', **COMPOSITION)
    dot.edge('GlobalSpawner', 'Entity', **INHERITANCE)
    dot.edge('ActionItem', 'ImpactConfig', headlabel='  impact [0..1]  ', **COMPOSITION)

    dot.edge('Entity', 'ActionItem', headlabel='\n\n  actions  ', **{**ASSOCIATION, 'constraint': 'false'})
    dot.edge('GlobalSpawner', 'ActionItem', headlabel='  new_user / app                            \n\n\n', **ASSOCIATION)
    dot.edge('ActionItem', 'DistributionDef', headlabel='                        frequency  ', **ASSOCIATION)
    dot.edge('ImpactConfig', 'DistributionDef', headlabel='\n  severity /                  \n duration                  ', **ASSOCIATION)
    dot.edge('ActionItem', 'ActionItem', headlabel='\n\n\n\n\n\n\n\n.           composed_of\n          (Macro-Events)  ', **AGGREGATION)

    # Restricciones de orden vertical con aristas invisibles
    dot.edge('ActionItem', 'Entity', style='invis')

    # Alineaciones verticales (Column 1: Root -> GlobalSpawner -> EnumGlobalAction)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('Root')
        s.node('GlobalSpawner')
        s.node('EnumGlobalAction')

    # Alineaciones verticales (Column 2: ActionItem -> Entity)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('ActionItem')
        s.node('Entity')

    # Alineaciones verticales (Column 3: EnumDist -> DistributionDef)
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('EnumDist')
        s.node('DistributionDef')

    output_path = os.path.join(output_dir, filename)
    dot.render(output_path, view=view, cleanup=True)
    print(f"[Global] Gráfico generado con éxito: {output_path}.pdf")
    return dot


def generate_all_subdiagrams(output_dir=None, view=True):
    """
    Genera de forma secuencial todos los subdiagramas independientes.
    """
    generate_infra_subdiagram(output_dir=output_dir, view=view)
    generate_user_subdiagram(output_dir=output_dir, view=view)
    generate_app_subdiagram(output_dir=output_dir, view=view)
    generate_global_subdiagram(output_dir=output_dir, view=view)


if __name__ == '__main__':
    generate_all_subdiagrams(view=True)
