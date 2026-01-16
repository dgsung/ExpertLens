/**
 * ExpertLens API Client
 * Handles all API communication with the backend
 */

const ExpertLensAPI = (function() {
    'use strict';

    // Detect environment and set API URL accordingly
    function detectApiUrl() {
        const hostname = window.location.hostname;

        // GitHub Codespaces: *.app.github.dev
        if (hostname.includes('.app.github.dev')) {
            // Replace port 8080 with 8000 in the URL
            return window.location.origin.replace('-8080.', '-8000.');
        }

        // Render: expertlens.onrender.com -> expertlens-api.onrender.com
        if (hostname.endsWith('.onrender.com')) {
            return 'https://expertlens-api.onrender.com';
        }

        // Local development
        return 'http://localhost:8000';
    }

    // API Configuration
    const config = {
        baseUrl: detectApiUrl(),
        timeout: 30000
    };

    /**
     * Check if API server is available
     * @returns {Promise<boolean>}
     */
    async function isAvailable() {
        try {
            const response = await fetch(`${config.baseUrl}/healthz`, {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });
            return response.ok;
        } catch (error) {
            console.warn('API server not available:', error.message);
            return false;
        }
    }

    /**
     * Create a new session
     * @param {string} language - Session language (ko, en)
     * @returns {Promise<{session_id: string}>}
     */
    async function createSession(language = 'ko') {
        const response = await fetch(`${config.baseUrl}/sessions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ language })
        });

        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get session by ID
     * @param {string} sessionId - Session UUID
     * @returns {Promise<Object>} Session data
     */
    async function getSession(sessionId) {
        const response = await fetch(`${config.baseUrl}/sessions/${sessionId}`, {
            method: 'GET'
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`Session not found: ${sessionId}`);
            }
            throw new Error(`Failed to get session: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Run a search query in a session
     * @param {string} sessionId - Session UUID
     * @param {string} query - Search query
     * @param {boolean} useMock - Use mock search (default: false for real search)
     * @param {string|null} clarificationResponse - User's response to clarification
     * @returns {Promise<Object>} Updated session data
     */
    async function runSearch(sessionId, query, useMock = false, clarificationResponse = null) {
        const body = { query, use_mock: useMock };
        if (clarificationResponse) {
            body.clarification_response = clarificationResponse;
        }

        const response = await fetch(`${config.baseUrl}/sessions/${sessionId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`Session not found: ${sessionId}`);
            }
            throw new Error(`Failed to run search: ${response.status}`);
        }

        return response.json();
    }

    /**
     * List all session IDs
     * @returns {Promise<string[]>}
     */
    async function listSessions() {
        const response = await fetch(`${config.baseUrl}/sessions`, {
            method: 'GET'
        });

        if (!response.ok) {
            throw new Error(`Failed to list sessions: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Create session and run search in one flow
     * @param {string} query - Search query
     * @param {string} language - Session language
     * @param {boolean} useMock - Use mock search (default: false for real search)
     * @returns {Promise<Object>} Session with search results
     */
    async function search(query, language = 'ko', useMock = false) {
        // Create new session
        const { session_id } = await createSession(language);

        // Run search
        const session = await runSearch(session_id, query, useMock);

        return session;
    }

    /**
     * Set the API base URL
     * @param {string} url - Base URL
     */
    function setBaseUrl(url) {
        config.baseUrl = url.replace(/\/$/, ''); // Remove trailing slash
    }

    /**
     * Get current configuration
     * @returns {Object}
     */
    function getConfig() {
        return { ...config };
    }

    // Public API
    return {
        isAvailable,
        createSession,
        getSession,
        runSearch,
        listSessions,
        search,
        setBaseUrl,
        getConfig
    };

})();

// Export for use in other modules
window.ExpertLensAPI = ExpertLensAPI;
