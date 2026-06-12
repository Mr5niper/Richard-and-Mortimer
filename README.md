# Rick and Morty - Multiverse Mayhem

> Oh good, you found the README. *burp* Slow clap, Morty. I crammed an entire
> multiverse RPG into a single Python file because I'm a genius and I was bored.
> You play Morty. You run my errands. You try not to die. That's the pitch.
> Keep reading or don't, I'm a wall of text, I literally cannot make you.

## What this even is

A single-player, text-driven RPG that runs in a little window on your Windows
machine. You play Morty (you don't get a choice, you're always Morty, deal with
it) wandering a 12 by 12 grid of the multiverse, talking to idiots, whacking
monsters, grabbing loot, and slowly building the one thing I actually care about.
<br><br>
<img width="1752" height="969" alt="image" src="https://github.com/user-attachments/assets/95e378af-2676-4b93-bb0c-434ce08e1992" />
<br><br>
No 3D garbage, no microtransactions, no "live service." Just words, a map, and
your famously questionable decision-making.

## Why you're doing any of this

Here's the deal. The Microverse Battery in my ship is dead. The tiny universe I
run inside it unionized and went on strike, because of course it did. So I'm
grounded at the Citadel workbench building an OMNI-CORE out of five exotic parts.
I can't go grab them myself, partly because I'd get shot on sight as a Rick, and
partly because I'm busy being smarter than you. Nobody bothers a Morty, though.
So congratulations, you're the errand boy of the cosmos. Go fetch.

## Stuff I crammed in

- A five-chapter main quest. Talk to me, hand my gadget to whatever weirdo runs that chapter, do the dumb thing they tell you, bring the part back. Repeat five times.
- Five side quests for the over-achievers. They pay out crafting parts you can't get any other way, so they're "optional" the way breathing is optional.
- Crafting, five recipes. You have to hunt the whole map AND finish side quests, because I don't do participation trophies.
- Twelve achievements, for the kind of person who needs a gold star to feel alive.
- Four difficulties: Easy, Normal, Hard, and Nightmare. Pick Easy. I won't judge. I will, but quietly.
- A gadget plus attachment loadout you grab from my garage at the start. Choose wisely. Or don't, *buuurp*, it's your funeral.
- Federation Credits, a pawn shop run by a slimy little guy, a journal, and a minimap with class radar so you can sense what's nearby before it eats you.

## How to actually run it

**The easy way (Windows):**
Download `Rick and Morty - Multiverse Mayhem.exe`, double-click it, and read the
legal wall that pops up first. You have to click "I Agree" or it won't even open.
That's not a bug, Morty, that's lawyers.

**The nerd way (from source):**
You need Python 3.13, and the build script is picky, it wants 3.13.12 exactly. No
pip installs, no dependencies, no `requirements.txt` nonsense. I built the whole
thing on the standard library like a civilized person. Drop the script, `icon.ico`,
and `version.txt` in one folder and double-click `BUILD_EXE.bat` to bake your own
`.exe`, or just run the `.py` directly if you're impatient.

## How to play

You type. Like it's 1985. *burp*

- Move with the **arrow keys**, or type a direction: `north` `south` `east` `west`, or `up` `down` `left` `right`, or just `n` `s` `e` `w`. I gave you like six ways to walk, Morty. Don't screw it up.
- `look` (or `examine`) to eyeball the room. `talk` to bug whoever's standing there.
- `get <item>` to grab loot, `use <item>` for gadgets and consumables, `give <item>` to hand something to an NPC.
- `hint` (or `quest`) tells you what to do next. `search` digs up intel hidden in special rooms.
- Standing in one of those special rooms? Do the thing it wants: `tinker`, `scavenge`, `haggle`, `negotiate`, `listen`, `call`, `investigate`, `order`, `harvest`, `connect`, and friends. Tab hands you the right verb.
- In a fight: `attack` for a basic swing, `flee` to run, or type a special attack straight. No "cast fireball" garbage.
- `craft <thing>` to build gear. At the pawn shop, `buy` and `sell`. Got the Portal Gun (Replica)? `portal_jump <X> <Y>` to anywhere you've already been.
- Mash Tab to autocomplete only the moves you can actually pull off right now.

## Cheats

Are there cheat codes? *buuurp* Maybe. Did I leave a few in because I'm the
developer and I do what I want? Possibly. Am I going to list them right here in
the README like some kind of sap? Not a chance. Figure it out, genius.

## Saving

Saves live in a `saves` folder right next to the game, so you can actually find
them and they don't vanish into some hidden Windows hole. Save often. The
multiverse is a meat grinder and it is not impressed by you.

## The boring legal part

This is an unofficial, non-commercial fan project. The real "Rick and Morty" and
everyone in it belong to Cartoon Network, Inc. and its parent Warner Bros.
Discovery; the show airs on Adult Swim and was created by Dan Harmon and Justin
Roiland. This project is not affiliated with them, not endorsed by them, and not
trying to make a dime. The game even shows you the full legal notice on launch,
which you should actually read instead of skimming this paragraph like you're
skimming this one.

## Version

Currently **v1.3.0.3**. The complete, slightly embarrassing development history,
including the pre-release `0.x` builds where I fixed a bunch of my own bugs, is in
`CHANGELOG.md`. Don't worry about it.

## Who did this

Built by Mr5niper5oft. The brilliant narration is me, Rick. The bugs were also
technically me, but we don't talk about those. Wubba lubba dub dub.