import rdflib
from rdflib.namespace import RDF, SH


def load_turtle_graph(path):
    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    return graph


def clean_shapes_graph(shapes_graph):
    additions = []
    deletions = []

    # Remove all sh:class
    shapes_graph.remove((None, rdflib.URIRef("http://www.w3.org/ns/shacl#class"), None))

    # Replace sh:or by first element of sh:or list
    for original_shape, p_or, first_element_rdf_list in shapes_graph.triples((None, SH['or'], None)):
        blank_node = shapes_graph.value(subject=first_element_rdf_list, predicate=RDF.first)

        for s, p, o in shapes_graph.triples((blank_node, None, None)):
            additions.append((original_shape, p, o))

        if first_element_rdf_list is not None and first_element_rdf_list != RDF.nil:
            while not first_element_rdf_list == RDF.nil and first_element_rdf_list is not None:
                current_list_value = shapes_graph.value(subject=first_element_rdf_list, predicate=RDF.first)
                next_element = shapes_graph.value(subject=first_element_rdf_list, predicate=RDF.rest)
                deletions.append((first_element_rdf_list, None, None))
                deletions.append((current_list_value, None, None))
                first_element_rdf_list = next_element

        deletions.append((original_shape, p_or, None))

    # Remove all sh:not
    for original_shape, p_not, blank_node in shapes_graph.triples((None, SH['not'], None)):
        deletions.append((original_shape, p_not, None))
        deletions.append((blank_node, None, None))

    for a in additions:
        shapes_graph.add(a)

    for d in deletions:
        shapes_graph.remove(d)

    return shapes_graph


def clean(shapes_path, output_path):
    shapes_graph = load_turtle_graph(shapes_path)
    cleaned_shapes_graph = clean_shapes_graph(shapes_graph)
    cleaned_shapes_graph.serialize(output_path, format="turtle")


if __name__ == '__main__':
    clean("./schema2.ttl",
          "./schema2_clean.ttl")
