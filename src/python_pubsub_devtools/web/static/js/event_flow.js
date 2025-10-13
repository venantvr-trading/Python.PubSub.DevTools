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
                // Position nodes in a grid layout
                const nodesWithPosition = data.nodes.map((node, i) => {
                    const cols = 6;
                    const xSpacing = 200;
                    const ySpacing = 150;
                    return {
                        ...node,
                        position: {
                            x: (i % cols) * xSpacing,
                            y: Math.floor(i / cols) * ySpacing
                        }
                    };
                });

                // Add marker to edges
                const edgesWithMarkers = data.edges.map(edge => ({
                    ...edge,
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        width: 20,
                        height: 20,
                        color: edge.animated ? '#4CAF50' : '#999'
                    },
                    style: {
                        strokeWidth: 2,
                        stroke: edge.animated ? '#4CAF50' : '#999'
                    }
                }));

                setNodes(nodesWithPosition);
                setEdges(edgesWithMarkers);
                setIsLoading(false);
            })
            .catch(err => {
                console.error('Error loading graph data:', err);
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

    return React.createElement(ReactFlow, {
        nodes: nodes,
        edges: edges,
        onNodesChange: onNodesChange,
        onEdgesChange: onEdgesChange,
        onConnect: onConnect,
        onEdgesDelete: onEdgesDelete,
        nodeTypes: nodeTypes,
        fitView: true,
        nodesDraggable: true, // Always draggable for better UX
        nodesConnectable: isEditable,
        elementsSelectable: isEditable,
        minZoom: 0.1,
        maxZoom: 2
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
