let currentTheme = localStorage.getItem('theme') || 'dark';

function applyThemeIcon() {
    const btn = document.getElementById('themeToggle');
    if (btn) btn.innerText = currentTheme === 'dark' ? '🌙' : '☀️';
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', currentTheme);
    document.documentElement.setAttribute('data-theme', currentTheme);
    applyThemeIcon();
    document.dispatchEvent(new Event('themeChanged'));
}

document.addEventListener('DOMContentLoaded', () => {
    applyThemeIcon();
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
});
