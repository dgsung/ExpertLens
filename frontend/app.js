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
            addMessage('system', 'API 서버에 연결할 수 없습니다.');
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
            const session = await ExpertLensAPI.runSearch(currentSessionId, query, false);

            // Load session into graph
            loadSession(session);

            // Add assistant response
            const expertCount = session.experts ? session.experts.length : 0;
            const companyCount = session.companies ? session.companies.length : 0;

            let responseHtml = '';

            if (expertCount > 0) {
                responseHtml = `${expertCount}명의 전문가를 찾았습니다.`;
                responseHtml += `<div class="result-card"><h4>전문가 목록</h4><ul>`;
                session.experts.slice(0, 5).forEach(expert => {
                    responseHtml += `<li>${escapeHtml(expert.canonical_name)}</li>`;
                });
                if (expertCount > 5) {
                    responseHtml += `<li>... 외 ${expertCount - 5}명</li>`;
                }
                responseHtml += `</ul></div>`;
            } else {
                responseHtml = `
                    <div class="empty-result">
                        <p>검색 결과가 없습니다.</p>
                        <p class="hint">다른 키워드로 시도해보세요.</p>
                    </div>
                `;
            }

            // Add search steps (collapsible)
            if (session.search_steps && session.search_steps.length > 0) {
                const stepsHtml = renderSearchSteps(session.search_steps);
                addMessage('assistant', stepsHtml);
            }

            addMessage('assistant', responseHtml);
            playNotificationSound();

        } catch (error) {
            console.error('Search failed:', error);
            addMessage('system', `오류: ${error.message}`);
            playNotificationSound();
        } finally {
            hideLoading();
            elements.chatSubmit.disabled = false;
        }
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
        addMessage('system', '데모 데이터를 로드했습니다. 노드를 클릭해서 상세 정보를 확인하세요.');
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
