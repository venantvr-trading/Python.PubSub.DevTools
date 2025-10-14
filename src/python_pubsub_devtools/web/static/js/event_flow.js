// Event Flow Visualization with React Flow
// Uses React.createElement (no JSX compilation needed)

const { useState, useCallback, useEffect } = React;
const ReactFlow = window.ReactFlow.default;
const { Controls, Background, useNodesState, useEdgesState, addEdge, MarkerType } = window.ReactFlow;

let currentRoot = null; // Keep track of current React root

// Custom Node Components
const EventNode = ({ data }) => {
    return React.createElement('div', {
        style: {
            background: '#A7C7E7',
            padding: '12px',
            borderRadius: '50%',
            border: '2px solid #5a7d9e',
            fontSize: '11px',
            textAlign: 'center',
            minWidth: '60px',
            maxWidth: '120px',
            wordWrap: 'break-word',
            color: '#000'
        }
    }, data.label);
};

const AgentNode = ({ data }) => {
    return React.createElement('div', {
        style: {
            background: '#FDFD96',
            padding: '10px 15px',
            borderRadius: '5px',
            border: '2px solid #c5c56d',
            fontSize: '11px',
            textAlign: 'center',
            minWidth: '80px',
            color: '#000'
        }
    }, data.label);
};

const nodeTypes = {
    event: EventNode,
    agent: AgentNode
};

// Main React Component for Event Flow Visualization
function EventFlowDiagram({ graphType, isEditable }) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Load graph data from API
    useEffect(() => {
        setIsLoading(true);
        fetch(`/api/graph-data/${graphType}`)
            .then(res => res.json())
            .then(data => {
                // Separate events and agents
                const events = data.nodes.filter(n => n.type === 'event');
                const agents = data.nodes.filter(n => n.type === 'agent');

                // Position nodes in a better layout: events on left, agents on right
                const eventsCols = 8;
                const agentsCols = 6;
                const xSpacing = 180;
                const ySpacing = 100;
                const agentsXOffset = eventsCols * xSpacing + 200; // Space between columns

                const eventsWithPosition = events.map((node, i) => ({
                    ...node,
                    position: {
                        x: (i % eventsCols) * xSpacing,
                        y: Math.floor(i / eventsCols) * ySpacing
                    }
                }));

                const agentsWithPosition = agents.map((node, i) => ({
                    ...node,
                    position: {
                        x: agentsXOffset + (i % agentsCols) * xSpacing,
                        y: Math.floor(i / agentsCols) * ySpacing
                    }
                }));

                const nodesWithPosition = [...eventsWithPosition, ...agentsWithPosition];

                // Create a set of valid node IDs for validation
                const nodeIds = new Set(nodesWithPosition.map(n => n.id));

                // Add marker to edges with better visibility and ensure ID field
                const edgesWithMarkers = data.edges
                    .map((edge, index) => {
                        const isPublication = edge.type === 'publication';
                        const color = isPublication ? '#4CAF50' : '#2196F3';

                        // Ensure edge has an ID (required by React Flow)
                        const edgeId = edge.id || `edge-${edge.source}-${edge.target}-${index}`;

                        return {
                            ...edge,
                            id: edgeId,
                            source: String(edge.source),
                            target: String(edge.target),
                            animated: isPublication,
                            markerEnd: {
                                type: MarkerType.ArrowClosed,
                                width: 25,
                                height: 25,
                                color: color
                            },
                            style: {
                                strokeWidth: 2.5,
                                stroke: color
                            },
                            label: edge.type === 'publication' ? '▶' : '→',
                            labelStyle: { fill: color, fontWeight: 700 },
                            labelBgStyle: { fill: 'transparent' }
                        };
                    })
                    .filter(edge => {
                        // Validate edge references existing nodes
                        const sourceExists = nodeIds.has(edge.source);
                        const targetExists = nodeIds.has(edge.target);

                        if (!sourceExists) {
                            console.warn(`⚠️ Edge ${edge.id} has invalid source: ${edge.source}`);
                        }
                        if (!targetExists) {
                            console.warn(`⚠️ Edge ${edge.id} has invalid target: ${edge.target}`);
                        }

                        return sourceExists && targetExists;
                    });

                console.log('📊 Loaded graph data:', {
                    totalNodes: nodesWithPosition.length,
                    eventNodes: eventsWithPosition.length,
                    agentNodes: agentsWithPosition.length,
                    totalEdges: edgesWithMarkers.length,
                    rawEdges: data.edges.length,
                    sampleNode: nodesWithPosition[0],
                    sampleEdge: edgesWithMarkers[0],
                    allNodeIds: Array.from(nodeIds).slice(0, 10),
                    firstFiveEdges: edgesWithMarkers.slice(0, 5).map(e => ({
                        id: e.id,
                        source: e.source,
                        target: e.target,
                        type: e.type
                    }))
                });

                setNodes(nodesWithPosition);
                setEdges(edgesWithMarkers);
                setIsLoading(false);
            })
            .catch(err => {
                console.error('❌ Error loading graph data:', err);
                setIsLoading(false);
            });
    }, [graphType]);

    // Handle new connections (only in editable mode)
    const onConnect = useCallback((params) => {
        if (!isEditable) return;

        setEdges((eds) => addEdge({
            ...params,
            markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 20,
                height: 20,
                color: '#4CAF50'
            },
            style: {
                strokeWidth: 2,
                stroke: '#4CAF50'
            },
            animated: true
        }, eds));

        generatePromptForChange({ ...params, type: 'add' });
    }, [isEditable, nodes]);

    // Handle edge deletion (only in editable mode)
    const onEdgesDelete = useCallback((edgesToDelete) => {
        if (!isEditable) return;
        edgesToDelete.forEach(edge => generatePromptForChange({ ...edge, type: 'remove' }));
    }, [isEditable, nodes]);

    // Generate prompt for graph modifications
    const generatePromptForChange = async (change) => {
        const promptDisplay = document.getElementById('prompt-display');
        if (!promptDisplay) return;

        const sourceNode = nodes.find(n => n.id === change.source);
        const targetNode = nodes.find(n => n.id === change.target);

        if (!sourceNode || !targetNode) return;

        let payload;

        if (sourceNode.type === 'event') {
            // Event -> Agent (subscription)
            payload = {
                action: change.type === 'add' ? "add_subscription" : "remove_subscription",
                event: change.source,
                agent: change.target
            };
        } else {
            // Agent -> Event (publication) - not supported yet
            promptDisplay.textContent = "Modification des publications non supportée pour le moment.";
            return;
        }

        promptDisplay.textContent = 'Génération du prompt...';

        try {
            const response = await fetch('/api/generate-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            promptDisplay.textContent = data.prompt;
        } catch (err) {
            promptDisplay.textContent = `Erreur lors de la génération du prompt: ${err.message}`;
        }
    };

    if (isLoading) {
        return React.createElement('div', {
            style: {
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                fontSize: '18px',
                color: '#666'
            }
        }, 'Chargement du graphe...');
    }

    // Debug: log current state
    console.log('🔍 ReactFlow render:', {
        nodesCount: nodes.length,
        edgesCount: edges.length,
        firstNode: nodes[0]?.id,
        firstEdge: edges[0]
    });

    return React.createElement(ReactFlow, {
        nodes: nodes,
        edges: edges,
        onNodesChange: onNodesChange,
        onEdgesChange: onEdgesChange,
        onConnect: onConnect,
        onEdgesDelete: onEdgesDelete,
        nodeTypes: nodeTypes,
        fitView: true,
        nodesDraggable: true,
        nodesConnectable: isEditable,
        elementsSelectable: isEditable,
        edgesUpdatable: isEditable,
        edgesFocusable: isEditable,
        defaultEdgeOptions: {
            type: 'default',
            markerEnd: { type: MarkerType.ArrowClosed }
        },
        connectionLineStyle: { stroke: '#4CAF50', strokeWidth: 2 },
        minZoom: 0.1,
        maxZoom: 2,
        style: { width: '100%', height: '100%' }
    }, [
        React.createElement(Controls, { key: 'controls' }),
        React.createElement(Background, { key: 'background', color: '#aaa', gap: 16 })
    ]);
}

// Global function to render the flow diagram
function renderFlow(tabId, isEditable) {
    // Manage tab state
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');

    // Find and activate the corresponding tab button
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach((tab, index) => {
        const tabTypes = ['simplified', 'complete', 'ia-editor'];
        if (tabTypes[index] === tabId) {
            tab.classList.add('active');
        }
    });

    const containerId = `flow-${tabId}`;
    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    // Destroy previous root if it exists
    if (currentRoot) {
        currentRoot.unmount();
    }

    // Create new root and render
    currentRoot = ReactDOM.createRoot(container);
    currentRoot.render(
        React.createElement(EventFlowDiagram, {
            graphType: tabId,
            isEditable: isEditable
        })
    );
}

// Copy prompt to clipboard
function copyPrompt() {
    const promptText = document.getElementById('prompt-display').textContent;
    navigator.clipboard.writeText(promptText).then(() => {
        alert('Prompt copié dans le presse-papiers !');
    }).catch(err => {
        console.error('Erreur lors de la copie:', err);
        alert('Erreur lors de la copie du prompt');
    });
}

// Filter functions (keep existing functionality)
function toggleFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const overlay = document.getElementById('filters-overlay');
    const isActive = sidebar.classList.contains('active');

    if (isActive) {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    } else {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    }
}

function selectAllNamespaces() {
    document.querySelectorAll('#namespace-filters input[type="checkbox"]').forEach(cb => {
        cb.checked = true;
    });
}

function deselectAllNamespaces() {
    document.querySelectorAll('#namespace-filters input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'F' || e.key === 'f') {
        toggleFilters();
    } else if (e.key === 'D' || e.key === 'd') {
        toggleDarkMode();
    } else if (e.ctrlKey && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Render the first tab by default
    const firstTab = document.querySelector('.tab');
    if (firstTab) {
        renderFlow('simplified', false);
    }
});
