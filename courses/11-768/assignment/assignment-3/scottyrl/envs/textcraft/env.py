"""TextCraft-Synth: craft target items up a synthetic recipe DAG (given).

The action space matches the TextCraft-Synth environment used in the
research literature exactly:

    craft(ingredients: dict, target: tuple[str, int])
    get_info(items: list)
    view_inventory()
    finish(message: str)

Crafting rules (these are strict):
  - `target` is (item_name, total_count); total_count must be divisible by
    the recipe's result_count.
  - `ingredients` must be EXACTLY the recipe's ingredients scaled by the
    number of crafts: no missing items, no wrong counts, no extras.
  - Ingredients are consumed from the inventory; raw materials only come
    from the task's initial inventory (there is no gather action).

Reward: 1.0 iff the agent calls finish() AND, for every target item,
(final inventory - initial inventory) >= required count. Ending the episode
without calling finish() scores 0 even if the items were crafted.

Task.info: {"target_items": {item: count}, "initial_inventory": {item: count},
            "difficulty": str, "max_depth": int, "num_craft_steps": int}
"""

from __future__ import annotations

import json

from scottyrl.envs.base import Env
from scottyrl.envs.textcraft.recipe_book import RecipeBook, default_recipe_book
from scottyrl.types import Observation, Task, ToolCall

TOOL_DOCS = """\
craft(ingredients: dict, target: tuple): craft items using ingredients from
  your inventory. `ingredients` is {item_name: count} to consume; `target` is
  (item_name, total_count) where total_count must be divisible by the
  recipe's result_count, and the ingredient counts must match the recipe
  scaled by the number of crafts -- exactly, with no extra items.
  Example: <tool>craft({"m0_i1": 2, "m1_i1": 1}, ("m2_i2", 2))</tool>
get_info(items: list): get recipe information for items. Returns, per item:
  {"item", "can_craft", "is_base", "in_inventory", "crafting_depth",
   "recipes": [{"ingredients": {...}, "result_count": int}, ...]}.
  crafting_depth: 0=base item, 1=direct craft, 2+=needs intermediate steps.
  Example: <tool>get_info(["m2_i2", "raw_a0"])</tool>
view_inventory(): view your current inventory as {item_name: count}.
  Example: <tool>view_inventory()</tool>
finish(message: str): complete the task. You MUST call this once the target
  items are crafted. Example: <tool>finish("crafted everything")</tool>"""


class TextCraftEnv(Env):
    def __init__(self, task: Task, recipe_book: RecipeBook | None = None):
        super().__init__(task)
        self.book = recipe_book if recipe_book is not None else default_recipe_book()
        self.initial_inventory: dict[str, int] = dict(task.info["initial_inventory"])
        self.inventory: dict[str, int] = dict(self.initial_inventory)
        self._finished_via_tool = False

    @property
    def tool_docs(self) -> str:
        return TOOL_DOCS

    async def _reset_state(self) -> None:
        self.inventory = dict(self.initial_inventory)
        self._finished_via_tool = False

    async def initial_observation(self) -> str:
        targets = ", ".join(f"{c}x {i}" for i, c in self.task.info["target_items"].items())
        return (
            f"Target: craft {targets}.\n"
            f"Initial inventory: {json.dumps(self.inventory)}\n"
            f"Use get_info([...]) to look up recipes. You have "
            f"{self.task.max_steps} steps; finish() when done."
        )

    async def apply(self, call: ToolCall) -> Observation:
        handler = getattr(self, f"_tool_{call.name}", None)
        if handler is None:
            return Observation(text=f"Unknown tool '{call.name}'.")
        return handler(call.args)

    # ------------------------------------------------------------- tools --

    def _tool_view_inventory(self, args: tuple) -> Observation:
        if args:
            return Observation(text="view_inventory() takes no arguments.")
        return Observation(text=json.dumps(dict(sorted(self.inventory.items()))))

    def _tool_get_info(self, args: tuple) -> Observation:
        if len(args) != 1 or not isinstance(args[0], (list, tuple)) or not all(
            isinstance(i, str) for i in args[0]
        ):
            return Observation(text="Invalid call. Use get_info(items: list of str).")
        results = []
        for item in args[0]:
            info = {
                "item": item,
                "can_craft": self.book.can_craft(item),
                "is_base": self.book.is_base_item(item),
                "in_inventory": self.inventory.get(item, 0),
                "crafting_depth": self.book.crafting_depth(item),
                "recipes": [
                    {"ingredients": r["ingredients"], "result_count": r["result_count"]}
                    for r in self.book.get_recipes_for_item(item)
                ],
            }
            results.append(info)
        return Observation(text=json.dumps(results))

    def _tool_craft(self, args: tuple) -> Observation:
        if len(args) != 2:
            return Observation(text="Invalid call. Use craft(ingredients: dict, target: tuple).")
        ingredients, target = args
        if not isinstance(ingredients, dict) or not all(
            isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in ingredients.items()
        ):
            return Observation(text="Error: ingredients must be a dict of {item_name: positive int}.")
        if (
            not isinstance(target, (tuple, list))
            or len(target) != 2
            or not isinstance(target[0], str)
            or not isinstance(target[1], int)
            or target[1] <= 0
        ):
            return Observation(text="Error: target must be a tuple of (item_name, positive int).")

        target_item, target_count = target
        recipes = self.book.get_recipes_for_item(target_item)
        if not recipes:
            return Observation(text=f"Error: No recipe found for {target_item}")

        errors = []
        for idx, recipe in enumerate(recipes):
            if target_count % recipe["result_count"] != 0:
                errors.append(
                    f"Recipe {idx + 1}: Target count {target_count} is not divisible "
                    f"by recipe result count {recipe['result_count']}"
                )
                continue
            num_crafts = target_count // recipe["result_count"]

            required = {ing: c * num_crafts for ing, c in recipe["ingredients"].items()}
            problem = None
            for ing, count in required.items():
                if ing not in ingredients:
                    problem = f"Missing required ingredient {ing}"
                    break
                if ingredients[ing] != count:
                    problem = f"Wrong amount of {ing}. Need {count}, provided {ingredients[ing]}"
                    break
            if problem is None:
                extras = [ing for ing in ingredients if ing not in required]
                if extras:
                    problem = f"Extra ingredients not required: {', '.join(extras)}"
            if problem is None:
                short = [
                    f"{ing}: need {count}, have {self.inventory.get(ing, 0)}"
                    for ing, count in required.items()
                    if self.inventory.get(ing, 0) < count
                ]
                if short:
                    problem = "Insufficient ingredients in inventory: " + ", ".join(short)
            if problem is not None:
                errors.append(f"Recipe {idx + 1}: {problem}")
                continue

            # This recipe works: consume and produce.
            for ing, count in required.items():
                self.inventory[ing] -= count
                if self.inventory[ing] <= 0:
                    del self.inventory[ing]
            self.inventory[target_item] = self.inventory.get(target_item, 0) + target_count
            return Observation(text=f"Successfully crafted {target_count} {target_item}(s)")

        return Observation(
            text=f"Error: All {len(recipes)} recipe(s) failed for {target_item}. Errors:\n"
            + "\n".join(errors)
        )

    def _tool_finish(self, args: tuple) -> Observation:
        if len(args) > 1 or (args and not isinstance(args[0], str)):
            return Observation(text="Invalid call. Use finish(message: str).")

        missing = {}
        for item, required in self.task.info["target_items"].items():
            crafted = self.inventory.get(item, 0) - self.initial_inventory.get(item, 0)
            if crafted < required:
                missing[item] = required - crafted

        if not missing:
            return Observation(text="Finished. All target items crafted!", reward=1.0, done=True)
        return Observation(
            text=f"Finished, but targets not met. Still missing: {json.dumps(missing)}",
            reward=0.0,
            done=True,
        )
