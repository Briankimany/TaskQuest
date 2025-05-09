/**
 * Theme Manager for Real-Life RPG System
 * Handles switching between professional and gaming themes
 */
class ThemeManager {
    constructor() {
        this.themeLink = document.createElement('link');
        this.themeLink.rel = 'stylesheet';
        this.themeLink.id = 'gaming-theme';
        
        this.templateThemeLink = document.createElement('link');
        this.templateThemeLink.rel = 'stylesheet';
        this.templateThemeLink.id = 'template-gaming-theme';
        
        this.toggleButton = document.querySelector('.theme-toggle-btn');
        
        // Create background overlay if it doesn't exist
        if (!document.querySelector('.theme-bg-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'theme-bg-overlay';
            document.body.prepend(overlay);
        }
        
        // Detect current template
        this.currentTemplate = this.detectCurrentTemplate();
    }

    initialize() {
        this.loadSavedTheme();
        this.setupEventListeners();
    }
    
    detectCurrentTemplate() {
        // Get current URL path
        const path = window.location.pathname;
        
        // Extract template name from path
        if (path.includes('/timetable')) {
            return 'timetable';
        } else if (path.includes('/activities')) {
            return 'activities';
        } else if (path.includes('/stats')) {
            return 'stats';
        } else if (path.includes('/dashboard')) {
            return 'dashboard';
        } else {
            return 'default';
        }
    }

    loadSavedTheme() {
        if(localStorage.getItem('theme') === 'gaming') {
            this.enableGamingTheme();
        }
    }

    enableGamingTheme() {
        // Load base gaming theme
        this.themeLink.href = '/static/css/base_gaming.css';
        document.head.appendChild(this.themeLink);
        
        // Load template-specific gaming theme if available
        if (this.currentTemplate !== 'default') {
            this.templateThemeLink.href = `/static/css/${this.currentTemplate}_gaming.css`;
            document.head.appendChild(this.templateThemeLink);
        }
        
        this.toggleButton.classList.add('active');
        document.body.classList.add('theme-gaming');
        localStorage.setItem('theme', 'gaming');
    }

    disableGamingTheme() {
        // Remove base gaming theme
        if (document.getElementById('gaming-theme')) {
            document.getElementById('gaming-theme').remove();
        }
        
        // Remove template-specific gaming theme
        if (document.getElementById('template-gaming-theme')) {
            document.getElementById('template-gaming-theme').remove();
        }
        
        this.toggleButton.classList.remove('active');
        document.body.classList.remove('theme-gaming');
        localStorage.setItem('theme', 'professional');
    }

    setupEventListeners() {
        this.toggleButton.addEventListener('click', () => {
            if(document.getElementById('gaming-theme')) {
                this.disableGamingTheme();
            } else {
                this.enableGamingTheme();
            }
        });
    }
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager().initialize();
});