# Clinical Assessment Library with complete questions, scoring, and severity bands

CLINICAL_ASSESSMENTS = {
    "PHQ-9": {
        "name": "Patient Health Questionnaire-9",
        "description": "A 9-item depression screening tool that measures severity of depressive symptoms over the past 2 weeks.",
        "category": "Depression",
        "time_estimate": "5 minutes",
        "scoring_method": "sum",
        "max_score": 27,
        "severity_bands": [
            {"min": 0, "max": 4, "label": "Minimal", "color": "green"},
            {"min": 5, "max": 9, "label": "Mild", "color": "yellow"},
            {"min": 10, "max": 14, "label": "Moderate", "color": "orange"},
            {"min": 15, "max": 19, "label": "Moderately Severe", "color": "red"},
            {"min": 20, "max": 27, "label": "Severe", "color": "darkred"}
        ],
        "questions": [
            {"id": 1, "text": "Little interest or pleasure in doing things", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 2, "text": "Feeling down, depressed, or hopeless", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 3, "text": "Trouble falling or staying asleep, or sleeping too much", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 4, "text": "Feeling tired or having little energy", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 5, "text": "Poor appetite or overeating", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 6, "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 7, "text": "Trouble concentrating on things, such as reading the newspaper or watching television", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 8, "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 9, "text": "Thoughts that you would be better off dead or of hurting yourself in some way", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "GAD-7": {
        "name": "Generalized Anxiety Disorder-7",
        "description": "A 7-item screening tool for generalized anxiety disorder measuring symptom severity over the past 2 weeks.",
        "category": "Anxiety",
        "time_estimate": "3 minutes",
        "scoring_method": "sum",
        "max_score": 21,
        "severity_bands": [
            {"min": 0, "max": 4, "label": "Minimal", "color": "green"},
            {"min": 5, "max": 9, "label": "Mild", "color": "yellow"},
            {"min": 10, "max": 14, "label": "Moderate", "color": "orange"},
            {"min": 15, "max": 21, "label": "Severe", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "Feeling nervous, anxious, or on edge", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 2, "text": "Not being able to stop or control worrying", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 3, "text": "Worrying too much about different things", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 4, "text": "Trouble relaxing", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 5, "text": "Being so restless that it's hard to sit still", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 6, "text": "Becoming easily annoyed or irritable", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]},
            {"id": 7, "text": "Feeling afraid as if something awful might happen", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Several days"}, {"value": 2, "label": "More than half the days"}, {"value": 3, "label": "Nearly every day"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "DASS-21": {
        "name": "Depression Anxiety Stress Scales-21",
        "description": "A 21-item scale measuring depression, anxiety, and stress with 7 items per subscale.",
        "category": "Multiple",
        "time_estimate": "10 minutes",
        "scoring_method": "subscales",
        "subscales": {
            "depression": {"items": [3, 5, 10, 13, 16, 17, 21], "multiplier": 2},
            "anxiety": {"items": [2, 4, 7, 9, 15, 19, 20], "multiplier": 2},
            "stress": {"items": [1, 6, 8, 11, 12, 14, 18], "multiplier": 2}
        },
        "severity_bands": {
            "depression": [
                {"min": 0, "max": 9, "label": "Normal", "color": "green"},
                {"min": 10, "max": 13, "label": "Mild", "color": "yellow"},
                {"min": 14, "max": 20, "label": "Moderate", "color": "orange"},
                {"min": 21, "max": 27, "label": "Severe", "color": "red"},
                {"min": 28, "max": 42, "label": "Extremely Severe", "color": "darkred"}
            ],
            "anxiety": [
                {"min": 0, "max": 7, "label": "Normal", "color": "green"},
                {"min": 8, "max": 9, "label": "Mild", "color": "yellow"},
                {"min": 10, "max": 14, "label": "Moderate", "color": "orange"},
                {"min": 15, "max": 19, "label": "Severe", "color": "red"},
                {"min": 20, "max": 42, "label": "Extremely Severe", "color": "darkred"}
            ],
            "stress": [
                {"min": 0, "max": 14, "label": "Normal", "color": "green"},
                {"min": 15, "max": 18, "label": "Mild", "color": "yellow"},
                {"min": 19, "max": 25, "label": "Moderate", "color": "orange"},
                {"min": 26, "max": 33, "label": "Severe", "color": "red"},
                {"min": 34, "max": 42, "label": "Extremely Severe", "color": "darkred"}
            ]
        },
        "questions": [
            {"id": 1, "text": "I found it hard to wind down", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 2, "text": "I was aware of dryness of my mouth", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 3, "text": "I couldn't seem to experience any positive feeling at all", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 4, "text": "I experienced breathing difficulty (e.g., excessively rapid breathing, breathlessness in the absence of physical exertion)", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 5, "text": "I found it difficult to work up the initiative to do things", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 6, "text": "I tended to over-react to situations", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 7, "text": "I experienced trembling (e.g., in the hands)", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 8, "text": "I felt that I was using a lot of nervous energy", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 9, "text": "I was worried about situations in which I might panic and make a fool of myself", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 10, "text": "I felt that I had nothing to look forward to", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 11, "text": "I found myself getting agitated", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 12, "text": "I found it difficult to relax", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 13, "text": "I felt down-hearted and blue", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 14, "text": "I was intolerant of anything that kept me from getting on with what I was doing", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 15, "text": "I felt I was close to panic", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 16, "text": "I was unable to become enthusiastic about anything", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 17, "text": "I felt I wasn't worth much as a person", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 18, "text": "I felt that I was rather touchy", "subscale": "stress", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 19, "text": "I was aware of the action of my heart in the absence of physical exertion (e.g., sense of heart rate increase, heart missing a beat)", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 20, "text": "I felt scared without any good reason", "subscale": "anxiety", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]},
            {"id": 21, "text": "I felt that life was meaningless", "subscale": "depression", "options": [{"value": 0, "label": "Did not apply to me at all"}, {"value": 1, "label": "Applied to me to some degree"}, {"value": 2, "label": "Applied to me a considerable degree"}, {"value": 3, "label": "Applied to me very much"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "WHO-5": {
        "name": "WHO-5 Well-Being Index",
        "description": "A 5-item scale measuring subjective psychological well-being over the past 2 weeks.",
        "category": "Well-being",
        "time_estimate": "2 minutes",
        "scoring_method": "sum_multiply",
        "multiplier": 4,
        "max_score": 100,
        "severity_bands": [
            {"min": 0, "max": 28, "label": "Poor Well-being (Screen for Depression)", "color": "red"},
            {"min": 29, "max": 50, "label": "Low Well-being", "color": "orange"},
            {"min": 51, "max": 75, "label": "Moderate Well-being", "color": "yellow"},
            {"min": 76, "max": 100, "label": "High Well-being", "color": "green"}
        ],
        "questions": [
            {"id": 1, "text": "I have felt cheerful and in good spirits", "options": [{"value": 5, "label": "All of the time"}, {"value": 4, "label": "Most of the time"}, {"value": 3, "label": "More than half of the time"}, {"value": 2, "label": "Less than half of the time"}, {"value": 1, "label": "Some of the time"}, {"value": 0, "label": "At no time"}]},
            {"id": 2, "text": "I have felt calm and relaxed", "options": [{"value": 5, "label": "All of the time"}, {"value": 4, "label": "Most of the time"}, {"value": 3, "label": "More than half of the time"}, {"value": 2, "label": "Less than half of the time"}, {"value": 1, "label": "Some of the time"}, {"value": 0, "label": "At no time"}]},
            {"id": 3, "text": "I have felt active and vigorous", "options": [{"value": 5, "label": "All of the time"}, {"value": 4, "label": "Most of the time"}, {"value": 3, "label": "More than half of the time"}, {"value": 2, "label": "Less than half of the time"}, {"value": 1, "label": "Some of the time"}, {"value": 0, "label": "At no time"}]},
            {"id": 4, "text": "I woke up feeling fresh and rested", "options": [{"value": 5, "label": "All of the time"}, {"value": 4, "label": "Most of the time"}, {"value": 3, "label": "More than half of the time"}, {"value": 2, "label": "Less than half of the time"}, {"value": 1, "label": "Some of the time"}, {"value": 0, "label": "At no time"}]},
            {"id": 5, "text": "My daily life has been filled with things that interest me", "options": [{"value": 5, "label": "All of the time"}, {"value": 4, "label": "Most of the time"}, {"value": 3, "label": "More than half of the time"}, {"value": 2, "label": "Less than half of the time"}, {"value": 1, "label": "Some of the time"}, {"value": 0, "label": "At no time"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "ASRS-v1.1": {
        "name": "Adult ADHD Self-Report Scale v1.1",
        "description": "An 18-item scale for screening ADHD symptoms in adults. Part A (6 items) is the screener.",
        "category": "ADHD",
        "time_estimate": "5 minutes",
        "scoring_method": "adhd_screener",
        "max_score": 72,
        "severity_bands": [
            {"min": 0, "max": 3, "label": "Unlikely ADHD (Part A)", "color": "green"},
            {"min": 4, "max": 6, "label": "Likely ADHD - Further evaluation recommended", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?", "part": "A", "shaded_threshold": 2, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]},
            {"id": 2, "text": "How often do you have difficulty getting things in order when you have to do a task that requires organization?", "part": "A", "shaded_threshold": 2, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]},
            {"id": 3, "text": "How often do you have problems remembering appointments or obligations?", "part": "A", "shaded_threshold": 2, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]},
            {"id": 4, "text": "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?", "part": "A", "shaded_threshold": 3, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]},
            {"id": 5, "text": "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?", "part": "A", "shaded_threshold": 3, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]},
            {"id": 6, "text": "How often do you feel overly active and compelled to do things, like you were driven by a motor?", "part": "A", "shaded_threshold": 3, "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Rarely"}, {"value": 2, "label": "Sometimes"}, {"value": 3, "label": "Often"}, {"value": 4, "label": "Very Often"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "Y-BOCS": {
        "name": "Yale-Brown Obsessive Compulsive Scale",
        "description": "A 10-item scale measuring OCD symptom severity for obsessions (5 items) and compulsions (5 items).",
        "category": "OCD",
        "time_estimate": "10 minutes",
        "scoring_method": "sum",
        "max_score": 40,
        "severity_bands": [
            {"min": 0, "max": 7, "label": "Subclinical", "color": "green"},
            {"min": 8, "max": 15, "label": "Mild", "color": "yellow"},
            {"min": 16, "max": 23, "label": "Moderate", "color": "orange"},
            {"min": 24, "max": 31, "label": "Severe", "color": "red"},
            {"min": 32, "max": 40, "label": "Extreme", "color": "darkred"}
        ],
        "questions": [
            {"id": 1, "text": "Time occupied by obsessive thoughts: How much of your time is occupied by obsessive thoughts?", "subscale": "obsessions", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Less than 1 hour/day"}, {"value": 2, "label": "1-3 hours/day"}, {"value": 3, "label": "3-8 hours/day"}, {"value": 4, "label": "More than 8 hours/day"}]},
            {"id": 2, "text": "Interference from obsessive thoughts: How much do your obsessive thoughts interfere with your social or work functioning?", "subscale": "obsessions", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild interference"}, {"value": 2, "label": "Moderate interference"}, {"value": 3, "label": "Severe interference"}, {"value": 4, "label": "Extreme interference"}]},
            {"id": 3, "text": "Distress of obsessive thoughts: How much distress do your obsessive thoughts cause you?", "subscale": "obsessions", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild distress"}, {"value": 2, "label": "Moderate distress"}, {"value": 3, "label": "Severe distress"}, {"value": 4, "label": "Extreme distress"}]},
            {"id": 4, "text": "Resistance to obsessions: How much effort do you make to resist the obsessive thoughts?", "subscale": "obsessions", "options": [{"value": 0, "label": "Always resist"}, {"value": 1, "label": "Much resistance"}, {"value": 2, "label": "Some resistance"}, {"value": 3, "label": "Often yield"}, {"value": 4, "label": "Completely yield"}]},
            {"id": 5, "text": "Control over obsessive thoughts: How much control do you have over your obsessive thoughts?", "subscale": "obsessions", "options": [{"value": 0, "label": "Complete control"}, {"value": 1, "label": "Much control"}, {"value": 2, "label": "Moderate control"}, {"value": 3, "label": "Little control"}, {"value": 4, "label": "No control"}]},
            {"id": 6, "text": "Time spent on compulsions: How much time do you spend performing compulsive behaviors?", "subscale": "compulsions", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Less than 1 hour/day"}, {"value": 2, "label": "1-3 hours/day"}, {"value": 3, "label": "3-8 hours/day"}, {"value": 4, "label": "More than 8 hours/day"}]},
            {"id": 7, "text": "Interference from compulsions: How much do your compulsive behaviors interfere with your social or work functioning?", "subscale": "compulsions", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild interference"}, {"value": 2, "label": "Moderate interference"}, {"value": 3, "label": "Severe interference"}, {"value": 4, "label": "Extreme interference"}]},
            {"id": 8, "text": "Distress from compulsions: How would you feel if prevented from performing your compulsion(s)?", "subscale": "compulsions", "options": [{"value": 0, "label": "No anxiety"}, {"value": 1, "label": "Mild anxiety"}, {"value": 2, "label": "Moderate anxiety"}, {"value": 3, "label": "Severe anxiety"}, {"value": 4, "label": "Extreme anxiety"}]},
            {"id": 9, "text": "Resistance to compulsions: How much effort do you make to resist the compulsions?", "subscale": "compulsions", "options": [{"value": 0, "label": "Always resist"}, {"value": 1, "label": "Much resistance"}, {"value": 2, "label": "Some resistance"}, {"value": 3, "label": "Often yield"}, {"value": 4, "label": "Completely yield"}]},
            {"id": 10, "text": "Control over compulsions: How much control do you have over your compulsive behavior?", "subscale": "compulsions", "options": [{"value": 0, "label": "Complete control"}, {"value": 1, "label": "Much control"}, {"value": 2, "label": "Moderate control"}, {"value": 3, "label": "Little control"}, {"value": 4, "label": "No control"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "HAM-A": {
        "name": "Hamilton Anxiety Rating Scale",
        "description": "A 14-item clinician-administered scale measuring severity of anxiety symptoms.",
        "category": "Anxiety",
        "time_estimate": "15 minutes",
        "scoring_method": "sum",
        "max_score": 56,
        "severity_bands": [
            {"min": 0, "max": 17, "label": "Mild", "color": "green"},
            {"min": 18, "max": 24, "label": "Mild to Moderate", "color": "yellow"},
            {"min": 25, "max": 30, "label": "Moderate to Severe", "color": "orange"},
            {"min": 31, "max": 56, "label": "Severe", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "Anxious mood: Worries, anticipation of the worst, fearful anticipation, irritability", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 2, "text": "Tension: Feelings of tension, fatigability, startle response, moved to tears easily, trembling, feelings of restlessness, inability to relax", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 3, "text": "Fears: Of dark, strangers, being left alone, animals, traffic, crowds", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 4, "text": "Insomnia: Difficulty falling asleep, broken sleep, unsatisfying sleep and fatigue on waking, dreams, nightmares, night terrors", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 5, "text": "Intellectual: Difficulty in concentration, poor memory", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 6, "text": "Depressed mood: Loss of interest, lack of pleasure in hobbies, depression, early waking, diurnal swing", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 7, "text": "Somatic (muscular): Pains and aches, twitching, stiffness, myoclonic jerks, grinding of teeth, unsteady voice, increased muscular tone", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 8, "text": "Somatic (sensory): Tinnitus, blurring of vision, hot and cold flushes, feelings of weakness, pricking sensation", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 9, "text": "Cardiovascular symptoms: Tachycardia, palpitations, pain in chest, throbbing of vessels, fainting feelings, missing beat", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 10, "text": "Respiratory symptoms: Pressure or constriction in chest, choking feelings, sighing, dyspnea", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 11, "text": "Gastrointestinal symptoms: Difficulty in swallowing, wind, abdominal pain, burning sensations, abdominal fullness, nausea, vomiting, borborygmi, looseness of bowels, loss of weight, constipation", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 12, "text": "Genitourinary symptoms: Frequency of micturition, urgency of micturition, amenorrhea, menorrhagia, development of frigidity, premature ejaculation, loss of libido, impotence", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 13, "text": "Autonomic symptoms: Dry mouth, flushing, pallor, tendency to sweat, giddiness, tension headache, raising of hair", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 14, "text": "Behavior at interview: Fidgeting, restlessness or pacing, tremor of hands, furrowed brow, strained face, sighing or rapid respiration, facial pallor, swallowing, etc.", "options": [{"value": 0, "label": "Not present"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "BDI-II": {
        "name": "Beck Depression Inventory-II",
        "description": "A 21-item self-report measure of depression severity in adults and adolescents aged 13 and older.",
        "category": "Depression",
        "time_estimate": "10 minutes",
        "scoring_method": "sum",
        "max_score": 63,
        "severity_bands": [
            {"min": 0, "max": 13, "label": "Minimal", "color": "green"},
            {"min": 14, "max": 19, "label": "Mild", "color": "yellow"},
            {"min": 20, "max": 28, "label": "Moderate", "color": "orange"},
            {"min": 29, "max": 63, "label": "Severe", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "Sadness", "options": [{"value": 0, "label": "I do not feel sad"}, {"value": 1, "label": "I feel sad much of the time"}, {"value": 2, "label": "I am sad all the time"}, {"value": 3, "label": "I am so sad or unhappy that I can't stand it"}]},
            {"id": 2, "text": "Pessimism", "options": [{"value": 0, "label": "I am not discouraged about my future"}, {"value": 1, "label": "I feel more discouraged about my future than I used to"}, {"value": 2, "label": "I do not expect things to work out for me"}, {"value": 3, "label": "I feel my future is hopeless and will only get worse"}]},
            {"id": 3, "text": "Past Failure", "options": [{"value": 0, "label": "I do not feel like a failure"}, {"value": 1, "label": "I have failed more than I should have"}, {"value": 2, "label": "As I look back, I see a lot of failures"}, {"value": 3, "label": "I feel I am a total failure as a person"}]},
            {"id": 4, "text": "Loss of Pleasure", "options": [{"value": 0, "label": "I get as much pleasure as I ever did from the things I enjoy"}, {"value": 1, "label": "I don't enjoy things as much as I used to"}, {"value": 2, "label": "I get very little pleasure from the things I used to enjoy"}, {"value": 3, "label": "I can't get any pleasure from the things I used to enjoy"}]},
            {"id": 5, "text": "Guilty Feelings", "options": [{"value": 0, "label": "I don't feel particularly guilty"}, {"value": 1, "label": "I feel guilty over many things I have done or should have done"}, {"value": 2, "label": "I feel quite guilty most of the time"}, {"value": 3, "label": "I feel guilty all of the time"}]},
            {"id": 6, "text": "Punishment Feelings", "options": [{"value": 0, "label": "I don't feel I am being punished"}, {"value": 1, "label": "I feel I may be punished"}, {"value": 2, "label": "I expect to be punished"}, {"value": 3, "label": "I feel I am being punished"}]},
            {"id": 7, "text": "Self-Dislike", "options": [{"value": 0, "label": "I feel the same about myself as ever"}, {"value": 1, "label": "I have lost confidence in myself"}, {"value": 2, "label": "I am disappointed in myself"}, {"value": 3, "label": "I dislike myself"}]},
            {"id": 8, "text": "Self-Criticalness", "options": [{"value": 0, "label": "I don't criticize or blame myself more than usual"}, {"value": 1, "label": "I am more critical of myself than I used to be"}, {"value": 2, "label": "I criticize myself for all of my faults"}, {"value": 3, "label": "I blame myself for everything bad that happens"}]},
            {"id": 9, "text": "Suicidal Thoughts or Wishes", "options": [{"value": 0, "label": "I don't have any thoughts of killing myself"}, {"value": 1, "label": "I have thoughts of killing myself, but I would not carry them out"}, {"value": 2, "label": "I would like to kill myself"}, {"value": 3, "label": "I would kill myself if I had the chance"}]},
            {"id": 10, "text": "Crying", "options": [{"value": 0, "label": "I don't cry anymore than I used to"}, {"value": 1, "label": "I cry more than I used to"}, {"value": 2, "label": "I cry over every little thing"}, {"value": 3, "label": "I feel like crying, but I can't"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "ISI": {
        "name": "Insomnia Severity Index",
        "description": "A 7-item scale assessing the nature, severity, and impact of insomnia over the past 2 weeks.",
        "category": "Sleep",
        "time_estimate": "3 minutes",
        "scoring_method": "sum",
        "max_score": 28,
        "severity_bands": [
            {"min": 0, "max": 7, "label": "No clinically significant insomnia", "color": "green"},
            {"min": 8, "max": 14, "label": "Subthreshold insomnia", "color": "yellow"},
            {"min": 15, "max": 21, "label": "Clinical insomnia (moderate)", "color": "orange"},
            {"min": 22, "max": 28, "label": "Clinical insomnia (severe)", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "Difficulty falling asleep", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 2, "text": "Difficulty staying asleep", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 3, "text": "Problem waking up too early", "options": [{"value": 0, "label": "None"}, {"value": 1, "label": "Mild"}, {"value": 2, "label": "Moderate"}, {"value": 3, "label": "Severe"}, {"value": 4, "label": "Very severe"}]},
            {"id": 4, "text": "How satisfied/dissatisfied are you with your current sleep pattern?", "options": [{"value": 0, "label": "Very satisfied"}, {"value": 1, "label": "Satisfied"}, {"value": 2, "label": "Neutral"}, {"value": 3, "label": "Dissatisfied"}, {"value": 4, "label": "Very dissatisfied"}]},
            {"id": 5, "text": "To what extent do you consider your sleep problem to interfere with your daily functioning?", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "A little"}, {"value": 2, "label": "Somewhat"}, {"value": 3, "label": "Much"}, {"value": 4, "label": "Very much"}]},
            {"id": 6, "text": "How noticeable to others do you think your sleeping problem is in terms of impairing the quality of your life?", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "Barely"}, {"value": 2, "label": "Somewhat"}, {"value": 3, "label": "Much"}, {"value": 4, "label": "Very much"}]},
            {"id": 7, "text": "How worried/distressed are you about your current sleep problem?", "options": [{"value": 0, "label": "Not at all"}, {"value": 1, "label": "A little"}, {"value": 2, "label": "Somewhat"}, {"value": 3, "label": "Much"}, {"value": 4, "label": "Very much"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "AUDIT": {
        "name": "Alcohol Use Disorders Identification Test",
        "description": "A 10-item screening tool developed by WHO to assess alcohol consumption and related problems.",
        "category": "Substance Use",
        "time_estimate": "3 minutes",
        "scoring_method": "sum",
        "max_score": 40,
        "severity_bands": [
            {"min": 0, "max": 7, "label": "Low Risk", "color": "green"},
            {"min": 8, "max": 15, "label": "Hazardous Drinking", "color": "yellow"},
            {"min": 16, "max": 19, "label": "Harmful Drinking", "color": "orange"},
            {"min": 20, "max": 40, "label": "Possible Dependence", "color": "red"}
        ],
        "questions": [
            {"id": 1, "text": "How often do you have a drink containing alcohol?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Monthly or less"}, {"value": 2, "label": "2-4 times a month"}, {"value": 3, "label": "2-3 times a week"}, {"value": 4, "label": "4+ times a week"}]},
            {"id": 2, "text": "How many drinks containing alcohol do you have on a typical day when you are drinking?", "options": [{"value": 0, "label": "1 or 2"}, {"value": 1, "label": "3 or 4"}, {"value": 2, "label": "5 or 6"}, {"value": 3, "label": "7 to 9"}, {"value": 4, "label": "10 or more"}]},
            {"id": 3, "text": "How often do you have six or more drinks on one occasion?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 4, "text": "How often during the last year have you found that you were not able to stop drinking once you had started?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 5, "text": "How often during the last year have you failed to do what was normally expected of you because of drinking?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 6, "text": "How often during the last year have you needed a first drink in the morning to get yourself going after a heavy drinking session?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 7, "text": "How often during the last year have you had a feeling of guilt or remorse after drinking?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 8, "text": "How often during the last year have you been unable to remember what happened the night before because of your drinking?", "options": [{"value": 0, "label": "Never"}, {"value": 1, "label": "Less than monthly"}, {"value": 2, "label": "Monthly"}, {"value": 3, "label": "Weekly"}, {"value": 4, "label": "Daily or almost daily"}]},
            {"id": 9, "text": "Have you or someone else been injured because of your drinking?", "options": [{"value": 0, "label": "No"}, {"value": 2, "label": "Yes, but not in the last year"}, {"value": 4, "label": "Yes, during the last year"}]},
            {"id": 10, "text": "Has a relative, friend, doctor, or other health care worker been concerned about your drinking or suggested you cut down?", "options": [{"value": 0, "label": "No"}, {"value": 2, "label": "Yes, but not in the last year"}, {"value": 4, "label": "Yes, during the last year"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    },
    
    "RSES": {
        "name": "Rosenberg Self-Esteem Scale",
        "description": "A 10-item scale measuring global self-worth by measuring both positive and negative feelings about the self.",
        "category": "Self-Esteem",
        "time_estimate": "3 minutes",
        "scoring_method": "sum_reverse",
        "reverse_items": [2, 5, 6, 8, 9],
        "max_score": 30,
        "severity_bands": [
            {"min": 0, "max": 14, "label": "Low Self-Esteem", "color": "red"},
            {"min": 15, "max": 25, "label": "Normal Self-Esteem", "color": "green"},
            {"min": 26, "max": 30, "label": "High Self-Esteem", "color": "green"}
        ],
        "questions": [
            {"id": 1, "text": "I feel that I am a person of worth, at least on an equal plane with others", "options": [{"value": 3, "label": "Strongly agree"}, {"value": 2, "label": "Agree"}, {"value": 1, "label": "Disagree"}, {"value": 0, "label": "Strongly disagree"}]},
            {"id": 2, "text": "I feel that I have a number of good qualities", "options": [{"value": 3, "label": "Strongly agree"}, {"value": 2, "label": "Agree"}, {"value": 1, "label": "Disagree"}, {"value": 0, "label": "Strongly disagree"}]},
            {"id": 3, "text": "All in all, I am inclined to feel that I am a failure", "reverse": True, "options": [{"value": 0, "label": "Strongly agree"}, {"value": 1, "label": "Agree"}, {"value": 2, "label": "Disagree"}, {"value": 3, "label": "Strongly disagree"}]},
            {"id": 4, "text": "I am able to do things as well as most other people", "options": [{"value": 3, "label": "Strongly agree"}, {"value": 2, "label": "Agree"}, {"value": 1, "label": "Disagree"}, {"value": 0, "label": "Strongly disagree"}]},
            {"id": 5, "text": "I feel I do not have much to be proud of", "reverse": True, "options": [{"value": 0, "label": "Strongly agree"}, {"value": 1, "label": "Agree"}, {"value": 2, "label": "Disagree"}, {"value": 3, "label": "Strongly disagree"}]},
            {"id": 6, "text": "I take a positive attitude toward myself", "options": [{"value": 3, "label": "Strongly agree"}, {"value": 2, "label": "Agree"}, {"value": 1, "label": "Disagree"}, {"value": 0, "label": "Strongly disagree"}]},
            {"id": 7, "text": "On the whole, I am satisfied with myself", "options": [{"value": 3, "label": "Strongly agree"}, {"value": 2, "label": "Agree"}, {"value": 1, "label": "Disagree"}, {"value": 0, "label": "Strongly disagree"}]},
            {"id": 8, "text": "I wish I could have more respect for myself", "reverse": True, "options": [{"value": 0, "label": "Strongly agree"}, {"value": 1, "label": "Agree"}, {"value": 2, "label": "Disagree"}, {"value": 3, "label": "Strongly disagree"}]},
            {"id": 9, "text": "I certainly feel useless at times", "reverse": True, "options": [{"value": 0, "label": "Strongly agree"}, {"value": 1, "label": "Agree"}, {"value": 2, "label": "Disagree"}, {"value": 3, "label": "Strongly disagree"}]},
            {"id": 10, "text": "At times I think I am no good at all", "reverse": True, "options": [{"value": 0, "label": "Strongly agree"}, {"value": 1, "label": "Agree"}, {"value": 2, "label": "Disagree"}, {"value": 3, "label": "Strongly disagree"}]}
        ],
        "disclaimer": "This is a screening tool and not a diagnostic instrument."
    }
}

# Scoring functions
def calculate_score(assessment_type, answers):
    """Calculate score and severity based on assessment type and answers"""
    assessment = CLINICAL_ASSESSMENTS.get(assessment_type)
    if not assessment:
        return {"total_score": 0, "severity": "Unknown", "subscores": {}}
    
    scoring_method = assessment.get("scoring_method", "sum")
    
    if scoring_method == "sum":
        total = sum(a.get("value", 0) for a in answers)
        severity = get_severity(total, assessment.get("severity_bands", []))
        return {"total_score": total, "max_score": assessment.get("max_score"), "severity": severity, "subscores": {}}
    
    elif scoring_method == "sum_multiply":
        raw_total = sum(a.get("value", 0) for a in answers)
        multiplier = assessment.get("multiplier", 1)
        total = raw_total * multiplier
        severity = get_severity(total, assessment.get("severity_bands", []))
        return {"total_score": total, "raw_score": raw_total, "max_score": assessment.get("max_score"), "severity": severity, "subscores": {}}
    
    elif scoring_method == "subscales":
        subscales = assessment.get("subscales", {})
        subscores = {}
        for scale_name, scale_config in subscales.items():
            items = scale_config.get("items", [])
            multiplier = scale_config.get("multiplier", 1)
            scale_total = sum(answers[i-1].get("value", 0) for i in items if i <= len(answers)) * multiplier
            scale_severity = get_severity(scale_total, assessment.get("severity_bands", {}).get(scale_name, []))
            subscores[scale_name] = {"score": scale_total, "severity": scale_severity}
        return {"total_score": sum(s["score"] for s in subscores.values()), "subscores": subscores, "severity": None}
    
    elif scoring_method == "adhd_screener":
        # Count shaded responses in Part A
        part_a_count = 0
        questions = assessment.get("questions", [])
        for i, ans in enumerate(answers[:6]):
            q = questions[i] if i < len(questions) else {}
            threshold = q.get("shaded_threshold", 2)
            if ans.get("value", 0) >= threshold:
                part_a_count += 1
        severity = "Likely ADHD - Further evaluation recommended" if part_a_count >= 4 else "Unlikely ADHD (Part A)"
        return {"total_score": sum(a.get("value", 0) for a in answers), "part_a_score": part_a_count, "severity": severity, "subscores": {}}
    
    return {"total_score": 0, "severity": "Unknown", "subscores": {}}

def get_severity(score, bands):
    """Get severity label based on score and bands"""
    for band in bands:
        if band["min"] <= score <= band["max"]:
            return {"label": band["label"], "color": band["color"]}
    return {"label": "Unknown", "color": "gray"}
