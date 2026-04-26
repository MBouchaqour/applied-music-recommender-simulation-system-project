flowchart TD

    %% ── PHASE 1 · USER INPUT ─────────────────────────────────────
    subgraph INPUT ["① USER INPUT"]
        direction LR
        NL["Natural Language Query\n─────────────────────────────\n'I want something calm\nand relaxing for studying'"]
        CSV[("songs.csv\n──────────\n20 songs on disk")]
    end

    %% ── PHASE 2 · CLAUDE AGENT ───────────────────────────────────
    subgraph AGENT ["② CLAUDE AGENT  —  agent.py · run_agent()"]
        SYSPROMPT["System Prompt\n──────────────────────────\nAvailable genres & moods\nInstruction: call search_songs\nbefore responding"]
        CLAUDE["Claude API\n(claude-haiku-4-5)\n──────────────────────────\nUnderstands intent\nDecides tool parameters"]
        TOOLDEF["Tool Definition\n──────────────────────────\nsearch_songs\n· genre  · mood\n· target_energy\n· target_acousticness\n· target_valence\n· target_danceability"]
    end

    %% ── PHASE 3 · TOOL EXECUTION ─────────────────────────────────
    subgraph TOOL ["③ TOOL EXECUTION  —  search_songs()"]
        LOADSONGS["load_songs()\n──────────────────────\nParse CSV → 20 song dicts"]
        LOOP["score_song()  ×20\n──────────────────────────────\nGenre match   +2.0\nMood match    +1.5\nEnergy sim    ×1.5\nAcoustic sim  ×1.5\nValence sim   ×1.0\nDance sim     ×0.5\n──────────────\nNormalize ÷ 8.0"]
        RANK["recommend_songs()\n──────────────────────\nSort DESC · slice top k"]
        TOOLRESULT["Tool Result  →  JSON\n──────────────────────────────────\ntitle · artist · genre · mood\nconfidence_score · why"]
    end

    %% ── PHASE 4 · AGENT RESPONSE ─────────────────────────────────
    subgraph RESPONSE ["④ AGENT RESPONSE"]
        CLAUDEREPLY["Claude formulates reply\n────────────────────────────────\nConversational recommendations\nPer-song explanation\nConfidence note"]
    end

    %% ── PHASE 5 · OUTPUT ─────────────────────────────────────────
    subgraph OUTPUT ["⑤ OUTPUT"]
        FINAL["CLI Response\n────────────────────────────────────────────\n'Here are 5 songs for studying:\n1. Library Rain — calm lofi, high acousticness\n2. Midnight Coding — focused lofi energy\n...\nI'm confident these match your vibe.'"]
        LOG["agent.log\n────────────────────────\nQuery · tool params\nTop score · stop_reason\nErrors & warnings"]
    end

    %% ── PHASE 6 · TESTING ────────────────────────────────────────
    subgraph TESTING ["⑥ RELIABILITY & TESTING"]
        TESTS["pytest  —  6 unit tests\n────────────────────────────────────\nRecommender OOP class\nscore_song logic\nrecommend_songs output count\nload_songs data integrity"]
        HUMAN["Human Evaluation\n────────────────────────\nReview sample interactions\nConfirm relevance of picks\nCheck confidence notes"]
    end

    %% ── CONNECTIONS ──────────────────────────────────────────────
    NL       --> SYSPROMPT
    SYSPROMPT --> CLAUDE
    TOOLDEF  --> CLAUDE

    CLAUDE -- "tool_use call\nwith structured params" --> LOADSONGS
    CSV --> LOADSONGS
    LOADSONGS --> LOOP --> RANK --> TOOLRESULT

    TOOLRESULT -- "tool_result\nback to agent" --> CLAUDEREPLY
    CLAUDEREPLY --> FINAL
    CLAUDEREPLY --> LOG

    FINAL --> HUMAN
    TESTS -.->|"validates scoring engine"| LOOP

    %% ── STYLES ───────────────────────────────────────────────────
    style INPUT    fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style AGENT    fill:#1a2a3a,color:#fff,stroke:#7ec8e3
    style TOOL     fill:#1a3a2a,color:#fff,stroke:#4caf50
    style RESPONSE fill:#2a1a3a,color:#fff,stroke:#ab47bc
    style OUTPUT   fill:#3a2a1a,color:#fff,stroke:#ff9800
    style TESTING  fill:#3a1a1a,color:#fff,stroke:#ef5350

    style NL          fill:#0d2137,color:#7ec8e3,stroke:#4a90d9
    style CSV         fill:#0d2137,color:#7ec8e3,stroke:#4a90d9
    style SYSPROMPT   fill:#0d1f2e,color:#7ec8e3,stroke:#4a90d9
    style CLAUDE      fill:#0d1f2e,color:#b3e5fc,stroke:#29b6f6
    style TOOLDEF     fill:#0d1f2e,color:#7ec8e3,stroke:#4a90d9
    style LOADSONGS   fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style LOOP        fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style RANK        fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style TOOLRESULT  fill:#0d3320,color:#a5d6a7,stroke:#4caf50
    style CLAUDEREPLY fill:#2a0d3a,color:#ce93d8,stroke:#ab47bc
    style FINAL       fill:#3a1f00,color:#ffcc80,stroke:#ff9800
    style LOG         fill:#3a1f00,color:#ffcc80,stroke:#ff9800
    style TESTS       fill:#3a0d0d,color:#ef9a9a,stroke:#ef5350
    style HUMAN       fill:#3a0d0d,color:#ef9a9a,stroke:#ef5350
