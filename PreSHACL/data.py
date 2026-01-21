# 3 Shapes Graphs

SG_1 = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

schema:PersonShape
    a sh:NodeShape ;
    sh:targetClass schema:Person ;
    sh:property [
        sh:path schema:name ;
        sh:datatype xsd:string ;
        sh:name "given name" ;
    ] ;
    sh:property [
        sh:path schema:birthDate ;
        sh:lessThan schema:deathDate ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:gender ;
        sh:in ( "female" "male" ) ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path schema:address ;
        sh:node schema:AddressShape ;
    ] .   

schema:AddressShape
    a sh:NodeShape ;
    sh:property [
        sh:path schema:streetAddress ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path schema:postalCode ;
        sh:or ( [ sh:datatype xsd:string ] [ sh:datatype xsd:integer ] ) ;
        sh:minInclusive 10000 ;
        sh:maxInclusive 99999 ;
    ] .
'''

SG_2 = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

schema:PersonShape
    a sh:NodeShape ;
    sh:targetClass schema:Person ;
    sh:closed true ;
	sh:ignoredProperties (rdf:type) ;
    sh:property [
        sh:path schema:name ;
        sh:datatype xsd:string ;
        sh:name "given name" ;
    ] ;
    sh:property [
        sh:path schema:birthDate ;
        sh:lessThan schema:deathDate ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:gender ;
        sh:in ( "female" "male" ) ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path schema:address ;
        sh:node schema:AddressShape ;
    ] .   

schema:AddressShape
    a sh:NodeShape ;
    sh:property [
        sh:path schema:streetAddress ;
        sh:datatype xsd:string ;
    ] ;
    sh:property [
        sh:path schema:postalCode ;
        sh:or ( [ sh:datatype xsd:string ] [ sh:datatype xsd:integer ] ) ;
        sh:minInclusive 10000 ;
        sh:maxInclusive 99999 ;
    ] .
'''


SG_3 = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

schema:ClosedShapeExampleShape
	a sh:NodeShape ;
	sh:targetNode schema:Alice, schema:Bob ;
	sh:closed true ;
	sh:ignoredProperties (rdf:type) ;
	sh:property [
		sh:path schema:firstName ;
        sh:minCount 1 ;
	] .
'''

# 4 Data Graphs

DG_1 = '''
@prefix : <http://example.org/ns#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:alice schema:nn "Alice";
       schema:gender "female".

:Alice schema:name "Alice".
       
schema:name owl:sameAs schema:Name.

schema:nn owl:sameAs schema:name;
          a owl:InverseFunctionalProperty.

:ali schema:address [ schema:streetAddress "1600 Amphitheatre Pkway"; schema:zipCode 94004] ;
     owl:sameAs :alice.   
     
schema:postalCode owl:equivalentProperty schema:zipCode.   
     
:simon schema:knows :alice.

schema:TL rdfs:subClassOf schema:Person.

schema:Student rdfs:subClassOf schema:TL.

schema:knows rdfs:domain schema:Student;
             rdfs:range schema:Student.

:math a schema:Course;
      schema:name "Math".
      
:SC a schema:Department;
    schema:name "Computer Science".
    
:Math owl:sameAs :math.

'''


DG_2 = '''
@prefix : <http://example.org/ns#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:alice schema:nn "Alice";
       schema:gender "female".

:Alice a schema:Person;
       schema:name "Alice".
       
schema:name owl:sameAs schema:Name.

schema:nn owl:sameAs schema:name;
          a owl:InverseFunctionalProperty.

:ali schema:address [ schema:streetAddress "1600 Amphitheatre Pkway"; schema:zipCode 94004] ;
     owl:sameAs :alice.   
     
schema:postalCode owl:equivalentProperty schema:zipCode.   
     
:simon schema:knows :alice;
       schema:gender "male".

schema:TL rdfs:subClassOf schema:Person.

schema:Student rdfs:subClassOf schema:TL.

schema:knows rdfs:domain schema:Student;
             rdfs:range schema:Student.

:math a schema:Course;
      schema:name "Math".
      
:SC a schema:Department;
    schema:name "Computer Science".
    
:Math owl:sameAs :math.

'''


DG_3 = '''
@prefix : <http://example.org/ns#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:alice schema:nn "Alice";
       schema:gender "female".

:Alice schema:name "Alice".
       
schema:name owl:sameAs schema:Name.

schema:nn owl:sameAs schema:name;
          a owl:InverseFunctionalProperty.

:ali schema:address [ schema:streetAddress "1600 Amphitheatre Pkway"; schema:zipCode 94004] ;
     owl:sameAs :alice.   
     
schema:postalCode owl:equivalentProperty schema:zipCode.   
     
:simon schema:knows :alice.

:semon owl:sameAs :simon.

schema:TL rdfs:subClassOf schema:Person.

schema:Student rdfs:subClassOf schema:TL.

schema:knows rdfs:domain schema:Student;
             rdfs:range schema:Student.

:math a schema:Course;
      schema:name "Math".
      
:SC a schema:Department;
    schema:name "Computer Science".
    
:Math owl:sameAs :math.

'''



DG_4 = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#>. 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

schema:Alice
	schema:firstName "Alice" .
 
schema:ali owl:sameAs schema:Alice.

schema:Bob
	schema:Name "Bob" .
 
schema:Name owl:sameAs schema:firstName.
'''

