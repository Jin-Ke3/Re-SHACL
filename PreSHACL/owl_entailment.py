from rdflib import RDF, RDFS, OWL


def entail(data_graph):
    changes = True
    inferred_triples = set()
    data_graph_size = len(data_graph)
    while changes:
        for s, _, o in data_graph.triples((None, OWL.sameAs, None)):
            # Symmetric sameAs
            if not o == s:
                inferred_triples.add((o, OWL.sameAs, s))

            # Transitive sameAs
            for _, _, super_o in data_graph.triples((o, OWL.sameAs, None)):
                inferred_triples.add((s, OWL.sameAs, super_o))
            # SameAs copy subject triples
            for _, pred, obj in data_graph.triples((s, None, None)):
                inferred_triples.add((o, pred, obj))
            # SameAs copy predicate triples
            for subj, _, obj in data_graph.triples((None, s, None)):
                inferred_triples.add((subj, o, obj))
            # SameAs copy object triples
            for subj, pred, _ in data_graph.triples((None, None, s)):
                inferred_triples.add((subj, pred, o))

        # Equivalence relation to sub property conversion
        for s, _, o in data_graph.triples((None, OWL.equivalentProperty, None)):
            inferred_triples.add((s, RDFS.subPropertyOf, o))
            inferred_triples.add((o, RDFS.subPropertyOf, s))

        for sub_property_name, _, super_property_name in data_graph.triples((None, RDFS.subPropertyOf, None)):
            for _, _, super_property in data_graph.triples((super_property_name, RDFS.subPropertyOf, None)):
                # Equivalent property relation
                if super_property == sub_property_name:
                    inferred_triples.add((sub_property_name, OWL.equivalentProperty, super_property_name))
                # Transitive property relation
                else:
                    inferred_triples.add((sub_property_name, RDFS.subPropertyOf, super_property))

        # RDFS domain
        for property_name, _, class_name in data_graph.triples((None, RDFS.domain, None)):
            # Type entailment for entity
            for entity_name, _, _ in data_graph.triples((None, property_name, None)):
                inferred_triples.add((entity_name, RDF.type, class_name))

            # Superclass entailment for domain expression
            for _, _, superclass_name in data_graph.triples((class_name, RDFS.subClassOf, None)):
                inferred_triples.add((property_name, RDFS.domain, superclass_name))

            # Super property entailment for domain expression
            for _, _, super_property_name in data_graph.triples((property_name, RDFS.subPropertyOf, None)):
                inferred_triples.add((super_property_name, RDFS.domain, class_name))

        # # RDFS range
        for property_name, _, class_name in data_graph.triples((None, RDFS.range, None)):
            # Type entailment for entity
            for _, _, entity_name in data_graph.triples((None, property_name, None)):
                inferred_triples.add((entity_name, RDF.type, class_name))

            # Superclass entailment for range expression
            for _, _, superclass_name in data_graph.triples((class_name, RDFS.subClassOf, None)):
                inferred_triples.add((property_name, RDFS.range, superclass_name))

            # Super property entailment for range expression
            for _, _, super_property_name in data_graph.triples((property_name, RDFS.subPropertyOf, None)):
                inferred_triples.add((super_property_name, RDFS.range, class_name))

        for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
            for _, _, super_class in data_graph.triples((superclass_name, RDFS.subClassOf, None)):
                # Transitive classes
                inferred_triples.add((subclass_name, RDFS.subClassOf, super_class))

                # Equivalent class relation
                if super_class == subclass_name:
                    inferred_triples.add((subclass_name, OWL.equivalentClass, superclass_name))

        # Class inheritance
        for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
            for entity_name, _, _ in data_graph.triples((None, RDF.type, subclass_name)):
                inferred_triples.add((entity_name, RDF.type, superclass_name))

        # Equivalence relation to subclass conversion
        for s, p, o in data_graph.triples((None, OWL.equivalentClass, None)):
            inferred_triples.add((s, RDFS.subClassOf, o))
            inferred_triples.add((o, RDFS.subClassOf, s))

        # Track if there are any changes
        changes = len(data_graph) != data_graph_size
        data_graph_size = len(data_graph)

        for s, p, o in inferred_triples:
            data_graph.add((s, p, o))

        inferred_triples = set()




# def check_inconsistencies(data_graph):
#     error_messages = []
#
#     # CLS-NOTHING2
#     for entity, _, _ in data_graph.triples((None, RDF.type, OWL.Nothing)):
#         error_messages.append(f"{entity} cannot be of type {OWL.Nothing}")
#
#     # CAX-DW
#     for class1, _, class2 in data_graph.triples((None, OWL.disjointWith, None)):
#         class1_entities = set(data_graph.subjects(predicate=RDF.type, object=class1))
#         class2_entities = set(data_graph.subjects(predicate=RDF.type, object=class2))
#         common_entities = class1_entities.intersection(class2_entities)
#         for entity in common_entities:
#             error_messages.append(f"{entity} cannot be in two disjoint classes {class1} and {class2}")
#
#     # PRP-PDW
#     for property1, _, property2 in data_graph.triples((None, OWL.propertyDisjointWith, None)):
#         property1_entities = set(data_graph.subject_objects(predicate=property1))
#         property2_entities = set(data_graph.subject_objects(predicate=property2))
#         common_entities = property1_entities.intersection(property2_entities)
#         for entity1, entity2 in common_entities:
#             error_messages.append(f"{property1} and {property2} are disjoint properties "
#                                   f"and cannot connect the same entities")
#
#     # PRP-IRP
#     for property1, _, _ in data_graph.triples((None, RDF.type, OWL.IrreflexiveProperty)):
#         for entity1, _, entity2 in data_graph.triples((None, property1, None)):
#             if entity1 == entity2:
#                 error_messages.append(f"{property1} is an irreflexive property. "
#                                       f"It cannot be used to connect {entity1} and {entity2}")
#
#     # PRP-ASYP
#     for property1, _, _ in data_graph.triples((None, RDF.type, OWL.AsymmetricProperty)):
#         property_entities = set(data_graph.subject_objects(property1))
#         inverse_property_entities = [(y, x) for x, y in property_entities if x != y]
#         common_entities = property_entities.intersection(inverse_property_entities)
#         for entity1, entity2 in common_entities:
#             error_messages.append(f"{property1} is an asymmetric property. "
#                                   f"It cannot be used to connect {entity1} and {entity2}")
#
#     # EQ-DIFF1
#     same_as_entities = set(data_graph.subject_objects(OWL.sameAs))
#     different_from_entities = set(data_graph.subject_objects(OWL.differentFrom))
#     different_from_reversed_entities = [(y, x) for x, y in different_from_entities]
#     common_entities = same_as_entities.intersection(different_from_entities) \
#         .union(same_as_entities.intersection(different_from_reversed_entities))
#     for entity1, entity2 in common_entities:
#         error_messages.append(f"{entity1} and {entity2} cannot be both sameAs and differentFrom")
#
#     return error_messages
