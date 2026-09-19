const videoUrl = document.getElementById("videoUrl");
const previewBtn = document.getElementById("previewBtn");
const clearBtn = document.getElementById("clearBtn");

const platformStatus = document.getElementById("platformStatus");
const previewSection = document.getElementById("previewSection");

const videoThumbnail = document.getElementById("videoThumbnail");
const videoTitle = document.getElementById("videoTitle");
const durationBadge = document.getElementById("durationBadge");
const detectedPlatform = document.getElementById("detectedPlatform");

const qualitySelect = document.getElementById("qualitySelect");
const downloadBtn = document.getElementById("downloadBtn");
const downloadStatus = document.getElementById("downloadStatus");


/* -------------------------
   Helpers
------------------------- */

function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) {
        return "00:00";
    }

    seconds = Math.floor(seconds);

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }

    return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}


function setStatus(message, type = "") {
    platformStatus.innerHTML = `
        <span class="status-dot"></span>
        ${message}
    `;

    platformStatus.className = "platform-status";

    if (type) {
        platformStatus.classList.add(type);
    }
}


/* -------------------------
   Automatic platform detection
------------------------- */

async function detectPlatform() {

    const url = videoUrl.value.trim();

    if (!url) {
        setStatus("Waiting for a link...");
        return;
    }

    try {

        const response = await fetch("/detect", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url
            })
        });

        const data = await response.json();

        if (data.success) {

            setStatus(`${data.platform} link detected`);

        } else {

            setStatus("Platform not supported");

        }

    } catch (error) {

        setStatus("Ready");

    }
}


/* -------------------------
   Detect while typing
------------------------- */

let detectTimer;

videoUrl.addEventListener("input", () => {

    clearTimeout(detectTimer);

    detectTimer = setTimeout(() => {
        detectPlatform();
    }, 350);

});


/* -------------------------
   Clear input
------------------------- */

clearBtn.addEventListener("click", () => {

    videoUrl.value = "";

    previewSection.classList.add("hidden");

    downloadStatus.textContent = "";

    setStatus("Waiting for a link...");

    videoUrl.focus();

});


/* -------------------------
   Fetch video preview
------------------------- */

previewBtn.addEventListener("click", async () => {

    const url = videoUrl.value.trim();

    if (!url) {

        setStatus("Paste a video link first.");

        videoUrl.focus();

        return;
    }


    previewBtn.disabled = true;
    previewBtn.classList.add("loading");

    setStatus("Fetching video information...");

    previewSection.classList.add("hidden");


    try {

        const response = await fetch("/preview", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                url: url
            })

        });


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error || "Unable to read this video."
            );

        }


        const video = data.video;


        /* Thumbnail */

const thumbnailFallback = document.getElementById("thumbnailFallback");

if (video.thumbnail) {
    videoThumbnail.src = video.thumbnail;
    videoThumbnail.style.display = "block";

    if (thumbnailFallback) {
        thumbnailFallback.style.display = "none";
    }
} else {
    videoThumbnail.removeAttribute("src");
    videoThumbnail.style.display = "none";

    if (thumbnailFallback) {
        thumbnailFallback.style.display = "flex";
    }
}


        /* Title */

        videoTitle.textContent =
            video.title || "Untitled video";


        /* Duration */

        durationBadge.textContent =
            formatDuration(video.duration);


        /* Platform */

        detectedPlatform.textContent =
            video.platform || "Video";


        /* Quality */

        qualitySelect.innerHTML = "";


        const qualities = video.qualities || [];


        if (qualities.length === 0) {

            qualitySelect.innerHTML = `
                <option value="720">Best available</option>
            `;

        } else {

            qualities.forEach((quality) => {

                const option =
                    document.createElement("option");

                option.value = quality;
                option.textContent = `${quality}p`;

                if (quality === 720) {
                    option.selected = true;
                }

                qualitySelect.appendChild(option);

            });

        }


        /* Show preview */

        previewSection.classList.remove("hidden");

        setStatus(
            `${video.platform} video ready`
        );

        downloadStatus.textContent = "";


        /* Smooth scroll */

        setTimeout(() => {

            previewSection.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        }, 150);


    } catch (error) {

        console.error(error);

        setStatus(
            "Couldn't read this link."
        );

        previewSection.classList.add("hidden");

    } finally {

        previewBtn.disabled = false;
        previewBtn.classList.remove("loading");

    }

});


/* -------------------------
   Download
------------------------- */

downloadBtn.addEventListener("click", async () => {

    const url = videoUrl.value.trim();
    const quality = qualitySelect.value;


    if (!url) {

        downloadStatus.textContent =
            "Paste a video link first.";

        return;
    }


    downloadBtn.disabled = true;

    downloadStatus.textContent =
        `Preparing ${quality}p download...`;


    try {

        const response = await fetch("/download", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                url: url,
                quality: quality
            })

        });


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error || "Download failed."
            );

        }


        downloadStatus.textContent =
            "Download ready — starting...";


        /* Start browser download */

        const link =
            document.createElement("a");

        link.href = data.download_url;

        link.download = "";

        document.body.appendChild(link);

        link.click();

        link.remove();


        setTimeout(() => {

            downloadStatus.textContent =
                "✓ Download started successfully.";

        }, 1000);


    } catch (error) {

        console.error(error);

        downloadStatus.textContent =
            error.message ||
            "Something went wrong.";

    } finally {

        downloadBtn.disabled = false;

    }

});
