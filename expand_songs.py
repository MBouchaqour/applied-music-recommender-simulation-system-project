"""
expand_songs.py — Appends 10,000 realistic songs to data/songs.csv

Run from the project root:
    python expand_songs.py
"""

import csv
import os
import random

SEED = 42
random.seed(SEED)

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "songs.csv")
TARGET_NEW_ROWS = 10_000

# ── Genre config: moods + realistic parameter ranges ─────────────────────────

GENRES = {
    "lofi":       {"moods": ["chill","focused","relaxed","melancholic","nostalgic"],
                   "energy":(0.22,0.55),"tempo":(58,95),"valence":(0.40,0.75),
                   "danceability":(0.38,0.72),"acousticness":(0.62,0.95)},
    "pop":        {"moods": ["happy","euphoric","confident","joyful","nostalgic"],
                   "energy":(0.62,0.97),"tempo":(98,138),"valence":(0.62,0.97),
                   "danceability":(0.65,0.97),"acousticness":(0.03,0.38)},
    "rock":       {"moods": ["intense","angry","confident","moody"],
                   "energy":(0.72,0.98),"tempo":(118,168),"valence":(0.22,0.72),
                   "danceability":(0.42,0.78),"acousticness":(0.02,0.28)},
    "ambient":    {"moods": ["peaceful","chill","relaxed","melancholic","nostalgic"],
                   "energy":(0.07,0.38),"tempo":(45,78),"valence":(0.42,0.82),
                   "danceability":(0.14,0.46),"acousticness":(0.72,0.98)},
    "jazz":       {"moods": ["relaxed","moody","romantic","nostalgic","melancholic","confident"],
                   "energy":(0.27,0.68),"tempo":(70,122),"valence":(0.46,0.88),
                   "danceability":(0.40,0.75),"acousticness":(0.62,0.95)},
    "synthwave":  {"moods": ["moody","nostalgic","confident","intense","euphoric"],
                   "energy":(0.55,0.92),"tempo":(86,132),"valence":(0.36,0.72),
                   "danceability":(0.60,0.88),"acousticness":(0.02,0.32)},
    "hip-hop":    {"moods": ["confident","happy","angry","joyful","intense","moody"],
                   "energy":(0.62,0.95),"tempo":(76,118),"valence":(0.42,0.86),
                   "danceability":(0.72,0.98),"acousticness":(0.02,0.22)},
    "blues":      {"moods": ["melancholic","nostalgic","moody","relaxed"],
                   "energy":(0.20,0.62),"tempo":(56,102),"valence":(0.16,0.56),
                   "danceability":(0.32,0.68),"acousticness":(0.62,0.95)},
    "classical":  {"moods": ["peaceful","melancholic","nostalgic","romantic","focused"],
                   "energy":(0.07,0.52),"tempo":(40,108),"valence":(0.46,0.88),
                   "danceability":(0.10,0.40),"acousticness":(0.80,0.99)},
    "edm":        {"moods": ["euphoric","happy","intense","joyful","confident"],
                   "energy":(0.80,0.99),"tempo":(120,162),"valence":(0.62,0.97),
                   "danceability":(0.80,0.99),"acousticness":(0.01,0.10)},
    "country":    {"moods": ["nostalgic","happy","joyful","melancholic","romantic"],
                   "energy":(0.36,0.78),"tempo":(80,122),"valence":(0.56,0.92),
                   "danceability":(0.50,0.82),"acousticness":(0.50,0.88)},
    "r&b":        {"moods": ["romantic","happy","moody","nostalgic","confident","joyful"],
                   "energy":(0.40,0.82),"tempo":(66,108),"valence":(0.56,0.92),
                   "danceability":(0.62,0.92),"acousticness":(0.20,0.65)},
    "metal":      {"moods": ["angry","intense","confident"],
                   "energy":(0.85,0.99),"tempo":(136,188),"valence":(0.10,0.45),
                   "danceability":(0.35,0.72),"acousticness":(0.01,0.09)},
    "reggae":     {"moods": ["joyful","happy","relaxed","peaceful"],
                   "energy":(0.40,0.75),"tempo":(66,102),"valence":(0.70,0.97),
                   "danceability":(0.65,0.92),"acousticness":(0.40,0.82)},
    "dream pop":  {"moods": ["nostalgic","melancholic","romantic","peaceful","moody"],
                   "energy":(0.32,0.72),"tempo":(72,118),"valence":(0.46,0.82),
                   "danceability":(0.42,0.75),"acousticness":(0.30,0.72)},
    "soul":       {"moods": ["romantic","melancholic","nostalgic","happy","moody","joyful"],
                   "energy":(0.30,0.72),"tempo":(60,108),"valence":(0.46,0.88),
                   "danceability":(0.50,0.82),"acousticness":(0.36,0.78)},
    "indie pop":  {"moods": ["happy","nostalgic","romantic","joyful","moody","melancholic"],
                   "energy":(0.50,0.88),"tempo":(92,132),"valence":(0.56,0.92),
                   "danceability":(0.56,0.88),"acousticness":(0.16,0.58)},
}

# ── Title word banks (per-genre) ──────────────────────────────────────────────

TITLE_WORDS = {
    "lofi": {
        "A": ["Midnight","Rainy","Late","Quiet","Soft","Faded","Dusty","Slow","Hazy","Dim",
              "Warm","Cloudy","Dreamy","Gentle","Mellow","Sleepy","Still","Hollow","Faint",
              "Amber","Tender","Foggy","Lazy","Cozy","Golden","Distant","Washed","Blurry",
              "Grainy","Worn","Muted","Velvet","Smoky","Drowsy","Hushed","Frayed","Linen"],
        "B": ["Afternoon","Session","Tape","Rain","Hour","Cafe","Loop","Study","Page",
              "Window","Basement","Notepad","Coffee","Blanket","Vinyl","Room","Sunset",
              "Memory","Journal","Dusk","Corridor","Drift","Archive","Lamp","Bedroom",
              "Static","Fog","Corner","Porch","Attic","Nook","Aisle","Shelf","Bookshelf"],
    },
    "pop": {
        "A": ["Neon","Summer","Golden","Electric","Bright","Shining","Rising","Sparkling",
              "Vibrant","Brilliant","Sunrise","Wild","Free","Glowing","Dancing","Fast",
              "Happy","Radiant","Blazing","Loud","Fresh","Bold","Chasing","Rushing","Soaring",
              "Blinding","Dazzling","Fiery","Glittering","Shimmering","Cascading","Pulsing"],
        "B": ["Heart","Dream","Night","Day","Light","City","World","Star","Sky","Fire",
              "Beat","Pulse","Wave","Echo","Vibe","Rush","Glow","Summer","Crowd","Fever",
              "Runway","Horizon","Signal","Storm","Spark","Anthem","Highway","Rooftop",
              "Skyline","Countdown","Voltage","Frequency","Broadcast","Weekend","Festival"],
    },
    "rock": {
        "A": ["Iron","Stone","Dark","Broken","Thunder","Burning","Raw","Heavy","Cracked",
              "Electric","Hollow","Blinding","Savage","Raging","Rusted","Wild","Steel",
              "Black","Shattered","Grinding","Smoldering","Jagged","Fierce","Snarling",
              "Screaming","Howling","Crashing","Reckless","Unbroken","Defiant","Roaring"],
        "B": ["Edge","Wall","Road","Sky","Chain","Fist","Storm","Blade","Fire","Mountain",
              "Machine","Corridor","Thunder","Wave","Signal","Cage","Engine","Bridge",
              "Tower","Wire","Current","Circuit","Hammer","Pulse","Wreckage","Rebellion",
              "Uprising","Barricade","Manifesto","Override","Shutdown","Collapse","Fracture"],
    },
    "ambient": {
        "A": ["Floating","Drifting","Endless","Infinite","Celestial","Cosmic","Deep","Vast",
              "Open","Still","Pale","Silent","Eternal","Distant","Transparent","Weightless",
              "Fading","Nebular","Glacial","Submerged","Suspended","Dissolving","Resonant"],
        "B": ["Space","Current","Field","Shore","Horizon","Tide","Breath","Cloud","Void",
              "Bloom","Silence","Ocean","Flow","Orbit","Drift","Wind","Cascade","Expanse",
              "Haze","Fog","Ether","Atmosphere","Stasis","Continuum","Frequency","Resonance",
              "Membrane","Threshold","Interval","Periphery","Boundary","Perimeter"],
    },
    "jazz": {
        "A": ["Midnight","Blue","Smoky","Velvet","Late","Warm","Slow","Golden","Sultry",
              "Soft","Rainy","Quiet","Deep","Mellow","Dim","Amber","Easy","Moody","Cool",
              "Hazy","Lazy","Rich","Tender","Breezy","Smokey","Dusky","Hushed","Moonlit"],
        "B": ["Avenue","Note","Club","Lounge","Hour","Session","Groove","Quartet","Solo",
              "Night","Room","Corner","Standard","Ballad","Suite","Melody","Improvisation",
              "Riff","Swing","Echo","Serenade","Waltz","Cadence","Interlude","Lullaby",
              "Passage","Movement","Phrase","Cadenza","Bridge","Refrain","Verse","Coda"],
    },
    "synthwave": {
        "A": ["Neon","Retro","Chrome","Electric","Digital","Cyber","Laser","Grid","Pixel",
              "Hologram","Hyper","Vector","Binary","Analog","Plasma","Quantum","Ultraviolet",
              "Infrared","Hexadecimal","Phosphor","Cathode","Transistor","Capacitor"],
        "B": ["Drive","City","Wave","Night","Sky","Highway","Dream","Grid","Core","Protocol",
              "Sequence","Matrix","Circuit","Pulse","Echo","Zone","Flux","Nexus","Override",
              "Storm","Vision","Surge","Runway","Frequency","Transmission","Broadcast",
              "Reception","Oscillation","Modulation","Synthesizer","Waveform","Oscillator"],
    },
    "hip-hop": {
        "A": ["Street","Urban","Block","Gold","Raw","Hard","Real","Live","Cold","Hot",
              "True","Hustle","Grind","Flow","West","East","Deep","Heavy","Crown","Rising",
              "Building","Concrete","Asphalt","Borough","District","Metro","Underground"],
        "B": ["Code","Sound","Game","Life","Wave","Verse","Bars","Flow","Track","Anthem",
              "Bounce","Freestyle","Cipher","Hustle","Grind","Crown","Throne","Hook",
              "Bridge","Drop","Beat","Rhythm","Motion","Cadence","Frequency","Legacy",
              "Heritage","Chronicle","Manifesto","Blueprint","Foundation","Architecture"],
    },
    "blues": {
        "A": ["Delta","Muddy","Rainy","Dark","Lonesome","Weary","Dusty","Old","Broken",
              "Heavy","Slow","Cold","Empty","Aching","Hollow","Deep","Faded","Worn",
              "Rusted","Southern","Low","Midnight","Wandering","Troubled","Forsaken"],
        "B": ["Road","River","Train","House","Field","Night","Morning","Rain","Tears",
              "Heart","Soul","Guitar","Harmonica","Porch","Crossroads","Highway","Trouble",
              "Feeling","Lament","Moan","Wail","Backwater","Bottleneck","Turnaround",
              "Shuffle","Boogie","Stomp","Ramble","Rambling","Wandering","Longing"],
    },
    "classical": {
        "A": ["Grand","Noble","Serene","Solemn","Gentle","Majestic","Tender","Delicate",
              "Graceful","Elegant","Pastoral","Lyrical","Flowing","Peaceful","Tempestuous",
              "Dreaming","Morning","Evening","Twilight","Springtime","Autumnal","Wintry"],
        "B": ["Symphony","Sonata","Nocturne","Prelude","Etude","Waltz","Concerto","Aria",
              "Serenade","Fugue","Ballade","Intermezzo","Rondo","Fantasia","Overture",
              "Variations","Caprice","Elegy","Hymn","Mazurka","Reverie","Impromptu",
              "Rhapsody","Berceuse","Barcarolle","Tarantella","Polonaise","Minuet","Gigue"],
    },
    "edm": {
        "A": ["Drop","Bass","Hyper","Ultra","Mega","Turbo","Warp","Surge","Blast","Boost",
              "Apex","Zenith","Peak","Maximum","Supreme","Core","Prime","Power","Flash",
              "Voltage","Atomic","Nuclear","Hypersonic","Supersonic","Overdrive","Redline"],
        "B": ["Drop","Kick","Wave","Beat","Rush","Surge","Pulse","Energy","Force","Drive",
              "Flow","Frenzy","Rave","Festival","Floor","Night","Rise","Explosion","Impact",
              "Momentum","Override","Sequence","Protocol","Algorithm","Frequency","Amplitude",
              "Resonance","Oscillation","Modulation","Synthesis","Compression","Distortion"],
    },
    "country": {
        "A": ["Back","Old","Dusty","Country","Southern","Blue","Red","Wide","Open","Rolling",
              "Simple","Honest","True","Good","Sweet","Warm","Gold","Sunset","Highway",
              "River","Mountain","Prairie","Lonesome","Hollow","Creek","Appalachian"],
        "B": ["Road","Porch","Home","Town","Bar","Night","Sky","Field","Rain","Sun","River",
              "Hill","Dirt","Track","Guitar","Heart","Song","Dance","Story","Memory",
              "Days","Summer","Dream","Harvest","Homestead","Farmhouse","Pasture","Meadow",
              "Backroad","Pickup","Tailgate","Honky-tonk","Saloon","Campfire","Bonfire"],
    },
    "r&b": {
        "A": ["Smooth","Velvet","Silk","Golden","Warm","Deep","Slow","Sweet","Rich","Tender",
              "Soft","Easy","Mellow","Soul","Midnight","Endless","Burning","Falling","Rising",
              "Forever","Simply","Always","Forever","Breathless","Timeless","Ageless"],
        "B": ["Groove","Love","Night","Soul","Heart","Touch","Feel","Move","Dance","Song",
              "Melody","Rhythm","Beat","Vibe","Magic","Dream","Flow","Wave","Harmony",
              "Tone","Desire","Moment","Fire","Rain","Embrace","Surrender","Promise",
              "Forever","Eternity","Devotion","Affection","Tenderness","Intimacy","Passion"],
    },
    "metal": {
        "A": ["Black","Death","Dark","Iron","Steel","Bone","Blood","Shadow","Chaos","Void",
              "Infernal","Burning","Raging","Crushing","Grinding","Savage","Brutal","Violent",
              "Shredding","Obliterating","Wrath","Wrathful","Merciless","Relentless","Unending"],
        "B": ["Throne","Pit","Storm","Gate","War","Blade","Chain","Hammer","Fist","Wall",
              "Siege","Assault","Destruction","Annihilation","Devastation","Mayhem","Chaos",
              "Abyss","Ruin","Rage","Fury","Wrath","Vengeance","Judgment","Reckoning",
              "Armageddon","Apocalypse","Tribulation","Damnation","Perdition","Inferno"],
    },
    "reggae": {
        "A": ["Island","Tropical","Sunny","Easy","Breezy","Warm","Golden","Free","Peaceful",
              "Joyful","Natural","Roots","One","Pure","True","Sweet","Mystic","Positive",
              "Rising","Flowing","Blessed","Sacred","Ancient","Timeless","Eternal"],
        "B": ["Vibes","Rhythm","Beat","Sound","Wave","Movement","Flow","Wind","Sun","Island",
              "Shore","Breeze","Harmony","Spirit","Love","Peace","Unity","Freedom","Nation",
              "Culture","Roots","Blessing","Chant","Meditation","Reasoning","Livity",
              "Iration","Guidance","Overstanding","Repatriation","Redemption","Liberation"],
    },
    "dream pop": {
        "A": ["Dreamy","Hazy","Soft","Floating","Gentle","Fading","Blurred","Distant","Wistful",
              "Tender","Velvet","Gauzy","Fragile","Delicate","Shimmering","Glowing","Drifting",
              "Whispered","Faint","Pale","Translucent","Diaphanous","Ephemeral","Transient"],
        "B": ["Memory","Dream","Reverie","Vision","Cloud","Haze","Echo","Reflection","Shadow",
              "Light","Glow","Bloom","Petal","Shore","Wave","Tide","Garden","Sky","Moon",
              "Star","Dusk","Dawn","Twilight","Horizon","Mirage","Illusion","Phantom",
              "Specter","Apparition","Impression","Suggestion","Whisper","Murmur","Breath"],
    },
    "soul": {
        "A": ["Deep","True","Real","Tender","Warm","Golden","Rich","Smooth","Sweet","Burning",
              "Yearning","Aching","Longing","Rising","Falling","Broken","Mended","Whole",
              "Free","Pure","Open","Wide","Naked","Honest","Sincere","Genuine","Authentic"],
        "B": ["Soul","Heart","Love","Spirit","Fire","Flame","Light","River","Song","Cry",
              "Gospel","Grace","Truth","Story","Voice","Feeling","Move","Sway","Groove",
              "Blues","Joy","Pain","Salvation","Glory","Redemption","Forgiveness","Healing",
              "Liberation","Transcendence","Transformation","Awakening","Revelation","Vision"],
    },
    "indie pop": {
        "A": ["Bright","Soft","Warm","Tender","Young","Wild","Free","Open","Simple","Pure",
              "Sweet","Gentle","Calm","Quiet","Small","Lovely","Pretty","Happy","Sunny",
              "Fresh","Clean","Light","Golden","Breezy","Airy","Crisp","Vivid","Vibrant"],
        "B": ["Heart","Day","Morning","Song","Sound","Dream","Memory","Friend","Letter","Story",
              "Garden","Summer","Weekend","Afternoon","Feeling","Moment","Thought","Mind",
              "Wonder","World","Life","Time","Space","Place","Room","Home","Road","Journey",
              "Adventure","Exploration","Discovery","Beginning","Ending","Chapter","Verse"],
    },
}

# ── Artist name components ────────────────────────────────────────────────────

ARTIST_FIRST = [
    "Neon","Solar","Lunar","Echo","Drift","Haze","Pulse","Velvet","Amber","Coral",
    "Indigo","Cobalt","Crimson","Azure","Silver","Golden","Hollow","Broken","Silent",
    "Vivid","Mellow","Static","Mosaic","Prism","Orbit","Nova","Zenith","Radiant",
    "Twilight","Midnight","Dawn","Dusk","Storm","Calm","Wild","Gentle","Distant",
    "Faded","Bright","Dark","Paper","Glass","Stone","Iron","Copper","Chrome","Rust",
    "Ash","Ember","Frost","Smoke","Deep","Wide","Open","Sharp","Soft","Loud","Quiet",
    "Heavy","Light","Warm","Cool","Raw","Pure","True","Lost","Found","Worn","Bare",
    "Slow","Fast","Still","Free","Bound","Young","Old","New","Pale","Bold","Dim",
    "Blazing","Shining","Glowing","Burning","Frozen","Melting","Rising","Falling",
    "Soaring","Sinking","Drifting","Floating","Spinning","Turning","Shifting","Changing",
]

ARTIST_SECOND = [
    "Echo","Wave","Bloom","Drift","Pulse","Light","Sound","Roots","Fire","Stone",
    "Forest","River","Ocean","Mountain","Valley","Desert","Garden","Lantern","Candle",
    "Mirror","Window","Bridge","Tower","Beacon","Signal","Circuit","Frequency","Voltage",
    "Current","Static","Noise","Silence","Harmony","Melody","Rhythm","Beat","Groove",
    "Flow","Rush","Surge","Storm","Calm","Glow","Shade","Shadow","Spark","Flame","Frost",
    "Snow","Rain","Cloud","Sky","Star","Moon","Sun","Mist","Fog","Wind","Tide","Shore",
    "Sea","Creek","Brook","Pond","Lake","Reef","Strings","Keys","Brass","Chorus",
    "Ensemble","Collective","Society","Project","Machine","Engine","System","Network",
    "Archive","Laboratory","Institute","Division","Assembly","Coalition","Alliance",
    "Syndicate","Bureau","Agency","Foundation","Movement","Initiative","Collective",
]


def _rnd(lo: float, hi: float) -> float:
    return round(random.uniform(lo, hi), 2)


def _load_existing(path: str) -> tuple[list[dict], set[str], int]:
    rows, titles, max_id = [], set(), 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
            titles.add(row["title"].lower())
            max_id = max(max_id, int(row["id"]))
    return rows, titles, max_id


def _generate_title(genre: str, used: set[str]) -> str:
    words = TITLE_WORDS[genre]
    for _ in range(200):
        title = f"{random.choice(words['A'])} {random.choice(words['B'])}"
        if title.lower() not in used:
            used.add(title.lower())
            return title
    # fallback: append a number to guarantee uniqueness
    base = f"{random.choice(words['A'])} {random.choice(words['B'])}"
    n = 2
    candidate = f"{base} {n}"
    while candidate.lower() in used:
        n += 1
        candidate = f"{base} {n}"
    used.add(candidate.lower())
    return candidate


def _generate_artist() -> str:
    return f"{random.choice(ARTIST_FIRST)} {random.choice(ARTIST_SECOND)}"


def generate_rows(count: int, start_id: int, used_titles: set[str]) -> list[dict]:
    genre_list = list(GENRES.keys())
    rows = []
    next_id = start_id + 1

    for _ in range(count):
        genre = random.choice(genre_list)
        cfg   = GENRES[genre]
        lo, hi = cfg["tempo"]

        rows.append({
            "id":           next_id,
            "title":        _generate_title(genre, used_titles),
            "artist":       _generate_artist(),
            "genre":        genre,
            "mood":         random.choice(cfg["moods"]),
            "energy":       _rnd(*cfg["energy"]),
            "tempo_bpm":    random.randint(int(lo), int(hi)),
            "valence":      _rnd(*cfg["valence"]),
            "danceability": _rnd(*cfg["danceability"]),
            "acousticness": _rnd(*cfg["acousticness"]),
        })
        next_id += 1

    return rows


def main():
    print(f"Reading {CSV_PATH} ...")
    existing, used_titles, max_id = _load_existing(CSV_PATH)
    print(f"  Existing rows: {len(existing)}  (max id={max_id})")

    print(f"Generating {TARGET_NEW_ROWS:,} new rows ...")
    new_rows = generate_rows(TARGET_NEW_ROWS, max_id, used_titles)

    print(f"Appending to {CSV_PATH} ...")
    fieldnames = ["id","title","artist","genre","mood","energy","tempo_bpm",
                  "valence","danceability","acousticness"]
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerows(new_rows)

    # Verify
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        final_count = sum(1 for _ in csv.DictReader(f))

    print(f"\nDone.")
    print(f"  Original rows : {len(existing):>6}")
    print(f"  New rows added: {len(new_rows):>6}")
    print(f"  Final row count: {final_count:>5}")
    assert final_count == len(existing) + TARGET_NEW_ROWS, "Row count mismatch!"
    print("  Assertion passed: no rows lost or duplicated.")


if __name__ == "__main__":
    main()
