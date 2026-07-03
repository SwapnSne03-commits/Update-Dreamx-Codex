import re
import time
import asyncio

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery
)

# -----------------------------
# Smart Filter Cache
# -----------------------------

FILTER_CACHE = {}

CACHE_EXPIRE = 1800      # 30 Minutes
_CLEANER_STARTED = False

def create_session(key: str, query: str, files: list, user_id: int):
    """
    Create a new smart filter session.
    """

    FILTER_CACHE[key] = {
        "query": query,
        "current_query": query,
        "all_files": list(files),
        "current_files": list(files),

        "user_id": user_id,
        
        "selected": {
            "season": None,
            "language": None,
            "quality": None,
            "combined": None,
        },

        "available": {
            "season": [],
            "language": [],
            "quality": [],
            "combined": [],
            "filtered_files": [],
        },

        "created": time.time(),
        "updated": time.time()
    }


def get_session(key: str):

    data = FILTER_CACHE.get(key)

    if not data:
        return None

    data["updated"] = time.time()

    return data


def delete_session(key: str):

    FILTER_CACHE.pop(key, None)


def touch_session(key: str):

    if key in FILTER_CACHE:
        FILTER_CACHE[key]["updated"] = time.time()

async def cache_cleaner():

    while True:

        now = time.time()

        remove = []

        for key, value in list(FILTER_CACHE.items()):

            if now - value["updated"] > CACHE_EXPIRE:

                remove.append(key)

        for key in remove:

            FILTER_CACHE.pop(key, None)

        await asyncio.sleep(300)

def start_cache_cleaner(loop):
    global _CLEANER_STARTED

    if _CLEANER_STARTED:
        return

    _CLEANER_STARTED = True
    loop.create_task(cache_cleaner())

# -----------------------------
# Season Detection
# -----------------------------

SEASON_PATTERNS = [

    # S01 / S1 / s03
    re.compile(r"\bS(?:EASON)?[\s._-]?(\d{1,2})\b", re.IGNORECASE),

    # Season 1 / Season-01
    re.compile(r"\bSEASON[\s._-]?(\d{1,2})\b", re.IGNORECASE),

    # S01E05 / S1E8
    re.compile(r"\bS(\d{1,2})[\s._-]?E\d{1,3}\b", re.IGNORECASE),

]

def normalize_season(season: int | str):

    try:
        season = int(season)
        return f"S{season:02d}"
    except:
        return None
  
def extract_season(filename: str):

    """
    Return:
        S01
        S02
        ...
        None
    """

    if not filename:
        return None

    for pattern in SEASON_PATTERNS:

        match = pattern.search(filename)

        if match:

            return normalize_season(match.group(1))

    return None

# -----------------------------
# Quality Detection
# -----------------------------

QUALITY_PATTERNS = {
    "2160p": [
        r"\b2160p\b",
        r"\b4k\b",
        r"\buhd\b"
    ],

    "1440p": [
        r"\b1440p\b"
    ],

    "1080p": [
        r"\b1080p\b",
        r"\b1080\b"
    ],

    "720p": [
        r"\b720p\b",
        r"\b720\b"
    ],

    "480p": [
        r"\b480p\b",
        r"\b480\b"
    ],

    "360p": [
        r"\b360p\b",
        r"\b360\b"
    ],

    "240p": [
        r"\b240p\b",
        r"\b240\b"
    ]
}


def extract_quality(filename: str):

    """
    Return:
        2160p
        1080p
        720p
        ...
        None
    """

    if not filename:
        return None

    filename = filename.lower()

    for quality, patterns in QUALITY_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, filename, re.IGNORECASE):
                return quality

    return None

# -----------------------------
# Language Detection
# -----------------------------

LANGUAGE_PATTERNS = {

    "Hindi": [
        r"\bhindi\b",
        r"\bhin\b",
        r"\bhind\b"
    ],

    "English": [
        r"\benglish\b",
        r"\beng\b",
        r"\bengl\b",
        r"\bengli\b"
    ],

    "Bengali": [
        r"\bbengali\b",
        r"\bbangla\b",
        r"\bbeng\b",
        r"\bbang\b"
    ],

    "Tamil": [
        r"\btamil\b",
        r"\btam\b"
    ],

    "Telugu": [
        r"\btelugu\b",
        r"\btel\b"
    ],

    "Malayalam": [
        r"\bmalayalam\b",
        r"\bmal\b",
        r"\bmalayali\b",
        r"\bmalaya\b"
    ],

    "Kannada": [
        r"\bkannada\b",
        r"\bkan\b"
    ],

    "Marathi": [
        r"\bmarathi\b",
        r"\bmar\b"
    ],

    "Punjabi": [
        r"\bpunjabi\b",
        r"\bpun\b"
    ],

    "Gujarati": [
        r"\bgujarati\b"
    ],

    "Bhojpuri": [
        r"\bbhojpuri\b"
    ],

    "Korean": [
        r"\bkorean\b",
        r"\bkor\b"
    ],

    "Japanese": [
        r"\bjapanese\b",
        r"\bjap\b"
    ],

    "Chinese": [
        r"\bchinese\b",
        r"\bchi\b",
    ],

    "French": [
        r"\bfrench\b"
    ],

    "Spanish": [
        r"\bspanish\b"
    ]
}

DISPLAY_NAMES = {
    "Hindi": "ʜɪɴᴅɪ",
    "English": "ᴇɴɢʟɪsʜ",
    "Tamil": "ᴛᴀᴍɪʟ",
    "Telugu": "ᴛᴇʟᴜɢᴜ",
    "Malayalam": "ᴍᴀʟᴀʏᴀʟᴀᴍ",
    "Bengali": "ʙᴇɴɢᴀʟɪ",
    "Korean": "ᴋᴏʀᴇᴀɴ",
    "Japanese": "ᴊᴀᴘᴀɴᴇsᴇ",
    "Chinese": "ᴄʜɪɴᴇsᴇ",
    "Marathi": "ᴍᴀʀᴀᴛʜɪ",
    "Punjabi": "ᴘᴜɴᴊᴀʙɪ",
    "Kannada": "ᴋᴀɴɴᴀᴅᴀ",
    "Dual Audio": "ᴅᴜᴀʟ ᴀᴜᴅɪᴏ",
    "Multi Audio": "ᴍᴜʟᴛɪ ᴀᴜᴅɪᴏ",
    "Combined": "ᴄᴏᴍʙɪɴᴇᴅ",
}

LANGUAGE_SEARCH = {
    "hindi": "hin",
    "english": "eng",
    "bengali": "ben",
    "tamil": "tam",
    "telugu": "tel",
    "korean": "kor",
    "japanese": "jap", 
    "malayalam": "mal",
    "chinese": "chin",
    "kannada": "kan",
    "dual audio": "dual",
    "multi audio": "multi",
}

SPECIAL_LANGUAGE_PATTERNS = {

    "Dual Audio": [
        r"dual[\s\-]?audio",
        r"dual"
    ],

    "Multi Audio": [
        r"multi[\s\-]?audio",
        r"multi[\s\-]?lang",
        r"multi"
    ]
}


def extract_languages(filename: str):

    """
    Returns:
        ["Hindi"]

        ["Hindi","English"]

        ["Dual Audio","Hindi","English"]

        ["Multi Audio","Hindi","Tamil","Telugu"]
    """

    if not filename:
        return []

    filename = filename.lower()

    found = []

    for special, patterns in SPECIAL_LANGUAGE_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, filename):

                found.append(special)

                break

    for language, patterns in LANGUAGE_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, filename):

                found.append(language)

                break

    return list(dict.fromkeys(found))

COMBINED_PATTERNS = [
    r"\bcombine\b",
    r"\bcombined\b",
    r"\bcomplete\s*series\b",
]

def extract_combined(filename: str):

    if not filename:
        return False

    filename = filename.lower()

    for pattern in COMBINED_PATTERNS:
        if re.search(pattern, filename):
            return True

    return False
    
# -----------------------------
# Build Available Filters
# -----------------------------

def build_available_filters(key: str):

    session = get_session(key)

    if not session:
        return

    seasons = set()
    qualities = set()
    languages = set()
    combined = set()

    for file in session["all_files"]:

        filename = getattr(file, "file_name", "") or ""

        # Season
        season = extract_season(filename)
        if season:
            seasons.add(season)

        # Quality
        quality = extract_quality(filename)
        if quality:
            qualities.add(quality)

        if extract_combined(filename):
            combined.add("Combined")
        # Language
        langs = extract_languages(filename)
        for lang in langs:
            languages.add(lang)

    session["available"]["season"] = sorted(
        seasons,
        key=lambda x: int(x[1:])
    )

    session["available"]["quality"] = sorted(
        qualities,
        key=lambda x: int(x.replace("p", "")),
        reverse=True
    )

    session["available"]["language"] = sorted(languages)
    session["available"]["combined"] = sorted(combined)

def refresh_available_filters(key: str):

    build_available_filters(key)

    touch_session(key)

# -----------------------------
# Keyboard Builder
# -----------------------------

FILTER_NAMES = {

    "season": "Season",

    "language": "Language",

    "quality": "Quality",

    "combined": "Combined",

}

def build_main_filter_buttons(key):

    session = get_session(key)

    rows = [
        [
            InlineKeyboardButton(
                "📺 Season",
                callback_data=f"sf:season:{key}"
            ),
            InlineKeyboardButton(
                "🌐 Language",
                callback_data=f"sf:language:{key}"
            ),
            InlineKeyboardButton(
                "🎥 Quality",
                callback_data=f"sf:quality:{key}"
            )
        ]
    ]

    if (
        session
        and session["available"]["combined"]
    ):
        rows.append([
            InlineKeyboardButton(
                "📦 Combined",
                callback_data=f"sf:combined:{key}"
            )
        ])

    return rows

def build_filter_keyboard(key: str, filter_name: str):

    session = get_session(key)

    if not session:
        return InlineKeyboardMarkup([])

    rows = []

    values = session["available"].get(filter_name, [])

    TITLE_TEXT = {
        "season": "⤋ ᴄʜᴏᴏsᴇ sᴇᴀsᴏɴ ⤋",
        "language": "⤋ ᴄʜᴏᴏsᴇ ʟᴀɴɢᴜᴀɢᴇ ⤋",
        "quality": "⤋ ᴄʜᴏᴏsᴇ ǫᴜᴀʟɪᴛʏ ⤋",
        "combined": "⤋ ᴄʜᴏᴏsᴇ ᴄᴏᴍʙɪɴᴇᴅ ⤋",
    }

    rows.append([
        InlineKeyboardButton(
            text=TITLE_TEXT.get(filter_name, "Choose Filter"),
            callback_data="sf:header"
        )
    ])

    for i in range(0, len(values), 2):

        row = []

        for j in (0, 1):

            if i + j >= len(values):
                break

            value = values[i + j]

            text = DISPLAY_NAMES.get(value, value)

            selected = session["selected"].get(filter_name)

            if selected == value:
                text = f"✅ {text}"
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"sf:set:{filter_name}:{i+j}:{key}"
                )
            )

        rows.append(row)

    # Back button
    rows.append([
        InlineKeyboardButton(
            "⤝ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ",
            callback_data=f"sf:main:{key}"
        )
    ])

    return InlineKeyboardMarkup(rows)

def get_filter_value(key: str, filter_name: str, index: int):

    session = get_session(key)

    if not session:
        return None

    values = session["available"].get(filter_name, [])

    if index < 0 or index >= len(values):
        return None

    return values[index]


def session_exists(key: str):

    return key in FILTER_CACHE

# -----------------------------
# Filter State
# -----------------------------

def set_filter(key: str, filter_name: str, value):

    session = get_session(key)

    if not session:
        return

    for name in session["selected"]:
        session["selected"][name] = None

    session["selected"][filter_name] = value

    touch_session(key)

def clear_filters(key: str):

    session = get_session(key)

    if not session:
        return

    session["selected"] = {

        "season": None,

        "language": None,

        "quality": None

    }

    session["current_files"] = list(session["all_files"])

    touch_session(key)

def get_selected_filters(key: str):

    session = get_session(key)

    if not session:
        return None

    return session["selected"]

def apply_filters(key: str):

    session = get_session(key)

    if not session:
        return []

    season = session["selected"]["season"]
    language = session["selected"]["language"]
    quality = session["selected"]["quality"]
    combined = session["selected"]["combined"]

    filtered = []

    for file in session["all_files"]:

        filename = getattr(file, "file_name", "") or ""

        # Season
        if season:

            if extract_season(filename) != season:
                continue

        # Language
        if language:

            langs = extract_languages(filename)

            if language not in langs:
                continue

        # Quality
        if quality:

            if extract_quality(filename) != quality:
                continue

        # Combined
        if combined:

            if not extract_combined(filename):
                continue

        filtered.append(file)

    session["current_files"] = filtered

    touch_session(key)

    return filtered

def build_search_query(key: str):
    """
    Build search query using the main query
    and only one active filter.
    """

    session = get_session(key)

    if not session:
        return None

    query = session["query"].strip()

    parts = [query]

    for value in session["selected"].values():

        if not value:
            continue

        value = value.strip()

        if value.lower() in LANGUAGE_SEARCH:
            value = LANGUAGE_SEARCH[value.lower()]
        # Prevent duplicate words
        if value.lower() not in query.lower():
            parts.append(value)

        break

    return " ".join(parts)

def get_current_files(key: str):

    session = get_session(key)

    if not session:
        return []

    return session["current_files"]

# -----------------------------
# Callback Prefix
# -----------------------------

CALLBACK_PREFIX = "sf"

async def handle_main(client, query, data):

    key = data[2]

    session = get_session(key)

    if not session:

        await query.answer(
            "Session Expired.",
            show_alert=True
        )

        return True

    session["current_query"] = session["query"]
    session["selected"] = {
        "season": None,
        "language": None,
        "quality": None,
    }
    await query.answer()

    return {
        "type": "main",
        "search": session["query"],
        "key": key,
    }

async def handle_menu(client, query, data):

    filter_name = data[1]

    key = data[2]

    session = get_session(key)

    if not session:

        await query.answer(
            "sᴀssɪᴏɴ ᴇxᴘɪʀᴇᴅ, sᴇᴀʀᴄʜ ᴀɢᴀɪɴ",
            show_alert=True
        )

        return True

    values = session["available"].get(filter_name, [])

    if not values:

        await query.answer(
            f"{filter_name.title()} ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜɪs ʀᴇsᴜʟᴛ.",
            show_alert=True
        )

        return True

    await query.message.edit_reply_markup(

        build_filter_keyboard(
            key,
            filter_name
        )

    )

    await query.answer()

    return True

async def handle_set(client, query, data):

    filter_name = data[2]

    try:
        index = int(data[3])
    except:
        await query.answer("Invalid Filter")
        return True

    key = data[4]

    if not session_exists(key):

        await query.answer(
            "Session Expired.",
            show_alert=True
        )
        return True

    value = get_filter_value(
        key,
        filter_name,
        index
    )

    if value is None:

        await query.answer(
            "Invalid Filter",
            show_alert=True
        )
        return True

    # Apply Filter
    # Save Selected Filter
    set_filter(
        key,
        filter_name,
        value
    )

    if filter_name == "combined":

        files = apply_filters(key)

        session = get_session(key)

        if session:
            session["filtered_files"] = files
        return {
            "type": "combined",
            "files": files[:10],
            "all_files": files,
            "offset": 0,
            "key": key,
        }

    # Build New Search Query
    search = build_search_query(key)

    session = get_session(key)

    if session:
        session["current_query"] = search

    await query.answer(
        f"ғɪʟᴛᴇʀɪɴɢ..."
    )

    # Next Step:
    # pmfilter.py will perform get_search_results(search)

    return {
        "search": search,
        "key": key,
    }

def has_active_filters(key: str):

    session = get_session(key)

    if not session:
        return False

    return any(session["selected"].values())

def active_filter_count(key: str):

    session = get_session(key)

    if not session:
        return 0

    return sum(
        value is not None
        for value in session["selected"].values()
    )

def get_active_filters(key: str):

    session = get_session(key)

    if not session:
        return {}

    return {

        k: v

        for k, v in session["selected"].items()

        if v is not None

    }

def reset_current_files(key: str):

    session = get_session(key)

    if not session:
        return []

    session["current_files"] = list(
        session["all_files"]
    )

    touch_session(key)

    return session["current_files"]


async def handle_back(client, query, data):
    pass

# -----------------------------
# Callback Dispatcher
# -----------------------------

async def handle_callback(client, query):

    if not query.data.startswith("sf:"):
        return False

    parts = query.data.split(":")

    key = parts[-1]

    session = get_session(key)

    if session:

        owner = session.get("user_id")

        if owner and owner != query.from_user.id:

            await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ. ᴅᴏ ʏᴏᴜʀs !!",
                show_alert=True
            )

            return True
    action = parts[1]

    if action == "main":

        return await handle_main(client, query, parts)

    elif action in ("season", "language", "quality", "combined",):

        return await handle_menu(client, query, parts)

    elif action == "set":

        return await handle_set(client, query, parts)

    elif action == "header":
        await query.answer()
        return True

    elif action == "none":

        await query.answer(
            "No filter available.",
            show_alert=True
        )
        return True

    return False
