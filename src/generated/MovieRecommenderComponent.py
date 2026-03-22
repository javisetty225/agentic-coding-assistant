from langflow.custom import Component
from langflow.inputs import (
    MessageTextInput,
    StrInput,
    DropdownInput,
    IntInput,
    SecretStrInput,
)
from langflow.outputs import MessageOutput
from langflow.schema.message import Message
from openai import OpenAI
import json


class MovieRecommenderComponent(Component):
    """
    CineBot – AI-powered movie recommendation engine.

    Inputs
    ------
    genres               : Comma-separated favourite genres (e.g. "Action, Sci-Fi")
    mood                 : Current viewer mood selected from a dropdown
    num_recommendations  : How many films to suggest (1–10, default 5)
    era_preference       : Preferred cinema era (Any / Classic / 80s-90s / 2000s / 2010s / 2020+)
    additional_preferences: Free-text extras ("Family friendly", "No subtitles", etc.)
    openai_api_key       : OpenAI secret key (stored securely)
    model_name           : GPT model to use (gpt-4o / gpt-4-turbo / gpt-3.5-turbo)

    Outputs
    -------
    recommendations : Formatted markdown list of movies with ratings & streaming hints
    reasoning       : CineBot's detailed reasoning for each pick
    """

    display_name = "Movie Recommender"
    description = (
        "Takes a user's favourite genres and current mood, then returns "
        "personalised movie recommendations powered by an LLM."
    )
    icon = "film"

    # ------------------------------------------------------------------ inputs
    inputs = [
        MessageTextInput(
            name="genres",
            display_name="Favorite Genres",
            info=(
                "Comma-separated list of favourite movie genres "
                "(e.g. 'Action, Sci-Fi, Comedy')."
            ),
            value="Action, Sci-Fi",
        ),
        DropdownInput(
            name="mood",
            display_name="Current Mood",
            info="Select the viewer's current mood to tailor recommendations.",
            options=[
                "Happy",
                "Sad",
                "Excited",
                "Relaxed",
                "Scared / Thrilled",
                "Romantic",
                "Nostalgic",
                "Curious / Intellectual",
                "Adventurous",
                "Bored",
            ],
            value="Happy",
        ),
        IntInput(
            name="num_recommendations",
            display_name="Number of Recommendations",
            info="How many movies to recommend (1–10).",
            value=5,
        ),
        DropdownInput(
            name="era_preference",
            display_name="Era Preference",
            info="Preferred movie era.",
            options=[
                "Any Era",
                "Classic (Before 1980)",
                "80s & 90s",
                "2000s",
                "2010s",
                "Recent (2020+)",
            ],
            value="Any Era",
        ),
        StrInput(
            name="additional_preferences",
            display_name="Additional Preferences",
            info=(
                "Optional free-text preferences "
                "(e.g. 'No subtitles', 'Family friendly', 'Based on a true story')."
            ),
            value="",
        ),
        SecretStrInput(
            name="openai_api_key",
            display_name="OpenAI API Key",
            info="Your OpenAI API key for generating recommendations.",
        ),
        DropdownInput(
            name="model_name",
            display_name="OpenAI Model",
            options=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            value="gpt-4o",
            info="The OpenAI chat model to use for generating recommendations.",
        ),
    ]

    # ----------------------------------------------------------------- outputs
    outputs = [
        MessageOutput(
            name="recommendations",
            display_name="Movie Recommendations",
            method="recommend_movies",
        ),
        MessageOutput(
            name="reasoning",
            display_name="Recommendation Reasoning",
            method="get_reasoning",
        ),
    ]

    # ============================================================= private helpers

    def _build_system_prompt(self) -> str:
        return (
            "You are CineBot, an expert movie critic and recommendation engine with "
            "encyclopedic knowledge of cinema across all genres, eras, and cultures. "
            "When given a viewer's preferences you return thoughtful, varied, and "
            "personalised movie recommendations. You always explain WHY each film "
            "matches the viewer's mood and genre taste. Your tone is friendly, "
            "enthusiastic, and concise. You must respond ONLY with a valid JSON object "
            "— no markdown fences, no extra commentary."
        )

    def _build_user_prompt(self) -> str:
        extra = (
            f"\n- Additional preferences: {self.additional_preferences}"
            if str(self.additional_preferences).strip()
            else ""
        )
        n = int(self.num_recommendations)
        return (
            f"Please recommend exactly {n} movies for a viewer with the following profile:\n\n"
            f"- Favourite genres: {self.genres}\n"
            f"- Current mood: {self.mood}\n"
            f"- Era preference: {self.era_preference}"
            f"{extra}\n\n"
            "Return your answer as a **valid JSON object** with this exact structure:\n"
            "{\n"
            '  "recommendations": [\n'
            "    {\n"
            '      "rank": 1,\n'
            '      "title": "Movie Title",\n'
            '      "year": 2021,\n'
            '      "genre": "Primary Genre",\n'
            '      "director": "Director Name",\n'
            '      "imdb_rating": 8.2,\n'
            '      "why_recommended": "Short explanation tied to mood and genre",\n'
            '      "mood_match": "Emoji + one-line mood match",\n'
            '      "streaming_hint": "Likely available on Netflix / Prime / etc."\n'
            "    }\n"
            "  ],\n"
            '  "summary": "One paragraph summarising the set and why it suits this viewer."\n'
            "}\n\n"
            "Return ONLY the JSON object — no markdown fences, no extra text."
        )

    def _call_llm(self) -> dict:
        """Calls the OpenAI chat API and parses the JSON response."""
        client = OpenAI(api_key=self.openai_api_key)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user",   "content": self._build_user_prompt()},
            ],
            temperature=0.8,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)

    def _format_recommendations(self, data: dict) -> str:
        """Renders the parsed LLM JSON as a pretty markdown string."""
        lines: list[str] = []

        # ── Header ────────────────────────────────────────────────────
        lines.append("# 🎬 Your Personalised Movie Recommendations\n")
        lines.append(f"> **Mood:** {self.mood}  ·  **Genres:** {self.genres}  ·  **Era:** {self.era_preference}\n")
        lines.append("---\n")

        # ── Movie cards ───────────────────────────────────────────────
        for movie in data.get("recommendations", []):
            rank          = movie.get("rank", "?")
            title         = movie.get("title", "Unknown")
            year          = movie.get("year", "?")
            genre         = movie.get("genre", "?")
            director      = movie.get("director", "?")
            rating        = movie.get("imdb_rating", "N/A")
            why           = movie.get("why_recommended", "")
            mood_match    = movie.get("mood_match", "")
            streaming     = movie.get("streaming_hint", "Check JustWatch")

            lines.append(f"## {rank}. {title} ({year})")
            lines.append(
                f"**Genre:** {genre}  |  **Director:** {director}  |  ⭐ {rating}/10"
            )
            lines.append(f"\n**Why watch it?** {why}")
            lines.append(f"**Mood match:** {mood_match}")
            lines.append(f"**Where to watch:** 📺 {streaming}\n")
            lines.append("---\n")

        # ── Summary ───────────────────────────────────────────────────
        if summary := data.get("summary"):
            lines.append("### 🤖 CineBot's Take")
            lines.append(summary)

        return "\n".join(lines)

    def _format_reasoning(self, data: dict) -> str:
        """Renders the per-movie reasoning as a markdown string."""
        lines: list[str] = ["## 🧠 CineBot Reasoning\n"]

        if summary := data.get("summary"):
            lines.append(f"**Overview:** {summary}\n")

        lines.append("### Per-movie rationale\n")
        for movie in data.get("recommendations", []):
            title = movie.get("title", "Unknown")
            why   = movie.get("why_recommended", "No explanation provided.")
            mood  = movie.get("mood_match", "")
            lines.append(f"**{title}**")
            lines.append(f"- Rationale: {why}")
            if mood:
                lines.append(f"- Mood match: {mood}")
            lines.append("")

        return "\n".join(lines)

    # ============================================================== output methods

    def recommend_movies(self) -> Message:
        """Primary output: formatted markdown movie list."""
        try:
            data = self._call_llm()
            # Cache so get_reasoning() can reuse the same LLM result in a single run
            self._llm_cache: dict = data
            return Message(text=self._format_recommendations(data))
        except json.JSONDecodeError as exc:
            return Message(text=f"⚠️ Could not parse LLM response as JSON: {exc}")
        except Exception as exc:
            return Message(text=f"⚠️ Error fetching recommendations: {exc}")

    def get_reasoning(self) -> Message:
        """Secondary output: CineBot's reasoning for each pick."""
        try:
            # Reuse cached response if recommend_movies() already ran
            data: dict = getattr(self, "_llm_cache", None) or self._call_llm()
            return Message(text=self._format_reasoning(data))
        except Exception as exc:
            return Message(text=f"⚠️ Error generating reasoning: {exc}")
