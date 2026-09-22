// Runtime configuration for the SPA. Plain JS on purpose: there is no build step, so this
// file is the only thing to edit when the backend moves.
window.ELEARN_CONFIG = {
  // Base URL of the Django server, with no trailing slash.
  //
  // Empty means "same origin as this page", which is how docker compose runs it: nginx
  // serves these files and proxies /api/, /ws/, /media/, /static/ and /admin/ to Django,
  // so there is no cross-origin request and no CORS to configure.
  //
  // Set it (e.g. 'http://127.0.0.1:8000') only when the SPA is served from a different
  // origin than Django -- then that origin also has to be listed in CORS_ALLOWED_ORIGINS
  // on the backend, with django-cors-headers installed.
  API_BASE: '',
};
