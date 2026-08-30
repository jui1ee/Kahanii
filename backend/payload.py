from pydantic import BaseModel, Field
from typing import List, Optional


class StoryToken(BaseModel):
    """One token in the parsed story."""
    display_word: str = Field(..., description="Original surface form as it appears in the story text.")
    lemma: str = Field(..., description="Lowercased lemma (used for dictionary lookup).")
    sign_video: Optional[str] = Field(
        None,
        description="Path to the sign video clip (e.g. '/signs/run.mp4'), or null if the word falls back to fingerspelling.",
    )
    is_fingerspelling: bool = Field(
        False,
        description="True when the UI should play letter-by-letter finger spelling instead of a single sign.",
    )
    scene_idx: int = Field(
        0,
        description="0-based sentence/scene index. All tokens in the same sentence share the same value.",
    )
