/**
 * ExpertLens Graph Module
 * Cytoscape.js integration for expert-company graph visualization
 */

// Graph configuration
const GraphConfig = {
    // Node colors
    colors: {
        expert: '#4A90D9',
        company: '#7B68EE',
        edge: '#95a5a6'
    },
    // Node sizing
    sizing: {
        expertBase: 30,
        expertScale: 5,  // Additional size per evidence
        expertMax: 60,
        companySize: 35
    },
    // Layout options
    layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        gravity: 0.25,
        numIter: 1000,
        padding: 50
    }
};

// Cytoscape style definitions
const cytoscapeStyle = [
    // Expert nodes (circle)
    {
        selector: 'node[type="expert"]',
        style: {
            'background-color': GraphConfig.colors.expert,
            'label': 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'font-size': '12px',
            'color': '#2c3e50',
            'text-wrap': 'wrap',
            'text-max-width': '80px',
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': 2,
            'border-color': '#fff'
        }
    },
    // Company nodes (rectangle)
    {
        selector: 'node[type="company"]',
        style: {
            'background-color': GraphConfig.colors.company,
            'shape': 'rectangle',
            'label': 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'font-size': '12px',
            'color': '#2c3e50',
            'text-wrap': 'wrap',
            'text-max-width': '80px',
            'width': GraphConfig.sizing.companySize,
            'height': GraphConfig.sizing.companySize,
            'border-width': 2,
            'border-color': '#fff'
        }
    },
    // Selected node
    {
        selector: 'node:selected',
        style: {
            'border-width': 4,
            'border-color': '#e74c3c'
        }
    },
    // Edges
    {
        selector: 'edge',
        style: {
            'width': 2,
            'line-color': GraphConfig.colors.edge,
            'curve-style': 'bezier',
            'target-arrow-shape': 'none',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
            'color': '#7f8c8d'
        }
    },
    // Edge on hover
    {
        selector: 'edge:selected',
        style: {
            'width': 3,
            'line-color': '#3498db'
        }
    }
];

/**
 * Convert session JSON to Cytoscape elements
 * @param {Object} session - Session JSON object
 * @returns {Object} Cytoscape elements { nodes, edges }
 */
function sessionToElements(session) {
    const nodes = [];
    const edges = [];
    const companySet = new Set();

    // Create expert nodes
    if (session.experts) {
        session.experts.forEach(expert => {
            const evidenceCount = expert.evidence_ids ? expert.evidence_ids.length : 0;
            const size = Math.min(
                GraphConfig.sizing.expertBase + (evidenceCount * GraphConfig.sizing.expertScale),
                GraphConfig.sizing.expertMax
            );

            nodes.push({
                data: {
                    id: `expert-${expert.expert_id}`,
                    label: expert.canonical_name,
                    type: 'expert',
                    evidenceCount: evidenceCount,
                    size: size,
                    expertData: expert
                }
            });

            // Process employment claims to create edges
            if (expert.claims) {
                expert.claims.forEach(claim => {
                    if (claim.claim_type === 'employment' && claim.company_id) {
                        companySet.add(claim.company_id);

                        edges.push({
                            data: {
                                id: `edge-${expert.expert_id}-${claim.company_id}`,
                                source: `expert-${expert.expert_id}`,
                                target: `company-${claim.company_id}`,
                                label: claim.role || ''
                            }
                        });
                    }
                });
            }
        });
    }

    // Create company nodes
    if (session.companies) {
        session.companies.forEach(company => {
            // Only add companies that have connections
            if (companySet.has(company.company_id)) {
                nodes.push({
                    data: {
                        id: `company-${company.company_id}`,
                        label: company.name,
                        type: 'company',
                        companyData: company
                    }
                });
            }
        });
    }

    return { nodes, edges };
}

/**
 * Initialize Cytoscape graph
 * @param {string} containerId - DOM container ID
 * @returns {Object} Cytoscape instance
 */
function initGraph(containerId) {
    const cy = cytoscape({
        container: document.getElementById(containerId),
        style: cytoscapeStyle,
        elements: [],
        minZoom: 0.3,
        maxZoom: 3,
        wheelSensitivity: 0.3
    });

    // Enable box selection
    cy.boxSelectionEnabled(true);

    return cy;
}

/**
 * Load session data into graph
 * @param {Object} cy - Cytoscape instance
 * @param {Object} session - Session JSON object
 */
function loadSessionToGraph(cy, session) {
    // Clear existing elements
    cy.elements().remove();

    // Convert and add new elements
    const elements = sessionToElements(session);
    cy.add(elements.nodes);
    cy.add(elements.edges);

    // Apply layout
    const layout = cy.layout(GraphConfig.layout);
    layout.run();

    // Fit to viewport after layout
    layout.on('layoutstop', () => {
        cy.fit(50);
    });
}

/**
 * Get evidence for an expert
 * @param {Object} session - Session JSON object
 * @param {Array} evidenceIds - Array of evidence IDs
 * @returns {Array} Evidence objects
 */
function getEvidenceForExpert(session, evidenceIds) {
    if (!session.evidence || !evidenceIds) return [];

    return session.evidence.filter(ev =>
        evidenceIds.includes(ev.evidence_id)
    );
}

/**
 * Get company by ID
 * @param {Object} session - Session JSON object
 * @param {string} companyId - Company ID
 * @returns {Object|null} Company object
 */
function getCompanyById(session, companyId) {
    if (!session.companies) return null;

    return session.companies.find(c => c.company_id === companyId) || null;
}

// Export for use in app.js
window.ExpertGraph = {
    initGraph,
    loadSessionToGraph,
    sessionToElements,
    getEvidenceForExpert,
    getCompanyById,
    config: GraphConfig
};
