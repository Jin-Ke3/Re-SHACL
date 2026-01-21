from rdflib import RDF, RDFS


def entail(data_graph):
    changes = True
    inferred_triples = set()
    num_inferred_triples = 0
    while changes:

        # Transitive properties
        for sub_property_name, _, super_property_name in data_graph.triples((None, RDFS.subPropertyOf, None)):
            for _, _, super_property in data_graph.triples((super_property_name, RDFS.subPropertyOf, None)):
                inferred_triples.add((sub_property_name, RDFS.subPropertyOf, super_property))

        for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
            # Transitive classes
            for _, _, super_class in data_graph.triples((superclass_name, RDFS.subClassOf, None)):
                inferred_triples.add((subclass_name, RDFS.subClassOf, super_class))
            # Class inheritance
            for entity_name, _, _ in data_graph.triples((None, RDF.type, subclass_name)):
                inferred_triples.add((entity_name, RDF.type, superclass_name))

        # Class inheritance
        # for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
        #     for entity_name, _, _ in data_graph.triples((None, RDF.type, subclass_name)):
        #         inferred_triples.add((entity_name, RDF.type, superclass_name))

        # RDFS domain
        for property_name, _, class_name in data_graph.triples((None, RDFS.domain, None)):
            for entity_name, _, _ in data_graph.triples((None, property_name, None)):
                inferred_triples.add((entity_name, RDF.type, class_name))

        # RDFS range
        for property_name, _, class_name in data_graph.triples((None, RDFS.range, None)):
            for _, _, entity_name in data_graph.triples((None, property_name, None)):
                inferred_triples.add((entity_name, RDF.type, class_name))

        # Track if there are any changes
        changes = len(inferred_triples) != num_inferred_triples
        num_inferred_triples = len(inferred_triples)

        for s, p, o in inferred_triples:
            data_graph.add((s, p, o))
