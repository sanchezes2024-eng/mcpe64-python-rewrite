# MCPE 0.6.1 C++ Reference Audit for the Python Reimplementation

This is a source-guided porting checklist, not a claim that every one of the repository's 1,343 C/C++ headers and source files has been manually read. The audit starts with the original client/gameplay implementation paths that define the requested features.

## Main menu and navigation
- `src/client/gui/screens/StartMenuScreen.cpp`: Start Game routes to world selection, Join Game routes to multiplayer, Options opens settings; title artwork and version/copyright labels are rendered from assets.
- `src/client/gui/screens/SelectWorldScreen.cpp`, `ChooseLevelScreen.cpp`, `SimpleChooseLevelScreen.cpp`: saved-world listing, selection, unique world names, and world startup.
- `src/client/gui/Screen.cpp`, `Screen.h`, `ScreenChooser.cpp`, `ScreenChooser.h`: common input/render lifecycle and screen transitions.
- `src/client/gui/screens/UsernameScreen.cpp`, `JoinGameScreen.cpp`, `ConfirmScreen.cpp`, `CreditsScreen.cpp`: additional menu destinations and dialogs.

## Options/settings
- `src/client/gui/screens/OptionsScreen.cpp`: category tabs (Login, Game, Controls, Graphics), username and credits actions.
- `src/client/gui/components/OptionsPane.cpp`, `OptionsGroup.cpp`, `OptionsItem.cpp`: option grouping and interaction.
- `src/client/Options.cpp`, `OptionsFile.cpp`, `OptionStrings.cpp`: defaults, key mappings, saved values, sensitivity, invert-Y, difficulty, GUI scale, graphics, audio, and control settings.

## Pause menu
- `src/client/gui/screens/PauseScreen.cpp`: Back to game, Quit to title, optional copy-map action, sound and third-person toggles, and server visibility when hosting.
- `src/client/Minecraft.cpp`: game/screen lifecycle, pause handling, leave-game transitions.

## Inventory and containers
- `src/client/gui/components/InventoryPane.cpp`: item-slot grid, scroll/selection behavior and item rendering.
- `src/client/gui/screens/ArmorScreen.cpp`, `ChestScreen.cpp`, `FurnaceScreen.cpp`, `WorkbenchScreen.cpp`, `PaneCraftingScreen.cpp`, `StonecutterScreen.cpp`: inventory/container/crafting screen families.
- `src/world/entity/player/Inventory.cpp`, `src/world/item/ItemInstance.cpp`, `src/world/item/Item.cpp`: authoritative item and inventory behavior; the Python prototype currently lacks a compatible item-stack model, so empty UI slots are not a real inventory port.

## Controls and player movement
- `src/client/player/input/KeyboardInput.cpp`: configured movement keys, jump/sneak and 0.3 sneak scaling.
- `src/client/player/input/MouseTurnInput.h`, `MouseBuildInput.h`, `ControllerTurnInput.h`, `src/client/player/input/touchscreen/TouchscreenInput.cpp`: mouse, controller and touch input paths.
- `src/client/Options.cpp`: default WASD/Space/Shift mappings and option persistence.
- `src/world/entity/Entity.cpp`, `src/client/player/LocalPlayer.cpp`, `src/client/gamemode/SurvivalMode.cpp`, `CreativeMode.cpp`: collision, player lifecycle and game-mode behavior.

## Particles
- `src/client/particle/Particle.cpp`: velocity, gravity, drag, lifetime and billboard rendering.
- `src/client/particle/ParticleEngine.cpp`: texture-grouped update/render lifecycle.
- `src/client/particle/ParticleInclude.h` and particle subclasses: terrain debris, smoke, flame, bubbles, splashes, lava and other particle families.

## Mobs/entities
- `src/world/entity/Entity.cpp`, `Mob.cpp`, `MobFactory.cpp`: entity lifecycle, movement and mob creation.
- `src/world/entity/ai/PathNavigation.h`, `ai/control/MoveControl.h`, `ai/control/JumpControl.h`, `ai/goal/GoalSelector.h`: mob AI/pathfinding control.
- `src/client/renderer/entity/EntityRenderDispatcher.cpp` and entity renderer subclasses: rendering, separate from simulation.

## World generation
- `src/world/level/levelgen/RandomLevelSource.cpp`: 128-high density interpolation, water/ice fill and biome surface construction.
- `src/world/level/biome/BiomeSource.cpp`: seed-derived temperature/downfall/noise maps and biome selection.
- `src/world/level/levelgen/feature/`: feature placement; cave/ore/tree and other generators must be followed through their implementation and called in the same order.
- `src/util/Random.h` and noise implementation files: exact seed compatibility depends on reproducing the original RNG and noise algorithms, not Python's built-in random module.

## Current Python gaps and porting order
The Python prototype currently has a small voxel world, simplified terrain, keyboard movement, block placement/removal, a Pyglet frontend and a prototype title/menu flow. It does not yet have the original save format/world list, item-stack inventory, mobs/AI, particle engine, multiplayer, or the full settings model.

Recommended implementation sequence:
1. Add screen-state/navigation model and port the original menu flow using the bundled original GUI assets.
2. Add persistent options/key bindings and implement pause/resume/quit semantics.
3. Port world storage and world selection/creation before claiming saved-world support.
4. Port block/item IDs and item stacks, then inventory/container/crafting interactions.
5. Port original RNG/noise and the full world-generation pipeline with fixed-seed comparisons against the C++ reference.
6. Add entity ticking/collision and mob factory/AI; then port particle simulation and renderers.
7. Add controls for mouse/keyboard/touch, inventory and hotbar, with behavior checks against the C++ mappings.

## Validation policy
A feature is considered ported only when its behavior is connected to the Python game state and checked with focused tests. A drawn button or decorative inventory grid alone is not a functional port. Exact world generation requires same-seed block-by-block comparisons against the original C++ implementation.
