# Shape-Only Entailment Refactoring Plan

**Last Updated:** 2026-01-20 14:31 UTC  
**Review Rating:** 9.5/10 (production-ready)

## Overview

This document outlines a comprehensive plan to refactor the entailment system to **only entail the shapes graph** based on the ontology, without entailing the data graph.

### Current Architecture

Currently, the system:
1. Entails the **data graph** using ontology information (data becomes data + ontology-inferred triples)
2. Uses the entailed data graph to discover new properties via semantic relationships
3. Extends closed SHACL shapes with additional properties based on what was found in the entailed data

### Target Architecture (Mode A: Ontology-Only Closure)

The new system should:
1. **NOT entail the data graph** at all (no ABox dependence)
2. Entail the **shapes graph only** using the ontology (TBox-based closure)
3. **Input:** shapes graph + ontology
4. **Output:** entailed shapes graph
5. The ontology itself should remain unchanged (no entailment applied to it)
6. **No usage filtering:** all ontology-implied properties are added regardless of data graph content

---

## Semantics: What Changes in the Shapes Graph

### Formal Definition

For each closed shape, we define:

**Allowed(shape)** := **Paths(shape)** ∪ **Ignored(shape)**

Where:
- **Paths(shape)** = `{ p | shape sh:property [ sh:path p ] }`
- **Ignored(shape)** = properties in `sh:ignoredProperties` list (if present)

### Goal

Compute **Allowed'(shape)** using **ontology-only** closure under the specified regime, such that:

`Allowed'(shape)` = old system's `Allowed(shape)` for the same ontology+shapes inputs

**Scope:** "Identical output" is defined **only** over the allowed-set `Allowed(shape)` (not graph isomorphism), and only for well-formed inputs where the old system's added paths were ontology-derived (not data-specific). If the old system relied on data-only relationships not in the ontology, outputs will differ—treat this as an ontology bug to be fixed.

### Constraints

1. **Whitelisting only:** We only expand the set of allowed properties; no constraint propagation
2. **Path-only property shapes:** Newly added properties are represented as blank-node property shapes with **only** `sh:path` (no constraints like `sh:minCount`, `sh:datatype`, etc.)
3. **No ABox dependence:** Property extension is based solely on ontology (TBox), never on data graph instances
4. **No usage filtering:** If ontology says `q rdfs:subPropertyOf p`, and `p` is allowed, then `q` is added—regardless of whether `q` appears in the data

### Correctness Criterion

**Output is correct** ⟺ For each closed shape:
```
Paths_new(shape) ∪ Ignored_new(shape) = Paths_old(shape) ∪ Ignored_old(shape)
```

Where `_old` refers to the current data-based system and `_new` refers to the ontology-only system.

---

## Closure Rules (Mode A)

### 1. Property Closure (Core Rule)

For every allowed property `p` in a closed shape:
- Add all `q` such that `q rdfs:subPropertyOf* p` (transitive closure in ontology)
- This is the **inverse** direction: we find sub-properties of allowed properties

**Example:**
```turtle
# Ontology:
ex:writes rdfs:subPropertyOf ex:authors .
ex:pens rdfs:subPropertyOf ex:writes .

# Shape (closed):
ex:PersonShape sh:property [ sh:path ex:authors ] .

# After entailment:
ex:PersonShape sh:property [ sh:path ex:authors ] ;  # original
               sh:property [ sh:path ex:writes ] ;   # added (sub of ex:authors)
               sh:property [ sh:path ex:pens ] .     # added (transitive sub of ex:authors)
```

#### Core Closure Function

```python
def compute_subproperty_closure(ontology_graph: Graph) -> Dict[URIRef, Set[URIRef]]:
    """
    Precompute transitive closure of rdfs:subPropertyOf.
    
    Returns:
        subprops[p] = {q | q rdfs:subPropertyOf* p}
        (All sub-properties of p, including transitive)
    
    Implementation:
    1. Build equivalence relation E where p~q iff (p owl:equivalentProperty q)
    2. For each (p owl:equivalentProperty q): add both (p rdfs:subPropertyOf q) 
       and (q rdfs:subPropertyOf p) edges to an INTERNAL adjacency structure
    3. Compute transitive closure using fixpoint iteration (graph reachability)
    4. Cache result by ontology hash for reuse
    
    IMPORTANT: The ontology graph is NOT mutated. We build a derived internal
    adjacency structure (dict of sets) with bidirectional edges for equivalence.
    
    Algorithm: Fixpoint propagation until no new edges added.
    Complexity: O(n*e) where n=nodes, e=edges; typically fast for sparse ontologies.
    """
```

#### Shape Extension Functions

```python
def entail_shape_from_ontology(
    ontology_graph: Graph,
    shacl_graph: Graph,
    shape_properties: Set[URIRef],
    property_shape: URIRef,
    shape: URIRef,
    regime: str,
    old_ignored_properties: Set[URIRef],
    subprop_closure: Dict[URIRef, Set[URIRef]]
) -> Tuple[Graph, Set[URIRef]]:
    """
    Extend shape with sub-properties from ontology closure.
    
    Args:
        ontology_graph: The ontology (not used if subprop_closure provided)
        shacl_graph: The SHACL shapes graph (modified in place)
        shape_properties: Current allowed property paths
        property_shape: Existing property shape blank node
        shape: Shape URI being extended
        regime: Inference regime (rdfs, owl-ld, owlrl)
        old_ignored_properties: Properties to skip
        subprop_closure: Precomputed closure from compute_subproperty_closure()
    
    Returns:
        Tuple of (modified shacl_graph, updated shape_properties set)
    
    Logic:
    1. Get property path `p` from property_shape
    2. Look up subprops[p] from closure
    3. For each q in subprops[p]:
         - If q not in shape_properties and q not in old_ignored_properties:
           - Create blank node with ONLY sh:path = q
           - Mark as generated (ex:generatedBy "ontology_entailer")
           - Add to shape
    """
```

```python
def entail_has_value_from_ontology(
    ontology_graph: Graph,
    shape: URIRef,
    shacl_graph: Graph,
    shape_properties: Set[URIRef]
) -> Tuple[Graph, Set[URIRef]]:
    """
    Add property shapes based on OWL hasValue restrictions in ontology.
    
    Pattern matching (not full reasoning):
    - For each target class C (from sh:targetClass):
      - Find rdfs:subClassOf* _:b in ontology
      - If _:b has owl:onProperty ?p and owl:hasValue ?v:
        - Add property shape for ?p (path-only, marked as generated)
    
    Only active when regime = "owlrl"
    """
```

```python
def extend_shacl_shape_from_ontology(
    shape: URIRef,
    property_blank_nodes: Set[BNode],
    shacl_graph: Graph,
    shape_properties: Set[URIRef],
    ontology_graph: Graph,
    regime: str,
    old_ignored_properties: Set[URIRef],
    subprop_closure: Dict[URIRef, Set[URIRef]]
) -> Graph:
    """
    Main orchestrator for shape extension using ontology.
    
    Replaces extend_shacl_shape() but uses ontology instead of data_graph.
    
    Logic:
    1. For each existing property shape:
         - Call entail_shape_from_ontology() with precomputed closure
    2. If regime == "owlrl":
         - Call entail_has_value_from_ontology()
    """
```

#### Utility Functions

```python
def mark_generated_node(shacl_graph: Graph, node: BNode) -> None:
    """
    Mark a property shape as generated by ontology entailer.
    
    Adds: node ex:generatedBy "ontology_entailer" .
    
    This enables clean regeneration and testing.
    """
```

```python
def strip_generated_paths(shacl_graph: Graph) -> Graph:
    """
    Remove all generated property shapes from a shapes graph.
    
    Removes all blank nodes marked with ex:generatedBy "ontology_entailer".
    
    STATUS: Internal/testing utility only.
    
    NOTE: Copy-on-write is the mandatory approach for preprocessing.
    This function is provided for:
    - Debug/testing: inspect shapes before/after generation
    - Regression tests: strip generated nodes for comparison
    
    Not needed for normal operation since preprocessing always uses copy-on-write.
    """
```

```python
def extract_allowed_paths(shacl_graph: Graph, shape: URIRef) -> Set[URIRef]:
    """
    Extract Allowed(shape) = Paths(shape) ∪ Ignored(shape).
    
    Returns:
        Set of all allowed property URIs for the shape
    
    Logic:
    1. Collect all sh:path values from sh:property nodes
    2. Collect all properties from sh:ignoredProperties RDF list
    3. Return union**Test:** For each `_:gen` where `shape sh:property _:gen` and `_:gen` is marked as generated:
```sparql
ASK {
  _:gen sh:path ?p .
  FILTER NOT EXISTS { _:gen ?pred ?val . FILTER(?pred != sh:path && ?pred != ex:generatedBy) }
}
```

This ensures generated nodes have ONLY `sh:path` and `ex:generatedBy` predicates (no `sh:minCount`, `sh:datatype`, `sh:class`, etc.)

---

## Algorithmic Design Choice

### Decision Point: Closure Computation Strategy

Two approaches for computing property closure:

#### Option 1: Precompute Indexes (Recommended Default)

**Build once per ontology:**
```python
# Precompute inverse subPropertyOf closure
subprops: Dict[URIRef, Set[URIRef]] = {}
# subprops[p] = {q | q rdfs:subPropertyOf* p}

# Optionally also:
superprops: Dict[URIRef, Set[URIRef]] = {}
subclasses: Dict[URIRef, Set[URIRef]] = {}
```

**Extension algorithm:**
```
For each shape:
  For each allowed property p:
    For each q in subprops[p]:
      Add property shape for q
```

**Complexity:** O(#allowed paths × avg_subprops) per shape, with O(ontology_size) preprocessing once.

**Advantages:**
- Deterministic (set iteration over precomputed sets)
- Efficient for multiple shapes or repeated runs
- Enables caching by ontology hash

**Disadvantages:**
- Memory overhead for large ontologies
- Preprocessing cost upfront

#### Option 2: On-Demand DFS/BFS Per Seed Property

**For each allowed property `p`:**
```python
visited = set()
queue = [p]
while queue:
  current = queue.pop(0)
  for q where (q rdfs:subPropertyOf current):
    if q not in visited:
      visited.add(q)
      queue.append(q)
      add_property_shape(q)
```

**Complexity:** O(#allowed paths × ontology_edges) worst case, but often faster for sparse ontologies.

**Advantages:**
- Lower memory footprint
- No preprocessing needed
- Good for small ontologies or single-run scenarios

**Disadvantages:**
- Non-deterministic iteration order (must sort before adding)
- Repeated work if same ontology used multiple times

#### Selection Criterion

**Use Option 1 (precompute) if:**
- Running experiments with multiple shapes on same ontology
- Ontology size < 1M triples (fits in memory)
- Need to cache results across runs

**Use Option 2 (on-demand) if:**
- One-off preprocessing
- Very large ontology (> 1M triples)
- Ontology changes frequently

**Recommended:** Start with Option 1 with caching by ontology hash (graph fingerprint/checksum). Profile if performance becomes an issue.

#### Stable Ordering Requirement

For deterministic output (stable serialization, reproducible tests), **always iterate over closure sets in sorted order during generation**:

```python
# When adding generated nodes:
for p in sorted(allowed_properties, key=str):  # Stable iteration
    subprops = closure[p]
    for q in sorted(subprops, key=str):  # Stable iteration
        if q not in existing_paths:
            add_generated_property_shape(q)
```

This ensures:
- Identical blank node creation order across runs
- Stable serialization output
- Easier debugging and regression testing

---

## Implementation Architecture

### Split: Library vs Plumbing

#### Phase 1: Core Library Refactor (Must Pass Unit Tests)

**Files to create/modify:**
1. `pre_shacl/ontology_shape_entailer.py` (NEW)
2. `pre_shacl/shape_preprocessor.py` (MODIFY)
3. `pre_shacl/pre_processor.py` (UPDATE exports)

**Unit tests must pass before moving to Phase 2.**

#### Phase 2: Plumbing Updates (Integration Layer)

**Files to modify:**
1. `run_experiment.py`
2. `experiments/experiments_runner.py`
3. `run.py`
4. Other entry points

**These changes are mechanical once core library is correct.**

---

## Key Changes Required

### 1. Create New Ontology-Based Shape Entailer

**File to Create:** `pre_shacl/ontology_shape_entailer.py`

This new module will replace the data-graph-based entailment logic with ontology-based reasoning.

**Key Functions to Implement:**

```python
def entail_shape_from_ontology(
    ontology_graph: Graph,
    shacl_graph: Graph,
    shape_properties: Set,
    property_shape: URIRef,
    shape: URIRef,
    regime: str,
    old_ignored_properties: Set
) -> Tuple[Graph, Set]:
    """
    Extend shapes based on ontology relationships (not data graph).
    
    Logic:
    1. Get property path p from property_shape
    2. Look up subprops[p] from precomputed closure (see Closure Rules section)
       where subprops[p] = {q | q rdfs:subPropertyOf* p} (transitive closure)
    3. For each q in subprops[p], add new path-only property shape
    
    See "Closure Rules (Mode A)" section for formal definition of rdfs:subPropertyOf*.
    """
```

```python
def entail_has_value_from_ontology(
    ontology_graph: Graph,
    shape: URIRef,
    shacl_graph: Graph,
    shape_properties: Set
) -> Tuple[Graph, Set]:
    """
    Add property shapes based on OWL hasValue restrictions in ONTOLOGY.
    
    Instead of checking data_graph for target class subclass relationships,
    this checks the ontology_graph.
    """
```

```python
def extend_shacl_shape_from_ontology(
    shape: URIRef,
    property_blank_nodes: Set,
    shacl_graph: Graph,
    shape_properties: Set,
    ontology_graph: Graph,
    regime: str,
    old_ignored_properties: Set
) -> Graph:
    """
    Main orchestrator for shape extension using ontology.
    
    Replaces extend_shacl_shape() but uses ontology instead of data_graph.
    """
```

---

### 2. Modify Shape Preprocessor

**File to Modify:** `pre_shacl/shape_preprocessor.py`

**Function to Refactor:** `pre_process_shacl_graph_full()`

**Current Signature:**
```python
def pre_process_shacl_graph_full(data_graph: Graph, shacl_graph: Graph, regime: str) -> Tuple[Graph, Graph]:
```

**New Signature:**
```python
def pre_process_shacl_graph_full(shacl_graph: Graph, ontology_graph: Graph, regime: str) -> Graph:
```

**Changes Required:**

1. **Remove data graph entailment:**
   - Delete lines that instantiate `EntailEngine` with data_graph
   - Delete lines that call `engine.entail()` on data_graph
   - Remove the return of entailed_data_graph

2. **Add ontology parameter:**
   - Accept `ontology_graph` as input parameter
   - Do NOT entail the ontology (keep it as-is)

3. **Update shape extension logic:**
   - Replace call to `extend_shacl_shape()` with `extend_shacl_shape_from_ontology()`
   - Pass `ontology_graph` instead of `data_graph`

4. **Update incongruence checking:**
   - Modify `check_incongruences()` to accept ontology_graph instead of data_graph
   - Check ontology for subClassOf and domain relationships

**Detailed Changes:**

```python
# OLD CODE (lines ~111-114):
engine = EntailEngine(data_graph, regime)
# The engine entails the data graph given a regime
entailed_data_graph = engine.entail()
if entailed_data_graph:
    data_graph = entailed_data_graph
else:
    return data_graph, shacl_graph

# NEW CODE:
# Remove all data graph entailment - ontology remains un-entailed

# OLD CODE (line ~127):
warning_messages += check_incongruences(shape_uri, data_graph, shacl_graph, shape_property_paths[shape_uri])

# NEW CODE:
warning_messages += check_incongruences(shape_uri, ontology_graph, shacl_graph, shape_property_paths[shape_uri])

# OLD CODE (lines ~128-129):
shacl_graph = extend_shacl_shape(shape_uri, shape_with_properties[shape_uri], shacl_graph,
                                shape_property_paths[shape_uri], data_graph, regime, old_ignored_properties)

# NEW CODE:
shacl_graph = extend_shacl_shape_from_ontology(shape_uri, shape_with_properties[shape_uri], shacl_graph,
                                               shape_property_paths[shape_uri], ontology_graph, regime, 
                                               old_ignored_properties)

# OLD CODE (final return):
return data_graph, shacl_graph

# NEW CODE (final return):
return shacl_graph
```

---

### 3. Update check_incongruences Function

**File to Modify:** `pre_shacl/shape_preprocessor.py`

**Function:** `check_incongruences()`

**Changes:**
- Change parameter from `data_graph` to `ontology_graph`
- Update all references to use ontology_graph instead

```python
# OLD:
def check_incongruences(shape: URIRef, data_graph: Graph, shacl_graph: Graph, 
                       shape_properties: Set) -> List[str]:

# NEW:
def check_incongruences(shape: URIRef, ontology_graph: Graph, shacl_graph: Graph, 
                       shape_properties: Set) -> List[str]:
```

**Update all triple queries:**
```python
# OLD:
for class_name, _, _ in data_graph.triples((None, RDFS.subClassOf, target_class)):

# NEW:
for class_name, _, _ in ontology_graph.triples((None, RDFS.subClassOf, target_class)):

# OLD:
for property_name, _, _ in data_graph.triples((None, RDFS.domain, target_class)):

# NEW:
for property_name, _, _ in ontology_graph.triples((None, RDFS.domain, target_class)):
```

**Semantic change:** This now validates **TBox/shape consistency** (not instance consistency). It checks whether closed shapes might conflict with ontology structure (e.g., target class has subclasses with additional properties), independent of actual data.

---

### 4. Update Backward Compatibility Wrapper

**File to Modify:** `pre_shacl/pre_processor.py`

This file re-exports functions for backward compatibility. Update imports to include the new ontology-based functions:

```python
# Add to imports:
from pre_shacl.ontology_shape_entailer import (
    entail_shape_from_ontology,
    entail_has_value_from_ontology,
    extend_shacl_shape_from_ontology
)

# Add to __all__:
__all__ = [
    # ... existing exports ...
    "entail_shape_from_ontology",
    "entail_has_value_from_ontology",
    "extend_shacl_shape_from_ontology",
]
```

---

### 5. Update Experiment Runner

**File to Modify:** `run_experiment.py`

**Function:** `run_pyshacl()`

**Changes Required:**

1. **Add ontology loading:**
   ```python
   # Add parameter to function signature:
   def run_pyshacl(dataset_name, g, sg, ontology_path, method, inference_method, pre_shacl=False):
   ```

2. **Update preprocessing call:**
   ```python
   # OLD (lines ~42-43):
   if pre_shacl:
       g, sg = pre_process_shacl_graph_full(g, sg, inference_method)
   
   # NEW:
   if pre_shacl:
       ontology = Graph()
       if ontology_path:
           ontology.parse(ontology_path)
       sg = pre_process_shacl_graph_full(sg, ontology, inference_method)
   ```

3. **Update validation call:**
   ```python
   # Data graph is no longer pre-entailed, so keep original inference_method
   # OLD:
   if pre_shacl:
       # Because the graph has already been fully entailed
       inference_method = 'none'
   
   # NEW:
   # Remove this block - data graph is NOT entailed anymore
   # Keep inference_method as-is for pyshacl to handle data graph entailment
   ```

---

### 6. Update run_reshacl Function

**File to Modify:** `run_experiment.py`

1. **Create closure computation module**
   - `compute_subproperty_closure()` with equivalentProperty preprocessing
   - Unit test: verify transitive closure correctness
   - Unit test: verify equivalentProperty → bidirectional subPropertyOf

2. **Create ontology shape entailer**
   - File: `pre_shacl/ontology_shape_entailer.py`
   - Implement: `entail_shape_from_ontology()`, `entail_has_value_from_ontology()`
   - Implement: `extend_shacl_shape_from_ontology()`
   - Implement: `mark_generated_node()`, `strip_generated_paths()`, `extract_allowed_paths()`

3. **Modify shape preprocessor**
   - File: `pre_shacl/shape_preprocessor.py`
   - Change signature: `pre_process_shacl_graph_full(shacl_graph, ontology_graph, regime)`
   - Remove data graph entailment
   - Call new ontology-based functions
   - Update `check_incongruences()` to use ontology

4. **Update backward compatibility wrapper**
   - File: `pre_shacl/pre_processor.py`
   - Export new functions
   - Remove exports of deleted functions

**Gate:** All unit tests pass before proceeding to Phase 2.

### Phase 2: Plumbing (Integration Layer)

5. **Update experiment runner**
   - File: `run_experiment.py`
   - Add ontology loading
   - Update `run_pyshacl()` and `run_reshacl()` signatures
   - Pass ontology to preprocessor

6. **Update experiments pipeline**
   - File: `experiments/experiments_runner.py`
   - Update `ValidationPipeline._preprocess_closed_shaper()`
   - Add ontology loading to pipeline methods

7. **Update main entry points**
   - File: `run.py`
   - Ensure ontology is loaded and passed
   - Update all function calls

### Phase 3: Testing & Validation

8. **Implement regression tests**
   - Test: allowed-set equality (old vs new)
   - Test: determinism (run twice, compare outputs)
   - Test: idempotence (preprocess twice, no changes second time)
   - Test: generated node invariant (path-only, no constraints)

9. **Run on real datasets**
   - Compare allowed-sets for all shapes
   - Verify no violations introduced
   - Profile performance

### Phase 4: Cleanup

10. **Delete old code**
    - Remove or deprecate `pre_shacl/shape_entailer.py`
    - Remove data-based entailment from `EntailEngine` usage
    - Clean up commented code

11. **Update documentation**
    - README.md
    - REFACTORING_SUMMARY.md
    - Docstrings
    - Add MIGRATION_GUIDE.md if needed
1. **Update _preprocess_closed_shaper method:**
   ```python
   # OLD:
   def _preprocess_closed_shaper(self,
                                  data_graph: rdflib.Graph,
                                  shapes_graph: rdflib.Graph,
                                  inference_lvl: str) -> Tuple[rdflib.Graph, rdflib.Graph]:
       """Apply Closed-Shaper preprocessing."""
       return pre_process_shacl_graph_full(data_graph, shapes_graph, inference_lvl)
   
   # NEW:
   def _preprocess_closed_shaper(self,
                                  shapes_graph: rdflib.Graph,
                                  ontology_graph: rdflib.Graph,
                                  inference_lvl: str) -> rdflib.Graph:
       """Apply Closed-Shaper preprocessing using ontology."""
       return pre_process_shacl_graph_full(shapes_graph, ontology_graph, inference_lvl)
   ```

2. **Add ontology loading to pipeline:**
   - Add ontology_path parameter to relevant methods
   - Load ontology graph in _load_graphs or create separate method

3. **Update all callers:**
   - Any method that calls `_preprocess_closed_shaper()` needs to pass ontology instead of data_graph
   - Update `_preprocess_combined()` accordingly
Correctness Criterion

**Primary test oracle:** For each closed shape:
```
extract_allowed_paths(shape_new) == extract_allowed_paths(shape_old)
```

Where:
- `shape_old` = shape after old system (data-based) preprocessing
- `shape_new` = shape after new system (ontology-only) preprocessing

### Unit Tests

#### 1. Closure Computation Tests

**File:** `tests/test_ontology_closure.py`

```python
def test_subproperty_transitive_closure():
    """Test transitive closure of rdfs:subPropertyOf."""
    ont = Graph()
    ont.add((p1, RDFS.subPropertyOf, p2))
    ont.add((p2, RDFS.subPropertyOf, p3))
    
    closure = compute_subproperty_closure(ont)
    
    assert p1 in closure[p3]  # transitive
    assert p1 in closure[p2]  # direct
    assert p2 in closure[p3]  # direct

def test_equivalent_property_becomes_bidirectional():
    """Test owl:equivalentProperty → rdfs:subPropertyOf (both ways)."""
    ont = Graph()
    ont.add((p1, OWL.equivalentProperty, p2))
    
    closure = compute_subproperty_closure(ont)
    
    assert p1 in closure[p2]
    assert p2 in closure[p1]

def test_closure_determinism():
    """Test closure is deterministic regardless of triple order."""
    ont1 = Graph()
    # Add triples in one order
    ont1.add((p1, RDFS.subPropertyOf, p2))
    ont1.add((p2, RDFS.subPropertyOf, p3))
    
    ont2 = Graph()
    # Add triples in different order
   Operational Features

### Clean Regeneration

**Problem:** Repeated preprocessing could accumulate generated nodes.

**Solution: Copy-on-write (mandatory approach)**
```python
def pre_process_shacl_graph_full(shacl_graph, ontology_graph, regime):
    # Create fresh output graph
    result = Graph()
    result += shacl_graph  # Copy input
    # Extend result with generated nodes...
    return result
```

**Rationale:**
- Input shapes graph remains immutable (no side effects)
- Clear separation between input and output
- Enables easy comparison testing
- Natural idempotence: running on fresh input always produces same result

**Note:** `strip_generated_paths()` utility is still useful for testing/debugging, but preprocessing always uses copy-on-write.

### Caching by Ontology Hash

**Optimization:** Cache closure computation per ontology.

```python
_closure_cache: Dict[str, Dict[URIRef, Set[URIRef]]] = {}

def compute_subproperty_closure(ontology_graph: Graph, ontology_id: Optional[str] = None) -> Dict[URIRef, Set[URIRef]]:
    # Compute stable hash of ontology
    if ontology_id is None:
        # Hash sorted triples (stable for same content)
        triples_sorted = sorted((str(s), str(p), str(o)) for s, p, o in ontology_graph)
        triple_str = '\n'.join(f"{s} {p} {o}" for s, p, o in triples_sorted)
        ont_hash = hashlib.sha256(triple_str.encode()).hexdigest()
    else:
        # Use caller-provided ID (e.g., filepath + mtime)
        ont_hash = ontology_id
    
    if ont_hash in _closure_cache:
        logger.debug(f"Using cached closure for ontology {ont_hash[:8]}")
        return _closure_cache[ont_hash]
    
    # Compute closure
    closure = _compute_closure_impl(ontology_graph)
    
    # Cache result
    _closure_cache[ont_hash] = closure
    return closure
```

**Note:** Avoid `serialize(format='nt')` for hashing—N-Triples serialization order is unstable and blank node skolemization varies. Use sorted triples or caller-provided ontology ID.

This avoids recomputing closure when running multiple experiments on same ontology.

---

## Removed from Plan (Contradictions with Constraints)

### ❌ Data Graph Entailment Discovery

**Old plan statement:** "Uses the entailed data graph to discover new properties"

**Why removed:** Violates "no ABox dependence" constraint. New system uses only ontology.

### ❌ propertyChainAxiom Support (for now)

**Old plan statement:** "Test with property chain axioms in ontology"

**Why removed:** Excluded from initial implementation per user requirements. Can be added later.

### ❌ Ontology Completeness Validation from Data

**Old plan statement:** "Provide utility to extract ontology axioms from data if needed"

**Why removed:** Violates "no data usage" constraint. If ontology is incomplete, fix ontology—don't extract from data.

### ❌ Usage Filtering

**Old plan statement:** (implicit in some examples)

**Why removed:** Mode A explicitly includes all ontology-implied properties regardless of data graph content.

---

## Potential Issues and Solutions

### Issue 1: Incomplete Ontology

**Problem:** Ontology might not contain all relationships that were discovered in the old data-based system.

**Solution:** 
- **Treat as ontology bug:** If shapes reference properties not in ontology, fix the ontology (not the data or system)
- Add validation step to check ontology completeness and log warnings
- Document missing axioms and update ontology accordingly

**Not a solution:** Extracting axioms from data (violates "no data usage" constraint)

### Issue 2: Performance with Large Ontologies

**Problem:** Very large ontologies might be slow to process.

**Solution:**
- **Primary:** Use precomputed closure with caching (see "Algorithmic Design Choice" section)
- **Optimization 1:** Extract relevant subset (properties/classes referenced in shapes only)
- **Optimization 2:** Lazy closure—compute only when first shape references a property
- Profile before optimizing—most ontologies are small enough

**Criterion:** If closure computation takes > 1 second, profile and optimize.

### Issue 3: Non-Identical Results During Migration

**Problem:** Ontology-based entailment might produce different allowed-sets than data-based.

**Root causes:**
1. Data graph contained relationships not in ontology (data was used as schema source)
2. Data-based system had bugs (order-dependent, non-idempotent)
3. Ontology is incomplete

**Solution:**
- **Run comparison tests** on real datasets
- **Document any differences** with root cause analysis
- **Fix ontology** if relationships are missing
- Accept that "identical" means identical for well-formed ontology+shapes inputs

### Issue 4: Determinism with Blank Nodes

**Problem:** Blank node IDs might vary across runs, making graph-level comparison difficult.

**Official solution: Use allowed-set equality for testing (ignore blank node IDs)**

Rationale:
- Correctness criterion is `Allowed(shape)` equality, not graph isomorphism
- Blank node IDs are implementation detail, not semantic content
- Simpler than maintaining stable hash-based blank node generation
- Works regardless of RDFLib's internal blank node allocation

**Implementation:**
```python
# Don't compare graphs directly:
assert not isomorphic(shapes_old, shapes_new)  # ❌ Fragile

# Do compare allowed-sets:
allowed_old = extract_allowed_paths(shapes_old, shape)
allowed_new = extract_allowed_paths(shapes_new, shape)
assert allowed_old == allowed_new  # ✅ Robust
```

**Optional (for debugging only):** Use stable iteration order (see "Stable Ordering Requirement") to produce consistent serialization—but don't rely on it for correctness tests.

---

## Helper: Extract Allowed Paths Implementation

For your specific RDF encoding (adjust if needed):

```python
def extract_allowed_paths(shacl_graph: Graph, shape: URIRef) -> Set[URIRef]:
    """
    Extract Allowed(shape) = Paths(shape) ∪ Ignored(shape).
    
    Args:
        shacl_graph: The SHACL shapes graph
        shape: Shape URI
    
    Returns:
        Set of all allowed property URIs
    """
    allowed = set()
    
    # 1. Collect all sh:path values from sh:property nodes
    for _, _, prop_node in shacl_graph.triples((shape, SH.property, None)):
        path = shacl_graph.value(prop_node, SH.path)
        if path and isinstance(path, URIRef):
            allowed.add(path)
    
    # 2. Collect all properties from sh:ignoredProperties RDF list
    ignored_list = shacl_graph.value(shape, SH.ignoredProperties)
    if ignored_list:
        from pre_shacl.rdf_list_utils import get_elements_in_rdf_list
        ignored_props = get_elements_in_rdf_list(shacl_graph, ignored_list)
        allowed.update(p for p in ignored_props if isinstance(p, URIRef))
    
    return allowed
```

**Usage in tests:**
```python
allowed_old = extract_allowed_paths(shapes_old, shape)
allowed_new = extract_allowed_paths(shapes_new, shape)
assert allowed_old == allowed_new, f"Allowed-set mismatch for {shape}"
```

This makes your equality tests one-liners and focuses on the semantic correctness criterion.

---

## Summary

### Transformation

**From (data-based):**
- **Input:** data graph + shapes graph (+ ontology embedded in data)
- **Process:** entail data graph, use entailed data to discover properties, extend shapes
- **Output:** entailed data + entailed shapes

**To (ontology-only):**
- **Input:** shapes graph + ontology (data graph not used)
- **Process:** compute property closure from ontology, extend shapes with path-only property shapes
- **Output:** entailed shapes (data graph unchanged)

### Transformation

**From (data-based):**
- **Input:** data graph + shapes graph (+ ontology embedded in data)
- **Process:** entail data graph, use entailed data to discover properties, extend shapes
- **Output:** entailed data + entailed shapes

**To (ontology-only):**
- **Input:** shapes graph + ontology (data graph not used)
- **Process:** compute property closure from ontology, extend shapes with path-only property shapes
- **Output:** entailed shapes (data graph unchanged)

### Key Insights

1. **Semantic relationships** needed to extend shapes (subPropertyOf, hasValue) should come from the **ontology (TBox)**, not the **data (ABox)**

2. **Mode A (no usage filtering):** If ontology says `q subPropertyOf p`, and shape allows `p`, then shape must allow `q`—regardless of whether `q` appears in data

3. **Correctness = allowed-set equality:** Two systems are equivalent if they produce the same `Allowed(shape)` for each closed shape

4. **Path-only generation:** New property shapes contain **only** `sh:path` (no constraints), preventing accidental semantic changes

5. **Determinism + idempotence:** Closure-based approach with stable ordering ensures reliable, reproducible results

### Benefits

1. **Clearer separation of concerns:**
   - Shapes graph entailment = preprocessing (TBox)
   - Data graph entailment = validation time (ABox, handled by pyshacl)

2. **Performance improvement:**
   - No need to entail potentially large data graphs during preprocessing
   - Precomputed closures cached and reused across experiments

3. **Deterministic and reproducible:**
   - Stable iteration order guarantees identical output across runs
   - Idempotent operation enables safe re-execution

4. **More accurate:**
   - Ontology explicitly defines the semantic model (TBox)
   - Don't rely on data (ABox) to discover schema information
   - No usage filtering—all ontology-implied properties included

5. **Easier to understand and maintain:**
   - Input/output clearer: shapes + ontology → entailed shapes
   - No confusion about what gets entailed when
   - Testable with simple allowed-set equality

6. **Future-proof for Virtuoso migration:**
   - Explicit closure computation translates directly to SPARQL queries
   - No hidden data-dependent behavior
   - TBox/ABox separation matches Virtuoso's reasoning architecture

### Implementation Strategy

1. **Precompute closure** (recommended): Build `subprops[p]` index once per ontology, cache by hash
2. **Mark generated nodes** with `ex:generatedBy` for clean regeneration and testing
3. **Hard switch** to new system—no dual codepaths or fallback to old behavior
4. **Stable ordering**: Always iterate sorted for deterministic output
5. **Test with allowed-set equality** as primary correctness oracle
6. **Regression tests during migration only**, then freeze as fixtures
7. **Profile before optimizing**—most ontologies are small enough for naive closure

This plan is now **formally specified**, **deterministic**, **testable**, and aligned with constraints (no data usage, Mode A, ontology-only, path-only generation, copy-on-write mandatory).

---

## Correctness Testing

### Test Oracle

**Primary test oracle:** For each closed shape:
```
extract_allowed_paths(shape_new) == extract_allowed_paths(shape_old)
```

Where:
- `shape_old` = shape after old system (data-based) preprocessing
- `shape_new` = shape after new system (ontology-only) preprocessing

### Unit Tests

#### 1. Closure Computation Tests

**File:** `tests/test_ontology_closure.py`

```python
def test_subproperty_transitive_closure():
    """Test transitive closure of rdfs:subPropertyOf."""
    ont = Graph()
    ont.add((p1, RDFS.subPropertyOf, p2))
    ont.add((p2, RDFS.subPropertyOf, p3))
    
    closure = compute_subproperty_closure(ont)
    
    assert p1 in closure[p3]  # transitive
    assert p1 in closure[p2]  # direct
    assert p2 in closure[p3]  # direct

def test_equivalent_property_becomes_bidirectional():
    """Test owl:equivalentProperty → rdfs:subPropertyOf (both ways)."""
    ont = Graph()
    ont.add((p1, OWL.equivalentProperty, p2))
    
    closure = compute_subproperty_closure(ont)
    
    assert p1 in closure[p2]
    assert p2 in closure[p1]

def test_closure_determinism():
    """Test closure is deterministic regardless of triple order."""
    ont1 = Graph()
    # Add triples in one order
    ont1.add((p1, RDFS.subPropertyOf, p2))
    ont1.add((p2, RDFS.subPropertyOf, p3))
    
    ont2 = Graph()
    # Add triples in different order
    ont2.add((p2, RDFS.subPropertyOf, p3))
    ont2.add((p1, RDFS.subPropertyOf, p2))
    
    closure1 = compute_subproperty_closure(ont1)
    closure2 = compute_subproperty_closure(ont2)
    
    assert closure1 == closure2
```

#### 2. Shape Extension Tests

**File:** `tests/test_shape_extension.py`

```python
def test_simple_subproperty_extension():
    """Test basic subPropertyOf extension."""
    shapes = Graph()
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    ont = Graph()
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    allowed = extract_allowed_paths(result, shape)
    assert p_super in allowed
    assert p_sub in allowed

def test_generated_nodes_are_path_only():
    """Test generated property shapes have only sh:path."""
    shapes = Graph()
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    shapes.add((pshape, SH.minCount, Literal(1)))  # existing constraint
    
    ont = Graph()
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    # Find generated nodes
    for _, _, gen_node in result.triples((shape, SH.property, None)):
        if result.value(gen_node, EX.generatedBy):
            path = result.value(gen_node, SH.path)
            assert path == p_sub
            # Count predicates on generated node
            predicates = set(p for _, p, _ in result.triples((gen_node, None, None)))
            # Should only have sh:path and ex:generatedBy
            assert predicates == {SH.path, EX.generatedBy}

def test_idempotence():
    """Test that preprocessing twice yields no changes."""
    shapes = Graph()
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    ont = Graph()
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    result1 = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    result2 = pre_process_shacl_graph_full(result1, ont, "rdfs")
    
    allowed1 = extract_allowed_paths(result1, shape)
    allowed2 = extract_allowed_paths(result2, shape)
    
    assert allowed1 == allowed2
    # Also verify graph size hasn't grown
    assert len(result1) == len(result2)
```

#### 3. Regression Tests (Old vs New Allowed-Set Equality)

**File:** `tests/test_regression_allowed_sets.py`

**Lifecycle:** These tests exist **only during migration** to verify parity. Once parity is confirmed:
1. Freeze expected allowed-sets as fixtures (e.g., `fixtures/expected_allowed_sets.json`)
2. Convert tests to compare against frozen fixtures (not old code)
3. Remove dependency on `old_pre_process_shacl_graph_full`
4. Delete old implementation

```python
def test_allowed_set_equality_simple():
    """Compare old and new system on simple subPropertyOf case."""
    # MIGRATION-ONLY TEST: Will be replaced with fixture-based test
    # Setup
    data = Graph()  # Empty data for new system
    shapes = Graph()
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    ont = Graph()
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    # Old system (requires data+ontology merged)
    data_with_ont = data + ont
    _, shapes_old = old_pre_process_shacl_graph_full(data_with_ont, shapes, "rdfs")
    allowed_old = extract_allowed_paths(shapes_old, shape)
    
    # New system
    shapes_new = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed_new = extract_allowed_paths(shapes_new, shape)
    
    assert allowed_old == allowed_new

def test_allowed_set_against_fixture():
    """POST-MIGRATION TEST: Compare against frozen expected output."""
    # Once parity confirmed, use this pattern instead:
    shapes = load_graph("fixtures/dbpedia_shapes.ttl")
    ont = load_graph("fixtures/dbpedia_ontology.owl")
    expected = load_json("fixtures/expected_allowed_sets.json")
    
    shapes_new = pre_process_shacl_graph_full(shapes, ont, "owlrl")
    
    for shape_uri, expected_paths in expected.items():
        actual = extract_allowed_paths(shapes_new, URIRef(shape_uri))
        assert actual == set(expected_paths), f"Mismatch for {shape_uri}"
```

#### 4. Invariant Tests

**File:** `tests/test_invariants.py`

```python
def test_no_data_graph_mutation():
    """Verify data graph is never modified."""
    data = Graph()
    data.add((s, p, o))
    data_copy = Graph()
    data_copy += data
    
    shapes = Graph()
    ont = Graph()
    
    # New system should not touch data
    _ = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    assert isomorphic(data, data_copy)

def test_determinism_multiple_runs():
    """Test outputs are identical across multiple runs."""
    shapes = Graph()
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p1))
    
    ont = Graph()
    ont.add((p2, RDFS.subPropertyOf, p1))
    ont.add((p3, RDFS.subPropertyOf, p1))
    
    results = []
    for _ in range(5):
        result = pre_process_shacl_graph_full(shapes.copy(), ont, "rdfs")
        allowed = extract_allowed_paths(result, shape)
        results.append(allowed)
    
    # All runs should produce identical sets
    assert all(r == results[0] for r in results)
```

### Integration Tests

**File:** `tests/test_integration_ontology.py`

Run full pipeline with ontology-only preprocessing:
1. Load shapes, ontology
2. Preprocess shapes
3. Validate against data (with inference at validation time)
4. Verify violations match expected

---

## Implementation Sequence

See "Implementation Plan" section earlier for detailed phase breakdown. Summary:

### Phase 1: Core Library (Must Pass Unit Tests)
1. Create closure computation module with equivalentProperty handling
2. Create `pre_shacl/ontology_shape_entailer.py` with new functions
3. Modify `pre_shacl/shape_preprocessor.py` signature and logic
4. Update exports in `pre_shacl/pre_processor.py`

### Phase 2: Plumbing (Integration Layer)
5. Update `run_experiment.py` to load ontology and pass to preprocessor
6. Update `experiments/experiments_runner.py` pipeline methods
7. Update all entry points (`run.py`, etc.)

### Phase 3: Testing & Validation
8. Implement unit tests (closure, extension, idempotence, determinism)
9. Implement regression tests (old vs new allowed-set equality, migration-only)
10. Run on real datasets and profile

### Phase 4: Cleanup
11. Delete `pre_shacl/shape_entailer.py` and old data-based code
12. Convert regression tests to fixture-based (remove old code dependency)
13. Update documentation (README, REFACTORING_SUMMARY, docstrings)

---

## Migration Notes

### Backward Compatibility

**Breaking changes:**
- `pre_process_shacl_graph_full()` signature changed from `(data_graph, shacl_graph, regime)` to `(shacl_graph, ontology_graph, regime)`
- Return value changed from `(data_graph, shapes_graph)` to `shapes_graph`
- All calling code must be updated

**Hard switch:** No dual codepaths. Old function signature deleted entirely.

### Documentation Updates

Update these files:
- `README.md` - Update usage examples
- `REFACTORING_SUMMARY.md` - Document this major change
- Docstrings in all modified functions
- Add `MIGRATION_GUIDE.md` if needed for external users
