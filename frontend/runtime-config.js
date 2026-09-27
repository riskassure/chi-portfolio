// Production uses one origin for the site and API. Live Server remains supported.
(() => {
    const local = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    window.PORTFOLIO_API_BASE = local && window.location.port === '5500'
        ? `${window.location.protocol}//${window.location.hostname}:5000/api`
        : '/api';
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('a[href^="/api/"]').forEach(link => {
            link.setAttribute('href', window.PORTFOLIO_API_BASE + link.getAttribute('href').slice(4));
        });
    });
})();
