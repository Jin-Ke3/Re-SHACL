import logging
import rdflib
from rdflib import Graph, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS, SH
from typing import Set, Dict, Tuple, List, Optional
from EntailEngine import EntailEngine, InferenceLevel

logger = logging.getLogger(__name__)


def list_all_shape_names(shacl_graph: Graph) -> Set[URIRef]:
    """Return a set of all SHACL NodeShape URIs in the graph."""
    shape_names = set()
    for s, p, o in shacl_graph.triples((None,
                                        RDF.type,
                                        SH.NodeShape)):
        shape_names.add(s)
    return shape_names


def map_shapes_to_properties(shacl_graph: Graph, shape_names: Set[URIRef]) -> Dict[URIRef, Set]:
    """Create a mapping from each shape to its property shapes."""
    shape_with_properties = {}
    for shape in shape_names:
        property_shapes = set(shacl_graph.objects(URIRef(shape),
                                                  SH.property))
        shape_with_properties[shape] = property_shapes

    return shape_with_properties


def get_shape_property_paths(shacl_graph: Graph, shape_names: Set[URIRef], shape_with_properties: Dict[URIRef, Set]) -> Dict[URIRef, Set]:
    """Extract property paths for each shape from its property shapes."""
    shape_property_paths = {}
    for shape in shape_names:
        property_paths = set()
        for property_shape in shape_with_properties[shape]:
            property_path = shacl_graph.value(property_shape, SH.path)
            property_paths.add(property_path)
        shape_property_paths[shape] = property_paths

    return shape_property_paths


def entail_shape_graph(data_graph: Graph, regime: str, shacl_graph: Graph, shape_properties: Set, property_shape: URIRef, shape: URIRef, old_ignored_properties: Set) -> Tuple[Graph, Set]:
    """Add new property shapes based on entailment in the data graph."""
    subgraph = get_subgraph_for_entailment(data_graph, regime)
    property_shape_path = shacl_graph.value(property_shape,
                                            SH.path)

    for dg_s, dg_p, dg_o in subgraph.triples((None,
                                              None,
                                              URIRef(property_shape_path))):
        # Check if the new property is not already in the shape properties
        if dg_s not in shape_properties and dg_s not in old_ignored_properties:
            # Create a new property shape
            property_node = BNode()
            shacl_graph.add((URIRef(shape), SH.property, property_node))
            # Add the path
            shacl_graph.add((property_node, SH.path, dg_s))

            shape_properties.add(dg_s)
            logger.info(f"Added new property path {dg_s}")

    return shacl_graph, shape_properties


def get_all_target_classes_for_shape(shape: URIRef, shacl_graph: Graph) -> Set:
    """Get all target classes for a SHACL shape."""
    target_classes = set()

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetClass, None)):
        target_classes.add(target_property)

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetSubjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.domain, None)):
            target_classes.add(class_name)

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetObjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.range, None)):
            target_classes.add(class_name)

    return target_classes


def entail_has_value_on_property(data_graph: Graph, shape: URIRef, shacl_graph: Graph, shape_properties: Set) -> Tuple[Graph, Set]:
    """Add property shapes based on OWL hasValue restrictions."""
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    if not target_classes:
        return shacl_graph, shape_properties

    for target_class in target_classes:
        for _, _, superclass_name in data_graph.triples((URIRef(target_class),
                                                         RDFS.subClassOf,
                                                         None)):

            on_property_value = data_graph.value(subject=superclass_name, predicate=OWL.onProperty)
            if on_property_value in shape_properties:
                continue

            bn_has_value_exists = data_graph.value(subject=superclass_name, predicate=OWL.hasValue) is not None
            bn_on_property_exists = on_property_value is not None

            if bn_has_value_exists and bn_on_property_exists:
                property_node = BNode()
                shacl_graph.add((URIRef(shape), SH.property, property_node))
                shacl_graph.add((property_node, SH.path, on_property_value))
                shape_properties.add(on_property_value)
                logger.info(f"Added new property path {on_property_value}")

    return shacl_graph, shape_properties


def entail_property_chain_axiom(data_graph: Graph, shacl_graph: Graph, shape: URIRef, shape_properties: Set) -> Tuple[Graph, Set]:
    """Add property shapes based on OWL property chain axioms."""
    # Get the first element of the list and if it matches, add s to the SHACL shape
    for new_property, p, list_of_elements in data_graph.triples((None,
                                                                 OWL.propertyChainAxiom,
                                                                 None)):
        if new_property in shape_properties:
            continue

        elements = get_elements_in_rdf_list(data_graph, list_of_elements)

        # This says that if the first element of a property chain is in the list of elements
        # That we can assume that the whole chain occurs - because the probability is larger than zero
        # This cannot cause violations - it can cause additional properties, however
        if elements[0] in shape_properties:
            property_node = BNode()
            shacl_graph.add((URIRef(shape), SH.property, property_node))
            shacl_graph.add((property_node, SH.path, new_property))
            shape_properties.add(new_property)
            logger.info(f"Added new property path {new_property}")

    return shacl_graph, shape_properties


def get_subgraph_for_entailment(data_graph: Graph, regime: str) -> Graph:
    """Extract relevant triples for entailment based on the inference regime."""
    subgraph = Graph()

    for s, p, o in data_graph.triples((None,
                                       RDFS.subPropertyOf,
                                       None)):
        subgraph.add((s, p, o))

    if regime == InferenceLevel.RDFS.value:
        return subgraph

    elif regime in (InferenceLevel.OWL_LD.value, InferenceLevel.OWLRL.value):
        for s, p, o in data_graph.triples((None,
                                           OWL.sameAs,
                                           None)):
            subgraph.add((s, p, o))

    return subgraph


def extend_shacl_shape(shape: URIRef, property_blank_nodes: Set, shacl_graph: Graph, shape_properties: Set,
                       data_graph: Graph, regime: str, old_ignored_properties: Set) -> Graph:
    """Extend a SHACL shape with additional property shapes based on entailment."""
    for property_shape in property_blank_nodes:
        shacl_graph, shape_properties = entail_shape_graph(data_graph, regime, shacl_graph, shape_properties,
                                                           property_shape, shape, old_ignored_properties)

    # Only in case of owlrl extra work is needed
    if regime == InferenceLevel.OWLRL.value:
        shacl_graph, shape_properties = entail_property_chain_axiom(data_graph, shacl_graph, shape,
                                                                    shape_properties)
        shacl_graph, shape_properties = entail_has_value_on_property(data_graph, shape, shacl_graph,
                                                                     shape_properties)

    return shacl_graph


def get_current_ignored_properties(shacl_graph: Graph, shape_uri: URIRef) -> Set:
    """Get the current set of ignored properties for a closed SHACL shape."""
    current_ignored_properties = set()

    # Get the first ignored property blank node
    ignored_property_node = shacl_graph.value(subject=URIRef(shape_uri),
                                              predicate=SH.ignoredProperties)

    # While there is another member of the list do
    index = 0

    while ignored_property_node != RDF.nil and ignored_property_node is not None:

        # Get the value of the list member
        ignored_property = shacl_graph.value(subject=ignored_property_node,
                                             predicate=RDF.first)

        current_ignored_properties.add(ignored_property)
        # Get the next list member if exists
        ignored_property_node = shacl_graph.value(subject=ignored_property_node,
                                                  predicate=RDF.rest)

        index += 1

        if ignored_property_node is None:
            break

    return current_ignored_properties


def add_ignored_properties_to_graph(shacl_graph: Graph, shape_uri: URIRef, ignored_properties: Set) -> Graph:
    """Add ignored properties to a SHACL shape as an RDF list."""
    list_subgraph = Graph()
    index = 0
    num_ignored_properties = len(ignored_properties)
    first_element = None

    for ignored_property in ignored_properties:
        first_element = add_element_to_rdf_list(list_subgraph, first_element, ignored_property)

        index += 1
        # For the last blank node, link it to the ignored properties
        if index == num_ignored_properties:

            # Recursively remove the old ignored properties
            old_ignored_properties = shacl_graph.value(URIRef(shape_uri),
                                                       SH.ignoredProperties)

            if old_ignored_properties is not None and old_ignored_properties != RDF.nil:
                while not old_ignored_properties == RDF.nil:
                    next_ignored_properties = shacl_graph.value(subject=old_ignored_properties,
                                                                predicate=RDF.rest)
                    shacl_graph.remove((old_ignored_properties, None, None))
                    old_ignored_properties = next_ignored_properties

            # Set the new ignored properties
            shacl_graph.set((URIRef(shape_uri),
                             SH.ignoredProperties,
                             first_element))

    # Add all other list values to the original graph
    for s, p, o in list_subgraph.triples((None, None, None)):
        shacl_graph.add((s, p, o))

    return shacl_graph


def get_elements_in_rdf_list(graph: Graph, rdf_list) -> List:
    """Extract all elements from an RDF list."""
    current_element = rdf_list
    elements = []
    if current_element is not None:
        while current_element != RDF.nil:
            current_value = graph.value(subject=current_element, predicate=RDF.first)
            elements.append(current_value)
            current_element = graph.value(subject=current_element, predicate=RDF.rest)

            if current_element is None:
                break

    return elements


def add_element_to_rdf_list(graph: Graph, rdf_list, bn):
    """Add an element to an RDF list."""
    # Traverse to last element
    current_element = rdf_list

    # Create new list blank node
    new_element = BNode()

    # Add value to list element
    graph.add((new_element,
               RDF.first,
               bn))

    # Make new list element end of list
    graph.add((new_element,
               RDF.rest,
               RDF.nil))

    if current_element is not None:
        while graph.value(subject=current_element, predicate=RDF.rest) != RDF.nil:
            current_element = graph.value(subject=current_element, predicate=RDF.rest)

        # Add new element to end of list
        graph.set((current_element,
                   RDF.rest,
                   new_element))
    else:
        return new_element

    return rdf_list


def check_incongruences(shape: URIRef, data_graph: Graph, shacl_graph: Graph, shape_properties: Set) -> List[str]:
    """Check for potential incongruences in closed shape definitions."""
    warning_messages = []
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    # subclass inconsistency
    for target_class in target_classes:
        for class_name, _, _ in data_graph.triples((None, RDFS.subClassOf, target_class)):
            warning_messages.append(f"{target_class} is a super-class of {class_name}, using this as the target class "
                                    f"for a SHACL closed shape {shape} could lead to incongruences.")

        for property_name, _, _ in data_graph.triples((None, RDFS.domain, target_class)):
            if property_name not in shape_properties:
                warning_messages.append(f"Property {property_name} was not found in the property constraints for "
                                        f"shape {shape} with {target_class}. Since {target_class} is the domain of "
                                        f"{property_name}, this could lead to incongruences.")

    return warning_messages


def pre_process_shacl_graph_full(data_graph: Graph, shacl_graph: Graph, regime: str) -> Tuple[Graph, Graph]:
    """Preprocess SHACL shapes graph with entailment-based extension for closed shapes."""
    if regime == InferenceLevel.NONE.value:
        return data_graph, shacl_graph

    warning_messages = []

    ignored_properties = set()
    if regime == InferenceLevel.RDFS.value:
        ignored_properties.add(RDF.type)
    if regime == InferenceLevel.OWL_LD.value:
        ignored_properties.add(OWL.sameAs)

    engine = EntailEngine(data_graph, regime)
    # The engine entails the data graph given a regime
    entailed_data_graph = engine.entail()
    if entailed_data_graph:
        data_graph = entailed_data_graph
    else:
        return data_graph, shacl_graph

    shape_names = list_all_shape_names(shacl_graph)
    shape_with_properties = map_shapes_to_properties(shacl_graph, shape_names)
    shape_property_paths = get_shape_property_paths(shacl_graph, shape_names, shape_with_properties)
    for shape_uri in shape_names:
        if not shacl_graph.value(URIRef(shape_uri), SH.closed):
            continue

        old_ignored_properties = get_current_ignored_properties(shacl_graph, shape_uri)

        warning_messages += check_incongruences(shape_uri, data_graph, shacl_graph, shape_property_paths[shape_uri])
        shacl_graph = extend_shacl_shape(shape_uri, shape_with_properties[shape_uri], shacl_graph,
                                         shape_property_paths[shape_uri], data_graph, regime, old_ignored_properties)

        ignored_properties = set(ignored_properties).union(set(old_ignored_properties))
        ignored_properties = set([x for x in ignored_properties if x not in shape_property_paths[shape_uri]])
        shacl_graph = add_ignored_properties_to_graph(shacl_graph, shape_uri, ignored_properties)
        ignored_properties = set()

    if warning_messages:
        logger.warning(f"{regime} entailment found the following incongruences in the data graph (WARNING):")
        for warning in warning_messages:
            logger.warning(warning)

    return data_graph, shacl_graph
