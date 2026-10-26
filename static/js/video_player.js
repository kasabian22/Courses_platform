/**
 * Custom HTML5 Video Player
 * Features: custom controls, timeline hover preview, hotkeys, volume/mute, speed selection, and PiP/Fullscreen.
 */
function initCustomVideoPlayers() {
    document.querySelectorAll('[data-video-player]').forEach((player) => {
        if (player.dataset.playerInitialized) return;
        player.dataset.playerInitialized = 'true';

        const q = (sel) => player.querySelector(sel);
        const video = q('[data-video]');
        const centerPlay = q('[data-center-play]');
        const playButton = q('[data-play]');
        const playIcon = q('[data-icon-play]');
        const pauseIcon = q('[data-icon-pause]');
        const controlsBar = q('[data-controls-bar]');
        const timeline = q('[data-timeline]');
        const seek = q('[data-seek]');
        const seekTooltip = q('[data-seek-tooltip]');
        const timeToggle = q('[data-time-toggle]');
        const currentTime = q('[data-current-time]');
        const duration = q('[data-duration]');
        const muteButton = q('[data-mute]');
        const soundIcon = q('[data-icon-sound]');
        const mutedIcon = q('[data-icon-muted]');
        const volume = q('[data-volume]');
        const pipButton = q('[data-pip]');
        const fullscreenButton = q('[data-fullscreen]');
        const speedControl = q('[data-speed-control]');
        const speedButton = q('[data-speed-button]');
        const speedMenu = q('[data-speed-menu]');

        if (!video || !centerPlay || !playButton || !timeline || !seek || !seekTooltip || !timeToggle || !currentTime || !duration) return;

        let showRemainingTime = false;
        let controlsTimeout = null;

        // Controls Auto-Hide
        const hideControls = () => {
            if (!video.paused && !video.ended && speedMenu?.classList.contains('hidden') !== false && !seek.matches(':active') && !volume?.matches(':active')) {
                controlsBar?.classList.add('opacity-0', 'pointer-events-none');
                player.classList.add('cursor-none');
            }
        };

        const showControls = () => {
            controlsBar?.classList.remove('opacity-0', 'pointer-events-none');
            player.classList.remove('cursor-none');
            clearTimeout(controlsTimeout);
            if (!video.paused && !video.ended && speedMenu?.classList.contains('hidden') !== false) {
                controlsTimeout = setTimeout(hideControls, 2500);
            }
        };

        ['pointermove', 'pointerdown', 'focusin'].forEach(evt => player.addEventListener(evt, showControls));
        player.addEventListener('pointerleave', () => { if (!video.paused && !video.ended) hideControls(); });

        // Time formatting (M:SS or H:MM:SS)
        const formatTime = (secs) => {
            if (!Number.isFinite(secs) || secs < 0) return '0:00';
            const t = Math.floor(secs);
            const h = Math.floor(t / 3600);
            const m = Math.floor((t % 3600) / 60);
            const s = String(t % 60).padStart(2, '0');
            return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`;
        };

        // Playback
        const togglePlayback = () => {
            if (video.paused || video.ended) {
                if (video.ended) video.currentTime = 0;
                video.play().catch(() => {});
            } else {
                video.pause();
            }
        };

        const updatePlaybackUI = () => {
            const playing = !video.paused && !video.ended;
            playIcon?.classList.toggle('hidden', playing);
            pauseIcon?.classList.toggle('hidden', !playing);
            centerPlay.classList.toggle('hidden', playing);
            const label = playing ? 'Pause video' : 'Play video';
            playButton.setAttribute('aria-label', label);
            centerPlay.setAttribute('aria-label', label);
            showControls();
        };

        [centerPlay, video].forEach(el => el.addEventListener('click', () => { player.focus(); togglePlayback(); }));
        playButton.addEventListener('click', togglePlayback);

        video.addEventListener('play', () => {
            document.querySelectorAll('video').forEach(v => { if (v !== video && !v.paused) v.pause(); });
            updatePlaybackUI();
        });
        ['pause', 'ended'].forEach(evt => video.addEventListener(evt, updatePlaybackUI));

        // Progress & Seek
        const updateSeekTrack = (pct) => {
            seek.style.background = `linear-gradient(to right, #795BFF 0%, #795BFF ${pct}%, rgba(255,255,255,0.22) ${pct}%, rgba(255,255,255,0.22) 100%)`;
        };

        const updateProgress = () => {
            const valid = Number.isFinite(video.duration) && video.duration > 0;
            const total = valid ? video.duration : 0;
            const cur = Number.isFinite(video.currentTime) ? video.currentTime : 0;
            currentTime.textContent = (showRemainingTime && valid) ? `-${formatTime(Math.max(0, total - cur))}` : formatTime(cur);
            duration.textContent = formatTime(total);
            const pct = valid ? Math.min(100, Math.max(0, (cur / total) * 100)) : 0;
            if (!seek.matches(':active')) seek.value = String(pct);
            updateSeekTrack(pct);
        };

        const updateTimeToggleLabel = () => {
            timeToggle.setAttribute('aria-label', showRemainingTime ? 'Show elapsed time' : 'Show remaining time');
            timeToggle.title = 'Switch between elapsed and remaining time';
        };

        timeToggle.addEventListener('click', () => {
            showRemainingTime = !showRemainingTime;
            updateProgress();
            updateTimeToggleLabel();
        });

        const updateSeekTooltip = (clientX = null) => {
            if (!Number.isFinite(video.duration) || video.duration <= 0) return;
            const sr = seek.getBoundingClientRect();
            const tr = timeline.getBoundingClientRect();
            const ratio = Math.min(1, Math.max(0, clientX !== null ? (clientX - sr.left) / sr.width : Number(seek.value) / 100));
            seekTooltip.textContent = formatTime(ratio * video.duration);
            const ptX = clientX !== null ? clientX : sr.left + ratio * sr.width;
            const pad = Math.min(40, tr.width / 2);
            seekTooltip.style.left = `${Math.max(pad, Math.min(tr.width - pad, ptX - tr.left))}px`;
            seekTooltip.classList.remove('hidden');
        };

        ['pointerenter', 'pointermove'].forEach(e => seek.addEventListener(e, ev => updateSeekTooltip(ev.clientX)));
        ['pointerleave', 'blur'].forEach(e => seek.addEventListener(e, () => seekTooltip.classList.add('hidden')));
        seek.addEventListener('focus', () => updateSeekTooltip());
        seek.addEventListener('input', () => {
            if (Number.isFinite(video.duration) && video.duration > 0) video.currentTime = (Number(seek.value) / 100) * video.duration;
            updateProgress();
            updateSeekTooltip();
        });
        ['loadedmetadata', 'durationchange', 'timeupdate'].forEach(e => video.addEventListener(e, updateProgress));

        // Volume
        const updateVolumeUI = () => {
            const muted = video.muted || video.volume === 0;
            soundIcon?.classList.toggle('hidden', muted);
            mutedIcon?.classList.toggle('hidden', !muted);
            muteButton?.setAttribute('aria-label', muted ? 'Turn on sound' : 'Mute sound');
            if (volume && !volume.matches(':active')) volume.value = String(muted ? 0 : video.volume);
        };

        muteButton?.addEventListener('click', () => {
            video.muted = !video.muted && video.volume > 0;
            if (!video.muted && video.volume === 0) video.volume = 0.7;
            updateVolumeUI();
        });
        volume?.addEventListener('input', () => {
            video.volume = Number(volume.value);
            video.muted = video.volume === 0;
            updateVolumeUI();
        });
        video.addEventListener('volumechange', updateVolumeUI);

        // Speed Menu
        const setSpeedMenuOpen = (open) => {
            if (!speedMenu || !speedButton) return;
            speedMenu.classList.toggle('hidden', !open);
            speedButton.setAttribute('aria-expanded', String(open));
            showControls();
        };

        const setPlaybackRate = (rate) => {
            video.playbackRate = rate;
            if (speedButton) {
                speedButton.textContent = `${rate}×`;
                speedButton.setAttribute('aria-label', `Video playback speed ${rate}×`);
            }
            speedMenu?.querySelectorAll('button[data-speed]').forEach((opt) => {
                const active = Number(opt.dataset.speed) === rate;
                opt.classList.toggle('bg-violet-600/20', active);
                opt.classList.toggle('text-violet-200', active);
                opt.classList.toggle('text-gray-200', !active);
                opt.setAttribute('aria-pressed', String(active));
            });
        };

        speedButton?.addEventListener('click', (e) => { e.stopPropagation(); setSpeedMenuOpen(speedMenu.classList.contains('hidden')); });
        speedMenu?.addEventListener('click', (e) => {
            const opt = e.target.closest('button[data-speed]');
            const rate = Number(opt?.dataset.speed);
            if (Number.isFinite(rate) && rate > 0) {
                setPlaybackRate(rate);
                setSpeedMenuOpen(false);
            }
        });
        document.addEventListener('click', (e) => { if (speedControl && !speedControl.contains(e.target)) setSpeedMenuOpen(false); });

        // PiP
        if (document.pictureInPictureEnabled && video.requestPictureInPicture) {
            pipButton?.addEventListener('click', async () => {
                try {
                    document.pictureInPictureElement === video ? await document.exitPictureInPicture() : await video.requestPictureInPicture();
                } catch {}
            });
            video.addEventListener('enterpictureinpicture', () => {
                pipButton?.classList.add('text-violet-400');
                pipButton?.setAttribute('aria-label', 'Exit picture in picture');
            });
            video.addEventListener('leavepictureinpicture', () => {
                pipButton?.classList.remove('text-violet-400');
                pipButton?.setAttribute('aria-label', 'Picture in picture');
            });
        } else if (pipButton) {
            pipButton.classList.add('hidden');
        }

        // Fullscreen
        fullscreenButton?.addEventListener('click', async () => {
            try {
                if (document.fullscreenElement === player) await document.exitFullscreen();
                else if (player.requestFullscreen) await player.requestFullscreen();
                else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
            } catch {}
        });
        document.addEventListener('fullscreenchange', () => {
            fullscreenButton?.setAttribute('aria-label', document.fullscreenElement === player ? 'Exit full screen' : 'Full-screen view');
        });

        // Hotkeys
        player.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') return setSpeedMenuOpen(false);
            const tag = e.target.tagName?.toLowerCase();
            if (tag === 'textarea' || (tag === 'input' && e.target.type !== 'range')) return;

            const k = e.key;
            if (k === ' ' || k === 'k' || k === 'K') {
                if (tag === 'button' && k === ' ') return;
                e.preventDefault();
                togglePlayback();
                showControls();
            } else if (k === 'ArrowLeft' || k === 'ArrowRight') {
                e.preventDefault();
                if (Number.isFinite(video.duration)) {
                    video.currentTime = Math.max(0, Math.min(video.duration, video.currentTime + (k === 'ArrowRight' ? 5 : -5)));
                    updateProgress();
                    showControls();
                }
            } else if (k === 'ArrowUp' || k === 'ArrowDown') {
                e.preventDefault();
                const delta = k === 'ArrowUp' ? 0.1 : -0.1;
                video.volume = Math.max(0, Math.min(1, Math.round((video.volume + delta) * 10) / 10));
                video.muted = video.volume === 0;
                updateVolumeUI();
                showControls();
            } else if (k === 'm' || k === 'M') {
                e.preventDefault();
                video.muted = !video.muted && video.volume > 0;
                if (!video.muted && video.volume === 0) video.volume = 0.7;
                updateVolumeUI();
                showControls();
            } else if (k === 'f' || k === 'F') {
                e.preventDefault();
                fullscreenButton?.click();
                showControls();
            } else if (k === 'p' || k === 'P') {
                if (pipButton && !pipButton.classList.contains('hidden')) {
                    e.preventDefault();
                    pipButton.click();
                    showControls();
                }
            }
        });

        // Initial state
        updatePlaybackUI();
        updateProgress();
        updateTimeToggleLabel();
        updateVolumeUI();
        setPlaybackRate(video.playbackRate || 1);
    });
}

window.initCustomVideoPlayers = initCustomVideoPlayers;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomVideoPlayers);
} else {
    initCustomVideoPlayers();
}

