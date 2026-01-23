package com.example.shacl.entailment;

import org.apache.jena.rdf.model.InfModel;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.reasoner.rulesys.GenericRuleReasoner;
import org.apache.jena.reasoner.rulesys.Rule;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class OWL2RLEntailer {
    
    private final Reasoner reasoner;
    private final List<Rule> rules;
    
    public OWL2RLEntailer(String rulesFilePath) throws IOException {
        this.rules = loadRulesFromFile(rulesFilePath);
        this.reasoner = new GenericRuleReasoner(rules);
        ((GenericRuleReasoner) reasoner).setMode(GenericRuleReasoner.FORWARD_RETE);
    }
    
    public OWL2RLEntailer(List<String> ruleStrings) {
        this.rules = parseRules(ruleStrings);
        this.reasoner = new GenericRuleReasoner(rules);
        ((GenericRuleReasoner) reasoner).setMode(GenericRuleReasoner.FORWARD_RETE);
    }
    
    public Model entail(Model model) {
        long start = System.nanoTime();
        System.out.println("  Applying OWL2RL entailment...");
        System.out.printf("    Loaded %d rules%n", rules.size());
        
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
    
    public Model entailWithOntology(Model dataModel, Model ontologyModel) {
        long start = System.nanoTime();
        System.out.println("  Applying OWL2RL entailment with ontology...");
        System.out.printf("    Loaded %d rules%n", rules.size());
        
        Model combinedModel = ModelFactory.createDefaultModel();
        combinedModel.add(dataModel);
        if (ontologyModel != null) {
            combinedModel.add(ontologyModel);
        }
        
        InfModel infModel = ModelFactory.createInfModel(reasoner, combinedModel);
        infModel.prepare();
        
        Model entailedModel = ModelFactory.createDefaultModel();
        entailedModel.add(infModel);
        
        long elapsed = System.nanoTime() - start;
        int originalSize = dataModel.size();
        int ontologySize = ontologyModel != null ? ontologyModel.size() : 0;
        int entailedSize = entailedModel.size();
        int newTriples = entailedSize - originalSize - ontologySize;
        
        System.out.printf("    Data triples: %d%n", originalSize);
        System.out.printf("    Ontology triples: %d%n", ontologySize);
        System.out.printf("    Entailed triples: %d%n", entailedSize);
        System.out.printf("    New triples: %d%n", newTriples);
        System.out.printf("    Entailment time: %.4fs%n", elapsed / 1e9);
        
        return entailedModel;
    }
    
    private List<Rule> loadRulesFromFile(String filePath) throws IOException {
        List<String> ruleStrings = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty() && !line.startsWith("#") && !line.startsWith("//")) {
                    ruleStrings.add(line);
                }
            }
        }
        return parseRules(ruleStrings);
    }
    
    private List<Rule> parseRules(List<String> ruleStrings) {
        List<Rule> parsedRules = new ArrayList<>();
        for (String ruleString : ruleStrings) {
            try {
                Rule rule = Rule.parseRule(ruleString);
                parsedRules.add(rule);
            } catch (Exception e) {
                System.err.println("Warning: Failed to parse rule: " + ruleString);
                System.err.println("  Error: " + e.getMessage());
            }
        }
        return parsedRules;
    }
    
    public int getRuleCount() {
        return rules.size();
    }
    
    public List<Rule> getRules() {
        return new ArrayList<>(rules);
    }
}
