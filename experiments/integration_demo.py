"""Integration Demo for Re-SHACL Validation

This script demonstrates the integration between Re-SHACL preprocessing and standard
SHACL validation. It shows how merged graphs from Re-SHACL are validated and how
the preprocessing affects the validation results.

The demo validates a sample Person shape against test data using both:
1. Standard SHACL validation
2. Re-SHACL merged graph validation
"""

from rdflib import Graph, Namespace, RDF, URIRef
from pyshacl import validate
import time
from ReSHACL.re_shacl import inter_graph, merged_graph
SG = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema1: <http://schema.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

schema1:PersonShape a sh:NodeShape ;
    sh:closed true ;
    sh:ignoredProperties ( rdfs:subClassOf rdfs:subPropertyOf owl:differentFrom rdf:type owl:sameAs owl:equivalentProperty ) ;
    sh:property [ sh:path schema1:nn ],
        [ sh:path schema1:Name ],
        [ sh:datatype xsd:string ;
            sh:name "given name" ;
            sh:path schema1:name ],
        [ sh:lessThan schema1:deathDate ;
            sh:maxCount 1 ;
            sh:path schema1:birthDate ],
        [ sh:in ( "female" "male" ) ;
            sh:minCount 1 ;
            sh:path schema1:gender ],
        [ sh:node schema1:AddressShape ;
            sh:path schema1:address ] ;
    sh:targetClass schema1:Person .

schema1:AddressShape a sh:NodeShape ;
    sh:property [ sh:datatype xsd:string ;
            sh:path schema1:streetAddress ],
        [ sh:maxInclusive 99999 ;
            sh:minInclusive 10000 ;
            sh:or ( [ sh:datatype xsd:string ] [ sh:datatype xsd:integer ] ) ;
            sh:path schema1:postalCode ] .
"""

G = """
@prefix : <http://example.org/ns#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema1: <http://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Alice schema1:Name "Alice" ;
    schema1:name "Alice" .

:SC a schema1:Department ;
    schema1:Name "Computer Science" ;
    schema1:name "Computer Science" .

schema1:knows rdfs:domain schema1:Student,
        schema1:TL ;
    rdfs:range schema1:Student .

:Math owl:sameAs :math .

:ali schema1:address _:n4bc229eaabc54222a8bd3dd5f37630d9b1 ;
    owl:sameAs :alice .

:semon owl:sameAs :simon .

schema1:nn a owl:InverseFunctionalProperty ;
    owl:sameAs schema1:Name,
        schema1:name .

schema1:postalCode rdfs:subPropertyOf schema1:zipCode ;
    owl:equivalentProperty schema1:zipCode .

:math a schema1:Course ;
    schema1:Name "Math" ;
    schema1:name "Math" ;
    owl:sameAs :Math,
        :math .

:simon a schema1:Student ;
    schema1:knows :alice ;
    owl:sameAs :semon,
        :simon .

schema1:TL rdfs:subClassOf schema1:Person .

schema1:zipCode rdfs:subPropertyOf schema1:postalCode .

:alice schema1:address _:n4bc229eaabc54222a8bd3dd5f37630d9b1 ;
    schema1:gender "female" ;
    schema1:name "Alice" ;
    schema1:nn "Alice" ;
    owl:sameAs :ali,
        :alice .

schema1:Name owl:sameAs schema1:Name,
        schema1:name .

schema1:Student rdfs:subClassOf schema1:Person,
        schema1:TL .

schema1:name a owl:InverseFunctionalProperty ;
    owl:sameAs schema1:Name,
        schema1:name,
        schema1:nn .

_:n4bc229eaabc54222a8bd3dd5f37630d9b1 schema1:streetAddress "1600 Amphitheatre Pkway" ;
    schema1:zipCode 94004 .
"""

conform1, v_g1, v_t1 = validate(G, shacl_graph=SG, inference='none')

print(v_t1)

fused_graph1, same_dic1, shapes = merged_graph(G, shacl_graph=SG,data_graph_format='turtle',shacl_graph_format='turtle')
conform2, v_g2, v_t2 = validate(fused_graph1, shacl_graph=shapes, inference='none')
print(v_t2)
print('finish')