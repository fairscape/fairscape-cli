import json
import os
import argparse
from pathlib import Path

def generate_evidence_graph_html(rocrate_path, output_path=None):
    """
    Generate a standalone HTML file containing an interactive React
    visualization of the evidence graph extracted from an RO-Crate.
    Includes panning functionality and adjusted node spacing.
    Automatically expands the first two levels of the graph.

    Args:
        rocrate_path: Path to the RO-Crate metadata.json file
        output_path: Path where the HTML output should be saved (default: same directory as input with .html extension)

    Returns:
        Path to the generated HTML file
    """
    try:
        with open(rocrate_path, 'r', encoding='utf-8') as f:
            rocrate_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: RO-Crate file not found at {rocrate_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {rocrate_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the RO-Crate: {e}")
        return None

    if output_path is None:
        output_path = Path(rocrate_path).with_suffix('.html')
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Note: Double curly braces {{ }} are used for literal braces in the f-string.
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evidence Graph Visualization</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@dagrejs/dagre@1.0.2/dist/dagre.min.js"></script>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            font-family: sans-serif;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        #root {{
            width: 100%;
            height: 100%;
            position: relative;
            overflow: hidden;
            background-color: #f8f9fa;
            cursor: grab;
        }}
         #root.dragging {{
            cursor: grabbing;
         }}
         .graph-viewport {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            will-change: transform;
         }}
         .graph-container {{
            position: relative;
            min-width: 1500px;
            min-height: 1000px;
            transform-origin: top left;
            background-color: #f8f9fa;
        }}
        .loading-overlay {{
            position: fixed;
            inset: 0;
            background-color: rgba(255, 255, 255, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            font-size: 1.2em;
            pointer-events: none;
        }}
        .node-wrapper {{
            position: absolute;
            cursor: default;
            box-sizing: border-box;
            transition: top 0.3s ease, left 0.3s ease;
            user-select: none;
        }}
        .node-container {{
            background: #fff;
            padding: 0;
            border-radius: 5px;
            border: 1px solid #ddd;
            text-align: center;
            width: 180px;
            height: 90px;
            font-size: 13px;
            position: relative;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-sizing: border-box;
        }}
        .node-container.expandable {{
            border: 2px dashed #333;
            cursor: pointer;
        }}
        .node-header {{
            padding: 8px 6px;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            width: 100%;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
            box-sizing: border-box;
            color: #333;
        }}
        .node-content {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px 15px;
            width: 100%;
            text-align: center;
            word-break: break-word;
            white-space: normal;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 12px;
            line-height: 1.3;
            box-sizing: border-box;
        }}
        .svg-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: visible;
        }}
        .edge-path {{
            stroke: #888;
            stroke-width: 1.5;
            fill: none;
        }}
        .edge-label-bg {{
             fill: #f8f9fa;
             stroke: #f8f9fa;
             stroke-width: 4px;
             stroke-linejoin: round;
             opacity: 0.8;
        }}
        .edge-label-text {{
            font-size: 10px;
            fill: #555;
            text-anchor: middle;
            dominant-baseline: middle;
            pointer-events: none;
        }}
        .controls-container {{
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #ddd;
            z-index: 5;
            display: flex;
            gap: 5px;
         }}
         .control-button {{
             padding: 4px 8px;
             font-size: 12px;
             cursor: pointer;
             border: 1px solid #ccc;
             background-color: #fff;
             border-radius: 3px;
         }}
         .control-button:hover {{
             background-color: #eee;
         }}
    </style>
</head>
<body>
    <div id="root"></div>

    <script>
    const evidenceGraphData = {json.dumps(rocrate_data, indent=2)};
    const MAX_LABEL_LENGTH = 50;
    const NODE_WIDTH = 180;
    const NODE_HEIGHT = 90;

    function getEntityType(typeUri) {{
        if (!typeUri) return "Unknown";
        const typeString = Array.isArray(typeUri) ? typeUri[0] : typeUri;
        const simpleType = typeString.split(/[#\\/]/).pop() || "Unknown";
        const eviPrefix = "evi:";
        const specificType = (Array.isArray(typeUri) ? typeUri : [typeUri])
            .map(t => t.split(/[#\\/]/).pop())
            .find(t => t && t.startsWith(eviPrefix));
        return specificType ? specificType.substring(eviPrefix.length) : simpleType;
    }}


    function abbreviateName(name, maxLength = MAX_LABEL_LENGTH) {{
        if (!name) return "";
        if (name.length <= maxLength) return name;
        return name.substring(0, maxLength - 3) + "...";
    }}

    function createEvidenceNode(entityData) {{
        if (!entityData || !entityData["@id"]) return null;
        const id = entityData["@id"];
        const type = getEntityType(entityData["@type"]);
        const label = entityData.name || entityData.label || id;
        const displayName = abbreviateName(label);
        const description = entityData.description || "";

        const hasGeneratedBy = !!entityData.generatedBy;
        const hasUsedSoftware = !!entityData.usedSoftware && (!Array.isArray(entityData.usedSoftware) || entityData.usedSoftware.length > 0);
        const hasUsedDataset = !!entityData.usedDataset && (!Array.isArray(entityData.usedDataset) || entityData.usedDataset.length > 0);
        const hasUsedSample = !!entityData.usedSample && (!Array.isArray(entityData.usedSample) || entityData.usedSample.length > 0);
        const hasUsedInstrument = !!entityData.usedInstrument && (!Array.isArray(entityData.usedInstrument) || entityData.usedInstrument.length > 0);

        let isExpandable = false;
        if (type === "Dataset" && hasGeneratedBy) {{ isExpandable = true; }}
        if ((type === "Computation" || type === "Experiment") && (hasUsedSoftware || hasUsedDataset || hasUsedSample || hasUsedInstrument)) {{ isExpandable = true; }}

        if (isExpandable) {{
            const checkRelation = (prop) => {{
                const value = entityData[prop];
                if (!value) return false;
                if (Array.isArray(value)) return value.some(item => item && (typeof item === 'string' || (typeof item === 'object' && item['@id'])));
                return typeof value === 'string' || (typeof value === 'object' && value['@id']);
            }};
            isExpandable = checkRelation('generatedBy') || checkRelation('usedSoftware') || checkRelation('usedDataset') || checkRelation('usedSample') || checkRelation('usedInstrument');
        }}

        const nodeData = {{
            id: id,
            type: type,
            label: label,
            displayName: displayName,
            description: description,
            expandable: isExpandable,
            _sourceData: {{ ...entityData }},
            _expanded: false,
            x: 0,
            y: 0,
            width: NODE_WIDTH,
            height: NODE_HEIGHT
        }};
        return nodeData;
    }}

     function createDatasetCollectionNode(computationId, datasets) {{
        const collectionId = `${{computationId}}_dataset_collection_${{Date.now()}}`;
        const validDatasets = datasets.filter(ds => ds && (typeof ds === "string" || (typeof ds === "object" && ds["@id"])))
                                      .map(ds => typeof ds === "string" ? {{ "@id": ds, "@type": "evi:Dataset" }} : ds);

        const count = validDatasets.length;
        if (count === 0) return null;

        const label = `Input Datasets (${{count}})`;
        const displayName = `Datasets (${{count}})`;

        const nodeData = {{
            id: collectionId,
            type: "DatasetCollection",
            label: label,
            displayName: displayName,
            description: `A collection of ${{count}} datasets used by ${{computationId.split(/[/#]/).pop()}}`,
            expandable: count > 0,
            _sourceData: {{ "@id": collectionId, "@type": "evi:DatasetCollection", name: label, count: count }},
            _remainingDatasets: [...validDatasets],
            _expandedCount: 0,
            _expanded: false,
            x: 0,
            y: 0,
            width: NODE_WIDTH,
            height: NODE_HEIGHT
        }};
        return nodeData;
    }}


    function getGraphEntities(graphData) {{
        if (!graphData || !graphData["@graph"]) return {{}};
        const entities = Array.isArray(graphData["@graph"]) ? graphData["@graph"] : [graphData["@graph"]];
        const rootEntity = entities.find(e => e["@id"] === "./" || e["@id"] === "ro-crate-metadata.json") || entities[0];
        const entityMap = new Map();
        entities.forEach(e => {{
            if (e && e["@id"]) {{
                entityMap.set(e["@id"], e);
            }}
        }});
        return {{ rootEntityId: rootEntity ? rootEntity["@id"] : null, entityMap }};
    }}


    function getInitialGraphState(graphData, initialExpansionDepth = 2) {{
        const {{ rootEntityId, entityMap }} = getGraphEntities(graphData);
        if (!rootEntityId || !entityMap.has(rootEntityId)) {{
            console.error("Could not determine root entity or find it in the graph data.");
            return {{ nodes: [], edges: [] }};
        }}

        let nodes = [];
        let edges = [];
        let nodesToExpand = new Set();
        const addedNodeIds = new Set();

        const rootEntityData = entityMap.get(rootEntityId);
        const rootNode = createEvidenceNode(rootEntityData);

        if (!rootNode) {{
            console.error("Failed to create root node.");
            return {{ nodes: [], edges: [] }};
        }}

        nodes.push(rootNode);
        addedNodeIds.add(rootNode.id);
        if (rootNode.expandable) {{
            nodesToExpand.add(rootNode.id);
        }}

        let currentLevelIds = new Set([rootNode.id]);
        for (let level = 0; level < initialExpansionDepth; level++) {{
            let nextLevelIds = new Set();
            if (currentLevelIds.size === 0) break;

            currentLevelIds.forEach(nodeId => {{
                 const nodeIndex = nodes.findIndex(n => n.id === nodeId);
                 if (nodeIndex === -1) return;
                 const node = nodes[nodeIndex];

                 if (!node || !node.expandable || node._expanded) return;

                 let expansionResult;
                 if (node.type === "DatasetCollection") {{
                     expansionResult = expandDatasetCollectionNodeInternal(node, nodes, edges, entityMap);
                 }} else {{
                     expansionResult = expandNodeInternal(node, nodes, edges, entityMap);
                 }}
                 const {{ newNodes, newEdges, updatedCollectionData }} = expansionResult;

                if (newNodes.length > 0 || newEdges.length > 0 || updatedCollectionData) {{

                     let updatedNode = {{...node}};
                     if (updatedCollectionData) {{
                         updatedNode = {{...updatedNode, ...updatedCollectionData}};
                     }} else {{
                         updatedNode._expanded = true;
                         updatedNode.expandable = false;
                     }}
                     nodes[nodeIndex] = updatedNode;


                     expansionResult.newNodes.forEach(newNode => {{
                        if (!addedNodeIds.has(newNode.id)) {{
                            nodes.push(newNode);
                            addedNodeIds.add(newNode.id);
                            if (newNode.expandable) {{
                                nextLevelIds.add(newNode.id);
                            }}
                        }}
                    }});
                    expansionResult.newEdges.forEach(newEdge => {{
                        if (!edges.some(e => e.id === newEdge.id)) {{
                            edges.push(newEdge);
                        }}
                    }});
                 }} else {{
                    nodes[nodeIndex] = {{...node, expandable: false}};
                 }}
            }});
            currentLevelIds = nextLevelIds;
        }}

        nodes.forEach((node, index) => {{
             if (!node._expanded) {{
                 const checkAgain = createEvidenceNode(node._sourceData);
                 let stillExpandable = checkAgain ? checkAgain.expandable : false;
                 if (node.type === 'DatasetCollection') {{
                    stillExpandable = node._remainingDatasets && node._remainingDatasets.length > 0;
                 }}
                 if (nodes[index].expandable !== stillExpandable) {{
                     nodes[index] = {{...node, expandable: stillExpandable}};
                 }}
             }}
        }});


        return {{ nodes, edges }};
    }}

    function expandNodeInternal(node, currentNodes, currentEdges, entityMap) {{
        const nodeId = node.id;
        const nodeType = node.type;
        const sourceData = node._sourceData;
        const result = {{ newNodes: [], newEdges: [] }};

        const nodeExists = (id) => currentNodes.some(n => n.id === id) || result.newNodes.some(n => n.id === id);
        const addNodeAndEdge = (targetEntityRef, relationshipLabel, relationshipType) => {{
            if (!targetEntityRef) return;

            let targetEntityData = null;
            let targetId = null;

            if (typeof targetEntityRef === 'string') {{
                targetId = targetEntityRef;
                targetEntityData = entityMap.get(targetId);
            }} else if (typeof targetEntityRef === 'object' && targetEntityRef['@id']) {{
                targetId = targetEntityRef['@id'];
                targetEntityData = entityMap.has(targetId) ? {{ ...entityMap.get(targetId), ...targetEntityRef }} : targetEntityRef;
            }}

            if (!targetId) {{
                 console.warn(`Invalid target entity reference for ${{relationshipType}}:`, targetEntityRef);
                 return;
            }}

             if (!targetEntityData && entityMap.has(targetId)) {{
                 targetEntityData = entityMap.get(targetId);
             }}

            if (!targetEntityData) {{
                console.warn(`Could not find entity data for ID: ${{targetId}} (relation: ${{relationshipType}} from ${{nodeId}})`);
                 return;
            }}

            const targetNode = createEvidenceNode(targetEntityData);
            if (targetNode) {{
                if (!nodeExists(targetNode.id)) {{
                    result.newNodes.push(targetNode);
                }}
                 const edgeId = `${{nodeId}}_${{relationshipType}}_${{targetNode.id}}`.replace(/[^a-zA-Z0-9_]/g, '-');
                 const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                 if (!edgeExists) {{
                    result.newEdges.push({{
                        id: edgeId,
                        source: nodeId,
                        target: targetNode.id,
                        label: relationshipLabel,
                        animated: false
                    }});
                }}
            }}
        }};

        if (nodeType === "Dataset" && sourceData.generatedBy) {{
            addNodeAndEdge(sourceData.generatedBy, "generated by", "generatedBy");
        }}

        if ((nodeType === "Computation" || nodeType === "Experiment")) {{
             const relations = [
                {{ prop: 'usedSoftware', label: 'used software', type: 'uses_sw' }},
                {{ prop: 'usedDataset', label: 'used dataset', type: 'uses_ds' }},
                {{ prop: 'usedSample', label: 'used sample', type: 'uses_sample' }},
                {{ prop: 'usedInstrument', label: 'used instrument', type: 'uses_instrument' }}
             ];

             relations.forEach(rel => {{
                 const items = sourceData[rel.prop];
                 if (items) {{
                    const itemList = Array.isArray(items) ? items : [items];

                    if (rel.prop === 'usedDataset' && itemList.length > 1) {{
                         const validDatasetRefs = itemList.filter(ds => ds && (typeof ds === "string" || (typeof ds === "object" && ds["@id"])));
                         if (validDatasetRefs.length > 1) {{
                            const collectionNode = createDatasetCollectionNode(nodeId, validDatasetRefs);
                             if (collectionNode) {{
                                if (!nodeExists(collectionNode.id)) {{
                                    result.newNodes.push(collectionNode);
                                }}
                                const edgeId = `${{nodeId}}_${{rel.type}}_coll_${{collectionNode.id}}`.replace(/[^a-zA-Z0-9_]/g, '-');
                                const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                                if (!edgeExists) {{
                                    result.newEdges.push({{ id: edgeId, source: nodeId, target: collectionNode.id, label: rel.label, animated: false }});
                                }}
                            }}
                            return;
                         }}
                     }}

                    itemList.forEach(itemRef => {{
                         addNodeAndEdge(itemRef, rel.label, rel.type);
                    }});
                 }}
             }});
        }}

        return result;
    }}

    function expandDatasetCollectionNodeInternal(collectionNode, currentNodes, currentEdges, entityMap) {{
        const nodeId = collectionNode.id;
        const result = {{ newNodes: [], newEdges: [], updatedCollectionData: null }};
        const originalData = collectionNode;
        const remaining = originalData._remainingDatasets;

        if (!remaining || remaining.length === 0) {{
            return {{ ...result, updatedCollectionData: {{ expandable: false, label: `Input Datasets (All Shown)`, displayName: `Datasets (All)` }} }};
        }}

        const datasetToExpandRef = remaining[0];
        let datasetNode = null;

        const nodeExists = (id) => currentNodes.some(n => n.id === id) || result.newNodes.some(n => n.id === id);

        let datasetEntityData = null;
        let datasetId = null;
        if (typeof datasetToExpandRef === 'string') {{
            datasetId = datasetToExpandRef;
            datasetEntityData = entityMap.get(datasetId);
        }} else if (typeof datasetToExpandRef === 'object' && datasetToExpandRef['@id']) {{
            datasetId = datasetToExpandRef['@id'];
            datasetEntityData = entityMap.has(datasetId) ? {{ ...entityMap.get(datasetId), ...datasetToExpandRef }} : datasetToExpandRef;
        }}

         if (datasetId && datasetEntityData) {{
            datasetNode = createEvidenceNode(datasetEntityData);
            if (datasetNode) {{
                if (!nodeExists(datasetNode.id)) {{
                    result.newNodes.push(datasetNode);
                }}
                 const edgeId = `${{nodeId}}_contains_${{datasetNode.id}}_${{originalData._expandedCount || 0}}`.replace(/[^a-zA-Z0-9_]/g, '-');
                 const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                 if (!edgeExists) {{
                    result.newEdges.push({{ id: edgeId, source: nodeId, target: datasetNode.id, label: "contains", animated: false }});
                }}
            }} else {{
                 console.warn("Failed to create node for dataset in collection:", datasetEntityData);
            }}
         }} else {{
             console.warn(`Could not find entity data for dataset ID in collection: ${{datasetId || JSON.stringify(datasetToExpandRef)}}`);
         }}

        const nextRemaining = remaining.slice(1);
        const nextExpandedCount = (originalData._expandedCount || 0) + 1;
        const nextExpandable = nextRemaining.length > 0;
        const nextLabel = nextExpandable ? `Input Datasets (${{nextRemaining.length}} more)` : `Input Datasets (All Shown)`;
        const nextDisplayName = nextExpandable ? `Datasets (${{nextRemaining.length}})` : `Datasets (All)`;

        result.updatedCollectionData = {{
            _remainingDatasets: nextRemaining,
            _expandedCount: nextExpandedCount,
            expandable: nextExpandable,
            label: nextLabel,
            displayName: nextDisplayName
        }};

        return result;
    }}


    function getLayoutedElements(nodes, edges, direction = "LR") {{
        if (!nodes || nodes.length === 0) {{
            console.log("Layout skipped: No nodes provided.");
            return {{ nodes, edges, width: 0, height: 0 }};
        }}
        const dagreGraph = new dagre.graphlib.Graph();
        dagreGraph.setDefaultEdgeLabel(() => ({{}}));

        const NODE_SEP = 50;
        const RANK_SEP = 80;
        const MARGIN_X = 50;
        const MARGIN_Y = 50;

        dagreGraph.setGraph({{
            rankdir: direction,
            nodesep: NODE_SEP,
            ranksep: RANK_SEP,
            marginx: MARGIN_X,
            marginy: MARGIN_Y,
            align: 'DL'
        }});

        nodes.forEach(node => {{
            dagreGraph.setNode(node.id, {{ width: NODE_WIDTH, height: NODE_HEIGHT, label: node.displayName }});
        }});

        edges.forEach(edge => {{
             if (nodes.some(n => n.id === edge.source) && nodes.some(n => n.id === edge.target)) {{
                dagreGraph.setEdge(edge.source, edge.target);
            }} else {{
                console.warn("Skipping edge due to missing node:", edge.id, edge.source, edge.target);
            }}
        }});

        try {{
            dagre.layout(dagreGraph);
        }} catch (e) {{
            console.error("Dagre layout calculation failed:", e);
            const layoutedNodes = nodes.map(node => ({{ ...node, x: node.x || Math.random()*500, y: node.y || Math.random()*500 }}));
            return {{ nodes: layoutedNodes, edges, width: 800, height: 600 }};
        }}

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

        const layoutedNodes = nodes.map(node => {{
            const nodeWithPosition = dagreGraph.node(node.id);
            if (nodeWithPosition) {{
                const x = nodeWithPosition.x - NODE_WIDTH / 2;
                const y = nodeWithPosition.y - NODE_HEIGHT / 2;

                 minX = Math.min(minX, x);
                 maxX = Math.max(maxX, x + NODE_WIDTH);
                 minY = Math.min(minY, y);
                 maxY = Math.max(maxY, y + NODE_HEIGHT);

                return {{ ...node, x: x, y: y, width: NODE_WIDTH, height: NODE_HEIGHT }};
            }} else {{
                console.warn(`Node ${{node.id}} not found in Dagre layout results. Keeping previous position or placing randomly.`);
                const x = node.x || Math.random() * 500;
                const y = node.y || Math.random() * 500;
                 minX = Math.min(minX, x);
                 maxX = Math.max(maxX, x + NODE_WIDTH);
                 minY = Math.min(minY, y);
                 maxY = Math.max(maxY, y + NODE_HEIGHT);
                return {{ ...node, x: x, y: y, width: NODE_WIDTH, height: NODE_HEIGHT }};
            }}
        }});

        const graphWidth = Math.max(1500, maxX - minX + 2 * MARGIN_X);
        const graphHeight = Math.max(1000, maxY - minY + 2 * MARGIN_Y);

         const offsetX = MARGIN_X - minX;
         const offsetY = MARGIN_Y - minY;
         const adjustedNodes = layoutedNodes.map(n => ({{...n, x: n.x + offsetX, y: n.y + offsetY }}));

        return {{ nodes: adjustedNodes, edges, width: graphWidth, height: graphHeight }};
    }}

    function getNodeColor(type) {{
        switch (type) {{
            case "Dataset": case "Sample": return "#8AE68A";
            case "Computation": case "Experiment": return "#FD9A9A";
            case "Software": case "Instrument": return "#FFC107";
            case "DatasetCollection": return "#B5DEFF";
            default: return "#E0E0E0";
        }}
    }}

    const {{ createElement, useState, useCallback, useEffect, useRef, memo }} = React;

    const EvidenceNode = memo(({{ nodeData, onClick }}) => {{
        const {{ id, type, displayName, expandable, x, y, width, height }} = nodeData;
        const nodeColor = getNodeColor(type);

        const handleClick = useCallback((event) => {{
            event.stopPropagation();
            if (expandable && onClick) {{
                onClick(id);
            }}
        }}, [id, expandable, onClick]);

        const style = {{
            left: `${{x}}px`,
            top: `${{y}}px`,
            width: `${{width}}px`,
            height: `${{height}}px`,
        }};

        const containerClasses = ['node-container'];
        if (expandable) {{
            containerClasses.push('expandable');
        }}

        return createElement(
            'div',
            {{ style: style, className: 'node-wrapper', onClick: handleClick, onMouseDown: (e) => e.stopPropagation() }},
            createElement('div', {{ className: containerClasses.join(' ') }}, [
                createElement('div', {{ key: 'header', className: 'node-header', style: {{ backgroundColor: nodeColor }} }}, type),
                createElement('div', {{ key: 'content', className: 'node-content' }},
                     createElement('div', {{ style: {{ width: '100%', textAlign: 'center' }} }}, displayName)
                )
            ])
        );
    }});

    const Edge = memo(({{ edgeData, sourceNode, targetNode }}) => {{
        if (!sourceNode || !targetNode || sourceNode.x === undefined || targetNode.x === undefined) {{
             return null;
        }}

        const sourceX = sourceNode.x + sourceNode.width;
        const sourceY = sourceNode.y + sourceNode.height / 2;
        const targetX = targetNode.x;
        const targetY = targetNode.y + targetNode.height / 2;

        const dx = targetX - sourceX;
        const dy = targetY - sourceY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let pathD;
        if (dist < 100) {{
            pathD = `M ${{sourceX}} ${{sourceY}} L ${{targetX}} ${{targetY}}`;
        }} else {{
            const midX = (sourceX + targetX) / 2;
            const midY = (sourceY + targetY) / 2;
            const c1X = sourceX + dx * 0.3;
            const c1Y = sourceY;
            const c2X = targetX - dx * 0.3;
            const c2Y = targetY;
            pathD = `M ${{sourceX}} ${{sourceY}} C ${{c1X}},${{c1Y}} ${{c2X}},${{c2Y}} ${{targetX}},${{targetY}}`;
        }}


        const labelX = (sourceX + targetX) / 2;
        const labelY = (sourceY + targetY) / 2;

        return createElement(
            'g',
            {{ key: edgeData.id }},
            [
                createElement('path', {{
                    className: 'edge-path',
                    d: pathD,
                    markerEnd: 'url(#arrowhead)'
                }}),
                 createElement('rect', {{
                     key: `${{edgeData.id}}-bg`,
                     className: 'edge-label-bg',
                     x: labelX - 25,
                     y: labelY - 8,
                     width: 50,
                     height: 16,
                     rx: 3,
                 }}),
                createElement('text', {{
                    key: `${{edgeData.id}}-text`,
                    className: 'edge-label-text',
                    x: labelX,
                    y: labelY,
                    dy: "0.em"
                }}, edgeData.label || '')
            ]
        );
    }});


    const GraphRenderer = ({{ graphData }}) => {{
        const [nodes, setNodes] = useState([]);
        const [edges, setEdges] = useState([]);
        const [isLoading, setIsLoading] = useState(true);
        const [graphWidth, setGraphWidth] = useState(1500);
        const [graphHeight, setGraphHeight] = useState(1000);
        const entityMapRef = useRef(new Map());
        const [scale, setScale] = useState(1);
        const [translate, setTranslate] = useState({{ x: 0, y: 0 }});
        const [isDragging, setIsDragging] = useState(false);
        const [startDragPos, setStartDragPos] = useState({{ x: 0, y: 0 }});
        const rootRef = useRef(null);


        const applyLayout = useCallback((nodesToLayout, edgesToLayout) => {{
            setIsLoading(true);
            setTimeout(() => {{
                try {{
                    const nodesWithDims = nodesToLayout.map(n => ({{ ...n, width: NODE_WIDTH, height: NODE_HEIGHT }}));
                    const {{ nodes: layoutedNodes, edges: finalEdges, width, height }} = getLayoutedElements(nodesWithDims, edgesToLayout, "LR");
                    setNodes(layoutedNodes);
                    setEdges(finalEdges);
                    setGraphWidth(width);
                    setGraphHeight(height);
                }} catch (error) {{
                    console.error("Layout application failed:", error);
                    setNodes(nodesToLayout);
                    setEdges(edgesToLayout);
                }} finally {{
                    setIsLoading(false);
                }}
            }}, 10);
        }}, []);

        useEffect(() => {{
            if (!graphData) {{
                setIsLoading(false);
                return;
            }}
             const {{ rootEntityId, entityMap }} = getGraphEntities(graphData);
             if (!rootEntityId) {{
                 console.error("No root entity found on initial load.");
                 setIsLoading(false);
                 return;
             }}
             entityMapRef.current = entityMap;

             // Initial expansion depth is now handled by the default parameter in getInitialGraphState
             const {{ nodes: initialNodes, edges: initialEdges }} = getInitialGraphState(graphData);

             if (initialNodes.length > 0) {{
                applyLayout(initialNodes, initialEdges);
             }} else {{
                setNodes([]);
                setEdges([]);
                setIsLoading(false);
             }}

        }}, [graphData, applyLayout]);


        const handleNodeClick = useCallback((nodeId) => {{
            const clickedNodeIndex = nodes.findIndex(n => n.id === nodeId);
            if (clickedNodeIndex === -1) return;

            const clickedNode = nodes[clickedNodeIndex];
            if (!clickedNode.expandable) return;

            setIsLoading(true);

            let expansionResult;
            if (clickedNode.type === "DatasetCollection") {{
                expansionResult = expandDatasetCollectionNodeInternal(clickedNode, nodes, edges, entityMapRef.current);
            }} else {{
                expansionResult = expandNodeInternal(clickedNode, nodes, edges, entityMapRef.current);
            }}

            const {{ newNodes, newEdges, updatedCollectionData }} = expansionResult;

            let nextNodes = [...nodes];
            let nodeUpdated = false;

             const originalNode = nextNodes[clickedNodeIndex];
             let updatedNodeData = {{ ...originalNode }};

             if (updatedCollectionData) {{
                 updatedNodeData = {{ ...updatedNodeData, ...updatedCollectionData }};
                 nodeUpdated = true;
             }} else if (newNodes.length > 0 || newEdges.length > 0) {{
                updatedNodeData._expanded = true;
                updatedNodeData.expandable = false;
                nodeUpdated = true;
             }} else {{
                updatedNodeData.expandable = false;
                nodeUpdated = true;
             }}

             if (nodeUpdated) {{
                nextNodes[clickedNodeIndex] = updatedNodeData;
             }}

            const nodesToAdd = newNodes.filter(newNode => !nextNodes.some(existingNode => existingNode.id === newNode.id));
            nextNodes = [...nextNodes, ...nodesToAdd];

            const combinedEdges = [...edges];
            newEdges.forEach(newEdge => {{
                if (!combinedEdges.some(existingEdge => existingEdge.id === newEdge.id)) {{
                    combinedEdges.push(newEdge);
                }}
            }});

             applyLayout(nextNodes, combinedEdges);

        }}, [nodes, edges, applyLayout]);


        const nodeMap = new Map(nodes.map(node => [node.id, node]));

        const zoomIn = useCallback(() => setScale(s => Math.min(s * 1.2, 3)), []);
        const zoomOut = useCallback(() => setScale(s => Math.max(s / 1.2, 0.2)), []);

        const handleMouseDown = useCallback((event) => {{
            if (event.button !== 0) return;
             if (event.target.closest('.controls-container') || event.target.closest('.node-wrapper')) {{
                 return;
             }}
            setIsDragging(true);
            setStartDragPos({{ x: event.clientX - translate.x, y: event.clientY - translate.y }});
            if(rootRef.current) rootRef.current.classList.add('dragging');
            event.preventDefault();
        }}, [translate.x, translate.y]);

        const handleMouseMove = useCallback((event) => {{
            if (!isDragging) return;
            const newX = event.clientX - startDragPos.x;
            const newY = event.clientY - startDragPos.y;
            setTranslate({{ x: newX, y: newY }});
        }}, [isDragging, startDragPos]);

        const handleMouseUp = useCallback(() => {{
            if (!isDragging) return;
            setIsDragging(false);
             if(rootRef.current) rootRef.current.classList.remove('dragging');
        }}, [isDragging]);

         const handleMouseLeave = useCallback(() => {{
            if (isDragging) {{
                setIsDragging(false);
                if(rootRef.current) rootRef.current.classList.remove('dragging');
            }}
        }}, [isDragging]);


        useEffect(() => {{
            const currentRoot = rootRef.current;
            if (currentRoot) {{
                 currentRoot.addEventListener('mousedown', handleMouseDown);
                 currentRoot.addEventListener('mousemove', handleMouseMove);
                 currentRoot.addEventListener('mouseup', handleMouseUp);
                 currentRoot.addEventListener('mouseleave', handleMouseLeave);

                 return () => {{
                     currentRoot.removeEventListener('mousedown', handleMouseDown);
                     currentRoot.removeEventListener('mousemove', handleMouseMove);
                     currentRoot.removeEventListener('mouseup', handleMouseUp);
                     currentRoot.removeEventListener('mouseleave', handleMouseLeave);
                 }};
            }}
        }}, [handleMouseDown, handleMouseMove, handleMouseUp, handleMouseLeave]);


        return React.createElement(
            'div',
            {{ ref: rootRef, style:{{ width: '100%', height: '100%', overflow: 'hidden', position: 'relative'}} }},
            [
                createElement('div', {{
                    key: 'viewport',
                    className: 'graph-viewport',
                    style: {{
                        transform: `translate(${{translate.x}}px, ${{translate.y}}px) scale(${{scale}})`,
                    }}
                 }},
                    createElement(
                        'div',
                        {{ className: 'graph-container', style: {{ width: `${{graphWidth}}px`, height: `${{graphHeight}}px` }} }},
                        [
                            createElement('svg', {{ key: 'svg-layer', className: 'svg-layer', width: graphWidth, height: graphHeight }}, [
                                createElement('defs', {{key: 'defs'}},
                                    createElement('marker', {{
                                        id: 'arrowhead',
                                        viewBox: '0 -5 10 10',
                                        refX: 8,
                                        refY: 0,
                                        markerWidth: 6,
                                        markerHeight: 6,
                                        orient: 'auto'
                                    }}, createElement('path', {{ d: 'M0,-5L10,0L0,5', fill: '#888' }}))
                                ),
                                createElement('g', {{ key: 'edges-group' }},
                                    edges.map(edge => createElement(Edge, {{
                                        key: edge.id,
                                        edgeData: edge,
                                        sourceNode: nodeMap.get(edge.source),
                                        targetNode: nodeMap.get(edge.target)
                                    }}))
                                )
                            ]),

                            createElement('div', {{ key: 'nodes-layer', style: {{ position: 'relative', width: '100%', height: '100%' }} }},
                                nodes.map(node => createElement(EvidenceNode, {{
                                    key: node.id,
                                    nodeData: node,
                                    onClick: handleNodeClick
                                }}))
                            )
                        ]
                    )
                ),
                 isLoading && createElement('div', {{ key: 'loading', className: 'loading-overlay' }}, 'Loading...'),

                 createElement('div', {{key: 'controls', className: 'controls-container'}}, [
                    createElement('button', {{ key: 'zoom-in', className: 'control-button', onClick: zoomIn }}, '+'),
                    createElement('button', {{ key: 'zoom-out', className: 'control-button', onClick: zoomOut }}, '-')
                 ])
            ]
        );
    }};

    const App = () => {{
        return React.createElement(GraphRenderer, {{ graphData: evidenceGraphData }});
    }};

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(App));

    </script>
</body>
</html>
    """

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Evidence graph visualization saved to: {output_path}")
        return str(output_path)
    except IOError as e:
        print(f"Error writing HTML file to {output_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while writing the HTML file: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate an evidence graph visualization from an RO-Crate using React (without React Flow)')
    parser.add_argument('rocrate_path', help='Path to the RO-Crate metadata.json file (or equivalent .jsonld)')
    parser.add_argument('--output', '-o', help='Output HTML file path (default: <rocrate_path_base>-evidence-graph.html)')

    args = parser.parse_args()

    crate_path = Path(args.rocrate_path)
    if not crate_path.is_file():
         print(f"Error: Input file not found at '{args.rocrate_path}'")
    else:
        output_file = args.output
        if not output_file:
            output_file = crate_path.parent / f"{crate_path.stem}-evidence-graph.html"


        generate_evidence_graph_html(str(crate_path), str(output_file))