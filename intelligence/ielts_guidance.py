"""
IELTS Guidance Module.

Structured guidance content for exam preparation, including
format explanation, band criteria, common mistakes, and strategies.
"""


class IELTSGuidance:
    """Static + dynamic IELTS guidance content."""

    @staticmethod
    def get_exam_format() -> dict:
        """Get IELTS Speaking exam format overview."""
        return {
            "overview": (
                "The IELTS Speaking test is a face-to-face interview lasting 11–14 minutes. "
                "It assesses your spoken English through three parts."
            ),
            "parts": [
                {
                    "name": "Part 1 — Introduction & Interview",
                    "duration": "4–5 minutes",
                    "description": (
                        "The examiner asks general questions about familiar topics like "
                        "your home, family, work, studies, and interests."
                    ),
                    "tips": [
                        "Give extended answers (2-3 sentences), not just 'yes' or 'no'",
                        "Use a range of tenses naturally",
                        "Be natural and relaxed — this is a warm-up section",
                    ],
                },
                {
                    "name": "Part 2 — Individual Long Turn (Cue Card)",
                    "duration": "3–4 minutes",
                    "description": (
                        "You receive a topic card and have 1 minute to prepare. "
                        "Then you speak for 1–2 minutes on the topic."
                    ),
                    "tips": [
                        "Use your 1-minute preparation time wisely — jot down key points",
                        "Cover ALL bullet points on the card",
                        "Speak for the full 2 minutes if possible",
                        "Use discourse markers: 'firstly', 'on the other hand', 'to sum up'",
                    ],
                },
                {
                    "name": "Part 3 — Two-way Discussion",
                    "duration": "4–5 minutes",
                    "description": (
                        "The examiner asks deeper, more abstract questions related "
                        "to the Part 2 topic. This tests your ability to discuss ideas."
                    ),
                    "tips": [
                        "Express and justify opinions",
                        "Compare different perspectives",
                        "Use academic vocabulary and complex sentences",
                        "Speculate about future trends or possibilities",
                    ],
                },
            ],
        }

    @staticmethod
    def get_band_criteria() -> list[dict]:
        """Get IELTS Speaking band score criteria breakdown."""
        return [
            {
                "criterion": "Fluency & Coherence",
                "weight": "25%",
                "bands": {
                    "7-9": "Speaks at length without noticeable effort. Uses connectives and discourse markers flexibly.",
                    "5-6": "Usually maintains flow but with repetition, self-correction, or slow speech. Simple connectives used.",
                    "3-4": "Long pauses, limited ability to link ideas. Speech is slow and fragmented.",
                },
                "tips": [
                    "Practice speaking without stopping to think too much",
                    "Use fillers like 'well', 'let me think' instead of long silence",
                    "Learn connective phrases: however, furthermore, in contrast",
                ],
            },
            {
                "criterion": "Lexical Resource",
                "weight": "25%",
                "bands": {
                    "7-9": "Uses vocabulary with flexibility and precision. Paraphrases effectively.",
                    "5-6": "Manages to talk about topics but uses limited vocabulary. Some inappropriate word choices.",
                    "3-4": "Uses simple vocabulary to convey basic meaning. Frequent errors in word choice.",
                },
                "tips": [
                    "Learn synonyms for common words (important → crucial, significant)",
                    "Use collocations (make a decision, take responsibility)",
                    "Practice paraphrasing — say the same thing in different words",
                ],
            },
            {
                "criterion": "Grammatical Range & Accuracy",
                "weight": "25%",
                "bands": {
                    "7-9": "Uses a range of complex structures with flexibility. Errors are rare.",
                    "5-6": "Produces basic sentence forms accurately. Attempts complex sentences with mixed success.",
                    "3-4": "Limited range of structures. Frequent errors that may obscure meaning.",
                },
                "tips": [
                    "Practice conditionals (If I were..., Had I known...)",
                    "Use passive voice naturally (It is believed that...)",
                    "Mix simple, compound, and complex sentences",
                ],
            },
            {
                "criterion": "Pronunciation",
                "weight": "25%",
                "bands": {
                    "7-9": "Uses features of connected speech (linking, weak forms). Easy to understand throughout.",
                    "5-6": "Generally intelligible. Some mispronunciations but rarely affect understanding.",
                    "3-4": "Pronunciation causes frequent difficulty for the listener.",
                },
                "tips": [
                    "Focus on word stress patterns",
                    "Practice sentence intonation — rising for questions, falling for statements",
                    "Record yourself and compare with native speakers",
                ],
            },
        ]

    @staticmethod
    def get_common_mistakes() -> list[dict]:
        """Get common IELTS speaking mistakes and how to avoid them."""
        return [
            {
                "mistake": "Memorizing answers",
                "why_bad": "Examiners can detect memorized responses and will lower your score",
                "fix": "Practice speaking about topics, not memorizing scripts",
            },
            {
                "mistake": "One-word answers",
                "why_bad": "Shows limited ability to communicate",
                "fix": "Always expand: give reasons, examples, and personal experiences",
            },
            {
                "mistake": "Using only simple vocabulary",
                "why_bad": "Limits your Lexical Resource score to Band 5-6",
                "fix": "Learn 5 new IELTS-relevant words daily and practice using them",
            },
            {
                "mistake": "Speaking too fast when nervous",
                "why_bad": "Reduces clarity and can affect pronunciation score",
                "fix": "Practice at a natural pace. Pausing briefly is better than rushing",
            },
            {
                "mistake": "Not answering the question",
                "why_bad": "Directly impacts Fluency & Coherence score",
                "fix": "Listen carefully, address the exact question, then expand",
            },
            {
                "mistake": "Ignoring Part 2 bullet points",
                "why_bad": "Shows inability to structure a speech",
                "fix": "Use your preparation time to address each bullet point",
            },
            {
                "mistake": "Using informal language",
                "why_bad": "IELTS is semi-formal — avoid slang",
                "fix": "Use 'approximately' not 'like about', 'considerable' not 'a lot'",
            },
        ]

    @staticmethod
    def get_daily_plan() -> list[dict]:
        """Get a suggested daily IELTS preparation plan."""
        return [
            {"time": "Morning (15 min)", "activity": "Review Word of the Day + example sentences"},
            {"time": "Midday (20 min)", "activity": "Practice speaking on a Part 2 cue card topic"},
            {"time": "Afternoon (10 min)", "activity": "Play vocabulary games for reinforcement"},
            {"time": "Evening (15 min)", "activity": "Have a conversation with the AI tutor"},
            {"time": "Before bed (5 min)", "activity": "Review today's vocabulary and corrections"},
        ]

    @staticmethod
    def get_exam_day_tips() -> list[str]:
        """Get exam day preparation tips."""
        return [
            "Get a good night's sleep — fatigue affects fluency",
            "Arrive early and stay calm — nervousness affects pronunciation",
            "Speak clearly at a natural pace — don't rush",
            "If you don't understand a question, ask the examiner to repeat it",
            "Use the 1-minute Part 2 preparation wisely — write key points",
            "Make eye contact with the examiner — it shows confidence",
            "If you make a mistake, correct yourself naturally and move on",
            "Don't worry about your accent — clarity matters more than accent",
            "Expand your answers — aim for 3-4 sentences in Part 1",
            "In Part 3, give opinions with reasons: 'I believe... because...'",
        ]

    @staticmethod
    def get_speaking_topics() -> dict:
        """Get common IELTS speaking topics by part."""
        return {
            "part1": [
                "Hometown", "Work or Studies", "Accommodation", "Family",
                "Friends", "Hobbies", "Sports", "Music", "Reading",
                "Travel", "Food", "Weather", "Technology", "Shopping",
                "Daily routine", "Weekends", "Holidays", "Animals",
            ],
            "part2": [
                {
                    "topic": "Describe a person who has influenced you",
                    "points": [
                        "Who this person is",
                        "How you know this person",
                        "What they did that influenced you",
                        "How you feel about this person",
                    ],
                },
                {
                    "topic": "Describe a place you would like to visit",
                    "points": [
                        "Where this place is",
                        "How you learned about it",
                        "What you would do there",
                        "Why you want to visit it",
                    ],
                },
                {
                    "topic": "Describe a skill you learned recently",
                    "points": [
                        "What the skill is",
                        "How you learned it",
                        "How difficult it was",
                        "How useful it is in your life",
                    ],
                },
                {
                    "topic": "Describe an important event in your life",
                    "points": [
                        "What the event was",
                        "When and where it happened",
                        "Who was involved",
                        "Why it was important to you",
                    ],
                },
                {
                    "topic": "Describe a book or movie that made an impression on you",
                    "points": [
                        "What it was about",
                        "When you read/watched it",
                        "What you liked about it",
                        "Why it made an impression",
                    ],
                },
            ],
            "part3_themes": [
                "Education and learning",
                "Technology and society",
                "Environment and sustainability",
                "Health and lifestyle",
                "Work and career",
                "Culture and traditions",
                "Media and communication",
                "Urbanization and city life",
            ],
        }

    @staticmethod
    def get_reading_practice_content() -> dict:
        """Get a mock IELTS reading passage and questions."""
        return {
            "title": "The Evolution of Renewable Energy",
            "passage": (
                "For decades, the global energy landscape has been dominated by fossil fuels. "
                "However, recent years have witnessed a paradigm shift towards renewable energy sources "
                "such as solar, wind, and hydroelectric power. This transition is primarily driven by "
                "the urgent need to mitigate climate change and reduce greenhouse gas emissions. "
                "Solar energy, in particular, has seen exponential growth due to significant cost reductions "
                "in photovoltaic technology.\n\n"
                "Despite these advancements, challenges remain. The intermittent nature of solar and wind "
                "power requires robust energy storage solutions. Lithium-ion batteries have emerged as a "
                "viable option, although concerns regarding resource extraction and battery disposal persist. "
                "Furthermore, upgrading existing electrical grids to accommodate decentralized energy generation "
                "is a colossal infrastructural undertaking.\n\n"
                "Governments worldwide are implementing policies to incentivize the adoption of renewables. "
                "Subsidies, tax credits, and carbon pricing are among the economic tools utilized to accelerate "
                "this transition. As technology continues to evolve, the prospect of a fully sustainable "
                "energy future becomes increasingly attainable, provided that international cooperation and "
                "investment remain steadfast."
            ),
            "questions": [
                {
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "What is the primary driver for the transition to renewable energy mentioned in the text?",
                    "options": [
                        "Technological advancements in battery storage.",
                        "The urgent need to mitigate climate change.",
                        "Government subsidies and tax credits.",
                        "The depletion of fossil fuel reserves."
                    ],
                    "answer": "The urgent need to mitigate climate change.",
                    "explanation": "The text explicitly states: 'This transition is primarily driven by the urgent need to mitigate climate change...'"
                },
                {
                    "id": "q2",
                    "type": "true_false_not_given",
                    "question": "Lithium-ion batteries are the only viable solution for energy storage.",
                    "options": ["True", "False", "Not Given"],
                    "answer": "False",
                    "explanation": "The text says they have 'emerged as a viable option', not that they are the 'only' viable option."
                },
                {
                    "id": "q3",
                    "type": "true_false_not_given",
                    "question": "Upgrading electrical grids is an easy and inexpensive process.",
                    "options": ["True", "False", "Not Given"],
                    "answer": "False",
                    "explanation": "The text describes it as a 'colossal infrastructural undertaking'."
                },
                {
                    "id": "q4",
                    "type": "multiple_choice",
                    "question": "Which of the following is NOT mentioned as an economic tool utilized by governments?",
                    "options": ["Subsidies", "Tax credits", "Import tariffs", "Carbon pricing"],
                    "answer": "Import tariffs",
                    "explanation": "The text mentions 'Subsidies, tax credits, and carbon pricing'. Import tariffs are not mentioned."
                }
            ]
        }

    @staticmethod
    def get_listening_practice_content() -> dict:
        """Get a mock IELTS listening script and questions."""
        return {
            "title": "University Library Orientation",
            "audio_text": (
                "Welcome to the central university library. I'm Sarah, the head librarian. "
                "Let me give you a quick overview of our facilities. On the ground floor, you'll "
                "find the main reception desk and the short-loan collection. This is where you can "
                "borrow course textbooks for up to 24 hours. The IT helpdesk is also located here "
                "in the east wing.\n\n"
                "Moving up to the first floor, we have the science and engineering sections. Please note "
                "that this is a strict silent zone. Group study rooms are available on the second floor, "
                "which houses the arts and humanities collections. You need to book these rooms in advance "
                "using the library app. Finally, the cafe is situated in the basement, open from 8 AM to 8 PM. "
                "Remember, no food or drink is allowed outside the cafe area. We hope you enjoy using the library."
            ),
            "questions": [
                {
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "Where is the IT helpdesk located?",
                    "options": [
                        "First floor",
                        "Ground floor, east wing",
                        "Second floor",
                        "Basement"
                    ],
                    "answer": "Ground floor, east wing",
                    "explanation": "The speaker says: 'The IT helpdesk is also located here (on the ground floor) in the east wing.'"
                },
                {
                    "id": "q2",
                    "type": "multiple_choice",
                    "question": "How long can textbooks from the short-loan collection be borrowed?",
                    "options": [
                        "48 hours",
                        "One week",
                        "24 hours",
                        "Until the end of the term"
                    ],
                    "answer": "24 hours",
                    "explanation": "The speaker states: 'This is where you can borrow course textbooks for up to 24 hours.'"
                },
                {
                    "id": "q3",
                    "type": "true_false_not_given",
                    "question": "Group study rooms on the second floor can be used without prior reservation.",
                    "options": ["True", "False", "Not Given"],
                    "answer": "False",
                    "explanation": "The speaker explicitly mentions: 'You need to book these rooms in advance using the library app.'"
                },
                {
                    "id": "q4",
                    "type": "true_false_not_given",
                    "question": "The cafe on the ground floor is open 24 hours.",
                    "options": ["True", "False", "Not Given"],
                    "answer": "False",
                    "explanation": "The speaker says the cafe is situated in the basement, not the ground floor, and is open from 8 AM to 8 PM."
                }
            ]
        }
