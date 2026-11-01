"""Recipe book for TextCraft-Synth (given).

The full synthetic recipe database ships with the repo as
`data/textcraft_recipes.json` (1,452 items, 1,402 craftable). The datasets
in `data/textcraft_*.jsonl` were generated against exactly this book; do not
edit it.

Format:
    {"base_items": [item, ...],
     "recipes": {item: [{"ingredients": {item: count}, "result_count": int},
                        ...]}}

An item can have multiple recipes; base items have none and can never be
crafted (they only come from the task's initial inventory).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "textcraft_recipes.json"


class RecipeBook:
    def __init__(self, base_items: set[str], recipes: dict[str, list[dict]]):
        self.base_items = set(base_items)
        self.recipes = recipes
        self.all_items = self.base_items | set(recipes)
        self._depth_cache: dict[str, int] = {}

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeBook":
        return cls(set(data["base_items"]), data["recipes"])

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_PATH) -> "RecipeBook":
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def get_recipes_for_item(self, item: str) -> list[dict]:
        return self.recipes.get(item, [])

    def can_craft(self, item: str) -> bool:
        return item in self.recipes

    def is_base_item(self, item: str) -> bool:
        return item in self.base_items

    def crafting_depth(self, item: str) -> int:
        """0 for base/unknown items; 1 + max ingredient depth otherwise."""
        if item in self._depth_cache:
            return self._depth_cache[item]
        if item not in self.recipes:
            return 0
        self._depth_cache[item] = 0  # cycle guard (recipes form a DAG, but be safe)
        recipe = self.recipes[item][0]
        depth = 1 + max((self.crafting_depth(ing) for ing in recipe["ingredients"]), default=0)
        self._depth_cache[item] = depth
        return depth


@lru_cache(maxsize=1)
def default_recipe_book() -> RecipeBook:
    return RecipeBook.from_file()
