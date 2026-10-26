/**
 * Authentication Pages Helper
 * Toggles password field visibility.
 */
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (input && btn) {
        if (input.type === 'password') {
            input.type = 'text';
            btn.classList.add('text-indigo-400');
        } else {
            input.type = 'password';
            btn.classList.remove('text-indigo-400');
        }
    }
}

window.togglePasswordVisibility = togglePasswordVisibility;

