
(function(window) {
    'use strict';

    // Configuration
    // In production, this should point to your real domain
    // const AUTH_BASE_URL = "https://codeman.bettermao.cfd"; 
    const AUTH_BASE_URL = window.location.origin.includes('localhost') 
        ? "http://localhost:5173" 
        : "https://codeman.bettermao.cfd";

    const API_BASE_URL = window.location.origin.includes('localhost')
        ? "http://localhost:8000/api"
        : "https://codeman.bettermao.cfd/api";

    /**
     * CodeMan SSO SDK
     */
    const CodeManSSO = {
        config: {
            clientId: null,
            redirectUri: window.location.href.split('?')[0], // Default to current page
            responseType: 'code',
            debug: false
        },

        /**
         * Initialize the SDK
         * @param {Object} options 
         */
        init: function(options) {
            this.config = { ...this.config, ...options };
            if (this.config.debug) {
                console.log('CodeMan SSO initialized with:', this.config);
            }
        },

        /**
         * Start Login Flow (Redirect)
         * Redirects the user to CodeMan authorization page
         * @param {string} state Optional state parameter for security
         */
        login: function(state) {
            if (!this.config.clientId) {
                console.error('CodeMan SSO: clientId is missing. Call init() first.');
                return;
            }

            const params = new URLSearchParams({
                client_id: this.config.clientId,
                redirect_uri: this.config.redirectUri,
                response_type: this.config.responseType
            });

            if (state) {
                params.append('state', state);
            }

            // Redirect to Vue Frontend Auth Page
            window.location.href = `${AUTH_BASE_URL}/oauth/authorize?${params.toString()}`;
        },

        /**
         * Exchange authorization code for user info (Client-side simplified flow)
         * Note: In a secure production app, code exchange should happen on your BACKEND.
         * This helper is for simple client-side apps or demos.
         * 
         * @param {string} code The authorization code from URL
         * @param {string} clientSecret WARNING: Only use if you understand the risks of exposing secret in frontend
         */
        exchangeToken: async function(code, clientSecret) {
            try {
                const response = await fetch(`${API_BASE_URL}/oauth/token`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        grant_type: 'authorization_code',
                        code: code,
                        client_id: this.config.clientId,
                        client_secret: clientSecret,
                        redirect_uri: this.config.redirectUri
                    })
                });

                if (!response.ok) {
                    throw new Error('Token exchange failed');
                }

                return await response.json();
            } catch (error) {
                console.error('CodeMan SSO Error:', error);
                throw error;
            }
        },

        /**
         * Get User Info using Access Token
         * @param {string} accessToken 
         */
        getUserInfo: async function(accessToken) {
            try {
                const response = await fetch(`${API_BASE_URL}/oauth/userinfo`, {
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch user info');
                }

                return await response.json();
            } catch (error) {
                console.error('CodeMan SSO Error:', error);
                throw error;
            }
        },

        /**
         * Helper to parse query parameters from URL
         */
        getAuthCodeFromUrl: function() {
            const params = new URLSearchParams(window.location.search);
            return params.get('code');
        }
    };

    // Expose to window
    window.CodeManSSO = CodeManSSO;

})(window);
