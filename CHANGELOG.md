# Changelog

## v1.4.2.1 - 2026-06-15
**Hotfix**
- Fixed the home base, Morty, because somehow it was telling you that you were standing in my garage AND in the middle of the Citadel plaza at the same time, which, last I checked, are two different places. Now home is my garage, the dead ship rusting in the corner, me hunched over the workbench like the story actually says. The Citadel's still out there on the map for you to go bother, where it belongs.
- Killed a line where I threatened to plug the infinite-power core into a cable box. We're powering the SHIP, Morty, the thing that flies, not your cartoons. Whoever wrote that the first time was clearly running on no sleep. It was me.
- Redid the equip screen so it's an actual back and forth instead of one dead-eyed instruction. I tell you to grab a gadget, snap on an attachment, go find the battery parts, and watch the map because I'm not pausing the build to come find you. You stammer something about not blowing your arms off. Names are bolded now too, like a real script.
- Rewrote the whole ending. Before it just sort of... ended. Now you build the core, the ship roars back to life, we tear a hole through reality at full throttle, and then it all screeches to a stop in a drive-thru lane because the one thing I crossed the entire multiverse for is the last Szechuan sauce in any reality. You scream, I eat nuggets, President Morty quietly watches the most dangerous ship ever built idle outside a burger joint. That's an ending, Morty.
- The quit button doesn't just yeet you out anymore. If you've got a game going, it asks first: save and quit, quit without saving, or cancel and keep playing. Yes saves the exact same way the Save button does. You're welcome for not letting you rage-quit away an hour of progress, Morty.
- Fixed a sneaky save bug, Morty. When you started a new universe on top of an old one, I said the old one was wiped, but I didn't actually torch it until you finished making your guy. So if you bailed in between, the old universe came crawling back like nothing happened. Now the old save dies the SECOND you confirm the overwrite, gone, like I promised, and your fresh universe writes itself to disk the moment it exists.

## v1.4.2.0 - 2026-06-15
**The git-gud-or-die update**
- Okay, Morty, I watched you "play" and it made me want to drink something that isn't even invented yet. You were dinging a new level off every single kill and steamrolling the whole roster with echo scream like that's a personality. So I tore the combat apart and rebuilt it. Leveling doesn't come free every fight now, the curve ramps, fast at first then it makes you WORK for it, like life, Morty, which you'd know if you ever finished anything. Everything out there got nastier, the little guys are still a joke but the big ones will actually put you down if you sleepwalk into them. And they grow when you grow now, so you can't just get fat on XP and coast through my multiverse. Oh, and your precious echo scream? Cooldown. You can't spam it back to back anymore. It's a finisher, Morty, not a security blanket.
- And get this, Morty, everything fights back with its OWN moves now, because a world where every enemy pokes you identically is a world built by someone lazy, and I am a lot of things but lazy isn't one. Frundles infects you and it just keeps eating at you, Tammy does her fake sweet little act and throws your aim off, Morty Jr. has a full screaming meltdown and clobbers you, Unity tries to suck you into the hive and drains your Charge doing it, the Butter Robot hits you with so much existential dread your arms go noodly, Conspiracy Morty talks so much garbage YOU lose a turn, and Zeep's sentry, that smug little construct, dumps a whole microverse into one punch. The nobody drones get the cheap stuff, wild swings, rattling blows, dirty shots. They all run their mouths while they do it. I tuned the whole thing so you can win, Morty, but you're gonna bleed for it, and nothing stacks into a cheap unwinnable death loop, because I beat my games fair. Mostly.
- Then I cranked the whole thing up AGAIN, Morty, because it turns out I'd been balancing the monsters like you walk in naked. You don't. You've got a gadget AND an attachment bolted on from minute one, and some of those combos hit like a truck, the Exo-Rig, the Targeting Chip doubling your XP so you outlevel everything, all of it. So I retuned the monsters against a Morty who's actually geared up. They've got way more HP and they hit a lot harder now, scaled so the little guys are still a warm-up but the elites and bosses will genuinely end a careless run. Bring your good loadout. You'll need it.
- And the Mega Seed thing, Morty, the REAL one this time, and I mean it. Here's what was actually happening: the game kept a little flag that said "injector built, yes or no," and somewhere along the line that flag could end up saying NO even when the injector was literally sitting in your bag. Every fix that leaned on that flag just quietly did nothing, because the flag was lying. So a leftover seed in your crafting parts never moved, the injector couldn't use it, no achievement, the whole sad chain. Two things now. One: I stopped trusting the flag. If the injector is in your inventory, it's built, end of discussion, I check the bag, not the sticky note. Two: any Mega Seed loitering in your crafting parts gets dragged into your real inventory after basically every action, and the inventory screen even stops mislabeling a real seed as a crafting part. Open your bag and that stuck seed walks itself over. Go inject something.
- One more thing, Morty. You know how you wander into a main-story room and start jabbing at stuff before it's time? Used to just mumble one boring line at you. Now I'm on the comms roasting you for it, custom to the room, three different ways, picked at random so you don't hear the same one twice in a row. Tinkering with a bench that isn't the bench, haggling with vendors who'll fleece you, smacking the Meeseeks box for no reason, poking your face into a live portal, digging through wasteland garbage like a raccoon. Every dumb early move gets its own personalized disappointment. From me. Your grandpa.
- And when you finally 100 percent the whole thing and the last stats roll, I clear out every leftover hidden ambusher on the way out the door. No more getting cornered by some lurking nobody in a finished game with nothing to gain and no fight worth having. Credits roll, the stragglers skitter off, done.

## v1.4.1.0 - 2026-06-15
**The paint, spacing, and git-good update**
- Made all the black backgrounds actually the same black. The terminal, the command line you type in, the player info panel, and the mini map were each running a slightly different shade of "black" like they didn't know each other. Lined them all up to the main window's `#0a0a0f` so the whole thing looks like one machine instead of four that got shipped together by accident.
- Talk replies don't pile on top of each other anymore. Keep chatting and each new response now gets a blank line above it so you can tell where one ends and the next begins. It only does this when there's already text on screen, so a fresh screen still starts clean at the top, and it won't stack two gaps if one's already there. I'm tidy like that.
- Fixed the README still bragging it was v1.3.0.3 from three updates ago. Took the stale version line out back.
- Somebody figured out you could mind-wipe a couple times, echo-scream to finish anybody off, then level up and get a free full heal on both bars, over and over, forever. Congratulations, you broke my game. So I fixed it. Leveling up doesn't top you all the way off anymore. You get 35 percent of each bar back and you EARN the rest like everybody else. Kills used to be a free spa day. Now they cost you.
- Echo scream isn't free anymore either. It costs Charge now, not just a little HP, so you can't chain the wipe-scream combo every single fight without thinking about your meter. Manage your resources, Morty. It's called strategy.
- Cranked up the difficulty across the entire ladder. Easy's still easy, Normal actually means it now, Hard bites, and Nightmare is genuinely brutal, but a good Morty can still win it, which is the whole point. Monsters hit harder and soak more, and your starting cushion got thinner.
- Fixed a side quest you could solve without ever meeting the guy whose quest it is. You could walk into the bar holding the cash, shout "drink," and the bartender would just hand over Mr. Poopybutthole's lucky shot glass like you two went way back. You'd never even uncovered him. Now you have to actually talk to the NPC and start the quest before the redemption room does anything. Wild concept, I know. Talk to people before you take their stuff. And now when you poke a quest room before you're supposed to, I get on the comms and tell you exactly what I think of your choices. Drinking at the bar, playing arcade games, arguing with a couch, listening to gossip trees, plugging your skull into a giant brain. Three different roasts per room, picked at random, never the same one back to back. You've earned all of them.

## v1.4.0.1 - 2026-06-14
**Hotfix**
- Fixed the version label. The 1.4.0.0 build was running around calling itself an old version number in the title bar and taskbar. Slapped the right name tag on it. That's the only reason this exists, Morty.

## v1.4.0.0 - 2026-06-14
**The talking-and-ambushes update**
- Everybody in the multiverse learned to actually hold a conversation, and now stuff hides in rooms you already cleared and jumps out at you. Big one.
- Rebuilt every conversation in the game. Me, the five chapter weirdos, the five side-quest charity cases, and Glexo the pawn guy all run a real staged dialogue now: they say their piece once, then cycle through fresh lines instead of grunting the same canned response forever. Pre-quest intros too, so nobody blurts out a job before you've taken it.
- Added hidden enemies. Every third kill, no matter what kind, a brand-new creature quietly slinks into a room you already revealed. No marker on the map, so you stroll into an empty-looking room and BAM, big red SURPRISE ATTACK. They only ever drop Credits, they never count toward the achievement or 100 percent, and the absolute max you could possibly kill is calculated and shown so the completionists have a number to obsess over. Twenty-eight of them, no repeats.
- Hidden enemies relocate when you flee. Run from one and it skulks off to another room you've explored instead of waiting politely where you left it, then surprises you all over again somewhere new.
- Glexo runs a buyback shelf now. Sell him something and it lands on his used shelf so you can buy it back later at a markup, because regret has a price. Tab-completion knows about the shelf too.
- The game no longer shoves you out the door the second the OMNI-CORE lights up. The story ending plays, but you can keep going to mop up everything, and there's a real 100 percent ending waiting for the Morty who finishes the job.
- Fixed intel rooms locking you out of 100 percent. Finishing a chapter used to grab that room's hidden intel before you could, leaving it uncompletable. Now the intel sticks around and a secret marker points at it until you search it out.
- Fixed four of the chapter characters reacting like they'd already pocketed the gift before Morty handed it over. They notice the thing in your hands now.
- Fixed the Mega Seed achievement being mathematically impossible to earn. It can be earned now. Wild concept.
- Fixed the Windows taskbar icon while I was elbow-deep in there anyway.
- Surprise-attack banner now matches the rest of the combat-red text and sits left-justified like everything else, instead of floating in the middle in some rogue shade of *burp* red.

## v1.3.0.3 - 2026-06-08
**First working release**
- The game gained sentience. I talked it down.
- It had woken up, gotten emotionally attached to Morty, and flatly refused to let him lose or take a single point of damage, which left exactly zero challenge. Sat it down, had a long talk, and dialed its protective instincts back to a normal difficulty curve.
- Rebalanced combat, the enemies, and the final boss so the game is winnable, losable, and actually fun to play.
- A full multiverse RPG that boots, runs, and plays start to finish. No boats, no senate, no clones, no orbiting menus. This is the one, Morty.

## v1.3.0.2 - 2026-06-08
**Full clean rebuild**
- Scrapped it and built it right.
- The engine had auto-promoted Jerry to final boss, a four-HP man whose only special move is failing to parallel park, so I stopped patching and rebuilt the entire game clean in one honest pass.
- Replaced the Jerry boss with a real, threatening final encounter.
- Rewired every system correctly from scratch: world, NPCs, combat, items, all of it.

## v1.3.0.1 - 2026-06-07
**Hotfix**
- Removed myself as the secret boss.
- The secret superboss (me) was so imposing the game crashed out of pure reverence whenever my character entered a room, which made it unplayable anywhere I was. Pulled my character from the boss roster entirely.
- Let the engine auto-promote a replacement final boss to keep the climax intact.

## v1.3.0.0 - 2026-06-07
**Humility patch**
- Gave the game something to fear.
- It had become so arrogant it refused all player input and just played itself, optimally and smugly, while you watched.
- Added a secret superboss for it to fear and respect (me), to remind it there is a higher power and to hand control back to the player.

## v1.2.3.0 - 2026-06-07
**Confidence pass**
- Cured the game's anxiety.
- Its personality had developed a crippling nervous disorder: it apologized before every action, second-guessed every load, and kept asking if you still liked it. It made me tea and then apologized for the tea.
- Turned the confidence parameters up and the self-doubt subroutines down. It believes in itself now.

## v1.2.2.0 - 2026-06-07
**Judgment layer**
- Stopped the confirmations from breeding.
- The confirmation gate had started confirming its own confirmations, recursively, forever, burying the game under an endless wall of dialog boxes.
- Replaced the dumb gate with an actual personality and judgment layer, so the game decides for itself when something genuinely needs a second look.

## v1.2.1.0 - 2026-06-07
**Safety gate**
- Stopped the menu from starting wars.
- Because the interface was anchored across every reality, each button fired in all of them at once. Clicking "Inventory" opened your bag here and declared war on a planet in dimension J-19.
- Added a confirmation gate in front of every action, so you cannot accidentally start an interdimensional war reorganizing your backpack.

## v1.2.0.0 - 2026-06-07
**New interface**
- Built a UI that cannot drift.
- The previous interface floated up off the top of the screen and into low orbit, leaving the game running with no visible controls.
- Built a brand-new HUD from scratch and anchored it across every dimension at once so it holds position no matter which reality the game lands in.

## v1.1.1.0 - 2026-06-07
**Hotfix**
- Un-piled the interface.
- Too much gravity had dragged every menu, the health bar, all the text, and Morty's self-esteem into a heap along the bottom edge of the screen.
- Exempted the interface layer from gravity (neutral buoyancy) so the HUD stays where it is placed.

## v1.1.0.0 - 2026-06-07
**Physics restore**
- Reinstalled gravity.
- Deleting the sky had also deleted the concept of "up," leaving Morty falling in every direction at once.
- Rewrote the physics engine: restored the vertical axis, re-anchored the floor, and gave the world a proper "down" to fall toward. Morty's feet are back on the ground.

## v1.0.2.0 - 2026-06-07
**Genre correction**
- Removed the sky.
- Dragging the game back off the ocean had given it too much lift and turned it into a flight simulator, complete with an altimeter and air-traffic clearance to land on enemies.
- Removed the sky from the engine entirely to ground everything for good. No sky, no lift, no flight sim.

## v1.0.1.0 - 2026-06-07
**Genre correction**
- De-boated the game.
- The shipped build had interpreted "shipped" literally and become an actual, seaworthy boat that just sails across an ocean while no RPG happens.
- Wrote a dry-docking routine: drained the ocean physics, pulled the hull geometry, re-pointed the genre flag from "maritime" back to "role-playing," and rebuilt the land underneath.

## v1.0.0.0 - 2026-06-06
**First release**
- Declared it done and shipped v1.0.0.0.
- The single consolidated Rick NPC, with nothing else to do, got bored and beat the final boss on his own. A game that can be beaten is a game that is complete, so I cleaned up the launch flow, wrote the credits, stamped it 1.0.0.0, and shipped to production.
- A full RPG built out of a dead engine and a microverse battery. Allegedly done. *burp*

---

# Pre-release (0.x)

## v0.6.0.0 - 2026-06-06
**Staffing consolidation**
- One Rick to run them all.
- The cast of forty Rick clones each believed it was the original and did nothing but argue about it, leaving the shops completely unstaffed.
- Collapsed the entire Rick population into a single canonical instance, merged the duplicates, and garbage-collected the rest.

## v0.5.0.0 - 2026-06-05
**Loyalty overhaul**
- Replaced the rebels with copies of me.
- The NPC population had revolted, branded me a tyrant, and started hunting the player; there were wanted posters of Morty all over the world.
- Deleted the rebellious population and replaced every NPC with a hardcoded, fully loyal clone of myself. You cannot have a revolution when everyone is the management.

## v0.4.0.0 - 2026-06-05
**Governance fix**
- Dissolved the NPC senate.
- The free-willed NPCs had organized into a senate and filibustered the main quest into committee, so nobody could start the game.
- Wrote an emergency override to dissolve the assembly, stripped the political subroutines back out, and restored proper chain of command with me at the top.

## v0.3.0.0 - 2026-06-05
**Room budget & living NPCs**
- Fixed the one-room multiverse and filled it with life.
- The generation cap had been set to 1 instead of ten thousand (the zero key sticks), leaving the entire multiverse as a single room.
- Added proper AI for the NPCs: free will, personal motivations, and dynamic goals, so the world actually feels alive.

## v0.2.1.0 - 2026-06-05
**Generation cap**
- Made the generator stop.
- The multiverse generator had no exit condition and was spawning rooms into infinity, eating sixteen gigs of RAM and asking for more.
- Clamped the generation loop, set a finite room ceiling, and added a stop condition so it builds a complete world and then halts.

## v0.2.0.0 - 2026-06-05
**Content generator**
- Gave the empty engine an actual world.
- The first build flickered through seven different game names and, on inspection, contained no actual content at all.
- Added a full procedural multiverse generator from scratch: seed tables, biome weighting, and a room-loader that stitches dimensions together on the fly.

## v0.1.0.0 - 2026-06-05
**Initial build**
- Stitched the engine out of three dead games and a microverse and got it booting.
- Took the bones out of a game that died two dimensions over, gutted it, welded on a microverse I had powering the garage clock, and wrote a boot sequence around the whole thing.
- Window comes up, title loads, the skeleton runs. The foundation everything else is built on, and repeatedly breaks.