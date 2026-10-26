/**
 * Module View Helper
 * Filters module contents by type (all, text, video, image, file).
 */
function filterContent(type, activeBtn) {
    const cards = document.querySelectorAll('.content-card');
    const buttons = document.querySelectorAll('.filter-btn');

    // Reset button styles
    buttons.forEach((btn) => {
        btn.className = 'filter-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#2a2d30] text-gray-300 border border-[#3c4043] hover:text-white transition-colors';
    });

    // Highlight active button
    if (activeBtn) {
        activeBtn.className = 'filter-btn active-filter px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition-colors';
    }

    // Show/hide content cards based on selected type
    cards.forEach((card) => {
        if (type === 'all' || card.getAttribute('data-content-type') === type) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

window.filterContent = filterContent;

