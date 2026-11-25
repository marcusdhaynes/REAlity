# GitHub Sign-In (GitHub Pages + Supabase Auth)

REAlity is hosted on GitHub Pages. No Vercel deployment is used or required. A website cannot read GitHub's cross-origin login cookie. GitHub's OAuth authorization page can reuse an existing GitHub session and request explicit application authorization.

## One-time administrator setup

1. Create a dedicated REAlity Supabase project (do not reuse unrelated applications' projects). Note the project URL and publishable key.
2. In GitHub, register a new OAuth application at https://github.com/settings/applications/new. Homepage: https://marcusdhaynes.github.io/REAlity/. Authorization callback: the exact GitHub provider callback shown in the project's Supabase Authentication settings (normally https://PROJECT_REF.supabase.co/auth/v1/callback).
3. Enable the GitHub provider in that project's Supabase Authentication settings. Enter the OAuth client ID and client secret directly in the Supabase dashboard; never commit the secret to GitHub.
4. Set the Supabase Site URL and allowed redirect URL to https://marcusdhaynes.github.io/REAlity/. Use exact URLs rather than wildcards.
5. Update docs/auth-config.json with the project URL and modern sb_publishable_ key. Never include a service-role or secret API key. Deploy GitHub Pages using the existing Actions workflow.
6. Select Continue With GitHub. Supabase's PKCE OAuth flow reuses the existing GitHub session if available. Review GitHub's public_repo and workflow permissions. The callback exchanges the code using a tab-local verifier and verifies the returned GitHub provider token against GitHub's /user endpoint.
7. Sign in before selecting files because OAuth redirects reset the unsaved workbench. The GitHub token stays in browser memory, not persistent storage. Disconnect clears the local token; revoke the authorization in GitHub if desired.

The project-specific provider configuration must be completed before live login can work. The scoped GitHub token fallback remains available. The optional self-hosted device flow is separate and not required for Supabase login.

Official setup: https://supabase.com/docs/guides/auth/social-sign-in/auth-github
