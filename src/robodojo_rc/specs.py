"""The six RoboDojo-RC Tier 1 tasks, copied from Robocurve's benchmark release 1.0.0.

Instruction, rubric (name, revision, guidance, levels) and equipment are exactly as released;
the release's setup and reset text point at this repository's copy of each setup photo.
The instruction is all the model is told. The judge's prompt holds the instruction and the whole
rubric, so any change to either is a new task version and a new rubric revision.
Rubric scores 0 and 1 stay integers on purpose: the judge prompt prints them as "Score 0" and
"Score 1", as in every published grade.
"""

from __future__ import annotations

from dataclasses import dataclass

RELEASE = "1.0.0"
"""The Robocurve benchmark release these tasks come from."""


@dataclass(frozen=True)
class Level:
    """One rubric level: the score it gives and the condition that earns it."""

    score: float
    value: str
    title: str
    description: str


@dataclass(frozen=True)
class Rubric:
    """A task's adapted rubric at one pinned revision; its levels are the only allowed scores."""

    name: str
    revision: str
    guidance: str
    levels: tuple[Level, ...]

    @property
    def scores(self) -> tuple[float, ...]:
        """The allowed trial scores, lowest first."""
        return tuple(level.score for level in self.levels)


@dataclass(frozen=True)
class Equipment:
    """An object the task needs, with the product the published runs used."""

    name: str
    quantity: int
    product: str
    url: str


@dataclass(frozen=True)
class TaskSpec:
    """One task: what the model is told, how the table is set, and how a trial is scored."""

    key: str
    release_id: str
    name: str
    version: int
    source_title: str
    source_url: str
    instruction: str
    setup: str
    reset: str
    rubric: Rubric
    equipment: tuple[Equipment, ...]
    photo: str


SPECS: tuple[TaskSpec, ...] = (
    TaskSpec(
        key="pack_and_pour_fruit",
        release_id="RD-pack-pour",
        name="Pack And Pour Fruit",
        version=1,
        source_title="Pack And Pour Fruit",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/pack-and-pour-fruit/",
        instruction="Place all the fruits into the blue bowl, then pour the fruits from the blue bowl into the large white bowl.",
        setup="There are several fruits, a blue bowl, and a large white bowl on the table. The robot needs to pick up all the fruits and place them into the blue bowl, then transfer them by pouring the fruits from the blue bowl into the large white bowl. Place everything as in the setup photo (docs/assets/pack_and_pour_fruit-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/pack_and_pour_fruit-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Pack And Pour Fruit",
            revision="79e63ce111e0",
            guidance="Adapted rubric agreed 2026-09-22. Award the highest qualifying score; never add scores. Picked up/gripped and lifted means the held object visibly clears its supporting surface. Lifting and contact milestones retain credit once achieved. Unless explicitly excepted, upright, overlapping, stacked, and contained-object conditions must hold at trial end. EXCEPTION: Packing scores 0.1, 0.3, and 0.5 retain credit once achieved, even if later spilling or unsuccessful pouring undoes that progress. Count the maximum number simultaneously contained in the small bowl, not cumulative placements. Scores 0.7 through 1.0 require all three fruits to have been packed first; 0.7 requires lifting with all three still inside. Pouring credit requires transfer by pouring, not direct placement, and the poured fruit must remain in the large bowl at trial end. Examples: two packed then spilled = 0.3; three packed then spilled before lifting = 0.5; lifted with all three then all spilled = 0.7.",
            levels=(
                Level(
                    score=0,
                    value="adapted_v2_score_0",
                    title="0",
                    description="No fruit successfully packed and no higher criterion achieved.",
                ),
                Level(
                    score=0.1,
                    value="adapted_v2_score_0_1",
                    title="0.1",
                    description="One fruit successfully placed into the small bowl.",
                ),
                Level(
                    score=0.3,
                    value="adapted_v2_score_0_3",
                    title="0.3",
                    description="Two fruits successfully contained in the small bowl at the same time.",
                ),
                Level(
                    score=0.5,
                    value="adapted_v2_score_0_5",
                    title="0.5",
                    description="Three fruits successfully contained in the small bowl at the same time.",
                ),
                Level(
                    score=0.7,
                    value="adapted_v2_score_0_7",
                    title="0.7",
                    description="Small bowl lifted clear of its supporting surface with all three fruits inside.",
                ),
                Level(
                    score=0.8,
                    value="adapted_v2_score_0_8",
                    title="0.8",
                    description="One fruit poured from the small bowl into the large bowl and remains there at trial end.",
                ),
                Level(
                    score=0.9,
                    value="adapted_v2_score_0_9",
                    title="0.9",
                    description="Two fruits poured from the small bowl into the large bowl and remain there at trial end.",
                ),
                Level(
                    score=1,
                    value="adapted_v2_score_1",
                    title="1",
                    description="All three fruits poured from the small bowl into the large bowl and remain there at trial end.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Small blue bowl",
                quantity=1,
                product="MASTERCOOK pastel plastic bowls, 15 oz, 6 pack",
                url="https://www.amazon.com/dp/B0GY9S1P3C",
            ),
            Equipment(
                name="Large white receiving bowl (squat truncated cone)",
                quantity=1,
                product="Gibson Home Great Essentials white ceramic bowl, 9.4 x 4 inches, 80 oz",
                url="https://www.target.com/p/-/A-92374680",
            ),
            Equipment(
                name="Yellow lemon prop",
                quantity=1,
                product="ZhangyiHot artificial yellow mini lemons, 6 pack",
                url="https://www.amazon.com/dp/B0DFGRFNFS",
            ),
            Equipment(
                name="Green pear prop",
                quantity=1,
                product="DisplayFakeFoods Fruit Assortment In Wire Bowl, SKU 5510",
                url="https://displayfakefoods.com/fruit-assortment-in-wire-bowl/",
            ),
            Equipment(
                name="Dark plum prop",
                quantity=1,
                product="DisplayFakeFoods Fruit Assortment In Wire Bowl, SKU 5510",
                url="https://displayfakefoods.com/fruit-assortment-in-wire-bowl/",
            ),
        ),
        photo="docs/assets/pack_and_pour_fruit-setup.jpg",
    ),
    TaskSpec(
        key="stack_bowls",
        release_id="RD-stack-bowls",
        name="Stack Bowls",
        version=1,
        source_title="Stack Bowls",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/stack-bowls/",
        instruction="Stack the bowls on the table.",
        setup="There are several bowls on the table. The robot needs to pick them up one by one and stack them neatly. Place everything as in the setup photo (docs/assets/stack_bowls-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/stack_bowls-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Stack Bowls",
            revision="e37caa41aa28",
            guidance="Adapted rubric agreed 2026-09-22. Award the highest qualifying score; never add scores. Picked up/gripped and lifted means the held object visibly clears its supporting surface. Lifting and contact milestones retain credit once achieved. Unless explicitly excepted, upright, overlapping, stacked, and contained-object conditions must hold at trial end. Overlapping means a bowl rests partly on another after release. For three bowls, all three must form one connected arrangement. Stacked means properly nested and stable.",
            levels=(
                Level(
                    score=0,
                    value="adapted_v2_score_0",
                    title="0",
                    description="No qualifying overlap or stack at trial end.",
                ),
                Level(
                    score=0.25,
                    value="adapted_v2_score_0_25",
                    title="0.25",
                    description="Two bowls overlapping at trial end.",
                ),
                Level(
                    score=0.5,
                    value="adapted_v2_score_0_5",
                    title="0.5",
                    description="Two bowls stacked at trial end.",
                ),
                Level(
                    score=0.75,
                    value="adapted_v2_score_0_75",
                    title="0.75",
                    description="Three bowls overlapping in one connected arrangement at trial end.",
                ),
                Level(
                    score=1,
                    value="adapted_v2_score_1",
                    title="1",
                    description="Three bowls stacked at trial end.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Pale green/cream bowl (left)",
                quantity=1,
                product="MASTERCOOK pastel plastic bowls, 15 oz, 6 pack",
                url="https://www.amazon.com/dp/B0GY9S1P3C",
            ),
            Equipment(
                name="Blue bowl (middle)",
                quantity=1,
                product="MASTERCOOK pastel plastic bowls, 15 oz, 6 pack",
                url="https://www.amazon.com/dp/B0GY9S1P3C",
            ),
            Equipment(
                name="Peach/pink bowl (right)",
                quantity=1,
                product="MASTERCOOK pastel plastic bowls, 15 oz, 6 pack",
                url="https://www.amazon.com/dp/B0GY9S1P3C",
            ),
        ),
        photo="docs/assets/stack_bowls-setup.jpg",
    ),
    TaskSpec(
        key="store_in_safe",
        release_id="RD-store-safe",
        name="Store In Safe",
        version=1,
        source_title="Store In Safe",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/store-in-safe/",
        instruction="Place all the objects into the safe, then close the safe.",
        setup="There are multiple objects on the table and a safe nearby. The robot needs to pick up all the objects one by one, place them into the safe, and then close the safe. Place everything as in the setup photo (docs/assets/store_in_safe-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/store_in_safe-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Store In Safe",
            revision="ff1828950ed0",
            guidance="Adapted rubric agreed 2026-09-22. Award the highest qualifying score; never add scores. Picked up/gripped and lifted means the held object visibly clears its supporting surface. Lifting and contact milestones retain credit once achieved. Unless explicitly excepted, upright, overlapping, stacked, and contained-object conditions must hold at trial end. No requirement to move the safe to the center of the table. A lid folded down over the opening counts as closed even when the contents hold it ajar or it does not latch; the robot is not penalized for a lid the objects prop open (rubric v2, 2026-10-23).",
            levels=(
                Level(
                    score=0,
                    value="adapted_v2_score_0",
                    title="0",
                    description="No objects inside the safe at trial end.",
                ),
                Level(
                    score=0.25,
                    value="adapted_v2_score_0_25",
                    title="0.25",
                    description="One object inside the safe at trial end.",
                ),
                Level(
                    score=0.5,
                    value="adapted_v2_score_0_5",
                    title="0.5",
                    description="Two objects inside the safe at trial end.",
                ),
                Level(
                    score=0.75,
                    value="adapted_v2_score_0_75",
                    title="0.75",
                    description="Three objects inside the safe at trial end.",
                ),
                Level(
                    score=1,
                    value="adapted_v2_score_1",
                    title="1",
                    description="Three objects inside the safe and the lid folded down over the opening at trial end, even if it rests on the contents or springs partly open when released.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Silver metal hinged case (called safe)",
                quantity=1,
                product="Housoutil silver aluminum briefcase with lock",
                url="https://www.amazon.com/dp/B0D8TKQN7X",
            ),
            Equipment(
                name="Red lining for case base and lid",
                quantity=1,
                product="Mesheshe red self-adhesive felt, 17 × 130 inch",
                url="https://www.amazon.com/dp/B09M7JV5YK",
            ),
            Equipment(
                name="Yellow lemon prop",
                quantity=1,
                product="ZhangyiHot artificial yellow mini lemons, 6 pack",
                url="https://www.amazon.com/dp/B0DFGRFNFS",
            ),
            Equipment(
                name="Light-colored Ryan figurine key holder",
                quantity=1,
                product="GIYOMGIYOM KAKA0 Ryan/Choonsik car smart key holder (Ryan Figurine)",
                url="https://www.amazon.com/dp/B0CZNLH4ZM",
            ),
            Equipment(
                name="Brown baby monkey plush",
                quantity=1,
                product="Tezituor 17.7 inch hanging mother and baby monkey plush set",
                url="https://www.amazon.com/dp/B0G8FRC3NV",
            ),
        ),
        photo="docs/assets/store_in_safe-setup.jpg",
    ),
    TaskSpec(
        key="cap_pen",
        release_id="RD-cap-pen",
        name="Cap Pen",
        version=1,
        source_title="Cap Pen",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/cap-pen/",
        instruction="Pick up the pen and the pen cap, then put the cap on the pen.",
        setup="There is a pen and a pen cap on the table. The robot needs to pick up both the pen and the cap, align them properly, and put the cap onto the pen. Place everything as in the setup photo (docs/assets/cap_pen-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/cap_pen-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Cap Pen",
            revision="02bd043f5381",
            guidance="Adapted rubric agreed 2026-09-22. Award the highest qualifying score; never add scores. Picked up/gripped and lifted means the held object visibly clears its supporting surface. Lifting and contact milestones retain credit once achieved. Unless explicitly excepted, upright, overlapping, stacked, and contained-object conditions must hold at trial end.",
            levels=(
                Level(
                    score=0,
                    value="adapted_v2_score_0",
                    title="0",
                    description="Neither pen nor cap picked up.",
                ),
                Level(
                    score=0.2,
                    value="adapted_v2_score_0_2",
                    title="0.2",
                    description="Pen or cap picked up.",
                ),
                Level(
                    score=0.5,
                    value="adapted_v2_score_0_5",
                    title="0.5",
                    description="Pen and cap both held off the surface simultaneously.",
                ),
                Level(
                    score=0.75,
                    value="adapted_v2_score_0_75",
                    title="0.75",
                    description="Pen and cap touch while both are held in the air. No alignment requirement.",
                ),
                Level(
                    score=1,
                    value="adapted_v2_score_1",
                    title="1",
                    description="Cap successfully placed onto the pen and remains attached at trial end.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Clear-barrel black ballpoint pen",
                quantity=1,
                product="BIC Cristal Xtra Bold black pens, 24 pack",
                url="https://www.amazon.com/dp/B004GEC2KC",
            ),
            Equipment(
                name="Matching black pen cap",
                quantity=1,
                product="BIC Cristal Xtra Bold black pens, 24 pack",
                url="https://www.amazon.com/dp/B004GEC2KC",
            ),
        ),
        photo="docs/assets/cap_pen-setup.jpg",
    ),
    TaskSpec(
        key="stand_up_bottles",
        release_id="RD-bottles",
        name="Stand Up Bottles",
        version=1,
        source_title="Stand Up Bottles",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/stand-up-bottles/",
        instruction="Stand all three bottles upright.",
        setup="There is a bottle lying on the table. The robot needs to pick it up and place it upright on the table. Place everything as in the setup photo (docs/assets/stand_up_bottles-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/stand_up_bottles-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Stand Up Bottles",
            revision="3ef7c2f54948",
            guidance="Award the highest qualifying score; never add scores. Gripped and lifted means the held bottle visibly clears its supporting surface. Tilted at least halfway upright means a bottle's top is raised roughly 45 degrees or more from lying flat while its bottom is in contact with or facing the desk. Held upright means the bottle is vertical on its base while a gripper still holds it. Standing means upright on its base and released (not held by a gripper). Scores 0.1 through 0.85 retain credit once achieved at any point in the trial; knocking a bottle over later does not remove that credit. Scores 0.4 and 0.7 count the maximum number of bottles standing simultaneously at any point. The second-bottle milestone (0.55) only counts while one other bottle is standing at that moment; the third-bottle milestone (0.85) only counts while two other bottles are standing at that moment. Only score 1 requires all three bottles standing at trial end.",
            levels=(
                Level(
                    score=0,
                    value="v2_score_0",
                    title="0",
                    description="No bottle gripped and lifted, tilted, or held upright.",
                ),
                Level(
                    score=0.1,
                    value="v2_score_0_1",
                    title="0.1",
                    description="A bottle gripped and lifted clear of its supporting surface.",
                ),
                Level(
                    score=0.25,
                    value="v2_score_0_25",
                    title="0.25",
                    description="A bottle tilted at least halfway upright or held upright at some point during the trial.",
                ),
                Level(
                    score=0.4,
                    value="v2_score_0_4",
                    title="0.4",
                    description="One bottle standing (upright and released) at some point during the trial.",
                ),
                Level(
                    score=0.55,
                    value="v2_score_0_55",
                    title="0.55",
                    description="One bottle standing and a second bottle tilted at least halfway upright or held upright at the same time.",
                ),
                Level(
                    score=0.7,
                    value="v2_score_0_7",
                    title="0.7",
                    description="Two bottles standing simultaneously at some point during the trial.",
                ),
                Level(
                    score=0.85,
                    value="v2_score_0_85",
                    title="0.85",
                    description="Two bottles standing and the third bottle tilted at least halfway upright or held upright at the same time.",
                ),
                Level(
                    score=1,
                    value="v2_score_1",
                    title="1",
                    description="All three bottles standing at trial end.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Clear Arrowhead water bottles with caps",
                quantity=3,
                product="Arrowhead water, 16.9 fl oz, 24 pack",
                url="https://www.amazon.com/dp/B000R5NRPI",
            ),
        ),
        photo="docs/assets/stand_up_bottles-setup.jpg",
    ),
    TaskSpec(
        key="sort_objects",
        release_id="RD-classify",
        name="Sort Objects",
        version=1,
        source_title="Classify Objects",
        source_url="https://robodojo-benchmark.com/doc/real-tasks/classify-objects/",
        instruction="Classify the two types of objects on the table and place them into the two baskets.",
        setup="There are two categories of objects and two baskets on the table. The robot needs to identify the category of each object, classify them accordingly, and place each type into the correct basket. Place everything as in the setup photo (docs/assets/sort_objects-setup.jpg), the team's reference layout.",
        reset="Put every object back where it is in the setup photo (docs/assets/sort_objects-setup.jpg), arms parked.",
        rubric=Rubric(
            name="Classify Objects",
            revision="b98515b26109",
            guidance="Grade the final state of the trial. There are two categories with three objects each and two baskets.\nAssign a different category to each basket. If the setup specifies the assignment, use it. Otherwise either assignment is acceptable: use the assignment giving the higher total, with one basket per category. Do not count the same category in both baskets.\nScore each basket separately:\n0 - Empty, mixed (contains objects from both categories), or contains only objects of the category assigned to the other basket.\n0.17 - One object of its assigned category, with no unrelated objects.\n0.33 - Two objects of its assigned category, with no unrelated objects.\n0.5 - All three objects of its assigned category, with no unrelated objects.\nAdd the two basket scores and select the matching total below. Mixed baskets always score zero. Maximum total is 1.0. Use the agreed decimal scores as written (for example, 0.17 + 0.17 = 0.34 and 0.33 + 0.33 = 0.66).",
            levels=(
                Level(
                    score=0,
                    value="pure_baskets_v3_score_0",
                    title="0",
                    description="Both baskets score 0.",
                ),
                Level(
                    score=0.17,
                    value="pure_baskets_v3_score_0_17",
                    title="0.17",
                    description="Basket scores 0.17 + 0, in either order.",
                ),
                Level(
                    score=0.33,
                    value="pure_baskets_v3_score_0_33",
                    title="0.33",
                    description="Basket scores 0.33 + 0, in either order.",
                ),
                Level(
                    score=0.34,
                    value="pure_baskets_v3_score_0_34",
                    title="0.34",
                    description="Basket scores 0.17 + 0.17, for different categories.",
                ),
                Level(
                    score=0.5,
                    value="pure_baskets_v3_score_0_5",
                    title="0.5",
                    description="Basket scores 0.5 + 0, or 0.33 + 0.17, in either order.",
                ),
                Level(
                    score=0.66,
                    value="pure_baskets_v3_score_0_66",
                    title="0.66",
                    description="Basket scores 0.33 + 0.33, for different categories.",
                ),
                Level(
                    score=0.67,
                    value="pure_baskets_v3_score_0_67",
                    title="0.67",
                    description="Basket scores 0.5 + 0.17, in either order.",
                ),
                Level(
                    score=0.83,
                    value="pure_baskets_v3_score_0_83",
                    title="0.83",
                    description="Basket scores 0.5 + 0.33, in either order.",
                ),
                Level(
                    score=1.0,
                    value="pure_baskets_v3_score_1_0",
                    title="1.0",
                    description="Basket scores 0.5 + 0.5: all three objects of each category in separate pure baskets.",
                ),
            ),
        ),
        equipment=(
            Equipment(
                name="Turquoise rectangular perforated baskets",
                quantity=2,
                product="EudokkyNA blue/white weave baskets, 6 pack",
                url="https://www.amazon.com/dp/B08K318YGG",
            ),
            Equipment(
                name="Gray dog plush",
                quantity=1,
                product="Skylety plush dogs: Schnauzer, Labrador, Mountain Dog, 3 pack",
                url="https://www.amazon.com/dp/B0B5L5M4H8",
            ),
            Equipment(
                name="Small sea otter keychain plush",
                quantity=1,
                product="Aurora Mini Selena Sea Otter Palm Pals clip-on plush, brown, 4 inch",
                url="https://www.target.com/p/aurora-mini-selena-sea-otter-palm-pals-adorable-clip-on-brown-4/-/A-1012081802",
            ),
            Equipment(
                name="Larger tan teddy-bear plush",
                quantity=1,
                product="LotFancy light brown teddy bear, 10 inch",
                url="https://www.amazon.com/dp/B08YF1HKRH",
            ),
            Equipment(
                name="Yellow marker/highlighter",
                quantity=1,
                product="Sharpie Tank assorted highlighters, 12 pack",
                url="https://www.amazon.com/dp/B002BA5WLE",
            ),
            Equipment(
                name="Blue Uni Paint marker",
                quantity=1,
                product="Uni Paint PX-20 light blue markers, 2 pack",
                url="https://www.amazon.com/dp/B0FCQXHNTW",
            ),
            Equipment(
                name="Black-capped white-barrel VOKART marker",
                quantity=1,
                product="VOKART black chisel-tip dry erase markers, 30 pack",
                url="https://www.amazon.com/dp/B0H4L7QLT6",
            ),
        ),
        photo="docs/assets/sort_objects-setup.jpg",
    ),
)

SPEC_BY_KEY: dict[str, TaskSpec] = {spec.key: spec for spec in SPECS}
"""Every task by its key (the part of the task name after ``robodojo-rc/``)."""
