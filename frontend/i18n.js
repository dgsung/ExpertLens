/**
 * ExpertLens i18n (Internationalization) Module
 * Supports Korean (ko) and English (en)
 */

const I18n = (function() {
    'use strict';

    // Translations
    const translations = {
        ko: {
            // Header
            'app.title': 'ExpertLens',

            // Chat
            'chat.welcome': '안녕하세요! 전문가를 검색해보세요.',
            'chat.example': '예: "배터리 전문가", "AI 연구원"',
            'chat.placeholder': '전문가 검색...',

            // Graph legend
            'legend.expert': 'Expert',
            'legend.company': 'Company',

            // Detail panel
            'detail.placeholder': '노드를 클릭하면 상세 정보가 표시됩니다.',
            'detail.expert': '전문가',
            'detail.company': '회사',
            'detail.claims': '주요 정보',
            'detail.evidence': '출처',
            'detail.employees': '소속 전문가',

            // Loading
            'loading.searching': '검색 중...',
            'loading.analyzing': '분석 중...',

            // Errors
            'error.fetch': '오류: 서버 연결 실패',
            'error.noResults': '검색 결과가 없습니다.',
            'error.tryAgain': '다른 키워드로 시도해보세요.',

            // Claims
            'claim.employment': '소속',
            'claim.education': '학력',
            'claim.publication': '논문',
            'claim.patent': '특허',
            'claim.contact': '연락처',
            'claim.award': '수상',
            'claim.present': '현재',

            // Messages
            'message.searching': '검색 중입니다...',
            'message.found': '명의 전문가를 찾았습니다.',
            'message.clarification': '질문이 있습니다:'
        },
        en: {
            // Header
            'app.title': 'ExpertLens',

            // Chat
            'chat.welcome': 'Hello! Search for experts.',
            'chat.example': 'e.g., "Battery expert", "AI researcher"',
            'chat.placeholder': 'Search experts...',

            // Graph legend
            'legend.expert': 'Expert',
            'legend.company': 'Company',

            // Detail panel
            'detail.placeholder': 'Click a node to see details.',
            'detail.expert': 'Expert',
            'detail.company': 'Company',
            'detail.claims': 'Information',
            'detail.evidence': 'Sources',
            'detail.employees': 'Affiliated Experts',

            // Loading
            'loading.searching': 'Searching...',
            'loading.analyzing': 'Analyzing...',

            // Errors
            'error.fetch': 'Error: Failed to connect to server',
            'error.noResults': 'No results found.',
            'error.tryAgain': 'Try different keywords.',

            // Claims
            'claim.employment': 'Employment',
            'claim.education': 'Education',
            'claim.publication': 'Publication',
            'claim.patent': 'Patent',
            'claim.contact': 'Contact',
            'claim.award': 'Award',
            'claim.present': 'Present',

            // Messages
            'message.searching': 'Searching...',
            'message.found': 'expert(s) found.',
            'message.clarification': 'A question for you:'
        }
    };

    // Current language
    let currentLang = 'ko';

    /**
     * Detect browser language
     * @returns {string} Language code (ko or en)
     */
    function detectLanguage() {
        const browserLang = navigator.language || navigator.userLanguage;
        // Check if Korean
        if (browserLang.startsWith('ko')) {
            return 'ko';
        }
        // Default to English for all other languages
        return 'en';
    }

    /**
     * Initialize i18n with detected or specified language
     * @param {string} [lang] - Optional language override
     */
    function init(lang) {
        currentLang = lang || detectLanguage();
        document.documentElement.lang = currentLang;
        applyTranslations();
    }

    /**
     * Get translation for a key
     * @param {string} key - Translation key
     * @param {Object} [params] - Optional parameters for interpolation
     * @returns {string} Translated text
     */
    function t(key, params = {}) {
        const text = translations[currentLang]?.[key] || translations['en']?.[key] || key;

        // Simple interpolation: replace {param} with value
        return text.replace(/\{(\w+)\}/g, (match, param) => {
            return params[param] !== undefined ? params[param] : match;
        });
    }

    /**
     * Apply translations to all elements with data-i18n attribute
     */
    function applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = t(key);
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = t(key);
        });

        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            el.innerHTML = t(key);
        });
    }

    /**
     * Set language and re-apply translations
     * @param {string} lang - Language code
     */
    function setLanguage(lang) {
        if (translations[lang]) {
            currentLang = lang;
            document.documentElement.lang = lang;
            applyTranslations();
        }
    }

    /**
     * Get current language
     * @returns {string} Current language code
     */
    function getLanguage() {
        return currentLang;
    }

    /**
     * Get available languages
     * @returns {string[]} Array of language codes
     */
    function getAvailableLanguages() {
        return Object.keys(translations);
    }

    // Public API
    return {
        init,
        t,
        setLanguage,
        getLanguage,
        getAvailableLanguages,
        applyTranslations
    };

})();

// Export for use in other modules
window.I18n = I18n;
