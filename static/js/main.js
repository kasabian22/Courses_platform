/**
 * Global application JavaScript.
 * Handles toasts, confirm modal, theme switching, navigation, and mobile menu.
 */

// 1. Toast Notifications Auto-Dismiss
function initToasts() {
    const toasts = document.querySelectorAll('.toast-message');
    if (!toasts.length) return;

    setTimeout(function () {
        toasts.forEach((toast) => {
            // Add fade-out and slide-down transition classes
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'translate-y-4');

            // Remove element completely from DOM after animation completes
            setTimeout(() => {
                toast.remove();
            }, 500);
        });
    }, 8000); // Auto-dismiss after 8000ms
}

// 2. Custom Confirmation Modal (intercepts form[data-confirm])
function initConfirmModal() {
    const modal = document.getElementById('custom-confirm-modal');
    const box = document.getElementById('custom-confirm-box');
    const titleEl = document.getElementById('confirm-modal-title');
    const messageEl = document.getElementById('confirm-modal-message');
    const cancelBtn = document.getElementById('confirm-cancel-btn');
    const acceptBtn = document.getElementById('confirm-accept-btn');

    if (!modal || !box || !acceptBtn || !cancelBtn) return;

    let pendingForm = null;

    function openConfirmModal(form, message, title) {
        pendingForm = form;
        if (messageEl) messageEl.textContent = message || 'Are you sure you want to proceed?';
        if (titleEl) titleEl.textContent = title || 'Confirm Deletion';

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        requestAnimationFrame(() => {
            modal.classList.remove('opacity-0');
            box.classList.remove('scale-95');
            box.classList.add('scale-100');
        });
    }

    function closeConfirmModal() {
        modal.classList.add('opacity-0');
        box.classList.remove('scale-100');
        box.classList.add('scale-95');
        setTimeout(() => {
            modal.classList.remove('flex');
            modal.classList.add('hidden');
            pendingForm = null;
        }, 200);
    }

    // Intercept form submissions that have data-confirm attribute
    document.addEventListener('submit', function (e) {
        const form = e.target.closest('form[data-confirm]');
        if (form && !form.dataset.confirmed) {
            e.preventDefault();
            openConfirmModal(form, form.dataset.confirm, form.dataset.confirmTitle);
        }
    });

    acceptBtn.addEventListener('click', function () {
        if (pendingForm) {
            pendingForm.dataset.confirmed = 'true';
            pendingForm.submit();
        }
    });

    cancelBtn.addEventListener('click', closeConfirmModal);

    // Close when clicking outside the box
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeConfirmModal();
    });

    // Close when pressing Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeConfirmModal();
        }
    });
}

// 3. Theme Toggle & Telegram-Style Circular Ripple Transition
function syncThemeIcons() {
    const isLight = document.documentElement.classList.contains('light-mode');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');
    if (sunIcon && moonIcon) {
        sunIcon.classList.toggle('hidden', isLight);
        moonIcon.classList.toggle('hidden', !isLight);
    }
}

function toggleThemeWithRipple(event) {
    const root = document.documentElement;

    const applyToggle = () => {
        const isNowLight = root.classList.toggle('light-mode');
        localStorage.setItem('theme', isNowLight ? 'light' : 'dark');
        syncThemeIcons();
    };

    if (!document.startViewTransition) {
        applyToggle();
        return;
    }

    const btn = event.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = event.clientX || (rect.left + rect.width / 2);
    const y = event.clientY || (rect.top + rect.height / 2);

    const endRadius = Math.hypot(
        Math.max(x, window.innerWidth - x),
        Math.max(y, window.innerHeight - y)
    );

    const transition = document.startViewTransition(() => {
        applyToggle();
    });

    transition.ready.then(() => {
        document.documentElement.animate(
            {
                clipPath: [
                    `circle(0px at ${x}px ${y}px)`,
                    `circle(${endRadius}px at ${x}px ${y}px)`
                ]
            },
            {
                duration: 550,
                easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
                pseudoElement: '::view-transition-new(root)'
            }
        );
    });
}

// 4. Horizontal Subject Navigation
function scrollSubjects(amount) {
    const nav = document.getElementById('subject-nav');
    if (nav) {
        nav.scrollBy({ left: amount, behavior: 'smooth' });
    }
}

function initSubjectNav() {
    const subjectNav = document.getElementById('subject-nav');
    if (subjectNav) {
        subjectNav.addEventListener('wheel', function (e) {
            if (e.deltaY !== 0) {
                e.preventDefault();
                subjectNav.scrollBy({ left: e.deltaY * 2, behavior: 'smooth' });
            }
        }, { passive: false });
    }
}

// 5. Mobile Menu Toggle
function initMobileMenu() {
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const iconOpen = document.getElementById('mobile-menu-icon-open');
    const iconClose = document.getElementById('mobile-menu-icon-close');

    if (mobileBtn && mobileMenu) {
        mobileBtn.addEventListener('click', function () {
            const isHidden = mobileMenu.classList.toggle('hidden');
            mobileBtn.setAttribute('aria-expanded', !isHidden);
            if (iconOpen && iconClose) {
                iconOpen.classList.toggle('hidden', !isHidden);
                iconOpen.classList.toggle('block', isHidden);
                iconClose.classList.toggle('hidden', isHidden);
                iconClose.classList.toggle('block', !isHidden);
            }
        });
    }
}

// Global functions for inline onclick handlers
window.syncThemeIcons = syncThemeIcons;
window.toggleThemeWithRipple = toggleThemeWithRipple;
window.scrollSubjects = scrollSubjects;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    initToasts();
    initConfirmModal();
    syncThemeIcons();
    initSubjectNav();
    initMobileMenu();
});

// Re-sync icons if returned from back-forward cache
window.addEventListener('pageshow', syncThemeIcons);
syncThemeIcons();

