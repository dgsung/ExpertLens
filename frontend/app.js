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
    let pendingClarificationQuery = null;

    // DOM elements
    const elements = {
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
        // Initialize i18n (auto-detects browser language)
        I18n.init();

        // Cache DOM elements
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

        console.log('ExpertLens Viewer initialized, language:', I18n.getLanguage());
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
            elements.chatInput.placeholder = I18n.t('chat.placeholder');
            console.log('API server connected');
        } else {
            elements.chatSubmit.disabled = true;
            elements.chatInput.placeholder = I18n.t('error.fetch');
            addMessage('system', I18n.t('error.fetch'));
            console.warn('API server not available');
        }
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Chat form submit
        elements.chatForm.addEventListener('submit', handleChatSubmit);

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
            addMessage('system', I18n.t('error.fetch'));
            return;
        }

        try {
            elements.chatSubmit.disabled = true;
            showLoading(I18n.t('loading.searching'));

            // Create session if needed (use detected language)
            if (!currentSessionId) {
                showLoading(I18n.t('loading.searching'));
                const result = await ExpertLensAPI.createSession(I18n.getLanguage());
                currentSessionId = result.session_id;
            }

            // Check if this is a clarification response
            let session;
            if (pendingClarificationQuery && currentSession?.status === 'clarification_needed') {
                showLoading(I18n.t('loading.analyzing'));
                session = await ExpertLensAPI.runSearch(
                    currentSessionId,
                    pendingClarificationQuery,
                    false,
                    query  // clarification_response
                );
                pendingClarificationQuery = null;
            } else {
                showLoading(I18n.t('loading.searching'));
                session = await ExpertLensAPI.runSearch(currentSessionId, query, false);
            }

            // Handle clarification needed
            if (session.status === 'clarification_needed' && session.clarification) {
                pendingClarificationQuery = query;
                currentSession = session;
                renderClarification(session.clarification);
                hideLoading();
                elements.chatSubmit.disabled = false;
                return;
            }

            // Load session into graph
            loadSession(session);

            // Render grouped results or simple list
            if (session.expert_groups && session.expert_groups.length > 0) {
                renderGroupedResults(session);
            } else {
                renderSimpleResults(session);
            }

            // Add search steps (collapsible)
            if (session.search_steps && session.search_steps.length > 0) {
                const stepsHtml = renderSearchSteps(session.search_steps);
                addMessage('assistant', stepsHtml);
            }

            playNotificationSound();

        } catch (error) {
            console.error('Search failed:', error);
            addMessage('system', `${I18n.t('error.fetch')}: ${error.message}`);
            playNotificationSound();
        } finally {
            hideLoading();
            elements.chatSubmit.disabled = false;
        }
    }

    /**
     * Render clarification question
     * @param {Object} clarification - Clarification object with question and options
     */
    function renderClarification(clarification) {
        const optionsHtml = clarification.options.map(opt => `
            <button class="clarification-option" data-value="${escapeHtml(opt.value)}" data-testid="clarification-option">
                ${escapeHtml(opt.label)}
            </button>
        `).join('');

        const html = `
            <div class="clarification-message" data-testid="assistant-clarification">
                <p class="clarification-question">${escapeHtml(clarification.question)}</p>
                <div class="clarification-options">
                    ${optionsHtml}
                </div>
                <p class="clarification-hint">${I18n.getLanguage() === 'ko' ? '또는 직접 입력하세요' : 'Or type your own response'}</p>
            </div>
        `;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `<div class="message-content">${html}</div>`;
        elements.chatMessages.appendChild(messageDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

        // Add click handlers for option buttons
        messageDiv.querySelectorAll('.clarification-option').forEach(btn => {
            btn.addEventListener('click', () => handleClarificationClick(btn.dataset.value));
        });
    }

    /**
     * Handle clarification option click
     * @param {string} value - Selected option value
     */
    async function handleClarificationClick(value) {
        // Map value to user-friendly text
        const responseText = value === 'yes' ? 'Yes, include tire manufacturers' : 'No, only rubber compound manufacturers';

        // Add as user message and process
        elements.chatInput.value = responseText;

        // Trigger form submit
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        elements.chatForm.dispatchEvent(submitEvent);
    }

    /**
     * Render grouped results with headers
     * @param {Object} session - Session with expert_groups
     */
    function renderGroupedResults(session) {
        const expertCount = session.experts ? session.experts.length : 0;

        let html = `<p>${expertCount} ${I18n.t('message.found')}</p>`;
        html += `<div class="results-list" data-testid="results-list">`;

        session.expert_groups.forEach(group => {
            const groupExperts = session.experts.filter(e =>
                group.expert_ids.includes(e.expert_id)
            );

            const testId = `group-header-${group.angle}`;
            html += `
                <div class="expert-group">
                    <h4 class="group-header" data-testid="${testId}">
                        ${escapeHtml(group.label)} (${group.count})
                    </h4>
                    <ul class="expert-list">
                        ${groupExperts.map(expert => `
                            <li class="expert-card" data-testid="expert-card" data-angle="${escapeHtml(expert.industry_tag || '')}">
                                <span class="expert-name">${escapeHtml(expert.canonical_name)}</span>
                                <span class="expert-industry-tag" data-testid="expert-industry-tag">${escapeHtml(expert.angle || '')}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        });

        html += `</div>`;

        addMessage('assistant', html);
    }

    /**
     * Render simple (non-grouped) results
     * @param {Object} session - Session object
     */
    function renderSimpleResults(session) {
        const expertCount = session.experts ? session.experts.length : 0;

        let responseHtml = '';

        if (expertCount > 0) {
            responseHtml = `${expertCount} ${I18n.t('message.found')}`;
            responseHtml += `<div class="result-card"><h4>${I18n.t('detail.expert')}</h4><ul>`;
            session.experts.slice(0, 5).forEach(expert => {
                responseHtml += `<li>${escapeHtml(expert.canonical_name)}</li>`;
            });
            if (expertCount > 5) {
                responseHtml += `<li>... +${expertCount - 5}</li>`;
            }
            responseHtml += `</ul></div>`;
        } else {
            responseHtml = `
                <div class="empty-result">
                    <p>${I18n.t('error.noResults')}</p>
                    <p class="hint">${I18n.t('error.tryAgain')}</p>
                </div>
            `;
        }

        addMessage('assistant', responseHtml);
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
                    <p>${I18n.t('detail.placeholder')}</p>
                </div>
            `;
        } else {
            const expertCount = currentSession.experts ? currentSession.experts.length : 0;
            const companyCount = currentSession.companies ? currentSession.companies.length : 0;
            elements.detailContent.innerHTML = `
                <div class="placeholder">
                    <p>${expertCount} ${I18n.t('detail.expert')}, ${companyCount} ${I18n.t('detail.company')}</p>
                    <p>${I18n.t('detail.placeholder')}</p>
                </div>
            `;
        }
    }

    /**
     * Show loading overlay
     * @param {string} message - Loading message
     */
    function showLoading(message = null) {
        message = message || I18n.t('loading.searching');
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
     * Render search steps as collapsible UI (ChatGPT style)
     * @param {Array} steps - Search steps from session
     * @returns {string} HTML string
     */
    function renderSearchSteps(steps) {
        const totalSources = steps.reduce((sum, s) => sum + s.result_count, 0);

        let detailsHtml = steps.map(step => {
            const icon = step.step_type === 'search' ? '🔍' : '📄';
            const urlList = step.urls && step.urls.length > 0
                ? `<ul class="step-urls">${step.urls.map(url => {
                    const domain = new URL(url).hostname;
                    return `<li><a href="${escapeHtml(url)}" target="_blank">${escapeHtml(domain)}</a></li>`;
                }).join('')}</ul>`
                : '';

            return `
                <div class="search-step">
                    <div class="step-header">
                        <span class="step-icon">${icon}</span>
                        <span class="step-desc">${escapeHtml(step.description)}</span>
                        <span class="step-count">${step.result_count}건</span>
                    </div>
                    ${urlList}
                </div>
            `;
        }).join('');

        return `
            <details class="search-process">
                <summary>
                    <span class="process-icon">🔎</span>
                    <span class="process-summary">${totalSources}개 소스 검색됨</span>
                </summary>
                <div class="search-steps-content">
                    ${detailsHtml}
                </div>
            </details>
        `;
    }

    /**
     * Play notification sound when job completes
     */
    function playNotificationSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.3;

            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            console.log('Audio notification not available');
        }
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

    /**
     * Load demo data for demonstration purposes
     */
    function loadDemoData() {
        const demoSession = {
            session_id: 'demo-session',
            language: 'ko',
            query: '데모 데이터',
            created_at: new Date().toISOString(),
            experts: [
                {
                    expert_id: 'demo-expert-1',
                    canonical_name: '김철수 박사',
                    evidence_ids: ['demo-ev-1', 'demo-ev-2'],
                    claims: [
                        {
                            claim_type: 'employment',
                            company: '삼성전자',
                            company_id: 'demo-company-1',
                            role: 'AI 연구소장',
                            start_date: '2020-01',
                            evidence_id: 'demo-ev-1'
                        },
                        {
                            claim_type: 'contact',
                            contact_type: 'email',
                            contact_value: 'example@demo.com',
                            status: 'verified',
                            evidence_id: 'demo-ev-1'
                        }
                    ]
                },
                {
                    expert_id: 'demo-expert-2',
                    canonical_name: '이영희 교수',
                    evidence_ids: ['demo-ev-3'],
                    claims: [
                        {
                            claim_type: 'employment',
                            company: '서울대학교',
                            company_id: 'demo-company-2',
                            role: '컴퓨터공학부 교수',
                            start_date: '2015-03',
                            evidence_id: 'demo-ev-3'
                        }
                    ]
                },
                {
                    expert_id: 'demo-expert-3',
                    canonical_name: '박민수',
                    evidence_ids: ['demo-ev-4'],
                    claims: [
                        {
                            claim_type: 'employment',
                            company: '삼성전자',
                            company_id: 'demo-company-1',
                            role: '수석 엔지니어',
                            start_date: '2018-06',
                            evidence_id: 'demo-ev-4'
                        }
                    ]
                }
            ],
            companies: [
                {
                    company_id: 'demo-company-1',
                    name: '삼성전자',
                    domain: 'samsung.com'
                },
                {
                    company_id: 'demo-company-2',
                    name: '서울대학교',
                    domain: 'snu.ac.kr'
                }
            ],
            evidence: [
                {
                    evidence_id: 'demo-ev-1',
                    url: 'https://example.com/profile/kimcs',
                    platform: 'LinkedIn'
                },
                {
                    evidence_id: 'demo-ev-2',
                    url: 'https://example.com/news/ai-research',
                    platform: 'News'
                },
                {
                    evidence_id: 'demo-ev-3',
                    url: 'https://example.com/professor/lee',
                    platform: 'University'
                },
                {
                    evidence_id: 'demo-ev-4',
                    url: 'https://example.com/engineer/park',
                    platform: 'Blog'
                }
            ]
        };

        loadSession(demoSession);
        addMessage('system', I18n.getLanguage() === 'ko'
            ? '데모 데이터를 로드했습니다. 노드를 클릭해서 상세 정보를 확인하세요.'
            : 'Demo data loaded. Click a node to see details.');
    }

    // Expose loadDemoData globally for button onclick
    window.loadDemoData = loadDemoData;

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
