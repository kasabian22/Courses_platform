/**
 * Add / Edit Content Helper
 * Handles video source switching and asynchronous file upload with progress bar.
 */

function switchVideoSource(source) {
    const urlContainer = document.getElementById('video-url-container');
    const uploadContainer = document.getElementById('video-upload-container');
    const tabUrlBtn = document.getElementById('tab-url-btn');
    const tabUploadBtn = document.getElementById('tab-upload-btn');
    const urlInput = document.querySelector('input[name="video_url"]') || document.getElementById('id_video_url');
    const uploadInput = document.querySelector('input[name="video_upload"]') || document.getElementById('id_video_upload');
    const clearVideoCheckbox = document.getElementById('video_upload-clear_id');

    if (!urlContainer || !uploadContainer || !tabUrlBtn || !tabUploadBtn) return;

    if (source === 'url') {
        urlContainer.classList.remove('hidden');
        uploadContainer.classList.add('hidden');
        tabUrlBtn.className = 'py-2.5 px-4 rounded-lg text-xs font-semibold transition-all bg-indigo-600 text-white';
        tabUploadBtn.className = 'py-2.5 px-4 rounded-lg text-xs font-semibold transition-all text-gray-400 hover:text-white';
        if (uploadInput) uploadInput.value = '';
        if (clearVideoCheckbox) clearVideoCheckbox.checked = true;
    } else {
        uploadContainer.classList.remove('hidden');
        urlContainer.classList.add('hidden');
        tabUploadBtn.className = 'py-2.5 px-4 rounded-lg text-xs font-semibold transition-all bg-indigo-600 text-white';
        tabUrlBtn.className = 'py-2.5 px-4 rounded-lg text-xs font-semibold transition-all text-gray-400 hover:text-white';
        if (urlInput) urlInput.value = '';
        if (clearVideoCheckbox) clearVideoCheckbox.checked = false;
    }
}

window.switchVideoSource = switchVideoSource;

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('content-upload-form');
    if (!form) return;

    // Check if the server rendered an initial tab preference
    const defaultSource = form.dataset.defaultVideoSource;
    if (defaultSource === 'upload') {
        switchVideoSource('upload');
    }

    const uploadInput = document.querySelector('input[name="video_upload"]') || document.getElementById('id_video_upload');

    // Live Progress Bar using XMLHttpRequest when uploading a video file
    form.addEventListener('submit', function (e) {
        if (uploadInput && uploadInput.files && uploadInput.files.length > 0) {
            e.preventDefault();
            const progressWrapper = document.getElementById('upload-progress-wrapper');
            const progressBar = document.getElementById('upload-progress-bar');
            const percentageText = document.getElementById('upload-percentage');
            const submitBtn = document.getElementById('submit-content-btn');

            if (progressWrapper) progressWrapper.classList.remove('hidden');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Uploading...';
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', window.location.href, true);

            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    const percent = Math.round((event.loaded / event.total) * 100);
                    if (progressBar) progressBar.style.width = percent + '%';
                    if (percentageText) percentageText.textContent = percent + '%';
                }
            };

            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 400) {
                    // If Django redirected after successful upload, follow the final URL
                    if (xhr.responseURL && xhr.responseURL !== window.location.href) {
                        window.location.href = xhr.responseURL;
                    } else {
                        // Form had validation errors; replace document with returned HTML
                        document.open();
                        document.write(xhr.responseText);
                        document.close();
                    }
                } else {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Save Video';
                    }
                }
            };

            xhr.onerror = function () {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Save Video';
                }
            };

            xhr.send(new FormData(form));
        }
    });
});

