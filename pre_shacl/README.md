# Pre-SHACL Module Documentation

## Overview

The `pre_shacl` module provides preprocessing functionality for SHACL (Shapes Constraint Language) validation workflows. It implements the "Closed-Shaper" approach, which:

1. **Applies semantic entailment** (RDFS/OWL) to data and shapes graphs
2. **Extends closed shapes** with inferred properties to avoid false validation violations
3. **Manages ignored properties** for closed shapes (rdf:type, owl:sameAs, etc.)

This preprocessing step significantly improves SHACL validation accuracy when working with ontologies and semantic reasoning.

## Architecture

```
pre_shacl/
├── pre_processor.py          # Main entry point (legacy compatibility)
├── shape_preprocessor.py     # High-level orchestration
├── EntailEngine.py            # Entailment engine abstraction
├── entailment_base.py         # Common fixpoint loop logic
├── rdfs_entailment.py         # RDFS inference rules
├── owl_entailment.py          # OWL inference rules
├── shape_analyzer.py          # SHACL shape querying
├── shape_entailer.py          # Shape extension logic
├── rdf_list_utils.py          # RDF list manipulation
└── ignored_properties_manager.py  # Property filtering
```

### Module Responsibilities

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| `pre_processor.py` | Legacy API entry point | `pre_process_shacl_graph_full()` |
| `shape_preprocessor.py` | Main preprocessing pipeline | `preprocess_shacl_graph()`, `check_incongruences()` |
| `EntailEngine.py` | Unified entailment interface | `EntailEngine.entail()` |
| `entailment_base.py` | Fixpoint iteration logic | `run_fixpoint_entailment()` |
| `rdfs_entailment.py` | RDFS rules (subClassOf, domain/range) | `apply_rdfs_rules()`, `entail()` |
| `owl_entailment.py` | OWL rules (sameAs, equivalence) | `apply_owl_rules()`, `entail()` |
| `shape_analyzer.py` | Shape metadata extraction | `list_all_shape_names()`, `get_shape_property_paths()` |
| `shape_entailer.py` | Closed shape extension | `extend_shacl_shape()` |
| `rdf_list_utils.py` | RDF list operations | `get_rdf_list_items()`, `create_rdf_list()` |
| `ignored_properties_manager.py` | Property filtering | `get_current_ignored_properties()` |

## Installation

```bash
pip install rdflib pyshacl
```

## Quick Start

### Basic Usage

```python
from rdflib import Graph
from pre_shacl.pre_processor import pre_process_shacl_graph_full

# Load your data and shapes
data_graph = Graph()
data_graph.parse("data.ttl", format="turtle")

shapes_graph = Graph()
shapes_graph.parse("shapes.ttl", format="turtle")

# Apply RDFS preprocessing
entailed_data, entailed_shapes = pre_process_shacl_graph_full(
    data_graph, 
    shapes_graph, 
    regime='rdfs'  # Options: 'none', 'rdfs', 'owl-ld'
)

# Use entailed graphs for validation
from pyshacl import validate

conforms, report, text = validate(
    entailed_data,
    shacl_graph=entailed_shapes,
    inference='none'  # Inference already applied!
)
```

### Inference Levels

| Level | Description | Typical Runtime |
|-------|-------------|-----------------|
| `'none'` | No entailment | ~0ms (baseline) |
| `'rdfs'` | RDFS rules (subClassOf, domain/range, subPropertyOf) | +10-50ms |
| `'owl-ld'` | OWL-LD rules (sameAs, equivalentClass/Property) | +50-200ms |

## Examples

### Example 1: Type Inference with RDFS

```python
from rdflib import Graph, Namespace, RDF, RDFS, Literal
from rdflib.namespace import SH
from pre_shacl.pre_processor import pre_process_shacl_graph_full

EX = Namespace("http://example.org/")

# Data with class hierarchy
data = Graph()
data.add((EX.Person, RDF.type, RDFS.Class))
data.add((EX.Student, RDFS.subClassOf, EX.Person))
data.add((EX.alice, RDF.type, EX.Student))
data.add((EX.alice, EX.name, Literal("Alice")))

# Closed shape targeting Person
shapes = Graph()
shapes.add((EX.PersonShape, RDF.type, SH.NodeShape))
shapes.add((EX.PersonShape, SH.targetClass, EX.Person))
shapes.add((EX.PersonShape, SH.closed, Literal(True)))

# Preprocess
entailed_data, entailed_shapes = pre_process_shacl_graph_full(data, shapes, regime='rdfs')

# alice now has type Person (inferred from Student subClassOf Person)
assert (EX.alice, RDF.type, EX.Person) in entailed_data
```

### Example 2: Property Hierarchy and Closed Shapes

```python
from rdflib import Graph, Namespace, RDFS, Literal, URIRef
from rdflib.namespace import RDF, SH
from pre_shacl.pre_processor import pre_process_shacl_graph_full

EX = Namespace("http://example.org/")

# Data with property hierarchy
data = Graph()
data.add((EX.name, RDFS.subPropertyOf, RDFS.label))
data.add((EX.alice, RDF.type, EX.Person))
data.add((EX.alice, EX.name, Literal("Alice")))

# Closed shape with ex:name property
shapes = Graph()
shapes.add((EX.PersonShape, RDF.type, SH.NodeShape))
shapes.add((EX.PersonShape, SH.targetClass, EX.Person))
shapes.add((EX.PersonShape, SH.closed, Literal(True)))

prop_shape = URIRef(EX.PersonShape_name)
shapes.add((EX.PersonShape, SH.property, prop_shape))
shapes.add((prop_shape, SH.path, EX.name))

# Preprocess
entailed_data, entailed_shapes = pre_process_shacl_graph_full(data, shapes, regime='rdfs')

# Data now has rdfs:label (inferred from ex:name subPropertyOf rdfs:label)
assert (EX.alice, RDFS.label, Literal("Alice")) in entailed_data

# Shape extended with rdfs:label property to avoid false violations
shape_properties = set()
for _, _, prop in entailed_shapes.triples((EX.PersonShape, SH.property, None)):
    for _, _, path in entailed_shapes.triples((prop, SH.path, None)):
        shape_properties.add(path)

assert RDFS.label in shape_properties  # Shape was extended!
```

### Example 3: owl:sameAs Handling

```python
from rdflib import Graph, Namespace, OWL, Literal
from rdflib.namespace import RDF, SH
from pre_shacl.pre_processor import pre_process_shacl_graph_full

EX = Namespace("http://example.org/")

# Data with sameAs relation
data = Graph()
data.add((EX.alice, OWL.sameAs, EX.aliceSmith))
data.add((EX.alice, EX.name, Literal("Alice")))

shapes = Graph()
shapes.add((EX.PersonShape, RDF.type, SH.NodeShape))
shapes.add((EX.PersonShape, SH.closed, Literal(True)))

# OWL preprocessing
entailed_data, entailed_shapes = pre_process_shacl_graph_full(data, shapes, regime='owl-ld')

# sameAs is symmetric
assert (EX.aliceSmith, OWL.sameAs, EX.alice) in entailed_data

# Properties copied to equivalent entity
assert (EX.aliceSmith, EX.name, Literal("Alice")) in entailed_data

# owl:sameAs added to ignored properties in shape
ignored_props = list(entailed_shapes.triples((EX.PersonShape, SH.ignoredProperties, None)))
assert len(ignored_props) > 0
```

## Advanced Usage

### Using EntailEngine Directly

```python
from pre_shacl.EntailEngine import EntailEngine, InferenceLevel
from rdflib import Graph

data_graph = Graph()
data_graph.parse("data.ttl", format="turtle")

# Apply RDFS entailment
engine = EntailEngine(data_graph, InferenceLevel.RDFS)
engine.entail(data_graph)  # Graph modified in-place

# Apply OWL entailment
engine = EntailEngine(data_graph, InferenceLevel.OWL_LD)
engine.entail(data_graph)
```

### Shape Analysis

```python
from pre_shacl.shape_analyzer import (
    list_all_shape_names,
    get_shape_property_paths,
    get_all_target_classes_for_shape
)
from rdflib import Graph

shapes_graph = Graph()
shapes_graph.parse("shapes.ttl", format="turtle")

# Get all shape names
shape_names = list_all_shape_names(shapes_graph)
print(f"Found {len(shape_names)} shapes")

# Get properties for a specific shape
for shape in shape_names:
    properties = get_shape_property_paths(shape, shapes_graph)
    target_classes = get_all_target_classes_for_shape(shape, shapes_graph)
    print(f"Shape {shape}: {len(properties)} properties, targets {target_classes}")
```

## API Reference

### Main Entry Point

#### `pre_process_shacl_graph_full(data_graph, shacl_graph, regime) -> Tuple[Graph, Graph]`

Apply preprocessing to data and shapes graphs.

**Parameters:**
- `data_graph` (Graph): RDF data graph
- `shacl_graph` (Graph): SHACL shapes graph
- `regime` (str): Inference level - 'none', 'rdfs', or 'owl-ld'

**Returns:**
- Tuple of (entailed_data_graph, entailed_shapes_graph)

**Example:**
```python
entailed_data, entailed_shapes = pre_process_shacl_graph_full(
    data_graph, shapes_graph, regime='rdfs'
)
```

### Entailment Engine

#### `EntailEngine(data_graph, inference_level)`

Unified interface for applying entailment rules.

**Parameters:**
- `data_graph` (Graph): The graph to analyze
- `inference_level` (InferenceLevel): NONE, RDFS, or OWL_LD

**Methods:**
- `entail(graph)`: Apply entailment rules to graph in-place

### Shape Analyzer

#### `list_all_shape_names(shacl_graph) -> Set[URIRef]`

Get all shape URIs in a shapes graph.

#### `get_shape_property_paths(shape, shacl_graph) -> Set[URIRef]`

Get all sh:path values for a shape's property shapes.

#### `get_all_target_classes_for_shape(shape, shacl_graph) -> Set[URIRef]`

Get all sh:targetClass values for a shape.

## Performance Considerations

### Benchmarks (EnDe-Lite50 dataset)

| Method | Preprocessing | Validation | Total | Violations |
|--------|--------------|------------|-------|------------|
| PySHACL (no reasoning) | 0ms | 17.3ms | **17.3ms** | 3 |
| PySHACL (RDFS) | 0ms | 67.1ms | **67.1ms** | 3 |
| Closed-Shaper (RDFS) | 12.2ms | 55.6ms | **67.8ms** | 3 |

**Key Insight:** Closed-Shaper preprocessing adds ~12ms but enables `inference='none'` validation, matching PySHACL RDFS performance while extending closed shapes correctly.

### Optimization Tips

1. **Cache entailed graphs** - Preprocessing is idempotent
2. **Use 'none' when possible** - Skip entailment if no ontology is present
3. **Measure carefully** - Preprocessing cost is amortized over multiple validations

## Testing

Run the test suite:

```bash
# All pre_shacl tests
pytest tests/test_rdfs_entailment.py -v
pytest tests/test_owl_entailment.py -v
pytest tests/test_integration.py -v

# Specific test
pytest tests/test_owl_entailment.py::TestOWLSameAs::test_sameas_symmetric -v
```

## Known Limitations

1. **No OWL Full support** - Only OWL-LD (a subset of OWL DL)
2. **No custom entailment rules** - Fixed RDFS/OWL rules only
3. **No SPARQL-based shapes** - Only property paths supported
4. **Max iterations limit** - Prevents infinite loops (default: 1000 iterations)

## Contributing

See [CODE_QUALITY_ANALYSIS.md](../PreSHACL/CODE_QUALITY_ANALYSIS.md) for code quality guidelines.

## References

- **SHACL Specification:** https://www.w3.org/TR/shacl/
- **RDFS Semantics:** https://www.w3.org/TR/rdf-schema/
- **OWL 2 Profiles:** https://www.w3.org/TR/owl2-profiles/
- **Closed-Shaper Paper:** (Add citation if published)

## License

(Add license information)

## Changelog

### Version 2.0 (January 2026)
- ✅ Modular architecture with 11 focused modules
- ✅ Separated entailment rules into focused functions
- ✅ Comprehensive test suite (600+ lines)
- ✅ Type hints throughout
- ✅ Detailed documentation

### Version 1.0 (Legacy)
- Monolithic implementation
- Basic RDFS/OWL entailment
- Limited testing
