# GitHub Sign-In Setup

REAlity now uses the normal OAuth authorization-code flow with PKCE. The GitHub authorization page reuses an existing GitHub login where possible. It does not read cross-origin cookies. Authorization remains explicit.

1. Register an OAuth App at https://github.com/settings/applications/new. Name: REAlity. Homepage: https://marcusdhaynes.github.io/REAlity/. Authorization callback: https://marcusdhaynes.github.io/REAlity/.
2. Deploy the standalone oauth-relay directory on Vercel (project root: oauth-relay). Configure GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET as production environment variables directly in the hosting dashboard. Never put the secret in GitHub, browser code, or chat. Redeploy after setting the variables.
3. Set docs/auth-config.json relay to the verified HTTPS endpoint ending /api/github-oauth. Deploy Pages. The endpoint accepts only the configured Pages origin and fixed callback; its GET response exposes only the public client ID and callback. Enable hosting rate limiting and monitor errors.
4. Open REAlity and select Continue With GitHub. The callback checks state and PKCE, verifies /user, and displays the account. Access tokens remain in browser memory and are cleared on disconnect or refresh. Start sign-in before loading files; full-page redirects reset unsaved work. Review public_repo and workflow permissions in GitHub. Revoke access in GitHub settings if needed.

The relay is committed but not deployed/configured. Until then the standard sign-in button reports that OAuth is unavailable. The optional scoped publishing token path remains separate. No password or client secret is requested in the browser.
