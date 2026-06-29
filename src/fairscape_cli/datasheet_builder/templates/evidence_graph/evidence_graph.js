const evidenceGraphData = window.__EVIDENCE_GRAPH_DATA__;
    const MAX_LABEL_LENGTH = 50;
    const NODE_WIDTH = 180;
    const NODE_HEIGHT = 90;

    function getEntityType(typeUri) {
        if (!typeUri) return "Unknown";
        const typeString = Array.isArray(typeUri) ? typeUri[typeUri.length - 1] : typeUri;
        const simpleType = typeString.split(/[#\/]/).pop() || "Unknown";
        const eviPrefix = "evi:";
        const specificType = (Array.isArray(typeUri) ? typeUri : [typeUri])
            .map(t => t.split(/[#\/]/).pop())
            .find(t => t && t.startsWith(eviPrefix));
        return specificType ? specificType.substring(eviPrefix.length) : simpleType;
    }


    function abbreviateName(name, maxLength = MAX_LABEL_LENGTH) {
        if (!name) return "";
        if (name.length <= maxLength) return name;
        return name.substring(0, maxLength - 3) + "...";
    }

    function createEvidenceNode(entityData) {
        if (!entityData || !entityData["@id"]) return null;
        const id = entityData["@id"];
        const type = getEntityType(entityData["@type"]);
        let label = entityData.name || entityData.label || id;
        const description = entityData.description || "";

        const hasGeneratedBy = !!entityData.generatedBy;
        const hasUsedSoftware = !!entityData.usedSoftware && (!Array.isArray(entityData.usedSoftware) || entityData.usedSoftware.length > 0);
        const hasUsedDataset = !!entityData.usedDataset && (!Array.isArray(entityData.usedDataset) || entityData.usedDataset.length > 0);
        const hasUsedSample = !!entityData.usedSample && (!Array.isArray(entityData.usedSample) || entityData.usedSample.length > 0);
        const hasUsedInstrument = !!entityData.usedInstrument && (!Array.isArray(entityData.usedInstrument) || entityData.usedInstrument.length > 0);
        // DatasetGroup is a UI condensation node emitted by EvidenceGraphBuilder when
        // many Datasets share identical provenance. It carries `evi:representativeDataset`
        // (a pointer to one member) and `evi:memberCount`/`evi:memberIds`. The graph
        // should not dead-end at the group — clicking it (or auto-expansion) should
        // follow the representative onward.
        const hasGroupRepresentative = !!(entityData["evi:representativeDataset"]
            && (typeof entityData["evi:representativeDataset"] === "string"
                || entityData["evi:representativeDataset"]["@id"]));

        let isExpandable = false;
        if (type === "Dataset" && hasGeneratedBy) { isExpandable = true; }
        if ((type === "Computation" || type === "Experiment") && (hasUsedSoftware || hasUsedDataset || hasUsedSample || hasUsedInstrument)) { isExpandable = true; }
        if (type === "DatasetGroup" && hasGroupRepresentative) { isExpandable = true; }

        if (type === "DatasetGroup") {
            const memberCount = entityData["evi:memberCount"]
                || (Array.isArray(entityData["evi:memberIds"]) ? entityData["evi:memberIds"].length : 0);
            if (memberCount) {
                label = `${label} — ${memberCount} members`;
            }
        }
        const displayName = abbreviateName(label);

        if (isExpandable && type !== "DatasetGroup") {
            const checkRelation = (prop) => {
                const value = entityData[prop];
                if (!value) return false;
                if (Array.isArray(value)) return value.some(item => item && (typeof item === 'string' || (typeof item === 'object' && item['@id'])));
                return typeof value === 'string' || (typeof value === 'object' && value['@id']);
            };
            isExpandable = checkRelation('generatedBy') || checkRelation('usedSoftware') || checkRelation('usedDataset') || checkRelation('usedSample') || checkRelation('usedInstrument');
        }

        const nodeData = {
            id: id,
            type: type,
            label: label,
            displayName: displayName,
            description: description,
            expandable: isExpandable,
            _sourceData: { ...entityData },
            _expanded: false,
            x: 0,
            y: 0,
            width: NODE_WIDTH,
            height: NODE_HEIGHT
        };
        return nodeData;
    }

     function createDatasetCollectionNode(computationId, datasets) {
        const collectionId = `${computationId}_dataset_collection_${Date.now()}`;
        const validDatasets = datasets.filter(ds => ds && (typeof ds === "string" || (typeof ds === "object" && ds["@id"])))
                                      .map(ds => typeof ds === "string" ? { "@id": ds, "@type": "evi:Dataset" } : ds);

        const count = validDatasets.length;
        if (count === 0) return null;

        const label = `Input Datasets (${count})`;
        const displayName = `Datasets (${count})`;

        const nodeData = {
            id: collectionId,
            type: "DatasetCollection",
            label: label,
            displayName: displayName,
            description: `A collection of ${count} datasets used by ${computationId.split(/[/#]/).pop()}`,
            expandable: count > 0,
            _sourceData: { "@id": collectionId, "@type": "evi:DatasetCollection", name: label, count: count },
            _remainingDatasets: [...validDatasets],
            _expandedCount: 0,
            _expanded: false,
            x: 0,
            y: 0,
            width: NODE_WIDTH,
            height: NODE_HEIGHT
        };
        return nodeData;
    }


    function getGraphEntities(graphData) {
        if (!graphData || !graphData["@graph"]) return {};
        const graphField = graphData["@graph"];

        let entities;
        if (Array.isArray(graphField)) {
            entities = graphField;
        } else if (typeof graphField === "object" && graphField["@id"]) {
            entities = [graphField];
        } else if (typeof graphField === "object") {
            // EvidenceGraphBuilder format: @graph is a dict keyed by entity @id
            entities = Object.values(graphField);
        } else {
            entities = [];
        }

        const entityMap = new Map();
        entities.forEach(e => {
            if (e && e["@id"]) {
                entityMap.set(e["@id"], e);
            }
        });

        let rootEntityId = null;
        if (Array.isArray(graphData.outputs) && graphData.outputs.length > 0) {
            const firstOut = graphData.outputs[0];
            rootEntityId = typeof firstOut === "string"
                ? firstOut
                : (firstOut && firstOut["@id"]) || null;
        }
        if (!rootEntityId) {
            const rootEntity = entities.find(e => e["@id"] === "./" || e["@id"] === "ro-crate-metadata.json") || entities[0];
            rootEntityId = rootEntity ? rootEntity["@id"] : null;
        }

        return { rootEntityId, entityMap };
    }


    // Default expansion depth covers the full chain when a DatasetGroup is in the path:
    // root Dataset → Computation → (Software, DatasetGroup → representative → Experiment → Sample/Instrument).
    function getInitialGraphState(graphData, initialExpansionDepth = 6) {
        const { rootEntityId, entityMap } = getGraphEntities(graphData);
        if (!rootEntityId || !entityMap.has(rootEntityId)) {
            console.error("Could not determine root entity or find it in the graph data.");
            return { nodes: [], edges: [] };
        }

        let nodes = [];
        let edges = [];
        let nodesToExpand = new Set();
        const addedNodeIds = new Set();

        const rootEntityData = entityMap.get(rootEntityId);
        const rootNode = createEvidenceNode(rootEntityData);

        if (!rootNode) {
            console.error("Failed to create root node.");
            return { nodes: [], edges: [] };
        }

        nodes.push(rootNode);
        addedNodeIds.add(rootNode.id);
        if (rootNode.expandable) {
            nodesToExpand.add(rootNode.id);
        }

        let currentLevelIds = new Set([rootNode.id]);
        for (let level = 0; level < initialExpansionDepth; level++) {
            let nextLevelIds = new Set();
            if (currentLevelIds.size === 0) break;

            currentLevelIds.forEach(nodeId => {
                 const nodeIndex = nodes.findIndex(n => n.id === nodeId);
                 if (nodeIndex === -1) return;
                 const node = nodes[nodeIndex];

                 if (!node || !node.expandable || node._expanded) return;

                 let expansionResult;
                 if (node.type === "DatasetCollection") {
                     expansionResult = expandDatasetCollectionNodeInternal(node, nodes, edges, entityMap);
                 } else {
                     expansionResult = expandNodeInternal(node, nodes, edges, entityMap);
                 }
                 const { newNodes, newEdges, updatedCollectionData } = expansionResult;

                if (newNodes.length > 0 || newEdges.length > 0 || updatedCollectionData) {

                     let updatedNode = {...node};
                     if (updatedCollectionData) {
                         updatedNode = {...updatedNode, ...updatedCollectionData};
                     } else {
                         updatedNode._expanded = true;
                         updatedNode.expandable = false;
                     }
                     nodes[nodeIndex] = updatedNode;


                     expansionResult.newNodes.forEach(newNode => {
                        if (!addedNodeIds.has(newNode.id)) {
                            nodes.push(newNode);
                            addedNodeIds.add(newNode.id);
                            if (newNode.expandable) {
                                nextLevelIds.add(newNode.id);
                            }
                        }
                    });
                    expansionResult.newEdges.forEach(newEdge => {
                        if (!edges.some(e => e.id === newEdge.id)) {
                            edges.push(newEdge);
                        }
                    });
                 } else {
                    nodes[nodeIndex] = {...node, expandable: false};
                 }
            });
            currentLevelIds = nextLevelIds;
        }

        nodes.forEach((node, index) => {
             if (!node._expanded) {
                 const checkAgain = createEvidenceNode(node._sourceData);
                 let stillExpandable = checkAgain ? checkAgain.expandable : false;
                 if (node.type === 'DatasetCollection') {
                    stillExpandable = node._remainingDatasets && node._remainingDatasets.length > 0;
                 }
                 if (nodes[index].expandable !== stillExpandable) {
                     nodes[index] = {...node, expandable: stillExpandable};
                 }
             }
        });


        return { nodes, edges };
    }

    function expandNodeInternal(node, currentNodes, currentEdges, entityMap) {
        const nodeId = node.id;
        const nodeType = node.type;
        const sourceData = node._sourceData;
        const result = { newNodes: [], newEdges: [] };

        const nodeExists = (id) => currentNodes.some(n => n.id === id) || result.newNodes.some(n => n.id === id);
        const addNodeAndEdge = (targetEntityRef, relationshipLabel, relationshipType) => {
            if (!targetEntityRef) return;

            let targetEntityData = null;
            let targetId = null;

            if (typeof targetEntityRef === 'string') {
                targetId = targetEntityRef;
                targetEntityData = entityMap.get(targetId);
            } else if (typeof targetEntityRef === 'object' && targetEntityRef['@id']) {
                targetId = targetEntityRef['@id'];
                targetEntityData = entityMap.has(targetId) ? { ...entityMap.get(targetId), ...targetEntityRef } : targetEntityRef;
            }

            if (!targetId) {
                 console.warn(`Invalid target entity reference for ${relationshipType}:`, targetEntityRef);
                 return;
            }

             if (!targetEntityData && entityMap.has(targetId)) {
                 targetEntityData = entityMap.get(targetId);
             }

            if (!targetEntityData) {
                console.warn(`Could not find entity data for ID: ${targetId} (relation: ${relationshipType} from ${nodeId})`);
                 return;
            }

            const targetNode = createEvidenceNode(targetEntityData);
            if (targetNode) {
                if (!nodeExists(targetNode.id)) {
                    result.newNodes.push(targetNode);
                }
                 const edgeId = `${nodeId}_${relationshipType}_${targetNode.id}`.replace(/[^a-zA-Z0-9_]/g, '-');
                 const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                 if (!edgeExists) {
                    result.newEdges.push({
                        id: edgeId,
                        source: nodeId,
                        target: targetNode.id,
                        label: relationshipLabel,
                        animated: false
                    });
                }
            }
        };

        if (nodeType === "Dataset" && sourceData.generatedBy) {
            addNodeAndEdge(sourceData.generatedBy, "generated by", "generatedBy");
        }

        if (nodeType === "DatasetGroup" && sourceData["evi:representativeDataset"]) {
            // Show the representative member; downstream `generatedBy` expansion will
            // continue the chain (representative.generatedBy → Experiment → Sample/Instrument).
            // The other 858+ members are intentionally collapsed: they share the same
            // provenance shape, that's why the builder grouped them in the first place.
            addNodeAndEdge(sourceData["evi:representativeDataset"], "representative member", "representativeMember");
        }

        if ((nodeType === "Computation" || nodeType === "Experiment")) {
             const relations = [
                { prop: 'usedSoftware', label: 'used software', type: 'uses_sw' },
                { prop: 'usedDataset', label: 'used dataset', type: 'uses_ds' },
                { prop: 'usedSample', label: 'used sample', type: 'uses_sample' },
                { prop: 'usedInstrument', label: 'used instrument', type: 'uses_instrument' }
             ];

             relations.forEach(rel => {
                 const items = sourceData[rel.prop];
                 if (items) {
                    const itemList = Array.isArray(items) ? items : [items];

                    if (rel.prop === 'usedDataset' && itemList.length > 1) {
                         const validDatasetRefs = itemList.filter(ds => ds && (typeof ds === "string" || (typeof ds === "object" && ds["@id"])));
                         if (validDatasetRefs.length > 1) {
                            const collectionNode = createDatasetCollectionNode(nodeId, validDatasetRefs);
                             if (collectionNode) {
                                if (!nodeExists(collectionNode.id)) {
                                    result.newNodes.push(collectionNode);
                                }
                                const edgeId = `${nodeId}_${rel.type}_coll_${collectionNode.id}`.replace(/[^a-zA-Z0-9_]/g, '-');
                                const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                                if (!edgeExists) {
                                    result.newEdges.push({ id: edgeId, source: nodeId, target: collectionNode.id, label: rel.label, animated: false });
                                }
                            }
                            return;
                         }
                     }

                    itemList.forEach(itemRef => {
                         addNodeAndEdge(itemRef, rel.label, rel.type);
                    });
                 }
             });
        }

        return result;
    }

    function expandDatasetCollectionNodeInternal(collectionNode, currentNodes, currentEdges, entityMap) {
        const nodeId = collectionNode.id;
        const result = { newNodes: [], newEdges: [], updatedCollectionData: null };
        const originalData = collectionNode;
        const remaining = originalData._remainingDatasets;

        if (!remaining || remaining.length === 0) {
            return { ...result, updatedCollectionData: { expandable: false, label: `Input Datasets (All Shown)`, displayName: `Datasets (All)` } };
        }

        const datasetToExpandRef = remaining[0];
        let datasetNode = null;

        const nodeExists = (id) => currentNodes.some(n => n.id === id) || result.newNodes.some(n => n.id === id);

        let datasetEntityData = null;
        let datasetId = null;
        if (typeof datasetToExpandRef === 'string') {
            datasetId = datasetToExpandRef;
            datasetEntityData = entityMap.get(datasetId);
        } else if (typeof datasetToExpandRef === 'object' && datasetToExpandRef['@id']) {
            datasetId = datasetToExpandRef['@id'];
            datasetEntityData = entityMap.has(datasetId) ? { ...entityMap.get(datasetId), ...datasetToExpandRef } : datasetToExpandRef;
        }

         if (datasetId && datasetEntityData) {
            datasetNode = createEvidenceNode(datasetEntityData);
            if (datasetNode) {
                if (!nodeExists(datasetNode.id)) {
                    result.newNodes.push(datasetNode);
                }
                 const edgeId = `${nodeId}_contains_${datasetNode.id}_${originalData._expandedCount || 0}`.replace(/[^a-zA-Z0-9_]/g, '-');
                 const edgeExists = currentEdges.some(e => e.id === edgeId) || result.newEdges.some(e => e.id === edgeId);
                 if (!edgeExists) {
                    result.newEdges.push({ id: edgeId, source: nodeId, target: datasetNode.id, label: "contains", animated: false });
                }
            } else {
                 console.warn("Failed to create node for dataset in collection:", datasetEntityData);
            }
         } else {
             console.warn(`Could not find entity data for dataset ID in collection: ${datasetId || JSON.stringify(datasetToExpandRef)}`);
         }

        const nextRemaining = remaining.slice(1);
        const nextExpandedCount = (originalData._expandedCount || 0) + 1;
        const nextExpandable = nextRemaining.length > 0;
        const nextLabel = nextExpandable ? `Input Datasets (${nextRemaining.length} more)` : `Input Datasets (All Shown)`;
        const nextDisplayName = nextExpandable ? `Datasets (${nextRemaining.length})` : `Datasets (All)`;

        result.updatedCollectionData = {
            _remainingDatasets: nextRemaining,
            _expandedCount: nextExpandedCount,
            expandable: nextExpandable,
            label: nextLabel,
            displayName: nextDisplayName
        };

        return result;
    }


    function getLayoutedElements(nodes, edges, direction = "LR") {
        if (!nodes || nodes.length === 0) {
            console.log("Layout skipped: No nodes provided.");
            return { nodes, edges, width: 0, height: 0 };
        }
        const dagreGraph = new dagre.graphlib.Graph();
        dagreGraph.setDefaultEdgeLabel(() => ({}));

        const NODE_SEP = 50;
        const RANK_SEP = 80;
        const MARGIN_X = 50;
        const MARGIN_Y = 50;

        dagreGraph.setGraph({
            rankdir: direction,
            nodesep: NODE_SEP,
            ranksep: RANK_SEP,
            marginx: MARGIN_X,
            marginy: MARGIN_Y,
            align: 'DL'
        });

        nodes.forEach(node => {
            dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT, label: node.displayName });
        });

        edges.forEach(edge => {
             if (nodes.some(n => n.id === edge.source) && nodes.some(n => n.id === edge.target)) {
                dagreGraph.setEdge(edge.source, edge.target);
            } else {
                console.warn("Skipping edge due to missing node:", edge.id, edge.source, edge.target);
            }
        });

        try {
            dagre.layout(dagreGraph);
        } catch (e) {
            console.error("Dagre layout calculation failed:", e);
            const layoutedNodes = nodes.map(node => ({ ...node, x: node.x || Math.random()*500, y: node.y || Math.random()*500 }));
            return { nodes: layoutedNodes, edges, width: 800, height: 600 };
        }

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

        const layoutedNodes = nodes.map(node => {
            const nodeWithPosition = dagreGraph.node(node.id);
            if (nodeWithPosition) {
                const x = nodeWithPosition.x - NODE_WIDTH / 2;
                const y = nodeWithPosition.y - NODE_HEIGHT / 2;

                 minX = Math.min(minX, x);
                 maxX = Math.max(maxX, x + NODE_WIDTH);
                 minY = Math.min(minY, y);
                 maxY = Math.max(maxY, y + NODE_HEIGHT);

                return { ...node, x: x, y: y, width: NODE_WIDTH, height: NODE_HEIGHT };
            } else {
                console.warn(`Node ${node.id} not found in Dagre layout results. Keeping previous position or placing randomly.`);
                const x = node.x || Math.random() * 500;
                const y = node.y || Math.random() * 500;
                 minX = Math.min(minX, x);
                 maxX = Math.max(maxX, x + NODE_WIDTH);
                 minY = Math.min(minY, y);
                 maxY = Math.max(maxY, y + NODE_HEIGHT);
                return { ...node, x: x, y: y, width: NODE_WIDTH, height: NODE_HEIGHT };
            }
        });

        const graphWidth = Math.max(1500, maxX - minX + 2 * MARGIN_X);
        const graphHeight = Math.max(1000, maxY - minY + 2 * MARGIN_Y);

         const offsetX = MARGIN_X - minX;
         const offsetY = MARGIN_Y - minY;
         const adjustedNodes = layoutedNodes.map(n => ({...n, x: n.x + offsetX, y: n.y + offsetY }));

        return { nodes: adjustedNodes, edges, width: graphWidth, height: graphHeight };
    }

    function getNodeColor(type) {
        switch (type) {
            case "Dataset": case "Sample": return "#8AE68A";
            case "Computation": case "Experiment": return "#FD9A9A";
            case "Software": case "Instrument": return "#FFC107";
            case "DatasetCollection": case "DatasetGroup": return "#B5DEFF";
            default: return "#E0E0E0";
        }
    }

    const { createElement, useState, useCallback, useEffect, useRef, memo } = React;

    const EvidenceNode = memo(({ nodeData, onClick }) => {
        const { id, type, label, displayName, description, expandable, x, y, width, height } = nodeData;
        const nodeColor = getNodeColor(type);
        // DatasetGroup (graph-condensation node) and DatasetCollection (synthetic UI grouping
        // node) are the same idea to a reader, so show one unified label for both.
        const displayType = (type === "DatasetCollection" || type === "DatasetGroup")
            ? "Dataset Group" : type;
        const tooltip = [label, `Type: ${displayType}`, `ID: ${id}`, description].filter(Boolean).join('\n');

        const handleClick = useCallback((event) => {
            event.stopPropagation();
            if (expandable && onClick) {
                onClick(id);
            }
        }, [id, expandable, onClick]);

        const style = {
            left: `${x}px`,
            top: `${y}px`,
            width: `${width}px`,
            height: `${height}px`,
        };

        const containerClasses = ['node-container'];
        if (expandable) {
            containerClasses.push('expandable');
        }

        return createElement(
            'div',
            { style: style, className: 'node-wrapper', title: tooltip, onClick: handleClick, onMouseDown: (e) => e.stopPropagation() },
            createElement('div', { className: containerClasses.join(' ') }, [
                createElement('div', { key: 'header', className: 'node-header', style: { backgroundColor: nodeColor } }, displayType),
                createElement('div', { key: 'content', className: 'node-content' },
                     createElement('div', { style: { width: '100%', textAlign: 'center' } }, displayName)
                )
            ])
        );
    });

    const Edge = memo(({ edgeData, sourceNode, targetNode }) => {
        if (!sourceNode || !targetNode || sourceNode.x === undefined || targetNode.x === undefined) {
             return null;
        }

        const sourceX = sourceNode.x + sourceNode.width;
        const sourceY = sourceNode.y + sourceNode.height / 2;
        const targetX = targetNode.x;
        const targetY = targetNode.y + targetNode.height / 2;

        const dx = targetX - sourceX;
        const dy = targetY - sourceY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let pathD;
        if (dist < 100) {
            pathD = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`;
        } else {
            const midX = (sourceX + targetX) / 2;
            const midY = (sourceY + targetY) / 2;
            const c1X = sourceX + dx * 0.3;
            const c1Y = sourceY;
            const c2X = targetX - dx * 0.3;
            const c2Y = targetY;
            pathD = `M ${sourceX} ${sourceY} C ${c1X},${c1Y} ${c2X},${c2Y} ${targetX},${targetY}`;
        }


        const labelX = (sourceX + targetX) / 2;
        const labelY = (sourceY + targetY) / 2;

        return createElement(
            'g',
            { key: edgeData.id },
            [
                createElement('path', {
                    className: 'edge-path',
                    d: pathD,
                    markerEnd: 'url(#arrowhead)'
                }),
                 createElement('rect', {
                     key: `${edgeData.id}-bg`,
                     className: 'edge-label-bg',
                     x: labelX - 25,
                     y: labelY - 8,
                     width: 50,
                     height: 16,
                     rx: 3,
                 }),
                createElement('text', {
                    key: `${edgeData.id}-text`,
                    className: 'edge-label-text',
                    x: labelX,
                    y: labelY,
                    dy: "0.em"
                }, edgeData.label || '')
            ]
        );
    });


    const GraphRenderer = ({ graphData }) => {
        const [nodes, setNodes] = useState([]);
        const [edges, setEdges] = useState([]);
        const [isLoading, setIsLoading] = useState(true);
        const [graphWidth, setGraphWidth] = useState(1500);
        const [graphHeight, setGraphHeight] = useState(1000);
        const entityMapRef = useRef(new Map());
        const [scale, setScale] = useState(1);
        const [translate, setTranslate] = useState({ x: 0, y: 0 });
        const [isDragging, setIsDragging] = useState(false);
        const [startDragPos, setStartDragPos] = useState({ x: 0, y: 0 });
        const rootRef = useRef(null);


        const applyLayout = useCallback((nodesToLayout, edgesToLayout) => {
            setIsLoading(true);
            setTimeout(() => {
                try {
                    const nodesWithDims = nodesToLayout.map(n => ({ ...n, width: NODE_WIDTH, height: NODE_HEIGHT }));
                    const { nodes: layoutedNodes, edges: finalEdges, width, height } = getLayoutedElements(nodesWithDims, edgesToLayout, "LR");
                    setNodes(layoutedNodes);
                    setEdges(finalEdges);
                    setGraphWidth(width);
                    setGraphHeight(height);
                } catch (error) {
                    console.error("Layout application failed:", error);
                    setNodes(nodesToLayout);
                    setEdges(edgesToLayout);
                } finally {
                    setIsLoading(false);
                }
            }, 10);
        }, []);

        useEffect(() => {
            if (!graphData) {
                setIsLoading(false);
                return;
            }
             const { rootEntityId, entityMap } = getGraphEntities(graphData);
             if (!rootEntityId) {
                 console.error("No root entity found on initial load.");
                 setIsLoading(false);
                 return;
             }
             entityMapRef.current = entityMap;

             // Initial expansion depth is now handled by the default parameter in getInitialGraphState
             const { nodes: initialNodes, edges: initialEdges } = getInitialGraphState(graphData);

             if (initialNodes.length > 0) {
                applyLayout(initialNodes, initialEdges);
             } else {
                setNodes([]);
                setEdges([]);
                setIsLoading(false);
             }

        }, [graphData, applyLayout]);


        const handleNodeClick = useCallback((nodeId) => {
            const clickedNodeIndex = nodes.findIndex(n => n.id === nodeId);
            if (clickedNodeIndex === -1) return;

            const clickedNode = nodes[clickedNodeIndex];
            if (!clickedNode.expandable) return;

            setIsLoading(true);

            let expansionResult;
            if (clickedNode.type === "DatasetCollection") {
                expansionResult = expandDatasetCollectionNodeInternal(clickedNode, nodes, edges, entityMapRef.current);
            } else {
                expansionResult = expandNodeInternal(clickedNode, nodes, edges, entityMapRef.current);
            }

            const { newNodes, newEdges, updatedCollectionData } = expansionResult;

            let nextNodes = [...nodes];
            let nodeUpdated = false;

             const originalNode = nextNodes[clickedNodeIndex];
             let updatedNodeData = { ...originalNode };

             if (updatedCollectionData) {
                 updatedNodeData = { ...updatedNodeData, ...updatedCollectionData };
                 nodeUpdated = true;
             } else if (newNodes.length > 0 || newEdges.length > 0) {
                updatedNodeData._expanded = true;
                updatedNodeData.expandable = false;
                nodeUpdated = true;
             } else {
                updatedNodeData.expandable = false;
                nodeUpdated = true;
             }

             if (nodeUpdated) {
                nextNodes[clickedNodeIndex] = updatedNodeData;
             }

            const nodesToAdd = newNodes.filter(newNode => !nextNodes.some(existingNode => existingNode.id === newNode.id));
            nextNodes = [...nextNodes, ...nodesToAdd];

            const combinedEdges = [...edges];
            newEdges.forEach(newEdge => {
                if (!combinedEdges.some(existingEdge => existingEdge.id === newEdge.id)) {
                    combinedEdges.push(newEdge);
                }
            });

             applyLayout(nextNodes, combinedEdges);

        }, [nodes, edges, applyLayout]);


        const nodeMap = new Map(nodes.map(node => [node.id, node]));

        const zoomIn = useCallback(() => setScale(s => Math.min(s * 1.2, 3)), []);
        const zoomOut = useCallback(() => setScale(s => Math.max(s / 1.2, 0.2)), []);
        const resetView = useCallback(() => {
            setScale(1);
            setTranslate({ x: 0, y: 0 });
        }, []);

        const handleMouseDown = useCallback((event) => {
            if (event.button !== 0) return;
             if (event.target.closest('.controls-container') || event.target.closest('.node-wrapper')) {
                 return;
             }
            setIsDragging(true);
            setStartDragPos({ x: event.clientX - translate.x, y: event.clientY - translate.y });
            if(rootRef.current) rootRef.current.classList.add('dragging');
            event.preventDefault();
        }, [translate.x, translate.y]);

        const handleMouseMove = useCallback((event) => {
            if (!isDragging) return;
            const newX = event.clientX - startDragPos.x;
            const newY = event.clientY - startDragPos.y;
            setTranslate({ x: newX, y: newY });
        }, [isDragging, startDragPos]);

        const handleMouseUp = useCallback(() => {
            if (!isDragging) return;
            setIsDragging(false);
             if(rootRef.current) rootRef.current.classList.remove('dragging');
        }, [isDragging]);

         const handleMouseLeave = useCallback(() => {
            if (isDragging) {
                setIsDragging(false);
                if(rootRef.current) rootRef.current.classList.remove('dragging');
            }
        }, [isDragging]);


        useEffect(() => {
            const currentRoot = rootRef.current;
            if (currentRoot) {
                 currentRoot.addEventListener('mousedown', handleMouseDown);
                 currentRoot.addEventListener('mousemove', handleMouseMove);
                 currentRoot.addEventListener('mouseup', handleMouseUp);
                 currentRoot.addEventListener('mouseleave', handleMouseLeave);

                 return () => {
                     currentRoot.removeEventListener('mousedown', handleMouseDown);
                     currentRoot.removeEventListener('mousemove', handleMouseMove);
                     currentRoot.removeEventListener('mouseup', handleMouseUp);
                     currentRoot.removeEventListener('mouseleave', handleMouseLeave);
                 };
            }
        }, [handleMouseDown, handleMouseMove, handleMouseUp, handleMouseLeave]);


        return React.createElement(
            'div',
            { ref: rootRef, style:{ width: '100%', height: '100%', overflow: 'hidden', position: 'relative'} },
            [
                createElement('div', {
                    key: 'viewport',
                    className: 'graph-viewport',
                    style: {
                        transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
                    }
                 },
                    createElement(
                        'div',
                        { className: 'graph-container', style: { width: `${graphWidth}px`, height: `${graphHeight}px` } },
                        [
                            createElement('svg', { key: 'svg-layer', className: 'svg-layer', width: graphWidth, height: graphHeight }, [
                                createElement('defs', {key: 'defs'},
                                    createElement('marker', {
                                        id: 'arrowhead',
                                        viewBox: '0 -5 10 10',
                                        refX: 8,
                                        refY: 0,
                                        markerWidth: 6,
                                        markerHeight: 6,
                                        orient: 'auto'
                                    }, createElement('path', { d: 'M0,-5L10,0L0,5', fill: '#888' }))
                                ),
                                createElement('g', { key: 'edges-group' },
                                    edges.map(edge => createElement(Edge, {
                                        key: edge.id,
                                        edgeData: edge,
                                        sourceNode: nodeMap.get(edge.source),
                                        targetNode: nodeMap.get(edge.target)
                                    }))
                                )
                            ]),

                            createElement('div', { key: 'nodes-layer', style: { position: 'relative', width: '100%', height: '100%' } },
                                nodes.map(node => createElement(EvidenceNode, {
                                    key: node.id,
                                    nodeData: node,
                                    onClick: handleNodeClick
                                }))
                            )
                        ]
                    )
                ),
                 isLoading && createElement('div', { key: 'loading', className: 'loading-overlay' }, 'Loading...'),

                 createElement('div', {key: 'controls', className: 'controls-container'}, [
                    createElement('button', { key: 'zoom-in', className: 'control-button', onClick: zoomIn }, '+'),
                    createElement('button', { key: 'zoom-out', className: 'control-button', onClick: zoomOut }, '-'),
                    createElement('button', { key: 'reset-view', className: 'control-button', onClick: resetView }, 'Reset')
                 ])
            ]
        );
    };

    const App = () => {
        return React.createElement(GraphRenderer, { graphData: evidenceGraphData });
    };

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(App));

