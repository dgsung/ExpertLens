/**
 * ExpertLens Viewer Application
 * Main application logic for chat, graph, and detail panel
 */

(function() {
    'use strict';

    // Application state
    let cy = null;
    let currentSession = null;
    let currentSessionId = null;
    let apiAvailable = false;

    // DOM elements
    const elements = {
        fileInput: null,
        sessionInfo: null,
        detailContent: null,
        graphContainer: null,
        chatForm: null,
        chatInput: null,
        chatSubmit: null,
        chatMessages: null,
        loadingOverlay: null,
        loadingMessage: null
    };

    /**
     * Initialize the application
     */
    async function init() {
        // Cache DOM elements
        elements.fileInput = document.getElementById('session-file');
        elements.sessionInfo = document.getElementById('session-info');
        elements.detailContent = document.getElementById('detail-content');
        elements.graphContainer = document.getElementById('cy');
        elements.chatForm = document.getElementById('chat-form');
        elements.chatInput = document.getElementById('chat-input');
        elements.chatSubmit = document.getElementById('chat-submit');
        elements.chatMessages = document.getElementById('chat-messages');
        elements.loadingOverlay = document.getElementById('loading-overlay');
        elements.loadingMessage = document.getElementById('loading-message');

        // Initialize Cytoscape graph
        cy = ExpertGraph.initGraph('cy');

        // Set up event listeners
        setupEventListeners();

        // Check API availability
        await checkApiStatus();

        console.log('ExpertLens Viewer initialized');
    }

    /**
     * Check if API server is available
     */
    async function checkApiStatus() {
        apiAvailable = await ExpertLensAPI.isAvailable();
        updateApiStatusUI();
    }

    /**
     * Update UI based on API availability
     */
    function updateApiStatusUI() {
        if (apiAvailable) {
            elements.chatSubmit.disabled = false;
            elements.chatInput.placeholder = '전문가 검색...';
            console.log('API server connected');
        } else {
            elements.chatSubmit.disabled = true;
            elements.chatInput.placeholder = 'API 서버 연결 안됨';
            addMessage('system', 'API 서버에 연결할 수 없습니다. 파일 로드를 사용해주세요.');
            console.warn('API server not available');
        }
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Chat form submit
        elements.chatForm.addEventListener('submit', handleChatSubmit);

        // File input change
        elements.fileInput.addEventListener('change', handleFileSelect);

        // Graph node click
        cy.on('tap', 'node', handleNodeClick);

        // Graph background click (deselect)
        cy.on('tap', function(evt) {
            if (evt.target === cy) {
                showPlaceholder();
            }
        });

        // Retry API connection on focus
        elements.chatInput.addEventListener('focus', async function() {
            if (!apiAvailable) {
                await checkApiStatus();
            }
        });
    }

    /**
     * Add message to chat
     * @param {string} type - 'user', 'assistant', or 'system'
     * @param {string} content - Message content (can include HTML)
     */
    function addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
        elements.chatMessages.appendChild(messageDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    /**
     * Handle chat form submission
     * @param {Event} event - Form submit event
     */
    async function handleChatSubmit(event) {
        event.preventDefault();

        const query = elements.chatInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage('user', escapeHtml(query));
        elements.chatInput.value = '';

        if (!apiAvailable) {
            addMessage('system', 'API 서버에 연결할 수 없습니다.');
            return;
        }

        try {
            elements.chatSubmit.disabled = true;
            showLoading('검색 중...');

            // Create session if needed
            if (!currentSessionId) {
                showLoading('세션 생성 중...');
                const result = await ExpertLensAPI.createSession('ko');
                currentSessionId = result.session_id;
            }

            showLoading(`"${query}" 검색 중...`);

            // Run search
            const session = await ExpertLensAPI.runSearch(currentSessionId, query);

            // Load session into graph
            loadSession(session);

            // Add assistant response
            const expertCount = session.experts ? session.experts.length : 0;
            const companyCount = session.companies ? session.companies.length : 0;

            let responseHtml = `${expertCount}명의 전문가를 찾았습니다.`;

            if (expertCount > 0) {
                responseHtml += `<div class="result-card"><h4>전문가 목록</h4><ul>`;
                session.experts.slice(0, 5).forEach(expert => {
                    responseHtml += `<li>${escapeHtml(expert.canonical_name)}</li>`;
                });
                if (expertCount > 5) {
                    responseHtml += `<li>... 외 ${expertCount - 5}명</li>`;
                }
                responseHtml += `</ul></div>`;
            }

            addMessage('assistant', responseHtml);

        } catch (error) {
            console.error('Search failed:', error);
            addMessage('system', `오류: ${error.message}`);
        } finally {
            hideLoading();
            elements.chatSubmit.disabled = false;
        }
    }

    /**
     * Handle file selection
     * @param {Event} event - File input change event
     */
    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();

        reader.onload = function(e) {
            try {
                const session = JSON.parse(e.target.result);
                loadSession(session);
                addMessage('system', `파일 로드됨: ${file.name}`);
            } catch (error) {
                console.error('Failed to parse JSON:', error);
                addMessage('system', '오류: 올바른 JSON 파일이 아닙니다.');
            }
        };

        reader.onerror = function() {
            console.error('Failed to read file');
            addMessage('system', '오류: 파일을 읽을 수 없습니다.');
        };

        reader.readAsText(file);
    }

    /**
     * Load session data
     * @param {Object} session - Session JSON object
     */
    function loadSession(session) {
        currentSession = session;
        currentSessionId = session.session_id;

        // Update session info
        const expertCount = session.experts ? session.experts.length : 0;
        const evidenceCount = session.evidence ? session.evidence.length : 0;
        elements.sessionInfo.textContent =
            `${expertCount} experts, ${evidenceCount} evidence`;

        // Load into graph
        ExpertGraph.loadSessionToGraph(cy, session);

        // Show placeholder
        showPlaceholder();

        console.log('Session loaded:', session.session_id);
    }

    /**
     * Handle node click
     * @param {Event} event - Cytoscape tap event
     */
    function handleNodeClick(event) {
        const node = event.target;
        const nodeType = node.data('type');

        if (nodeType === 'expert') {
            showExpertDetail(node.data('expertData'));
        } else if (nodeType === 'company') {
            showCompanyDetail(node.data('companyData'));
        }
    }

    /**
     * Show expert detail in panel
     * @param {Object} expert - Expert data object
     */
    function showExpertDetail(expert) {
        if (!expert) return;

        const evidence = ExpertGraph.getEvidenceForExpert(
            currentSession,
            expert.evidence_ids
        );

        // Separate claims by type
        const employmentClaims = [];
        const contactClaims = [];

        if (expert.claims) {
            expert.claims.forEach(claim => {
                if (claim.claim_type === 'employment') {
                    employmentClaims.push(claim);
                } else if (claim.claim_type === 'contact') {
                    contactClaims.push(claim);
                }
            });
        }

        let html = `
            <div class="detail-header">
                <h2>${escapeHtml(expert.canonical_name)}</h2>
                <span class="entity-type">Expert</span>
            </div>
        `;

        // Employment claims
        if (employmentClaims.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>Employment</h3>
                    <ul class="claims-list">
                        ${employmentClaims.map(claim => `
                            <li class="claim-item employment">
                                <div class="claim-type">Employment</div>
                                <div class="claim-content">${escapeHtml(claim.company)}</div>
                                ${claim.role ? `<div class="claim-detail">${escapeHtml(claim.role)}</div>` : ''}
                                ${claim.start_date || claim.end_date ? `
                                    <div class="claim-detail">
                                        ${claim.start_date || '?'} ~ ${claim.end_date || 'present'}
                                    </div>
                                ` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Contact claims
        if (contactClaims.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>Contact</h3>
                    <ul class="claims-list">
                        ${contactClaims.map(claim => `
                            <li class="claim-item contact">
                                <div class="claim-type">${escapeHtml(claim.contact_type)}</div>
                                <div class="claim-content">${escapeHtml(claim.contact_value)}</div>
                                <div class="claim-detail">Status: ${claim.status || 'unknown'}</div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        // Evidence
        if (evidence.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>Evidence (${evidence.length})</h3>
                    <ul class="evidence-list">
                        ${evidence.map(ev => `
                            <li class="evidence-item">
                                <a href="${escapeHtml(ev.url)}" target="_blank" rel="noopener" class="evidence-link">
                                    <span class="evidence-platform">${escapeHtml(ev.platform)}</span>
                                    <span class="evidence-url">${escapeHtml(truncateUrl(ev.url))}</span>
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        elements.detailContent.innerHTML = html;
    }

    /**
     * Show company detail in panel
     * @param {Object} company - Company data object
     */
    function showCompanyDetail(company) {
        if (!company) return;

        // Find experts connected to this company
        const connectedExperts = [];
        if (currentSession.experts) {
            currentSession.experts.forEach(expert => {
                if (expert.claims) {
                    const hasConnection = expert.claims.some(
                        claim => claim.company_id === company.company_id
                    );
                    if (hasConnection) {
                        connectedExperts.push(expert);
                    }
                }
            });
        }

        let html = `
            <div class="detail-header">
                <h2>${escapeHtml(company.name)}</h2>
                <span class="entity-type">Company</span>
            </div>

            <div class="detail-section">
                <h3>Information</h3>
                <div class="company-info">
                    ${company.domain ? `
                        <p><span class="label">Domain:</span>${escapeHtml(company.domain)}</p>
                    ` : ''}
                    ${company.region ? `
                        <p><span class="label">Region:</span>${escapeHtml(company.region)}</p>
                    ` : ''}
                </div>
            </div>
        `;

        // Connected experts
        if (connectedExperts.length > 0) {
            html += `
                <div class="detail-section">
                    <h3>Connected Experts (${connectedExperts.length})</h3>
                    <ul class="claims-list">
                        ${connectedExperts.map(expert => {
                            const claim = expert.claims.find(
                                c => c.company_id === company.company_id
                            );
                            return `
                                <li class="claim-item employment">
                                    <div class="claim-content">${escapeHtml(expert.canonical_name)}</div>
                                    ${claim && claim.role ? `
                                        <div class="claim-detail">${escapeHtml(claim.role)}</div>
                                    ` : ''}
                                </li>
                            `;
                        }).join('')}
                    </ul>
                </div>
            `;
        }

        elements.detailContent.innerHTML = html;
    }

    /**
     * Show placeholder in detail panel
     */
    function showPlaceholder() {
        if (!currentSession) {
            elements.detailContent.innerHTML = `
                <div class="placeholder">
                    <p>노드를 클릭하면 상세 정보가 표시됩니다.</p>
                </div>
            `;
        } else {
            const expertCount = currentSession.experts ? currentSession.experts.length : 0;
            const companyCount = currentSession.companies ? currentSession.companies.length : 0;
            elements.detailContent.innerHTML = `
                <div class="placeholder">
                    <p>${expertCount} 전문가, ${companyCount} 기업</p>
                    <p>노드를 클릭하면 상세 정보가 표시됩니다.</p>
                </div>
            `;
        }
    }

    /**
     * Show loading overlay
     * @param {string} message - Loading message
     */
    function showLoading(message = '로딩 중...') {
        elements.loadingMessage.textContent = message;
        elements.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    function hideLoading() {
        elements.loadingOverlay.classList.add('hidden');
    }

    /**
     * Escape HTML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Truncate URL for display
     * @param {string} url - URL to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated URL
     */
    function truncateUrl(url, maxLength = 50) {
        if (!url) return '';
        if (url.length <= maxLength) return url;

        // Remove protocol
        let display = url.replace(/^https?:\/\//, '');

        if (display.length <= maxLength) return display;

        // Truncate with ellipsis
        return display.substring(0, maxLength - 3) + '...';
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
