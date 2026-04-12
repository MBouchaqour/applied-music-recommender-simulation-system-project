flowchart TD

    %% ── PHASE 1 · INPUT ──────────────────────────────────────────
    subgraph INPUT ["① INPUT"]
        direction LR
        CSV[("songs.csv\n──────────\n20 songs on disk")]
        PREFS["User Taste Profile\n──────────────────\ngenre          lofi\nmood           chill\ntarget_energy  0.38\ntarget_acousticness  0.78\ntarget_valence  0.58\ntarget_danceability  0.55"]
    end

    %% ── PHASE 2 · LOAD ───────────────────────────────────────────
    subgraph LOAD ["② LOAD"]
        LOADSONGS["load_songs()\n─────────────────────────────\nOpen CSV · parse each row\nReturn list of 20 song dicts"]
    end

    %% ── PHASE 3 · SCORING LOOP ───────────────────────────────────
    subgraph LOOP ["③ SCORING LOOP  —  score_song() called once per song"]
        PICK["Take next song from list"]

        GENRE{"song.genre\n== lofi ?"}
        G_YES["+ 2.0 pts\nreason: genre match"]
        G_NO["+ 0.0 pts"]

        MOOD{"song.mood\n== chill ?"}
        M_YES["+ 1.5 pts\nreason: mood match"]
        M_NO["+ 0.0 pts"]

        NUMERIC["Numeric Proximity\n──────────────────────────────────────────────────\nenergy        1 minus abs(song.energy minus 0.38) times 1.5\nacousticness  1 minus abs(song.acousticness minus 0.78) times 1.5\nvalence       1 minus abs(song.valence minus 0.58) times 1.0\ndanceability  1 minus abs(song.danceability minus 0.55) times 0.5"]

        NORMALIZE["Normalize\n──────────────────────────────\nfinal_score = total points divided by 8.0\nResult range: 0.0 to 1.0"]

        STORE["Append to results list\nsong_dict  final_score  reasons"]

        MORE{"More songs\nin list?"}
    end

    %% ── PHASE 4 · RANKING ────────────────────────────────────────
    subgraph RANK ["④ RANKING  —  recommend_songs()"]
        SORT["Sort results list\nby final_score DESC"]
        TOPK["Slice top k = 5"]
    end

    %% ── PHASE 5 · OUTPUT ─────────────────────────────────────────
    subgraph OUTPUT ["⑤ OUTPUT"]
        RESULT["Ranked Recommendations\n────────────────────────────────────────────\n1  Library Rain          0.97   genre mood energy\n2  Midnight Coding        0.91   genre mood\n3  Focus Flow             0.79   genre energy\n4  Spacewalk Thoughts     0.63   mood acousticness\n5  Coffee Shop Stories    0.54   acousticness"]
    end

    %% ── CONNECTIONS ──────────────────────────────────────────────
    CSV      --> LOADSONGS
    LOADSONGS --> PICK
    PREFS    --> GENRE

    PICK --> GENRE

    GENRE -- Yes --> G_YES --> MOOD
    GENRE -- No  --> G_NO  --> MOOD

    MOOD -- Yes --> M_YES --> NUMERIC
    MOOD -- No  --> M_NO  --> NUMERIC

    NUMERIC --> NORMALIZE --> STORE --> MORE

    MORE -- Yes --> PICK
    MORE -- No  --> SORT

    SORT --> TOPK --> RESULT

    %% ── STYLES ───────────────────────────────────────────────────
    style INPUT   fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style LOAD    fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style LOOP    fill:#1a3a2a,color:#fff,stroke:#4caf50
    style RANK    fill:#3a1e3a,color:#fff,stroke:#ab47bc
    style OUTPUT  fill:#3a2a1a,color:#fff,stroke:#ff9800

    style CSV        fill:#0d2137,color:#7ec8e3,stroke:#4a90d9
    style PREFS      fill:#0d2137,color:#7ec8e3,stroke:#4a90d9
    style LOADSONGS  fill:#0d2137,color:#7ec8e3,stroke:#4a90d9
    style PICK       fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style GENRE      fill:#1b4020,color:#c8e6c9,stroke:#66bb6a
    style G_YES      fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style G_NO       fill:#3a1a1a,color:#ef9a9a,stroke:#ef5350
    style MOOD       fill:#1b4020,color:#c8e6c9,stroke:#66bb6a
    style M_YES      fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style M_NO       fill:#3a1a1a,color:#ef9a9a,stroke:#ef5350
    style NUMERIC    fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style NORMALIZE  fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style STORE      fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style MORE       fill:#1b4020,color:#c8e6c9,stroke:#66bb6a
    style SORT       fill:#2a0d3a,color:#ce93d8,stroke:#ab47bc
    style TOPK       fill:#2a0d3a,color:#ce93d8,stroke:#ab47bc
    style RESULT     fill:#3a1f00,color:#ffcc80,stroke:#ff9800
