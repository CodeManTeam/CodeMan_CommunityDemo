
<script setup>
import { ref } from 'vue'
import MarkdownEditor from '../components/MarkdownEditor.vue' // Reusing for display if needed or just HTML

const activeTab = ref('intro')

const sdkCode = `<!-- Include SDK -->
<script src="https://codeman.bettermao.cfd/sdk/codeman-sso.js"><\/script>

<script>
  // 1. Initialize
  CodeManSSO.init({
      clientId: 'YOUR_CLIENT_ID',
      redirectUri: 'YOUR_CALLBACK_URL'
  });

  // 2. Login
  function login() {
      CodeManSSO.login();
  }
<\/script>`
</script>

<template>
  <div class="prose prose-blue max-w-none">
    <h1>CodeMan Developer Documentation</h1>
    
    <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-8">
      <p class="text-blue-700 m-0">
        <strong>Welcome!</strong> Build the next generation of creative coding tools using CodeMan's unified authentication and API services.
      </p>
    </div>

    <h2>Getting Started</h2>
    <p>
      CodeMan provides a standard OAuth 2.0 provider service. You can use it to let users log in to your application using their CodeMan (and by extension, Codemao) identity.
    </p>

    <h3>1. Create an Application</h3>
    <p>
      First, go to the <router-link to="/developer/dashboard" class="text-blue-600 font-bold">Dashboard</router-link> to create a new application and get your <code>Client ID</code> and <code>Client Secret</code>.
    </p>

    <h3>2. Integrate SDK</h3>
    <p>Add the following code to your website:</p>
    
    <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto text-sm text-gray-300 font-mono">
      <pre>{{ sdkCode }}</pre>
    </div>

    <h3>3. Handle Callback</h3>
    <p>
      After the user logs in, they will be redirected to your <code>redirectUri</code> with a <code>code</code> parameter.
    </p>
    <p>
      <code>https://yoursite.com/callback?code=AUTHORIZATION_CODE</code>
    </p>
    <p>
      You should then exchange this code for an access token on your backend:
    </p>
    
    <div class="bg-gray-100 p-4 rounded-lg">
      <h4 class="text-sm font-bold uppercase text-gray-500 mb-2">POST /api/oauth/token</h4>
      <ul class="list-none p-0 m-0 text-sm space-y-1">
        <li><strong>grant_type:</strong> "authorization_code"</li>
        <li><strong>code:</strong> The code you received</li>
        <li><strong>client_id:</strong> Your Client ID</li>
        <li><strong>client_secret:</strong> Your Client Secret</li>
        <li><strong>redirect_uri:</strong> The same redirect URI used in step 1</li>
      </ul>
    </div>

  </div>
</template>
