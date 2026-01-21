import rdflib
from rdflib.namespace import OWL, RDF, RDFS, SH
from EntailEngine import *


# List all SHACL shapes
def get_shape_names(shacl_graph):
    shape_names = set()
    for s, p, o in shacl_graph.triples((None,
                                        RDF.type,
                                        SH.NodeShape)):
        shape_names.add(s)
    return shape_names


# List the property shapes for a SHACL shape
def get_shape_with_properties(shacl_graph, shape_names):
    shape_with_properties = {}
    for shape in shape_names:
        property_shapes = set(shacl_graph.objects(rdflib.URIRef(shape),
                                                  SH.property))
        shape_with_properties[shape] = property_shapes

    return shape_with_properties


# Look at the blank nodes of these property shapes
def get_shape_property_paths(shacl_graph, shape_names, shape_with_properties):
    shape_property_paths = {}
    for shape in shape_names:
        property_paths = set()
        for property_shape in shape_with_properties[shape]:
            property_path = shacl_graph.value(property_shape, SH.path)
            property_paths.add(property_path)
        shape_property_paths[shape] = property_paths

    return shape_property_paths


def entail_shape_graph(data_graph, regime, shacl_graph, shape_properties, property_shape, shape, old_ignored_properties):
    subgraph = get_subgraph_for_entailment(data_graph, regime)
    property_shape_path = shacl_graph.value(property_shape,
                                            SH.path)

    for dg_s, dg_p, dg_o in subgraph.triples((None,
                                              None,
                                              rdflib.URIRef(property_shape_path))):
        # Check if the new property is not already in the shape properties
        if dg_s not in shape_properties and dg_s not in old_ignored_properties:
            # Create a new property shape
            property_node = rdflib.BNode()
            shacl_graph.add((rdflib.URIRef(shape), SH.property, property_node))
            # Add the path
            shacl_graph.add((property_node, SH.path, dg_s))

            # # Copy all the other properties and change the path value
            # for s, p, o in shacl_graph.triples((property_shape, None, None)):
            #     if p == SH.path:
            #         shacl_graph.add((property_node, p, dg_s))
            #     else:
            #         shacl_graph.add((property_node, p, o))

            shape_properties.add(dg_s)
            print(f"Added new property path {dg_s}")

    return shacl_graph, shape_properties


def get_all_target_classes_for_shape(shape, shacl_graph):
    target_classes = set()

    for _, _, target_property in shacl_graph.triples((rdflib.URIRef(shape), SH.targetClass, None)):
        target_classes.add(target_property)

    for _, _, target_property in shacl_graph.triples((rdflib.URIRef(shape), SH.targetSubjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.domain, None)):
            target_classes.add(class_name)

    for _, _, target_property in shacl_graph.triples((rdflib.URIRef(shape), SH.targetObjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.range, None)):
            target_classes.add(class_name)

    return target_classes


def entail_has_value_on_property(data_graph, shape, shacl_graph, shape_properties):
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    if not target_classes:
        return shacl_graph, shape_properties

    for target_class in target_classes:
        for _, _, superclass_name in data_graph.triples((rdflib.URIRef(target_class),
                                                         RDFS.subClassOf,
                                                         None)):

            on_property_value = data_graph.value(subject=superclass_name, predicate=OWL.onProperty)
            if on_property_value in shape_properties:
                continue

            bn_has_value_exists = data_graph.value(subject=superclass_name, predicate=OWL.hasValue) is not None
            bn_on_property_exists = on_property_value is not None

            if bn_has_value_exists and bn_on_property_exists:
                property_node = rdflib.BNode()
                shacl_graph.add((rdflib.URIRef(shape), SH.property, property_node))
                shacl_graph.add((property_node, SH.path, on_property_value))
                shape_properties.add(on_property_value)
                print(f"Added new property path {on_property_value}")

    return shacl_graph, shape_properties


def entail_property_chain_axiom(data_graph, shacl_graph, shape, shape_properties):
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
            property_node = rdflib.BNode()
            shacl_graph.add((rdflib.URIRef(shape), SH.property, property_node))
            shacl_graph.add((property_node, SH.path, new_property))
            shape_properties.add(new_property)
            print(f"Added new property path {new_property}")

    return shacl_graph, shape_properties


def get_subgraph_for_entailment(data_graph, regime):
    subgraph = rdflib.Graph()

    for s, p, o in data_graph.triples((None,
                                       RDFS.subPropertyOf,
                                       None)):
        subgraph.add((s, p, o))

    if regime == 'rdfs':
        return subgraph

    elif regime == 'owl-ld' or regime == 'owlrl':
        for s, p, o in data_graph.triples((None,
                                           OWL.sameAs,
                                           None)):
            subgraph.add((s, p, o))

    return subgraph


def extend_shacl_shape(shape, property_blank_nodes, shacl_graph, shape_properties,
                       data_graph, regime, old_ignored_properties):
    for property_shape in property_blank_nodes:
        shacl_graph, shape_properties = entail_shape_graph(data_graph, regime, shacl_graph, shape_properties,
                                                           property_shape, shape, old_ignored_properties)

    # Only in case of owlrl extra work is needed
    if regime == 'owlrl':
        shacl_graph, shape_properties = entail_property_chain_axiom(data_graph, shacl_graph, shape,
                                                                    shape_properties)
        shacl_graph, shape_properties = entail_has_value_on_property(data_graph, shape, shacl_graph,
                                                                     shape_properties)

    return shacl_graph


def get_current_ignored_properties(shacl_graph, shape_uri):
    current_ignored_properties = set()

    # Get the first ignored property blank node
    ignored_property_node = shacl_graph.value(subject=rdflib.URIRef(shape_uri),
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


def add_ignored_properties_to_graph(shacl_graph, shape_uri, ignored_properties):
    list_subgraph = rdflib.Graph()
    index = 0
    num_ignored_properties = len(ignored_properties)
    first_element = None

    for ignored_property in ignored_properties:
        first_element = add_element_to_rdf_list(list_subgraph, first_element, ignored_property)

        index += 1
        # For the last blank node, link it to the ignored properties
        if index == num_ignored_properties:

            # Recursively remove the old ignored properties
            old_ignored_properties = shacl_graph.value(rdflib.URIRef(shape_uri),
                                                       SH.ignoredProperties)

            if old_ignored_properties is not None and old_ignored_properties != RDF.nil:
                while not old_ignored_properties == RDF.nil:
                    next_ignored_properties = shacl_graph.value(subject=old_ignored_properties,
                                                                predicate=RDF.rest)
                    shacl_graph.remove((old_ignored_properties, None, None))
                    old_ignored_properties = next_ignored_properties

            # Set the new ignored properties
            shacl_graph.set((rdflib.URIRef(shape_uri),
                             SH.ignoredProperties,
                             first_element))

    # Add all other list values to the original graph
    for s, p, o in list_subgraph.triples((None, None, None)):
        shacl_graph.add((s, p, o))

    return shacl_graph


def get_elements_in_rdf_list(graph, rdf_list):
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


def add_element_to_rdf_list(graph, rdf_list, bn):
    # Traverse to last element
    current_element = rdf_list

    # Create new list blank node
    new_element = rdflib.BNode()

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


def check_incongruences(shape, data_graph, shacl_graph, shape_properties):
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


def pre_process_shacl_graph_full(data_graph, shacl_graph, regime):
    if regime == 'none':
        return data_graph, shacl_graph

    warning_messages = []

    ignored_properties = set()
    if regime == 'rdfs':
        ignored_properties.add(RDF.type)
    if regime == 'owl-ld':
        ignored_properties.add(OWL.sameAs)

    engine = EntailEngine(data_graph, regime)
    # The engine entails the data graph given a regime
    entailed_data_graph = engine.entail()
    if entailed_data_graph:
        data_graph = entailed_data_graph
    else:
        return data_graph, shacl_graph

    shape_names = get_shape_names(shacl_graph)
    shape_with_properties = get_shape_with_properties(shacl_graph, shape_names)
    shape_property_paths = get_shape_property_paths(shacl_graph, shape_names, shape_with_properties)
    for shape_uri in shape_names:
        if not shacl_graph.value(rdflib.URIRef(shape_uri), SH.closed):
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
        print(f"{regime} entailment found the following incongruences in the data graph (WARNING):")
        for warning in warning_messages:
            print(warning)
    #     print("CONTINUING ...")

    return data_graph, shacl_graph
