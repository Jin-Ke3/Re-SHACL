from importlib import reload
from rdflib import Graph, Namespace
UB = Namespace("http://swat.cse.lehigh.edu/onto/univ-bench.owl#")
from pyshacl import validate
import time
import pickle
import sys

sys.path.insert(0, sys.path[0]+"/../")

from prettytable import PrettyTable
import numpy as np
from ReSHACL.re_shacl import inter_graph, merged_graph


if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf-8")


# g = Graph()
# print( "Loading the data graph" )
# g.parse( "source/Datasets/lubm-mkg-2.ttl")
# print(len(g))

# print( "Importing Ontology into the data graph")
# g.parse("http://swat.cse.lehigh.edu/onto/univ-bench.owl", format="xml")
# print(len(g))

# sg1 = Graph()
# print( "Loading the shapes graph")
# sg1.parse("source/ShapesGraphs/lubm/schema1.ttl")
# print("schema1:",len(sg1))

# sg2 = Graph()
# print( "Loading the shapes graph")
# sg2.parse("source/ShapesGraphs/lubm/schema2.ttl")
# print("schema2:",len(sg2))

# sg3 = Graph()
# print( "Loading the shapes graph")
# sg3.parse("source/ShapesGraphs/lubm/schema3.ttl")
# print("schema3:",len(sg3))

with open("source/Datasets/lubm-mkg-1.pkl", 'rb') as file:
    g = pickle.load(file)
with open("source/ShapesGraphs/lubm/schema1.pkl", 'rb') as file:
    sg1 = pickle.load(file)
with open("source/ShapesGraphs/lubm/schema2.pkl", 'rb') as file:
    sg2 = pickle.load(file)
with open("source/ShapesGraphs/lubm/schema3.pkl", 'rb') as file:
    sg3 = pickle.load(file)

 
def run_exp(g, sg, index):
    # Preheating with 10 rounds
    
    index=str(index)
   
    for i in range(5):
        conform, v_g, v_t = validate(g, shacl_graph=sg, inference='none')  

    title = "***** START VALIDATION ON [lubm-mkg-2][schema"+ index +"] *****"
    print(title)


    table = PrettyTable(['Method','Average validation time (s)','Standard deviation','Conform','#Violation'])

    result_query = """
    SELECT ?v
    WHERE {
        ?s <http://www.w3.org/ns/shacl#result> ?v
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
    v_g1.serialize(destination="Outputs/lubm/mkg2/validationGraph/pyshacl_results[schema"+ index +"].ttl")

    # Saving the validation report in txt

    file = open("Outputs/lubm/mkg2/validationReports/pyshacl_results[schema"+ index +"].txt", "w")
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
        
    v_g2.serialize(destination="Outputs/lubm/mkg2/validationGraph/re-shacl_results[schema"+ index +"].ttl")

    # Saving the validation report in txt

    file = open("Outputs/lubm/mkg2/validationReports/re-shacl_results[schema"+ index +"].txt", "w")
    file.write(v_t2)
    file.close()

    table.add_row(['Re-SHACL', mean_time2, std2, conform2, len(result2)])


    ########### [pySHACL-RDFS] ##########

    inter_time3 = []
    for n3 in range (0,3):
        t5=time.time()
        conform3, v_g3, v_t3 = validate(g, shacl_graph=sg, inference='rdfs')  
        t6=time.time()

        inter_time3.append(t6-t5)  
            
    mean_time3 = np.mean(inter_time3)
    std3= np.std(inter_time3)

    result3=v_g3.query(result_query)

    print('[pySHACL-RDFS]=============================')

    print(' Average validation time: ', mean_time3, 's')
    print(' Standard deviation: ', std3, 's')
    print(' #Violation: ', len(result3))

    v_g3.serialize(destination="Outputs/lubm/mkg2/validationGraph/pyshacl-rdfs_results[schema"+ index +"].ttl")

    # Saving the validation report in txt

    file = open("Outputs/lubm/mkg2/validationReports/pyshacl-rdfs_results[schema"+ index +"].txt", "w")
    file.write(v_t3)
    file.close()

    table.add_row(['pySHACL-RDFS', mean_time3, std3, conform3, len(result3)])


    file_table = open("Outputs/lubm/mkg2/RunTimeResults.txt", "a+")
    file_table .write(title+ '\n')
    file_table .write(str(table))
    file_table .close()
    
    print(table)
    
    if index != 3:
        print("========================Waiting for results from other schema================================")
    
    else:
        print("========================Finished================================")
        
    
shapes = [sg1, sg2, sg3]
index = 1
for sh in shapes:
    run_exp(g, sh, index)
    index = index + 1