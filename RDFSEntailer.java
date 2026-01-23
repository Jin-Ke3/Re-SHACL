package com.example.shacl.entailment;

import org.apache.jena.rdf.model.InfModel;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.reasoner.ReasonerRegistry;

public class RDFSEntailer {
    
    private final Reasoner reasoner;
    
    public RDFSEntailer() {
        this.reasoner = ReasonerRegistry.getRDFSReasoner();
    }
    
    public Model entail(Model model) {
        long start = System.nanoTime();
        System.out.println("  Applying RDFS entailment...");
        
        InfModel infModel = ModelFactory.createInfModel(reasoner, model);
        infModel.prepare();
        
        Model entailedModel = ModelFactory.createDefaultModel();
        entailedModel.add(infModel);
        
        long elapsed = System.nanoTime() - start;
        int originalSize = model.size();
        int entailedSize = entailedModel.size();
        int newTriples = entailedSize - originalSize;
        
        System.out.printf("    Original triples: %d%n", originalSize);
        System.out.printf("    Entailed triples: %d%n", entailedSize);
        System.out.printf("    New triples: %d%n", newTriples);
        System.out.printf("    Entailment time: %.4fs%n", elapsed / 1e9);
        
        return entailedModel;
    }
    
    public Model entailWithSchema(Model dataModel, Model schemaModel) {
        long start = System.nanoTime();
        System.out.println("  Applying RDFS entailment with schema...");
        
        Reasoner boundReasoner = reasoner.bindSchema(schemaModel);
        InfModel infModel = ModelFactory.createInfModel(boundReasoner, dataModel);
        infModel.prepare();
        
        Model entailedModel = ModelFactory.createDefaultModel();
        entailedModel.add(infModel);
        
        long elapsed = System.nanoTime() - start;
        int originalSize = dataModel.size();
        int schemaSize = schemaModel != null ? schemaModel.size() : 0;
        int entailedSize = entailedModel.size();
        int newTriples = entailedSize - originalSize;
        
        System.out.printf("    Data triples: %d%n", originalSize);
        System.out.printf("    Schema triples: %d%n", schemaSize);
        System.out.printf("    Entailed triples: %d%n", entailedSize);
        System.out.printf("    New triples: %d%n", newTriples);
        System.out.printf("    Entailment time: %.4fs%n", elapsed / 1e9);
        
        return entailedModel;
    }
}
