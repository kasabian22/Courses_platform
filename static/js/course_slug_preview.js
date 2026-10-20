document.addEventListener("DOMContentLoaded", function () {
    const titleInput = document.getElementById("id_title");
    const slugInput = document.getElementById("id_slug");

    if (!titleInput || !slugInput) return;

    // Track whether the instructor manually edited the slug field
    let isSlugManuallyEdited = false;
    let debounceTimer = null;

    // Optional: If editing an existing course, lock auto-generation initially so we don't accidentally change published URLs
    const currentCourseId = "{{ form.instance.pk|default:'' }}";
    if (slugInput.value.trim() !== "") {
        isSlugManuallyEdited = true;
    }

    // 1. Build a clean UI wrapper around the slug input
    const wrapper = document.createElement("div");
    wrapper.className = "mt-2 flex flex-col gap-2 w-full";

    const inputGroup = document.createElement("div");
    // Increased padding and height (py-1.5, min-h-[46px]) for a spacious modern look
    inputGroup.className = "flex items-center w-full rounded-xl overflow-hidden border border-[#3c4043] bg-[#1c1d22] focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all";

    // Compact Prefix: Showing only "/course/" saves huge horizontal space for the actual slug
    const prefixSpan = document.createElement("span");
    prefixSpan.className = "px-4 py-3 text-sm font-semibold text-gray-400 bg-[#2a2d30] border-r border-[#3c4043] select-none shrink-0 font-mono";
    prefixSpan.textContent = "/course/";

    // Regenerate / Reset button
    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.title = "Regenerate slug automatically from title";
    resetBtn.className = "px-4 py-3 text-xs sm:text-sm font-medium text-indigo-400 hover:text-white hover:bg-indigo-600 transition-colors shrink-0 border-l border-[#3c4043] cursor-pointer flex items-center gap-1";
    resetBtn.innerHTML = "<span>↻</span> <span>Auto</span>";

    // Status message badge below the input
    const statusText = document.createElement("div");
    statusText.className = "text-xs font-medium min-h-[1.25rem] transition-all text-gray-400";

    // Configure the main slug input
    slugInput.parentNode.insertBefore(wrapper, slugInput);
    // flex-1 ensures it expands to take all remaining width smoothly
    slugInput.className = "flex-1 w-full px-4 py-2.5 text-sm sm:text-base bg-transparent text-white focus:outline-none font-mono tracking-wide placeholder-gray-500";
    slugInput.placeholder = "course-url-slug";

    inputGroup.appendChild(prefixSpan);
    inputGroup.appendChild(slugInput);
    inputGroup.appendChild(resetBtn);
    wrapper.appendChild(inputGroup);
    wrapper.appendChild(statusText);

    // 2. Function to call the Django AJAX endpoint
    function fetchSmartSlug( { title = "", customSlug = "", updateInputValue = true } ) {
        const params = new URLSearchParams({
            title: title,
            custom_slug: customSlug,
            course_id: currentCourseId
        });

        statusText.textContent = "Checking availability...";
        statusText.className = "text-xs font-medium text-gray-400";

        // Replace the hardcoded {% url %} string with the global variable
        const previewUrl = window.SLUG_PREVIEW_URL || '/courses/api/generate-slug-preview/';

        fetch(`${previewUrl}?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                if (!data.is_valid) {
                    if (updateInputValue) slugInput.value = "";
                    statusText.textContent = data.message;
                    statusText.className = "text-xs font-medium text-amber-400";
                    return;
                }

                if (updateInputValue) {
                    slugInput.value = data.slug;
                }

                if (data.was_modified_for_uniqueness) {
                    statusText.textContent = `Note: Base slug was already taken. Adjusted to "${data.slug}"`;
                    statusText.className = "text-xs font-medium text-amber-400";
                } else {
                    statusText.textContent = `✓ URL will be: /course/${data.slug}/`;
                    statusText.className = "text-xs font-medium text-emerald-400";
                }
            })
            .catch(() => {
                statusText.textContent = "";
            });
    }

    // 3. Listen to Title input (with 350ms Debounce)
    titleInput.addEventListener("input", function () {
        if (isSlugManuallyEdited) return;

        clearTimeout(debounceTimer);
        const currentTitle = this.value.trim();

        if (!currentTitle) {
            slugInput.value = "";
            statusText.textContent = "";
            return;
        }

        debounceTimer = setTimeout(() => {
            fetchSmartSlug({ title: currentTitle, updateInputValue: true });
        }, 1000);
    });

    // 4. Listen to manual typing inside Custom URL Slug (enforce slug format live)
    slugInput.addEventListener("input", function () {
        isSlugManuallyEdited = true;

        // Live formatting: lowercase, spaces to hyphens, strip invalid characters except Arabic/English/numbers/hyphens
        let formatted = this.value
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9\u0600-\u06FF\-]/g, "")
            .replace(/\-+/g, "-");

        this.value = formatted;

        clearTimeout(debounceTimer);
        if (!formatted) {
            statusText.textContent = "Leave empty to auto-generate from title.";
            statusText.className = "text-xs font-medium text-gray-400";
            return;
        }

        debounceTimer = setTimeout(() => {
            // Validate & transliterate if user typed Arabic inside the slug box, and check uniqueness
            fetchSmartSlug({ title: titleInput.value, customSlug: formatted, updateInputValue: true });
        }, 400);
    });

    // 5. Reset / Auto button click: re-link to Title and regenerate immediately
    resetBtn.addEventListener("click", function () {
        isSlugManuallyEdited = false;
        if (titleInput.value.trim()) {
            fetchSmartSlug({ title: titleInput.value.trim(), updateInputValue: true });
        } else {
            slugInput.value = "";
            statusText.textContent = "";
        }
    });
});
