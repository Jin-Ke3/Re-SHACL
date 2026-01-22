"""
Generate LaTeX table with shapes graph statistics including before/after entailment comparison.
"""

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, SH

def count_shapes_stats(shapes_file):
    """Count various statistics in a shapes graph."""
    g = Graph()
    g.parse(shapes_file, format='turtle')
    
    # Count node shapes
    node_shapes = set(g.subjects(RDF.type, SH.NodeShape))
    
    # Count property shapes (sh:property)
    property_shapes = 0
    for shape in node_shapes:
        property_shapes += len(list(g.objects(shape, SH.property)))
    
    # Count targeted classes
    targeted_classes = set()
    for shape in node_shapes:
        for cls in g.objects(shape, SH.targetClass):
            targeted_classes.add(cls)
    
    # Count targeted properties (unique sh:path values)
    targeted_properties = set()
    for shape in node_shapes:
        for prop_shape in g.objects(shape, SH.property):
            for path in g.objects(prop_shape, SH.path):
                targeted_properties.add(path)
    
    # Count closed shapes
    closed_shapes = 0
    for shape in node_shapes:
        closed = g.value(shape, SH.closed)
        if closed and str(closed).lower() == 'true':
            closed_shapes += 1
    
    # Count constraints (any property on property shapes that's a constraint)
    # Common SHACL constraint properties
    constraint_props = [
        SH.minCount, SH.maxCount, SH.minLength, SH.maxLength,
        SH.pattern, SH.minInclusive, SH.maxInclusive,
        SH.minExclusive, SH.maxExclusive, SH['class'], SH.datatype,
        SH.nodeKind, SH['in'], SH.hasValue, SH.uniqueLang
    ]
    
    constraints = 0
    for shape in node_shapes:
        for prop_shape in g.objects(shape, SH.property):
            for constraint_prop in constraint_props:
                if g.value(prop_shape, constraint_prop) is not None:
                    constraints += 1
    
    return {
        'node_shapes': len(node_shapes),
        'property_shapes': property_shapes,
        'targeted_classes': len(targeted_classes),
        'targeted_properties': len(targeted_properties),
        'closed_shapes': closed_shapes,
        'constraints': constraints
    }

# Analyze original shapes
shapes_files = {
    'SG1': 'tests/fixtures/SG1.ttl',
    'SG2': 'tests/fixtures/SG2.ttl',
    'SG3': 'tests/fixtures/person_shape_closed.ttl',
    'SG4': 'tests/fixtures/closed_shape_example.ttl'
}

# Analyze entailed shapes (RDFS and OWL-LD)
entailed_shapes_rdfs = {
    'SG1': 'Outputs/entailed_shapes/rdfs/SG1_entailed.ttl',
    'SG2': 'Outputs/entailed_shapes/rdfs/SG2_entailed.ttl',
    'SG3': 'Outputs/entailed_shapes/rdfs/SG3_entailed.ttl',
    'SG4': 'Outputs/entailed_shapes/rdfs/SG4_entailed.ttl'
}

entailed_shapes_owl = {
    'SG1': 'Outputs/entailed_shapes/owl-ld/SG1_entailed.ttl',
    'SG2': 'Outputs/entailed_shapes/owl-ld/SG2_entailed.ttl',
    'SG3': 'Outputs/entailed_shapes/owl-ld/SG3_entailed.ttl',
    'SG4': 'Outputs/entailed_shapes/owl-ld/SG4_entailed.ttl'
}

print("Analyzing shapes graphs...")
print()

# Collect statistics
stats = {}
for name, file in shapes_files.items():
    stats[name] = {
        'original': count_shapes_stats(file),
        'rdfs': count_shapes_stats(entailed_shapes_rdfs[name]),
        'owl': count_shapes_stats(entailed_shapes_owl[name])
    }

# Generate LaTeX table
print("\\begin{table}[h]")
print("    \\centering")
print("\\begin{tabular}{lrrrrrrrr}")
print("\\toprule")
print("Shapes & Node & Property & Targeted & Targeted & Closed & Constraints & Property & Constraints \\\\")
print("Graph & Shapes & Shapes & Classes & Properties & Shapes & (Original) & Shapes (Ent.) & (Ent.) \\\\")
print("\\midrule")

for name in ['SG1', 'SG2', 'SG3', 'SG4']:
    orig = stats[name]['original']
    owl = stats[name]['owl']  # Use OWL-LD for entailed stats
    
    print(f"${name.replace('SG', 'SG_')}$ & "
          f"{orig['node_shapes']:>12} & "
          f"{orig['property_shapes']:>16} & "
          f"{orig['targeted_classes']:>17} & "
          f"{orig['targeted_properties']:>19} & "
          f"{orig['closed_shapes']:>14} & "
          f"{orig['constraints']:>18} & "
          f"{owl['property_shapes']:>18} & "
          f"{owl['constraints']:>17} \\\\")

print("\\bottomrule")
print("\\end{tabular}")
print("    \\caption{Overview of the statistics for the shapes graphs used in the experiments.")
print("             Original shapes statistics and entailed shapes statistics (OWL-LD) are shown.")
print("             The entailed values show the effect of ontology-based shape extension.}")
print("    \\label{tab:shapes-stats}")
print("\\end{table}")

# Also print a summary
print("\n\nSummary Statistics:")
print("=" * 80)
for name in ['SG1', 'SG2', 'SG3', 'SG4']:
    print(f"\n{name}:")
    print(f"  Original: {stats[name]['original']['property_shapes']} property shapes, "
          f"{stats[name]['original']['constraints']} constraints")
    print(f"  RDFS:     {stats[name]['rdfs']['property_shapes']} property shapes (+{stats[name]['rdfs']['property_shapes'] - stats[name]['original']['property_shapes']}), "
          f"{stats[name]['rdfs']['constraints']} constraints (+{stats[name]['rdfs']['constraints'] - stats[name]['original']['constraints']})")
    print(f"  OWL-LD:   {stats[name]['owl']['property_shapes']} property shapes (+{stats[name]['owl']['property_shapes'] - stats[name]['original']['property_shapes']}), "
          f"{stats[name]['owl']['constraints']} constraints (+{stats[name]['owl']['constraints'] - stats[name]['original']['constraints']})")
