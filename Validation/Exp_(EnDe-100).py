from importlib import reload
from rdflib import Graph
from pyshacl import validate
import time

import sys

sys.path.insert(0, sys.path[0]+"/../")

from prettytable import PrettyTable
import numpy as np
from ReSHACL.re_shacl import inter_graph, merged_graph


if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    

g = Graph()
# Loading the data graph
g.parse( "source/Datasets/EnDe-100(without_Ontology).ttl")

# Importing Ontology into the data graph
g.parse("source/dbpedia_ontology.owl", format="xml")


sg = Graph()
# Loading the shapes graph
sg.parse("source/ShapesGraphs/DBpedia_SHACL(non-referenced).ttl")


# Preheating with 10 rounds
i = 0
for i in range(5):
    conform, v_g, v_t = validate(g, shacl_graph=sg, inference='none')  


print("***** START VALIDATION ON [EnDe-100] *****")


table = PrettyTable(['Method','Average validation time (s)','Standard deviation','Conform','#Violation'])

result_query = """
SELECT ?v
WHERE {
    ?s sh:result ?v
}"""

########### [pySHACL] ##########

inter_time1 = []
for n1 in range (0,3):
    t1=time.time()
    conform1, v_g1, v_t1 = validate(g, shacl_graph=sg, inference='none')  
    t2=time.time()
    
    inter_time1.append(t2-t1)  
        
mean_time1 = np.mean(inter_time1)
std1= np.std(inter_time1)

result1=v_g1.query(result_query)

print('[pySHACL]=============================')

print(' Average validation time: ', mean_time1, 's')
print(' Standard deviation: ', std1, 's')
print(' #Violation: ', len(result1))

# Saving the validation report graph
v_g1.serialize(destination="Outputs/EnDe-100/violationGraph/pyshacl_results.ttl")

# Saving the validation report in txt

file = open("Outputs/EnDe-100/validationReports/pyshacl_results.txt", "w")
file.write(v_t1)
file.close()

table.add_row(['pySHACL', mean_time1, std1, conform1, len(result1)])

########### [Re-SHACL] ##########

inter_time2 = []
for n2 in range (0,3):
    t3=time.time()
    fused_graph1, same_dic1, shapes = merged_graph(g, shacl_graph=sg,data_graph_format='turtle',shacl_graph_format='turtle')
    conform2, v_g2, v_t2 = validate(fused_graph1, shacl_graph=shapes, inference='none')   
    t4=time.time()
    
    inter_time2.append(t4-t3)  
        
mean_time2 = np.mean(inter_time2)
std2= np.std(inter_time2)

result2=v_g2.query(result_query)

print('[Re-SHACL]=============================')

print(' Average validation time: ', mean_time2, 's')
print(' Standard deviation: ', std2, 's')
print(' #Violation: ', len(result2))
    
v_g2.serialize(destination="Outputs/EnDe-100/violationGraph/re-shacl_results.ttl")

# Saving the validation report in txt

file = open("Outputs/EnDe-100/validationReports/re-shacl_results.txt", "w")
file.write(v_t2)
file.close()

table.add_row(['Re-SHACL', mean_time2, std2, conform2, len(result2)])


########### [pySHACL-OWL] ##########

inter_time3 = []
#for n3 in range (0,3):
t5=time.time()
conform3, v_g3, v_t3 = validate(g, shacl_graph=sg, inference='both')  
t6=time.time()

inter_time3.append(t6-t5)  
        
mean_time3 = np.mean(inter_time3)
std3= np.std(inter_time3)

result3=v_g3.query(result_query)

print('[pySHACL-OWL]=============================')

print(' Average validation time: ', mean_time3, 's')
print(' Standard deviation: ', std3, 's')
print(' #Violation: ', len(result3))

v_g3.serialize(destination="Outputs/EnDe-100/violationGraph/pyshacl-owl_results.ttl")

# Saving the validation report in txt

file = open("Outputs/EnDe-100/validationReports/pyshacl-owl_results.txt", "w")
file.write(v_t3)
file.close()

table.add_row(['Re-SHACL', mean_time3, std3, conform3, len(result3)])


file_table = open("Outputs/EnDe-100/RunTimeResults.txt", "a+")
file_table .write(str(table))
file_table .close()

print(table)