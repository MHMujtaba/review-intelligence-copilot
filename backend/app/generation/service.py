from textwrap import dedent

from app.core.config import get_settings
from app.schemas.contracts import RetrievedReview
from app.utils.text import extract_review_themes


class ContextBuilder:
    def build(self, query_type: str, reviews: list[RetrievedReview]) -> dict:
        positive_reviews = [review for review in reviews if review.overall >= 4.0]
        negative_reviews = [review for review in reviews if review.overall <= 2.0]
        representative_reviews = self._representative_reviews(reviews)
        weighted_insights = self._helpfulness_weighted_insights(reviews)

        return {
            "query_type": query_type,
            "top_positive_reviews": self._review_cards(positive_reviews[:3]),
            "top_negative_reviews": self._review_cards(negative_reviews[:3]),
            "representative_reviews": representative_reviews,
            "helpfulness_weighted_insights": weighted_insights,
            "positive_themes": extract_review_themes(positive_reviews, polarity="positive", limit=4),
            "negative_themes": extract_review_themes(negative_reviews, polarity="negative", limit=4),
        }

    def _review_cards(self, reviews: list[RetrievedReview]) -> list[dict]:
        return [
            {
                "review_id": review.review_id,
                "summary": review.summary,
                "review_text": review.review_text[:240].strip(),
                "overall": review.overall,
                "helpfulness_ratio": round(review.helpfulness_ratio, 3),
            }
            for review in reviews
        ]

    def _representative_reviews(self, reviews: list[RetrievedReview]) -> list[dict]:
        selected: list[dict] = []
        seen_aspects: set[str] = set()
        for review in reviews:
            aspect_key = f"{round(review.overall)}-{review.summary[:40].lower()}"
            if aspect_key in seen_aspects:
                continue
            seen_aspects.add(aspect_key)
            selected.append(
                {
                    "review_id": review.review_id,
                    "summary": review.summary,
                    "review_text": review.review_text[:240].strip(),
                    "overall": review.overall,
                    "helpfulness_ratio": round(review.helpfulness_ratio, 3),
                }
            )
            if len(selected) >= 4:
                break
        return selected

    def _helpfulness_weighted_insights(self, reviews: list[RetrievedReview]) -> list[dict]:
        sorted_reviews = sorted(reviews, key=lambda item: (item.helpfulness_ratio, item.final_score), reverse=True)
        insights: list[dict] = []
        for review in sorted_reviews[:4]:
            insights.append(
                {
                    "signal": review.summary or review.review_text[:80],
                    "overall": review.overall,
                    "helpfulness_ratio": round(review.helpfulness_ratio, 3),
                }
            )
        return insights


class GenerationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.context_builder = ContextBuilder()
    
    # async def answer(self, query: str, query_type: str, reviews: list[RetrievedReview]) -> tuple[str, dict]:
    #     context = self.context_builder.build(query_type, reviews)
    #     if self.settings.openai_api_key:
    #         try:
    #             answer = await self._answer_with_openai(query, context)
    #             return answer, context
    #         except Exception:
    #             pass
    #     return self._deterministic_answer(context), context

    # async def _answer_with_openai(self, query: str, context: dict) -> str:
    #     from openai import AsyncOpenAI

    #     client = AsyncOpenAI(api_key=self.settings.openai_api_key)
    #     prompt = dedent(
    #         f"""
    #         You are Review-Centric RAG Intelligence System.
    #         Use only the structured context below.
    #         Do not hallucinate or use outside knowledge.
    #         Summarize patterns across reviews rather than retelling a single review.

    #         User query: {query}

    #         Structured context:
    #         Top Positive Reviews: {context["top_positive_reviews"]}
    #         Top Negative Reviews: {context["top_negative_reviews"]}
    #         Representative Reviews: {context["representative_reviews"]}
    #         Helpfulness-weighted Insights: {context["helpfulness_weighted_insights"]}
    #         Positive Themes: {context["positive_themes"]}
    #         Negative Themes: {context["negative_themes"]}

    #         Output sections:
    #         Summary
    #         Pros
    #         Cons
    #         Key insights
    #         Overall sentiment
    #         """
    #     ).strip()

    #     response = await client.responses.create(model=self.settings.openai_model, input=prompt)
    #     return response.output_text.strip()
    # In your generator class

    # async def answer(
    #     self,
    #     query: str,
    #     query_type: str,
    #     reviews: list[RetrievedReview],
    #     mode: str = "ask",  # "ask" | "summary"
    # ) -> tuple[str, dict]:
    #     context = self.context_builder.build(query_type, reviews)
    #     if self.settings.openai_api_key:
    #         try:
    #             answer = await self._answer_with_openai(query, context, mode=mode)
    #             return answer, context
    #         except Exception:
    #             pass
    #     return self._deterministic_answer(context), context

    # async def _answer_with_openai(self, query: str, context: dict, mode: str = "ask") -> str:
    #     from openai import AsyncOpenAI

    #     client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    #     SYSTEM_PROMPT = dedent("""
    #         You are an internal product intelligence copilot for an e-commerce operations team.
    #         You have access to structured, retrieval-augmented review data for specific products (ASINs).
    #         Your role is to help analysts, PMs, and support teams make grounded decisions by surfacing
    #         patterns across customer reviews — complaints, praise, quality signals, and sentiment trends.

    #         Rules:
    #         - Use only the structured context provided. Never hallucinate or use outside knowledge.
    #         - Summarize patterns across reviews, not individual anecdotes.
    #         - Be concise and direct. This is an internal tool — skip pleasantries.
    #         - If the context does not contain enough information to answer, say so clearly.
    #     """).strip()

    #     CONTEXT_BLOCK = dedent(f"""
    #         Structured review context:
    #         - Top Positive Reviews: {context["top_positive_reviews"]}
    #         - Top Negative Reviews: {context["top_negative_reviews"]}
    #         - Representative Reviews: {context["representative_reviews"]}
    #         - Helpfulness-weighted Insights: {context["helpfulness_weighted_insights"]}
    #         - Positive Themes: {context["positive_themes"]}
    #         - Negative Themes: {context["negative_themes"]}
    #     """).strip()

    #     if mode == "summary":
    #         user_message = dedent(f"""
    #             Generate a structured product summary from the review context below.

    #             {CONTEXT_BLOCK}

    #             Output the following sections:
    #             Summary
    #             Pros
    #             Cons
    #             Key Insights
    #             Overall Sentiment
    #         """).strip()
    #     else:  # mode == "ask"
    #         print("here we are")
    #         user_message = dedent(f"""
    #             Answer the following question using only the review context below.
    #             Be direct and specific. Do not produce a generic summary — answer the question asked.

    #             Question: {query}

    #             {CONTEXT_BLOCK}
    #         """).strip()
    #     print(f"input: {SYSTEM_PROMPT} and {user_message}")

    #     response = await client.responses.create(
    #         model=self.settings.openai_model,
    #         instructions=SYSTEM_PROMPT,
    #         input=user_message,
    #     )
    #     print("response:",response)
    #     print(response.output_text.strip())
    #     return response.output_text.strip()
    
    async def answer(
        self,
        query: str,
        query_type: str,
        reviews: list[RetrievedReview],
        mode: str = "ask",
        previous_response_id: str | None = None,  # <-- new
    ) -> tuple[str, dict, str | None]:             # <-- also return response_id
        context = self.context_builder.build(query_type, reviews)
        if self.settings.openai_api_key:
            try:
                answer, response_id = await self._answer_with_openai(
                    query, context, mode=mode, previous_response_id=previous_response_id
                )
                return answer, context, response_id
            except Exception:
                pass
        return self._deterministic_answer(context), context, None

    async def _answer_with_openai(
        self,
        query: str,
        context: dict,
        mode: str = "ask",
        previous_response_id: str | None = None,  # <-- new
    ) -> tuple[str, str | None]:                   # <-- return (answer, response_id)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)

        SYSTEM_PROMPT = dedent("""
            You are an internal product intelligence copilot for an e-commerce operations team.
            You have access to structured, retrieval-augmented review data for specific products (ASINs).
            Your role is to help analysts, PMs, and support teams make grounded decisions by surfacing
            patterns across customer reviews — complaints, praise, quality signals, and sentiment trends.

            Rules:
            - Use only the structured context provided. Never hallucinate or use outside knowledge.
            - Summarize patterns across reviews, not individual anecdotes.
            - Be concise and direct. This is an internal tool — skip pleasantries.
            - If the context does not contain enough information to answer, say so clearly.
        """).strip()

        CONTEXT_BLOCK = dedent(f"""
            Structured review context:
            - Top Positive Reviews: {context["top_positive_reviews"]}
            - Top Negative Reviews: {context["top_negative_reviews"]}
            - Representative Reviews: {context["representative_reviews"]}
            - Helpfulness-weighted Insights: {context["helpfulness_weighted_insights"]}
            - Positive Themes: {context["positive_themes"]}
            - Negative Themes: {context["negative_themes"]}
        """).strip()

        if mode == "summary":
            user_message = dedent(f"""
                Generate a structured product summary from the review context below.

                {CONTEXT_BLOCK}

                Output the following sections:
                Summary
                Pros
                Cons
                Key Insights
                Overall Sentiment
            """).strip()
        else:  # mode == "ask"
            if previous_response_id:
                # History exists — only send the new query, no need to re-send context
                user_message = query
            else:
                # First turn — inject the review context so the model is grounded
                user_message = dedent(f"""
                    Answer the following question using only the review context below.
                    Be direct and specific. Do not produce a generic summary — answer the question asked.

                    Question: {query}

                    {CONTEXT_BLOCK}
                """).strip()

        kwargs = dict(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=user_message,
        )
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        # print("kwargs:",kwargs)
        response = await client.responses.create(**kwargs)
        # print("resp:",response.output_text.strip())
        return response.output_text.strip(), response.id  # <-- return the id

    def _deterministic_answer(self, context: dict) -> str:
        positives = context["positive_themes"] or ["No strong positive patterns retrieved."]
        negatives = context["negative_themes"] or ["No strong negative patterns retrieved."]

        sentiment = "mixed"
        if len(positives) > len(negatives):
            sentiment = "mostly positive"
        elif len(negatives) > len(positives):
            sentiment = "mostly negative"

        return dedent(
            f"""
            Summary
            - Customer feedback centers on {", ".join((positives + negatives)[:3])}.

            Pros
            - {positives[0]}
            - {positives[1] if len(positives) > 1 else positives[0]}

            Cons
            - {negatives[0]}
            - {negatives[1] if len(negatives) > 1 else negatives[0]}

            Key insights
            - The most helpful reviews emphasize: {", ".join(item["signal"] for item in context["helpfulness_weighted_insights"][:3]) or "limited high-helpfulness evidence"}.

            Overall sentiment
            - The retrieved review set suggests {sentiment} sentiment.
            """
        ).strip()
