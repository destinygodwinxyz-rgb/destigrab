from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
from urllib.parse import urlparse

app = Flask(__name__)

DOWNLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "downloads"
)

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# =========================================================
# URL VALIDATION
# =========================================================

def is_valid_url(url):
    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ["http", "https"]
            and bool(parsed.netloc)
        )

    except Exception:
        return False


# =========================================================
# YOUTUBE / YT-DLP OPTIONS
# =========================================================

def get_ydl_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "tv",
                    "android_vr",
                    "web_embedded"
                ]
            }
        }
    }


# =========================================================
# PLATFORM DETECTION
# =========================================================

def detect_platform(url):

    if not is_valid_url(url):
        return None

    try:

        options = get_ydl_options()

        options["skip_download"] = True

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        extractor = (
            info.get("extractor_key")
            or info.get("extractor")
            or "Web"
        )

        return extractor

    except Exception as e:

        print(
            "DETECT ERROR:",
            repr(e)
        )

        return None


# =========================================================
# GET VIDEO INFORMATION
# =========================================================

def get_video_info(url):

    if not is_valid_url(url):
        raise ValueError(
            "Invalid URL."
        )

    options = get_ydl_options()

    options["skip_download"] = True

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

    thumbnail = info.get(
        "thumbnail"
    )

    available_heights = set()

    for fmt in info.get(
        "formats",
        []
    ):

        height = fmt.get(
            "height"
        )

        if height and height >= 144:

            available_heights.add(
                height
            )

    available_heights = sorted(
        available_heights
    )

    preferred_qualities = [
        360,
        480,
        720,
        1080,
        1440,
        2160
    ]

    qualities = []

    for quality in preferred_qualities:

        if any(
            height >= quality
            for height in available_heights
        ):

            qualities.append(
                quality
            )

    if not qualities and available_heights:

        qualities = [
            available_heights[-1]
        ]

    platform = (
        info.get("extractor_key")
        or info.get("extractor")
        or "Web"
    )

    return {

        "title": info.get(
            "title",
            "Untitled video"
        ),

        "thumbnail": thumbnail,

        "duration": info.get(
            "duration"
        ),

        "platform": platform,

        "qualities": qualities
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# PREVIEW
# =========================================================

@app.route(
    "/preview",
    methods=["POST"]
)
def preview():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    url = data.get(
        "url",
        ""
    ).strip()

    if not url:

        return jsonify({

            "success": False,

            "error":
                "Paste a video link first."

        }), 400

    try:

        info = get_video_info(
            url
        )

        return jsonify({

            "success": True,

            "video": info

        })

    except Exception as e:

        print(
            "PREVIEW ERROR:",
            repr(e)
        )

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 400


# =========================================================
# DETECT
# =========================================================

@app.route(
    "/detect",
    methods=["POST"]
)
def detect():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    url = data.get(
        "url",
        ""
    ).strip()

    if not is_valid_url(url):

        return jsonify({

            "success": False,

            "platform": None

        })

    platform = detect_platform(
        url
    )

    if platform:

        return jsonify({

            "success": True,

            "platform": platform

        })

    return jsonify({

        "success": False,

        "platform": None

    })


# =========================================================
# DOWNLOAD
# =========================================================

@app.route(
    "/download",
    methods=["POST"]
)
def download():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    url = data.get(
        "url",
        ""
    ).strip()

    quality = str(
        data.get(
            "quality",
            "720"
        )
    )

    if not url:

        return jsonify({

            "success": False,

            "error":
                "No video link provided."

        }), 400

    if not is_valid_url(url):

        return jsonify({

            "success": False,

            "error":
                "Invalid video URL."

        }), 400

    allowed_qualities = [
        "360",
        "480",
        "720",
        "1080",
        "1440",
        "2160"
    ]

    if quality not in allowed_qualities:

        quality = "720"

    file_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_FOLDER,
        f"{file_id}.%(ext)s"
    )

    ydl_opts = get_ydl_options()

    ydl_opts.update({

        "outtmpl":
            output_template,

        "merge_output_format":
            "mp4",

        "format":
            (
                f"bestvideo[height<={quality}]"
                f"+bestaudio/"
                f"best[height<={quality}]"
                f"/best"
            )
    })

    try:

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = None

            requested_downloads = (
                info.get(
                    "requested_downloads"
                )
                or []
            )

            for item in requested_downloads:

                filepath = item.get(
                    "filepath"
                )

                if (
                    filepath
                    and os.path.exists(
                        filepath
                    )
                ):

                    filename = os.path.basename(
                        filepath
                    )

                    break

            # Check merged file
            if not filename:

                prepared = (
                    ydl.prepare_filename(
                        info
                    )
                )

                base = os.path.splitext(
                    prepared
                )[0]

                possible_files = [

                    base + ".mp4",

                    base + ".webm",

                    base + ".mkv",

                    base + ".m4a"

                ]

                for file in possible_files:

                    if os.path.exists(file):

                        filename = os.path.basename(
                            file
                        )

                        break

        if not filename:

            return jsonify({

                "success": False,

                "error":
                    "Download completed but "
                    "the file could not be located."

            }), 500

        return jsonify({

            "success": True,

            "filename":
                filename,

            "download_url":
                f"/file/{filename}"

        })

    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            repr(e)
        )

        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


# =========================================================
# SERVE DOWNLOADED FILE
# =========================================================

@app.route(
    "/file/<path:filename>"
)
def serve_file(filename):

    return send_from_directory(

        DOWNLOAD_FOLDER,

        filename,

        as_attachment=True

    )


# =========================================================
# START DESTIGRAB
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "==================================="
    )
    print(
        "       🚀 DESTIGRAB UNIVERSAL"
    )
    print(
        "==================================="
    )
    print(
        "Multi-platform downloader engine"
    )
    print(
        "YouTube client fallback enabled"
    )
    print(
        "Local: http://127.0.0.1:5000"
    )
    print("")

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )
