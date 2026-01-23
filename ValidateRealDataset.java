import org.apache.jena.graph.Graph;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.shacl.ShaclValidator;
import org.apache.jena.shacl.Shapes;
import org.apache.jena.shacl.ValidationReport;
import org.apache.jena.shacl.lib.ShLib;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * SHACL Validation Runner for Real Dataset (EnDe-Lite50)
 * 
 * This script validates the entailed EnDe-Lite50 data graph against
 * 4 entailed shapes graphs and measures validation time for each.
 * 
 * Data graph: source/Datasets/EnDe-Lite50_RDFS_entailed.ttl
 * Shapes graphs: source/ShapesGraphs/entailed/Shape_30_closed_*_entailed.ttl
 * 
 * Output: Validation reports and timing results
 */
public class ValidateRealDataset {
    
    // Paths
    private static final String DATA_GRAPH_PATH = "C:\\Users\\zenon\\eclipse-workspace\\closed-shaper\\source\\Datasets\\EnDe-Lite50_RDFS_entailed.ttl";
    private static final String SHAPES_DIR = "C:\\Users\\zenon\\eclipse-workspace\\closed-shaper\\source\\ShapesGraphs\\entailed";
    private static final String OUTPUT_DIR = "C:\\Users\\zenon\\eclipse-workspace\\closed-shaper\\Outputs\\real_dataset_validation";
    
    // Shapes files to validate against
    private static final String[] SHAPE_FILES = {
        "Shape_30_closed_3_entailed.ttl",
        "Shape_30_closed_6_entailed.ttl",
        "Shape_30_closed_15_entailed.ttl",
        "Shape_30_closed_30_entailed.ttl"
    };
    
    public static void main(String[] args) {
        System.out.println("=".repeat(80));
        System.out.println("SHACL Validation for Real Dataset (EnDe-Lite50)");
        System.out.println("=".repeat(80));
        System.out.println();
        
        try {
            // Create output directory
            Files.createDirectories(Paths.get(OUTPUT_DIR));
            
            // Load data graph once
            System.out.println("1. Loading entailed data graph...");
            System.out.println("   Path: " + DATA_GRAPH_PATH);
            long start = System.nanoTime();
            Model dataModel = RDFDataMgr.loadModel(DATA_GRAPH_PATH);
            Graph dataGraph = dataModel.getGraph();
            long elapsed = System.nanoTime() - start;
            System.out.printf("   Loaded %d triples in %.2fs%n", dataGraph.size(), elapsed / 1e9);
            
            // Results storage
            List<ValidationResult> results = new ArrayList<>();
            
            System.out.println();
            System.out.println("=".repeat(80));
            System.out.println("2. Running SHACL Validation");
            System.out.println("=".repeat(80));
            
            // Validate against each shapes graph
            for (int i = 0; i < SHAPE_FILES.length; i++) {
                String shapeFile = SHAPE_FILES[i];
                System.out.printf("%n[%d/%d] Validating with: %s%n", i + 1, SHAPE_FILES.length, shapeFile);
                System.out.println("-".repeat(80));
                
                String shapePath = SHAPES_DIR + "\\" + shapeFile;
                
                // Load shapes graph
                System.out.println("  Loading shapes graph...");
                start = System.nanoTime();
                Model shapesModel = RDFDataMgr.loadModel(shapePath);
                Graph shapesGraph = shapesModel.getGraph();
                Shapes shapes = Shapes.parse(shapesGraph);
                long loadTime = System.nanoTime() - start;
                System.out.printf("    Loaded %d triples in %.4fs%n", shapesGraph.size(), loadTime / 1e9);
                
                // Run validation
                System.out.println("  Running SHACL validation...");
                start = System.nanoTime();
                ValidationReport report = ShaclValidator.get().validate(shapes, dataGraph);
                long validationTime = System.nanoTime() - start;
                
                boolean conforms = report.conforms();
                int violationCount = report.getEntries().size();
                
                System.out.printf("    Validation completed in %.4fs%n", validationTime / 1e9);
                System.out.printf("    Conforms: %s%n", conforms);
                System.out.printf("    Violations: %d%n", violationCount);
                
                // Save validation report
                String reportFile = shapeFile.replace("_entailed.ttl", "_validation_report.ttl");
                String reportPath = OUTPUT_DIR + "\\" + reportFile;
                System.out.println("  Saving validation report...");
                start = System.nanoTime();
                Model reportModel = report.getModel();
                reportModel.write(new FileWriter(reportPath), "TURTLE");
                long saveTime = System.nanoTime() - start;
                System.out.printf("    Saved to: %s (%.4fs)%n", reportFile, saveTime / 1e9);
                
                // Store results
                results.add(new ValidationResult(
                    shapeFile,
                    shapesGraph.size(),
                    conforms,
                    violationCount,
                    loadTime / 1e9,
                    validationTime / 1e9,
                    saveTime / 1e9
                ));
                
                System.out.println("  Complete!");
            }
            
            // Print summary
            System.out.println();
            System.out.println("=".repeat(80));
            System.out.println("Summary");
            System.out.println("=".repeat(80));
            System.out.println();
            System.out.printf("%-40s | %-10s | %-12s | %-18s%n", 
                "Shape File", "Conforms", "Violations", "Validation Time");
            System.out.println("-".repeat(100));
            
            double totalValidationTime = 0;
            for (ValidationResult result : results) {
                System.out.printf("%-40s | %-10s | %-12d | %.4fs%n",
                    result.shapeFile,
                    result.conforms ? "YES" : "NO",
                    result.violations,
                    result.validationTime);
                totalValidationTime += result.validationTime;
            }
            
            System.out.println("-".repeat(100));
            System.out.printf("%-40s   %-12s   %.4fs (%.2f minutes)%n",
                "Total Validation Time:", "", totalValidationTime, totalValidationTime / 60);
            
            // Save results to CSV
            String csvPath = OUTPUT_DIR + "\\validation_results.csv";
            saveResultsToCSV(results, csvPath);
            System.out.println();
            System.out.printf("Results saved to: %s%n", csvPath);
            
            System.out.println();
            System.out.println("=".repeat(80));
            System.out.println("Validation completed successfully!");
            System.out.println("=".repeat(80));
            System.out.println();
            System.out.println("Output directory: " + OUTPUT_DIR);
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    private static void saveResultsToCSV(List<ValidationResult> results, String path) throws IOException {
        try (FileWriter writer = new FileWriter(path)) {
            writer.write("Shape File,Shapes Triples,Conforms,Violations,Load Time (s),Validation Time (s),Save Time (s),Total Time (s)\n");
            for (ValidationResult result : results) {
                writer.write(String.format("%s,%d,%s,%d,%.4f,%.4f,%.4f,%.4f\n",
                    result.shapeFile,
                    result.shapesTriples,
                    result.conforms,
                    result.violations,
                    result.loadTime,
                    result.validationTime,
                    result.saveTime,
                    result.loadTime + result.validationTime + result.saveTime));
            }
        }
    }
    
    static class ValidationResult {
        String shapeFile;
        int shapesTriples;
        boolean conforms;
        int violations;
        double loadTime;
        double validationTime;
        double saveTime;
        
        ValidationResult(String shapeFile, int shapesTriples, boolean conforms, int violations,
                        double loadTime, double validationTime, double saveTime) {
            this.shapeFile = shapeFile;
            this.shapesTriples = shapesTriples;
            this.conforms = conforms;
            this.violations = violations;
            this.loadTime = loadTime;
            this.validationTime = validationTime;
            this.saveTime = saveTime;
        }
    }
}
