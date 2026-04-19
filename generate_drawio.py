import xml.etree.ElementTree as ET

def create_drawio_xml():
    mxfile = ET.Element('mxfile', host='Electron', modified='2023-01-01T00:00:00.000Z', agent='Mozilla/5.0', version='21.1.2', type='device')
    diagram = ET.SubElement(mxfile, 'diagram', id='diagram1', name='Pipeline')
    mxGraphModel = ET.SubElement(diagram, 'mxGraphModel', dx='1000', dy='1000', grid='1', gridSize='10', guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1', pageWidth='1600', pageHeight='2000', math='0', shadow='0')
    root = ET.SubElement(mxGraphModel, 'root')
    
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    
    nodes = [
        ("nstart", "User Query: EGFR T790M"),
        ("n1", "1. MutationParserAgent"),
        ("n2", "2. PlannerAgent"),
        ("n3", "3. FetchAgent (PubMed)"),
        ("n4", "4. FetchAgent (UniProt)"),
        ("n5", "5. FetchAgent (PDB)"),
        ("n6", "6. FetchAgent (PubChem)"),
        ("n7", "7. StructurePrepAgent"),
        ("n8", "8. VariantEffectAgent"),
        ("n9", "9. PocketDetectionAgent"),
        ("n10", "10. MoleculeGenerationAgent"),
        ("n11", "11. DockingAgent"),
        ("n12", "12. SelectivityAgent"),
        ("n13", "13. ADMETAgent"),
        ("n14", "14. LeadOptimizationAgent"),
        ("n15", "15. GNNAffinityAgent"),
        ("n16", "16. MDValidationAgent"),
        ("n17", "17. ResistanceAgent"),
        ("n18", "18. SimilaritySearchAgent"),
        ("n19", "19. SynergyAgent"),
        ("n20", "20. ClinicalTrialAgent"),
        ("n21", "21. SynthesisAgent"),
        ("n22", "22. ReportAgent"),
        ("nend", "Neon PostgreSQL DB")
    ]
    
    edges = [
        ("nstart", "n1"), ("n1", "n2"),
        ("n2", "n3"), ("n2", "n4"), ("n2", "n5"), ("n2", "n6"),
        ("n3", "n7"), ("n4", "n7"), ("n5", "n7"), ("n6", "n7"),
        ("n7", "n8"), ("n8", "n9"), ("n9", "n10"), ("n10", "n11"),
        ("n11", "n12"), ("n12", "n13"), ("n13", "n14"), ("n14", "n15"),
        ("n15", "n16"), ("n16", "n17"),
        ("n17", "n18"), ("n17", "n19"), ("n17", "n20"),
        ("n18", "n21"), ("n19", "n21"), ("n20", "n21"),
        ("n21", "n22"), ("n22", "nend")
    ]

    # Layout params
    col_x = [400, 200, 400, 600, 800] 
    y_start = 50
    y_step = 100
    
    pos_map = {}
    current_y = y_start
    
    # Assign positions manually to ensure no overlap
    pos_map["nstart"] = (400, current_y)
    current_y += y_step
    pos_map["n1"] = (400, current_y)
    current_y += y_step
    pos_map["n2"] = (400, current_y)
    current_y += y_step
    
    # Parallel fetches
    pos_map["n3"] = (200, current_y)
    pos_map["n4"] = (400, current_y)
    pos_map["n5"] = (600, current_y)
    pos_map["n6"] = (800, current_y)
    current_y += y_step
    
    # Linear down to 17
    for id in [f"n{i}" for i in range(7, 18)]:
        pos_map[id] = (400, current_y)
        current_y += y_step
        
    # Parallel side tasks
    pos_map["n18"] = (200, current_y)
    pos_map["n19"] = (400, current_y)
    pos_map["n20"] = (600, current_y)
    current_y += y_step
    
    # Linear end
    pos_map["n21"] = (400, current_y)
    current_y += y_step
    pos_map["n22"] = (400, current_y)
    current_y += y_step
    pos_map["nend"] = (400, current_y)

    for nid, label in nodes:
        x, y = pos_map[nid]
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        cell = ET.SubElement(root, 'mxCell', id=nid, value=label, style=style, vertex="1", parent="1")
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width="180", height="60", **{'as': 'geometry'})
        
    for i, (f, t) in enumerate(edges):
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
        cell = ET.SubElement(root, 'mxCell', id=f"e{i}", style=style, edge="1", parent="1", source=f, target=t)
        ET.SubElement(cell, 'mxGeometry', relative="1", **{'as': 'geometry'})
        
    xml_str = ET.tostring(mxfile, encoding='utf-8').decode('utf-8')
    # Add proper XML declaration
    with open("workflow.drawio", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str)

if __name__ == "__main__":
    create_drawio_xml()
