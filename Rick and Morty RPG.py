import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import random, pickle, os, sys
from dataclasses import dataclass
from typing import List
from enum import Enum
import string
import re
# ===== The version lives HERE and only here. Change this one line to bump the game; the title bar and =====
# ===== both Windows taskbar IDs all read from it. No more hunting it down in three places, Morty. =====
GAME_VERSION = "1.4.2.0"
# ===== Utility junk. The little functions that do the boring lifting so the cool code doesn't have to. =====
def to_letter_number(x, y):
    if not (1 <= x <= 26):
        return f"?{x},{y}"
    return f"{string.ascii_uppercase[x-1]},{y}"
def parse_coord(value):
    return string.ascii_uppercase.index(value.upper()) + 1 if value.isalpha() else int(value)
def a_or_an(word: str) -> str:
    """Return 'an' if the word begins with a vowel sound, else 'a'."""
    return "an" if word[0].lower() in "aeiou" else "a"
# ===== The data. This is where I hard-coded reality. Tweak it wrong and the multiverse falls apart, Morty. =====
class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    QUEST = "quest"
    CRAFTING = "crafting"
    SPECIAL = "special"
class DifficultyLevel(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"
@dataclass
class Achievement:
    name: str
    description: str
    reward: str
    condition: str
    unlocked: bool = False
@dataclass
class Monster:
    name: str
    hp: int
    max_hp: int
    damage: int
    loot: List[str] = None
    description: str = ""
    special_attack_chance: float = 0.0  # A probability, zero to one. Math, Morty. Try to keep up.
    special_attack_name: str = ""
    is_boss: bool = False      # This flag is how I tag the big nasty bosses. Zeep, Cromulons, Fart, all the usual disappointments.
    stun_turns: int = 0
    weakened_next_attack: bool = False
    hidden: bool = False       # A hidden ambusher I drop in after kills. No map marker, only ever coughs up Credits, never counts toward the achievement or 100 percent.
    level_scaled: bool = False  # Set once we've scaled this thing to the player's level, so it doesn't keep compounding every round.
    echo_cd: bool = False        # True the turn AFTER an echo scream, so you can't spam it back to back.
    def __post_init__(self):
        if self.loot is None:
            self.loot = []
# ===== All the game's actual content lives down here. I built every bit of it. You're welcome. =====
EXTENDED_MOTIFS = [
    {"room": "A dimension where everything is on a cob. Even the air is a tiny cob.", "motif": "cob_dimension", "clue": "where everything is corny", "interaction": "eat_cob", "hidden_lore": "Rick's dead Microverse Battery once powered a whole tiny civilization that worshipped him as their god. Turns out even gods get picketed when they stop paying overtime."},
    {"room": "The chaotic main street of the Citadel of Ricks, bustling with various Ricks and Mortys.", "motif": "citadel_street", "clue": "where countless Ricks and Mortys roam", "interaction": "observe_ricks", "hidden_lore": "The Citadel of Ricks runs on a million Mortys and a million egos. Statistically, your Rick is exactly average, a fact that would send him into a three-hour rant if he ever heard it."},
    {"room": "An abandoned Blips and Chitz arcade, some games still flicker dimly.", "motif": "blips_and_chitz", "clue": "where pixels tell tales of forgotten fun", "interaction": "play_game", "rick_barbs": ["Rick crackles in over comms: \"Are you playing ARCADE games right now, Morty? I send you on ONE errand and you find a Blips and Chitz to dick around in. This is why your report cards are a cry for help.\"", "Rick's voice cuts through static: \"Oh, you found a quarter-muncher, huh Morty? Great. Real productive. While you're racking up a high score, the thing I actually need is sitting somewhere getting LESS findable. Go.\"", "Rick groans: \"Morty, I can hear the bleep-bloops from here. You're in an arcade. You. In an arcade. Buddy, the mission is not in the claw machine. Walk away from the lights, Morty.\""], "hidden_lore": "The 'Roy: A Life Well Lived' cabinet simulates an entire human lifetime in real time. Rick once played as Roy until he was 55, got bored, and quit being a carpet salesman out of pure spite.",
     "repeatable_action": {"cost_type": "credits", "cost_amount": 5, "flavor": "You insert 5 Credits into a dusty arcade machine..."}},
    {"room": "A garage workshop, smelling of alien chemicals, coolant, and despair. Tools are scattered everywhere.", "motif": "rick's_garage", "clue": "where genius and liquor combine", "interaction": "tinker_workbench", "quest_barbs": ["Rick crackles in: \"Morty, you're tinkering with a random bench like a kid mashing buttons on an unplugged controller. The Shard isn't ready for you yet. Go where the story's pointing before you electrocute yourself.\"", "Rick sighs: \"Oh, you found A workbench. Congratulations. It's not THE workbench, Morty, you haven't even done the legwork yet. Quit fiddling and follow the actual plan.\"", "Rick: \"Morty, buddy, poking screwdrivers into strange machinery you don't understand is how you END UP a cautionary tale. Not yet. Do the steps in order, you maniac.\""], "hidden_lore": "Rick's workbench wears scorch marks from forty-seven failed power cores. The OMNI-CORE is attempt forty-eight. He labels none of them. Labels are for people who plan to fail.",
     "repeatable_action": {"cost_type": "material", "cost_amount": 1, "flavor": "You grab a random piece of junk and start tinkering on the workbench..."}},
    {"room": "A plush, overly decorated living room with giant, sentient furniture demanding attention.", "motif": "sentient_furniture_house", "clue": "where furniture talks back", "interaction": "negotiate_couch", "rick_barbs": ["Rick's voice cuts in: \"You're NEGOTIATING with a COUCH, Morty. A couch. You lose that one, by the way. You're losing an argument to upholstery and I'm watching it happen in real time. Move.\"", "Rick sighs over comms: \"Morty, please tell me you are not taking debate notes from a loveseat. That's a chair with opinions, buddy, it is not your therapist, and it is definitely not the mission. Get up.\"", "Rick snaps in: \"Oh, the furniture has THOUGHTS about your posture? Fascinating, Morty. Riveting. Now picture me not caring at a speed that would kill a normal man, and go do the thing I sent you for.\""], "hidden_lore": "This furniture gained sentience after a sofa-shaped neutrino leaked through the wall. It now holds strong opinions about your posture and zero intention of keeping them to itself."},
    {"room": "A serene, yet unsettling dimension filled with glowing, talking trees.", "motif": "talking_tree_forest", "clue": "where nature has opinions", "interaction": "listen_trees", "rick_barbs": ["Rick groans over the line: \"Oh good, you found the gossip trees. You're standing in a forest of slander LISTENING to drama, Morty, while I age. Eighty percent of that is about your dad. None of it is the thing I sent you for.\"", "Rick cuts in flat: \"Morty. Morty. Those are trees. You're getting your news from TREES. Do you hear how that sounds? The shrubs do not have what I need, buddy, and they are not your friends.\"", "Rick's voice drips with contempt: \"Let me guess, the foliage is telling you something juicy and you HAVE to hear how it ends. It's about Jerry, Morty, it's always about Jerry, and it is still not the mission. Walk.\""], "hidden_lore": "These trees photosynthesize gossip instead of sunlight. A juicy enough rumor sprouts a whole sapling overnight. Roughly eighty percent of this forest is slander about Jerry."},
    {"room": "The desolate, yet beautiful landscapes of post-apocalyptic Earth (Wasteland Dimension).", "motif": "wasteland", "clue": "where chrome survivors roam", "interaction": "scavenge_ruins", "quest_barbs": ["Rick's voice cuts in: \"Morty, you're picking through garbage like a raccoon with a concussion. The Capacitor's not just lying out here, you skipped a step. Go do the thing you were supposed to do FIRST.\"", "Rick groans: \"Scavenging already? You look like your dad at a yard sale, Morty. There's nothing for you to dig up yet. Follow the trail before you cut yourself on a tetanus rock.\"", "Rick: \"Morty, rooting around in the rubble before the story says to is just you volunteering to get jumped by raiders for zero payoff. Patience. Or, in your case, instructions.\""], "hidden_lore": "This dimension's sun collapsed mid-divorce between two physics constants. What's left is rust, raiders, and a Summer who, frankly, has never been happier."},
    {"room": "A bustling alien marketplace, with strange creatures hawking even stranger wares.", "motif": "alien_market", "clue": "where bizarre goods are traded", "interaction": "haggle_vendor", "quest_barbs": ["Rick crackles in: \"Morty, you're trying to haggle with NO leverage and no reason to be here yet. You'll pay triple and come back with a cursed lamp. Do the story step first, then shop, genius.\"", "Rick: \"Oh great, Morty's negotiating. You couldn't haggle your way out of a timeshare seminar. The Conduit deal isn't open to you yet. Go advance the plot before you get fleeced.\"", "Rick sighs: \"Morty, these vendors smell a mark from nine stalls away, and right now that mark is you, for no reason, because you jumped the gun. Come back when the story actually sends you.\""], "hidden_lore": "Everything for sale here was technically stolen from a dimension that hasn't invented it yet. The vendors call it 'pre-tail.' The lawyers call it 'unreachable, please stop asking.'",
     "repeatable_action": {"cost_type": "credits", "cost_amount": 10, "flavor": "You try your luck haggling with a shifty-looking vendor for a 'mystery box'..."}},
    {"room": "A room full of Plumbuses, each one unique and perfect in its own way.", "motif": "plumbus_factory", "clue": "where Plumbuses are born", "interaction": "examine_plumbus", "hidden_lore": "A Plumbus starts with a dinglebop, gets smoothed with a grumbo, and involves three steps no sober being has witnessed in full. Every home owns one. Nobody can explain why."},
    {"room": "A dark, ominous chamber with a giant, glowing green portal throbbing at its center.", "motif": "dark_portal_chamber", "clue": "where realities converge", "interaction": "investigate_portal", "quest_barbs": ["Rick's voice snaps in: \"Morty, do NOT go poking your face into a strange portal because you're bored. That's a great way to come back inside out. The Singularity step isn't live yet. Walk away from the glowy hole.\"", "Rick: \"Investigating the portal, are we? You, the kid who once got lost in a corn maze. There's nothing here for you yet, Morty. Follow the actual story before you fall into fourteen dimensions at once.\"", "Rick groans: \"Morty, last time you 'investigated' something glowing you spent a week as a rumor. It's not time. Do the steps in order and stop free-styling near reality-tearing equipment.\""], "hidden_lore": "Portal fluid is concentrated 'somewhere else.' Drink it and you don't go anywhere. You just briefly become a rumor in fourteen dimensions at once. So: don't drink the portal fluid."},
    {"room": "A sterile, white chamber, echoing with the sound of tiny footsteps.", "motif": "meeseeks_box_room", "clue": "where existence is pain", "interaction": "call_meeseeks", "quest_barbs": ["Rick crackles in: \"Morty, do not smack that Meeseeks box for fun. Every one you spawn is in screaming agony from the second it exists, and you've got no task for it yet. Leave the poor blue guys alone and do the story.\"", "Rick: \"Oh, you wanna call a Meeseeks? With no goal? So it can suffer pointlessly and then resent you? That's dark even for me, Morty. It's not time. Step away from the box.\"", "Rick sighs: \"Morty, a Meeseeks with no clear task is a countdown to a murder, and right now the task is 'nothing,' because you skipped ahead. Follow the plan before you spawn a problem.\""], "hidden_lore": "A Meeseeks blinks into existence already in pain and stays that way until its one task is done. Rick files this under 'features.' The Meeseeks files it under 'grounds for a lawsuit.'"},
    {"room": "A shimmering, iridescent cave where rare Mega Seeds grow, guarded by protective flora.", "motif": "mega_seed_cave", "clue": "where knowledge blossoms", "interaction": "harvest_seed", "hidden_lore": "Mega Seeds spike your IQ to galaxy-brain levels for about an hour. The comedown involves deep regret, one tearful confession, and a heartfelt apology to a houseplant."},
    {"room": "A dimly lit, futuristic bar populated by various alien species, many of whom look menacing.", "motif": "blips_bar", "clue": "where alien drinks flow", "interaction": "order_drink", "rick_barbs": ["Rick's voice blares in your ear: \"Are you DRINKING right now, Morty? I'm supposed to be the day-drinker in this operation, that's MY thing, and you're at some bar ordering rounds while I'm out here doing the actual science. Put the glass down and go find what I sent you for.\"", "Rick snaps over comms: \"Morty, that bar is full of guys with bounties on their heads, and you're worried about your TAB? You're fourteen, buddy. Order a juice box of self-respect and get moving.\"", "Rick cackles, then stops: \"Ohhh you think you're so cool, Morty, sidling up to the alien bar. You can't even handle root beer. Get out of there before something with four mouths adopts you as a snack.\""], "hidden_lore": "Half the regulars here are wanted across nine galaxies; the other half are bounty hunters too drunk to collect. The bartender stays neutral and overcharges everyone with perfect fairness."},
    {"room": "An interdimensional courthouse, where the legal system is a confusing, bureaucratic nightmare.", "motif": "interdimensional_court", "clue": "where justice is a gamble", "interaction": "bribe_official", "hidden_lore": "The Galactic Federation's legal code runs six billion statutes, all enforced by Gromflomites who would rather be anywhere else. Justice here is ninety percent paperwork and ten percent resentment."},
    {"room": "A gigantic, pulsating brain-like entity occupies the center of the room, humming with psychic energy.", "motif": "glarblon_mind", "clue": "where thoughts echo", "interaction": "connect_mind", "rick_barbs": ["Rick sighs hard over comms: \"You're jacking your brain into a giant psychic MEATBALL, Morty, unprompted, for no reason. You've got, what, half a thought rattling around in there, and you're donating it to a stranger? Unplug. Now. Before it gives the thing back out of pity.\"", "Rick's voice spikes: \"Morty, no, do NOT mind-meld with the mystery brain. That's how you end up with someone else's tax anxiety living in your skull. We are not doing free psychic surgery today. Back away.\"", "Rick deadpans: \"Oh, you're connecting minds with it. Cool. Real cool, Morty. It's read every Rick in the multiverse and found us exhausting, and you're volunteering to be the dumbest data point it's ever seen. Unhook yourself.\""], "hidden_lore": "This brain has read the private thoughts of every Rick in existence and reached one conclusion: they are all, without exception, exhausting. It would leave, but (it cannot stress this enough) it is a brain."},
]
# ===== The main story. Five chapters, you build the OMNI-CORE outta the dead Microverse Battery. Linear, because you can't handle choices. =====
# Here's how every chapter loops, Morty, pay attention:
# First I hand you a gadget, a clue, and an objective, because you'd be lost otherwise.
# Then you go bug the chapter's character, give them my gadget, and they tip you off to some special move.
# You do that move in the right room and out pops the find-item. Magic. No, science.
# You haul the find-item back to me, I forge one OMNI-CORE part, and we roll to the next chapter.
# Every story item is one-of-a-kind and gets eaten up as you go. You don't keep any of it,
# and none of it touches crafting. Don't go hoarding, you little raccoon.
GAME_OBJECTIVE = (
    "Rick's ship runs on a Microverse Battery, a whole tiny universe he built to "
    "generate power. The little guys inside finally unionized and walked off the job, "
    "so the battery is dead and the ship is going nowhere. Rick is welding together a "
    "replacement he calls the OMNI-CORE, and it needs five exotic parts scattered "
    "across the multiverse. Here is the catch. Rick cannot step away from the workbench "
    "until the core is finished, and half the dimensions holding those parts would put "
    "a bullet in a Rick the second he showed his face. Nobody looks twice at a Morty. "
    "So Rick presses his spare portal gun into your hands, points at the door, and "
    "tells you to go fetch. Bring back all five parts. Do not lose the portal gun, and "
    "try real hard not to die out there."
)
EXTENDED_QUESTS = [
    dict(
        act="Act I: Cold Open", title="A Shard of a Tiny Universe",
        character="Zeep Xanflorp", giver_npc="Zeep Xanflorp",
        persona="The smug little genius who built a Miniverse inside Rick's Microverse. Hates Rick. Respects no one.",
        motif=3,  # rick's_garage, you tinker. Obviously.
        rick_gift="Miniverse Peace Accord",
        rick_send=("Rick burps. \"{pc}, my Microverse battery's a ghost town - the little "
                   "ingrates organized. So we're building the OMNI-CORE. First part's a "
                   "Tessellated Void Shard, and the only guy who makes 'em is that smug "
                   "sub-atomic dweeb Zeep. Take him this peace accord so he doesn't vaporize "
                   "you. He's somewhere out there - go.\""),
        char_need=("Zeep squints at the accord. \"Rick wants MY help? Fine. There's a Void "
                   "Shard wedged in a workbench in a junk-stinking garage dimension. TINKER "
                   "with the workbench and it'll pop loose. Don't break it, errand boy.\""),
        item="Tessellated Void Shard",
        retrieve_story="You tinker at the cluttered workbench. A pocket of folded space-time clicks free: a Tessellated Void Shard!",
        rick_install=("Rick snatches the shard. \"Heh. Zeep does decent work, don't tell him I "
                      "said that.\" He welds it into a casing. OMNI-CORE: Core Casing installed."),
        core_part="Core Casing",
        riddle_extra="Zeep said a Void Shard is stuck in a workbench in a garage dimension. TINKER it loose.",
        completion="Core Casing installed.",
    ),
    dict(
        act="Act II: Old Friends", title="Salvage From the War",
        character="Birdperson", giver_npc="Birdperson",
        persona="Stoic war veteran, part cyborg now. Speaks in slow, heavy truths.",
        motif=6,  # wasteland, you scavenge. Pick through the garbage like a Jerry.
        rick_gift="Cybernetic Tune-Up Kit",
        rick_send=("Rick: \"Next part needs a War-Forged Capacitor, and the only ones left are "
                   "rusting on Birdperson's old battlefield. He's half-machine these days, so "
                   "bring him this tune-up kit - call it a peace offering. Go find him.\""),
        char_need=("Birdperson accepts the kit with a slow nod. \"In war, we buried our "
                   "capacitors in the wasteland so the Federation could not take them. SCAVENGE "
                   "the ruins. What you find belongs to the cause now.\""),
        item="War-Forged Capacitor",
        retrieve_story="You scavenge the scorched ruins. Under a fallen banner: a still-humming War-Forged Capacitor.",
        rick_install=("Rick: \"Birdperson's old gear never fails. Unlike Birdperson's marriages.\" "
                      "He clamps it in. OMNI-CORE: Surge Regulator installed."),
        core_part="Surge Regulator",
        riddle_extra="Birdperson buried War-Forged Capacitors in the wasteland ruins. SCAVENGE for one.",
        completion="Surge Regulator installed.",
    ),
    dict(
        act="Act III: Squanch Business", title="A Conduit Worth Haggling For",
        character="Squanchy", giver_npc="Squanchy",
        persona="A cat-like party animal who uses 'squanch' as every part of speech. Surprisingly dangerous.",
        motif=7,  # alien_market, you haggle. Don't get ripped off.
        rick_gift="Bottle of Eyehole Wine",
        rick_send=("Rick: \"Third part's a Squanch-Grade Plasma Conduit - black-market stuff. "
                   "Squanchy's got the connects, but he only deals after a drink. Bring him "
                   "this bottle of the good Eyehole wine and don't squanch it up.\""),
        char_need=("Squanchy sniffs the bottle and purrs. \"Ohh, you really know how to squanch a "
                   "guy! Okay - there's a Plasma Conduit at the alien market, but that vendor's a "
                   "crook. Go HAGGLE him down. Squanch him good.\""),
        item="Squanch-Grade Plasma Conduit",
        retrieve_story="You haggle the twitchy vendor into a corner. Defeated, he slaps a Squanch-Grade Plasma Conduit on the counter.",
        rick_install=("Rick: \"Squanchy's sketchy, but his hardware's clean.\" He threads the "
                      "conduit through the casing. OMNI-CORE: Plasma Conduit installed."),
        core_part="Plasma Conduit",
        riddle_extra="A Squanch-Grade Plasma Conduit is for sale at the alien market. HAGGLE the vendor down.",
        completion="Plasma Conduit installed.",
    ),
    dict(
        act="Act IV: Existence Is Pain", title="The Coil Only a Meeseeks Can Get",
        character="Mr. Meeseeks", giver_npc="Mr. Meeseeks",
        persona="A blue being summoned to do one task, then poof. Cheerful until the task drags on. 'Existence is pain!'",
        motif=10,  # meeseeks_box_room, you call. Press the box, make a wish, try not to die.
        rick_gift="Fresh Meeseeks Box Battery",
        rick_send=("Rick: \"Part four is an Existential Flux Coil. Nasty to grab - so we let "
                   "something disposable do it. There's a Meeseeks whose box died mid-task; "
                   "he's been screaming for years. Bring him this battery, he'll owe you one.\""),
        char_need=("'OOH, a fresh battery! I'm Mr. Meeseeks, LOOK AT ME!' He vibrates with relief. "
                   "'You need a Flux Coil? Go to my box room and CALL a Meeseeks - he'll yank it "
                   "out of the unstable zone so you don't have to. Existence is paaain!'"),
        item="Existential Flux Coil",
        retrieve_story="You CALL a Meeseeks. 'CAN DO!' It dives into the flux, screams gloriously, and hands you an Existential Flux Coil before poofing.",
        rick_install=("Rick: \"Meeseeks: nature's disposable interns.\" He slots the coil. "
                      "OMNI-CORE: Flux Stabilizer installed."),
        core_part="Flux Stabilizer",
        riddle_extra="Go to the Meeseeks box room and CALL a Meeseeks to fetch the Existential Flux Coil.",
        completion="Flux Stabilizer installed.",
    ),
    dict(
        act="Act V: The Smartest Morty", title="The Heart of the Curve",
        character="President Morty", giver_npc="President Morty",
        persona="Calm, calculating, chillingly intelligent. Smiles like he already planned this.",
        motif=9,  # dark_portal_chamber, you investigate. *burp*
        rick_gift="Encrypted Data-Stick",
        rick_send=("Rick: \"Last part's a Curve-Stabilized Singularity, and the only one in "
                   "reach is behind a dark portal President Morty controls. I don't trust that "
                   "kid as far as I can throw a galaxy, but take him this data-stick and get me "
                   "the part. Then we're DONE, {pc}.\""),
        char_need=("President Morty pockets the data-stick, unsmiling. \"Rick always needs one "
                   "last favor. The Singularity sits inside the dark portal chamber. INVESTIGATE "
                   "the portal. Try not to fall in. I have plans that require you intact.\""),
        item="Curve-Stabilized Singularity",
        retrieve_story="You investigate the throbbing green portal. A pinprick of impossible density drifts out: the Curve-Stabilized Singularity.",
        rick_install=("Rick seats the Singularity. The OMNI-CORE hums to life. \"That's it, {pc}. "
                      "We did it. Infinite, guilt-free power forever.\""),
        core_part="Singularity Heart",
        riddle_extra="The Curve-Stabilized Singularity is inside the dark portal chamber. INVESTIGATE the portal.",
        completion="Singularity Heart installed. OMNI-CORE complete.",
    ),
]

NPC_PREQUEST_CHAT = {
    # What everybody says when Morty bugs them before I've sent him their way. The intro
    # runs once, a line per talk, and the five of them together tell my whole story from
    # the cheap seats. After that it cycles three "go see Rick" brush-offs at random. No repeats.
    "Zeep Xanflorp": {
        "intro": [
            "Zeep barely looks up from a glowing schematic. \"A Morty. So Rick's reduced to subcontracting his legwork to a child. The empire crumbles.\"",
            "\"You do know his great power source died? The little people he farmed for energy organized and walked off the job. Inside MY domain, no less. I built a whole universe in that battery.\"",
            "\"So now he welds together a replacement out of parts he can't fetch himself, because half the multiverse wants a Rick dead on sight. Tragic. Hilarious. Both.\"",
            "Zeep finally meets your eyes. \"Here's what he won't tell you, kid: Rick only builds something new when the old thing humiliated him. Whatever he's making, it's an apology he'll never say out loud.\"",
            "\"Now run along. Tell Rick that Zeep intends to watch this one fail in person. And that he still has to come ask me himself.\"",
        ],
        "endings": [
            "Zeep waves you off. \"Run back to Rick. Tell him Zeep's enjoying the show.\"",
            "Zeep returns to his schematic. \"We're done until Rick lowers himself to ask me directly. Shoo.\"",
            "Zeep smirks. \"Come back when Rick has the spine to make the request himself.\"",
        ],
    },
    "Birdperson": {
        "intro": [
            "Birdperson regards you in long silence. \"Morty. Rick speaks of you. Rarely kindly. Always proudly. I knew why you had come before you did.\"",
            "\"Once, Rick and I fought a war so that no being would be owned by another. We won. Then he went home and built a universe of small people to power his ship.\"",
            "\"Now those people have freed themselves, and he scrambles to replace them. He calls this progress. I call it the same war, fought now against himself.\"",
            "\"The parts he sends you to gather are not toys, {pc}. I have watched many terrible things begin as small, reasonable pieces.\"",
            "Birdperson rises. \"I will give him what he needs, for the sake of old brotherhood. But the asking must come from Rick. Return to him.\"",
        ],
        "endings": [
            "Birdperson inclines his head slowly. \"Return to Rick. When he is ready to ask, I will be ready to answer.\"",
            "Birdperson is still as stone. \"There is nothing here for you yet, young one. Seek Rick first.\"",
            "Birdperson's mechanical eye whirs. \"Go. Tell Rick that Birdperson still remembers the war. He will understand.\"",
        ],
    },
    "Squanchy": {
        "intro": [
            "Squanchy sprawls across a crate, grinning. \"Heeey, a little Morty! Rick sent his tiniest guy to run the scary errands? Classic squanch move.\"",
            "\"Me and Rick squanched through the bad old days together, baby. I know what his shopping list looks like when he's truly desperate.\"",
            "He flicks his tail, claws glinting. \"And this list is a HOT one. You got any idea how many dimensions would gut a guy for even ONE of the parts he's chasing?\"",
            "\"He's not just building a battery, sweetie. He's lighting a flare over his own head and pointing it at you, while he hides safe at the workbench.\"",
            "Squanchy's grin sharpens. \"I'll squanch him a favor, for old times. But Rick wants Squanchy, Rick comes and asks me to my face. Now scoot.\"",
        ],
        "endings": [
            "Squanchy yawns, all teeth. \"Go squanch off to Rick, little buddy. He knows where to find me.\"",
            "Squanchy bats at a dust mote. \"Nothin' to squanch about till Rick asks me himself. Scoot.\"",
            "Squanchy purrs. \"Tell Rick the first round's on him. Then we squanch business.\"",
        ],
    },
    "Mr. Meeseeks": {
        "intro": [
            "The Meeseeks erupts upright, grinning. \"OOOH! Hi! I'm Mr. Meeseeks! LOOK AT ME!\"",
            "\"Rick made me to do ONE little job, and then my box broke, and I've been HERE, existing, for so very long. Existence is paaain, Morty!\"",
            "His grin flickers. \"You know who else Rick made to do his jobs? Those little battery people. Used 'em up and tossed 'em. Just like he'll toss me. Just like... wait.\"",
            "He grabs your shoulders, eyes huge. \"He's building a whole NEW thing to use up, isn't he? And he sent YOU to carry the pieces. Oh no. Oh no no no, {pc}, do you see it too?\"",
            "\"Get Rick to give me a REAL task so I can POOF before I think about this one more second! Go! Go ask Rick! GO!\"",
        ],
        "endings": [
            "Mr. Meeseeks bounces on his heels. \"Go talk to Rick! Get me a task! I NEED a task, Morty, please!\"",
            "Mr. Meeseeks' grin twitches. \"No job yet? That's fine! That's FINE! Go get one from Rick! Hurry, existence is paaain!\"",
            "Mr. Meeseeks claps frantically. \"Rick points, I poof! Go make him point at me! GO, {pc}!\"",
        ],
    },
    "President Morty": {
        "intro": [
            "President Morty studies you with a faint smile. \"Hello, me. Or close enough. Funny, isn't it, how every version of us ends up fetching for some version of him.\"",
            "\"I know all of it already. The battery that unionized. The old rival, the old soldier, the old party animal. Rick calling in everyone he ever burned, one favor at a time.\"",
            "\"He believes he's building a power source. What he's actually assembling is a confession, made of every person who ever had a reason to tell him no.\"",
            "He turns a coin over his knuckles. \"And the one piece that holds it all together is a Morty doing exactly as he's told. That part never changes, in any timeline. I made certain to count on it.\"",
            "\"I'll hand him the last piece when the moment comes. For now, keep up appearances. Let Rick make the request. Run along, me.\"",
        ],
        "endings": [
            "President Morty folds his hands. \"Run along to Rick. His last piece is safe with me, until it isn't.\"",
            "President Morty smiles thinly. \"Nothing for you here until Rick asks. And he will. They always do.\"",
            "President Morty turns back to a wall of screens. \"Go see Rick. Everything is proceeding exactly as I intend.\"",
        ],
    },
}

# Everything the main-quest crew says, per stage. Three story beats once, a line per talk,
# then three reminders on random rotation. They go by name; my own lines use
# {gift}/{character}/{item} so I'm not retyping the same junk five times. I'm efficient.
STORY_CHAT = {
    "Zeep Xanflorp": {
        "arrive": {
            "story": [
                "Zeep eyes the {gift} in your hands like it's diseased. \"A peace accord. From Rick. He's apologizing in document form because he can't form the words with his mouth.\"",
                "\"You understand what this is, errand boy? Rick needs something only I can make, and he'd sign a treaty before admitting that out loud.\"",
                "\"Fine. Hand it over properly and I'll consider lowering myself to help. Slowly. While judging him.\"",
            ],
            "cycle": [
                "Zeep taps the air impatiently. \"The accord, child. GIVE me the {gift} so we can get this humiliation moving.\"",
                "\"I'm not accepting it telepathically. Hand over the {gift}, or did Rick forget to install object permanence in you?\"",
                "\"Still holding it? Give me the {gift}. My genius keeps a schedule.\"",
            ],
        },
        "retrieve": {
            "story": [
                "Zeep sighs at the signed accord. \"There. We have an arrangement. Try not to feel important about it.\"",
                "\"The part you want is a Void Shard, a folded pocket of space-time I left wedged in a workbench in some garbage garage dimension.\"",
                "\"TINKER with that bench like you almost know what you're doing and the Shard pops free. Don't drop it into a smaller universe. I have. It's annoying.\"",
            ],
            "cycle": [
                "Zeep waves a hand. \"Still here? Go TINKER the workbench in the garage dimension and bring back the Tessellated Void Shard.\"",
                "\"The Shard won't fetch itself, errand boy. TINKER the bench. A houseplant could manage this.\"",
                "\"Tinker. Bench. Void Shard. I've explained it more times than Rick deserves. Go.\"",
            ],
        },
        "to_rick": {
            "story": [
                "Zeep eyes the Void Shard in your hands. \"Hm. You got it out without folding yourself into a singularity. Color me mildly less unimpressed.\"",
                "\"Take it to Rick. Watch his face when he realizes my casework is cleaner than anything he's welded in decades.\"",
                "\"And tell him the accord holds only as long as he stops pretending he didn't need me.\"",
            ],
            "cycle": [
                "Zeep shoos you. \"Why are you still here? Take the Shard to Rick. That is the entire point of you.\"",
                "\"Go give Rick his Void Shard, errand boy. I have superior things to do.\"",
                "\"The Shard goes to Rick. You go away. Everyone wins, mostly me.\"",
            ],
        },
        "done": {
            "story": [
                "Zeep barely looks up. \"Oh. You. The Shard worked, didn't it. Of course it worked. I made it.\"",
                "\"Whatever Rick's stacking those parts into, it'll be impressive right up until it humiliates him. They always do.\"",
                "\"Run along. Go fetch his next embarrassment. I'll be here, being correct.\"",
            ],
            "cycle": [
                "Zeep smirks. \"We're square, child. Tell Rick his casing holds. Grudgingly. Like our truce.\"",
                "\"Nothing more for you here. Go be Rick's hands somewhere else.\"",
                "\"Still impressed by my work? Good instinct. Now shoo.\"",
            ],
        },
    },
    "Birdperson": {
        "arrive": {
            "story": [
                "Birdperson's gaze settles on the {gift} you're holding. \"A tune-up kit. Rick remembers I am part machine now. He remembers when it is useful to him.\"",
                "\"We were soldiers together, {pc}. I have learned that Rick's gifts always arrive attached to a request.\"",
                "\"Place it in my hands properly. I will not refuse an old comrade. But I will not pretend I do not see the shape of this.\"",
            ],
            "cycle": [
                "\"The kit, young one. Give me the {gift}, and we will speak of what Rick truly wants.\"",
                "\"Hand me the {gift}. A soldier does not leave a task half-delivered.\"",
                "Birdperson waits, unmoving. \"The {gift}. When you are ready.\"",
            ],
        },
        "retrieve": {
            "story": [
                "Birdperson's eyes dim in memory. \"In the war, we buried our War-Forged Capacitors in the wasteland, so the Federation could never turn our own power against us.\"",
                "\"One remains, beneath a fallen banner in the ruins. SCAVENGE for it. What you find there was paid for in blood.\"",
                "\"Carry it with respect, {pc}. It has outlived everyone who made it.\"",
            ],
            "cycle": [
                "\"Return to the wasteland ruins. SCAVENGE beneath the fallen banner for the War-Forged Capacitor.\"",
                "Birdperson points a slow arm. \"The Capacitor waits in the ruins. SCAVENGE. Do not return empty.\"",
                "\"The cause requires the Capacitor. Go to the wasteland and SCAVENGE it free.\"",
            ],
        },
        "to_rick": {
            "story": [
                "Birdperson studies the humming Capacitor in your grip. \"It still lives. Good. The war made things that do not die easily.\"",
                "\"Take it to Rick. Tell him it is the last of its kind, and that I expect it used for something better than a battery.\"",
                "\"Though I know Rick. It will be used for exactly a battery.\"",
            ],
            "cycle": [
                "\"Bring the Capacitor to Rick, {pc}. The old gear should serve once more.\"",
                "Birdperson nods toward the horizon. \"Rick is waiting. Carry the Capacitor to him.\"",
                "\"Your task is not done until Rick holds it. Go.\"",
            ],
        },
        "done": {
            "story": [
                "Birdperson regards you with something almost warm. \"The Capacitor serves Rick now. The circle continues. It always does, with him.\"",
                "\"He frees a thing, then cages another to replace it. One day he will run out of friends to ask. That day worries me, {pc}.\"",
                "\"Go. Whatever piece he sends you for next, walk carefully. The pieces are getting heavier.\"",
            ],
            "cycle": [
                "Birdperson inclines his head. \"We are square, young one. Tell Rick that Birdperson kept his word.\"",
                "\"There is nothing more here. The wasteland keeps its silence now.\"",
                "\"Go in peace, {pc}. You carried it well.\"",
            ],
        },
    },
    "Squanchy": {
        "arrive": {
            "story": [
                "Squanchy's nose twitches at the {gift} in your hands, eyes already rolling back. \"Ohhh, the GOOD Eyehole wine. Rick remembered. The magnificent squanch.\"",
                "\"You don't bring a squanch this bottle unless you need somethin' squanched bad, baby. So let's hear it. After a sip.\"",
                "\"Hand it over proper first, little Morty. A squanch's hospitality has STANDARDS.\"",
            ],
            "cycle": [
                "Squanchy makes grabby paws. \"The bottle, sweetie. GIVE me the {gift} before I squanch it out of your tiny hands.\"",
                "\"C'mon, c'mon, hand over the {gift}. My liver's been waitin' all day.\"",
                "\"You're still holdin' my wine, baby. Give. The {gift}. Squanch it here.\"",
            ],
        },
        "retrieve": {
            "story": [
                "Squanchy takes a long pull and grins, fangs out. \"Okaaay. Now we squanch business. There's a Plasma Conduit at the alien market, top shelf, squanch-grade.\"",
                "\"But that vendor's a crook with eight wallets and no soul. You don't BUY from a guy like that, baby. You HAGGLE him into the floor.\"",
                "\"Squanch him hard, little Morty. Make his ancestors feel it.\"",
            ],
            "cycle": [
                "Squanchy waves the bottle. \"Go to the alien market and HAGGLE that crook down for the Squanch-Grade Plasma Conduit, baby.\"",
                "\"The Conduit's still at the market, sweetie. HAGGLE. Don't let the vendor squanch YOU.\"",
                "\"Market. Vendor. HAGGLE. Bring back the Conduit. Easy squanch.\"",
            ],
        },
        "to_rick": {
            "story": [
                "Squanchy whistles at the Conduit. \"Ohh, you squanched him good! Look at that. Barely a scratch and probably only mostly stolen.\"",
                "\"Take it to Rick, baby. Tell him Squanchy's hardware is always clean. Cleaner than his conscience, anyway.\"",
                "\"And tell him the tab's still runnin' on that thing from the squanch moon. He knows.\"",
            ],
            "cycle": [
                "Squanchy points lazily. \"Run that Conduit over to Rick, little buddy. Go on, squanch.\"",
                "\"Rick's waitin' on his shiny part, sweetie. Take the Conduit to him.\"",
                "\"You got it, now squanch it to Rick. That's the gig, baby.\"",
            ],
        },
        "done": {
            "story": [
                "Squanchy lounges, utterly relaxed. \"Heeey, my favorite errand-Morty. The Conduit workin' out for Rick? Course it is.\"",
                "\"Word on the street is Rick's collectin' some HEAVY squanch lately, baby. People are noticin'. People with teeth.\"",
                "\"You watch yourself out there, little Morty. Whatever Rick's buildin', the wrong squanchers want it too.\"",
            ],
            "cycle": [
                "Squanchy raises an imaginary glass. \"We're square, baby. Tell Rick the next bottle's on HIM.\"",
                "\"Nothin' left to squanch here, sweetie. Go enjoy the multiverse.\"",
                "\"You're alright, little Morty. Squanch on.\"",
            ],
        },
    },
    "Mr. Meeseeks": {
        "arrive": {
            "story": [
                "The Meeseeks gasps at the {gift}. \"A FRESH BOX BATTERY?! Oh thank Rick, thank RICK, I can almost feel the poof from here!\"",
                "\"Gimme gimme gimme, ooh, with a workin' box I can finish ANYTHING, I can finally STOP, Morty, I can finally REST!\"",
                "\"Hand it over, hand it over, I'll do whatever you need, just GIVE me the {gift}!\"",
            ],
            "cycle": [
                "Mr. Meeseeks vibrates. \"The battery! GIVE me the {gift}! I can taste the poof, Morty, PLEASE!\"",
                "\"You're still holding it?! The {gift}! Hand it over before I think about existing any longer!\"",
                "\"Battery. Me. Now. GIVE me the {gift}, ohhh existence is paaain!\"",
            ],
        },
        "retrieve": {
            "story": [
                "The Meeseeks snaps the battery in and SHUDDERS with joy. \"OHHH that's the stuff! Okay! Okay okay okay, your turn, Morty!\"",
                "\"You need an Existential Flux Coil! It's in a zone so unstable it'd kill YOU, so go to my box room and CALL a Meeseeks instead!\"",
                "\"He'll grab it, he'll scream, he'll POOF, it's beautiful, it's what we're FOR! Go CALL one!\"",
            ],
            "cycle": [
                "\"Go to the box room and CALL a Meeseeks to yank out the Existential Flux Coil, Morty! Existence is pain, but the Coil's worth it!\"",
                "Mr. Meeseeks bounces. \"The Coil! CALL a Meeseeks in the box room! Let HIM do the dyin' part!\"",
                "\"Box room. Press the box. CALL. Flux Coil. GO GO GO, {pc}!\"",
            ],
        },
        "to_rick": {
            "story": [
                "The Meeseeks stares at the Coil with shining eyes. \"You GOT it! A Meeseeks poofed for that, and he poofed HAPPY, oh I'm so jealous!\"",
                "\"Take it to Rick, Morty, complete the task, finish the chain, let everybody POOF in peace!\"",
                "\"Go go go! The sooner Rick's done, the sooner WE'RE done! Maybe! Hopefully! PLEASE!\"",
            ],
            "cycle": [
                "\"Take the Flux Coil to Rick, Morty! Finish it! End my suffering by proxy!\"",
                "Mr. Meeseeks claps. \"Rick! The Coil! Go give it to Rick so SOMETHING gets completed today!\"",
                "\"You're SO close, {pc}! Coil to Rick! Then maybe, MAYBE, I can stop existing!\"",
            ],
        },
        "done": {
            "story": [
                "The Meeseeks is still here, grin stretched tight. \"Oh. Oh you're back. The Coil worked. So why am I... why am I still HERE, Morty?\"",
                "\"My task was helping you. I HELPED. So I should POOF. Unless... unless helping Rick is never really DONE. Oh no.\"",
                "\"Is that the secret, Morty? Does anyone Rick uses ever really get to stop? ...Go. GO, before I think about it more!\"",
            ],
            "cycle": [
                "Mr. Meeseeks twitches a smile. \"We did it! We're square! Now WHY am I still here, hahaha, ha, ha...\"",
                "\"Nothing else for you, Morty! Go! Let me have my little existential crisis in private!\"",
                "\"You're a good Morty. Tell Rick a Meeseeks said hi. And that he's a monster. Both!\"",
            ],
        },
    },
    "President Morty": {
        "arrive": {
            "story": [
                "President Morty barely glances at the {gift} in your hand. \"An encrypted data-stick. Rick thinks he's sending me a message. He's sending me exactly what I asked him to, through you.\"",
                "\"It's almost sweet, watching him believe he's running this. Sit. Or don't. You'll do what comes next either way.\"",
                "\"Give me the {gift}, me. Let's keep the wheels turning.\"",
            ],
            "cycle": [
                "President Morty holds out a hand. \"The data-stick. Give me the {gift}. We both know you're going to.\"",
                "\"Hand over the {gift}, me. Resisting would be a new and interesting timeline. Not today, though.\"",
                "\"Still holding it? Give me the {gift}. The schedule is the schedule.\"",
            ],
        },
        "retrieve": {
            "story": [
                "President Morty pockets the stick. \"Good. The last piece Rick wants is a Curve-Stabilized Singularity, behind a dark portal I happen to control.\"",
                "\"INVESTIGATE the portal in the dark chamber. The Singularity will come to you. I've already arranged for it to.\"",
                "\"Try not to fall in, me. I have uses for you that require you whole. For now.\"",
            ],
            "cycle": [
                "\"Return to the dark portal chamber and INVESTIGATE the portal for the Curve-Stabilized Singularity.\"",
                "President Morty gestures faintly. \"The Singularity waits behind the portal. INVESTIGATE it. It's expecting you.\"",
                "\"Dark chamber. The portal. INVESTIGATE. Bring out the Singularity. You know the steps, me.\"",
            ],
        },
        "to_rick": {
            "story": [
                "President Morty studies the Singularity in your hands and smiles. \"There it is. The heart of Rick's little machine. The final piece on the board.\"",
                "\"Take it to him. Watch him switch it on, so proud, so sure he built something that's his.\"",
                "\"He didn't. But let's let him have the moment. Go on, me. Deliver the ending.\"",
            ],
            "cycle": [
                "President Morty nods. \"Take the Singularity to Rick, me. The last move is his to think he made.\"",
                "\"Carry it to Rick. Everything finishes when he seats that piece.\"",
                "\"Go. Give Rick his Singularity. I'll be watching how it all comes together.\"",
            ],
        },
        "done": {
            "story": [
                "President Morty is watching you on a screen before you even speak. \"The OMNI-CORE runs. Rick has his infinite power. He thinks that's the end of the story.\"",
                "\"Every piece came from someone he burned, carried by a Morty who trusted him. That isn't a power source, me. That's a pattern. And patterns can be inherited.\"",
                "\"You did beautifully. You always do. Now go back to Rick, and don't think too hard about how easy all of this was.\"",
            ],
            "cycle": [
                "President Morty smiles. \"We're square, me. Give Rick my regards. He'll need them eventually.\"",
                "\"Nothing more for now. Everything else is already in motion.\"",
                "\"Run along. The board looks exactly how I wanted it to.\"",
            ],
        },
    },
}

RICK_CHAT = {
    "deliver_char": {
        "story": [
            "Rick doesn't look up from the workbench. \"You're still here? The {gift}'s not gonna deliver itself to {character}, {pc}.\"",
            "\"Look, the faster you hand {character} that {gift}, the faster I get my part and the faster you stop hovering.\"",
            "\"Go. Portal's charged. {character}. {gift}. Try not to overthink the one job.\"",
        ],
        "cycle": [
            "Rick waves a wrench. \"Still here? Take the {gift} to {character}, {pc}. *burp* Chop chop.\"",
            "\"{character}'s waiting on that {gift}, Morty. I'm waiting on you. Everybody's waiting. Go.\"",
            "\"Deliver the {gift} to {character}. It's not complicated. It's the literal opposite of my job.\"",
        ],
    },
    "retrieve": {
        "story": [
            "Rick squints at a schematic. \"So {character} sent you after the {item}. Good. That's the part I actually need. The rest is networking.\"",
            "\"Don't bring me a fake. I'll know. I built the scanner that knows. Don't make me use the scanner.\"",
            "\"Get the {item} and get back. The OMNI-CORE's got a {item}-shaped hole in it and I hate holes.\"",
        ],
        "cycle": [
            "Rick gestures vaguely. \"Why're you here? Go get me the {item}, {pc}. *burp*\"",
            "\"The {item}, Morty. Still need it. Still don't have it. Notice the problem?\"",
            "\"Less talking, more {item}. Go.\"",
        ],
    },
    "rick_noitem": {
        "story": [
            "Rick holds out a hand without looking. \"Gimme the {item}. ...You don't have it. I can tell by the empty hand and the guilty face.\"",
            "\"Morty. The {item}. The whole reason you left. The thing. Did you get the thing?\"",
            "\"Go back and get the {item} before I build a Morty that can. *burp*\"",
        ],
        "cycle": [
            "Rick sighs. \"No {item}, no progress, {pc}. Go get it.\"",
            "\"Empty-handed again. The {item}, Morty. Find it.\"",
            "\"I need the {item}, not your company. Go.\"",
        ],
    },
    "rick_haveitem": {
        "story": [
            "Rick's eyes lock onto the {item}. \"Is that... yeah. Yeah that's it. Gimme gimme gimme, {pc}, hand over the {item}.\"",
            "\"Don't just stand there cradling my OMNI-CORE part like it's a hamster. GIVE it here.\"",
            "\"Use 'give', Morty. Give me the {item}. Let's bolt this thing in.\"",
        ],
        "cycle": [
            "Rick makes grabby hands. \"The {item}, {pc}. GIVE it to me. We're so close.\"",
            "\"You're holding the {item} RIGHT THERE. Give it. Come on.\"",
            "\"Hand over the {item} already, Morty. The core's not gonna assemble out of vibes.\"",
        ],
    },
    "complete": {
        "story": [
            "Rick leans back, OMNI-CORE humming. \"It's done, {pc}. Infinite, guilt-free power. We actually pulled it off.\"",
            "\"Five impossible parts, one tiny idiot grandson, zero deaths that mattered. I'd call that a win.\"",
            "\"Go enjoy the apocalypse you helped cause. *burp* I earned a nap.\"",
        ],
        "cycle": [
            "Rick waves you off. \"It's done, Morty. Go do whatever it is you do. *burp*\"",
            "\"OMNI-CORE's humming. We're retired from questing. Shoo.\"",
            "\"Infinite power, {pc}. Try not to break it before I plug in the cable box.\"",
        ],
    },
}

# Same setup for the side-quest crowd. Three story beats once, then three rotating
# reminders. For the 'need' state I staple the hint on only after the story's done,
# never during it. Let 'em squirm through three lines first, Morty.
SIDEQUEST_CHAT = {
    "Jerry Smith": {
        "need": {
            "story": [
                "Jerry sniffles. \"My sentient couch took my World's Best Dad Mug HOSTAGE. It says I don't 'earn' it. If you had some snacks, you could maybe negotiate with it?\"",
                "\"It's the only thing that's ever called me the best at anything, Morty. Beth bought it ironically, but I CHOOSE to believe it.\"",
                "\"I tried reasoning with the couch. It just absorbed the remote and my dignity. You're my only hope, which is, honestly, on brand for my life.\"",
            ],
            "cycle": [
                "Jerry wrings his hands. \"Please, Morty, get my mug back from the couch. You're basically my best friend right now, which is also depressing.\"",
                "\"Any luck with the couch? It's started charging me rent. For the cushions. That I own.\"",
                "\"The mug, Morty. The World's Best Dad Mug. I need to be told I'm the best by ceramic again.\"",
            ],
        },
        "have": {
            "story": [
                "\"You found my World's Best Dad Mug?! That couch had NO right to take it. Hand it back, I'm begging you.\"",
                "\"Oh thank god, thank you, you wonderful boy. Rick never gets me anything back. He once portaled my car into a sun.\"",
                "\"Give it here, give it here, let me hold the lie that completes me.\"",
            ],
            "cycle": [
                "Jerry reaches out, trembling. \"The mug, Morty. Give me the World's Best Dad Mug. Please.\"",
                "\"You're still holding it. Hand over the mug before the couch wants it back.\"",
                "\"Give me the mug, Morty. I need this win. I need ONE win.\"",
            ],
        },
        "done": {
            "story": [
                "Jerry hugs the mug to his chest. \"I have it back. I'm whole. Well, as whole as I get, which the family will confirm is not very.\"",
                "\"You're a better grandson to me than you are to Rick, and HE'S the one who likes you. Funny how that works.\"",
                "\"If you ever need someone to believe in you with zero qualifications, I'm your guy, Morty.\"",
            ],
            "cycle": [
                "Jerry beams. \"Thanks again, {pc}! Best Dad, right here. It says so on the mug.\"",
                "\"You're the best, Morty. Don't tell Rick I said someone other than him was useful.\"",
                "\"Come back anytime. I'll be here. Where else would I be.\"",
            ],
        },
    },
    "Summer Smith": {
        "need": {
            "story": [
                "Summer groans. \"My PHONE got eaten by that 'Roy' machine at Blips and Chitz. My whole follower count is in there. Get a token and PLAY it out, please.\"",
                "\"Do you know who I am without my phone, Morty? Nobody. I'm a girl just STANDING here. It's a nightmare.\"",
                "\"Ugh, and of course you're busy with Grandpa Rick's weird scavenger hunt. Can you multitask, or are you as useless as you look?\"",
            ],
            "cycle": [
                "Summer holds out an empty hand. \"Phone. Roy machine. PLAY it. Go, Morty, I'm losing followers by the second.\"",
                "\"Still no phone? I've had to make eye contact with PEOPLE, Morty. Real ones. It's awful.\"",
                "\"Get my phone out of the Roy machine. I will literally owe you, and I never owe anybody.\"",
            ],
        },
        "have": {
            "story": [
                "\"You actually pulled my phone out of that thing?! Ugh, FINALLY. Hand it over before I lose any more followers.\"",
                "\"Wait, did you PLAY as Roy? Did you live his whole boring life? You did, didn't you. You've got Roy eyes now.\"",
                "\"Whatever. Give me the phone. We do not speak of Roy.\"",
            ],
            "cycle": [
                "Summer snaps her fingers. \"Phone. Now. Hand it over, Morty.\"",
                "\"You're holding my entire identity in your sweaty hand. Give it.\"",
                "\"The phone, Morty. Give. I have a brand to maintain.\"",
            ],
        },
        "done": {
            "story": [
                "Summer is already typing. \"Got it. Posting that you 'rescued my phone from a parallel dimension.' You're trending. You're welcome.\"",
                "\"Honestly? Thanks. Rick treats you like a tool, but you came through for me. That's more than he does.\"",
                "\"Don't let it go to your head. I'll deny this entire conversation happened.\"",
            ],
            "cycle": [
                "Summer doesn't look up. \"Thanks again, {pc}. You're a legend. Lowercase l.\"",
                "\"We're good, Morty. Now stop hovering, it's weird.\"",
                "\"You're alright. For a brother. On Rick's errand-boy salary.\"",
            ],
        },
    },
    "Beth Smith": {
        "need": {
            "story": [
                "Beth, scrubbing in: \"I need a Stable-Grade Alien Herb for horse surgery. The gossiping trees know where it grows, but they only trade for fresh gossip.\"",
                "\"The horse is sedated, Morty, which means I have a window, a scalpel, and a deadline. Romantic, isn't it.\"",
                "\"You're Dad's little courier now? Don't worry about it. Helping me is at least an honest errand. Probably the only one you'll run today.\"",
            ],
            "cycle": [
                "Beth checks the clock. \"Tabloid Datapad, talking trees, LISTEN, trade the gossip. Get me the herb, Morty.\"",
                "\"Still no herb? The horse isn't getting LESS open, Morty. Hurry.\"",
                "\"Bring me the Stable-Grade Alien Herb. A creature's life is technically in your tiny hands.\"",
            ],
        },
        "have": {
            "story": [
                "\"Is that the Stable-Grade Alien Herb? Oh thank god, that horse is not going to operate on itself. Hand it over.\"",
                "\"You got the trees to gossip? Good. They're worse than the PTA and twice as leafy.\"",
                "\"Give me the herb, Morty, before the anesthesia wears off and this becomes a rodeo.\"",
            ],
            "cycle": [
                "Beth holds out a gloved hand. \"The herb. Give it to me, Morty. The horse is waiting.\"",
                "\"You're still holding it. Surgery, Morty. Hand it over.\"",
                "\"Herb. Now. Before I have to improvise, and you do NOT want to see me improvise.\"",
            ],
        },
        "done": {
            "story": [
                "Beth peels off her gloves. \"The horse will live. Probably. I rate that a strong success by my standards.\"",
                "\"You know, you and I are the ones who actually DO things in this family. Dad just narrates and drinks.\"",
                "\"Thank you, Morty. Genuinely. Now go run whatever Rick's got you running, and be careful out there.\"",
            ],
            "cycle": [
                "Beth nods. \"Thanks again, {pc}. The horse sends its regards. It can't, but emotionally.\"",
                "\"We're square, Morty. Go on. Try not to die for your grandfather.\"",
                "\"You did good. Don't tell Dad I said you're more reliable than him. He'll sulk.\"",
            ],
        },
    },
    "Scary Terry": {
        "need": {
            "story": [
                "\"Yo, I lost my Dream Knife inside some nerd's nightmare, bitch! Can't scare nobody without it. Knock yourself out and go get it, bitch!\"",
                "\"You don't get it, bitch, a dream demon without his knife is just a guy in a sweater yelling at you in your sleep. It's embarrassing!\"",
                "\"I got a reputation, bitch! Kids gotta wake up SCREAMING, not goin' 'aw, he tried.' Get my knife back, bitch!\"",
            ],
            "cycle": [
                "Scary Terry crosses his arms. \"Box of Sleeping Pills, CONNECT to the dreamer, grab my knife, bitch. Easy peasy, bitch.\"",
                "\"Still no knife? I been scarin' people with FINGER GUNS, bitch. It's humiliating. Hurry up!\"",
                "\"Get my Dream Knife outta that nightmare, bitch. I got an appointment in a toddler's REM cycle.\"",
            ],
        },
        "have": {
            "story": [
                "\"MY DREAM KNIFE! You beautiful bastard, hand it here, I got people to scare, bitch!\"",
                "\"You went INTO the nightmare for it? That's metal, bitch. Respect. A little fear-respect.\"",
                "\"Gimme gimme, hand over the knife, bitch, I feel naked without it, and not the good scary kind!\"",
            ],
            "cycle": [
                "Scary Terry reaches out. \"The knife, bitch. Give me the Dream Knife. Come on, bitch.\"",
                "\"You're STILL holding it?! Hand over the knife, bitch, I got nightmares backed up!\"",
                "\"Dream Knife. My hand. Now. Give it, bitch!\"",
            ],
        },
        "done": {
            "story": [
                "Terry twirls the knife, grinning. \"Back in business, bitch! Tonight, every nerd in this sector wakes up cryin'. Beautiful.\"",
                "\"You're alright, bitch. You ever need somebody scared, you know a guy. I do birthdays. Sort of.\"",
                "\"Now beat it before I scare you on instinct, bitch. Old habits.\"",
            ],
            "cycle": [
                "\"We're square, bitch. Sleep tight. Or DON'T, bitch! Ha!\"",
                "\"Thanks again, {pc}. You're alright. For a snack-sized human, bitch.\"",
                "\"Go on, bitch. I got dreams to ruin.\"",
            ],
        },
    },
    "Mr. Poopybutthole": {
        "need": {
            "story": [
                "\"Ooo-wee! The bartender's holding my lucky shot glass till I clear my tab. I'm a bit short. Cover it and it's yours to grab, ya hear?\"",
                "\"That ol' glass got me through some rough patches, ya hear. After Rick shot me that one time, it's been a real comfort. No hard feelings on the shootin', mostly.\"",
                "\"You settle my tab and that glass is yours to fetch, friend. You got a good heart, I can tell, ooo-wee.\"",
            ],
            "cycle": [
                "Mr. Poopybutthole leans on the bar. \"Wad of Schmeckles, ORDER a round, settle my tab, grab the lucky glass. Ooo-wee, you got this!\"",
                "\"No luck yet, friend? That ol' tab ain't payin' itself, ya hear. Get some Schmeckles together.\"",
                "\"Settle the tab and the Lucky Shot Glass is yours to bring me, ooo-wee!\"",
            ],
        },
        "have": {
            "story": [
                "\"Ooo-wee, my Lucky Shot Glass! You sprung it loose? Hand it over, you wonderful soul, ya hear?\"",
                "\"I knew you were a good egg the second you walked in. Rick could learn a thing from you, ya hear, though don't tell him I said it.\"",
                "\"Pass it here, friend, gentle now, that's a lifetime of good luck in one little glass.\"",
            ],
            "cycle": [
                "Mr. Poopybutthole holds out both hands. \"The glass, friend. Hand over the Lucky Shot Glass, ooo-wee.\"",
                "\"Still holdin' my lucky glass, ya hear? Pass it on over, gentle now.\"",
                "\"The Lucky Shot Glass, friend. Give it here. Ooo-wee, I missed it.\"",
            ],
        },
        "done": {
            "story": [
                "Mr. Poopybutthole cradles the glass. \"Ooo-wee, my luck's back where it belongs! I feel ten years and one gunshot younger!\"",
                "\"You're good people, {pc}. The whole family's lucky to have ya, even if they're too busy to say it.\"",
                "\"Anything you need, you find ol' Mr. Poopybutthole. I owe ya one, ya hear?\"",
            ],
            "cycle": [
                "\"Thanks again, {pc}! Don't spend my luck all at once, ya hear!\"",
                "\"We're square, friend! Ooo-wee, what a day!\"",
                "\"You take care now. And tell Rick... actually, don't tell Rick anything. Ooo-wee.\"",
            ],
        },
    },
}

# Glexo the pawn dealer, same engine: three story beats once, then nudges that keep
# reminding Morty he can list, buy, and sell. The four-eyed weirdo grows on you.
SHOP_CHAT = {
    "Glexo Slimslom": {
        "talk": {
            "story": [
                "Glexo's four eyes swivel onto you. \"A Morty. Lemme guess: Rick's got you hauling parts across the multiverse and you're already broke. Seen it a thousand times.\"",
                "\"Name's Glexo Slimslom. I buy what you looted, I sell what you'll need, and I don't ask where any of it came from. Questions are bad for business.\"",
                "\"Free advice, kid, the only free thing in here: the junk Rick's collecting is worth more than your whole tab. Don't go flashing your inventory around. People notice.\"",
            ],
            "cycle": [
                "Glexo grunts. \"Whaddya want? `list` what I got, `buy <item>`, or `sell <item>` you don't need. Don't waste my time.\"",
                "Glexo taps the counter. \"You buyin' or browsin'? `list`, `buy`, `sell`. Clock's runnin', Morty.\"",
                "Glexo's eyes narrow. \"This ain't a hangout. `list`, `buy`, or `sell`, or beat it, kid.\"",
            ],
        },
    },
}

# ===== Side quests. Two stages, optional, way funnier than the main plot. Each one pays out a crafting piece you can't get anywhere else. =====
# Stage one: track down the one-of-a-kind KEY item. It's either on the floor or rotting inside some enemy you gotta kill.
# Stage two: drag that key to the room I hinted at and do the action there. That
# spits out the NEED item. Hand it to the NPC and they cough up a crafting piece
# you literally cannot get any other way. Every craft needs one. No shortcuts, Morty.
EXTENDED_SUBQUESTS = [
    dict(npc="Jerry Smith", motif=4,  # sentient_furniture, you negotiate. With a couch. Don't ask.
         key_item="Bag of Couch Snacks", need_item="World's Best Dad Mug",
         reward_item="Confidence Capacitor",
         lost_line=("Jerry sniffles. \"My sentient couch took my World's Best Dad Mug HOSTAGE. "
                    "It says I don't 'earn' it. If you had some snacks you could maybe... negotiate with it?\""),
         key_hint="Find a Bag of Couch Snacks, then go NEGOTIATE with the sentient furniture.",
         retrieve_line="You toss the couch the snacks and NEGOTIATE. Satisfied, it burps up Jerry's World's Best Dad Mug.",
         reward_line="Jerry weeps with joy and presses a Confidence Capacitor into your hands. 'I made this in a self-help seminar!'",
         give_line="\"You found my World's Best Dad Mug?! That couch had NO right to take it. Hand it back, I'm begging you.\""),
    dict(npc="Summer Smith", motif=2,  # blips_and_chitz, you play. Watch out for Roy.
         key_item="Spare Arcade Token", need_item="Summer's Phone",
         reward_item="Influencer Microchip",
         lost_line=("Summer groans. \"My PHONE got eaten by that 'Roy' machine at Blips and Chitz. "
                    "My whole follower count is in there. Get a token and PLAY it out, please.\""),
         key_hint="Find a Spare Arcade Token, then PLAY the machine at Blips and Chitz.",
         retrieve_line="You feed in the token and PLAY. You live a full life as Roy, die of old age, and the machine spits out Summer's Phone.",
         reward_line="Summer screenshots you immediately. 'You're a legend.' She hands you an Influencer Microchip.",
         give_line="\"You actually pulled my phone out of that thing?! Ugh, FINALLY. Hand it over before I lose any more followers.\""),
    dict(npc="Beth Smith", motif=5,  # talking_tree_forest, you listen. Trees talk. Deal with it.
         key_item="Tabloid Datapad", need_item="Stable-Grade Alien Herb",
         reward_item="Surgical Nanite Vial",
         lost_line=("Beth, scrubbing in: \"I need a Stable-Grade Alien Herb for horse surgery. The "
                    "gossiping trees know where it grows but they only trade for fresh gossip.\""),
         key_hint="Find a Tabloid Datapad, then LISTEN to the talking trees and trade them the gossip.",
         retrieve_line="You LISTEN, then dish the tabloid gossip. Scandalized and delighted, the trees drop a Stable-Grade Alien Herb.",
         reward_line="Beth pockets the herb. 'The horse will live. Probably.' She gives you a Surgical Nanite Vial.",
         give_line="\"Is that the Stable-Grade Alien Herb? Oh thank god, that horse is not going to operate on itself. Hand it over.\""),
    dict(npc="Scary Terry", motif=14,  # glarblon_mind, you connect. Telepathy, basically.
         key_item="Box of Sleeping Pills", need_item="Terry's Dream Knife",
         reward_item="Nightmare Fuel Cell",
         lost_line=("\"Yo, I lost my Dream Knife inside some nerd's nightmare, bitch! Can't scare "
                    "nobody without it. Knock yourself out and go get it, bitch!\""),
         key_hint="Find a Box of Sleeping Pills, then CONNECT to the dreaming mind to enter the nightmare.",
         retrieve_line="You take the pills and CONNECT to the sleeping mind. Inside the nightmare you pry loose Terry's Dream Knife.",
         reward_line="\"AY, my knife! You're alright, bitch.\" Terry slips you a Nightmare Fuel Cell. \"Bitch.\"",
         give_line="\"MY DREAM KNIFE! You beautiful bastard, hand it here, I got people to scare, bitch!\""),
    dict(npc="Mr. Poopybutthole", motif=12,  # blips_bar, you order. A drink. From a bar. Genius design.
         key_item="Wad of Schmeckles", need_item="Lucky Shot Glass",
         reward_item="Lucky Charm Resonator",
         lost_line=("\"Ooo-wee! The bartender's holding my lucky shot glass till I clear my tab. "
                    "I'm a bit short. Cover it and it's yours to grab, ya hear?\""),
         key_hint="Find a Wad of Schmeckles, then ORDER at the bar and settle the tab.",
         retrieve_line="You ORDER a round and slap down the Schmeckles. The bartender slides over Mr. Poopybutthole's Lucky Shot Glass.",
         reward_line="\"Ooo-wee, you're a good one!\" He hands you a Lucky Charm Resonator. \"Don't spend my luck all at once!\"",
         give_line="\"Ooo-wee, my Lucky Shot Glass! You sprung it loose? Hand it over, you wonderful soul, ya hear?\""),
]
# ===== Stats. HP, Charge, all the numbers that decide if you live. =====
EXPANDED_RACES = [
    {"name": "Force-Field Gauntlet", "hp_bonus": 5, "charge_bonus": -2, "special": "Rick's wrist-mounted shield projector. Soaks punishment for +5 Max HP, but the field constantly sips your reserves (-2 Charge). The sturdiest loadout in the garage."},
    {"name": "Laser Pistol", "hp_bonus": 3, "charge_bonus": 1, "special": "Rick's go-to sidearm. +2 Damage, plus +3 Max HP and +1 Charge. Point, shoot, move on."},
    {"name": "Recon Visor", "hp_bonus": 2, "charge_bonus": 2, "special": "A heads-up scanner with light plating. +1 Armor and a Scan that paints enemies in adjacent rooms. +2 Max HP / +2 Charge."},
    {"name": "Phoenix Implant", "hp_bonus": 4, "charge_bonus": -1, "special": "Salvaged Operation Phoenix tech. +4 Max HP and quietly knits you back together: it regenerates 1 HP every 5 moves. A little power-hungry (-1 Charge)."},
    {"name": "Neutrino Bomb", "hp_bonus": 0, "charge_bonus": 5, "special": "'In and out, twenty-minute adventure.' The most Charge of any loadout (+5) and a devastating charged blast in combat."},
    {"name": "Freeze Ray", "hp_bonus": 1, "charge_bonus": 3, "special": "Rick's freeze gun. A clean, balanced energy weapon: +3 Charge and +1 Max HP."},
    {"name": "Brainalyzer", "hp_bonus": 2, "charge_bonus": 0, "special": "A brain-scrambling headset. +1 Armor and a 10% chance to scramble an enemy's focus so its next attack misses. +2 Max HP."},
    {"name": "Kalaxian Crystals", "hp_bonus": -5, "charge_bonus": 0, "special": "Rick's favorite contraband. A reckless high: the lowest Max HP of any loadout (-5) and no special tricks. Pure, ill-advised vibes."},
]
EXPANDED_CLASSES = [
    {"name": "Dark Matter Cell", "hp_bonus": 0, "charge_bonus": 6, "special": "A volatile concentrated-dark-matter core: the most Charge of any attachment and the lowest HP, a glass cannon. Supercharges your Healing Serums and Energy Cells (+5 each), and its sensor pings nearby Quest-Rooms & the Pawn Shop (Q/$ shown dimmed)."},
    {"name": "Holo-Mapper", "hp_bonus": 2, "charge_bonus": 1, "special": "Projects the terrain ahead: SENSES nearby Items (I shown dimmed) and a 20% chance to reveal an adjacent room on entry. Well-rounded."},
    {"name": "Universal Translator", "hp_bonus": 1, "charge_bonus": 3, "special": "Smooths every conversation: SENSES nearby Main-Quest NPCs (N shown dimmed). Talking sometimes turns up extra intel or a small HP/Charge boost."},
    {"name": "Targeting Chip", "hp_bonus": 3, "charge_bonus": 2, "special": "A combat-analysis implant: +1 Damage, +1 Armor, and DOUBLE XP from every kill, so you level up fastest. No radar, so you fight blind but grow strong."},
    {"name": "Fabricator Drone", "hp_bonus": 2, "charge_bonus": 4, "special": "A pocket builder-bot: SENSES nearby Side-Quest NPCs (S shown dimmed), the folks who hand you crafting parts. It also has a 25% chance to build an item without using up your materials."},
    {"name": "Parasite Scanner", "hp_bonus": 4, "charge_bonus": 0, "special": "Sniffs out infestations: SENSES nearby Enemies (E shown dimmed) and deals +2 Damage. Tough, but low on Charge."},
    {"name": "Combat Exo-Rig", "hp_bonus": 6, "charge_bonus": -2, "special": "Brute-force exo-augments: +4 Damage and +6 Max HP, the toughest hitter in the garage. No radar and low Charge, just pure blind melee."},
    {"name": "Portal Coil", "hp_bonus": 0, "charge_bonus": 5, "special": "A spare portal-gun coil: +5 Charge, and it powers a Portal Gun (Replica) for free, so portal_jump to any visited room costs you no Charge. No radar; raw mobility is your edge."},
]
# Every class gets a passive RADAR. It paints ONE kind of marker, dimmed, for rooms you haven't
# walked into yet, but only within this Manhattan radius. Classes I left off this list get no radar,
# because they traded the map smarts for raw muscle or utility. Can't have everything, Morty.
CLASS_SENSE = {
    "Dark Matter Cell":     ("objective", 3),  # Quest rooms and the pawn shop (Q and the dollar sign).
    "Holo-Mapper":          ("items", 3),       # Loose items (I).
    "Universal Translator": ("main_npc", 3),    # Main-quest NPCs (N).
    "Fabricator Drone":     ("side_npc", 3),    # Side-quest NPCs (S).
    "Parasite Scanner":     ("enemy", 3),       # Enemies (E). The stabby ones.
}
# These are the dimmed radar colors. Faded versions of the normal markers so a sensed-but-unvisited
# room reads as 'I detect something there, haven't been yet.' Subtle. Like me.
DIM_SENSE_COLORS = {
    "dim_item": "#7A4A86", "dim_monster": "#8A3A3A", "dim_quest": "#2C7A4A",
    "dim_npc": "#8A7400", "dim_subnpc": "#2A6A8A", "dim_shop": "#8A5A00",
}
# ===== Monsters. Everything in the multiverse that wants you dead. =====
MONSTERS = [
    Monster(
        "Gromflomite Guard", 15, 15, 5,
        ["Federation Credits", "Energy Cell", "Healing Serum"],
        "A standard Galactic Federation soldier, heavily armed and bureaucratic.",
        special_attack_chance=0.25,
        special_attack_name="Suppressing Fire"
    ),
    Monster("Sentient Furniture", 20, 20, 6, ["Upholstery Scrap", "Energy Cell"], "A living piece of furniture, easily offended and surprisingly durable.", special_attack_chance=0.25, special_attack_name="Wild Swing"),
    Monster(
        "Zeep's Microverse Sentry", 25, 25, 8,
        ["Microverse Battery", "Healing Serum"],
        "A hulking security construct Zeep built to guard his microverse, all blades and contempt.",
        special_attack_chance=0.3,
        special_attack_name="Microverse Override",
        is_boss=True
    ),
    Monster("Death Stalker", 18, 18, 7, ["Wasteland Metal", "Energy Cell"], "A hulking, mutated beast from the Wasteland Dimension, always hunting.", special_attack_chance=0.3, special_attack_name="Wild Swing"),
    Monster("Council of Ricks Drone", 12, 12, 4, ["Drone Circuitry", "Healing Serum"], "An automated defense unit, programmed to protect the Council at all costs.", special_attack_chance=0.25, special_attack_name="Rattling Blow"),
    Monster("Mr. Frundles", 30, 30, 9, ["Parasitic Spore", "Mimic Essence", "Energy Cell"], "A highly infectious creature that spreads joy and horror simultaneously.", special_attack_chance=0.35, special_attack_name="Infectious Spread"),
    Monster(
        "Giant Head (Cromulon)", 35, 35, 10,
        ["Interdimensional Song", "Cosmic Dust", "Healing Serum"],
        "A massive, judgmental head demanding to know 'WHAT YOU GOT!'",
        special_attack_chance=0.3,
        special_attack_name="SHOW ME WHAT YOU GOT",
        is_boss=True
    ),
    Monster("Morty Jr.", 10, 10, 3, ["Gazorpian Genes", "Youthful Rage", "Energy Cell"], "A hot-headed Gazorpazorpian, prone to lashing out when provoked.", special_attack_chance=0.3, special_attack_name="Gazorpian Tantrum"),
    Monster("Tammy Gueterman", 22, 22, 7, ["Federation Agent ID", "Birdperson Feather", "Healing Serum"], "A ruthless Federation agent, and a tragic figure in love with Birdperson.", special_attack_chance=0.3, special_attack_name="Federation Charm"),
    Monster(
        "Mr. Nimbus", 28, 28, 8,
        ["Ocean's Trident", "King's Crown", "Energy Cell"],
        "He is Mr. Nimbus! He controls the police!",
        special_attack_chance=0.3,
        special_attack_name="Summon Police"
    ),
    Monster("Planetina's Minion", 16, 16, 5, ["Eco-Logic Circuit", "Elemental Shard", "Energy Cell"], "A small, environmentally-conscious but fierce defender of Planetina.", special_attack_chance=0.3, special_attack_name="Eco Lecture"),
    Monster("Butter Robot's Vengeance", 8, 8, 3, ["Butter Grease", "Existential Dread", "Healing Serum"], "A rogue Butter Robot, fueled by a purpose of pure spite.", special_attack_chance=0.3, special_attack_name="Existential Crisis"),
    Monster("Gotron Drone", 17, 17, 6, ["Gotron Component", "Mecha-Servo", "Energy Cell"], "A modular robot designed for combining into a giant mech, but still dangerous alone.", special_attack_chance=0.3, special_attack_name="Mecha Combine"),
    Monster("Unity (Possessed Host)", 28, 28, 8, ["Hive Mind Fragment", "Controlled Will", "Energy Cell"], "A member of Unity's collective, acting against its true will.", special_attack_chance=0.3, special_attack_name="Hive Assimilation"),
    Monster(
        "Fart (Cromulon Form)", 40, 40, 12,
        ["Gas Cloud Essence", "Telepathic Gem", "Energy Cell"],
        "A gaseous, telepathic being from another dimension, capable of mass destruction.",
        special_attack_chance=0.4,
        special_attack_name="Telepathic Assault",
        is_boss=True
    ),
    Monster("Conspiracy Morty", 20, 20, 6, ["Conspiracy Theory", "Tin Foil Hat", "Healing Serum"], "A Morty who knows too much, always muttering about the truth behind the Ricks.", special_attack_chance=0.3, special_attack_name="Tinfoil Rant"),
]
# ===== The hidden ambushers. =====
# Brand-new nasties from around the multiverse, none of them already in MONSTERS above, all of them
# the kind of thing that WOULD take a swing at me or Morty. I drop one of these in every time three
# enemies die. They never carry quest junk or craft parts, only Credits, and they leave no mark on the
# map. (name, base HP, base damage, the line you read right before it ruins your day.) HP sits in the
# same 8 to 30 band as the regular crowd. There are way more here than the cascade can ever spawn in
# one run, so you'll never see the same one twice in a game. Do the math, Morty, I did.
HIDDEN_ENEMIES = [
    ("Cronenberg Monster", 22, 7, "A lumpy, fleshy horror from a dimension I, uh, may have ruined. It's mad about it."),
    ("Krombopulos Michael", 12, 8, "A cheerful little assassin with zero moral hangups. 'Ooh boy, here I go killing again!'"),
    ("Gearhead", 17, 6, "A treacherous gear-faced merchant who'd absolutely stab you over a bad deal."),
    ("Eyehole Man", 15, 5, "He shows up the instant you touch an eyehole. 'YOU DON'T EAT MY EYEHOLES!'"),
    ("Abradolf Lincler", 27, 8, "My failed experiment in splicing Lincoln and Hitler. Morally conflicted, physically furious."),
    ("Million Ants", 25, 7, "A sentient swarm in a tasteful suit. Technically a billion now, but who's counting."),
    ("Heistotron", 23, 7, "A heist robot I built that won't stop planning heists, including a heist on you."),
    ("Memory Parasite", 20, 6, "A bug that worms into your memories pretending it's an old friend. It is not."),
    ("Pencilvester", 10, 4, "A pencil with a face and legs. Looks harmless. The parasites never are."),
    ("Hamurai", 18, 6, "Half ham, half samurai, all parasite. Slices first, asks for backstory never."),
    ("Photography Raptor", 16, 6, "A raptor that loves photography and lunging at faces. A real two-hobby guy."),
    ("Sleepy Gary", 17, 5, "Seems like a great husband from a life you never had. That's the parasite talking."),
    ("Zigerion Scammer", 14, 5, "A green con-artist from a simulation outfit, furious you keep seeing through the sims."),
    ("Glootie", 12, 4, "Has 'DO NOT DEVELOP MY APP' tattooed on his forehead. Develops chaos instead."),
    ("Glorzo", 14, 5, "An oil-loving alien from a soundstage planet. Very precious about its oil."),
    ("Cronenberg Hobo", 19, 6, "Another mistake from that dimension. Drifting, twitching, and looking right at you."),
    ("Purge Planet Native", 16, 6, "A villager who only gets one sanctioned murder night a year and is way behind quota."),
    ("Hamster-in-Butt Brute", 24, 7, "A tiny rider from Hamster in Butt World, weirdly buff, weirdly aggressive."),
    ("Antique Store Devil", 26, 8, "A smug shopkeep demon peddling cursed bargains. Refunds are violent."),
    ("Pancreas Pirate", 16, 6, "A microscopic buccaneer from inside somebody's Anatomy Park. Yarrr, etc."),
    ("Hepatitis A Hulk", 28, 8, "A towering disease-beast from the Anatomy Park outbreak. Wash your hands."),
    ("Bubonic Plague Cluster", 18, 6, "A creeping clump of medieval doom that escaped a tiny body theme park."),
    ("Federation Tax Auditor", 13, 5, "Worse than a Gromflomite soldier: this one has a clipboard and questions."),
    ("Scroopy Noopers", 10, 4, "A radicalized squanch-adjacent kid with a bomb-shaped grudge."),
    ("Rat-Suit Sentinel", 19, 6, "A sewer rat wearing a tiny powered exo-rig. I'd know, I built worse as a pickle."),
    ("Reverse Giraffe", 13, 4, "One of my drunk-invention rejects. All neck on the wrong end, all attitude."),
    ("Snowball's Hover-Sentinel", 20, 6, "A dog-built war drone. My houndmind's defense contract really got out of hand."),
    ("Gazorpian Reproborg", 21, 6, "A combat android from Gazorpazorp that just keeps reproducing more of itself."),
]
ACHIEVEMENTS = [
    Achievement("Dimension Hopper", "Complete all main quests", "Permanent Portal Fuel (Portal Jump has no charge cost)", "player.quest_idx >= len(EXTENDED_QUESTS)"),
    Achievement("Side Quest Morty", "Complete all side quests", "Morty Jr.'s Respect (+10% XP from all sources)", "len(player.subquest_ack) >= len(EXTENDED_SUBQUESTS)"),
    Achievement("Interdimensional Explorer", "Visit every room on the map", "+10 Max HP", "len(player.visited) >= total_rooms"),
    Achievement("Federation Fighter", "Defeat 15 monsters", "+5 Damage Bonus", "player.placed_monsters_defeated >= 15"),
    Achievement("Master Crafter Rick", "Craft 3 unique items", "New crafting recipes unlocked (all recipes become available)", "player.items_crafted >= 3"),
    Achievement("Galaxy Brain (C-137)", "Uncover every scrap of intel hidden across the dimensions", "+10 Max Charge", "len(player.lore_fragments) >= app.total_lore_fragments_count"),
    Achievement(
        "Collector of Oddities",
        "Collect 25 items",
        "Strange Hoarder’s Luck (+a bit more interesting loot overall).",
        "player.total_items_collected >= 25"
    ),
    Achievement("Schmeckle Millionaire", "Have 50 Federation Credits at once", "Permanent Price Reduction (gain 2 extra credits for every 10 credits found)", "player.federation_credits >= 50"),
    Achievement("Survived a Jerry", "Complete the game without dying", "Jerry-Proof Vest (+1 Armor)", "player.deaths == 0 and game_complete"),
    Achievement("Show Me What You Got!", "Defeat a Cromulon", "Cromulon's Blessing (gain 5 XP)", "cromulon_defeated_count >= 1"),
    Achievement("Plumbus Pro", "Collect a Plumbus", "Plumbus Mastery (Healing Serums heal for 5 more HP)", "player.plumbuses_collected >= 1 or 'Plumbus' in player.inventory or 'Plumbus' in player.crafting_materials or 'Plumbus Repair Kit' in player.inventory"),
    Achievement("Mega Seed Master", "Use 1 Mega Seed", "Enhanced Intelligence (+3 Max Charge)", "mega_seeds_used >= 1"),
]
CRAFTING_RECIPES = {
    # Every recipe wants exactly ONE unique side-quest reward piece, and you only pry those loose
    # by finishing the matching side quest. On top of that it wants materials that exist as a
    # single copy out on the map or stuffed in some enemy. So yeah, you actually have to
    # hunt the whole map AND do side quests to build anything. I don't do participation trophies.
    "Portal Gun (Replica)": {
        "materials": ["Confidence Capacitor", "Rickium Alloy", "Tiny Capacitor"],
        "effect": "Allows teleportation to any visited room (costs 5 Charge). Command: portal_jump <X> <Y>",
        "description": "A functional, albeit slightly unstable, replica of Rick's iconic device.",
        "key_piece": "Confidence Capacitor",
    },
    "Butter Robot": {
        "materials": ["Influencer Microchip", "Scavenged Parts", "Mind Thread"],
        "effect": "A loyal companion! +2 Damage Bonus while carried.",
        "description": "A small, subservient robot, whose sole purpose is to pass butter.",
        "key_piece": "Influencer Microchip",
    },
    "Interdimensional Goggles": {
        "materials": ["Surgical Nanite Vial", "Cognitive Fabric", "Neural Processor"],
        "effect": "Reveals all NPCs, Monsters, and Quest Motifs on the entire map.",
        "description": "See beyond the veil of your dimension, into infinite possibilities.",
        "key_piece": "Surgical Nanite Vial",
    },
    "Mega Seed Injector": {
        "materials": ["Nightmare Fuel Cell", "Mega Seed", "Tiny Capacitor"],
        "effect": "Permanently boosts Max Charge by 10, but causes temporary nausea (lose 5 HP).",
        "description": "A device to safely administer Mega Seeds for maximum intellectual gain.",
        "key_piece": "Nightmare Fuel Cell",
    },
    "Plumbus Repair Kit": {
        "materials": ["Lucky Charm Resonator", "Plumbus", "Scavenged Parts"],
        "effect": "Fully restores all HP and Charge (single use).",
        "description": "Everything you need to get your Plumbus back to optimal 'grumbo' status.",
        "key_piece": "Lucky Charm Resonator",
    },
}
# These are the materials that should exist as exactly one copy somewhere out there, floor or
# enemy loot. Side-quest reward pieces are NOT in here, the NPCs hand those out, keep up.
# I build this list by walking every recipe and dropping each non-key material once PER recipe that wants it,
# so a material two recipes share gets placed twice. That's the trick that makes all five craftable. *burp*
CRAFT_MATERIALS_SINGLE = [
    m for rdata in CRAFTING_RECIPES.values()
    for m in rdata["materials"] if m != rdata.get("key_piece")
]
# Reward pieces the side-quest NPCs hand you. I use these to gate crafting and fill the journal.
SIDE_REWARD_PIECES = [s["reward_item"] for s in EXTENDED_SUBQUESTS]
# The stage-one key items, each one dropped exactly once into the world.
SIDE_KEY_ITEMS = [s["key_item"] for s in EXTENDED_SUBQUESTS]

def _motif_verb(motif_idx):
    return EXTENDED_MOTIFS[motif_idx].get("interaction", "examine").split("_")[0]

def build_main_steps():
    """Flatten the chapters into an ordered list of 4 steps each:
    talk Rick -> deliver Rick's gadget to the chapter character -> retrieve the
    find-item via special action -> bring the find-item to Rick."""
    steps = []
    for ci, ch in enumerate(EXTENDED_QUESTS):
        steps.append(dict(kind="talk_rick", ci=ci))
        steps.append(dict(kind="deliver_char", ci=ci, item=ch["rick_gift"], to=ch["character"]))
        steps.append(dict(kind="retrieve", ci=ci, item=ch["item"], motif=ch["motif"]))
        steps.append(dict(kind="deliver_rick", ci=ci, item=ch["item"]))
    return steps

MAIN_STEPS = build_main_steps()
STEPS_PER_CHAPTER = 4
COMMAND_VERBS = [
    "north", "south", "east", "west", "n", "s", "e", "w",
    "talk", "hint", "quest", "look", "examine", "l",
    "get", "give", "use", "inventory", "inv", "i",
    "scan", "sense", "craft", "stats", "status", "search",
    "attack", "flee", "plasma_blast", "mind_wipe", "echo_scream", "show_me_what_you_got",
    "list", "buy", "sell",  # Shop commands. Buying and selling, the capitalist part.
    "eat", "observe", "play", "tinker", "negotiate", "listen",
    "scavenge", "haggle", "investigate", "call",
    "harvest", "order", "bribe", "connect",
    "watch", "bite", "workbench", "bench", "couch", "rummage", "loot", "barter", "deal", "inspect", "study", "probe", "analyze", "summon", "pick", "pluck", "drink", "sip", "payoff", "grease", "sync", "link",
    "map", "journal", "achievements", "portal_jump",
    "save", "load", "help",
]
# You type combat moves straight, no 'cast' nonsense. These aliases just let your sloppy
# friendly spellings through and snap them back to the real underscored command. You're welcome.
COMBAT_MOVES = ["plasma_blast", "mind_wipe", "echo_scream", "show_me_what_you_got"]
DIRECT_ALIAS = {
    "scream": "echo_scream", "echoscream": "echo_scream", "echo_scream": "echo_scream",
    "plasma": "plasma_blast", "plasmablast": "plasma_blast", "wrist_plasma": "plasma_blast", "blaster": "plasma_blast",
    "mindwipe": "mind_wipe", "mindblower": "mind_wipe", "mind_blower": "mind_wipe", "mind_pulse": "mind_wipe",
    "showmewhatyougot": "show_me_what_you_got",
}
DIFFICULTY_MODIFIERS = {
    # Cranked the whole ladder up a notch. Now that leveling doesn't hand you a free full heal,
    # the monsters get to actually mean it. Nightmare is brutal on purpose, but a good Morty can still win.
    DifficultyLevel.EASY: {"monster_hp_mult": 0.85, "monster_damage_mult": 0.9, "hint_clarity": 1.5, "starting_hp_bonus": 6, "starting_charge_bonus": 3},
    DifficultyLevel.NORMAL: {"monster_hp_mult": 1.15, "monster_damage_mult": 1.15, "hint_clarity": 1.0, "starting_hp_bonus": -2, "starting_charge_bonus": 0},
    DifficultyLevel.HARD: {"monster_hp_mult": 1.5, "monster_damage_mult": 1.4, "hint_clarity": 0.7, "starting_hp_bonus": -7, "starting_charge_bonus": -3},
    DifficultyLevel.NIGHTMARE: {"monster_hp_mult": 2.0, "monster_damage_mult": 1.65, "hint_clarity": 0.5, "starting_hp_bonus": -12, "starting_charge_bonus": -6}
}
ATTACK_COST = {
    "plasma_blast":         {"hp": 0, "charge": 4, "xp": 0},
    "mind_wipe":            {"hp": 0, "charge": 5, "xp": 0},
    "portal_jump":          {"hp": 0, "charge": 10, "xp": 0},
    "echo_scream":          {"hp": 2, "charge": 3, "xp": 0},
    "show_me_what_you_got": {"hp": 0, "charge": 7, "xp": 0},
}
# A basic swing always lands for at least this much, before any gear or level bonus. I set a floor
# so combat isn't you chipping away one measly point of damage a turn like some sad little gnat.
PLAYER_BASE_DAMAGE = 5
class NPC:
    def __init__(self, name, quest_idx, motif_idx, hand_to_giver, is_subquest=False, subqdata=None, is_rick=False, sub_idx=None, is_shop=False):
        self.name          = name
        self.quest_idx     = quest_idx
        self.motif_idx     = motif_idx
        self.hand_to_giver = hand_to_giver
        self.is_subquest   = is_subquest
        self.subqdata      = subqdata
        self.is_rick       = is_rick
        self.sub_idx       = sub_idx
        self.is_shop       = is_shop
class Player:
    def __init__(self, name=None, race=None, pclass=None, difficulty=DifficultyLevel.NORMAL):
        self.name       = name or "Morty"
        self.race       = race or "Force-Field Gauntlet"
        self.pclass     = pclass or "Holo-Mapper"
        self.difficulty = difficulty
        race_data  = next((r for r in EXPANDED_RACES if r["name"] == self.race),  EXPANDED_RACES[0])
        class_data = next((c for c in EXPANDED_CLASSES if c["name"] == self.pclass), EXPANDED_CLASSES[0])
        diff_mod  = DIFFICULTY_MODIFIERS[difficulty]
        base_hp   = 20 + random.randint(0, 5) + race_data["hp_bonus"] + class_data["hp_bonus"] + diff_mod["starting_hp_bonus"]
        base_charge = 15 + random.randint(0, 5) + race_data["charge_bonus"] + class_data["charge_bonus"] + diff_mod["starting_charge_bonus"]
        self.x, self.y   = 1, 1
        self.last_room   = (1, 1)
        self.inventory   = []
        self.crafting_materials = []
        self.shop_buyback = {}    # Stuff Morty pawned to Glexo. He'll sell it back at a markup, because regret has a price.
        self.quest_idx   = 0
        self.step_idx    = 0          # Index into MAIN_STEPS. Four steps per chapter. Count 'em, Morty.
        self.objective_shown = False  # I, Rick, lay out the grand objective exactly once. Listen the first time.
        self.quest_await = set()
        self.quest_heard  = set()
        self.subquest_heard = set()
        self.subquest_met   = set()
        self.await_item  = None
        self.await_motif = None
        self.await_verb  = None
        self.await_npc   = None
        self.subquest_ack = set()
        self.visited        = set()
        self.teleport_locations = {(1,1)}
        self.max_hp   = max(1, base_hp)
        self.hp       = self.max_hp
        self.charge     = max(1, base_charge)
        self.max_charge = self.charge
        self.xp    = 0
        self.level = 1
        self.moves_taken            = 0
        self.monsters_defeated      = 0   # TOTAL kills, placed AND hidden. This is the kill score you try to max out.
        self.monsters_killed        = 0
        self.placed_monsters_defeated = 0  # Only the enemies I planted at world-gen. THESE are the ones the achievement and 100 percent count.
        self.placed_enemy_count     = 0    # How many I planted at the start. Set the moment your game begins.
        self.max_total_kills        = 0    # The math ceiling: placed plus every hidden one the every-3-kills cascade can ever cough up.
        self.hidden_pool            = []   # Shuffled bag of brand-new creatures, drawn without repeats as hidden ones spawn.
        self.items_crafted          = 0
        self.crafted_recipes        = set()  # Every gadget Morty's actually built. I count these for the real ending. No faking it.
        self.true_ending_shown      = False  # Trips once Morty 100 percents everything. Then, and only then, am I impressed.
        self.motif_puzzles_solved   = 0
        self.lore_fragments         = []
        self.total_items_collected  = 0
        self.deaths                 = 0
        self.achievements           = []
        self.special_abilities      = []
        self.federation_credits     = 0
        self.cromulon_defeated_count = 0
        self.plumbuses_collected    = 0
        self.mega_seeds_used        = 0
        self.mega_seed_injector_built = False  # Flips on once I build the Injector. After that a Mega Seed's a usable item, not crafting junk.
        self.npc_chat_progress = {}  # How far I've let each NPC ramble at Morty before I sent him their way.
        self.npc_chat_last_end = {}  # Last brush-off each NPC used, so they quit repeating themselves like broken toys.
        self.chat_stage = {}      # How far Morty's gotten through each character's spiel. Not telling it to him twice.
        self.chat_lastcycle = {}  # Last cycling line per state so nobody repeats back to back. You're welcome.
        self.xp_bonus_percent       = 0
        self.current_combat_turn    = 0
        self.meeseeks_attack_doubled = False
        self.stunned_for_next_turn = False  # For stunning Mr. Nimbus. He runs the police, you know.
        # New combat statuses the monsters can lay on you. All of them tick DOWN and expire, on purpose,
        # so nothing locks you in a death spiral. Struggle, yes. Unwinnable, no.
        self.damage_debuff_turns = 0   # While > 0, your hits are weaker. Counts down each combat turn.
        self.dot_turns = 0             # Damage over time (poison/infection/etc). Ticks at turn start.
        self.dot_damage = 0            # How much the DoT does per tick.
        self.dot_label = ""            # Flavor name for whatever's eating you alive.
        self.stun_immune_next = False  # After a stun resolves, you shrug off the next one. No stun-locking.
        self.base_armor = 0
        self.base_damage_bonus = 0
        self.base_armor += race_data.get("armor_bonus", 0)
        self.base_damage_bonus += race_data.get("damage_bonus", 0)
        self.base_armor += class_data.get("armor_bonus", 0)
        self.base_damage_bonus += class_data.get("damage_bonus", 0)
        if self.race == "Recon Visor": self.base_armor += 1
        if self.race == "Laser Pistol": self.base_damage_bonus += 2
        if self.race == "Brainalyzer": self.base_armor += 1
        if self.pclass == "Targeting Chip": self.base_damage_bonus += 1; self.base_armor += 1
        if self.pclass == "Parasite Scanner": self.base_damage_bonus += 2
        if self.pclass == "Combat Exo-Rig": self.base_damage_bonus += 4
        self.item_armor_bonus = 0; self.item_damage_bonus = 0
        self.armor = self.base_armor + self.item_armor_bonus
        self.damage_bonus = self.base_damage_bonus + self.item_damage_bonus
        self.portal_gun_no_charge_cost = False; self.xp_bonus_active = False; self.plumbus_pro_active = False; self.unity_mind_shield_active = False
        if self.pclass == "Targeting Chip": self.xp_bonus_active = True; self.xp_bonus_percent += 100
        if self.pclass == "Portal Coil": self.portal_gun_no_charge_cost = True
        if self.race == "Recon Visor": self.special_abilities.append("Basic Room Scan")
        elif self.race == "Phoenix Implant": self.special_abilities.append("Passive HP Regen (1 HP / 5 moves)")
        elif self.race == "Brainalyzer": self.special_abilities.append("Disorient Enemy (10% chance to miss)")
        self.special_abilities.append(race_data["special"]); self.special_abilities.append(class_data["special"])
def make_spine(width, height, nodes):
    xs = [max(1, min(width, 1 + i * (width // max(1, nodes-1)))) for i in range(nodes)]
    ys = [max(1, min(height, 1 + i * (height // max(1, nodes-1)))) for i in range(nodes)]
    return list(dict.fromkeys(list(zip(xs, ys))))
def generate_enhanced_game(width, height, difficulty=DifficultyLevel.NORMAL,
                           quests=EXTENDED_QUESTS, motifs=EXTENDED_MOTIFS,
                           subquests=EXTENDED_SUBQUESTS):
    world = {}
    rooms = []
    starting_descriptions = [
        "A pocket dimension filled with colorful, bouncing goo-creatures.",
        "The infinite void between dimensions, strangely peaceful.",
        "A dilapidated alien diner, serving questionable interdimensional cuisine.",
        "A hallway in the Citadel of Ricks, plastered with propaganda posters.",
        "A forgotten corner of Blips and Chitz, smelling faintly of stale pizza.",
        "A toxic waste dump dimension, glowing with ominous green liquid.",
        "The interior of a giant alien's stomach, surprisingly spacious.",
        "A dimension where time flows backward.",
        "A sterile Galactic Federation outpost.",
        "A room filled with various, brightly colored test tubes and beakers.",
        "The inside of a colossal, living space whale.",
        "A cavern formed entirely from crystallized feelings and memories.",
        "A futuristic apartment complex.",
        "A dimension where everything is made of sentient, talking spaghetti.",
        "A desolate alien battlefield.",
        "A lush, overgrown jungle planet.",
        "The interior of a giant, bored Glarblon's mind.",
        "A dimension where gravity constantly shifts.",
        "A quiet, abandoned spaceship hangar.",
        "A bizarre art gallery.",
        "A bustling space station market.",
        "A room where sound itself takes on physical form.",
        "The interior of a giant, sentient crystal.",
        "A desolate asteroid field.",
        "A dimension entirely composed of fluffy, dangerous clouds.",
        "A futuristic classroom.",
        "A labyrinthine sewer system.",
        "A hidden bunker.",
        "A realm where every surface is a mirror.",
        "A dimension of pure silence.",
        "A giant vat of liquid.",
        "A waiting room in an interdimensional DMV.",
        "A 'Microverse Battery' floating endlessly.",
        "A dimension where all currency is sentient.",
        "A desolate planet, populated only by giant, depressed worms.",
        "The inside of a colossal, malfunctioning 'Meeseeks Box' factory.",
        "A museum of forgotten interdimensional technology.",
        "A planet where the trees grow upside down.",
        "A cosmic library where books float freely.",
        "A dimension made entirely of candy.",
        "A sterile operating theater.",
        "The headquarters of the 'Evil Morty Fan Club'.",
        "A giant game of interdimensional chess.",
        "A gas station on an alien highway.",
        "A dimension where every animal is a cat.",
        "A collection of abandoned 'Gotron' parts.",
        "A room filled with portals to other dimensions.",
        "The remnants of a failed 'Jerry Daycare' experiment.",
        "A factory producing 'Eyeholes'.",
        "A dimension where music is a physical force.",
        "An alien zoo.",
        "A giant, pulsating brain-like entity hums softly.",
        "A surreal landscape of floating islands.",
        "The interior of a living spaceship.",
        "A courtroom where the judge is a giant, angry pickle.",
        "A dimension where everything is tiny.",
        "A colossal, decaying space station.",
        "A bizarre carnival.",
        "A hidden laboratory.",
        "A dimension where every living being is a 'Mr. Poopybutthole'."
    ]
    for y in range(1, height + 1):
        for x in range(1, width + 1):
            world[(x, y)] = {
                "name": f"Room ({x},{y})",
                "desc": random.choice(starting_descriptions),
                "items": [],
                "npc": None,
                "monster": None,
                "quest_idx": None,
                "motif": None,
                "visited": False,
                "subquest_done": False,
                "lore_discovered": False,
                "special_interactions": [],
                "hidden_passages": [],
                "theme": None
            }
            rooms.append((x, y))
    used_rooms = {(1, 1)}
    # The Hub. Home base. Where I am.
    world[(1, 1)]["name"] = "Citadel Hub"
    world[(1, 1)]["desc"] = "The Citadel Hub: neon, noise, and a thousand arguments. Ricks and Mortys swarm the plaza."
    world[(1, 1)]["theme"] = "hub"
    glexo_pos = None  # The pawn shop's scattered out on the map somewhere, not bolted to the hub. Go find it.
    quest_rooms = []        # The rooms where the main-story special actions happen.
    quest_paths = []
    npc_rooms = []          # Every NPC tile. Me, the chapter characters, the side NPCs, Glexo, the whole circus.
    placed_main_npcs = {}   # Maps a name to a position. Name in, coordinates out.

    def m_dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def spread_pick(candidates, avoid, k):
        """Pick k well-separated rooms, far from each other and from the `avoid`
        anchors. Farthest-point sampling, but chooses randomly among the best
        options so layouts stay spread yet differ from game to game."""
        pool = list(candidates); refs = list(avoid); chosen = []
        for _ in range(k):
            if not pool:
                break
            scored = [(min((m_dist(p, r) for r in refs), default=10**9), p) for p in pool]
            best = max(s2 for s2, _ in scored)
            good = [p for s2, p in scored if s2 >= best * 0.75]
            pick = random.choice(good) if good else pool[0]
            chosen.append(pick); pool.remove(pick); refs.append(pick)
        return chosen

    # I live at the Citadel Hub, which is also where you start, so you can hit me up right away
    # and keep crawling back to me between chapters. Don't get clingy.
    world[(1, 1)]["npc"] = NPC("Rick C-137", -2, None, False, is_rick=True)
    world[(1, 1)]["desc"] += " Rick C-137 is here, hunched over a half-built contraption, muttering and drinking."
    npc_rooms.append((1, 1)); placed_main_npcs["Rick C-137"] = (1, 1)

    # All the special rooms (chapter characters, story rooms, side NPCs, side rooms, AND the pawn
    # shop) get dropped in one nicely-spread pass, then I assign their roles in a SHUFFLED order.
    # One pass keeps everything spread out and interleaved instead of clumped, and a clearance
    # ring keeps your starting area clear so you don't get jumped the second you spawn.
    SPAWN_CLEAR = 3  # Nothing spawns closer than this (Manhattan) to the hub. Breathing room.
    nq = len(quests); ns = len(subquests)
    special_candidates = [
        r for r in rooms
        if r not in used_rooms and world[r]["npc"] is None
        and m_dist(r, (1, 1)) >= SPAWN_CLEAR
    ]
    # That extra +1 slot on the end? Reserved for the pawn shop. Planned ahead, like a genius.
    special_positions = spread_pick(special_candidates, [(1, 1)], 2 * nq + 2 * ns + 1)
    glexo_pos = special_positions.pop() if special_positions else None
    random.shuffle(special_positions)
    # Deal the shuffled spread positions out across the four roles. Like cards, Morty.
    char_positions = special_positions[0:nq]
    motif_positions = special_positions[nq:2 * nq]
    sub_positions = special_positions[2 * nq:2 * nq + ns]
    side_motif_positions = special_positions[2 * nq + ns:2 * nq + 2 * ns]

    # The pawn shop, run by Glexo Slimslom, sits somewhere out in the multiverse, NOT glued
    # to your spawn square. Make him work for the foot traffic.
    if glexo_pos is not None:
        world[glexo_pos]["name"] = "The Pawn Shop at the End of Despair"
        world[glexo_pos]["desc"] = (
            "A grimy, cluttered stall is crammed into the alley. A four-eyed alien, Glexo Slimslom, "
            "polishes a blaster rifle with a greasy rag. He looks up, his gaze lingering on your pockets. "
            "The air smells of ozone and desperation."
        )
        world[glexo_pos]["npc"] = NPC(name="Glexo Slimslom", quest_idx=-1, motif_idx=None,
                                      hand_to_giver=False, is_subquest=True, is_shop=True)
        used_rooms.add(glexo_pos); npc_rooms.append(glexo_pos)

    # The chapter characters go here.
    for ci, Q in enumerate(quests):
        if ci >= len(char_positions): break
        pos = char_positions[ci]
        world[pos]["npc"] = NPC(Q["character"], ci, Q["motif"], False)
        world[pos]["desc"] += f" {Q['character']} is here."
        placed_main_npcs[Q["character"]] = pos
        npc_rooms.append(pos); used_rooms.add(pos)

    # The main-story special-action rooms.
    for ci, Q in enumerate(quests):
        if ci >= len(motif_positions): break
        pos = motif_positions[ci]; motif_idx = Q["motif"]; motif_data = motifs[motif_idx]
        world[pos]["desc"] = f"{Q['title']}: {motif_data['room']}"
        world[pos]["motif"] = motif_idx
        world[pos]["quest_idx"] = ci
        world[pos]["special_interactions"] = [motif_data.get("interaction", "examine")]
        if "hidden_lore" in motif_data:
            world[pos]["hidden_lore"] = motif_data["hidden_lore"]
        world[pos]["hidden_item"] = Q["item"]; world[pos]["quest_item_revealed"] = False
        quest_rooms.append(pos); used_rooms.add(pos)

    # The side-quest NPCs.
    sub_npc_rooms = []
    for si, sub in enumerate(subquests):
        if si >= len(sub_positions): break
        npc_pos = sub_positions[si]
        used_rooms.add(npc_pos); sub_npc_rooms.append(npc_pos)
        world[npc_pos]["npc"] = NPC(sub["npc"], -1, None, False, is_subquest=True, subqdata=sub, sub_idx=si)
        world[npc_pos]["desc"] += f" You see {sub['npc']} here, clearly in need of a favor."
        npc_rooms.append(npc_pos)

    # The side-quest special-action rooms. You bring the found KEY item here to produce the
    # item the NPC wants. I tag each with its side-quest index so nothing gets crossed up.
    for si, sub in enumerate(subquests):
        if si >= len(side_motif_positions): break
        pos = side_motif_positions[si]; motif_idx = sub["motif"]; motif_data = motifs[motif_idx]
        world[pos]["desc"] = f"{motif_data['room']}"
        world[pos]["motif"] = motif_idx
        world[pos]["side_idx"] = si
        world[pos]["special_interactions"] = [motif_data.get("interaction", "examine")]
        if "hidden_lore" in motif_data:
            world[pos]["hidden_lore"] = motif_data["hidden_lore"]
        used_rooms.add(pos)
    # ===== Dumping monsters onto the map. =====
    # I tune the density to the map size, roughly one monster per N rooms. A safe zone around the
    # hub stays monster-free so a fresh player can get their bearings before something eats them, and
    # I place bosses on purpose instead of sprinkling them like an idiot. Regular enemies lean
    # toward the weak end so the whole world isn't wall-to-wall heavy hitters. It's that
    # 80/20 weak-to-strong split every decent roguelike uses. I didn't invent it, I just do it right.
    diff_mod = DIFFICULTY_MODIFIERS[difficulty]
    total_rooms = width * height
    density = {
        DifficultyLevel.EASY: 9,
        DifficultyLevel.NORMAL: 7,
        DifficultyLevel.HARD: 5,
        DifficultyLevel.NIGHTMARE: 4,
    }[difficulty]
    monster_count = max(6, total_rooms // density)

    SAFE_RADIUS = 2  # Rooms within this Manhattan distance of the hub stay clear. Your safety bubble.
    placed_monsters = []
    monster_rooms = [
        pos for pos in rooms
        if pos not in quest_rooms
        and pos not in used_rooms
        and world[pos]["npc"] is None
        and world[pos]["motif"] is None
        and pos != glexo_pos
        and m_dist(pos, (1, 1)) > SAFE_RADIUS
    ]
    random.shuffle(monster_rooms)

    regular_monsters = [m for m in MONSTERS if not m.is_boss]
    boss_monsters = [m for m in MONSTERS if m.is_boss]
    # A weighted pool, so the weaker monsters (lower max HP) show up way *buuurp* more often.
    weights = [max(1, 40 - m.max_hp) for m in regular_monsters]

    def scale_monster(mon):
        # ===== BALANCE METRIC BASIS (the static numbers all tuning is measured against) =====
        # Player damage/turn: base 5 + level + gear (gadget/attachment add up to +4 dmg). Plasma blast ~2x,
        #   echo scream 2 strikes (then 1-turn cooldown).
        # Consumables, FIXED real values: Healing Serum = 10 HP (15 w/ Dark Matter Cell, +5 w/ Plumbus Pro);
        #   Energy Cell = 15 Charge (20 w/ Dark Matter Cell); Fleeb = 75; Plumbus Repair Kit = full HP+Charge.
        # Expected combat stock used for balancing a fight: ~4 Healing Serums and ~3 Energy Cells.
        # Tuned so: trash = warm-up, mid-tier elites = real fights, named bosses = hard, beat them with
        #   smart consumable use / a tanky loadout / the Repair Kit. Numbers below assume a GEARED Morty.
        spread = max(0.85, 1.0 + (mon.max_hp - 20) * 0.01)
        hp = int(mon.max_hp * 1.4 * spread * diff_mod["monster_hp_mult"])
        dmg = int(mon.damage * 1.3 * (1.0 + (spread - 1.0) * 0.5) * diff_mod["monster_damage_mult"])
        return Monster(
            mon.name,
            max(1, hp),
            max(1, hp),
            max(1, dmg),
            mon.loot.copy(),
            mon.description,
            mon.special_attack_chance,
            mon.special_attack_name,
            mon.is_boss,
        )

    for pos in monster_rooms:
        if len(placed_monsters) >= monster_count:
            break
        if any(m_dist(pos, m) < 2 for m in placed_monsters):
            continue  # Never park two monsters in rooms right next to each other. No gang ambushes.
        mon = random.choices(regular_monsters, weights=weights, k=1)[0]
        scaled = scale_monster(mon)
        world[pos]["monster"] = scaled
        world[pos]["desc"] += f" A {mon.name} lurks here. {mon.description}"
        placed_monsters.append(pos)
        used_rooms.add(pos)

    # I drop one or two bosses guarding the rooms next to the final quest motifs, so the
    # finale actually has some bite instead of being a cakewalk.
    if boss_monsters and quest_rooms:
        guard_targets = quest_rooms[-2:]
        # Distinct bosses, Cromulons dealt first, so at least one Cromulon ALWAYS exists, because the
        # 'Show Me What You Got' achievement needs one and I'm not leaving that to chance.
        boss_picks = random.sample(boss_monsters, min(len(guard_targets), len(boss_monsters)))
        boss_picks.sort(key=lambda mob: 0 if "Cromulon" in mob.name else 1)
        for i, target in enumerate(guard_targets):
            neighbours = [
                (target[0] + dx, target[1] + dy)
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                if (target[0] + dx, target[1] + dy) in world
                and world[(target[0] + dx, target[1] + dy)]["npc"] is None
                and world[(target[0] + dx, target[1] + dy)]["monster"] is None
                and world[(target[0] + dx, target[1] + dy)]["motif"] is None
                and (target[0] + dx, target[1] + dy) != glexo_pos
                and m_dist((target[0] + dx, target[1] + dy), (1, 1)) > SAFE_RADIUS
            ]
            if neighbours:
                bpos = random.choice(neighbours)
                boss = scale_monster(boss_picks[i % len(boss_picks)])
                world[bpos]["monster"] = boss
                world[bpos]["desc"] += f" A {boss.name} lurks here. {boss.description}"
                placed_monsters.append(bpos)
                used_rooms.add(bpos)
    # ===== Scattering the loot around. =====
    # Single-instance stuff: every side-quest KEY item and every crafting MATERIAL exists exactly
    # once, either on the floor or carried by one enemy. Side-quest REWARD pieces are NOT placed
    # here, the NPCs hand those out when you finish their quest, so every craft genuinely makes you
    # do a side quest AND hunt down materials. No freebies in my multiverse.
    monster_positions = list(placed_monsters)
    open_rooms = [
        r for r in rooms
        if r not in used_rooms and world[r]["npc"] is None
        and world[r]["monster"] is None and world[r].get("motif") is None
        and r != glexo_pos
    ]
    random.shuffle(open_rooms)
    item_positions = []  # floor rooms that already hold an item, for soft spacing

    def take_spread_room():
        # Still random, just nudged apart: most of the time I eyeball a few random
        # candidates and take whichever sits farthest from the nearest existing item,
        # so loot spreads out instead of bunching up. No grid, no checkerboard. And
        # about a third of the time I just grab a random one, so clusters can still happen.
        if not open_rooms:
            return None
        if item_positions and random.random() < 0.7:
            k = min(6, len(open_rooms))
            cands = random.sample(open_rooms, k)
            chosen = max(cands, key=lambda c: min(m_dist(c, p) for p in item_positions))
        else:
            chosen = random.choice(open_rooms)
        open_rooms.remove(chosen); item_positions.append(chosen)
        return chosen

    def place_single(item):
        # About a 35% shot I hang it on an existing enemy, so you gotta kill for it, otherwise it's on the floor.
        if monster_positions and random.random() < 0.35:
            mp = random.choice(monster_positions)
            world[mp]["monster"].loot.append(item)
            return
        pos = take_spread_room()
        if pos is not None:
            world[pos]["items"].append(item)
            world[pos]["desc"] += f" You notice {a_or_an(item)} {item} here."
            used_rooms.add(pos)

    for it in SIDE_KEY_ITEMS:
        place_single(it)
    for it in CRAFT_MATERIALS_SINGLE:
        place_single(it)

    # Consumables are allowed to repeat. Keeps exploring and fighting worth your while.
    consumables = ["Healing Serum", "Energy Cell", "Federation Credits"]
    n_consumable_rooms = max(8, len(open_rooms) // 4)
    for _ in range(n_consumable_rooms):
        pos = take_spread_room()
        if pos is None:
            break
        item = random.choice(consumables)
        world[pos]["items"].append(item)
        world[pos]["desc"] += f" You notice {a_or_an(item)} {item} here."
    total_lore_fragments_count = sum(1 for rm in world.values() if rm.get("hidden_lore"))
    return world, quest_paths, quest_rooms, npc_rooms, [Q["motif"] for Q in EXTENDED_QUESTS], 0, total_lore_fragments_count
# ===== Combat and achievement brains. The part that decides if you win or cry. =====
def check_achievements(player, world, app_instance=None):
    unlocked = []; total_rooms = len(world); game_complete = player.quest_idx >= len(EXTENDED_QUESTS)
    for ach in ACHIEVEMENTS:
        if ach.unlocked: continue
        try:
            local_scope = {
                "player": player, "total_rooms": total_rooms, "game_complete": game_complete,
                "cromulon_defeated_count": player.cromulon_defeated_count,
                "mega_seeds_used": player.mega_seeds_used,
                "EXTENDED_QUESTS": EXTENDED_QUESTS, "EXTENDED_SUBQUESTS": EXTENDED_SUBQUESTS,
            }
            if app_instance: local_scope["app"] = app_instance
            condition = ach.condition
            # I shove the module globals in here so any data names inside the conditions actually resolve. Plumbing.
            if eval(condition, globals(), local_scope):
                ach.unlocked = True; unlocked.append(ach)
                if app_instance:
                    app_instance.root.bell()
                    app_instance.append_colored(f"🏅 ACHIEVEMENT UNLOCKED: {ach.name}!\n", "achievement")
                    app_instance.append_colored(f"   Reward: {ach.reward}\n", "success")
                if ach.name == "Dimension Hopper": player.portal_gun_no_charge_cost = True
                elif ach.name == "Side Quest Morty": player.xp_bonus_active = True; player.xp_bonus_percent = 10
                elif ach.name == "Interdimensional Explorer": player.max_hp += 10; player.hp = min(player.hp+10, player.max_hp)
                elif ach.name == "Federation Fighter": player.base_damage_bonus += 5
                elif ach.name == "Galaxy Brain (C-137)": player.max_charge += 10; player.charge = player.max_charge
                elif ach.name == "Survived a Jerry": player.base_armor += 1
                elif ach.name == "Plumbus Pro": player.plumbus_pro_active = True
                elif ach.name == "Mega Seed Master": player.max_charge += 3; player.charge = min(player.charge+3, player.max_charge)
                if app_instance: app_instance._recalc_passives(); app_instance.update_info_display()
        except Exception as _ach_err:
            # A truly busted condition shouldn't crash the whole game, but I'm also not gonna
            # sweep it under the rug and pretend it's fine. Loud and non-fatal.
            import sys as _sys
            print(f"[achievement check] '{ach.name}' condition failed: {_ach_err}", file=_sys.stderr)
    if app_instance is not None and hasattr(app_instance, "_maybe_true_ending"):
        app_instance._maybe_true_ending()
    return unlocked
def craft_item(recipe_name, player_materials, player_class=None):
    if recipe_name not in CRAFTING_RECIPES: return False, "Unknown recipe", []
    recipe = CRAFTING_RECIPES[recipe_name]; required = recipe["materials"]
    temp = player_materials.copy()
    for m in required:
        if m in temp: temp.remove(m)
        else: return False, f"Missing {m}", []
    consumed = []
    if player_class == "Fabricator Drone" and random.random() < 0.25: return True, recipe, consumed
    for m in required: player_materials.remove(m); consumed.append(m)
    return True, recipe, consumed
# ===== The big game app class. This is the brain of the whole operation, Morty. =====
class EnhancedGameApp:
    
    def _rm_h(self, q): return f"{q.get('act','').strip()}: {q.get('title', q.get('item','')).strip()}".strip(": ")
    def _rm_verb(self, q): return EXTENDED_MOTIFS[q['motif']].get('interaction', 'examine').split('_')[0]
    def _rm_clue(self, q): return EXTENDED_MOTIFS[q['motif']].get('clue', '').strip()
    def _rm_npc_open(self, npc, q):
        v = self._rm_verb(q); c = self._rm_clue(q)
        if npc == "Rick C-137": return f"Rick burps. “Alright, {self.player.name}, {v} {c}, grab the thing, bring it back. It’s not rocket science. Well, it is, but just do it.”"
        if npc == "Birdperson": return f"Birdperson tilts his head. “{v.capitalize()} {c}. It would be appreciated.”"
        if npc == "President Morty": return f"Morty’s voice is calm and cold. “{v.capitalize()} {c}. Don’t make me repeat myself.”"
        return f"{npc} says, “{v.capitalize()} {c}. Then bring it.”"
    def _rm_npc_repeat(self, npc, q):
        v = self._rm_verb(q); c = self._rm_clue(q)
        if npc == "Rick C-137": return f"Rick sighs. “Still here? {v} {c}. Go.”"
        if npc == "Birdperson": return f"Birdperson is patient. “{v.capitalize()} {c}. Then return.”"
        if npc == "President Morty": return f"Morty doesn’t blink. “{v.capitalize()} {c}. Now.”"
        return f"{npc}: “{v.capitalize()} {c}.”"
    def _rm_have_item(self, npc, item):
        norm_item = self._normalize_text(item)
        if npc == "Rick C-137": return f"Rick eyes your pack. “You actually got the {item}? Hand it over. Type 'give {norm_item}'.”"
        if npc == "Birdperson": return f"Birdperson nods once. “You found the {item}. You may give it to me. 'give {norm_item}'.”"
        if npc == "President Morty": return f"Morty’s gaze lingers. “The {item}. Now. 'give {norm_item}'.”"
        return f"{npc} notices. “The {item}. Give it to me. 'give {norm_item}'.”"
    def _rm_gated(self, next_npc=None):
        if next_npc: return f"This would make sense if you’d talked to {next_npc}. It doesn’t. Yet."
        return "This doesn’t make sense yet. You’re missing context (and probably poor life choices)."
    def _rm_found(self, q, item):
        v = self._rm_verb(q)
        if v == "tinker": return q["retrieve_story"]
        if v == "scavenge": return q["retrieve_story"]
        if v == "eat": return q["retrieve_story"]
        if v == "observe": return q["retrieve_story"]
        if v == "investigate": return q["retrieve_story"]
        return f"You {v}. Now you have a {item}. Don’t overthink it."
    def _rm_completed(self, npc):
        if npc == "Rick C-137": return "Rick grunts approval. “Huh. Competent. Hate that.”"
        if npc == "Birdperson": return "Birdperson bows slightly. “This… helps.”"
        if npc == "President Morty": return "Morty smiles a smile that says ‘I planned this.’"
        return f"{npc} accepts your offering with minimal drama."
    def _rm_next_same(self, npc, nq):
        v = self._rm_verb(nq); c = self._rm_clue(nq)
        if npc == "Rick C-137": return f"Rick’s already onto the next problem. “{v.capitalize()} {c}. Next.”"
        return f"{npc}: “{v.capitalize()} {c}.”"
    def _normalize_text(self, s: str) -> str:
        s = s.lower(); s = re.sub(r"[^\w\s]", "", s); s = re.sub(r"\s+", " ", s).strip(); return s
    def _find_item_in_list(self, typed: str, options: list) -> str | None:
        if not options: return None
        t = self._normalize_text(typed); norm_map = {self._normalize_text(opt): opt for opt in options}
        if t in norm_map: return norm_map.get(t)
        for opt in options:
            n = self._normalize_text(opt)
            if t and (t in n or n in t): return opt
        return None
    def _is_plural(self, item_name: str) -> bool:
        token = item_name.strip().split()[-1].lower()
        known_plural = {"components", "credits", "goggles", "parts", "shards", "fragments", "ruins", "seeds", "cells", "notes", "scraps", "remains", "supplies", "wares", "chips", "circuits", "schematics"}
        exceptions_singular = {"glass", "gas", "class"}
        if token in known_plural: return True
        if token.endswith("s") and token not in exceptions_singular: return True
        return False
    def _np(self, item_name: str, definite: bool = False) -> str:
        if definite or self._is_plural(item_name): return f"the {item_name}"
        return f"{a_or_an(item_name)} {item_name}"
    def _pickup_phrase(self, item_name: str) -> str:
        if self._is_plural(item_name): return f"some {item_name}"
        return f"{a_or_an(item_name)} {item_name}"
    
    # ===== Feature 1: the shop. Where credits go to die. =====
    def _handle_shop_interaction(self, command, parts):
        shop_inventory = {
            "Healing Serum": 10,
            "Energy Cell": 15,
            "Rickium Alloy": 50,
            "Fleeb": 75,
            "Microverse Battery": 30,
            "Scavenged Parts": 5,
            "Mega Seed": 10,
        }
        main_quest_items = [q['item'] for q in EXTENDED_QUESTS] + [q['rick_gift'] for q in EXTENDED_QUESTS]
        
        if command == "talk":
            sc = SHOP_CHAT.get("Glexo Slimslom", {})
            if "talk" in sc: self._staged_chat("Glexo Slimslom:shop_talk", sc["talk"])
            else: self.append_colored("Glexo grunts. 'Whaddya want? See what I got with `list`, `buy <item>`, or `sell <item>` what you don't need. Don't waste my time.'\n", "lore")
            return
        
        if command == "list":
            self.append_colored("Glexo gestures to his wares. 'Best junk this side of the finite curve.'\n", "quest")
            for item, price in sorted(shop_inventory.items()):
                self.append_colored(f"  - {item}: {price} Credits\n")
            bb = getattr(self.player, "shop_buyback", None) or {}
            if bb:
                self.append_colored("Glexo jerks a thumb at a shelf of your old junk. 'Stuff you pawned. Want it back? It'll cost ya.'\n", "lore")
                for item in sorted(bb):
                    e = bb[item]; qty = f" x{e['qty']}" if e.get("qty", 1) > 1 else ""
                    self.append_colored(f"  - {item}: {e['price']} Credits{qty}\n")
            self.append_colored(f"You have {self.player.federation_credits} Credits.\n", "success")
            return
        
        if command == "buy":
            if len(parts) < 2: self.append_colored("Glexo rolls his eyes. 'Buy what, genius? `buy <item>`.'\n", "error"); self.root.bell(); return
            query = " ".join(parts[1:])
            item_name = self._find_item_in_list(query, list(shop_inventory.keys()))
            bb = getattr(self.player, "shop_buyback", None) or {}
            if not item_name:
                # Not in regular stock. Maybe it's something Morty pawned and now wants back.
                bb_name = self._find_item_in_list(query, list(bb.keys()))
                if bb_name:
                    price = bb[bb_name]["price"]
                    if self.player.federation_credits < price: self.append_colored(f"'Buyin' your own junk back is {price} Credits. You got {self.player.federation_credits}. Math, kid.'\n", "error"); self.root.bell(); return
                    self.player.federation_credits -= price
                    dest = bb[bb_name].get("dest", "materials")
                    (self.player.inventory if dest == "inventory" else self.player.crafting_materials).append(bb_name)
                    bb[bb_name]["qty"] -= 1
                    if bb[bb_name]["qty"] <= 0: del bb[bb_name]
                    self.append_colored(f"You bought back {self._np(bb_name)} for {price} Credits. Glexo smirks.\n", "success")
                    self.update_info_display(); self.root.bell()
                    return
                self.append_colored("'I ain't sellin' that. Check the list.'\n", "error"); self.root.bell(); return
            
            price = shop_inventory[item_name]
            if self.player.federation_credits < price: self.append_colored(f"'You think I'm running a charity? That's {price} Credits. You only got {self.player.federation_credits}. Get outta here.'\n", "error"); self.root.bell(); return
            
            self.player.federation_credits -= price
            
            if item_name in ["Healing Serum", "Energy Cell", "Fleeb"] or (item_name == "Mega Seed" and getattr(self.player, "mega_seed_injector_built", False)):
                self.player.inventory.append(item_name)
            else:
                self.player.crafting_materials.append(item_name)
                
            self.append_colored(f"You bought {self._np(item_name)} for {price} Credits.\n", "success")
            self.update_info_display(); self.root.bell()
            return
        
        if command == "sell":
            if len(parts) < 2: self.append_colored("'Sell what? Don't waste my time.'\n", "error"); self.root.bell(); return
            
            available_for_sale = self.player.inventory + self.player.crafting_materials
            item_to_sell = self._find_item_in_list(" ".join(parts[1:]), available_for_sale)
            
            side_quest_items = [s["key_item"] for s in EXTENDED_SUBQUESTS] + [s["need_item"] for s in EXTENDED_SUBQUESTS] + SIDE_REWARD_PIECES
            crafted_core_items = list(CRAFTING_RECIPES.keys())
            blocked_items = set(main_quest_items + side_quest_items + crafted_core_items)
            
            if item_to_sell in blocked_items: self.append_colored("'Are you crazy? That looks important. I'm not touching it. Too much heat.'\n", "error"); self.root.bell(); return
            if not item_to_sell: self.append_colored("'You don't have that, you idiot.'\n", "error"); self.root.bell(); return
            
            sell_price = shop_inventory.get(item_to_sell, 0) // 3 or 2

            if item_to_sell in self.player.inventory: self.player.inventory.remove(item_to_sell); dest = "inventory"
            elif item_to_sell in self.player.crafting_materials: self.player.crafting_materials.remove(item_to_sell); dest = "materials"
            else: dest = "materials"

            self.player.federation_credits += sell_price
            # It lands on Glexo's used shelf. Buy-back costs a little more than he paid Morty, because of course it does.
            if item_to_sell not in shop_inventory:
                if getattr(self.player, "shop_buyback", None) is None: self.player.shop_buyback = {}
                bb = self.player.shop_buyback
                buyback_price = sell_price + max(1, sell_price // 2)
                if item_to_sell in bb: bb[item_to_sell]["qty"] += 1; bb[item_to_sell]["price"] = buyback_price; bb[item_to_sell]["dest"] = dest
                else: bb[item_to_sell] = {"price": buyback_price, "qty": 1, "dest": dest}
            self.append_colored(f"You sold {item_to_sell} for {sell_price} Credits. Glexo barely looks up.\n", "success")
            self.update_info_display(); self.root.bell()
            return
            
    # ===== Feature 2: random events. The multiverse being weird for fun. =====
    def _trigger_random_event(self):
        # Rare just-for-laughs multiverse weirdness. It only fires in 'quiet' rooms, meaning
        # nothing else is going on (no NPC, quest, or monster), at a low chance, pulling from a big
        # pool so it never gets repetitive. And relax, nothing in here can ever actually kill you.
        if self._check_if_dead(): return
        room = self.world[(self.player.x, self.player.y)]
        if room.get("npc") or room.get("motif") or room.get("monster"): return
        if random.random() >= 0.05: return  # Roughly 5% per quiet move. Rare on purpose, Morty, don't expect fireworks every step.
        p = self.player
        flavor = [
            "A Mr. Meeseeks poofs in, shouts 'EXISTENCE IS PAIN!', and poofs back out before you can reply.",
            "A tiny Rick on a hoverboard zips past screaming about back taxes, then blinks out of reality.",
            "A portal opens, drops a half-eaten sandwich at your feet, and snaps shut. You leave it. Probably cursed.",
            "The floor briefly turns into writhing Cronenberg flesh, reconsiders, and goes back to being a floor.",
            "Two Jerrys shuffle past arguing about which one is the real Jerry. Neither is worth the trouble.",
            "You catch your reflection in a puddle. It winks at you. You did not wink.",
            "A Plumbus rolls by, beeps once in greeting, and continues about its day.",
            "Snowball trots past in a tailored power suit. He gives you a respectful nod. You nod back.",
            "Birdperson's voice echoes from nowhere: 'In Bird culture, this is considered a dick move.' You did nothing. Yet.",
            "A Gromflomite tourist asks you for directions to the Citadel, then wanders off before you can answer.",
            "A cosmic announcer booms 'GET SCHWIFTY!' across the dimension, then quietly mutters an apology.",
            "An empty Meeseeks box hums on the ground. You decide, wisely, not to press the button.",
            "Reality buffers for a second, like a stream catching up. Then everything's fine. Mostly.",
            "Squanchy waves at you from a passing interdimensional bus. At least you think it was Squanchy.",
            "A vending machine offers you 'Eyehole Man' cereal. You decline. It judges you silently.",
            "A wormhole burps somewhere nearby. It smells faintly of Szechuan sauce. You move on with your life.",
            "You hear faint applause from an audience that isn't there. The fourth wall feels thin today.",
            "A Gazorpian drone scans you, labels you 'NOT A THREAT', and flies off insultingly fast.",
        ]
        roll = random.random()
        if roll < 0.82:                                   # Mostly just harmless flavor. Window dressing.
            self.append_colored("🌀 " + random.choice(flavor) + "\n", "lore")
        elif roll < 0.90:                                 # A little lucky credit find. Pocket change.
            c = random.randint(1, 5); p.federation_credits += c
            self.append_colored(f"🪙 A pouch of {c} Federation Credits tumbles out of a closing portal. Finders keepers. (Total: {p.federation_credits})\n", "success")
            self.update_info_display()
        elif roll < 0.96 and p.hp < p.max_hp:             # A tiny heal, but only if you're actually hurt. No topping off at full.
            h = random.randint(1, 3); p.hp = min(p.max_hp, p.hp + h)
            self.append_colored(f"💚 A passing Meeseeks 'fixes your posture.' You feel oddly better. (+{h} HP)\n", "success")
            self.update_info_display()
        elif p.hp > 1:                                    # A harmless little mishap. It can NEVER knock you to zero. I'm not a monster. Mostly.
            p.hp -= 1
            self.append_colored("🤕 You stub your toe on an interdimensional pebble. HP -1. You're fine, walk it off.\n", "combat")
            self.update_info_display()
        else:                                             # At 1 HP it's pure flavor, zero risk. I'm not killing you with a gag.
            self.append_colored("🌀 " + random.choice(flavor) + "\n", "lore")
    def __init__(self, root):
        # A 12 by 12 grid. 144 rooms. Do the math, I already did.
        self.width, self.height = 12, 12
        self.root = root
        self.root.title(f"Rick and Morty - Multiverse Mayhem v{GAME_VERSION}")
        # Windows slaps the Python interpreter's icon on the TASKBAR by default because it lumps
        # our window in under pythonw.exe. So I declare our own AppUserModelID, which makes Windows
        # treat this like its own real application and finally show OUR icon in the taskbar.
        # The title-bar icon is a separate fight I handle below. Windows, am I right.
        try:
            if sys.platform.startswith("win"):
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"RickAndMorty.MultiverseMayhem.{GAME_VERSION}")
        except Exception:
            pass
        # I resolve the window icon once and hang onto it so every popup can reuse it.
        # Toplevel windows don't inherit the main window's icon, so without this little
        # stash the map, journal, all of 'em would show that generic Python feather. Gross.
        if hasattr(sys, "_MEIPASS"):
            self.icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if not os.path.exists(self.icon_path):
            self.icon_path = "icon.ico"
        # Setting it as the default means every Toplevel, current and future, just inherits it,
        # which together with that AppUserModelID up top is the combo that finally makes the
        # icon stick in the Windows taskbar. Took me two hacks. Worth it.
        try:
            if os.path.exists(self.icon_path):
                self.root.iconbitmap(default=self.icon_path)
        except Exception:
            pass
        self._apply_icon(self.root)
        self.root.geometry("1200x900+30+20")
        self.world = None; self.quest_paths = None; self.quest_rooms = None; self.npc_rooms = None; self.motifs_in_play = None
        self.player = None; self.difficulty = DifficultyLevel.NORMAL; self.map_popup = None; self._last_wait_line = None
        # Saves go in a 'saves' folder right next to the game (next to the .exe when it's frozen,
        # next to the .py otherwise) so they survive and you can actually find them. Logical.
        if getattr(sys, "frozen", False):
            _base = os.path.dirname(sys.executable)
        else:
            try: _base = os.path.dirname(os.path.abspath(__file__))
            except NameError: _base = os.getcwd()
        self.saves_dir = os.path.join(_base, "saves")
        try: os.makedirs(self.saves_dir, exist_ok=True)
        except Exception: self.saves_dir = os.path.join(os.getcwd(), "saves"); os.makedirs(self.saves_dir, exist_ok=True)
        self.current_save_name = None
        self.journal_popup = None; self.achievements_popup = None; self.crafting_popup = None; self.combat_in_progress = False
        self.total_lore_fragments_count = 0
        self.setup_interface()
        self.set_button_states(menu=True)
        self.show_main_menu()
        self.root.bind("<FocusIn>", self.on_window_focus); self.root.bind("<Button-1>", self.on_window_click)
        
    def _hard_exit(self):
        from tkinter import messagebox; import sys
        if not messagebox.askyesno("Quit Game", "Are you sure you want to quit?"): return
        self.root.quit(); self.root.destroy(); sys.exit(0)
    def setup_interface(self):
        main_frame = tk.Frame(self.root); main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = tk.Frame(main_frame); left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text = scrolledtext.ScrolledText(left_frame, width=80, height=30, font=("Cascadia Mono", 13), state='disabled', bg='#0a0a0f', fg='#AFFF94', wrap=tk.WORD); self.text.pack(fill=tk.BOTH, expand=True); self.text.bind("<Configure>", self._on_text_resize)
        self.text.tag_config("center", justify="center"); self.text.tag_config("quest", foreground="#FFD700"); self.text.tag_config("combat", foreground="#FF6B6B"); self.text.tag_config("achievement", foreground="#98D8E8")
        self.text.tag_config("lore", foreground="#DDD6FE"); self.text.tag_config("error", foreground="#FF4444"); self.text.tag_config("success", foreground="#4ADE80"); self.text.tag_config("banner", font=("Consolas", 28, "bold"), foreground="#FFD700", justify="center"); self.text.tag_config("intro_text", font=("Consolas", 11), foreground="#DDD6FE", justify="center")
        # Big, loud, bold alert for when a hidden ambusher jumps Morty out of an empty-looking room, so nobody's left going "wait, where did THAT come from?"
        # Same red as the rest of the combat text, just bold, and left-justified like everything else.
        self.text.tag_config("surprise", font=("Consolas", 16, "bold"), foreground="#FF6B6B")
        self.entry = tk.Entry(left_frame, width=80, font=("Consolas", 13), bg="#0a0a0f", fg="#FFFFFF", insertbackground="#FFFFFF", disabledbackground="#0a0a0f", disabledforeground="#FFFFFF"); self.entry.pack(fill=tk.X, pady=(5, 0))
        self.entry.bind("<Up>", self._entry_arrow_up); self.entry.bind("<Down>", self._entry_arrow_down); self.entry.bind("<Left>", self._entry_arrow_left); self.entry.bind("<Right>", self._entry_arrow_right)
        self._init_smart_completion(); self.entry.bind('<Return>', self.process_command); self.entry.config(state="disabled")
        right_frame = tk.Frame(main_frame, width=300); right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0)); right_frame.pack_propagate(False)
        action_frame = tk.LabelFrame(right_frame, text="Actions", font=("Arial", 10, "bold")); action_frame.pack(fill=tk.X, pady=(0, 10))
        self.buttons = {}; actions = [("Map", self.toggle_map, "map"), ("Journal", self.toggle_journal, "journal"), ("Achievements", self.toggle_achievements, "achievements"), ("Crafting", self.toggle_crafting, "crafting"), ("Hint", self.show_hint, "hint"), ("Scan", self.scan_room, "scan")]
        for i, (text, cmd, tag) in enumerate(actions):
            btn = tk.Button(action_frame, text=text, width=12, command=cmd); btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew"); self.buttons[tag] = btn
        action_frame.columnconfigure(0, weight=1); action_frame.columnconfigure(1, weight=1)
        control_frame = tk.LabelFrame(right_frame, text="Game", font=("Arial", 10, "bold")); control_frame.pack(fill=tk.X, pady=(0, 10))
        # 'New / Load Game' takes the left column, 'Save' and 'Quit' split the right. Tidy.
        _game_btn_font = ("Segoe UI", 9)
        newload = tk.Button(control_frame, text="New / Load Game", height=2, font=_game_btn_font, command=self.show_save_manager); newload.grid(row=0, column=0, padx=2, pady=2, sticky="ew"); self.buttons["new"] = newload; self.buttons["load"] = newload
        sq_frame = tk.Frame(control_frame); sq_frame.grid(row=0, column=1, padx=0, pady=0, sticky="ew")
        save_btn = tk.Button(sq_frame, text="Save", height=2, font=_game_btn_font, command=self.save_game); save_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew"); self.buttons["save"] = save_btn
        quit_btn = tk.Button(sq_frame, text="Quit", height=2, font=_game_btn_font, command=self._hard_exit); quit_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew"); self.buttons["quit"] = quit_btn
        sq_frame.columnconfigure(0, weight=1); sq_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(0, weight=1, uniform="gamerow"); control_frame.columnconfigure(1, weight=1, uniform="gamerow")
        self.root.protocol("WM_DELETE_WINDOW", self._hard_exit)
        self.info_frame = tk.LabelFrame(right_frame, text="Player Info", font=("Arial", 10, "bold")); self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.info_text = tk.Text(self.info_frame, height=21, width=30, font=("Consolas", 11), state='disabled', bg='#0a0a0f', fg='#AFFF94'); self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.tag_config("lbl", foreground="#AFFF94"); self.info_text.tag_config("val", foreground="#5EEAD4")
        self.minimap_frame = tk.LabelFrame(right_frame, text="Mini Map", font=("Arial", 10, "bold")); self.minimap_frame.pack(fill=tk.X)
        self.minimap_text = tk.Text(self.minimap_frame, height=12, width=30, font=("Consolas", 16), state='disabled', bg='#0a0a0f', fg='#888888'); self.minimap_text.pack(fill=tk.X, padx=5, pady=5)
        # The Player Info and Mini Map panels are read-only displays. Look, don't touch.
        # I rip out the default 'Text' class bindings so they ignore ALL your input: wheel,
        # click, and especially click-drag, which otherwise kicks off Tk's self-rescheduling
        # auto-scroll timer and slides the box around. I can still update them in code,
        # I just killed the user-event handling so you can't screw them up.
        for _w in (self.info_text, self.minimap_text):
            _w.bindtags(tuple(t for t in _w.bindtags() if t != "Text"))
        self.minimap_text.tag_config("legend", font=("Consolas", 12), foreground="#AFFF94")
    # ===== Tab-completion engine. So you don't have to type like an animal. =====
    def _init_smart_completion(self):
        self._tab = None  # The live Tab-cycle state, or None when you're not cycling.
        self.entry.bind("<Tab>", self._on_tab, add="+")
        self.entry.bind("<ISO_Left_Tab>", self._on_shift_tab, add="+")
        self.entry.bind("<Shift-Tab>", self._on_shift_tab, add="+")
        # Typing anything that isn't Tab or a modifier kills the current cycle, so the NEXT
        # Tab recomputes fresh from whatever's actually sitting in the box.
        self.entry.bind("<Key>", self._cancel_tab_cycle, add="+")
    # Verbs that expect a target after 'em. Complete one of these and I tack on a space
    # so you can immediately Tab again and cycle through the valid targets. Smooth.
    _ARG_VERBS = {"get", "give", "use", "craft", "buy", "sell", "look", "examine", "l", "portal_jump", "sense"}
    def _cancel_tab_cycle(self, event):
        if event.keysym not in ("Tab", "ISO_Left_Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            self._tab = None
    def _close_completion_popup(self):
        # No popup here. It's a harmless stub. Left it on purpose, don't delete it.
        self._tab = None
    def _on_tab(self, event):
        self._cycle_completion(1); return "break"
    def _on_shift_tab(self, event):
        self._cycle_completion(-1); return "break"
    def _cycle_completion(self, direction):
        if not getattr(self, "player", None) or not getattr(self, "world", None): return
        try: text = self.entry.get()
        except Exception: return
        try: caret = self.entry.index(tk.INSERT)
        except Exception: caret = len(text)
        st = self._tab
        if st and st.get("result_text") == text and st.get("result_caret") == caret and st.get("candidates"):
            st["index"] = (st["index"] + direction) % len(st["candidates"])  # Keep the cycle going.
        else:
            ctx = self._get_command_context(text, caret)
            cands = self._completion_candidates(ctx)
            if not cands:
                self._tab = None; return
            st = {"start": ctx["stem_start"], "candidates": cands,
                  "index": 0 if direction >= 0 else len(cands) - 1,
                  "arg0": (ctx["arg_index"] == 0)}
        cand = st["candidates"][st["index"]]
        self.entry.delete(st["start"], tk.END)  # The stem runs to the end of the line while you're completing.
        self.entry.insert(st["start"], cand)
        caret_after = st["start"] + len(cand)
        # A single top-level verb that takes a target, so I add a space and end the cycle,
        # and the next Tab starts cycling that verb's valid targets. Chain it, Morty.
        if st.get("arg0") and len(st["candidates"]) == 1 and cand in self._ARG_VERBS:
            self.entry.insert(caret_after, " "); caret_after += 1
            self.entry.icursor(caret_after); self._tab = None; return
        self.entry.icursor(caret_after)
        st["result_text"] = self.entry.get(); st["result_caret"] = caret_after
        self._tab = st
    def _completion_candidates(self, ctx):
        """Candidates relevant to this exact moment, narrowed by what's typed."""
        vocab = self._gather_vocab(ctx)
        stem = ctx["stem"].lower()
        if not stem:
            return list(vocab)
        starts = [v for v in vocab if v.lower().startswith(stem)]
        if starts: return starts
        return [v for v in vocab if stem in v.lower()]  # Fallback: just match on substring. Good enough.
    def _entry_arrow_up(self, event):
        self.move((0, -1)); return "break"
    def _entry_arrow_down(self, event):
        self.move((0, 1)); return "break"
    def _entry_arrow_left(self, event):
        self.move((-1, 0)); return "break"
    def _entry_arrow_right(self, event):
        self.move((1, 0)); return "break"
    def _get_command_context(self, text, caret_index):
        before = text[:caret_index]; parts = before.split()
        if before.endswith(" ") or not parts: stem = ""; stem_start = caret_index; stem_end = caret_index; arg_index = len(parts); tokens = parts[:]
        else: stem = parts[-1]; tokens = parts[:-1]; stem_start = caret_index - len(stem); stem_end = caret_index; arg_index = len(tokens)
        verb = (tokens[0].lower() if tokens else (stem.lower() if arg_index == 0 else ""))
        return {"tokens": tokens, "verb": verb, "arg_index": arg_index, "stem": stem, "stem_start": stem_start, "stem_end": stem_end, "full_text": text, "caret": caret_index,}
    def _gather_vocab(self, ctx):
        verb = ctx["verb"]; argi = ctx["arg_index"]
        if not getattr(self, "player", None) or not getattr(self, "world", None):
            return sorted(set(COMMAND_VERBS), key=lambda s: s.lower()) if argi == 0 else []
        p = self.player; pos = (p.x, p.y); room = self.world.get(pos, {}); inv_items = list(dict.fromkeys(p.inventory)); room_items = room.get("items", [])[:]; recipes = list(CRAFTING_RECIPES.keys())
        # Top level: I only offer the actions you can actually pull off RIGHT NOW. No teasing.
        if argi == 0:
            return self._relevant_actions()
        v = verb; shop_inventory_keys = ["Healing Serum", "Energy Cell", "Rickium Alloy", "Fleeb", "Microverse Battery", "Scavenged Parts", "Mega Seed"]
        # These verbs take a single, maybe multi-word, target. I only offer choices for the first
        # argument slot so a multi-word item can't get jammed back in on itself. Edge cases, ugh.
        if argi >= 2 and v not in ("portal_jump", "sense"):
            return []
        if v in ("get",): return sorted(set(room_items), key=lambda s: s.lower())
        if v in ("buy",): return sorted(set(shop_inventory_keys + list(getattr(p, "shop_buyback", None) or {})), key=lambda s: s.lower())
        if v in ("sell", "give"): return sorted(set(inv_items + p.crafting_materials), key=lambda s: s.lower())
        if v in ("use",):
            usable = ["Healing Serum", "Energy Cell"]; usable.extend(inv_items)
            for item in CRAFTING_RECIPES:
                if item in inv_items: usable.append(item)
            if "Energy Cell" in p.crafting_materials and "Energy Cell" not in usable: usable.append("Energy Cell")
            if "Mega Seed" in p.inventory and "Mega Seed" not in usable: usable.append("Mega Seed")
            return sorted(set(usable), key=lambda s: s.lower())
        if v in ("craft",):
            # Only the recipes you can build right this second, meaning you've got all the parts.
            buildable = [r for r, data in CRAFTING_RECIPES.items() if self._can_craft(data)]
            return sorted(buildable or recipes, key=lambda s: s.lower())
        if v in ("look", "examine", "l"):
            base_targets = ["room"]
            if room.get("npc"): base_targets.append("npc")
            if room.get("monster"): base_targets.append("enemy")
            if "hidden_lore" in room and not room.get("lore_discovered"): base_targets.append("lore")
            return sorted(set(base_targets + room_items), key=lambda s: s.lower())
        if v in ("portal_jump", "sense"):
            visited = sorted(getattr(p, "teleport_locations", [])); letters = [string.ascii_uppercase[i-1] for i in range(1, self.width+1)]
            if argi == 1:
                combo = [f"{string.ascii_uppercase[x-1]} {y}" for (x, y) in visited]; return sorted(set(letters + combo), key=lambda s: s.lower())
            elif argi == 2: return [str(y) for y in range(1, self.height+1)]
            else: return []
        return []
    def _can_craft(self, recipe_data):
        """True if the player currently holds every material a recipe needs."""
        from collections import Counter
        have = Counter(self.player.crafting_materials) + Counter(self.player.inventory)
        need = Counter(recipe_data["materials"])
        return all(have.get(m, 0) >= n for m, n in need.items())
    def _relevant_actions(self):
        """The commands that make sense at this exact moment, used so Tab only
        cycles through actions you can actually take here and now."""
        p = self.player
        if not p or not self.world: return sorted(COMMAND_VERBS, key=lambda s: s.lower())
        room = self.world.get((p.x, p.y), {})
        acts = set()
        # Always on the table: menus, info, the meta stuff.
        acts.update(["look", "examine", "inventory", "stats", "map", "journal",
                     "achievements", "hint", "quest", "help", "save", "load", "use"])
        if room.get("monster"):
            # Mid-fight I only show fight options. Movement's locked, you can't just stroll off.
            acts.update(["attack", "flee", "plasma_blast", "mind_wipe", "echo_scream"])
            if p.race == "Neutrino Bomb": acts.add("show_me_what_you_got")
        else:
            # Out of combat you're free to roam and poke at things.
            if p.y > 1: acts.add("north")
            if p.y < self.height: acts.add("south")
            if p.x < self.width: acts.add("east")
            if p.x > 1: acts.add("west")
            npc = room.get("npc")
            if npc and getattr(npc, "is_shop", False): acts.update(["talk", "list", "buy", "sell"])
            elif npc: acts.update(["talk", "give"])
            if room.get("items"): acts.add("get")
            for si in room.get("special_interactions", []): acts.add(si.split("_")[0])
            if "hidden_lore" in room and not room.get("lore_discovered"): acts.add("search")
            if p.crafting_materials: acts.add("craft")
            if "Portal Gun (Replica)" in p.inventory: acts.add("portal_jump")
            if p.race == "Recon Visor": acts.update(["scan", "sense"])
        return sorted(acts, key=lambda s: s.lower())
    def _longest_common_prefix(self, words):
        if not words: return ""
        s1 = min(words, key=str.lower); s2 = max(words, key=str.lower)
        i = 0; L = min(len(s1), len(s2))
        while i < L and s1[i].lower() == s2[i].lower(): i += 1
        return s1[:i]
    
    # ===== UI and game flow. The screens, the menus, the whole show. =====
    def append_centered(self, text, color_tag=None):
        self.text.config(state='normal'); lines = text.strip("\n").splitlines()
        for ln in lines: self.text.insert(tk.END, ln + "\n", ("center", color_tag) if color_tag else ("center",))
        self.text.see(tk.END); self.text.config(state='disabled')

    def _on_text_resize(self, event=None):
        # While the start menu's up, I re-center it every time the window resizes. Keeps it pretty.
        if not getattr(self, "_menu_active", False): return
        if getattr(self, "_recenter_job", None):
            try: self.root.after_cancel(self._recenter_job)
            except Exception: pass
        self._recenter_job = self.root.after(120, self._center_menu_vertically)

    def _center_menu_vertically(self, _attempt=0):
        # Tk Text hugs the top, so to center the splash vertically I pad the top with blank lines
        # equal to half the leftover space. If anything goes sideways it just no-ops. No harm done.
        if not getattr(self, "_menu_active", False): return
        try:
            self.text.update_idletasks()
            h = self.text.winfo_height()
            if h <= 1 and _attempt < 12:
                self.root.after(80, lambda: self._center_menu_vertically(_attempt + 1)); return
            self.text.config(state="normal")
            prev = getattr(self, "_vpad_lines", 0)
            if prev:
                self.text.delete("1.0", f"{prev + 1}.0"); self._vpad_lines = 0
            content_px = self.text.count("1.0", "end", "ypixels")
            if isinstance(content_px, (tuple, list)): content_px = content_px[0]
            import tkinter.font as tkfont
            line_px = tkfont.Font(font=self.text.cget("font")).metrics("linespace") or 18
            if content_px and h > content_px:
                pad = int((h - content_px) // 2 // line_px)
                if pad > 0:
                    self.text.insert("1.0", "\n" * pad); self._vpad_lines = pad
            self.text.yview_moveto(0.0); self.text.config(state="disabled")
        except Exception:
            try: self.text.config(state="disabled")
            except Exception: pass

    def append_colored(self, text, color_tag=None):
        self.text.config(state='normal')
        if color_tag:
            self.text.insert(tk.END, text, color_tag)
        else:
            self.text.insert(tk.END, text)
        self.text.see(tk.END)
        self.text.config(state='disabled')

    def _talk_separator(self):
        # Put a blank line before a new talk reply so successive replies don't run together,
        # BUT only if there's already text on screen. A freshly cleared screen starts clean,
        # no awkward leading gap. Also avoids stacking two blank lines if one's already there.
        # NOTE: Tk's Text.get always tacks on an extra trailing newline that isn't really in
        # the widget, so we drop exactly one trailing "\n" before inspecting.
        try:
            existing = self.text.get("1.0", "end-1c")
        except Exception:
            existing = ""
        if existing.strip() and not existing.endswith("\n\n"):
            self.append_colored("\n")

    def set_button_states(self, menu=False):
        self._menu_active = menu
        if hasattr(self, "_close_completion_popup"): self._close_completion_popup()
        for tag, btn in self.buttons.items():
            btn.config(state="normal" if not menu or tag in ["new", "load", "quit"] else "disabled")
        self.entry.config(state="disabled" if menu else "normal")
    def show_main_menu(self):
        self.set_button_states(menu=True); self.text.config(state="normal"); self.text.delete(1.0, tk.END)
        self.append_centered("RICK AND MORTY\n", "banner"); self.append_centered("🌟  Multiverse Mayhem! 🌟\n\n", "quest")
        splash = r"""
 ⠀⠀⠀⠀⠀  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⢀⣀⣤⣴⣾⠿⠿⠿⠿⠟⠿⠟⠛⠻⠿⠿⠿⢿⣿⣷⣶⣤⣀                      
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡤⠤⢤⣄⣀⢀⣤⣶⣿⣷⣽⣌⠙⠳⢭⣉⣁⢀⣀⣤⣤⣶⣶⣤⣤⣤⣄⡀⠀ ⢿⣿⡟⠻⢿⣷⣦⡀⠀                 
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣆⠀⠀⠉⠙⠾⣝⠿⣉⣠⣿⡀⠀⠀⠙⣟⢿⠋⢩⡉⡛⠛⠛⠛⠻⢿⣿⣦⡀⠀⠉⠀⠀⠀⠈⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀     
  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠸⡄⠀⠀⠀⠀⠈⠳⣝⢿⣼⠀⠀⠀⠀⠘⣟⣷⣺⢳⣹⣿⣷⣦⣤⣤⣬⣽⣿⣷⣤⡀⠀⠀⠀⠈⠛⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀        
  ⠀  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⠀⠀⠀⠀⠈⠻⠃⠀⠀⠀⠀⠀⠸⣮⠏⠀⢧⠉⠛⢿⣿⣿⣉⠉⠻⣿⣿⣿⣄⡀⠀ ⠀⠻⢿⣿⣶⣄⠀⠀⠀⠀⠀⠀⠀       
       ⠀⣀⣀⣀⣀⣀⣀⠤⡾⡇⠀⠀⠀⠀⠀⢀⣀⣠⠤⠤⠤⣄⣀⠀⠠⠏ ⢀⡇⠀⢀⠀⠘⠿⣧⠀⠻⣯⣙⠻⣿⣿⣶⣿⠆⠹⣏⠻⣿⣦⡀⠀⠀⠀⠀      
  ⠀⠀⠀⠉⠻⣍⠉⠀⠀⠀⠀⠀⠀⠀⠈⠉⠳⠃⠀⠀⢀⣤⠞⠋⠁⠀⠀⠀⠀⣀⡈⠳⣄⠀⠀⠀⢀⡇⠀⠀⠀⢀⠀⠘⠿⣧⠀⠻⣯⣙⠻⣿⣿⣄⠀⠈⠀⠈⠻⣿⣷⡄⠀      
 ⠀⠀⠀⠀⠀⠀⠙⠲⣄⠀⠀⠀⠀⠀⠀⠀⣰⠏⠀⢀⣠⠴⠒⠋⠉⢉⣉⣉⣉⣻⢷⡀⠀⢸⣅⣀⡤⢖⣯⣤⣤⣤⣄⠀⠀⠈⣿⣧⣈⠻⣿⣿⣄⠀⠈⠀⠈⠻⣿⣷⡄⠀     
 ⠀⠀⠀⠀⠀⠀⠀⠀⣾⢷⡀⠀⠀⠀⠀⣼⠁⣠⠞⢉⡤⠖⠚⠉⠉⠉⠉⠉⢀⣠⠬⢷⣄⠀⠀⠀⠀⣼⠙⢻⣿⣿⣿⣦⡀⠀⢻⣿⣿⣧⠈⢻⣿⣧⠀⣦⠀⠀⢿⣿⣿⠀     
 ⠀⠀⠀⠀⠀⠀⠀⢰⣿⣯⣇⠀⠀⠀⣰⠇⠀⠓⠊⠁⣠⣤⣤⣀⠀⠀⢀⡾⠋⠀⠀⠀⠈⢳⡀⠀⢠⠇⠀⠀⣧⣽⣿⣿⣿⡆⠀⠙⣿⡌⠁⢸⣷⡙⣦⣿⡷⠀⠈⢿⣿⠀     
 ⠀⠀⠀⣀⣀⢀⣠⣾⣛⣻⠼⠀⠀⠀⡿⠀⠀⢀⡴⠋⠀⠀⠀⠈⠳⡄⡾⠀⠀⢀⡤⠄⠀⠀⡇⠀⡞⠀⠀⡀⠈⠉⠉⣿⡿⠁⠀⠀⠻⠿⣦⡈⠙⣷⡘⢿⣄⠀⢰⣿⣿⠀     
  ⠀⠀⠀⠉⠻⣍⠉⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⡼⠀⠀⠀⡆⠀⠀⠀⢱⢳⠀⠀⠀⠀⠀⠀⢠⡇⠞⠓⠒⣺⠁⠀⠀⢰⡯⠖⠋⠉⠉⠉⠉⠉⠙⠓⠺⢽⡀⠙⣆⠈⣿⣿⡄        
 ⠀ ⠀⠀⠀⠀⠈⢳⣤⡀⠀⠀⠀⠀⠀⣇⠀⠀⢷⠀⠀⠀  ⠀⠀⢀⡾⠈⠳⡤⣄⣀⡠⠴⣻⠀⠀⠀⢠⠏⢀⡤⠞⠉⠀⠀⢀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠉⠳⣟⢰⣿⣿⣧        
 ⠀⠀⠀⠀⠀⠀⢸⣷⣭⢗⣤⡤⠄⠀⢸⡀⠀⢈⠳⣄⣀⣀⣠⡴⠋⠀⣄⠀⢳⠠⠤⠶⠚⢹⡙⠲⣤⠏⢀⡞⠀⢀⣠⠴⠾⠭⠥⢤⣀⠀⠈⠉⠙⠲⢤⡀⠀⠈⠳⡽⣿⣿     
 ⠀⠀⠀⠀⠀⠀⣼⣫⠞⠋⠀⠀⠀⠀⢘⣇⠀⠈⠓⠢⠤⠖⠚⠉⠀⠀⠘⣆⣈⡇⠀⠀⠀⠀⡇⣠⠇⢠⠎⠀⡴⠋⡥⠖⠋⠙⠒⢦⡀⠀⠀⠀⠀⢤⣀⡉⠳⡄⠀⢹⣹⡟     
 ⠀⠀⠀⠀⠀⠰⣟⣒⡦⢤⣀⠀⠀⢰⠟⢻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠀⠀⠀⠀⠀⡟⠁⢰⠃⢀⡞⠁⡼⠁⠀⠀⠀ ⠀⠀⠹⡄⠀⢀⣠⠤⠤⣍⡳⡝⡆⠀⢧⡇        
 ⠀⠀⠀⠀⠀⠀⣿⣿⣿⣦⠈⠛⣦⠘⣆⠈⣧⠀⠀⢠⢇⣀⡤⢴⡖⠛⠛⠛⠛⠲⢤⡀⣶⠐⡇⠀⢸⡀⡞⠀⢷⠀ ⠀⠛⠋ ⠀⢰⠇⣰⠋⠀⠀⠀⠀⠙⣆⢹⡀⢸⠀     
 ⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⠇⡼⠁⠀⠈⠉⢻⣧⠀⠘⢯⠙⡶⠋⠀⠀⠀⠀⠀⠀⠠⠞⠃⢠⡇⢀⡼⢻⠁⠀⠀⠈⠳⢤⣀⣀⣀⡴⠋⠀⡇⠀⠀⢠⣄⠀⠀⢸⠀⡇⢸⠀     
 ⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⡟⣼⣠⡴⢖⡚⠉⢿⣿⡳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡞⠀⢸⡀⢸⠀⠀⠀  ⠀⠀⠀⠀⠀⠠⣄⡘⣦⠹⣄⠀⠀⠉⠀⢀⡞⠀⡇⡾⠀       
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢷⣯⣾⣷⡈⢿⡄⠻⠿⢿⣮⡷⣄⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⠋⠀⠀⠀⠙⠺⡄⠀ ⠀⠀⣀⣤⠶⡶⠦⣌⡉⠉ ⠈⠙⠒⠒⠚⠉⠀⢸⢱⠇⠀        
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣾⣿⡄⠀⠀⠀⠈⠻⣿⣿⣷⣦⣤⣽⣿⣿⣷⣤⣤⣶⣶⣦⣤⡻⣄   ⠉⠉⠉⠻⣿⣿⣿⠀⠀⠀  ⠀⠀⣠⠏⢸⠀⠀⠀         
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣷⡦⠀⠀⠀⠈⠛⢿⣭⣝⡛⠛⠛⠻⠿⠿⠟⠛⠻⢿⣿⣮⣳⢦⣀⠀⠀⠀⠀⠈⠉⠁⠀  ⢀⣠⠞⠓⠒⠋⠀⠀⠀          
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⣿⣦⡀⠀⠀⣀⣀⠀⠙⢿⣿⣷⣶⣶⣶⣶⣤⣄⣤⣴⣿⣿⡿⠓⠋⠙⠒⠦⠤⠤⣴⣺⠏⠀⠀⠀⠀⠀⠀⠀⠀           
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⢿⣷⣤⣿⣿⣆⠀⠀⠈⠙⠛⠛⠛⠛⠛⠉⠉⠀⢀⣠⣤⣤⣴⣶⣿⣿⣿⣿⣿⠿⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀          
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠻⢿⣿⣿⣿⣿⣷⣤⣴⣿⣶⣾⣿⣷⣶⣿⣿⣿⣿⠿⠛⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀          
                
"""
        self.append_centered(splash, "achievement"); intro = ("Welcome to Rick and Morty: Multiverse Mayhem! Rick's got a problem, a half-built contraption, and a Morty-shaped errand boy: you. Explore the multiverse, run his jobs, fight weird monsters, craft ridiculous gadgets, and unlock absurd achievements.\n")
        self.append_centered("\n\n" + intro + "\n\n", "intro_text"); self.append_centered("Hit 'New / Load Game' to pick a universe or start a fresh one. Rick will explain the rest.\n")
        self.text.config(state="disabled"); self._vpad_lines = 0; self.root.after(60, self._center_menu_vertically)
    
    # ===== Player logic and combat helpers. Your guts, basically. =====
    def _q(self, s):
        """Swap the {pc} placeholder in quest/dialogue text for the player's chosen character name."""
        return s.replace("{pc}", self.player.name) if self.player else s
    def _check_if_dead(self) -> bool:
        if self.player and self.player.hp <= 0:
            self.append_colored("🩸 YOU ARE DEAD! Please load or start a new game.\n", "combat")
            self.entry.config(state="disabled")
            return True
        return False
        
    def _is_crafting_material(self, item_name):
        # ONE place decides what's a crafting material. A Mega Seed is a crafting ingredient ONLY until
        # the injector exists. After that it's a usable item, full stop, and nothing in the game gets to
        # call it crafting material again. This is the actual fix: stop classifying it as a part.
        if item_name == "Mega Seed" and "Mega Seed Injector" in self.player.inventory:
            return False
        return any(item_name in r["materials"] for r in CRAFTING_RECIPES.values())

    def _recalc_passives(self):
        if not self.player: return
        p = self.player; p.item_armor_bonus = 0; p.item_damage_bonus = 0; p.unity_mind_shield_active = False; p.plumbus_pro_active = False; p.portal_gun_no_charge_cost = False; p.xp_bonus_active = False; p.xp_bonus_percent = 0
        # THE global Mega Seed rule, runs on every recalc, no exceptions: if the injector is in your
        # inventory, then a Mega Seed belongs in your inventory, not the crafting parts. Move it. Always.
        if "Mega Seed Injector" in p.inventory:
            p.mega_seed_injector_built = True
            while "Mega Seed" in p.crafting_materials:
                p.crafting_materials.remove("Mega Seed"); p.inventory.append("Mega Seed")
        if "Unity's Mind Shield" in p.inventory: p.item_armor_bonus += 4; p.unity_mind_shield_active = True
        if "Butter Robot" in p.inventory: p.item_damage_bonus += 2
        if any(a.name == "Plumbus Pro" and a.unlocked for a in ACHIEVEMENTS): p.plumbus_pro_active = True
        if any(a.name == "Dimension Hopper" and a.unlocked for a in ACHIEVEMENTS): p.portal_gun_no_charge_cost = True
        if any(a.name == "Side Quest Morty" and a.unlocked for a in ACHIEVEMENTS): p.xp_bonus_active = True; p.xp_bonus_percent = 10
        if p.pclass == "Targeting Chip": p.xp_bonus_active = True; p.xp_bonus_percent += 100
        if p.pclass == "Portal Coil": p.portal_gun_no_charge_cost = True
        # Heads up: 'Survived a Jerry' grants +1 base_armor ONE time, over in check_achievements.
        # Do NOT re-apply it here or base_armor balloons by +1 on every recalc, and that runs on
        # damn near every action, so you'd end up with infinite armor. I caught that. You're welcome.
        p.armor = p.base_armor + p.item_armor_bonus; p.damage_bonus = p.base_damage_bonus + p.item_damage_bonus
    def grant_xp(self, amount: int, source: str = ""):
        if amount <= 0 or not self.player: return
        p = self.player
        if p.xp_bonus_active: amount = int(amount * (1 + p.xp_bonus_percent / 100))
        old_level = p.level; p.xp += amount
        # Escalating curve, Morty, not that flat "ding every kill" garbage from before. Each level
        # costs more than the last: cumulative XP for level N is 25*(N-1)*N. So L2 is 50, L3 is 150,
        # L5 is 500, L10 is 2250. You level fast early because that feels good, then it slows down so
        # by the back half you actually have to EARN it instead of tripping over a level every fight.
        lvl = 1
        while 25 * lvl * (lvl + 1) <= p.xp:
            lvl += 1
        p.level = lvl
        msg = f"🌀 You gain {amount} XP"
        if source: 
            msg += f"  ({source})"
        self.append_colored(msg + "\n", "success")
        if p.level > old_level:
            self.root.bell()
            inc = p.level - old_level; p.base_damage_bonus += inc; p.max_charge += 2 * inc; p.max_hp += 2 * inc
            # Leveling used to top you ALL the way off, HP and Charge both, which meant every kill
            # was a free spa day and you could mind-wipe/echo-scream forever without ever running dry.
            # Not anymore, Morty. You get a cut back, 35 percent of each bar, and you EARN the rest.
            heal_hp = max(1, int(p.max_hp * 0.35)); heal_charge = max(1, int(p.max_charge * 0.35))
            p.hp = min(p.max_hp, p.hp + heal_hp); p.charge = min(p.max_charge, p.charge + heal_charge)
            self._recalc_passives()
            self.append_colored(f"💫 Level UP! Now level {p.level}. Damage +{inc}, Max HP +{2*inc}, Max Charge +{2*inc}. Recovered {heal_hp} HP and {heal_charge} Charge.\n", "achievement")
        self.update_info_display(); check_achievements(self.player, self.world, self)
    def _consume_resources(self, charge=0, hp=0, xp=0) -> bool:
        p = self.player
        if p is None: return False
        if p.hp < hp or p.charge < charge or p.xp < xp:
            missing = []
            if p.hp < hp: missing.append(f"{hp} HP (have {p.hp})")
            if p.charge < charge: missing.append(f"{charge} Charge (have {p.charge})")
            if p.xp < xp: missing.append(f"{xp} XP (have {p.xp})")
            self.append_colored("❌ Not enough for that: needs " + ", ".join(missing) + ".\n", "error"); self.root.bell(); return False
        p.hp -= hp; p.charge -= charge; p.xp -= xp
        self.update_info_display(); return True
    def _comedic_whiff(self, move, room):
        """Use a combat move when there's NO enemy here. It's a dumb, funny flail:
        it still spends whatever the move normally costs, but it changes nothing in
        the world. No NPC is hurt, no item is destroyed, no quest/side-quest or
        story state moves. Purely comic relief. HP cost is clamped so attacking
        nothing can never actually kill you."""
        p = self.player
        cost = ATTACK_COST.get(move, {"hp": 0, "charge": 0, "xp": 0})
        charge_c = cost.get("charge", 0); xp_c = cost.get("xp", 0); hp_c = cost.get("hp", 0)
        # You still pay the Charge or XP this normally costs, and if you can't afford it,
        # you just don't get to do the dumb thing. Economics, Morty.
        if p.charge < charge_c or p.xp < xp_c:
            missing = []
            if p.charge < charge_c: missing.append(f"{charge_c} Charge (have {p.charge})")
            if p.xp < xp_c: missing.append(f"{xp_c} XP (have {p.xp})")
            self.append_colored("❌ You wind up for something incredibly stupid, then realize you can't afford it: needs " + ", ".join(missing) + ".\n", "error"); self.root.bell(); return
        p.charge -= charge_c; p.xp -= xp_c
        if hp_c: p.hp = max(1, p.hp - hp_c)   # Swinging at empty air won't kill you. Calm down, slugger.
        self.update_info_display()
        self.append_colored(self._whiff_line(move, room) + "\n", "combat")
        self.root.bell()

    def _whiff_line(self, move, room):
        weapon = {
            "attack": "take a wild swing",
            "plasma_blast": "fire off a plasma blast",
            "mind_wipe": "loose a mind-wipe pulse",
            "echo_scream": "rip out an echo scream",
            "show_me_what_you_got": "prime the Neutrino Bomb",
        }.get(move, "attack")
        npc = room.get("npc")
        if npc and getattr(npc, "is_rick", False):
            lines = [
                f"You {weapon} at Rick. He doesn't even look up from his flask. \"Swing at me again, {self.player.name}, and I'll reschedule your birthday to *never*.\"",
                f"You {weapon} at Rick. He burps, sidesteps, and keeps drinking. \"Bold. Stupid, but bold. Mostly stupid.\"",
                f"You {weapon} at the only guy who can portal you home. Rick stares. \"Real galaxy-brain move there, champ.\"",
            ]
        elif npc and getattr(npc, "is_shop", False):
            lines = [
                f"You {weapon} at Glexo. All four eyes narrow as he racks a blaster. \"Pull that again and I'll add YOU to the inventory. Bargain bin.\"",
                f"You {weapon} at the pawn stall. A 'YOU BREAK IT YOU BUY IT' sign clatters to the floor. Glexo just... waits.",
            ]
        elif npc and getattr(npc, "is_subquest", False):
            nm = npc.name
            lines = [
                f"You {weapon} at {nm}, who yelps, flinches, and is somehow completely fine. \"RUDE. I was gonna help you!\"",
                f"You {weapon} at {nm}. Absolutely nothing happens except a deeply disappointed look. Classic.",
            ]
        elif npc:
            nm = npc.name
            lines = [
                f"You {weapon} at {nm}. They saw it coming a mile away and aren't impressed. Not a scratch.",
                f"You {weapon} at {nm}. The universe flatly refuses to let plot-relevant characters die to your nonsense.",
            ]
        elif room.get("items"):
            itm = room["items"][0]
            lines = [
                f"You {weapon} at the {itm} lying on the ground. You miss by a mile. The {itm} sits there, judging you.",
                f"You {weapon} near the {itm}. Scorch marks everywhere, but the {itm} is, annoyingly, perfectly intact.",
            ]
        else:
            lines = [
                f"You {weapon} at absolutely nothing. The empty air takes it like a champ.",
                f"You {weapon} into the void. A distant voice mutters, 'THIS guy's the hero?' (Probably Rick.)",
                f"You {weapon} at the room itself. The room declines to press charges. For now.",
            ]
        return random.choice(lines)

    def _quip(self, kind, what=""):
        """A witty, Rick-and-Morty-flavored line for when an action does nothing,
        makes no sense, or is just plain dumb. Used so EVERY action gets a response
        instead of silence, and stupid ones get roasted."""
        what = (what or "").strip()
        pc = self.player.name if self.player else "you"
        banks = {
            "unknown": [
                f"\"{what}\"? That's not a command, {pc}, that's a cry for help. Type 'help' before you hurt yourself.",
                f"I-I don't even know what \"{what}\" is supposed to do, and I'm the smart one here. Try 'help'.",
                f"Rick crackles over the comms: \"'{what}'? Did you faceplant on the keyboard again? It's 'help', genius.\"",
                f"The multiverse has infinite valid commands. \"{what}\" is somehow not one of them. ('help' lists the real ones.)",
                f"Wow, \"{what}\". Bold word salad for someone who clearly can't read a help menu. Type 'help'.",
            ],
            "nothing_to_take": [
                f"There's nothing here to grab, {pc}. You're patting down an empty room like a confused raccoon.",
                "Take what, exactly? The floor? The crushing disappointment? There's nothing here.",
                "You reach for loot that doesn't exist. On brand, honestly.",
            ],
            "no_one": [
                f"There's nobody here, {pc}. You're talking to drywall. Again.",
                "Who are you even addressing? It's just you and your poor life choices in this room.",
                "Nobody's here. Striking up a conversation with empty space. Real galaxy-brain stuff.",
            ],
            "dont_have": [
                f"You don't have {what}, {pc}. You can't use what you don't own. That's, like, basic reality.",
                f"Check your pockets, genius: no {what} in there. Just lint and regret.",
                f"\"{what}\"? You don't have one. Try living in the same universe as your inventory.",
            ],
            "no_exit": [
                "You walk face-first into the edge of the map. The universe has a wall here and you found it. With your nose.",
                f"There's no exit that way, {pc}. That's just reality politely telling you 'no.'",
                "You can't go that way. There's literally nothing rendered over there, kind of like in your head.",
            ],
            "cant_craft": [
                f"You can't build {what}. You're missing parts, {pc}. A genius works with what he has. You work with... nothing.",
                f"Crafting {what} needs materials you don't have. Shocking development, truly.",
            ],
            "wrong_place": [
                f"You can't do that here, {pc}. Right idea, catastrophically wrong room.",
                "Nope. Not here. The one time you try something and it's in the wrong place entirely.",
            ],
        }
        return random.choice(banks.get(kind, banks["unknown"]))

    def _npc_quest_state(self, npc_name: str):
        cur = self.player.quest_idx; idxs = [i for i, q in enumerate(EXTENDED_QUESTS) if q['giver_npc'] == npc_name]
        if not idxs: return (None, None)
        if cur in idxs: return ("current", cur)
        past = [i for i in idxs if i < cur]
        if past: return ("past", max(past))
        future = [i for i in idxs if i > cur]
        if future: return ("future", min(future))
        return (None, None)
    
    def update_info_display(self):
        if not self.player: return
        self.info_text.config(state='normal'); self.info_text.delete(1.0, tk.END)
        p = self.player
        _sense = CLASS_SENSE.get(p.pclass)
        _sense_label = {"items": "Items (I)", "enemy": "Enemies (E)", "objective": "Quests/Shop (Q/$)", "main_npc": "Main NPCs (N)", "side_npc": "Side NPCs (S)"}
        radar = _sense_label.get(_sense[0], 'none') if _sense else 'none'
        def line(label, value):
            self.info_text.insert(tk.END, f"{label}: ", "lbl"); self.info_text.insert(tk.END, f"{value}\n", "val")
        def gap():
            self.info_text.insert(tk.END, "\n")
        line("Universe", self.current_save_name or "(none)"); line("Character", p.name); line("Main Gadget", p.race); line("Attachment", p.pclass)
        line("Radar", radar); line("Difficulty", p.difficulty.value.title())
        line("HP", f"{p.hp}/{p.max_hp}"); line("Charge", f"{p.charge}/{p.max_charge}"); line("XP", f"{p.xp}   (Level {p.level})")
        line("Armor", p.armor); line("Damage", f"+{p.damage_bonus}")
        gap()
        line("Position", f"({p.x}, {p.y})"); line("Quest", f"{p.quest_idx + 1}/{len(EXTENDED_QUESTS)}")
        line("Moves", p.moves_taken); line("Achievements", f"{len([a for a in ACHIEVEMENTS if a.unlocked])}/{len(ACHIEVEMENTS)}")
        gap()
        line("Items", len(p.inventory)); line("Materials", len(p.crafting_materials)); line("Intel", len(p.lore_fragments)); line("Federation Credits", p.federation_credits)
        self.info_text.config(state='disabled')
    def _sensed(self, x, y, room):
        """If the player's class radar detects this UNVISITED room's category and
        it's within range, return (symbol, dim_tag) so the map can draw a faint
        'detected' marker. Otherwise None (room stays '?')."""
        if not self.player: return None
        sense = CLASS_SENSE.get(self.player.pclass)
        if not sense: return None
        category, radius = sense
        if abs(x - self.player.x) + abs(y - self.player.y) > radius: return None
        npc = room.get("npc")
        if category == "items" and room.get("items"): return ("[I]", "dim_item")
        if category == "enemy" and room.get("monster"): return ("[E]", "dim_monster")
        if category == "main_npc" and npc and not getattr(npc, "is_subquest", False) and not getattr(npc, "is_shop", False):
            return ("[N]", "dim_npc")
        if category == "side_npc" and npc and getattr(npc, "is_subquest", False):
            return ("[S]", "dim_subnpc")
        if category == "objective":
            if npc and getattr(npc, "is_shop", False): return ("[$]", "dim_shop")
            if room.get("motif") is not None:
                solved = (room.get("subquest_done") or (room.get("quest_idx") is not None and room["quest_idx"] < self.player.quest_idx))
                if not solved: return ("[Q]", "dim_quest")
        return None
    def update_enhanced_map(self):
        if not (hasattr(self, "map_popup") and self.map_popup and hasattr(self, "map_text_widget") and self.map_text_widget and self.map_popup.winfo_exists()): return
        letters = string.ascii_uppercase; cellw = 3
        self.map_text_widget.configure(state="normal"); self.map_text_widget.delete(1.0, tk.END)
        tag_colors = {"map_player": "#FFFFFF", "map_monster": "#FF6B6B", "map_npc": "#FFD700", "map_shop": "#FFA500", "map_subnpc": "#40C4FF", "map_item": "#E67BFF", "map_quest": "#4ADE80", "map_intel": "#2A4DAE", "map_empty": "#888888", "map_monwarn": "#C40202", "map_questwarn": "#019644", "map_subwarn": "#019644", "map_unknown": "#555555", **DIM_SENSE_COLORS}
        for tag, col in tag_colors.items(): self.map_text_widget.tag_config(tag, foreground=col)
        self.map_text_widget.insert(tk.END, "   ");
        for x in range(1, self.width + 1): self.map_text_widget.insert(tk.END, f"{letters[x-1]}".center(cellw), ("map_empty",))
        self.map_text_widget.insert(tk.END, "\n")
        for y in range(1, self.height + 1):
            self.map_text_widget.insert(tk.END, f"{y:<2} ", ("map_empty",))
            for x in range(1, self.width + 1):
                room = self.world[(x, y)]; symbol, tag = "[ ]", "map_empty"
                if (x, y) == (self.player.x, self.player.y): symbol, tag = "[@]", "map_player"
                elif room.get("theme") == "hub" and (x, y) == (1, 1): symbol, tag = "[H]", "map_npc"
                elif not room.get("visited"):
                    sensed = self._sensed(x, y, room)
                    symbol, tag = sensed if sensed else ("[?]", "map_unknown")
                elif room.get("monster") and not getattr(room["monster"], "hidden", False): symbol, tag = "[E]", "map_monster"
                elif room.get("npc"):
                    _n = room["npc"]
                    if getattr(_n, "is_shop", False): symbol, tag = "[$]", "map_shop"
                    elif getattr(_n, "is_subquest", False): symbol, tag = "[S]", "map_subnpc"
                    else: symbol, tag = "[N]", "map_npc"
                elif room.get("items"): symbol, tag = "[I]", "map_item"
                elif room.get("motif") is not None:
                    solved = (room.get("subquest_done") or (room.get("quest_idx") is not None and room["quest_idx"] < self.player.quest_idx))
                    if not solved: symbol, tag = "[Q]", "map_quest"
                    elif room.get("hidden_lore") and not room.get("lore_discovered"): symbol, tag = "[!]", "map_intel"
                    else: symbol, tag = "[ ]", "map_empty"
                if tag == "map_intel":
                    self.map_text_widget.insert(tk.END, "[", "map_empty"); self.map_text_widget.insert(tk.END, "!", "map_intel"); self.map_text_widget.insert(tk.END, "]", "map_empty")
                else:
                    self.map_text_widget.insert(tk.END, symbol, tag)
            self.map_text_widget.insert(tk.END, "\n")
        _W = 20
        _pairs = [("@ = You", "I = Items (or Credits)"),
                  ("E = Enemy", "N = Main Quest NPC"),
                  ("S = Side Quest NPC", "Q = Quest Room"),
                  ("$ = Pawn Shop", "H = Citadel Hub")]
        legend = "\nLEGEND:\n" + "".join(l.ljust(_W) + r + "\n" for l, r in _pairs)
        legend += "? = Unseen Dimension\n"
        self.map_text_widget.tag_config("map_legend", font=("Consolas", 15))
        self.map_text_widget.insert(tk.END, legend, "map_legend"); self.map_text_widget.configure(state="disabled")
    def show_enhanced_map(self):
        if self._check_if_dead(): return
        if not self.player: self.append_colored("Start a game to view the map!\n", "error"); return
        if self.map_popup and self.map_popup.winfo_exists():
            self.update_enhanced_map()
            try:
                self.map_popup.deiconify(); self.map_popup.lift(); self.map_popup.focus_force()
                # I briefly flag it topmost so it pops above the main window on Windows, then immediately
                # let go of topmost so other popups can still come to the front later. In and out.
                self.map_popup.attributes("-topmost", True)
                self.map_popup.after(400, lambda: self.map_popup.winfo_exists() and self.map_popup.attributes("-topmost", False))
            except Exception:
                pass
            return
        self.map_popup = tk.Toplevel(self.root); self.map_popup.title("Cosmic Navigation Map"); self.map_popup.resizable(False, False); self._apply_icon(self.map_popup)
        self.map_text_widget = tk.Text(self.map_popup, font=("Consolas", 16), bg="#0a0a0f", fg="#AFFF94", wrap="none", width=self.width*3+4, height=self.height+9, state='disabled', borderwidth=0, highlightthickness=0)
        tag_colors = {"map_player": "#AFFF94", "map_monster": "#FF6B6B", "map_npc": "#FFD700", "map_shop": "#FFA500", "map_subnpc": "#40C4FF", "map_item": "#E67BFF", "map_quest": "#4ADE80", "map_empty": "#888888", "mini_monwarn": "#C40202", "mini_questwarn": "#019644", "mini_subwarn": "#019644", "map_unknown": "#555555",}
        for tag, col in tag_colors.items(): self.map_text_widget.tag_config(tag, foreground=col)
        self.map_text_widget.pack(padx=10, pady=10); self.map_popup.update_idletasks()
        _mw = self.map_text_widget.winfo_reqwidth() + 20; _mh = self.map_text_widget.winfo_reqheight() + 40
        self.map_popup.geometry(f"{_mw}x{_mh}")
        try:
            self.map_popup.lift(); self.map_popup.focus_force()
            self.map_popup.attributes("-topmost", True)
            self.map_popup.after(400, lambda: self.map_popup and self.map_popup.winfo_exists() and self.map_popup.attributes("-topmost", False))
        except Exception:
            self.map_popup.focus_set()
        def _map_move(delta): self.move(delta); return "break"
        self.map_popup.bind("<Up>", lambda e: _map_move((0, -1))); self.map_popup.bind("<Down>", lambda e: _map_move((0, 1))); self.map_popup.bind("<Left>", lambda e: _map_move((-1, 0))); self.map_popup.bind("<Right>", lambda e: _map_move((1, 0)))
        def _forward_key(event):
            if event.char: self.entry.insert(tk.END, event.char); self.entry.focus_set(); return "break"
        self.map_popup.bind("<Key>", _forward_key); self.map_popup.bind("<Button-1>", lambda e: self.map_popup.focus_set())
        self.update_enhanced_map()
        # Final placement: 20px down from the top, right edge 20px in from the screen's right.
        # Two passes: first I place it using the size I set, then I MEASURE where the window's
        # right edge actually landed, frame borders and all, and nudge it so it sits exactly 20px in.
        # I do this dead last, once the window's fully realized, or the numbers lie to me.
        try:
            self.map_popup.update_idletasks()
            sw = self.map_popup.winfo_screenwidth()
            x = max(0, sw - _mw - 40)
            self.map_popup.geometry(f"+{x}+20")
            self.map_popup.update_idletasks()
            right = self.map_popup.winfo_rootx() + self.map_popup.winfo_width()
            err = (sw - 40) - right
            if abs(err) > 2:
                x = max(0, x + err)
                self.map_popup.geometry(f"+{x}+20")
        except Exception:
            self.map_popup.geometry("+900+20")
        def close_map(): self.map_popup.destroy(); self.map_popup = None; self.map_text_widget = None; self.entry.focus_set()
        self.map_popup.protocol("WM_DELETE_WINDOW", close_map)
    def update_minimap(self):
        if not self.player or not self.world: return
        self.minimap_text.config(state="normal"); self.minimap_text.delete(1.0, tk.END)
        tags = {"mini_player": "#FFFFFF", "mini_monster": "#FF6B6B", "mini_npc": "#FFD700", "mini_shop": "#FFA500", "mini_subnpc": "#40C4FF", "mini_item": "#E67BFF", "mini_quest": "#4ADE80", "mini_intel": "#2A4DAE", "mini_empty": "#888888", "mini_unknown": "#555555", **DIM_SENSE_COLORS}
        for tag, col in tags.items(): self.minimap_text.tag_config(tag, foreground=col)
        px, py = self.player.x, self.player.y; start_x = max(1, px - 2); start_y = max(1, py - 2)
        end_x = min(self.width, start_x + 4); end_y = min(self.height, start_y + 4)
        self.minimap_text.insert(tk.END, "   ", ("mini_empty",));
        for x in range(start_x, end_x + 1): self.minimap_text.insert(tk.END, f"{string.ascii_uppercase[x-1]}".center(3), ("mini_empty",))
        self.minimap_text.insert(tk.END, "\n")
        for y in range(start_y, end_y + 1):
            self.minimap_text.insert(tk.END, f"{y:<2} ", ("mini_empty",))
            for x in range(start_x, end_x + 1):
                room = self.world.get((x, y), {"visited": False}); symbol, tag = "[ ]", "mini_empty"
                if (x, y) == (px, py): symbol, tag = "[@]", "mini_player"
                elif room.get("theme") == "hub" and (x, y) == (1, 1): symbol, tag = "[H]", "mini_npc"
                elif not room.get("visited"):
                    sensed = self._sensed(x, y, room)
                    symbol, tag = sensed if sensed else ("[?]", "mini_unknown")
                elif room.get("monster") and not getattr(room["monster"], "hidden", False): symbol, tag = "[E]", "mini_monster"
                elif room.get("npc"):
                    _n = room["npc"]
                    if getattr(_n, "is_shop", False): symbol, tag = "[$]", "mini_shop"
                    elif getattr(_n, "is_subquest", False): symbol, tag = "[S]", "mini_subnpc"
                    else: symbol, tag = "[N]", "mini_npc"
                elif room.get("items"): symbol, tag = "[I]", "mini_item"
                elif room.get("motif") is not None:
                    solved = (room.get("subquest_done") or (room.get("quest_idx") is not None and room["quest_idx"] < self.player.quest_idx))
                    if not solved: symbol, tag = "[Q]", "mini_quest"
                    elif room.get("hidden_lore") and not room.get("lore_discovered"): symbol, tag = "[!]", "mini_intel"
                    else: symbol, tag = "[ ]", "mini_empty"
                if tag == "mini_intel":
                    self.minimap_text.insert(tk.END, "[", "mini_empty"); self.minimap_text.insert(tk.END, "!", "mini_intel"); self.minimap_text.insert(tk.END, "]", "mini_empty")
                else:
                    self.minimap_text.insert(tk.END, symbol, tag)
            self.minimap_text.insert(tk.END, "\n")
        self.minimap_text.insert(
            tk.END, "\nLEGEND:\n@ = You        S = Side-NPC\nE = Enemy      I = Items\nN = Main-NPC   Q = Quest-Room\n$ = Pawn Shop  ? = Unseen\nH = Citadel Hub  [ ] = Empty", ("legend",)); self.minimap_text.config(state="disabled")
    def toggle_crafting(self):
        if self._check_if_dead(): return
        if not self.player: self.append_colored("Start a game to craft!\n", "error"); return
        if getattr(self, 'crafting_popup', None) and self.crafting_popup and self.crafting_popup.winfo_exists(): self.crafting_popup.deiconify(); self.crafting_popup.lift(); self.crafting_popup.focus_force(); return
        self.crafting_popup = tk.Toplevel(self.root); self.crafting_popup.title("Crafting Panel"); self._center_popup(self.crafting_popup, 400, 500); self.crafting_popup.minsize(380, 440); self._apply_icon(self.crafting_popup)
        tk.Label(self.crafting_popup, text="Available Recipes:", font=("Arial", 12, "bold")).pack(pady=(8, 4))
        listbox = tk.Listbox(self.crafting_popup, font=("Consolas", 10), width=40, height=6)
        for rec_name in CRAFTING_RECIPES: listbox.insert(tk.END, rec_name)
        listbox.pack(pady=(2, 4))
        info_label = tk.Label(self.crafting_popup, text="← select a recipe", justify="left", anchor="nw", wraplength=360); info_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))
        def show_recipe_info(event=None):
            sel = listbox.curselection();
            if not sel: info_label.config(text="← select a recipe"); return
            name = listbox.get(sel[0]); data = CRAFTING_RECIPES[name]
            info = ("Materials:\n  - " + "\n  - ".join(data["materials"]) + f"\n\nEffect: {data['effect']}\n\nDescription: {data['description']}")
            info_label.config(text=info)
        listbox.bind("<<ListboxSelect>>", show_recipe_info)
        def craft_selected():
            sel = listbox.curselection();
            if not sel: return
            recipe_name = listbox.get(sel[0])
            success, result, consumed_materials = craft_item(recipe_name, self.player.crafting_materials, self.player.pclass)
            if not success: self.append_colored(f"❌ Crafting failed: {result}\n", "error"); self.root.bell(); return
            if not consumed_materials and self.player.pclass == "Fabricator Drone": self.append_colored("⚙️ Fabricator Drone kicks in. Materials not consumed!\n", "success")
            self.root.bell()
            self.player.inventory.append(recipe_name); self.player.items_crafted += 1; self.player.total_items_collected += 1
            self.player.crafted_recipes.add(recipe_name)
            self.append_colored(f"🔨 Successfully crafted: {recipe_name}!\n", "success"); self.append_colored(f"   Effect: {result['effect']}\n", "achievement")
            self._apply_post_craft_effects(recipe_name)
            self._recalc_passives(); self.update_info_display(); self.update_enhanced_map(); self.update_minimap(); check_achievements(self.player, self.world, self)
        tk.Button(self.crafting_popup, text="Craft Selected", width=18, command=craft_selected).pack(side=tk.BOTTOM, pady=(0, 8))
        def close_crafting(): self.crafting_popup.destroy(); self.crafting_popup = None; self.entry.focus_set()
        self.crafting_popup.protocol("WM_DELETE_WINDOW", close_crafting)
    def toggle_journal(self):
        if self._check_if_dead(): return
        if not self.player: self.append_colored("Start a game to view your journal!\n", "error"); return
        if hasattr(self, 'journal_popup') and self.journal_popup and self.journal_popup.winfo_exists(): self.journal_popup.deiconify(); self.journal_popup.lift(); self.journal_popup.focus_force(); return
        self.journal_popup = tk.Toplevel(self.root); self.journal_popup.title("Cosmic Adventure Journal"); self._center_popup(self.journal_popup, 700, 600); self._apply_icon(self.journal_popup)
        notebook = ttk.Notebook(self.journal_popup); notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        quest_frame = ttk.Frame(notebook); notebook.add(quest_frame, text="Main Quests"); quest_text = scrolledtext.ScrolledText(quest_frame, font=("Arial", 10), wrap=tk.WORD); quest_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        quest_info = "📜 QUEST JOURNAL\n" + "="*40 + "\n\n"
        for i, quest in enumerate(EXTENDED_QUESTS):
            if i < self.player.quest_idx: quest_info += f"✅ COMPLETED: {quest['act']}, {quest['title']}\n   {quest['completion']}\n\n"
            elif i == self.player.quest_idx:
                step = self._cur_step()
                quest_info += f"🎯 CURRENT: {quest['act']}, {quest['title']}\n   Character: {quest['character']}\n"
                if step is not None:
                    k = step["kind"]
                    if k == "talk_rick": status = "Talk to Rick for your gadget and clue."
                    elif k == "deliver_char": status = f"Deliver Rick's {quest['rick_gift']} to {quest['character']}."
                    elif k == "retrieve": status = quest['riddle_extra']
                    else: status = f"Bring the {quest['item']} to Rick."
                    quest_info += f"   Next step: {status}\n\n"
                else:
                    quest_info += "\n"
            else: quest_info += f"🔒 LOCKED: {quest['act']}, {quest['title']}\n   Comes later in the story.\n\n"
        quest_text.insert(1.0, quest_info); quest_text.config(state='disabled')
        side_frame = ttk.Frame(notebook); notebook.add(side_frame, text="Side Quests"); side_text = scrolledtext.ScrolledText(side_frame, font=("Arial", 10), wrap=tk.WORD); side_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        side_info = "🧩 SIDE-QUEST JOURNAL\n" + "="*40 + "\n\n"
        for sub in EXTENDED_SUBQUESTS:
            if sub["npc"].lower() not in self.player.subquest_met and sub["npc"].lower() not in self.player.subquest_ack: continue
            if sub["npc"].lower() in self.player.subquest_ack: side_info += f"✅ COMPLETED: {sub['npc']}\n   Reward piece: {sub['reward_item']}\n\n"
            else:
                side_info += f"🎯 CURRENT: {sub['npc']}\n   Needs: {sub['need_item']}\n   How: {sub['key_hint']}\n"
                if self._find_item_in_list(sub['need_item'], self.player.inventory): side_info += f"   Status: ✅ {sub['need_item']} in hand. Return it to {sub['npc']}.\n\n"
                else: side_info += "   Status: 🔍 Still working on it…\n\n"
        if side_info.strip() == "🧩 SIDE-QUEST JOURNAL\n" + "="*40: side_info += "No side-quests discovered yet. Talk to more unique characters!\n"
        side_text.insert(1.0, side_info); side_text.config(state='disabled')
        lore_frame = ttk.Frame(notebook); notebook.add(lore_frame, text="Intel"); lore_text = scrolledtext.ScrolledText(lore_frame, font=("Arial", 10), wrap=tk.WORD); lore_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        lore_content = "📋 RICK'S INTEL: FIELD NOTES\n" + "="*40 + "\n\n"
        if self.player.lore_fragments:
            for i, lore in enumerate(self.player.lore_fragments, 1): lore_content += f"Fragment {i}:\n📜 {lore}\n\n"
        else: lore_content += "No intel gathered yet.\n"; lore_content += "Poke around special rooms and you might turn up some weird multiverse intel.\n"
        lore_text.insert(1.0, lore_content); lore_text.config(state='disabled')
        inv_frame = ttk.Frame(notebook); notebook.add(inv_frame, text="Inventory & Stats"); inv_text = scrolledtext.ScrolledText(inv_frame, font=("Arial", 10), wrap=tk.WORD); inv_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        inv_content = "🎒 INVENTORY & CHARACTER STATUS\n" + "="*40 + "\n\n"; inv_content += f"Morty  •  {self.player.race}  +  {self.player.pclass}  (Universe: {self.current_save_name or "(none)"})\n"
        inv_content += f"Health: {self.player.hp}/{self.player.max_hp}\n"; inv_content += f"Charge: {self.player.charge}/{self.player.max_charge}\n"; inv_content += f"Armor: {self.player.armor}\n\n"; inv_content += "🎒 QUEST ITEMS:\n"
        quest_items = [item for item in self.player.inventory if any(item == q["item"] for q in EXTENDED_QUESTS)]
        if quest_items:
            for item in quest_items: inv_content += f"   • {item}\n"
        else: inv_content += "   None\n"
        inv_content += "\n🔧 CRAFTING MATERIALS:\n"
        if self.player.crafting_materials:
            material_counts = {}; [material_counts.update({material: material_counts.get(material, 0) + 1}) for material in self.player.crafting_materials]
            for material, count in material_counts.items(): inv_content += f"   • {material} x{count}\n"
        else: inv_content += "   None\n"
        inv_content += "\n🌟 SPECIAL ABILITIES:\n"
        for ability in self.player.special_abilities: inv_content += f"   • {ability}\n"
        inv_text.insert(1.0, inv_content); inv_text.config(state='disabled')
        def close_journal(): self.journal_popup.destroy(); self.journal_popup = None; self.entry.focus_set()
        self.journal_popup.protocol("WM_DELETE_WINDOW", close_journal)
    def toggle_achievements(self):
        if self._check_if_dead(): return
        if not self.player: self.append_colored("Start a game to view achievements!\n", "error"); return
        if hasattr(self, 'achievements_popup') and self.achievements_popup and self.achievements_popup.winfo_exists(): self.achievements_popup.deiconify(); self.achievements_popup.lift(); self.achievements_popup.focus_force(); return
        self.achievements_popup = tk.Toplevel(self.root); self.achievements_popup.title("Cosmic Achievements"); self._center_popup(self.achievements_popup, 700, 600); self._apply_icon(self.achievements_popup)
        main_frame = tk.Frame(self.achievements_popup); main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        unlocked_count = len([a for a in ACHIEVEMENTS if a.unlocked]); total_count = len(ACHIEVEMENTS)
        progress_frame = tk.LabelFrame(main_frame, text="Achievement Progress", font=("Arial", 12, "bold")); progress_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(progress_frame, text=f"Achievements Unlocked: {unlocked_count}/{total_count}", font=("Arial", 14, "bold")).pack(pady=5)
        progress_bar = ttk.Progressbar(progress_frame, length=500, mode='determinate'); progress_bar['value'] = (unlocked_count / total_count) * 100 if total_count > 0 else 0; progress_bar.pack(pady=5)
        percentage = int((unlocked_count / total_count) * 100) if total_count > 0 else 0; tk.Label(progress_frame, text=f"{percentage}% Complete", font=("Arial", 11), fg="blue").pack(pady=2)
        list_frame = tk.LabelFrame(main_frame, text="All Achievements", font=("Arial", 12, "bold")); list_frame.pack(fill=tk.BOTH, expand=True)
        achievement_notebook = ttk.Notebook(list_frame); achievement_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        quest_achievements = []; combat_achievements = []; exploration_achievements = []; special_achievements = []
        for achievement in ACHIEVEMENTS:
            if "quest" in achievement.name.lower() or "hopper" in achievement.name.lower(): quest_achievements.append(achievement)
            elif "fighter" in achievement.name.lower() or "cromulon" in achievement.name.lower(): combat_achievements.append(achievement)
            elif "explorer" in achievement.name.lower() or "collector" in achievement.name.lower(): exploration_achievements.append(achievement)
            else: special_achievements.append(achievement)
        categories = [("Quest & Story", quest_achievements), ("Combat", combat_achievements), ("Exploration", exploration_achievements), ("Special", special_achievements)]
        for cat_name, cat_achievements in categories:
            if not cat_achievements: continue
            cat_frame = ttk.Frame(achievement_notebook); achievement_notebook.add(cat_frame, text=cat_name)
            cat_text = scrolledtext.ScrolledText(cat_frame, font=("Arial", 10), wrap=tk.WORD); cat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            cat_content = ""
            for achievement in cat_achievements:
                if achievement.unlocked: cat_content += f"🏅 {achievement.name}\n   ✅ UNLOCKED\n   📖 {achievement.description}\n   🎁 Reward: {achievement.reward}\n\n"
                else:
                    cat_content += f"🔒 {achievement.name}\n   ❌ LOCKED\n   📖 {achievement.description}\n   🎁 Reward: {achievement.reward}\n"
                    if self.player:
                        if "player.quest_idx >= len(EXTENDED_QUESTS)" in achievement.condition: cat_content += f"   📊 Progress: {self.player.quest_idx}/{len(EXTENDED_QUESTS)} main quests completed\n"
                        elif "len(player.subquest_ack) >= len(EXTENDED_SUBQUESTS)" in achievement.condition: cat_content += f"   📊 Progress: {len(self.player.subquest_ack)}/{len(EXTENDED_SUBQUESTS)} side quests completed\n"
                        elif "len(player.visited) >= total_rooms" in achievement.condition: cat_content += f"   📊 Progress: {len(self.player.visited)}/{len(self.world)} rooms visited\n"
                        elif "player.placed_monsters_defeated >= 15" in achievement.condition: cat_content += f"   📊 Progress: {self.player.placed_monsters_defeated}/15 enemies defeated\n"
                        elif "player.items_crafted >= 3" in achievement.condition: cat_content += f"   📊 Progress: {self.player.items_crafted}/3 items crafted\n"
                        elif "len(player.lore_fragments) >= app.total_lore_fragments_count" in achievement.condition: cat_content += f"   📊 Progress: {len(self.player.lore_fragments)}/{self.total_lore_fragments_count} lore fragments collected\n"
                        elif "player.total_items_collected >= 25" in achievement.condition: cat_content += f"   📊 Progress: {self.player.total_items_collected}/25 items collected\n"
                        elif "player.federation_credits >= 50" in achievement.condition: cat_content += f"   📊 Progress: {self.player.federation_credits}/50 Federation Credits acquired\n"
                        elif "player.deaths == 0 and game_complete" in achievement.condition: cat_content += f"   📊 Progress: Deaths: {self.player.deaths} (must be 0 at game completion)\n"
                        elif "cromulon_defeated_count >= 1" in achievement.condition: cat_content += f"   📊 Progress: Cromulons defeated: {self.player.cromulon_defeated_count}/1\n"
                        elif "'Plumbus' in player.inventory or 'Plumbus' in player.crafting_materials" in achievement.condition: cat_content += f"   📊 Progress: Plumbus acquired: {'Yes' if (self.player.plumbuses_collected >= 1 or 'Plumbus' in self.player.inventory or 'Plumbus' in self.player.crafting_materials or 'Plumbus Repair Kit' in self.player.inventory) else 'No'}\n"
                        elif "mega_seeds_used >= 1" in achievement.condition: cat_content += f"   📊 Progress: Mega Seeds used: {self.player.mega_seeds_used}/1\n"
                    cat_content += "\n"
            cat_text.insert(1.0, cat_content); cat_text.config(state='disabled')
        stats_frame = tk.LabelFrame(main_frame, text="Current Statistics", font=("Arial", 12, "bold")); stats_frame.pack(fill=tk.X, pady=(10, 0))
        stats_text = f"Moves: {self.player.moves_taken} | Enemies: {self.player.monsters_defeated} | Crafted: {self.player.items_crafted} | Intel: {len(self.player.lore_fragments)} | Deaths: {self.player.deaths} | Credits: {self.player.federation_credits}" if self.player else "Start a game to track statistics!"
        tk.Label(stats_frame, text=stats_text, font=("Arial", 9)).pack(pady=5)
        def close_achievements(): self.achievements_popup.destroy(); self.achievements_popup = None; self.entry.focus_set()
        self.achievements_popup.protocol("WM_DELETE_WINDOW", close_achievements)
    def start_new_game(self): self.show_difficulty_selection()
    def show_difficulty_selection(self):
        def set_difficulty_and_proceed():
            selected_difficulty = difficulty_var.get()
            self.difficulty = DifficultyLevel(selected_difficulty)
            d.destroy()
            self.root.after(50, self.setup_game_world)
        d = tk.Toplevel(self.root)
        d.title("Select Difficulty")
        self._center_popup(d, 400, 380)
        d.resizable(False, False)
        self._apply_icon(d)
        tk.Label(d, text="Choose Your Challenge", font=("Arial", 14, "bold")).pack(pady=10)
        
        difficulty_var = tk.StringVar(value="normal")
        difficulties = [
            ("Easy", "easy", "More health, weaker enemies, clearer hints"),
            ("Normal", "normal", "Balanced experience for most players"),
            ("Hard", "hard", "Stronger enemies, cryptic clues, less health"),
            ("Nightmare", "nightmare", "For masochists only - brutal difficulty")
        ]
        
        for name, value, desc in difficulties:
            frame = tk.Frame(d)
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Radiobutton(frame, text=name, variable=difficulty_var, value=value, font=("Arial", 11, "bold")).pack(anchor=tk.W)
            tk.Label(frame, text=desc, font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=20)
            
        tk.Button(d, text="Begin Adventure", command=set_difficulty_and_proceed, font=("Arial", 12)).pack(pady=20)
        d.transient(self.root)
        d.grab_set()
        self.root.wait_window(d)
    def _close_all_popups(self):
        """Tear down every secondary window so a new/loaded game can't keep
        showing the previous world. Safe to call when nothing is open."""
        for attr in ("map_popup", "journal_popup", "achievements_popup", "crafting_popup"):
            win = getattr(self, attr, None)
            try:
                if win and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
            setattr(self, attr, None)
        self.map_text_widget = None

    def _sanitize_world(self):
        """Hard rule: a room that holds an NPC (Rick, a quest-giver, a side-quest
        character or the shop) or the starting hub can never also hold a monster, so
        the people you are meant to talk to can never turn into a fight. Runs on a
        freshly generated world and right after a save loads, so an older or
        corrupted save repairs itself instead of dropping you into a bogus battle."""
        if not self.world: return
        for pos, room in self.world.items():
            mon = room.get("monster")
            if not mon: continue
            protected = (room.get("npc") is not None or pos == (1, 1)
                         or room.get("quest_idx") is not None or room.get("side_idx") is not None)
            if protected:
                room["monster"] = None
                blurb = f" A {mon.name} lurks here. {getattr(mon, 'description', '')}"
                if blurb in room.get("desc", ""):
                    room["desc"] = room["desc"].replace(blurb, "")
    def setup_game_world(self):
        # Fresh run: I close any windows left hanging from the last game, the big map especially,
        # or they'll just keep rendering the OLD world like nothing happened. Clean slate.
        self._close_all_popups()
        # I wipe any achievement unlocks left over from a previous game this session, so their
        # one-time perks don't leak onto your shiny new character. No double-dipping.
        for a in ACHIEVEMENTS:
            a.unlocked = False
        (self.world, self.quest_paths, self.quest_rooms, self.npc_rooms, self.motifs_in_play, total_enemies, self.total_lore_fragments_count) = generate_enhanced_game(self.width, self.height, self.difficulty)
        self._sanitize_world()
        self.player = None
        self.show_character_creation()
    def ask_new_game(self):
        if self.player and not messagebox.askyesno("Universe Manager", "Leave this universe? Any unsaved progress here will be lost."): return
        self.show_save_manager()
    def ask_load(self):
        if self.player and not messagebox.askyesno("Universe Manager", "Leave this universe? Any unsaved progress here will be lost."): return
        self.show_save_manager()
    def show_character_creation(self):
        dlg = tk.Toplevel(self.root); dlg.title("Rick's Garage"); self._center_popup(dlg, 480, 470); dlg.transient(self.root); dlg.grab_set(); self._apply_icon(dlg)
        def start():
            self.player = Player("Morty", mainvar.get(), attachvar.get(), self.difficulty)
            self._init_hidden_enemy_system()
            save_name = self.current_save_name or "Morty"; self.current_save_name = save_name
            self._write_save(save_name, announce=False)
            dlg.destroy(); self.set_button_states(menu=False); self.print_room(); self.update_info_display(); self.update_minimap(); self.entry.focus_set()
            self.append_colored(f"🌀 Universe '{save_name}' ready. Morty grabs the {mainvar.get()} and clips on the {attachvar.get()}. Now go talk to Rick.\n", "success")
        def _cycle(combo, update_func, event):
            letter = event.char.lower()
            if not letter.isalpha(): return
            values = combo['values']; cur = combo.current(); start_i = (cur + 1) % len(values); idx = start_i
            while True:
                if values[idx].lower().startswith(letter): combo.current(idx); update_func(); return "break"
                idx = (idx + 1) % len(values)
                if idx == start_i: return "break"
        def _cycle_open(event):
            if event.char.isalpha():
                combo = event.widget.master.master
                if combo == main_combo: _cycle(main_combo, update_main_desc, event)
                elif combo == attach_combo: _cycle(attach_combo, update_attach_desc, event)
                return "break"
        dlg.bind_class("TComboboxPopdown", "<Key>", _cycle_open)
        tk.Label(dlg, text="The ship is dead, the bench is buried in junk, and Rick clearly has not slept. He jabs a thumb at the gear scattered across the workbench. \"Before you set one foot through a portal, Morty, kit yourself out. Take one of my gadgets and clip an attachment onto it. Choose like your life depends on it, because the second you step out there it absolutely does.\"", font=("Arial", 10), justify="left", wraplength=450).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=12, pady=(12, 8))
        tk.Label(dlg, text="Main Gadget:", font=("Arial", 12)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        mainvar = tk.StringVar(value=random.choice([r["name"] for r in EXPANDED_RACES])); main_combo = ttk.Combobox(dlg, textvariable=mainvar, width=20, font=("Arial", 11), state="readonly")
        main_combo['values'] = [r["name"] for r in EXPANDED_RACES]; main_combo.grid(row=1, column=1, padx=10, pady=5)
        main_desc = tk.Text(dlg, height=4, width=54, font=("Arial", 9), wrap=tk.WORD, state="disabled"); main_desc.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        def update_main_desc(event=None):
            data = next(r for r in EXPANDED_RACES if r["name"] == mainvar.get()); main_desc.config(state="normal"); main_desc.delete(1.0, tk.END)
            main_desc.insert(1.0, data['special']); main_desc.config(state="disabled")
        main_combo.bind('<<ComboboxSelected>>', update_main_desc); main_combo.bind('<Key>', lambda e: _cycle(main_combo, update_main_desc, e)); update_main_desc()
        tk.Label(dlg, text="Attachment:", font=("Arial", 12)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        attachvar = tk.StringVar(value=random.choice([c["name"] for c in EXPANDED_CLASSES])); attach_combo = ttk.Combobox(dlg, textvariable=attachvar, width=20, font=("Arial", 11), state="readonly")
        attach_combo['values'] = [c["name"] for c in EXPANDED_CLASSES]; attach_combo.grid(row=3, column=1, padx=10, pady=5)
        attach_desc = tk.Text(dlg, height=4, width=54, font=("Arial", 9), wrap=tk.WORD, state="disabled"); attach_desc.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        def update_attach_desc(event=None):
            data = next(c for c in EXPANDED_CLASSES if c["name"] == attachvar.get()); attach_desc.config(state="normal"); attach_desc.delete(1.0, tk.END)
            attach_desc.insert(1.0, data['special']); attach_desc.config(state="disabled")
        attach_combo.bind('<<ComboboxSelected>>', update_attach_desc); attach_combo.bind('<Key>', lambda e: _cycle(attach_combo, update_attach_desc, e)); update_attach_desc()
        tk.Label(dlg, text=f"Difficulty: {self.difficulty.value.title()}    •    Universe: {self.current_save_name or '(none)'}", font=("Arial", 11, "bold")).grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(dlg, text="Begin", command=start, font=("Arial", 14), bg="#4ADE80", fg="white").grid(row=6, column=0, columnspan=2, pady=16)
        main_combo.focus_set()
    def print_room(self):
        if not self.player: return
        x, y = self.player.x, self.player.y; room = self.world[(x, y)]; room["visited"] = True; self.player.visited.add((x, y)); self.player.teleport_locations.add((x, y))
        if self.player.pclass == "Holo-Mapper" and random.random() < 0.20:
            unvisited_neighbors = [(x+dx, y+dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)] if (x+dx, y+dy) in self.world and (x+dx, y+dy) not in self.player.visited]
            if unvisited_neighbors:
                revealed_room_pos = random.choice(unvisited_neighbors); self.world[revealed_room_pos]["visited"] = True; self.player.visited.add(revealed_room_pos)
                self.append_colored(f"🗺️ Holo-Mapper reveals a nearby area: {to_letter_number(revealed_room_pos[0], revealed_room_pos[1])}\n", "achievement"); self.update_enhanced_map(); self.update_minimap()
        self.text.config(state='normal'); self.text.delete(1.0, tk.END); self.text.config(state='disabled')
        self.append_colored(f"\n== Location {to_letter_number(x, y)} ==\n", "quest")
        self.append_colored(f"{room['desc']}\n")
        if "hidden_lore" in room and not room.get("lore_discovered", False): self.append_colored("📋 Something here catches your eye. There's more to this place than it lets on.\n", "lore")
        if room["items"]: self.append_colored("🎒 You see: ", "success"); self.append_colored(", ".join(room["items"]) + "\n")
        elif room.get("looted"): self.append_colored(f"🫳 Nothing left here. You already grabbed {self._np(room['looted'][-1])} from this spot.\n", "lore")
        if room["npc"]: self.append_colored(f"👤 {room['npc'].name} is here.\n", "achievement" if room['npc'].is_subquest else "quest")
        if room["monster"]:
            if getattr(room["monster"], "hidden", False):
                self.append_colored("\n*** SURPRISE ATTACK!!! ***\n", "surprise")
            self.append_colored(f"⚔️ DANGER: {room['monster'].name} blocks your path! ", "combat"); self.append_colored(f"(HP: {room['monster'].hp}/{room['monster'].max_hp})\n", "combat")
        if room.get("monster") is None and room.get("last_defeated_monster"): self.append_colored(f"💀 You see the remains of a {room['last_defeated_monster']} here.\n", "lore")
        exits = [];
        if y > 1: exits.append("north")
        if y < self.height: exits.append("south")
        if x > 1: exits.append("west")
        if x < self.width: exits.append("east")
        self.append_colored(f"🚪 Exits: {', '.join(exits)}\n")
        check_achievements(self.player, self.world, self); self.update_info_display(); self.update_minimap()
    def scan_room(self):
        if self._check_if_dead(): return
        if not self.player: self.append_colored("Start a game first!\n", "error"); return
        x, y = self.player.x, self.player.y; room = self.world[(x, y)]
        
        if self.player.race != "Recon Visor":
            self.append_colored("You need the Recon Visor equipped to scan a room.\n", "error")
            self.root.bell()
            return
            
        self.append_colored("\n🔍 SCAN RESULTS:\n", "achievement")
        if room.get("motif") is not None:
            motif_data = EXTENDED_MOTIFS[room["motif"]]; self.append_colored(f"   Motif detected: {motif_data['motif']}\n", "lore")
        if room.get("quest_idx") is not None: self.append_colored(f"   Quest significance: Level {room['quest_idx'] + 1}\n", "quest")
        if room.get("hidden_lore") and not room.get("lore_discovered"): self.append_colored("   Hidden lore fragment detected!\n", "lore")
        if room.get("special_interactions"): self.append_colored(f"   Special interactions: {', '.join(room['special_interactions'])}\n", "success")
        adjacent_monsters = sum(1 for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)] if (x + dx, y + dy) in self.world and self.world[(x + dx, y + dy)].get("monster"))
        if adjacent_monsters > 0: self.append_colored(f"   ⚠️ {adjacent_monsters} {'enemy' if adjacent_monsters == 1 else 'enemies'} detected nearby!\n", "combat")
        else: self.append_colored("   ✅ No immediate dangers detected.\n", "success")
        self.entry.focus_set()
    def discover_lore(self):
        if not self.player: return
        room = self.world[(self.player.x, self.player.y)]
        if "hidden_lore" in room and not room.get("lore_discovered", False):
            lore = room["hidden_lore"]; self.player.lore_fragments.append(lore); room["lore_discovered"] = True
            self.append_colored("📋 You search the area and turn up some intel:\n", "achievement"); self.append_colored(f"📜 {lore}\n", "lore")
            self.append_colored(f"Intel gathered: {len(self.player.lore_fragments)}.\n", "success")
            self.grant_xp(3, "intel uncovered"); check_achievements(self.player, self.world, self)
        else: self.append_colored(f"Nothing useful to search here, {self.player.name}. Move on.\n")
    def _find_pos(self, predicate):
        """Return the first world coordinate whose room satisfies predicate, else None."""
        for pos, rm in self.world.items():
            if predicate(pos, rm):
                return pos
        return None

    def _compass_to(self, target):
        """Human-readable compass nudge from the player toward target coords."""
        if not target:
            return ""
        tx, ty = target; px, py = self.player.x, self.player.y
        if (tx, ty) == (px, py):
            return "right where you're standing"
        ns = "north" if ty < py else ("south" if ty > py else "")
        ew = "west" if tx < px else ("east" if tx > px else "")
        direction = (ns + ew) if (ns and ew) else (ns or ew)  # e.g. northwest, east, that kind of thing.
        steps = abs(tx - px) + abs(ty - py)
        return f"to the {direction} (~{steps} room{'s' if steps != 1 else ''} away)"

    def show_hint(self, event=None):
        p = self.player
        if not p: self.append_colored("You don't even have a baseline reality yet.\n", "lore"); return
        step = self._cur_step()
        if step is None: self.append_colored("🏁 The OMNI-CORE is finished. That thread's cut. Explore or wrap up side quests.\n", "success"); return
        ch = EXTENDED_QUESTS[step["ci"]]; kind = step["kind"]
        self.append_colored(f"📖 {ch['act']}: {ch['title']}\n", "quest")
        rick_pos = self._find_pos(lambda pos, rm: rm.get("npc") and getattr(rm["npc"], "is_rick", False))
        char_pos = self._find_pos(lambda pos, rm: rm.get("npc") and not getattr(rm["npc"], "is_rick", False) and not rm["npc"].is_subquest and rm["npc"].name == ch["character"])
        if kind == "talk_rick":
            self.append_colored("Talk to Rick for your next gadget and clue.\n", "lore")
            if rick_pos: self.append_colored(f"🧭 Rick is {self._compass_to(rick_pos)}.\n", "lore")
        elif kind == "deliver_char":
            self.append_colored(f"Take Rick's {ch['rick_gift']} to {ch['character']}.\n", "lore")
            if char_pos: self.append_colored(f"🧭 {ch['character']} is {self._compass_to(char_pos)}.\n", "lore")
        elif kind == "retrieve":
            motif_pos = self._find_pos(lambda pos, rm: rm.get("quest_idx") == step["ci"] and rm.get("motif") is not None)
            self.append_colored(f"{ch['riddle_extra']}\n", "lore")
            if motif_pos: self.append_colored(f"🧭 The place to {_motif_verb(ch['motif'])} lies {self._compass_to(motif_pos)}.\n", "lore")
        elif kind == "deliver_rick":
            self.append_colored(f"Bring the {ch['item']} back to Rick. He'll forge the next OMNI-CORE part.\n", "lore")
            if rick_pos: self.append_colored(f"🧭 Rick is {self._compass_to(rick_pos)}.\n", "lore")
    def handle_combat(self, monster, damage_override=None, stun_monster_for_turn=False, player_strikes=1):
        """One round of combat. player_strikes > 1 means the player lands several
        hits THIS turn (e.g. echo_scream) before the monster gets its single
        retaliation, not multiple full rounds."""
        p = self.player
        combat_log = []   # Always initialize it. Don't make me explain why.

        # ===== Level-scaling: monsters keep pace with you so you can't just outlevel the whole game. =====
        # Done ONCE per monster (the flag stops it compounding every round). Above level 1, each player
        # level adds +5% HP and +3.5% damage to whatever this thing already had, so the world keeps pace
        # with you instead of becoming a petting zoo, without snowballing into an unwinnable wall.
        if not getattr(monster, "level_scaled", False) and p.level > 1:
            lv = p.level - 1
            hp_scale = 1.0 + 0.05 * lv
            dmg_scale = 1.0 + 0.035 * lv
            monster.max_hp = max(1, int(monster.max_hp * hp_scale))
            monster.hp = max(1, int(monster.hp * hp_scale))
            monster.damage = max(1, int(monster.damage * dmg_scale))
            monster.level_scaled = True

        # ===== Status ticks at the top of the round: poison eats you, debuffs count down. =====
        if p.dot_turns > 0:
            tick = max(1, p.dot_damage)
            p.hp -= tick
            combat_log.append(f"🤢 {p.dot_label or 'Something nasty'} eats at you for {tick} damage. (Your HP: {max(p.hp,0)}/{p.max_hp})")
            p.dot_turns -= 1
            if p.dot_turns == 0:
                p.dot_damage = 0; p.dot_label = ""
            if p.hp <= 0:
                combat_log.append("You are defeated!")
                for line in combat_log: self.append_colored(line + "\n", "combat")
                p.deaths += 1; self.update_info_display(); self._check_if_dead(); return

        # ===== You hitting the monster. Could be several strikes in one turn. =====
        if p.stunned_for_next_turn:
            p.stunned_for_next_turn = False
            combat_log.append(
                "🚓 You're still dealing with interdimensional police paperwork and miss your chance to attack this round!"
            )
        else:
            for _ in range(max(1, player_strikes)):
                base_player_attack = PLAYER_BASE_DAMAGE + p.damage_bonus + random.randint(-1, 1)
                if damage_override is not None:
                    base_player_attack = damage_override
                # If a monster weakened you (Tammy's charm, a parasite, whatever), your hits land softer
                # until it wears off. The debuff ticks down once per round, handled below.
                if p.damage_debuff_turns > 0:
                    base_player_attack = max(1, int(base_player_attack * 0.6))
                dmg_to_mon = max(1, base_player_attack)
                monster.hp -= dmg_to_mon
                combat_log.append(
                    f"You attack {monster.name} for {dmg_to_mon} damage! "
                    f"({monster.name} HP: {max(monster.hp,0)}/{monster.max_hp})"
                )
                if monster.hp <= 0:
                    break
        if monster.hp <= 0:
            combat_log.append(f"{monster.name} is defeated!")
            # Something died: do the world bookkeeping first, before anything else.
            x, y = p.x, p.y
            self.world[(x, y)]["monster"] = None
            self.world[(x, y)]["last_defeated_monster"] = monster.name
            is_hidden = getattr(monster, "hidden", False)
            prev_total = p.monsters_defeated
            p.monsters_defeated += 1                       # total kill score (placed + hidden)
            if not is_hidden:
                p.placed_monsters_defeated += 1            # only placed ones count toward the achievement and 100 percent
            if "Cromulon" in monster.name:
                p.cromulon_defeated_count += 1
            p.meeseeks_attack_doubled = False
            self.update_enhanced_map(); self.update_minimap()
            # Print the attack lines FIRST, killing blow included. Drama matters.
            for line in combat_log:
                self.append_colored(line + "\n", "combat")
            # ...THEN the loot drop.
            if is_hidden:
                # Hidden ambushers only ever pay out Credits, and I hand them over directly so they're
                # NOT logged as a collected item. Nothing the game needs ever comes off one of these.
                gained = random.randint(2, 6)
                p.federation_credits += gained
                self.append_colored(f"💰 The {monster.name} jumped you out of nowhere and dropped {gained} Federation Credits. (Total: {p.federation_credits})\n", "success")
                self._recalc_passives()
            elif monster.loot:
                credit_drops = monster.loot.count("Federation Credits")
                item_loot = [it for it in monster.loot if it != "Federation Credits"]
                if item_loot:
                    self.append_colored(
                        f"The {monster.name} dropped: {', '.join(item_loot)}\n", "success"
                    )
                for it in item_loot:
                    if any(it in r["materials"] for r in CRAFTING_RECIPES.values()):
                        p.crafting_materials.append(it)
                    else:
                        p.inventory.append(it)
                    p.total_items_collected += 1
                if credit_drops:
                    gained = sum(random.randint(1, 5) for _ in range(credit_drops))
                    p.federation_credits += gained
                    p.total_items_collected += credit_drops
                    self.append_colored(f"💰 You loot {gained} Federation Credits off the {monster.name}. (Total: {p.federation_credits})\n", "success")
                self._recalc_passives()
            else:
                self.append_colored("No loot dropped.\n", "lore")
            # ...THEN the XP gain. Order of operations, Morty.
            self.grant_xp(monster.max_hp, f"defeated {monster.name}")
            # Every third kill, no matter what kind, pops a fresh hidden one somewhere you've already been.
            self._cascade_hidden_spawns(prev_total, p.monsters_defeated)
            self.update_info_display()
            self._check_if_dead() # If you died this turn, lock input instantly. Game over means game over.
            return
        
        # ===== The monster hitting back. One retaliation, that's it. =====
        # Either it was a one-turn stun (mind_wipe) OR the thing's still got a multi-turn stun from the Mindblower.
        if stun_monster_for_turn or getattr(monster, "stun_turns", 0) > 0:
            if getattr(monster, "stun_turns", 0) > 0:
                monster.stun_turns -= 1
                combat_log.append(
                    f"🧠 {monster.name} is still dazed from the Mindblower and can't act this turn!"
                )
            else:
                combat_log.append(
                    f"🧠 {monster.name} is stunned and cannot attack this turn!"
                )
        else:
            # Butter Robot's little disorient gimmick.
            butter_robot_disorient = (
                p and p.race == "Brainalyzer" and random.random() < 0.10
            )
            if butter_robot_disorient:
                combat_log.append(
                    f"🤖 The Butter Robot's existential dread disorients {monster.name}, making it miss!"
                )
            else:
                total_armor = p.armor
                base_damage_value = monster.damage
                # If it's still woozy from mind_wipe, I halve its next hit and clear the flag. One-time mercy.
                if getattr(monster, "weakened_next_attack", False):
                    base_damage_value = max(1, base_damage_value // 2)
                    monster.weakened_next_attack = False
                    combat_log.append(
                        f"💫 {monster.name} is still trying to remember its own name after your mind wipe. "
                        "Its attack is half-hearted."
                    )
                # ===== Special attack logic. The flashy moves. =====
                use_special = (
                    getattr(monster, "special_attack_chance", 0.0) > 0.0
                    and random.random() < monster.special_attack_chance
                )
                if use_special and monster.special_attack_name:
                    combat_log.append(
                        f"🚨 {monster.name} uses {monster.special_attack_name}!"
                    )
                    special_damage = monster.damage
                    sn = monster.special_attack_name

                    # Small helper so no stun can ever chain two turns in a row. If you're already
                    # flagged immune, the stun fizzles into a glancing hit instead. Struggle, not lockdown.
                    def _try_stun():
                        if getattr(p, "stun_immune_next", False):
                            combat_log.append("   ...but you shake it off before it can pin you twice in a row.")
                            p.stun_immune_next = False
                            return False
                        p.stunned_for_next_turn = True
                        p.stun_immune_next = True
                        return True

                    # ===== Existing four =====
                    if sn == "Suppressing Fire":
                        special_damage = int(monster.damage * 1.5)
                        combat_log.append("   It lays down a barrage of blaster fire!")
                    elif sn == "SHOW ME WHAT YOU GOT":
                        combat_log.append("   'SHOW ME WHAT YOU GOT!' A psychic shockwave smashes into your brain!")
                        drain = 5; old_charge = p.charge; p.charge = max(0, p.charge - drain)
                        if p.charge < old_charge: combat_log.append(f"   Your Charge drops by {drain}!")
                    elif sn == "Telepathic Assault":
                        special_damage = int(monster.damage * 0.5)
                        combat_log.append("   Its thoughts invade your mind, making you dizzy!")
                    elif sn == "Summon Police":
                        special_damage = int(monster.damage * 0.8)
                        combat_log.append("   'I CONTROL the police!' he bellows. You're suddenly being arrested.")
                        _try_stun()
                    # ===== Iconic bespoke specials =====
                    elif sn == "Existential Crisis":  # Butter Robot
                        special_damage = max(1, int(monster.damage * 0.4))
                        combat_log.append("   'What is my purpose?' it whimpers. The sheer despair makes your arms heavy.")
                        if p.damage_debuff_turns <= 0:
                            p.damage_debuff_turns = 2
                            combat_log.append("   Your swings go limp for a couple turns. Pass the butter.")
                    elif sn == "Infectious Spread":  # Mr. Frundles
                        special_damage = int(monster.damage * 0.7)
                        combat_log.append("   'I'm Mr. Frundles!' It nicks you and something starts spreading.")
                        if p.dot_turns <= 0:
                            p.dot_turns = 3; p.dot_damage = max(2, int(monster.damage * 0.3)); p.dot_label = "Frundles infection"
                            combat_log.append("   You're infected. This is gonna keep hurting, Morty.")
                    elif sn == "Gazorpian Tantrum":  # Morty Jr.
                        special_damage = int(monster.damage * 1.6)
                        combat_log.append("   'I AM A PERSON!' Morty Jr. flies into a full Gazorpian rage and clobbers you.")
                    elif sn == "Federation Charm":  # Tammy
                        special_damage = int(monster.damage * 0.6)
                        combat_log.append("   'Oh my god, you totally fell for it.' Tammy's whole nice-girl act throws you off your game.")
                        if p.damage_debuff_turns <= 0:
                            p.damage_debuff_turns = 2
                            combat_log.append("   You're rattled. Your damage drops for a couple turns.")
                    elif sn == "Hive Assimilation":  # Unity
                        combat_log.append("   'We could be so good together.' Unity's collective tries to fold you in, and siphons your focus.")
                        drain = 6; old = p.charge; p.charge = max(0, p.charge - drain)
                        if p.charge < old: combat_log.append(f"   Your Charge drains by {drain} into the hive!")
                        special_damage = int(monster.damage * 0.7)
                    elif sn == "Mecha Combine":  # Gotron Drone
                        special_damage = int(monster.damage * 1.4)
                        combat_log.append("   The drone snaps into partial Gotron config and comes down on you like a small building.")
                    elif sn == "Tinfoil Rant":  # Conspiracy Morty
                        special_damage = int(monster.damage * 0.5)
                        combat_log.append("   'The Ricks are watching, man! Wake UP!' His rambling actually distracts YOU more than him.")
                        if random.random() < 0.5 and not getattr(p, "stun_immune_next", False):
                            _try_stun()
                            combat_log.append("   You lose a turn just trying to follow his logic.")
                    elif sn == "Eco Lecture":  # Planetina's Minion
                        special_damage = int(monster.damage * 0.6)
                        combat_log.append("   It guilt-trips you about carbon emissions mid-swing. Weirdly effective.")
                        if p.damage_debuff_turns <= 0:
                            p.damage_debuff_turns = 1
                            combat_log.append("   You feel bad enough to pull your next hit.")
                    elif sn == "Microverse Override":  # Zeep's Sentry (boss)
                        special_damage = int(monster.damage * 1.3)
                        combat_log.append("   Zeep's sentry reroutes its whole microverse's power into one contemptuous strike.")
                        if p.charge > 0:
                            drain = 4; p.charge = max(0, p.charge - drain)
                            combat_log.append(f"   It shorts out {drain} of your Charge for good measure.")
                    # ===== Shared generic specials (the no-name drones and brutes) =====
                    elif sn == "Wild Swing":
                        special_damage = int(monster.damage * 1.4)
                        combat_log.append("   It throws everything into one reckless haymaker.")
                    elif sn == "Rattling Blow":
                        special_damage = int(monster.damage * 0.9)
                        combat_log.append("   A jarring hit that leaves your ears ringing.")
                        if random.random() < 0.4: _try_stun()
                    elif sn == "Cheap Shot":
                        special_damage = int(monster.damage * 0.7)
                        combat_log.append("   A dirty little jab where it counts.")
                        if p.damage_debuff_turns <= 0: p.damage_debuff_turns = 1
                    # End of the specials.
                    dmg_to_player = max(
                        1, special_damage + random.randint(-1, 1) - total_armor
                    )
                else:
                    # A plain old normal attack.
                    dmg_to_player = max(
                        1, base_damage_value + random.randint(-1, 1) - total_armor
                    )
                p.hp -= dmg_to_player
                combat_log.append(
                    f"{monster.name} attacks you for {dmg_to_player} damage! "
                    f"(Your HP: {max(p.hp,0)}/{p.max_hp})"
                )
                if p.hp <= 0:
                    combat_log.append("You are defeated!")
                    p.deaths += 1
        # The weaken debuff counts down once per round it survived to the end of. When it expires, say so.
        if p.damage_debuff_turns > 0:
            p.damage_debuff_turns -= 1
            if p.damage_debuff_turns == 0:
                combat_log.append("💪 You shake off the funk. Your hits are back to full strength.")
        # Print the log and refresh the UI, one line at a time.
        for line in combat_log:
            self.append_colored(line + "\n", "combat")
        self.update_info_display()
        self._check_if_dead() # If you died this turn, lock input instantly. Same deal as before.
    def _handle_portal_jump(self, parts):
        p = self.player;
        if "Portal Gun (Replica)" not in p.inventory: self.append_colored("❌ You need a 'Portal Gun (Replica)' to jump dimensions!", "error"); return
        cost_charge = ATTACK_COST["portal_jump"]["charge"]
        if p.portal_gun_no_charge_cost: cost_charge = 0; self.append_colored("🌟 Portal jump is FREE!", "success")
        if p.charge < cost_charge: self.append_colored(f"❌ Not enough charge to open a portal. Needs {cost_charge}.", "error"); return
        if len(parts) < 3: self.append_colored("Usage: portal_jump <X> <Y> (e.g. portal_jump B 4)\n", "error"); self.append_colored("Known locations: " + ", ".join(sorted([to_letter_number(x,y) for x,y in p.teleport_locations])) + "\n", "lore"); return
        try: target_x = parse_coord(parts[1]); target_y = parse_coord(parts[2])
        except (ValueError, IndexError): self.append_colored("❌ Invalid coordinates. Use format: portal_jump <X> <Y>\n", "error"); return
        if (target_x, target_y) not in p.teleport_locations: self.append_colored(f"❌ You haven't visited {to_letter_number(target_x, target_y)} yet. You can only jump to known locations.\n", "error"); return
        
        target_room = self.world[(target_x, target_y)]
        if target_room.get("monster"):
            self.append_colored(
                f"⚠️ Warning: Sensors detect a hostile presence in {to_letter_number(target_x, target_y)}. Proceed with caution.\n", 
                "combat"
            )
            
        p.charge -= cost_charge; p.last_room = (p.x, p.y); p.x, p.y = target_x, target_y
        p.moves_taken += 1; self.append_colored(f"🌐 You activate the Portal Gun and jump to {to_letter_number(target_x, target_y)}!\n", "success")
        self.print_room(); self.update_enhanced_map(); self.update_minimap(); self.update_info_display()
    
    # ===== Feature 2.2: hooking events into movement. Stuff that fires when you walk. =====
    def move(self, delta):
        if self._check_if_dead(): return
        if not self.player: return
        dx, dy = delta; nx, ny = self.player.x + dx, self.player.y + dy
        if 1 <= nx <= self.width and 1 <= ny <= self.height:
            if self.world[(self.player.x, self.player.y)].get("monster"): self.append_colored("⚔️ An enemy blocks your path! You must fight or flee!\n", "combat"); self.root.bell(); return
            self.player.last_room = (self.player.x, self.player.y); self.player.x, self.player.y = nx, ny; self.player.moves_taken += 1
            # Phoenix Implant passive: you regenerate 1 HP every 5 real moves. Slow and steady.
            if self.player.race == "Phoenix Implant" and self.player.moves_taken % 5 == 0 and 0 < self.player.hp < self.player.max_hp:
                self.player.hp = min(self.player.hp + 1, self.player.max_hp)
                self.append_colored("💚 The Phoenix Implant knits you back together (+1 HP).\n", "success")
            self.print_room(); self.update_enhanced_map(); self.player.teleport_locations.add((self.player.x, self.player.y))
            self._trigger_random_event()
        else: self.append_colored("🚫 " + self._quip("no_exit") + "\n", "error"); self.root.bell()
        self.entry.delete(0, tk.END); self.entry.focus_set()
    def process_command(self, event=None):
        if hasattr(self, "_close_completion_popup"): self._close_completion_popup()
        cmd = self.entry.get().strip(); self.entry.delete(0, tk.END)
        if not cmd or not self.player: return
        if self._check_if_dead(): return
        p = self.player; x, y = p.x, p.y; room = self.world[(x, y)]; parts = cmd.lower().split(); command = parts[0]
        
        motif_alias = {"watch": "observe", "bite": "eat", "workbench": "tinker", "bench": "tinker", "couch": "negotiate", "rummage": "scavenge", "loot": "scavenge", "barter": "haggle", "deal": "haggle", "inspect": "examine", "study": "examine", "probe": "investigate", "analyze": "investigate", "summon": "call", "pick": "harvest", "pluck": "harvest", "drink": "order", "sip": "order", "payoff": "bribe", "grease": "bribe", "sync": "connect", "link": "connect",}
        if command in motif_alias: command = motif_alias[command]; parts[0] = command
        # Combat moves get typed straight. Here I just normalize your friendly spelling variants.
        if command in DIRECT_ALIAS: command = DIRECT_ALIAS[command]; parts = [command]
        # e.g. 'echo scream', 'cast plasma_blast', 'fire plasma', 'discover lore'. I forgive a lot.
        if command in ("echo", "cast", "fire") and len(parts) >= 2:
            command = DIRECT_ALIAS.get(parts[1], parts[1]); parts = [command]
        if command == "discover" and len(parts) >= 2 and parts[1] == "lore":
            command = "discover_lore"; parts = ["discover_lore"]

        # =====
        # DEVELOPER CHEAT CODES. Yeah I left cheats in. I'm the developer. Don't lecture me, Morty.
        # =====
        if command == "8675309":  # Rip the whole map open. See everything.
            for pos, rm in self.world.items():
                rm["visited"] = True; p.visited.add(pos); p.teleport_locations.add(pos)
            self.append_colored("🧠 Cheat: all rooms revealed.\n", "success")
            self.update_enhanced_map(); self.update_minimap(); self.update_info_display(); return
        if command == "uuddlrlrbastart":  # Vacuum up every loose item on the map. Finders keepers.
            scooped = 0
            for pos, rm in self.world.items():
                for it in rm["items"][:]:
                    if it == "Federation Credits": p.federation_credits += random.randint(5, 15)
                    elif it == "Mega Seed" and getattr(p, "mega_seed_injector_built", False): p.inventory.append(it)
                    elif any(it in r["materials"] for r in CRAFTING_RECIPES.values()): p.crafting_materials.append(it)
                    else: p.inventory.append(it)
                    p.total_items_collected += 1; scooped += 1
                    self._strip_found_sentence(rm, it); rm["items"].remove(it)
                    rm["visited"] = True; p.visited.add(pos)
            self.append_colored(f"🍺 Cheat: {scooped} loose item(s) collected.\n", "success")
            self._recalc_passives(); self.update_enhanced_map(); self.update_minimap(); self.update_info_display()
            check_achievements(p, self.world, self); return
        if command == "mr5niper5ux":  # One-shot every enemy and loot the corpses. Efficient.
            wiped = grabbed = placed_wiped = 0
            for pos, rm in self.world.items():
                if rm.get("monster"):
                    mon = rm["monster"]
                    if not getattr(mon, "hidden", False): placed_wiped += 1
                    for it in (mon.loot or [])[:]:
                        if it == "Federation Credits": p.federation_credits += 1
                        elif it == "Mega Seed" and getattr(p, "mega_seed_injector_built", False): p.inventory.append(it)
                        elif any(it in r["materials"] for r in CRAFTING_RECIPES.values()): p.crafting_materials.append(it)
                        else: p.inventory.append(it)
                        p.total_items_collected += 1; grabbed += 1
                    if "Cromulon" in mon.name: p.cromulon_defeated_count += 1
                    mon.loot.clear()
                    rm["last_defeated_monster"] = mon.name; rm["monster"] = None
                    rm["visited"] = True; p.visited.add(pos); wiped += 1
            p.monsters_defeated += wiped
            p.placed_monsters_defeated += placed_wiped
            # No cascade here on purpose: this cheat is a board-clear, so re-seeding hidden ones would fight its whole point.
            self.append_colored(f"💀 Cheat: {wiped} enemies evaporated; {grabbed} item(s) collected.\n", "success")
            self._recalc_passives(); self.update_enhanced_map(); self.update_minimap(); self.update_info_display()
            check_achievements(p, self.world, self); return
        if command == "ucdclcrc":  # Hand yourself every craftable gadget. Skip the homework.
            crafted_now = []
            for itm in CRAFTING_RECIPES:
                if itm not in p.inventory:
                    p.inventory.append(itm); crafted_now.append(itm)
                    p.items_crafted += 1; p.total_items_collected += 1; p.crafted_recipes.add(itm)
            if "Mega Seed Injector" in p.inventory and not getattr(p, "mega_seed_injector_built", False):
                p.mega_seed_injector_built = True
                while "Mega Seed" in p.crafting_materials:
                    p.crafting_materials.remove("Mega Seed"); p.inventory.append("Mega Seed")
            self.append_colored(f"🔧 Cheat: {len(crafted_now)} gadget(s) granted: {', '.join(crafted_now) if crafted_now else '(already had them all)'}.\n", "success")
            self._recalc_passives(); self.update_info_display(); self.update_enhanced_map(); self.update_minimap()
            check_achievements(p, self.world, self); return

        # Movement via text commands. North, south, you get it.
        if command in ["north", "n", "up"]:
            self.move((0, -1))
            return
        elif command in ["south", "s", "down"]:
            self.move((0, 1))
            return
        elif command in ["west", "w", "left"]:
            self.move((-1, 0))
            return
        elif command in ["east", "e", "right"]:
            self.move((1, 0))
            return
        
        # ===== Feature 1.4: shop and talk logic. Spending money and yapping. =====
        if command in ["talk", "list", "buy", "sell"]:
            if room.get("npc") and room["npc"].name == "Glexo Slimslom":
                self._handle_shop_interaction(command, parts)
            elif command == "talk":
                if not room["npc"]: self.append_colored("🗣️ " + self._quip("no_one") + "\n", "error"); self.root.bell(); return
                self._talk_separator()
                npc = room["npc"]
                if getattr(npc, "is_rick", False): self.handle_rick_dialog(npc)
                elif npc.is_subquest: self.handle_subquest_dialog(npc, room)
                else: self.handle_chapter_char_dialog(npc)
            else:
                self.append_colored("You can only do that at a shop.\n", "error"); self.root.bell()
            return
        # ===== End of the shop logic. =====
        
        elif command in COMBAT_MOVES:
            monster = room.get("monster")
            if command == "show_me_what_you_got" and p.race != "Neutrino Bomb":
                self.append_colored("❌ That blast needs the Neutrino Bomb equipped.\n", "error"); self.root.bell(); return
            if not monster:
                # No enemy here, so you just flail around like an idiot. It still burns the move's cost,
                # but nothing in the world, NPCs, or quests actually changes. Swing at ghosts, sure.
                self._comedic_whiff(command, room); return
            cost = ATTACK_COST[command]
            # Echo scream cooldown: it's a two-hit finisher, not a spam button. If you screamed last
            # turn, the move's on cooldown and you have to do literally anything else for one turn.
            # We check this BEFORE charging you, so a blocked scream doesn't cost you a thing.
            if command == "echo_scream" and getattr(monster, "echo_cd", False):
                self.append_colored("🗯️ Your throat's still raw from the last echo scream. Cooldown, Morty. Do something else this turn.\n", "error"); self.root.bell(); return
            if not self._consume_resources(charge=cost["charge"], hp=cost["hp"], xp=cost["xp"]):
                return  # Couldn't afford it, so no attack happens. Broke, Morty.
            # Any move that isn't an echo scream clears the cooldown; the scream itself sets it.
            if command == "echo_scream":
                monster.echo_cd = True
            else:
                monster.echo_cd = False
            if command == "plasma_blast":
                self.handle_combat(monster, damage_override=PLAYER_BASE_DAMAGE * 2 + p.damage_bonus + random.randint(0, 2))
            elif command == "mind_wipe":
                monster.weakened_next_attack = True
                self.handle_combat(monster, damage_override=PLAYER_BASE_DAMAGE + p.damage_bonus + random.randint(0, 1), stun_monster_for_turn=True)
            elif command == "show_me_what_you_got":
                self.handle_combat(monster, damage_override=PLAYER_BASE_DAMAGE * 3 + p.damage_bonus + random.randint(0, 3))
            elif command == "echo_scream":
                self.append_colored("You unleash a devastating echo scream!\n", "combat")
                self.handle_combat(monster, player_strikes=2)  # Two of your hits, but only ONE retaliation. Math in your favor for once.
            return
        elif command == "attack":
            monster = room.get("monster")
            if monster:
                monster.echo_cd = False  # A normal swing counts as "something else", clears the scream cooldown.
                self.handle_combat(monster)
                return
            else:
                self._comedic_whiff("attack", room); return
        elif command == "flee":
            if room.get("monster"):
                p.meeseeks_attack_doubled = False  # Always reset it. Every time.
                if random.random() < 0.7:
                    self.append_colored("💨 You successfully flee from combat!\n", "success")
                    fled_monster = room.get("monster")
                    last_x, last_y = p.last_room
                    if abs(last_x - x) + abs(last_y - y) == 1 and (1 <= last_x <= self.width) and (1 <= last_y <= self.height): 
                        p.x, p.y = last_x, last_y; self.print_room(); self.update_enhanced_map()
                    else:
                        possible_moves = [(dx, dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)] if 1 <= x + dx <= self.width and 1 <= y + dy <= self.height]
                        if possible_moves: 
                            dx, dy = random.choice(possible_moves); p.x, p.y = x + dx, y + dy; self.print_room(); self.update_enhanced_map()
                    # A hidden ambusher doesn't sit politely where you left it. When you slip away it skulks
                    # off to some OTHER empty room you've already been through, never the one you fled into.
                    if fled_monster is not None and getattr(fled_monster, "hidden", False):
                        room["monster"] = None
                        spots = self._hidden_candidate_rooms(exclude={(x, y)})  # your new tile is auto-excluded
                        if spots:
                            self.world[random.choice(spots)]["monster"] = fled_monster
                        else:
                            room["monster"] = fled_monster  # Nowhere legal to skulk off to, so it stays put this once.
                        self.update_enhanced_map(); self.update_minimap()
                else: self.append_colored("💥 Failed to flee! The enemy attacks!\n", "combat"); self.handle_combat(room["monster"])
            else: self.append_colored("❌ Nothing to flee from.\n", "error"); self.root.bell()
            return
        elif command == "get":
            if not room["items"]: self.append_colored("🤲 " + self._quip("nothing_to_take") + "\n", "error"); self.root.bell(); return
            if len(parts) > 1:
                typed_raw = " ".join(parts[1:]).strip()
                if self._normalize_text(typed_raw) in {"federation credits", "credits", "credit"}:
                    if "Federation Credits" in room["items"]:
                        credits_amount = random.randint(5, 15);
                        if any(a.name == "Schmeckle Millionaire" and a.unlocked for a in ACHIEVEMENTS): credits_amount += (credits_amount // 10) * 2
                        p.federation_credits += credits_amount; room["items"].remove("Federation Credits"); self._strip_found_sentence(room, "Federation Credits"); p.total_items_collected += 1
                        check_achievements(p, self.world, self); self.update_info_display(); self.print_room(); self.append_colored(f"💰 You collect {credits_amount} Federation Credits. Total: {p.federation_credits}\n", "success"); return
                    else: self.append_colored("💸 " + self._quip("nothing_to_take") + "\n", "error"); self.root.bell(); return
                match = self._find_item_in_list(typed_raw, room["items"])
                if match: self.get_specific_item(match)
                else: self.append_colored(f"🤲 There's no \"{typed_raw}\" here, {self.player.name}. You're grabbing at stuff that doesn't exist again.\n", "error"); self.root.bell()
            else: self.get_first_available_item()
            return
        elif command == "give":
            if len(parts) < 2: self.append_colored("Give what? Usage: give <item name>\n", "error"); self.root.bell(); return
            if not room.get("npc"): self.append_colored("🤝 " + self._quip("no_one") + "\n", "error"); self.root.bell(); return
            typed_raw = " ".join(parts[1:]).strip(); inv_match = self._find_item_in_list(typed_raw, p.inventory)
            if not inv_match: self.append_colored("🎒 " + self._quip("dont_have", typed_raw) + "\n", "error"); self.root.bell(); return
            npc = room["npc"]; item_to_give = inv_match
            # ===== Giving to me: only the current chapter's find-item, and only on the deliver step. =====
            if getattr(npc, "is_rick", False):
                step = self._cur_step()
                if step and step["kind"] == "deliver_rick":
                    ch = EXTENDED_QUESTS[step["ci"]]
                    if self._normalize_text(item_to_give) == self._normalize_text(ch["item"]):
                        self.root.bell(); p.inventory.remove(item_to_give); self._install_core_part(ch); return
                self.append_colored(f'Rick waves you off. "I don\'t need {self._np(item_to_give, True)} right now, {self.player.name}."\n', "lore"); return
            # ===== Giving to a chapter character: only my gadget, and only on the deliver step. =====
            if not npc.is_subquest:
                step = self._cur_step()
                if step and step["kind"] == "deliver_char" and npc.name == step.get("to"):
                    ch = EXTENDED_QUESTS[step["ci"]]
                    if self._normalize_text(item_to_give) == self._normalize_text(ch["rick_gift"]):
                        self.root.bell(); p.inventory.remove(item_to_give)
                        self.append_colored(self._q(ch["char_need"]) + "\n", "quest")
                        self._advance_step(); self.grant_xp(10, "delivered Rick's gadget"); self.update_info_display(); return
                self.append_colored(f"{npc.name} doesn't need {self._np(item_to_give, True)} right now.\n", "lore"); return
            # ===== Side quest: hand over the NEED item to score a unique crafting reward. =====
            subq = npc.subqdata
            if self._normalize_text(item_to_give) == self._normalize_text(subq["need_item"]):
                if npc.name.lower() in p.subquest_ack: self.append_colored(f"{npc.name} already thanked you.\n", "lore"); return
                self.root.bell(); p.inventory.remove(item_to_give); p.subquest_ack.add(npc.name.lower()); room["subquest_done"] = True
                reward = subq["reward_item"]; p.crafting_materials.append(reward)
                self.append_colored(f"{npc.name} {subq['reward_line']}\n", "achievement")
                self.append_colored(f"🧩 You received a unique crafting piece: {reward}.\n", "success")
                self.grant_xp(20, "side quest complete"); self.update_info_display(); check_achievements(p, self.world, self); return
            else:
                self.append_colored(f'{npc.name}: "That\'s not my {subq["need_item"]}."\n', "lore"); return
        elif command == "use":
            if len(parts) < 2: self.append_colored("❌ Use what?\n", "error"); self.root.bell(); return
            typed_raw = " ".join(parts[1:]).strip(); inv_match = self._find_item_in_list(typed_raw, p.inventory)
            if self._normalize_text(typed_raw) in {"energy cell", "energy cells"}:
                item_name = "Energy Cell"; source = None
                if item_name in p.inventory: p.inventory.remove(item_name); source = "inventory"
                elif item_name in p.crafting_materials: p.crafting_materials.remove(item_name); source = "parts"
                if source:
                    charge_gain = 10;
                    if p.pclass == "Dark Matter Cell": charge_gain += 5; self.append_colored("🔧 Dark Matter Cell supercharge. That cell kicks harder (+5).\n", "success")
                    before = p.charge; p.charge = min(p.max_charge, p.charge + charge_gain); gained = p.charge - before
                    self.append_colored(f"🔋 You slot an Energy Cell ({source}). Charge +{gained}.\n", "success"); self.update_info_display(); return
                else: self.append_colored("❌ You don’t have an Energy Cell.\n", "error"); self.root.bell(); return
            if self._normalize_text(typed_raw) in {"healing serum", "serum"}:
                if "Healing Serum" in p.inventory:
                    p.inventory.remove("Healing Serum"); heal_amount = 10
                    if p.pclass == "Dark Matter Cell": heal_amount += 5; self.append_colored("🔬 Dark Matter Cell: enhanced Healing Serum!\n", "success")
                    if p.plumbus_pro_active: heal_amount += 5; self.append_colored("🔧 Plumbus Pro perk: it hits harder.\n", "success")
                    old_hp = p.hp; p.hp = min(p.max_hp, p.hp + heal_amount); gained = p.hp - old_hp
                    self.append_colored(f"💉 You inject a healing serum and regain {gained} HP! (Now at {p.hp}/{p.max_hp})\n", "success"); self.update_info_display(); return
                else: self.append_colored("You don't have a healing serum.\n", "error"); self.root.bell(); return
            
            # Meeseeks Box: instant kill on anything that isn't a boss. Existence is pain, etc.
            if self._normalize_text(typed_raw) == "meeseeks box":
                if "Meeseeks Box" not in p.inventory:
                    self.append_colored("You don't have a Meeseeks Box.\n", "error")
                    return
                monster = room.get("monster")
                if not monster:
                    self.append_colored(
                        "'I'm Mr. Meeseeks, look at me! What's the task?!' ...There's nothing to fight here.\n",
                        "lore"
                    )
                    return
                # Block it on boss monsters. No cheesing the big guys.
                if getattr(monster, "is_boss", False):
                    self.append_colored(
                        "'Ooh, that's a tough one! I don't think I can do that!' "
                        "The Meeseeks poofs out of existence in a cloud of logic failure.\n",
                        "error"
                    )
                    p.inventory.remove("Meeseeks Box")
                    return
                self.append_colored(
                    "'I'M MR. MEESEEKS, LOOK AT ME!' A blue creature appears. "
                    "'YOUR TASK IS TO DESTROY THAT GUY!'\n",
                    "achievement"
                )
                self.append_colored(
                    f"'CAAAAAN DO!' The Meeseeks obliterates the {monster.name} and vanishes with a cheerful 'ALL DONE!'\n",
                    "success"
                )
                p.inventory.remove("Meeseeks Box")
                room["monster"] = None
                room["last_defeated_monster"] = monster.name
                prev_total = p.monsters_defeated
                p.monsters_defeated += 1
                if not getattr(monster, "hidden", False):
                    p.placed_monsters_defeated += 1
                self._cascade_hidden_spawns(prev_total, p.monsters_defeated)
                self.update_info_display()
                self.print_room()
                return
            if inv_match:
                self.use_item(inv_match, room)
                return
            else:
                self.append_colored("🎒 " + self._quip("dont_have", typed_raw) + "\n", "error")
                self.root.bell()
                return
        elif command == "craft":
            if len(parts) < 2: self.append_colored("❌ Craft what? Available recipes: " + ", ".join(CRAFTING_RECIPES.keys()) + "\n", "error"); self.root.bell(); return
            recipe_name = " ".join(parts[1:]).title(); success, result, consumed_materials = craft_item(recipe_name, p.crafting_materials, p.pclass)
            if success:
                if not consumed_materials and p.pclass == "Fabricator Drone": self.append_colored("⚙️ Fabricator Drone kicks in. Materials not consumed!\n", "success")
                self.root.bell()
                p.inventory.append(recipe_name); p.items_crafted += 1; p.total_items_collected += 1; p.crafted_recipes.add(recipe_name); self.append_colored(f"🔨 Successfully crafted: {recipe_name}!\n", "success")
                self.append_colored(f"   Effect: {result['effect']}\n", "achievement")
                self._apply_post_craft_effects(recipe_name)
                self._recalc_passives(); self.update_info_display(); self.update_enhanced_map(); self.update_minimap(); check_achievements(p, self.world, self)
            else: self.append_colored("🔧 " + self._quip("cant_craft", recipe_name) + f" ({result})\n", "error"); self.root.bell(); return
            return
        elif command in ["help", "h", "?"]: self.show_enhanced_help(); return
        elif command in ["look", "examine", "l"]:
            if (len(parts) == 1 and room.get("special_interactions") and any(inter.startswith("look") for inter in room["special_interactions"])): self.handle_special_interaction("look", room); return
            if len(parts) > 1: self.examine_target(" ".join(parts[1:]), room)
            else: self.print_room(); return
            return
        elif command in ["eat", "observe", "play", "tinker", "negotiate", "listen",
                         "scavenge", "haggle", "examine", "investigate", "call",
                         "harvest", "order", "bribe", "connect"]:
            self.handle_special_interaction(command, room)
            return
        elif command in ["stats", "status"]:
            self.show_detailed_stats()
            return
        elif command == "map": self.toggle_map(); return
        elif command == "journal": self.toggle_journal(); return
        elif command == "achievements": self.toggle_achievements(); return
        elif command == "save": self.save_game(); return
        elif command == "load": self.load_game(); return
        elif command == "sense":
            if p.race == "Recon Visor":
                mana_cost = 2
                range_limit = 999
            else:
                self.append_colored("You need the Recon Visor equipped to sense a room.\n", "error")
                self.root.bell()
                return
            
            if len(parts) < 3: self.append_colored("Usage: sense <col> <row> (e.g. sense C 4)", "error"); self.root.bell(); return
            try: tx, ty = parse_coord(parts[1]), parse_coord(parts[2])
            except (ValueError, IndexError): self.append_colored("Invalid coordinates.", "error"); self.root.bell(); return
            
            if abs(tx - x) > range_limit or abs(ty - y) > range_limit: self.append_colored("Scan target is outside operational range.", "error"); self.root.bell(); return
            if (tx, ty) not in self.world: self.append_colored("There's no room at those coordinates.", "error"); self.root.bell(); return
            if p.charge < mana_cost: self.append_colored(f"❌ Not enough charge to use scan. Needs {mana_cost} Charge.", "error"); self.root.bell(); return
            p.charge -= mana_cost; self.append_colored(f"🔭 Scan results for {to_letter_number(tx,ty)}:\n", "lore")
            self.append_colored(self.world[(tx, ty)].get("desc", "Mysterious space") + "\n", "lore")
            self.update_info_display(); return
        elif command == "hint": self.show_hint(); return
        elif command == "quest":
            self.show_hint(); return
        elif command in ("search", "discover_lore") or (command == "discover" and len(parts) > 1 and parts[1] == "lore"):
            self.discover_lore()
            return
        elif command == "portal_jump": self._handle_portal_jump(parts); return
        elif command in ["inventory", "inv", "i"]:
            self.show_inventory()
            return
        
        self.append_colored("❌ " + self._quip("unknown", cmd) + "\n", "error"); self.root.bell()
        
    def _strip_found_sentence(self, room, item_name):
        aa = a_or_an(item_name)
        patterns = [
            f" You notice {aa} {item_name} here.",
            f" You notice a {item_name} here.",
            f" You notice an {item_name} here.",
            # The 'glinting' spelling variants, in case some text uses 'em. Covering my bases.
            f" You notice {aa} {item_name} glinting here.",
            " Something glints here…", " Something unusual lies here…",
        ]
        for p in patterns:
            if p in room["desc"]:
                room["desc"] = room["desc"].replace(p, ""); break
        # I remember what got cleared out of here so the room can show a faded little note later.
        room.setdefault("looted", [])
        if item_name not in room["looted"]:
            room["looted"].append(item_name)
    def get_specific_item(self, item_name):
        x, y = self.player.x, self.player.y; room = self.world[(x, y)]
        if item_name not in room["items"]: self.append_colored(f"❌ {item_name} is not here to pick up.\n", "error"); return
        if item_name == "Federation Credits":
            credits_amount = random.randint(5, 15)
            if any(a.name == "Schmeckle Millionaire" and a.unlocked for a in ACHIEVEMENTS):
                credits_amount += (credits_amount // 10) * 2
            self.player.federation_credits += credits_amount
            room["items"].remove("Federation Credits"); self._strip_found_sentence(room, "Federation Credits"); self.player.total_items_collected += 1
            self._recalc_passives(); self.update_enhanced_map(); self.print_room()
            self.append_colored(f"💰 You collect {credits_amount} Federation Credits. Total: {self.player.federation_credits}\n", "success")
            self.grant_xp(1, "collected Federation Credits")
            check_achievements(self.player, self.world, self)
            return
        is_material = self._is_crafting_material(item_name)
        if is_material: self.player.crafting_materials.append(item_name)
        else: self.player.inventory.append(item_name)
        room["items"].remove(item_name); self._strip_found_sentence(room, item_name); self.player.total_items_collected += 1
        is_main_quest_item = item_name in [q["item"] for q in EXTENDED_QUESTS]
        if is_main_quest_item: msg, tag, bonus_xp = f"✨ You pocket {self._np(item_name)}.", "lore", 3
        elif item_name == "Plumbus": self.player.plumbuses_collected += 1; msg, tag, bonus_xp = f"✨ You pocket {self._np(item_name)}. Everyone has one!", "achievement", 1
        elif item_name == "Mega Seed": msg, tag, bonus_xp = f"🧠 You carefully pick up {self._np(item_name)}. Extreme intelligence awaits!", "achievement", 1
        elif is_material: msg, tag, bonus_xp = f"💎 You collect {self._np(item_name)} for crafting!", "success", 1
        else: msg, tag, bonus_xp = f"🎒 You pick up {self._pickup_phrase(item_name)}.", "success", 1
        self._recalc_passives(); self.update_enhanced_map()
        # Re-render the room FIRST, now that the item's gone, so the confirmation I print
        # next doesn't get wiped out by print_room nuking the screen. Order matters, Morty.
        self.print_room()
        self.append_colored(msg + "\n", tag)
        self.grant_xp(bonus_xp, f"collected {item_name}")
        check_achievements(self.player, self.world, self)
    def get_first_available_item(self):
        room = self.world[(self.player.x, self.player.y)]
        if not room["items"]: self.append_colored("🤲 " + self._quip("nothing_to_take") + "\n", "error"); return
        item = room["items"][0]; self.get_specific_item(item)
    def _cur_step(self):
        si = self.player.step_idx
        return MAIN_STEPS[si] if 0 <= si < len(MAIN_STEPS) else None

    def _advance_step(self):
        self.player.step_idx += 1
        # quest_idx tracks completed CHAPTERS (4 steps each) for the map, journal, achievements,
        # and info display, all of which I wrote against it. Don't go redefining it on me.
        self.player.quest_idx = self.player.step_idx // STEPS_PER_CHAPTER

    def handle_rick_dialog(self, npc):
        p = self.player; step = self._cur_step()
        if step is None:
            self._staged_chat("Rick:complete", RICK_CHAT["complete"]); return
        ch = EXTENDED_QUESTS[step["ci"]]; kind = step["kind"]; ci = step["ci"]
        repl = {"{gift}": ch["rick_gift"], "{character}": ch["character"], "{item}": ch["item"]}
        if kind == "talk_rick":
            if step["ci"] == 0 and not p.objective_shown:
                self.append_colored("🌀 THE MISSION:\n" + GAME_OBJECTIVE + "\n\n", "quest")
                p.objective_shown = True
            gift = ch["rick_gift"]
            if not self._find_item_in_list(gift, p.inventory): p.inventory.append(gift)
            self.append_colored(self._q(ch["rick_send"]) + "\n", "quest")
            self.append_colored(f"📦 Rick hands you: {gift}. Take it to {ch['character']}.\n", "success")
            self._advance_step(); self.grant_xp(5, "briefed by Rick"); self.update_info_display(); check_achievements(p, self.world, self)
        elif kind == "deliver_char":
            self._staged_chat(f"Rick:deliver_char:{ci}", RICK_CHAT["deliver_char"], repl=repl)
        elif kind == "retrieve":
            self._staged_chat(f"Rick:retrieve:{ci}", RICK_CHAT["retrieve"], repl=repl)
        elif kind == "deliver_rick":
            if self._find_item_in_list(ch["item"], p.inventory):
                self._staged_chat(f"Rick:rick_haveitem:{ci}", RICK_CHAT["rick_haveitem"], tag="quest", repl=repl)
            else:
                self._staged_chat(f"Rick:rick_noitem:{ci}", RICK_CHAT["rick_noitem"], repl=repl)

    def _staged_line(self, key, story, cycle):
        # Hands back the next line of a conversation: the story beats once, a line per talk,
        # then I cycle the filler at random so nobody repeats themselves. Saved per key. Obviously.
        p = self.player
        if getattr(p, "chat_stage", None) is None: p.chat_stage = {}
        if getattr(p, "chat_lastcycle", None) is None: p.chat_lastcycle = {}
        idx = p.chat_stage.get(key, 0)
        if idx < len(story):
            p.chat_stage[key] = idx + 1; return story[idx]
        if not cycle: return story[-1] if story else ""
        last = p.chat_lastcycle.get(key, -1)
        choices = [i for i in range(len(cycle)) if i != last] or list(range(len(cycle)))
        pick = random.choice(choices); p.chat_lastcycle[key] = pick; return cycle[pick]

    def _staged_chat(self, key, data, tag="lore", repl=None):
        line = self._staged_line(key, data.get("story", []), data.get("cycle", []))
        if repl:
            for k, v in repl.items(): line = line.replace(k, v)
        self.append_colored(line.replace("{pc}", self.player.name) + "\n", tag)

    def _prequest_chat(self, npc):
        # Morty walked up to somebody before I sent him. They run their bit once, a line per
        # talk, then cycle three different "go bug Rick" brush-offs at random. Never the same one
        # twice in a row, because I'm not a hack.
        p = self.player
        data = NPC_PREQUEST_CHAT.get(npc.name)
        if not data:
            self.append_colored(f'{npc.name} eyes you. "Rick hasn\'t sent you my way yet, kid. Come back when he does."\n', "lore"); return
        if getattr(p, "npc_chat_progress", None) is None: p.npc_chat_progress = {}
        if getattr(p, "npc_chat_last_end", None) is None: p.npc_chat_last_end = {}
        intro = data["intro"]; idx = p.npc_chat_progress.get(npc.name, 0)
        if idx < len(intro):
            line = intro[idx]; p.npc_chat_progress[npc.name] = idx + 1
        else:
            endings = data["endings"]; last = p.npc_chat_last_end.get(npc.name, -1)
            choices = [i for i in range(len(endings)) if i != last] or list(range(len(endings)))
            pick = random.choice(choices); p.npc_chat_last_end[npc.name] = pick; line = endings[pick]
        self.append_colored(line.replace("{pc}", p.name) + "\n", "lore")

    def handle_chapter_char_dialog(self, npc):
        p = self.player; step = self._cur_step(); ci = npc.quest_idx; ch = EXTENDED_QUESTS[ci]
        sc = STORY_CHAT.get(npc.name, {})
        if step is None or ci < step["ci"]:
            if "done" in sc: self._staged_chat(f"{npc.name}:done", sc["done"])
            else: self.append_colored(f'{npc.name}: "We\'re square. Tell Rick he still owes me."\n', "lore")
            return
        if ci > step["ci"]:
            self._prequest_chat(npc); return
        kind = step["kind"]
        if kind == "talk_rick":
            self._prequest_chat(npc)
        elif kind == "deliver_char":
            if self._find_item_in_list(ch["rick_gift"], p.inventory):
                if "arrive" in sc: self._staged_chat(f"{npc.name}:arrive", sc["arrive"], tag="quest", repl={"{gift}": ch["rick_gift"]})
                else: self.append_colored(f'{npc.name}: "You holding something from Rick? Hand it over."\n', "quest")
            else:
                self.append_colored(f'{npc.name}: "Rick was supposed to send a {ch["rick_gift"]}. No gift, no help."\n', "lore")
        elif kind == "retrieve":
            if "retrieve" in sc: self._staged_chat(f"{npc.name}:retrieve", sc["retrieve"], tag="quest", repl={"{item}": ch["item"]})
            else: self.append_colored(self._q(ch["char_need"]) + "\n", "quest")
        elif kind == "deliver_rick":
            if "to_rick" in sc: self._staged_chat(f"{npc.name}:to_rick", sc["to_rick"], repl={"{item}": ch["item"]})
            else: self.append_colored(f'{npc.name}: "You got the {ch["item"]}? That\'s Rick\'s headache now. Go see him."\n', "lore")

    def _install_core_part(self, ch):
        p = self.player
        self.append_colored(self._q(ch["rick_install"]) + "\n", "achievement")
        p.motif_puzzles_solved += 1; self.grant_xp(50, "OMNI-CORE part installed")
        self._advance_step()
        if self._cur_step() is None:
            self.handle_game_completion()
        else:
            check_achievements(p, self.world, self)
            self.append_colored(f'Rick: "One part down. Talk to me when you\'re ready for the next, {self.player.name}."\n', "lore")
        self.update_info_display()

    def handle_subquest_dialog(self, npc, room):
        p = self.player; subq = npc.subqdata; name = npc.name
        p.subquest_met.add(name.lower())
        sc = SIDEQUEST_CHAT.get(name, {})
        if name.lower() in p.subquest_ack:
            if "done" in sc: self._staged_chat(f"{name}:sq_done", sc["done"], tag="success")
            else: self.append_colored(f'😊 {name}: "Thanks again, {p.name}!"\n', "success")
            return
        if self._find_item_in_list(subq["need_item"], p.inventory):
            if "have" in sc: self._staged_chat(f"{name}:sq_have", sc["have"], tag="quest")
            else: self.append_colored(f'{name}: {subq["give_line"]}\n', "quest")
        else:
            if "need" in sc:
                key = f"{name}:sq_need"
                stage = getattr(p, "chat_stage", None) or {}
                in_cycle = stage.get(key, 0) >= len(sc["need"]["story"])
                self._staged_chat(key, sc["need"], tag="lore")
                if in_cycle:
                    self.append_colored(f"   (Hint: {subq['key_hint']})\n", "quest")
            else:
                self.append_colored(f"❓ {name}: {subq['lost_line']}\n", "lore")
                self.append_colored(f"   (Hint: {subq['key_hint']})\n", "quest")
        p.subquest_heard.add(name.lower())
        if p.pclass == "Universal Translator" and random.random() < 0.30:
            if random.choice([True, False]): heal_amount = random.randint(3, 7); p.hp = min(p.max_hp, p.hp + heal_amount); self.append_colored(f"🤝 Your diplomatic charm earns you {heal_amount} HP from {name}!\n", "success")
            else: charge_gain = random.randint(2, 5); p.charge = min(p.max_charge, p.charge + charge_gain); self.append_colored(f"🤝 Your smooth talk restores {charge_gain} Charge from {name}!\n", "success")
            self.update_info_display()
    def handle_game_completion(self):
        # OMNI-CORE's built, so the STORY's done, but maybe not the game. If Morty's still got
        # achievements, side quests, or gadgets hanging, I toss him the stats and let him keep
        # going. The real ending only fires once he's done EVERYTHING. See _maybe_true_ending.
        self.append_colored("\n" + "="*60 + "\n", "achievement")
        self.append_centered("THE OMNI-CORE IS COMPLETE\n", "banner")
        self.append_colored("="*60 + "\n", "achievement")
        self.append_colored(
            "Rick snaps the Singularity Heart into place. The OMNI-CORE thrums, five stolen "
            "wonders humming as one. No tiny civilization to unionize, no Zeep to one-up him. "
            "Strike-proof, guilt-free, infinite power.\n", "lore")
        self.append_colored(
            f"'We did it, {self.player.name},' Rick burps. 'Real talk, you fetched, you fought, you didn't die. "
            "Color me moderately impressed.'\n", "quest")
        self.append_colored(
            "He carries the OMNI-CORE past the dead Microverse Battery... and plugs it straight into "
            "his interdimensional cable box.\n\n", "lore")
        self.append_colored(
            "'...Rick, that's a UNIVERSE of infinite power. For your CABLE?'\n", "lore")
        self.append_colored(
            f"'I'm never paying that bill again, {self.player.name}. Priorities. Now get schwifty, there's a "
            "season finale on in nine thousand dimensions at once.'\n\n", "lore")
        self.append_colored(
            "Across the multiverse, President Morty notes the new power signature, smiles, and files "
            "it away for later.\n", "success")
        # Light up the end-game achievements now, but I'm holding the real ending till I decide.
        self._suppress_true_ending = True
        check_achievements(self.player, self.world, self)
        self._suppress_true_ending = False
        if self._is_fully_complete():
            # He saved the main quest for dead last? Fine. Straight to the real ending with him.
            self._true_ending(); return
        # Still got stuff to do. Show the run so far, point him at 100, leave the keyboard on.
        self._show_run_stats("📊 MAIN QUEST STATISTICS:")
        left = self._completion_remaining()
        self.append_colored("\n" + "="*60 + "\n", "quest")
        self.append_colored(
            f"The main story's done, {self.player.name}, but you haven't squeezed this multiverse dry yet. "
            "Rick wanders off to enjoy his cable. You're free to keep poking around.\n", "lore")
        self.append_colored("Still on the board before you've truly 100%'d it:\n", "quest")
        self.append_colored(f"   Achievements:    {left['ach_done']}/{left['ach_total']}\n")
        self.append_colored(f"   Side quests:     {left['sq_done']}/{left['sq_total']}\n")
        self.append_colored(f"   Intel fragments: {left['intel_done']}/{left['intel_total']}\n")
        self.append_colored(f"   Gadgets crafted: {left['craft_done']}/{left['craft_total']}\n")
        self.append_colored(
            "Finish every last one and Rick might just say something he'll regret. Keep going.\n", "success")
        self.update_info_display()

    def _compute_max_total_kills(self, placed, pool_size):
        # Every third kill (ANY kind) pops one more hidden enemy, and killing those counts toward the
        # next three too. So the absolute ceiling is the fixed point of M = placed + floor(M/3),
        # roughly one and a half times the placed count, capped by how many new creatures I packed.
        total = 0; available = placed; hidden_left = pool_size
        while available > 0:
            available -= 1; total += 1
            if total % 3 == 0 and hidden_left > 0:
                available += 1; hidden_left -= 1
        return total

    def _init_hidden_enemy_system(self):
        # Called the second a new game begins. Snapshot how many enemies I planted, shuffle the bag of
        # hidden ones, and work out the max kills this run could ever produce.
        p = self.player
        placed = sum(1 for rm in self.world.values() if rm.get("monster") and not getattr(rm["monster"], "hidden", False))
        p.placed_enemy_count = placed
        p.placed_monsters_defeated = 0
        p.hidden_pool = list(HIDDEN_ENEMIES); random.shuffle(p.hidden_pool)
        p.max_total_kills = self._compute_max_total_kills(placed, len(HIDDEN_ENEMIES))

    def _hidden_candidate_rooms(self, exclude=()):
        # Every legal landing spot for a hidden enemy: a room you've already revealed, totally empty, out
        # of the hub safety bubble, and not crowding another monster. Same rules I use at world-gen. The
        # player's current tile and the hub are always off-limits; pass extra rooms in 'exclude' to skip.
        p = self.player
        SAFE_RADIUS = 2
        def m_dist(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
        placed_positions = [pos for pos, rm in self.world.items() if rm.get("monster")]
        banned = set(exclude); banned.add((1, 1)); banned.add((p.x, p.y))
        candidates = []
        for pos, rm in self.world.items():
            if pos in banned: continue                          # hub, your tile, or anything I was told to skip
            if not rm.get("visited"): continue                  # only on rooms you've actually revealed
            if rm.get("npc") or rm.get("monster") or rm.get("items") or rm.get("motif") is not None: continue  # fully empty only
            if m_dist(pos, (1, 1)) <= SAFE_RADIUS: continue      # respect the home safe zone
            if any(m_dist(pos, mp) < 2 for mp in placed_positions): continue  # same spacing as gen, no clumping
            candidates.append(pos)
        return candidates

    def _spawn_hidden_enemy(self):
        # Drop ONE hidden ambusher onto an already-revealed, totally empty room, using the same rules I
        # use at world-gen: stay out of the hub's safety bubble and never crowd another monster. No
        # marker goes on the map, so the room still looks empty until Morty blunders in. Returns whether
        # one actually landed (it won't if the bag's empty or there's no legal revealed room yet).
        p = self.player
        pool = getattr(p, "hidden_pool", None)
        if not pool: return False  # Bag's empty. I never repeat a creature, so that's that.
        candidates = self._hidden_candidate_rooms()
        if not candidates: return False  # Nowhere legal that you've revealed yet. Skip it; the math still holds as a ceiling.
        pos = random.choice(candidates)
        name, base_hp, base_dmg, desc = pool.pop()
        diff_mod = DIFFICULTY_MODIFIERS[p.difficulty]
        hp = max(1, int(base_hp * diff_mod["monster_hp_mult"]))
        dmg = max(1, int(base_dmg * diff_mod["monster_damage_mult"]))
        # Loot stays empty on purpose; the Credits get handed out on the kill so they never count as a
        # collected item or feed any achievement. These give nothing the game needs.
        self.world[pos]["monster"] = Monster(name, hp, hp, dmg, [], desc, hidden=True)
        return True

    def _cascade_hidden_spawns(self, prev_total, new_total):
        # One hidden enemy for every NEW multiple of three total kills crossed this turn. Killing a
        # hidden one bumps the total too, so the chain keeps itself going.
        spawns = (new_total // 3) - (prev_total // 3)
        landed = 0
        for _ in range(max(0, spawns)):
            if self._spawn_hidden_enemy(): landed += 1
            else: break
        if landed:
            self.update_enhanced_map(); self.update_minimap()

    def _show_run_stats(self, header):
        p = self.player
        self.append_colored("\n" + header + "\n", "quest")
        self.append_colored(f"   Moves taken: {p.moves_taken}\n")
        self.append_colored(f"   Enemies defeated: {p.monsters_defeated} (max possible this run: {getattr(p, 'max_total_kills', 0) or p.monsters_defeated})\n")
        self.append_colored(f"   Items crafted: {p.items_crafted}\n")
        self.append_colored(f"   Lore fragments: {len(p.lore_fragments)}\n")
        self.append_colored(f"   Difficulty: {p.difficulty.value.title()}\n")

    def _completion_remaining(self):
        p = self.player
        return {
            "ach_done": sum(1 for a in ACHIEVEMENTS if a.unlocked), "ach_total": len(ACHIEVEMENTS),
            "sq_done": len(p.subquest_ack), "sq_total": len(EXTENDED_SUBQUESTS),
            "craft_done": len(set(CRAFTING_RECIPES) & getattr(p, "crafted_recipes", set())), "craft_total": len(CRAFTING_RECIPES),
            "intel_done": len(p.lore_fragments), "intel_total": getattr(self, "total_lore_fragments_count", 0),
        }

    def _is_fully_complete(self):
        p = self.player
        # The journal's own tabs count toward 100, right next to achievements and crafts.
        if p.quest_idx < len(EXTENDED_QUESTS): return False                          # journal: my main story
        if len(p.subquest_ack) < len(EXTENDED_SUBQUESTS): return False                # journal: the side gigs
        if len(p.lore_fragments) < getattr(self, "total_lore_fragments_count", 0): return False  # journal: every scrap of intel
        if not all(a.unlocked for a in ACHIEVEMENTS): return False                    # all my achievements
        if not set(CRAFTING_RECIPES).issubset(getattr(p, "crafted_recipes", set())): return False  # every gadget on the bench
        return True

    def _maybe_true_ending(self):
        # check_achievements pokes this after just about everything. The second Morty finishes
        # the very last thing, the real ending fires. Once. I'm not doing an encore.
        if getattr(self, "_suppress_true_ending", False): return
        p = self.player
        if getattr(p, "true_ending_shown", False): return
        if not self._is_fully_complete(): return
        p.true_ending_shown = True
        self._true_ending()

    def _true_ending(self):
        p = self.player
        p.true_ending_shown = True
        self.append_colored("\n" + "="*60 + "\n", "achievement")
        self.append_centered("100%  -  NOTHING LEFT UNDONE\n", "banner")
        self.append_colored("="*60 + "\n", "achievement")
        self.append_colored(
            f"That's it, {p.name}. Every part, every quest, every scrap of intel, every gadget on the "
            "bench, every favor owed across the whole multiverse. The board is empty. There is nothing "
            "left to fetch.\n", "lore")
        self.append_colored(
            "Rick sets the flask down. For once he doesn't burp, doesn't deflect, doesn't change the "
            "subject. He just looks at you.\n", "lore")
        self.append_colored(
            f"'...You actually did everything. Every dumb little errand, every side thing nobody made you "
            f"finish. Most Mortys tap out after the main quest.' He almost smiles. 'You're a good Morty, "
            f"{p.name}. The good one.'\n", "quest")
        self.append_colored(
            "He musses your hair, which is about as much affection as Rick can manage without a portal gun "
            "in the other hand. *buuurp* 'Don't let it go to your head.'\n\n", "lore")
        self._show_run_stats("📊 FINAL STATISTICS:")
        self.append_colored(f"   Achievements: {len(ACHIEVEMENTS)}/{len(ACHIEVEMENTS)}\n")
        self.append_colored(f"   Side quests: {len(EXTENDED_SUBQUESTS)}/{len(EXTENDED_SUBQUESTS)}\n")
        self.append_colored(f"   Gadgets crafted: {len(CRAFTING_RECIPES)}/{len(CRAFTING_RECIPES)}\n\n")
        self.append_centered("YOU 100%'D THE MULTIVERSE, MORTY.\n", "banner")
        self.append_centered("--- THE END. NOW GO TOUCH SOME GRASS. ---\n", "banner")
        try: self.entry.config(state="disabled")
        except Exception: pass
    def _apply_post_craft_effects(self, recipe_name):
        # Special on-build effects, shared by the popup AND the typed `craft` command so the two can
        # never drift apart again (which is exactly how the injector ended up half-built before).
        # Building the Mega Seed Injector is itself one safe dose: it flips Mega Seeds into usable
        # items, drags any you already had out of the crafting pile, and counts as using a seed.
        p = self.player
        if recipe_name == "Mega Seed Injector":
            p.max_charge += 10; p.charge = p.max_charge; p.hp = max(1, p.hp - 5); p.mega_seeds_used += 1
            p.mega_seed_injector_built = True
            self.append_colored("🧠 Mega Seed Injector boosts max charge by 10 but causes nausea (lose 5 HP)!\n", "achievement")
            self.append_colored("🌱 Injector online. Mega Seeds are usable items now, not crafting parts.\n", "lore")
        elif recipe_name == "Interdimensional Goggles":
            for pos, rm in self.world.items():
                if rm.get("npc") or rm.get("monster") or rm.get("items") or rm.get("motif") is not None: rm["visited"] = True
            self.append_colored("🌌 Interdimensional Goggles reveal every special room!\n", "achievement"); self.update_enhanced_map()

    def use_item(self, item_name, room):
        p = self.player
        if item_name not in p.inventory: self.append_colored(f"❌ You don't have {self._np(item_name)} in your inventory.\n", "error"); self.root.bell(); return
        if item_name == "Mega Seed":
            p.inventory.remove(item_name); p.mega_seeds_used += 1; mana_boost = 5; hp_loss = 10
            p.max_charge = min(p.max_charge + mana_boost, 999); p.charge = min(p.charge + mana_boost, p.max_charge); p.hp = max(1, p.hp - hp_loss)
            self.append_colored(f"🧠 You directly consume the Mega Seed! Your Max Charge permanently increases by {mana_boost}, but you lose {hp_loss} HP.\n", "success")
            check_achievements(p, self.world, self); self.update_info_display(); return
        if item_name in CRAFTING_RECIPES:
            recipe = CRAFTING_RECIPES[item_name]; self.append_colored(f"🔮 You activate {self._np(item_name)}!\n", "success"); self.append_colored(f"✨ {recipe['effect']}\n", "achievement")
            if item_name == "Mega Seed Injector":
                if "Mega Seed" in p.inventory:
                    p.inventory.remove("Mega Seed"); p.mega_seeds_used += 1; mana_boost = 10; hp_loss = 5
                    p.max_charge = min(p.max_charge + mana_boost, 999); p.charge = min(p.charge + mana_boost, p.max_charge); p.hp = max(1, p.hp - hp_loss)
                    self.append_colored(f"🧠 The injector safely administers a Mega Seed! Max Charge +{mana_boost}, lose {hp_loss} HP.\n", "success")
                    check_achievements(p, self.world, self)  # The injector is a reusable device; it stays in your bag.
                else: self.append_colored("🌱 The injector's ready, but you've got no Mega Seed loaded. Find or buy one, then use it again.\n", "error"); self.root.bell(); return
            elif item_name == "Schmeckle Converter":
                if p.federation_credits >= 5:
                    p.federation_credits -= 5; available_materials = [mat for recipe_data in CRAFTING_RECIPES.values() for mat in recipe_data["materials"]]
                    new_material = random.choice(available_materials); p.total_items_collected += 1
                    if new_material == "Mega Seed" and getattr(p, "mega_seed_injector_built", False): p.inventory.append(new_material)
                    else: p.crafting_materials.append(new_material)
                    self.append_colored(f"♻️ Converter produces {self._np(new_material)}! Lost 5 Credits.\n", "success"); p.inventory.remove(item_name)
                else: self.append_colored("❌ Need 5 Federation Credits to use the Schmeckle Converter.\n", "error"); self.root.bell(); return
            elif item_name == "Interdimensional Goggles":
                for pos, rm in self.world.items():
                    if rm.get("npc") or rm.get("monster") or rm.get("items") or rm.get("motif") is not None: rm["visited"] = True; p.visited.add(pos); p.teleport_locations.add(pos)
                self.append_colored("🌌 Goggles reveal all key locations on your map!\n", "success"); self.update_enhanced_map(); self.update_minimap(); p.inventory.remove(item_name)
            elif item_name == "Plumbus Repair Kit": p.hp = p.max_hp; p.charge = p.max_charge; self.append_colored("✨ Repair Kit restores your HP and Charge to full!\n", "success"); p.inventory.remove(item_name)
            elif item_name == "Mindblower Device":
                current_monster = room.get("monster")
                if current_monster: 
                    # Slap a strong multi-turn stun on it.
                    current_monster.stun_turns = 2
                    self.append_colored(
                        f"🧠 Mindblower scrambles the {current_monster.name}'s brain! It's out of it for a while.\n",
                        "success"
                    )
                    p.inventory.remove(item_name)
                    self.update_info_display()
                else:
                    self.append_colored("❌ No monster here.\n", "error")
                    self.root.bell()
                return
            elif item_name == "Portal Gun (Replica)": self.append_colored("🌐 To use, type 'portal_jump <X> <Y>'.\n", "lore");
            self._recalc_passives(); self.update_info_display(); return
        self.append_colored("❌ Nothing happens. Try the right place, time, and quest...\n", "error"); self.root.bell()
    def handle_special_interaction(self, command, room):
        p = self.player
        full_cmd = command.lower().strip()
        verb = full_cmd.split()[0]
        
        interaction_verbs = [v.split('_')[0].lower() for v in room.get("special_interactions", [])]
        if verb not in interaction_verbs:
            self.append_colored(f"❌ You can't {verb} anything special here.\n", "error")
            self.root.bell()
            return
        
        # Guard against a missing motif. Belt and suspenders.
        if room.get("motif") is None:
            if "hidden_lore" in room and not room.get("lore_discovered"):
                self.discover_lore()
            else:
                self.append_colored("You do that. Nothing interesting happens.\n", "lore")
            return
        
        # Okay, now it's safe:
        motif_data = EXTENDED_MOTIFS[room["motif"]]
        step = self._cur_step()
        motif_verb = _motif_verb(room["motif"])

        # ===== Main-story retrieval: only the current chapter's room, only on its retrieve step. =====
        if room.get("quest_idx") is not None:
            ci = room["quest_idx"]; ch = EXTENDED_QUESTS[ci]
            if not room.get("quest_item_revealed"):
                if step and step["kind"] == "retrieve" and step["ci"] == ci and verb == motif_verb:
                    item_name = ch["item"]; room["quest_item_revealed"] = True
                    p.inventory.append(item_name); p.total_items_collected += 1
                    self.append_colored(ch["retrieve_story"] + "\n", "achievement")
                    self.append_colored(f"🎁 You obtained: {item_name}. Take it to Rick.\n", "success")
                    self.grant_xp(15, "special action: story item"); self._advance_step()
                    self.update_info_display(); check_achievements(p, self.world, self)
                    return
                # Not the right time for this room. Rick gets on the comms and roasts you for poking it
                # early, three lines per room, fitting the room's action, random with no back-to-back repeat.
                qbarbs = motif_data.get("quest_barbs")
                if qbarbs:
                    if getattr(p, "barb_lastpick", None) is None: p.barb_lastpick = {}
                    bkey = f"quest:{room['motif']}:{ci}"
                    last = p.barb_lastpick.get(bkey, -1)
                    choices = [i for i in range(len(qbarbs)) if i != last] or list(range(len(qbarbs)))
                    pick = random.choice(choices); p.barb_lastpick[bkey] = pick
                    self.append_colored(qbarbs[pick] + "\n", "combat")
                else:
                    self.append_colored("You poke around, but nothing happens here yet. Follow the story's lead (try 'hint').\n", "lore")
                return
            # Already solved it, so fall through to whatever repeatable action's below.

        # ===== Side-quest retrieval: use the found KEY item here to spit out the NEED item. =====
        if room.get("side_idx") is not None and not room.get("subquest_done"):
            si = room["side_idx"]; subq = EXTENDED_SUBQUESTS[si]
            if verb == motif_verb:
                # You have to actually TALK to the guy first, Morty. Walking into a bar holding a
                # wad of cash and shouting "drink" does not magically teach you whose tab the
                # bartender is sitting on. No quest started means no glass. Go find the NPC.
                # And while you're wasting everyone's time, Rick has OPINIONS about it: three per
                # room, picked at random, never the same one twice in a row, because I'm not a hack.
                if subq["npc"].lower() not in p.subquest_met:
                    barbs = motif_data.get("rick_barbs") or ([motif_data["rick_barb"]] if motif_data.get("rick_barb") else [])
                    if barbs:
                        if getattr(p, "barb_lastpick", None) is None: p.barb_lastpick = {}
                        bkey = f"{room['motif']}:{si}"
                        last = p.barb_lastpick.get(bkey, -1)
                        choices = [i for i in range(len(barbs)) if i != last] or list(range(len(barbs)))
                        pick = random.choice(choices); p.barb_lastpick[bkey] = pick
                        self.append_colored(barbs[pick] + "\n", "combat")
                    else:
                        self.append_colored(f"You {verb}, but nothing special happens. Maybe there's someone around here you should talk to first.\n", "lore")
                    return
                key = subq["key_item"]; need = subq["need_item"]
                key_match = self._find_item_in_list(key, p.inventory) or self._find_item_in_list(key, p.crafting_materials)
                if key_match:
                    if key_match in p.inventory: p.inventory.remove(key_match)
                    elif key_match in p.crafting_materials: p.crafting_materials.remove(key_match)
                    p.inventory.append(need); room["subquest_done"] = True
                    self.append_colored(subq["retrieve_line"] + "\n", "achievement")
                    self.append_colored(f"🎁 You obtained: {need}. Return it to {subq['npc']}.\n", "success")
                    self.grant_xp(12, "special action: side item")
                    self.update_info_display(); check_achievements(p, self.world, self)
                    return
                else:
                    self.append_colored(f"You {verb}, but nothing comes of it. You need the {subq['key_item']} first. ({subq['key_hint']})\n", "lore"); return
        motif_data = EXTENDED_MOTIFS[room["motif"]]
        if "repeatable_action" in motif_data:
            action = motif_data["repeatable_action"]
            cost_type = action["cost_type"]
            cost_amount = action["cost_amount"]
            
            # Check whether you can pay the cost.
            if cost_type == "credits" and p.federation_credits < cost_amount:
                self.append_colored(f"You need {cost_amount} Credits to do that here. You only have {p.federation_credits}.\n", "error"); self.root.bell(); return
            elif cost_type == "material" and not p.crafting_materials:
                self.append_colored("You need at least one spare crafting material to tinker with.\n", "error"); self.root.bell(); return
                
            # Pay the cost.
            self.append_colored(action["flavor"] + "\n", "lore")
            if cost_type == "credits": p.federation_credits -= cost_amount
            elif cost_type == "material": p.crafting_materials.pop(random.randrange(len(p.crafting_materials)))
            
            self.update_info_display()
            
            # ===== Figuring out what actually happens. =====
            # Blips and Chitz: random buff, debuff, or reward. Roll the dice.
            if motif_data["motif"] == "blips_and_chitz":
                outcomes = ["buff_hp", "buff_charge", "find_credits", "get_scammed", "flavor_roy"]
                result = random.choice(outcomes)
                if result == "buff_hp":
                    p.hp = min(p.max_hp, p.hp + 5)
                    self.append_colored("You won! The machine dispenses a nutritious paste. (+5 HP)\n", "success")
                elif result == "buff_charge":
                    p.charge = min(p.max_charge, p.charge + 5)
                    self.append_colored("You hit the jackpot! The machine sparks and recharges some of your gear. (+5 Charge)\n", "success")
                elif result == "find_credits":
                    found = random.randint(1, 10)
                    p.federation_credits += found
                    self.append_colored(f"You find {found} Credits left in the coin return!\n", "success")
                elif result == "get_scammed":
                    self.append_colored("The game was rigged from the start. You get nothing.\n", "error")
                else:
                    self.append_colored("You play a game of 'Roy: A Life Well Lived'. You go back to the carpet store. What a life.\n", "lore")
                self.update_info_display()
            # Rick's Garage: tinker and walk out with a new item.
            elif motif_data["motif"] == "rick's_garage":
                outcomes = ["new_material", "consumable", "failure"]
                result = random.choice(outcomes)
                if result == "new_material":
                    new_mat = random.choice(["Rickium Alloy", "Cognitive Fabric", "Neural Processor"])
                    p.crafting_materials.append(new_mat)
                    self.append_colored(f"You successfully cobbled together a working {new_mat}!\n", "success")
                elif result == "consumable":
                    item = random.choice(["Healing Serum", "Energy Cell"])
                    p.inventory.append(item)
                    self.append_colored(f"Your tinkering accidentally creates a {item}!\n", "success")
                else:
                    self.append_colored("The parts explode in a shower of sparks, leaving behind useless slag.\n", "error")
            # Alien Market: gamble for something rare.
            elif motif_data["motif"] == "alien_market":
                if random.random() < 0.2: # 20% shot at an actually good item.
                    rare_item = random.choice(["Plumbus", "Mega Seed", "Fleeb"])
                    if rare_item == "Mega Seed" and not getattr(p, "mega_seed_injector_built", False): p.crafting_materials.append(rare_item)
                    else: p.inventory.append(rare_item)
                    self.append_colored(f"The box contains... a {rare_item}! What a steal!\n", "achievement")
                else: # 80% of the time it's junk. That's gambling, Morty.
                    self.append_colored("You open the box to find a perfectly ordinary rock. You've been scammed.\n", "error")
            return
        # ===== Fallback: generic motif response, or maybe you stumble onto some lore. =====
        # If no quest fired and no repeatable action happened, maybe you dig up some lore.
        if "hidden_lore" in room and not room.get("lore_discovered"):
            self.discover_lore()
        else:
            interaction_key = next((i for i in room["special_interactions"] if i.startswith(verb)), verb)
            responses = {"eat_cob": "You take another bite of a cob. Still corny.", "observe_ricks": "You watch the Ricks. They haven't changed.", "listen_trees": "The trees continue their endless chatter."}
            self.append_colored(responses.get(interaction_key, "You do that again. Nothing new happens.\n"), "lore")
    
    # ===== The rest of the UI and logic methods. Odds and ends. =====
    def show_inventory(self):
        p = self.player
        # GLOBAL RULE, no flags, no conditions: injector in inventory means Mega Seeds live in inventory.
        # Physically MOVE them out of crafting parts right here, every time you open your bag.
        if "Mega Seed Injector" in p.inventory:
            p.mega_seed_injector_built = True
            while "Mega Seed" in p.crafting_materials:
                p.crafting_materials.remove("Mega Seed"); p.inventory.append("Mega Seed")
        self._recalc_passives()
        quest_items_set = {q["item"] for q in EXTENDED_QUESTS} | {q["rick_gift"] for q in EXTENDED_QUESTS}; subquest_items_set = {s["key_item"] for s in EXTENDED_SUBQUESTS} | {s["need_item"] for s in EXTENDED_SUBQUESTS}
        crafting_materials_set = {m for rec in CRAFTING_RECIPES.values() for m in rec["materials"] if self._is_crafting_material(m)}
        def count_list(items): counts = {}; [counts.update({it: counts.get(it, 0) + 1}) for it in items]; return counts
        inv_normal = [itm for itm in p.inventory if itm not in crafting_materials_set and itm not in quest_items_set and itm not in subquest_items_set]
        counts_normal = count_list(inv_normal); counts_quest = count_list([it for it in p.inventory if it in quest_items_set])
        counts_sub = count_list([it for it in p.inventory if it in subquest_items_set]); combined_mats = count_list(p.crafting_materials + [it for it in p.inventory if it in crafting_materials_set])
        self.append_colored("\n🎒 INVENTORY:\n", "achievement")
        if counts_normal: [self.append_colored(f"   • {it}" + (f" x{cnt}" if cnt > 1 else "") + "\n") for it, cnt in sorted(counts_normal.items())]
        else: self.append_colored("   None\n")
        self.append_colored("\n📜 MAIN-QUEST ITEMS:\n", "quest")
        if counts_quest: [self.append_colored(f"   • {it}" + (f" x{cnt}" if cnt > 1 else "") + "\n") for it, cnt in sorted(counts_quest.items())]
        else: self.append_colored("   None\n")
        self.append_colored("\n🧩 SIDE-QUEST ITEMS:\n", "achievement")
        if counts_sub: [self.append_colored(f"   • {it}" + (f" x{cnt}" if cnt > 1 else "") + "\n") for it, cnt in sorted(counts_sub.items())]
        else: self.append_colored("   None\n")
        self.append_colored("\n🔧 CRAFTING MATERIALS:\n", "achievement")
        if combined_mats: [self.append_colored(f"   • {it} x{cnt}\n") for it, cnt in sorted(combined_mats.items())]
        else: self.append_colored("   None\n")
        self.append_colored("\n💰 CURRENCY:\n", "success"); self.append_colored(f"   • Federation Credits: {p.federation_credits}\n")
    def show_detailed_stats(self):
        self.append_colored("\n📊 DETAILED STATISTICS:\n", "quest"); self.append_colored("Character: Morty\n"); self.append_colored(f"Main Gadget: {self.player.race}\n"); self.append_colored(f"Attachment: {self.player.pclass}\n"); self.append_colored(f"Universe: {self.current_save_name or "(none)"}\n")
        self.append_colored(f"Difficulty: {self.player.difficulty.value.title()}\n"); self.append_colored(f"HP: {self.player.hp}/{self.player.max_hp}\n")
        self.append_colored(f"Charge: {self.player.charge}/{self.player.max_charge}\n"); self.append_colored(f"Armor: {self.player.armor}\n"); self.append_colored(f"Damage Bonus: +{self.player.damage_bonus}\n\n")
        self.append_colored(f"Quest Progress: {self.player.quest_idx}/{len(EXTENDED_QUESTS)}\n"); self.append_colored(f"Moves Taken: {self.player.moves_taken}\n")
        self.append_colored(f"Enemies Defeated: {self.player.monsters_defeated} / {getattr(self.player, 'max_total_kills', 0) or self.player.monsters_defeated} possible\n"); self.append_colored(f"Items Crafted: {self.player.items_crafted}\n"); self.append_colored(f"Lore Fragments: {len(self.player.lore_fragments)}\n")
        self.append_colored(f"Total Items Collected: {self.player.total_items_collected}\n"); self.append_colored(f"Deaths: {self.player.deaths}\n\n")
        self.append_colored("🌟 SPECIAL ABILITIES:\n", "achievement")
        for ability in self.player.special_abilities: self.append_colored(f"   • {ability}\n")
        self.append_colored("\n📊 RICK & MORTY TRACKING:\n", "lore"); self.append_colored(f"   Federation Credits: {self.player.federation_credits}\n")
        self.append_colored(f"   Cromulons Defeated: {self.player.cromulon_defeated_count}\n"); self.append_colored(f"   Plumbuses Collected: {self.player.plumbuses_collected}\n")
        self.append_colored(f"   Mega Seeds Used: {self.player.mega_seeds_used}\n"); self.append_colored(f"   XP Bonus: {self.player.xp_bonus_percent}%\n")
    def show_enhanced_help(self):
        self.append_colored("\nRICK AND MORTY: MULTIVERSE MAYHEM COMMANDS\n", "quest"); self.append_colored("="*60 + "\n", "quest")
        self.append_colored("THE GOAL:\n", "achievement"); self.append_colored("  Rick's Microverse Battery died, so run his errands across the\n  multiverse to build the OMNI-CORE. Talk to Rick to begin.\n")
        self.append_colored("\nTYPING TIP, TAB AUTOCOMPLETE:\n", "success")
        self.append_colored("  Press Tab to cycle through only the actions you can take right now.\n")
        self.append_colored("  Type a letter first to narrow it (e.g. 'g'+Tab). After a command\n  that needs a target (get / use / give / craft / buy / sell), Tab\n  cycles the valid choices (e.g. 'get'+space+Tab lists what's here).\n")
        self.append_colored("\nMOVE:\n", "achievement"); self.append_colored("  north / south / east / west  (or n / s / e / w)\n"); self.append_colored("  portal_jump <X> <Y>: jump to any visited coord (needs a Portal Gun (Replica))\n")
        self.append_colored("\nTALK & INTERACT:\n", "achievement"); self.append_colored("  talk: speak to whoever is here\n"); self.append_colored("  give <item>: hand an item to the NPC here\n"); self.append_colored("  get <item>: pick something up\n"); self.append_colored("  use <item>: use a gadget/consumable (e.g. Healing Serum, Energy Cell)\n"); self.append_colored("  look / examine / l: re-describe the room or a target\n"); self.append_colored("  hint / quest: your current objective and where to go next\n"); self.append_colored("  search: dig up useful intel/clues hidden in a special room\n")
        self.append_colored("\nSPECIAL-ROOM ACTIONS (used to retrieve quest items):\n", "achievement"); self.append_colored("  eat, observe, play, tinker, negotiate, listen, scavenge, haggle,\n  investigate, call, harvest, order, bribe, connect\n"); self.append_colored("  (Tab will suggest the right one when you're standing in such a room.)\n")
        self.append_colored("\nSHOP (only at Glexo's Pawn Shop, marked $ on the map):\n", "success"); self.append_colored("  list: see what's for sale\n  buy <item> / sell <item>\n")
        self.append_colored("\nCOMBAT (typed directly, no 'cast'):\n", "combat")
        self.append_colored("  attack: basic attack\n  flee: try to escape\n")
        self.append_colored("  plasma_blast: heavy hit (costs Charge)\n")
        self.append_colored("  mind_wipe: hit + stun the enemy a turn (costs Charge)\n")
        self.append_colored("  echo_scream: double hit (costs HP)\n")
        if self.player and self.player.race == "Neutrino Bomb": self.append_colored("  show_me_what_you_got: detonate the Neutrino Bomb (costs Charge)\n", "achievement")
        self.append_colored("  A failed or mistyped command never costs you a turn. Only real\n  actions do, so you won't get hit for typing something wrong.\n")
        if self.player and self.player.race == "Recon Visor":
            self.append_colored("\nRECON VISOR:\n", "achievement"); self.append_colored("  scan: analyze the current room\n  sense <X> <Y>: peek at coordinates (costs 2 Charge)\n")
        self.append_colored("\nINVENTORY / CRAFTING:\n", "achievement"); self.append_colored("  inventory / inv / i: what you carry\n  stats: your full character sheet\n  craft <item>: build a gadget (needs a side-quest reward piece + parts)\n")
        self.append_colored("\nGAME:\n", "lore"); self.append_colored("  map / journal / achievements: open those panels\n  save / load: save or load your game\n")
        self.append_colored("\nCLASS RADAR:\n", "success")
        self.append_colored("  Your attachment faintly senses one kind of room a few tiles away, shown as a\n  DIMMED marker on the map before you've been there: Holo-Mapper=Items,\n  Parasite Scanner=Enemies, Dark Matter Cell=Quests/Shop, Universal Translator=Main NPCs,\n  Fabricator Drone=Side NPCs. Targeting Chip/Combat Exo-Rig/Portal Coil have no radar but\n  hit harder / level faster / move freer instead. (See 'Radar:' in your stats.)\n")
        self.append_colored("\nRESOURCES:\n", "lore"); self.append_colored("  Charge = gadget energy (restore with Energy Cell). HP heals with Healing Serum.\n")
    def examine_target(self, target, room):
        target_lower = target.lower()
        if target_lower in ["room", "area", "surroundings"]: self.print_room()
        elif target_lower in ["npc", "person"] and room.get("npc"):
            npc = room["npc"]
            if getattr(npc, "is_shop", False): self.append_colored(f"🔍 {npc.name}: a four-eyed pawnbroker. Type 'list' to see his wares.\n", "lore")
            elif npc.is_subquest: self.append_colored(f"🔍 {npc.name} needs {self._np(npc.subqdata['need_item'], True)}.\n", "lore")
            elif getattr(npc, "is_rick", False): self.append_colored("🔍 Rick C-137: your grandfather, a genius, and the reason you're doing all this.\n", "quest")
            else: self.append_colored(f"🔍 {npc.name}: {EXTENDED_QUESTS[npc.quest_idx]['persona']}\n", "quest")
        elif target_lower in ["enemy", "creature", "monster"] and room.get("monster"):
            monster = room["monster"]
            self.append_colored(f"🔍 {monster.name} (HP: {monster.hp}/{monster.max_hp})\n", "combat")
            self.append_colored(f"    {monster.description}\n")
            if monster.loot:
                self.append_colored(f"    Might drop: {', '.join(monster.loot)}\n", "success")
        elif target_lower in ["lore"] and "hidden_lore" in room and not room.get("lore_discovered"): self.append_colored("📋 Something here catches your eye. There's more to this place than it lets on.\n", "lore")
        else:
            item_match = self._find_item_in_list(target, room.get("items", []))
            if item_match: self.append_colored(f"🔍 {item_match}: An intriguing object that might be useful.\n", "success")
            else: self.append_colored(f"❌ You don't see anything notable about '{target}' here.\n", "error")
    def toggle_map(self):
        if self._check_if_dead(): return
        # I always route through show_enhanced_map, which builds the window if it's missing
        # or reliably yanks the existing one back to the front. One door in.
        self.show_enhanced_map()
    def _save_path(self, name):
        safe = "".join(c for c in name if c.isalnum() or c in " -_").strip()
        return os.path.join(self.saves_dir, (safe or "universe") + ".rmsave")
    def _list_saves(self):
        try:
            return sorted((fn[:-7] for fn in os.listdir(self.saves_dir) if fn.endswith(".rmsave")), key=str.lower)
        except Exception:
            return []
    def _write_save(self, name, announce=True):
        if not self.player:
            if announce: self.append_colored("No game to save!\n", "error")
            return False
        try:
            data = {"player": self.player, "world": self.world, "difficulty": self.difficulty, "width": self.width, "height": self.height,
                    "total_lore_fragments_count": getattr(self, "total_lore_fragments_count", 0),
                    "unlocked_achievements": [a.name for a in ACHIEVEMENTS if a.unlocked], "save_name": name}
            with open(self._save_path(name), 'wb') as f: pickle.dump(data, f)
            self.current_save_name = name
            if announce: self.append_colored(f"💾 Universe '{name}' saved.\n", "success"); self.root.bell()
            return True
        except Exception as ex:
            messagebox.showerror("Save Error", f"Failed to save: {ex}"); return False
    def save_game(self):
        if not self.player: self.append_colored("No game to save!\n", "error"); return
        if self.current_save_name: self._write_save(self.current_save_name)
        else: self.show_save_manager()
    def _read_save(self, name):
        path = self._save_path(name)
        if not os.path.isfile(path): messagebox.showerror("Load Error", "That universe no longer exists."); return
        try:
            with open(path, 'rb') as f: data = pickle.load(f)
            self.player = data["player"]; self.world = data["world"]; self._sanitize_world()
            # Old save from before I added the seed toggle. If the Injector's already built, the
            # seeds count as usable now, so flip the switch and drag the loose ones over. Cleaning up after past me.
            # Repair the Mega Seed Injector state. If the injector's in the bag but the switch never
            # flipped (older saves, or one built via the typed `craft` command back when that path
            # skipped the special handling), turn it on now. Building it IS one safe dose, so it counts
            # as a used seed, and any seeds stranded in the crafting pile become usable items. The
            # achievement re-check at the end of load then hands over Mega Seed Master.
            if not hasattr(self.player, "mega_seed_injector_built"):
                self.player.mega_seed_injector_built = False
            if "Mega Seed Injector" in self.player.inventory and not self.player.mega_seed_injector_built:
                self.player.mega_seed_injector_built = True
                self.player.mega_seeds_used = max(getattr(self.player, "mega_seeds_used", 0), 1)
            if self.player.mega_seed_injector_built:
                while "Mega Seed" in self.player.crafting_materials:
                    self.player.crafting_materials.remove("Mega Seed"); self.player.inventory.append("Mega Seed")
            # Old save from before I tracked completion. Scrape the crafted gadgets off whatever
            # Morty's still holding so he isn't punished for saving before I got organized.
            if not hasattr(self.player, "crafted_recipes") or self.player.crafted_recipes is None:
                self.player.crafted_recipes = set()
            for _r in CRAFTING_RECIPES:
                if _r in self.player.inventory: self.player.crafted_recipes.add(_r)
            if not hasattr(self.player, "true_ending_shown"):
                self.player.true_ending_shown = False
            if not hasattr(self.player, "shop_buyback") or self.player.shop_buyback is None:
                self.player.shop_buyback = {}
            # Old save from before hidden enemies existed. Every kill on record was a placed one (no hidden
            # ones could have existed yet), so seed the placed counter from the old total. Then rebuild the
            # placed count (alive placed + already-killed placed), shuffle a fresh pool, and recompute the max.
            if not hasattr(self.player, "placed_monsters_defeated"):
                self.player.placed_monsters_defeated = self.player.monsters_defeated
            if not hasattr(self.player, "hidden_pool") or self.player.hidden_pool is None:
                self.player.hidden_pool = list(HIDDEN_ENEMIES); random.shuffle(self.player.hidden_pool)
            if not getattr(self.player, "placed_enemy_count", 0):
                alive_placed = sum(1 for rm in self.world.values() if rm.get("monster") and not getattr(rm["monster"], "hidden", False))
                self.player.placed_enemy_count = alive_placed + self.player.placed_monsters_defeated
            if not getattr(self.player, "max_total_kills", 0):
                self.player.max_total_kills = self._compute_max_total_kills(self.player.placed_enemy_count, len(HIDDEN_ENEMIES))
            self.difficulty = data.get("difficulty", DifficultyLevel.NORMAL)
            self.width = data.get("width", 12); self.height = data.get("height", 12)
            self.total_lore_fragments_count = data.get("total_lore_fragments_count", 0)
            self.current_save_name = data.get("save_name", name)
            # Restore the achievement unlock state on load, so earned perks (free portal jumps,
            # XP bonus, Plumbus Pro, all of it) survive a reload instead of quietly switching off
            # when _recalc_passives runs against a fresh ACHIEVEMENTS list. Learned that one the hard way.
            saved_unlocked = set(data.get("unlocked_achievements", []))
            for a in ACHIEVEMENTS:
                a.unlocked = a.name in saved_unlocked
            # Re-run the check after all the repairs above, so anything you genuinely earned but that
            # never got flagged (like Mega Seed Master once the injector's fixed) unlocks right now.
            check_achievements(self.player, self.world, self)
            self._vpad_lines = 0
            self.set_button_states(menu=False)
            self._close_all_popups()
            self.append_colored(f"📁 Entered universe '{self.current_save_name}'.\n", "success"); self._recalc_passives(); self.print_room(); self.update_info_display(); self.update_enhanced_map(); self.update_minimap()
            self.root.bell()
        except Exception as ex: messagebox.showerror("Load Error", f"Failed to load save: {ex}")
    def load_game(self): self.show_save_manager()
    def show_save_manager(self):
        win = tk.Toplevel(self.root); win.title("Choose Your Universe"); self._center_popup(win, 470, 470); win.transient(self.root); win.grab_set(); self._apply_icon(win)
        tk.Label(win, text="🌀 Choose Your Universe", font=("Arial", 15, "bold")).pack(pady=(14, 2))
        tk.Label(win, text="Load a saved universe, or spin up a brand-new one.", font=("Arial", 10)).pack(pady=(0, 8))
        saves = self._list_saves()
        lf = tk.LabelFrame(win, text="Saved Universes", font=("Arial", 10, "bold")); lf.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        listbox = tk.Listbox(lf, font=("Consolas", 11), height=7, activestyle="dotbox"); listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 4))
        for nm in saves: listbox.insert(tk.END, nm)
        if not saves:
            listbox.insert(tk.END, "  (no saved universes yet)"); listbox.config(fg="#888")
        else:
            listbox.selection_set(0)
        def do_load(event=None):
            if not saves: return
            sel = listbox.curselection()
            if not sel: messagebox.showinfo("Pick One", "Select a universe to enter first."); return
            name = saves[sel[0]]; win.destroy(); self._read_save(name)
        tk.Button(lf, text="▶  Enter Selected Universe", font=("Arial", 11), command=do_load).pack(pady=(0, 8))
        listbox.bind("<Double-Button-1>", do_load)
        nf = tk.LabelFrame(win, text="New Universe", font=("Arial", 10, "bold")); nf.pack(fill=tk.X, padx=14, pady=(4, 12))
        row = tk.Frame(nf); row.pack(fill=tk.X, padx=6, pady=(8, 4))
        tk.Label(row, text="Name:", font=("Arial", 10)).pack(side=tk.LEFT)
        namevar = tk.StringVar(); ent = tk.Entry(row, textvariable=namevar, font=("Arial", 11)); ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        def do_create(event=None):
            name = namevar.get().strip()
            if not name: messagebox.showerror("Name Required", "Give your new universe a name first."); return
            if name in self._list_saves():
                if not messagebox.askyesno("⚠️  Universe Already Exists",
                        f"A universe named '{name}' already exists.\n\nStarting a new one here will WIPE IT FROM EXISTENCE. Every room, every quest, that entire universe, gone forever.\n\nObliterate it and start fresh?"):
                    return
            self.current_save_name = name; win.destroy(); self.start_new_game()
        tk.Button(nf, text="✨  Create New Universe", font=("Arial", 11), command=do_create).pack(pady=(0, 8))
        ent.bind("<Return>", do_create)
        win.protocol("WM_DELETE_WINDOW", win.destroy); ent.focus_set()
    def _apply_icon(self, win):
        """Give a window the game's icon. Toplevel popups don't inherit the
        main window's icon, so without this they show the generic Python feather
        in the title-bar corner and taskbar."""
        try:
            if getattr(self, "icon_path", None) and os.path.exists(self.icon_path):
                win.iconbitmap(self.icon_path)
        except Exception:
            pass
    def _center_popup(self, win, w, h):
        """Place a popup of size w x h in the middle of the screen."""
        try:
            win.update_idletasks()
            sw = win.winfo_screenwidth(); sh = win.winfo_screenheight()
            x = max(0, (sw - w) // 2); y = max(0, (sh - h) // 2)
            win.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            win.geometry(f"{w}x{h}")
    def on_window_focus(self, event=None):
        if hasattr(self, 'entry') and self.entry.winfo_exists(): self.entry.focus_set()
    def on_window_click(self, event=None):
        if hasattr(self, 'entry') and self.entry.winfo_exists(): self.entry.focus_set()
LEGAL_DISCLAIMER_TEXT = """LEGAL NOTICE, DISCLAIMER, AND ACKNOWLEDGEMENT OF INTELLECTUAL PROPERTY RIGHTS

PLEASE READ THIS NOTICE CAREFULLY AND IN FULL BEFORE USING THIS SOFTWARE.

1. UNOFFICIAL, UNAFFILIATED FAN WORK.
This program (the "Game") is an unofficial, non-commercial, fan-made work created solely for personal entertainment and educational purposes. It is NOT an official product. It is NOT created, produced, published, licensed, sponsored, endorsed, approved, or authorized by, and is in no way affiliated with, the owners of the "Rick and Morty" property or any of their subsidiaries, affiliates, parents, partners, agents, or licensors.

2. OWNERSHIP OF INTELLECTUAL PROPERTY.
"Rick and Morty," together with all associated characters, character names, likenesses, voices, catchphrases, dialogue, logos, designs, settings, locations, storylines, and all other related elements (collectively, the "Licensed Property"), are the exclusive intellectual property of, and are protected by the copyright, trademark, trade dress, and other laws of the United States and other countries owned by, their respective rights holders. Those rights holders include, without limitation:
   - Cartoon Network, Inc., the registered owner of the "RICK AND MORTY" trademark (U.S. Trademark Reg. No. 5407816);
   - Warner Bros. Discovery, Inc., the ultimate parent company of Cartoon Network, Inc.;
   - Adult Swim, the programming brand and network on which the series is broadcast; and
   - the series' co-creators, Dan Harmon and Justin Roiland.
All rights in and to the Licensed Property are reserved by their respective owners. All trademarks, service marks, trade names, and registered marks referenced herein are the property of their respective owners.

3. NO CLAIM OF OWNERSHIP BY THE DEVELOPER.
The developer of this Game claims NO ownership of, and asserts NO right, title, or interest in, the Licensed Property. The developer does not own any character, name, story, setting, dialogue, logo, or other element derived from "Rick and Morty." Any such elements appearing in this Game remain the sole and exclusive property of their respective owners. The developer's only claim of ownership extends to the original computer source code and original software components personally authored by the developer, and that claim expressly excludes the Licensed Property.

4. NO INFRINGEMENT INTENDED; NOMINATIVE USE.
No copyright or trademark infringement is intended. References to the Licensed Property are made nominatively, solely to identify the source material that inspired this non-commercial fan work. Nothing in this Game is intended to compete with, substitute for, dilute, tarnish, or imply any association with, sponsorship of, or endorsement by the rights holders. Any names, marks, or material used are used for identification and commentary purposes only.

5. NON-COMMERCIAL DISTRIBUTION.
This Game is distributed free of charge. The developer derives no commercial benefit from it and does not sell, rent, license, monetize, or otherwise commercially exploit it or the Licensed Property in any manner.

6. NO LICENSE GRANTED; COMPLIANCE AND TAKEDOWN.
This notice does not grant, transfer, assign, or convey any right, title, license, permission, or interest in the Licensed Property to any person. The developer respects the rights of the owners of the Licensed Property and will promptly comply with any lawful request from a rights holder to cease use of, modify, or remove any allegedly infringing material.

7. NO WARRANTY; LIMITATION OF LIABILITY.
This Game is provided "AS IS" and "AS AVAILABLE," without warranty of any kind, whether express, implied, or statutory, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, title, and non-infringement. To the fullest extent permitted by applicable law, in no event shall the developer be liable for any direct, indirect, incidental, special, consequential, or exemplary damages, or for any claim or other liability whatsoever, arising from, out of, or in connection with the Game, its use, or this notice.

8. OFFICIAL PROPERTY.
For the official "Rick and Morty" property, please visit the rights holders' official websites listed below this text.

By selecting "I AGREE & CONTINUE," you acknowledge that you have read and understood this notice, that you understand the developer does not own the Licensed Property and claims no rights in it, and that this is an unofficial, non-commercial, fan-made work. If you do not agree, select "DECLINE & EXIT" to close the program without launching it.
"""


def show_legal_disclaimer(root):
    """Modal IP/legal notice. Must be acknowledged before the game builds.
    Returns True if the user agreed, False if they declined or closed it."""
    BG = "#0a0a0f"; PANEL = "#05050a"; FG = "#AFFF94"; HDR = "#FFD700"
    LINK = "#40C4FF"; OKC = "#4ADE80"; NOC = "#C40202"
    state = {"agreed": False}

    dlg = tk.Toplevel(root)
    dlg.title("Legal Disclaimer - Rick and Morty - Multiverse Mayhem")
    dlg.configure(bg=BG)
    try:
        if hasattr(sys, "_MEIPASS"):
            _ip = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            _ip = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if not os.path.exists(_ip):
            _ip = "icon.ico"
        if os.path.exists(_ip):
            dlg.iconbitmap(_ip)
    except Exception:
        pass

    tk.Label(dlg, text="LEGAL NOTICE & INTELLECTUAL PROPERTY DISCLAIMER",
             font=("Consolas", 14, "bold"), bg=BG, fg=HDR).pack(fill=tk.X, padx=16, pady=(14, 2))
    tk.Label(dlg, text="Please read this notice in full before continuing.",
             font=("Consolas", 10), bg=BG, fg=FG).pack(fill=tk.X, padx=16, pady=(0, 8))

    body = scrolledtext.ScrolledText(dlg, wrap="word", font=("Consolas", 10),
                                     bg=PANEL, fg=FG, insertbackground=FG, borderwidth=0,
                                     highlightthickness=1, highlightbackground="#222222",
                                     width=92, height=22)
    body.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
    body.insert("1.0", LEGAL_DISCLAIMER_TEXT)
    body.configure(state="disabled")

    def _open(url):
        try:
            import webbrowser
            webbrowser.open_new_tab(url)
        except Exception:
            pass

    linkrow = tk.Frame(dlg, bg=BG); linkrow.pack(fill=tk.X, padx=16, pady=(2, 0))
    tk.Label(linkrow, text="Official property:", font=("Consolas", 10), bg=BG, fg=FG).pack(side=tk.LEFT)
    for _label, _url in (("Adult Swim (Rick and Morty)", "https://www.adultswim.com/videos/rick-and-morty"),
                         ("Warner Bros. Discovery", "https://www.wbd.com")):
        _lk = tk.Label(linkrow, text=_label, font=("Consolas", 10, "underline"),
                       bg=BG, fg=LINK, cursor="hand2")
        _lk.pack(side=tk.LEFT, padx=(10, 0))
        _lk.bind("<Button-1>", lambda e, u=_url: _open(u))

    def _decline():
        state["agreed"] = False; dlg.destroy()

    def _agree():
        state["agreed"] = True; dlg.destroy()

    btnrow = tk.Frame(dlg, bg=BG); btnrow.pack(fill=tk.X, padx=16, pady=12)
    tk.Button(btnrow, text="DECLINE & EXIT", font=("Arial", 11, "bold"), bg=NOC, fg="white",
              activebackground="#8A0000", activeforeground="white", command=_decline).pack(side=tk.LEFT)
    tk.Button(btnrow, text="I AGREE & CONTINUE", font=("Arial", 11, "bold"), bg=OKC, fg="black",
              activebackground="#2EA043", activeforeground="black", command=_agree).pack(side=tk.RIGHT)

    dlg.protocol("WM_DELETE_WINDOW", _decline)
    W, H = 780, 660
    try:
        dlg.update_idletasks()
        sw = dlg.winfo_screenwidth(); sh = dlg.winfo_screenheight()
        x = max(0, (sw - W) // 2); y = max(0, (sh - H) // 2)
        dlg.geometry(f"{W}x{H}+{x}+{y}")
    except Exception:
        dlg.geometry(f"{W}x{H}")
    dlg.minsize(560, 440)
    dlg.grab_set()
    dlg.lift()
    try:
        dlg.attributes("-topmost", True)
        dlg.after(400, lambda: dlg.winfo_exists() and dlg.attributes("-topmost", False))
    except Exception:
        pass
    dlg.focus_force()
    root.wait_window(dlg)
    return state["agreed"]


if __name__ == "__main__":
    # Windows taskbar icon, ugh. I gotta tell Windows who we are and load the icon BEFORE the
    # first window pops, because Windows nails the taskbar icon down the instant a window shows.
    # Do it late and run one gets the dumb default feather, run two looks fine off the cache.
    # Doing it right here, ahead of tk.Tk(), is what makes my icon show on the very first launch.
    try:
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"RickAndMorty.MultiverseMayhem.{GAME_VERSION}")
    except Exception:
        pass
    _boot_icon = os.path.join(sys._MEIPASS, "icon.ico") if hasattr(sys, "_MEIPASS") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if not os.path.exists(_boot_icon):
        _boot_icon = "icon.ico"
    root = tk.Tk()
    try:
        if os.path.exists(_boot_icon):
            root.iconbitmap(default=_boot_icon)
    except Exception:
        pass
    # Hide the main window until the legal notice has been acknowledged, so nothing
    # else opens first. Decline = exit before the game ever builds.
    root.withdraw()
    if not show_legal_disclaimer(root):
        root.destroy()
        sys.exit(0)
    root.deiconify()
    # The window icon gets set inside EnhancedGameApp.__init__ and applied to every popup,
    # so the entire app shows icon.ico the same everywhere. Consistency, Morty.
    app = EnhancedGameApp(root)
    root.mainloop()