#!/usr/bin/env python3
"""Write one product-page JSON per priced item into src/data/products/.

    python3 tools/gen-product-pages.py            # new files only
    python3 tools/gen-product-pages.py --force    # rewrite every generated file
    python3 tools/gen-product-pages.py shirt saree --force

Each item belongs to a PROFILE (everyday wear, tailoring, ethnic, knitwear,
leather, home textiles, carpet, footwear, laundry). The profile carries the
copy that is true for the whole family — how it is cleaned, which stains it
meets, what the finishing protects. The PRODUCTS table adds what is specific
to one item: its noun, its best-for list, the three details that make it
different, and one question customers actually ask about it.

Prices are NOT written here. build.py reads them from pricing.json at build
time (and fills {price1}/{price2} in copy), so a price change never needs a
regeneration. Sections every page shares (studio, process, doorstep, local,
common FAQs) live in src/data/products/_shared.json.

jeans.json is hand-written and is never touched unless named with --force.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
OUT = DATA / "products"
HAND_WRITTEN = {"jeans"}

DISCLAIMER = (
    "Treatment results depend on the type of stain, fabric condition, age of the stain "
    "and any previous treatment. We use professional spot-lifting techniques, but complete "
    "removal cannot be guaranteed for every aged or heat-set mark."
)

T_DRYCLEAN = "24–48 hours"
T_PRESS = "24 hours"

# ---------------------------------------------------------------------------
# Service templates
# ---------------------------------------------------------------------------

def dryclean_service(p: dict, prof: dict) -> dict:
    return {
        "id": "dry-clean",
        "slug": p["slug"],
        "name": prof.get("svc_name", "Dryclean & Press"),
        "short": prof.get("svc_short", "Dryclean"),
        "tagline": prof.get("svc_tagline", "Deep Dryclean & Finishing"),
        "shortDescription": prof["svc_short_desc"].replace("{noun}", p["noun"]),
        "longDescription": prof["svc_long_desc"].replace("{noun}", p["noun"]),
        "bestFor": p["best_for"],
        "includes": prof["includes"],
        "turnaround": p.get("turnaround", prof.get("turnaround", T_DRYCLEAN)),
    }


def steam_service(p: dict) -> dict:
    n = p["noun"]
    return {
        "id": "steam-press",
        "slug": p["iron"],
        "name": "Steam Press",
        "short": "Steam Press",
        "tagline": "Wrinkle Removal & Refresh",
        "shortDescription": "Crisp wrinkle removal and a fresh finish for pieces that are already clean.",
        "longDescription": "Professional steam pressing for pieces that are already clean but creased: shape, seams and drape reset on a steam finishing table, without shine or stiffness.",
        "bestFor": [
            "Already-clean pieces that only need the creases out",
            "A quick refresh before work, travel or an event",
            "Home-washed pieces that dried crumpled",
            "Keeping a sharp, neat everyday look",
        ],
        "includes": [
            "Garment & fastener inspection",
            "Professional steam pressing",
            "Seam, collar and hem alignment",
            "Natural drape restored",
            "Protective fold or hanger packaging",
        ],
        "turnaround": T_PRESS,
    }


def compare_block(p: dict, prof: dict) -> dict:
    n = p["many"]
    return {
        "eyebrow": "Service Selection Guide",
        "title": f"Which {p['name']} Service Should You Choose?",
        "intro": "Choose Dryclean & Press when the piece has been worn and needs a proper professional clean. Choose Steam Press when it is already clean and only needs a crisp finish.",
        "features": [
            {"name": "Professional dryclean on commercial machines", "cells": [True, False]},
            {"name": "Stain & spot pre-treatment", "cells": [True, False]},
            {"name": "Lifts body oils, sweat and odour", "cells": [True, False]},
            {"name": prof["compare_protect"], "cells": [True, "N/A"]},
            {"name": "Steam wrinkle removal", "cells": [True, True]},
            {"name": "Seam, collar & hem alignment", "cells": [True, True]},
            {"name": "Pocket & trim check", "cells": [True, True]},
            {"name": f"Best for worn or soiled {n}", "cells": [True, False]},
            {"name": f"Best for clean {n} needing a refresh", "cells": [False, True]},
            {"name": "Free doorstep pickup & delivery", "cells": [True, True]},
        ],
    }


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

DRYCLEAN_INCLUDES = [
    "Individual item & pocket check",
    "Stain & spot pre-treatment where applicable",
    "Closed-cycle professional dryclean",
    "Shape & seam alignment",
    "Hand steam finishing",
    "Quality inspection & protective packaging",
]

PROFILES: dict[str, dict] = {}

PROFILES["everyday"] = {
    "category": "Everyday Wear",
    "parent": "premium-dry-cleaning",
    "svc_short_desc": "Professional dryclean for worn {noun}, finished on a steam table.",
    "svc_long_desc": "A professional dryclean on commercial machines that lifts sweat, body oils and everyday grime from your {noun} while protecting colour, fit and fabric, followed by a hand steam finish.",
    "includes": DRYCLEAN_INCLUDES,
    "compare_protect": "Protects colour from water washout",
    "why": {
        "eyebrow": "Fabric Preservation",
        "subtitle": "Home machines rub fibres against each other, fade colour and pull garments out of shape a little more every wash. Here is why professional dryclean care makes the difference:",
        "points": [
            ("Colour Stays True", "Solvent cleaning does not bleed dye the way hot water and detergent do, so darks stay dark and prints stay sharp."),
            ("Fit & Shape Hold", "No spin cycle to twist seams or stretch necklines and waistbands out of shape."),
            ("Less Fibre Wear", "A low-friction dryclean cycle means less pilling, fuzzing and thinning at elbows, collars and seats."),
            ("Oils Actually Lift", "Body oils and deodorant build-up dissolve in dryclean solvent where a cold home wash leaves them behind."),
            ("A Finish You Can See", "Pressed on a steam finishing table, not a domestic iron, so seams sit flat and fabric keeps its drape."),
            ("Checked Before & After", "Buttons, seams and stains are checked when the piece arrives and again before it leaves."),
        ],
    },
    "stains": [
        ("Food & Beverage", "Tea, coffee, curry, gravy, sauces and oil drips"),
        ("Sweat & Body Oils", "Collar and underarm build-up, yellowing and odour"),
        ("Deodorant Marks", "White streaks and stiff underarm residue"),
        ("Ink & Pen", "Pen marks near pockets and cuffs"),
        ("Cosmetics", "Foundation, lipstick and sunscreen transfer"),
        ("Dust & Commute Grime", "Grey cuffs, hems and seat areas from daily wear"),
    ],
    "details": [
        ("Buttons & Fasteners", "Checked on arrival; loose buttons are flagged before cleaning so nothing is lost in the machine."),
        ("Colour Care", "Darks, whites and prints are assessed separately so colour never transfers between garments."),
        ("Finishing", "Steam-pressed to the garment's natural shape rather than flattened into hard creases."),
    ],
    "before_after": [
        ("Collar & Cuff Grime", "A grey line along the collar and cuffs from daily wear.", "Targeted pre-treatment on the soiled edges, then a professional dryclean.", "Clean, even collar and cuffs with the fabric's colour intact."),
        ("Food Spill", "A fresh gravy or oil mark on the front of the garment.", "Degreasing spot treatment before the dryclean cycle.", "Mark lifted without a water ring or a faded patch."),
        ("Crumpled After Travel", "Deep creases from a suitcase or a crowded cupboard.", "Steam finishing with seams and hems aligned.", "Smooth, crisp and ready to wear."),
    ],
    "related": ["shirt", "jeans", "pant-trouser", "t-shirt", "dress", "men-suit-2pcs"],
    "banner": {"src": "images/studio/shirts-hung.webp", "alt": "Pressed shirts hanging on a rail", "caption": "Finished by hand, hung to hold their shape"},
}

PROFILES["tailored"] = {
    "category": "Formal & Tailored Wear",
    "parent": "premium-dry-cleaning",
    "svc_short_desc": "Professional dryclean for a tailored {noun}, with hand-finished shoulders and lapels.",
    "svc_long_desc": "A tailored {noun} is built with canvas, interfacing and linings that water would distort. A professional dryclean cleans it without shrinking the layers, then the shoulders, lapels and creases are finished by hand on a steam table.",
    "includes": [
        "Pocket, lining & button check",
        "Stain & spot pre-treatment where applicable",
        "Closed-cycle professional dryclean",
        "Shoulder & lapel shaping",
        "Hand steam finishing & crease setting",
        "Covered on a hanger for delivery",
    ],
    "compare_protect": "Protects canvas & interlining structure",
    "why": {
        "eyebrow": "Structure Preservation",
        "subtitle": "Tailoring depends on layers — shell fabric, canvas, interfacing and lining — that shrink at different rates in water. Here is why tailored pieces need professional dryclean care:",
        "points": [
            ("Structure Holds", "No water means canvas and interfacing do not shrink, bubble or separate from the shell fabric."),
            ("Shoulders & Lapels", "Shoulders are pressed on a form and lapels rolled by hand, never flattened on a board."),
            ("Wool Without Shine", "Steam finishing through a cloth keeps wool from turning shiny at the seams and pockets."),
            ("Linings Stay Put", "Linings are cleaned with the shell so nothing puckers or hangs below the hem."),
            ("Sharp Creases", "Trouser creases are set cleanly along the original line — not a second, doubled crease."),
            ("Delivered Hung", "Returned on a hanger in a cover, ready to wear rather than folded into new creases."),
        ],
    },
    "stains": [
        ("Food & Wine", "Dinner and event spills on lapels, cuffs and fronts"),
        ("Sweat & Collar Line", "Collar and underarm build-up from a long day"),
        ("Makeup Transfer", "Foundation and lipstick on collars and shoulders"),
        ("Ink", "Pen marks near inside pockets"),
        ("Rain & Water Spots", "Rings and marks from monsoon showers"),
        ("Dust & Shine", "Surface dust, dullness and shiny wear spots"),
    ],
    "details": [
        ("Lapels & Collar", "The lapel roll is steamed back into shape by hand instead of being pressed flat."),
        ("Buttons & Linings", "Horn and metal buttons are checked and linings are smoothed so they never pull."),
        ("Trouser Creases", "Creases are set along the original line, with the waistband and seat pressed separately."),
    ],
    "before_after": [
        ("Event Spill on a Lapel", "A drink or food splash on the lapel after a function.", "Targeted spot treatment, then a gentle professional dryclean.", "Clean lapel with the roll and texture intact."),
        ("Tired, Shapeless Shoulders", "Shoulders have lost their line after months of wear.", "Dryclean followed by shoulder pressing on a form.", "Shoulders and chest sit the way the tailor cut them."),
        ("Double Crease on Trousers", "A second crease line from a home iron.", "Steam finishing to relax the old line and set the original crease.", "One clean, sharp crease down each leg."),
    ],
    "related": ["men-suit-2pcs", "men-suit-3pcs", "coat", "shirt", "pant-trouser", "long-coat"],
    "banner": {"src": "images/studio/suits-hung.webp", "alt": "Tailored jackets hanging after professional dry cleaning", "caption": "Shoulders shaped, lapels rolled, returned on a hanger"},
}

PROFILES["ethnic"] = {
    "category": "Ethnic & Occasion Wear",
    "parent": "premium-dry-cleaning",
    "svc_short_desc": "Professional dryclean for your {noun}, with embroidery, zari and borders protected.",
    "svc_long_desc": "Silk, georgette, zari and hand embroidery do not survive a home wash. Your {noun} is drycleaned on commercial machines with solvents that are gentle on dye and metallic thread, then steam-finished by hand around the work, not over it.",
    "includes": [
        "Embroidery, zari & trim inspection",
        "Stain & spot pre-treatment where safe",
        "Closed-cycle professional dryclean",
        "Colour-bleed check on dyed fabrics",
        "Hand steam finishing around the work",
        "Folded with tissue & protective packaging",
    ],
    "compare_protect": "Protects zari, embroidery & dyes",
    "why": {
        "eyebrow": "Heritage Fabric Care",
        "subtitle": "Occasion wear is often silk, has hand work, and is only worn a few times a year — which is exactly when a home wash does the most damage. Here is why professional dryclean care makes the difference:",
        "points": [
            ("Dyes Do Not Run", "Rich silks and hand-dyed fabrics can bleed in water. A dryclean solvent keeps colour where it belongs."),
            ("Zari Stays Bright", "Metallic thread tarnishes and frays with detergent and agitation; a gentle dryclean cycle avoids both."),
            ("Embroidery Protected", "Beads, sequins and mirror work are checked first and finished from the reverse, never pressed flat."),
            ("Silk Keeps Its Sheen", "Silk loses lustre and water-marks easily at home. Professional handling keeps its natural sheen."),
            ("Borders & Pleats", "Borders are pressed straight and pleats set by hand so the garment drapes as it should."),
            ("Stored the Right Way", "Returned folded with tissue, ready to store until the next occasion without new creases."),
        ],
    },
    "stains": [
        ("Food & Gravy", "Wedding-buffet curry, oil and sweets"),
        ("Haldi & Mehendi", "Turmeric and henna marks from ceremonies"),
        ("Makeup", "Foundation, kajal and lipstick on necklines and dupattas"),
        ("Sweat", "Underarm and neckline marks from a long event"),
        ("Wax & Candle", "Diya and candle wax drips"),
        ("Perfume Marks", "Rings left by perfume sprayed on silk"),
    ],
    "details": [
        ("Zari & Metallic Thread", "Handled to avoid tarnish and snagging; never scrubbed or pressed directly."),
        ("Embroidery & Embellishment", "Beads, sequins and mirror work are checked before cleaning and finished from the reverse."),
        ("Borders & Pleats", "Borders are pressed straight and pleats reset by hand so the drape is right."),
    ],
    "before_after": [
        ("Haldi on Silk", "A turmeric mark from a haldi ceremony on a silk garment.", "Careful spot assessment and pre-treatment suited to silk, then a gentle dryclean.", "Mark reduced or lifted with the silk's sheen intact."),
        ("Food Stain Near Embroidery", "A gravy drip right beside hand embroidery.", "Targeted treatment around the work, then a professional dryclean.", "Stain treated without disturbing beads or thread."),
        ("Crushed After an Event", "Creased borders and pleats after a long function.", "Hand steam finishing from the reverse, borders and pleats set by hand.", "Fresh drape and straight borders, ready to store."),
    ],
    "related": ["saree", "lehenga", "kurta", "sherwani", "dupatta", "blouse"],
    "banner": None,
}

PROFILES["knit"] = {
    "category": "Knitwear & Winter Wear",
    "parent": "premium-dry-cleaning",
    "svc_short_desc": "Professional dryclean for your {noun}, shaped and dried flat so it keeps its size.",
    "svc_long_desc": "Wool and knitted fibres felt and shrink with heat and agitation. Your {noun} is drycleaned on commercial machines without the tumble, then blocked back to shape and finished with light steam so it keeps its size and softness.",
    "includes": [
        "Knit, cuff & button check",
        "Stain & spot pre-treatment where applicable",
        "Closed-cycle professional dryclean",
        "Blocked back to shape",
        "Light steam finishing",
        "Folded flat — never hung — for delivery",
    ],
    "compare_protect": "Prevents shrinking & felting",
    "why": {
        "eyebrow": "Knit Preservation",
        "subtitle": "Knitted fabrics are loops of yarn, and heat plus agitation lock them together into felt. Here is why professional dryclean care is the safer choice for winter wear:",
        "points": [
            ("No Shrinking", "No hot wash and no tumble dryer — the two things that shrink wool."),
            ("No Felting", "A gentle solvent cycle keeps fibres from matting into a stiff, felted surface."),
            ("Shape Restored", "Each piece is blocked back to its size, so cuffs, hems and necklines do not flare."),
            ("Softness Kept", "Natural oils in wool are not stripped the way detergent strips them."),
            ("Less Pilling", "Low friction means fewer bobbles on sleeves and sides."),
            ("Stored Folded", "Returned folded flat, because a hanger stretches knitwear out of shape."),
        ],
    },
    "stains": [
        ("Food & Drink", "Tea, coffee, soup and sauce drips"),
        ("Sweat & Body Oils", "Neck, cuff and underarm build-up"),
        ("Makeup", "Foundation on necklines and collars"),
        ("Dust & Smoke", "Winter-evening bonfire smoke and street dust"),
        ("Storage Mustiness", "Stale smell after a summer in storage"),
        ("Pet Hair & Lint", "Hair and fluff caught in the knit"),
    ],
    "details": [
        ("Cuffs & Ribbing", "Ribbed cuffs and hems are blocked back so they grip again instead of flaring."),
        ("Necklines", "Necklines are shaped by hand so they do not stretch open."),
        ("Surface Finish", "Light steam lifts the pile without flattening the knit."),
    ],
    "before_after": [
        ("Out of Storage", "A winter piece that smells stale after months in a trunk.", "Professional dryclean and airing.", "Fresh, clean and ready for the first cold morning."),
        ("Stretched Cuffs", "Cuffs and hem have lost their grip and flare out.", "Dryclean and blocking back to the original size.", "Cuffs and hem sit neatly again."),
        ("Food Drip on the Front", "A soup or tea mark on the chest.", "Spot pre-treatment suited to wool, then a gentle dryclean.", "Mark treated without shrinking or felting the knit."),
    ],
    "related": ["sweater", "cardigan", "sweatshirt", "jacket", "shawl", "long-coat"],
    "banner": None,
}

PROFILES["leather"] = {
    "category": "Leather Care",
    "parent": "leather-cleaning",
    "care": "leather care",
    "eyebrow": "Professional Leather Care",
    "svc_name": "Leather Clean & Condition",
    "svc_short": "Leather Care",
    "svc_tagline": "Clean, Condition & Protect",
    "svc_short_desc": "Specialist leather cleaning and conditioning for your {noun}.",
    "svc_long_desc": "Leather is never put through a normal dryclean load — the solvents and heat that suit wool dry hide out and crack it. Your {noun} goes through a separate specialist process: surface-cleaned with pH-balanced leather products, conditioned, and finished by hand.",
    "includes": [
        "Leather type & finish assessment",
        "Seams, zips & lining check",
        "pH-balanced surface cleaning",
        "Conditioning to keep leather supple",
        "Hand finishing & buffing",
        "Protective packaging",
    ],
    "turnaround": "48–72 hours",
    "studio": {
        "eyebrow": "Inside Wash4You",
        "title": "How Wash4You Cares for Your {name}",
        "subtitle": "Leather never goes into the dryclean machine with everything else. It is tagged at your door and handled on its own, by hand, with products made for leather.",
        "points": [
            ("Kept out of the main load", "Leather is processed separately so it never meets solvents or heat meant for fabric."),
            ("Tagged from pickup to delivery", "Each piece is counted at your door and carries a Wash4You tag through every stage."),
            ("pH-balanced leather products", "Cleaned and conditioned with products designed for hide, not general detergents."),
            ("Hand finishing", "Buffed and finished by hand, then checked under light before it is packed."),
        ],
    },
    "why": {
        "eyebrow": "Leather Preservation",
        "subtitle": "Leather is skin: it needs its oils to stay supple, and it marks with water. Here is why professional leather care is worth it:",
        "points": [
            ("No Cracking", "The wrong solvent or heat dries leather out until it cracks. We use leather-specific products only."),
            ("Stays Supple", "Conditioning puts back the oils that daily wear and dry air take out."),
            ("Colour Protected", "Surface cleaning lifts grime without stripping the finish or dye."),
            ("Water-Mark Safe", "Leather is never soaked, so it does not dry stiff or ringed."),
            ("Hardware Cared For", "Zips, studs and buckles are cleaned and checked alongside the leather."),
            ("Lining Freshened", "The lining is freshened so the piece smells clean inside as well as out."),
        ],
    },
    "stains": [
        ("Surface Grime", "Dark handling marks on edges, cuffs and handles"),
        ("Oil & Grease", "Food oil and hand-cream marks"),
        ("Water Spots", "Rain spots and rings"),
        ("Ink", "Pen marks — assessed carefully, as ink can set in leather"),
        ("Dye Transfer", "Denim blue rubbing onto light leather"),
        ("Mildew", "White bloom from storage in a humid cupboard"),
    ],
    "details": [
        ("Leather Type", "Nappa, suede, nubuck and coated leathers each get their own method."),
        ("Seams & Edges", "Edge paint and stitched seams are cleaned without lifting or fraying."),
        ("Hardware", "Zips, studs and buckles are cleaned and checked for smooth action."),
    ],
    "before_after": [
        ("Dull, Dry Surface", "Leather that looks tired and feels stiff.", "Surface clean and conditioning by hand.", "Supple leather with its natural sheen back."),
        ("Handling Marks", "Dark marks on edges from hands and daily use.", "Targeted leather-safe cleaning on the soiled areas.", "Even colour along the edges."),
        ("Storage Bloom", "White mildew bloom after storage.", "Gentle cleaning and conditioning.", "Clean, fresh leather ready to use."),
    ],
    "related": ["leather-jacket", "handbag-leather", "leather-shoes", "suede-leather-shoes", "jacket", "boots-mid-length"],
    "banner": None,
    "photos": {
        "hero": {"src": "images/studio/covered-aisle.webp", "alt": "Cleaned garments hanging in protective covers at a garment care facility"},
    },
    "studio_label": "Leather Care",
}

PROFILES["home"] = {
    "category": "Home Textiles",
    "parent": "blanket-quilt-cleaning",
    "svc_short_desc": "Professional dryclean for your {noun}, which a home machine cannot handle properly.",
    "svc_long_desc": "Big household textiles are too bulky for a home machine and hard to dry properly on a balcony. At Wash4You they are cleaned on commercial machines with the capacity to handle them, dried completely so nothing smells damp, and folded for storage.",
    "includes": [
        "Size, fabric & filling check",
        "Stain & spot pre-treatment where applicable",
        "Professional cleaning on commercial machines",
        "Thorough drying — no dampness left",
        "Finishing & folding",
        "Protective packaging for storage",
    ],
    "turnaround": "48 hours",
    "compare_protect": "Deep clean of dust & allergens",
    "why": {
        "eyebrow": "Home Fabric Care",
        "subtitle": "Big household textiles collect dust, sweat and allergens, and they are exactly the items a home machine and a balcony cannot deal with. Here is why professional dryclean care makes sense:",
        "points": [
            ("Real Machine Capacity", "Commercial machines have room to clean bulky pieces evenly, not just the outer layer."),
            ("Dried All the Way Through", "Thick fabric and filling are dried completely, so nothing goes into storage damp."),
            ("Dust & Allergens Out", "A deep clean removes the dust and mites that build up over a season."),
            ("Filling Stays Even", "Fillings are handled so they do not bunch into lumps."),
            ("Colour & Fabric Protected", "Colours and finishes are assessed before cleaning so nothing fades or shrinks."),
            ("Ready to Store", "Returned folded and packed, ready for the cupboard or the bed."),
        ],
    },
    "stains": [
        ("Food & Drink", "Tea and snack spills from use in bed"),
        ("Sweat & Body Oils", "Yellowing where the fabric meets skin"),
        ("Dust & Allergens", "Built-up dust and mites from months of use"),
        ("Storage Smell", "Mustiness after a season in a trunk"),
        ("Pet Hair", "Hair and dander caught in the fabric"),
        ("Water Marks", "Rings from spills or a leaking cupboard"),
    ],
    "details": [
        ("Size & Weight", "Measured and checked so it is cleaned on a machine with the right capacity."),
        ("Drying", "Dried fully through the thickest part so no damp is sealed into storage."),
        ("Folding & Packing", "Folded for storage and packed so it stays clean until you need it."),
    ],
    "before_after": [
        ("Out of Storage", "Bedding that smells musty after a season packed away.", "Professional clean and complete drying.", "Fresh, soft and ready for the bed."),
        ("Everyday Yellowing", "Yellowed edges where the fabric meets skin.", "Targeted pre-treatment, then a deep clean.", "Brighter, fresher fabric."),
        ("Dust Build-Up", "A season of dust and allergens in the fabric.", "Deep clean on commercial machines.", "Clean, dust-free and fresh."),
    ],
    "related": ["double-blanket", "single-blanket", "comforter-double", "curtain", "double-bed-sheet", "carpet"],
    "banner": {"src": "images/studio/folded-table.webp", "alt": "Neatly folded household textiles on a packing table", "caption": "Dried through, folded and packed for storage"},
}

PROFILES["carpet"] = {
    "category": "Home Textiles",
    "parent": "carpet-cleaning",
    "care": "carpet care",
    "eyebrow": "Professional Carpet Care",
    "svc_name": "Carpet Deep Cleaning",
    "svc_short": "Carpet Cleaning",
    "svc_tagline": "Dust Extraction & Deep Clean",
    "svc_short_desc": "Deep extraction cleaning for rugs and carpets, priced per square foot.",
    "svc_long_desc": "Your {noun} is collected, dusted, deep-cleaned with extraction methods that pull dirt out of the pile rather than pushing it in, dried completely and returned rolled.",
    "includes": [
        "Size, fibre & backing check",
        "Dry dusting of the pile",
        "Spot pre-treatment where applicable",
        "Deep extraction cleaning",
        "Complete drying",
        "Rolled & packed for delivery",
    ],
    "turnaround": "48 hours",
    "studio": {
        "eyebrow": "Inside Wash4You",
        "title": "How Wash4You Cleans Your {name}",
        "subtitle": "A carpet cannot be cleaned properly on the floor it lies on. It is collected, cleaned at the Wash4You studio, dried through and returned rolled.",
        "points": [
            ("Dusted first", "Loose grit is removed from the pile before any liquid touches it."),
            ("Tagged from pickup to delivery", "Measured and tagged at your door, so you know exactly what is being cleaned."),
            ("Extraction cleaning", "Dirt is pulled out of the pile and backing, not spread around it."),
            ("Dried completely", "Dried all the way to the backing so it never goes back down damp."),
        ],
    },
    "why": {
        "eyebrow": "Carpet Care",
        "subtitle": "Carpets hold far more dust and grit than they show. Here is why professional carpet cleaning is worth doing once or twice a year:",
        "points": [
            ("Grit Out of the Pile", "Grit cuts carpet fibres from below; dusting and extraction remove it."),
            ("Allergens Removed", "Dust, mites and pet dander are cleaned out, not just vacuumed from the surface."),
            ("Colours Revived", "A deep clean lifts the grey film that dulls colour over time."),
            ("Dried Properly", "Complete drying avoids the damp smell of a carpet washed at home."),
            ("Backing Protected", "Fibre and backing are assessed so the carpet keeps its shape."),
            ("No Mess at Home", "We take it away and bring it back; nothing is soaked on your floor."),
        ],
    },
    "stains": [
        ("Food & Drink", "Tea, coffee, juice and snack spills"),
        ("Mud & Footwear", "Tracked-in mud and grit"),
        ("Pet Accidents", "Pet stains and odour"),
        ("Oil & Grease", "Food oil and cosmetic marks"),
        ("Ink & Crayon", "Children's pens and crayons"),
        ("Traffic Lanes", "Grey paths where people walk every day"),
    ],
    "details": [
        ("Fibre Type", "Wool, silk, synthetic and blends are identified first; each needs a different method."),
        ("Fringes & Edges", "Fringes are cleaned and combed out; edges are checked for fraying."),
        ("Pile Direction", "The pile is groomed in its natural direction as it dries."),
    ],
    "before_after": [
        ("Grey Traffic Lanes", "Walking paths that have gone visibly grey.", "Dusting, pre-treatment and extraction cleaning.", "Even colour across the carpet."),
        ("Tea Spill", "A spill that dried into a brown ring.", "Spot pre-treatment before the deep clean.", "Ring treated and the area blended back in."),
        ("Musty Smell", "A carpet that smells damp and stale.", "Deep clean and complete drying.", "Fresh-smelling carpet."),
    ],
    "related": ["curtain", "double-blanket", "comforter-double", "bed-spread-double", "single-blanket", "double-bed-sheet"],
    "banner": None,
    "photos": {
        "hero": {"src": "images/studio/washers.webp", "alt": "Commercial cleaning machines at a laundry facility"},
    },
    "studio_label": "Carpet Care",
    "process": [
        ("Book Your Pickup", "Book online or on WhatsApp and tell us the carpet size."),
        ("Doorstep Collection", "Measured, tagged and rolled at your door."),
        ("Inspection", "Fibre, backing, fringes and stains are checked."),
        ("Dry Dusting", "Grit is removed from the pile before cleaning."),
        ("Extraction Cleaning", "Deep-cleaned to pull dirt out of the pile and backing."),
        ("Complete Drying", "Dried through to the backing, pile groomed as it dries."),
        ("Quality Check", "Checked for evenness, smell and dryness."),
        ("Rolled & Delivered", "Rolled, packed and delivered back to your door."),
    ],
}

PROFILES["footwear"] = {
    "category": "Footwear Cleaning",
    "parent": "shoe-cleaning",
    "care": "shoe care",
    "eyebrow": "Professional Shoe Care",
    "svc_name": "Shoe Deep Cleaning",
    "svc_short": "Shoe Cleaning",
    "svc_tagline": "Hand-Cleaned by Material",
    "svc_short_desc": "Hand cleaning for {noun}, by material, with soles, laces and insoles included.",
    "svc_long_desc": "Every pair is cleaned by hand at a Wash4You store, never thrown in a washing machine. Uppers are cleaned with products suited to their material, soles and midsoles are scrubbed, laces washed, insoles freshened, and the pair is dried at room temperature.",
    "includes": [
        "Material & condition check",
        "Upper cleaning by material",
        "Sole & midsole scrub",
        "Lace wash & insole refresh",
        "Deodorising",
        "Air-dried at room temperature",
    ],
    "studio": {
        "eyebrow": "Inside Wash4You",
        "title": "How Wash4You Cleans Your {name}",
        "subtitle": "Shoes are cleaned by hand at our Sushant Lok and Sector 49 stores — not in a washing machine. These are real before-and-after results from our own bench.",
        "points": [
            ("Cleaned by hand", "Every pair is worked on by hand with brushes and products suited to its material."),
            ("Tagged from pickup to delivery", "Each pair is counted at your door and tagged so it never gets mixed up."),
            ("Sole to lace", "Uppers, soles, midsoles, laces and insoles are all cleaned, not just the parts you see."),
            ("Dried at room temperature", "No heat, which warps soles and cracks glue."),
        ],
    },
    "why": {
        "eyebrow": "Footwear Care",
        "subtitle": "A washing machine breaks down glue, warps soles and ruins leather and suede. Here is why professional shoe care is the better way to clean them:",
        "points": [
            ("No Machine Damage", "Hand cleaning means no tumbling to loosen glue or crush heel counters."),
            ("Right Product per Material", "Leather, suede, mesh, knit and canvas each get their own cleaner."),
            ("Soles Brightened", "Midsoles and outsoles are scrubbed back towards their original colour."),
            ("Odour Treated", "Insoles are freshened and pairs deodorised, not just cleaned outside."),
            ("Shape Kept", "Pairs are dried at room temperature with their shape supported."),
            ("Done at Our Stores", "Cleaned at our own Gurugram stores, not sent out."),
        ],
    },
    "stains": [
        ("Mud & Dust", "Dried mud, rain splashes and street dust"),
        ("Grass & Ground Marks", "Park, pitch and lawn stains"),
        ("Scuffs", "Black scuff marks on toes and sides"),
        ("Yellowed Soles", "Discoloured midsoles and rubber"),
        ("Food & Drink", "Spills on uppers and laces"),
        ("Odour", "Sweat and odour inside the shoe"),
    ],
    "details": [
        ("Uppers", "Leather, suede, mesh and knit uppers are each cleaned with their own product and brush."),
        ("Soles & Midsoles", "Scrubbed to lift grime from the texture and the edges."),
        ("Laces & Insoles", "Laces are washed separately and insoles freshened."),
    ],
    "before_after": [
        ("Muddy After the Rain", "Dried mud caked on uppers and soles.", "Dry brushing, then hand cleaning by material.", "Clean uppers and soles."),
        ("Grey, Tired Soles", "Midsoles gone grey and dull with wear.", "Sole and midsole scrub.", "Brighter, cleaner soles."),
        ("Odour", "A pair that smells even after airing.", "Insole refresh and deodorising.", "Fresh inside and out."),
    ],
    "ba_photos": [
        {"before": "images/proof/sneaker-nike-before.webp", "after": "images/proof/sneaker-nike-after.webp", "alt": "Suede sneaker", "caption": "Suede sneaker — cleaned by hand at Wash4You"},
        {"before": "images/proof/sneaker-hoka-before.webp", "after": "images/proof/sneaker-hoka-after.webp", "alt": "White running shoes", "caption": "White running shoes — uppers, midsoles and laces"},
    ],
    "related": ["sneakers", "sports-shoes", "leather-shoes", "suede-leather-shoes", "boots-mid-length", "sneaker-ankle"],
    "banner": None,
    "photos": {
        "hero": {"src": "images/proof/sneaker-hoka-after.webp", "alt": "White running shoes after hand cleaning at a Wash4You store"},
        "studio": [
            {"src": "images/proof/sneaker-hoka-after.webp", "alt": "Running shoes after cleaning at Wash4You", "caption": "Cleaned by hand at Wash4You"},
            {"src": "images/proof/sneaker-nike-after.webp", "alt": "Suede sneaker after cleaning at Wash4You", "caption": "Suede, cleaned by material"},
            {"src": "images/hero-wall/leather-shoes.webp", "alt": "Polished leather shoes", "caption": "Leather conditioned, not soaked"},
        ],
    },
    "studio_label": "Shoe Care",
    "process": [
        ("Book Your Pickup", "Book online or on WhatsApp."),
        ("Doorstep Collection", "Your pairs are counted and tagged at your door."),
        ("Material Check", "Uppers, soles and any damage are noted before cleaning."),
        ("Dry Brushing", "Loose dirt and mud are brushed out first."),
        ("Hand Cleaning", "Uppers, soles and midsoles cleaned by hand, by material."),
        ("Laces & Insoles", "Laces washed, insoles freshened, pair deodorised."),
        ("Room-Temperature Drying", "Dried with shape supported, no heat."),
        ("Packed & Delivered", "Checked, packed and delivered back to your door."),
    ],
}

PROFILES["laundry"] = {
    "category": "Laundry Services",
    "parent": "eco-friendly-laundry",
    "care": "laundry care",
    "eyebrow": "Professional Laundry Care",
    "svc_name": None,  # the item's own name
    "svc_short": "Laundry",
    "svc_tagline": "Sorted, Washed & Finished",
    "svc_short_desc": "{noun}",
    "svc_long_desc": "{noun}",
    "includes": [],
    "turnaround": "24 hours",
    "studio": {
        "eyebrow": "Inside Wash4You",
        "title": "How Wash4You Handles Your Laundry",
        "subtitle": "Your laundry never shares a machine with anyone else's. It is tagged at your door, sorted, washed on commercial machines with eco-friendly detergents, and finished before it comes home.",
        "points": [
            ("Your load only", "Each customer's laundry is washed separately, never mixed with another order."),
            ("Tagged from pickup to delivery", "Counted at your door and tagged through every stage."),
            ("Commercial machines", "Washed on commercial machines with biodegradable, skin-safe detergents."),
            ("Finished properly", "Folded or steam-ironed, checked and packed before delivery."),
        ],
    },
    "why": {
        "eyebrow": "Laundry, Done Properly",
        "subtitle": "Laundry is the chore that takes the most time for the least reward. Here is what professional laundry care does differently:",
        "points": [
            ("Sorted First", "Whites, darks and delicates are separated before anything is washed."),
            ("Right Temperature", "Wash temperature is set by fabric, not by habit."),
            ("Eco-Friendly Detergents", "Biodegradable, skin-safe detergents that are gentle enough for children's clothes."),
            ("Fully Dried", "Dried completely, so nothing comes back damp or musty."),
            ("Neatly Finished", "Folded or steam-ironed so it goes straight into the wardrobe."),
            ("Your Time Back", "No washing, drying or folding at home — just pickup and delivery."),
        ],
    },
    "stains": None,
    "details": None,
    "before_after": None,
    "related": ["wash-and-fold", "wash-and-steam-iron", "premium-laundry", "woollen-laundry", "shirt", "single-bed-sheet"],
    "banner": None,
    "photos": {
        "hero": {"src": "images/studio/washers.webp", "alt": "Commercial washer-extractors at a laundry facility"},
    },
    "studio_label": "Laundry Studio",
    "process": [
        ("Book Your Pickup", "Book online or on WhatsApp."),
        ("Doorstep Collection", "Your laundry is collected, weighed or counted, and tagged."),
        ("Sorting", "Separated by colour, fabric and care label."),
        ("Pocket & Stain Check", "Pockets emptied, visible stains pre-treated."),
        ("Washing", "Washed on commercial machines with eco-friendly detergents."),
        ("Drying", "Dried completely at the right temperature for the fabric."),
        ("Finishing", "Folded or steam-ironed, then checked."),
        ("Packed & Delivered", "Packed and delivered back to your door."),
    ],
}

# ---------------------------------------------------------------------------
# Products. `noun` is how the item reads mid-sentence; `plural` titles the H1.
# ---------------------------------------------------------------------------

PRODUCTS: list[dict] = [
    # Everyday wear
    {"slug": "pant-trouser", "profile": "everyday", "noun": "trousers", "plural": "Trousers", "iron": "iron-pant-trouser",
     "seo": "Trouser Dry Cleaning",
     "best_for": ["Office trousers worn through a working week", "Wool, poly-wool and linen trousers", "Trousers with food or grease marks", "Formal trousers that need a sharp crease"],
     "details": [("Crease Line", "The front crease is set along the original line, never doubled."), ("Waistband & Seat", "Waistband and seat are pressed separately so they sit flat without shine."), ("Hems & Turn-ups", "Hems and turn-ups are pressed straight and even.")],
     "faq": ("Will my trousers come back with a crease?", "Yes, if they were made with one. Formal trousers are pressed with the crease set along the original line; casual trousers and chinos are pressed flat unless you ask otherwise.")},
    {"slug": "shirt", "profile": "everyday", "noun": "shirts", "plural": "Shirts", "iron": "iron-shirt",
     "seo": "Shirt Dry Cleaning",
     "best_for": ["Formal office shirts", "Linen, silk and premium cotton shirts", "Shirts with collar and cuff grime", "Shirts with sweat or deodorant marks"],
     "details": [("Collar & Cuffs", "Collars and cuffs are pre-treated for grime and pressed crisp, with collar points kept sharp."), ("Buttons", "Buttons are checked before cleaning and pressed around, never over."), ("Placket & Yoke", "The button placket and back yoke are pressed flat and straight.")],
     "faq": ("Can you remove collar and underarm yellowing from shirts?", "Collar grime and underarm marks are pre-treated before the dryclean. Fresh build-up usually lifts well; yellowing that has been there for months may lighten rather than disappear completely.")},
    {"slug": "t-shirt", "profile": "everyday", "noun": "T-shirts", "plural": "T-Shirts", "iron": "iron-t-shirt",
     "seo": "T-Shirt Dry Cleaning",
     "best_for": ["Premium cotton and polo T-shirts", "Printed and graphic T-shirts", "T-shirts with food or sweat marks", "Pieces that lose shape in a home wash"],
     "details": [("Necklines", "Necklines and ribbing are shaped so they do not stretch open."), ("Prints", "Printed areas are never pressed directly, so prints do not crack or stick."), ("Polo Collars", "Polo collars and plackets are pressed flat and even.")],
     "faq": ("Will the print on my T-shirt be damaged?", "No. Printed areas are cleaned gently and pressed from the reverse, or not pressed at all, so prints do not crack, fade or stick to the iron.")},
    {"slug": "top", "profile": "everyday", "noun": "tops", "plural": "Tops",
     "seo": "Top Dry Cleaning",
     "best_for": ["Silk, satin and georgette tops", "Tops with lace, frills or embellishment", "Party and office tops", "Delicate fabrics that should not be machine-washed"],
     "details": [("Delicate Fabrics", "Silk, satin and chiffon are handled gently and pressed at low heat."), ("Trims & Lace", "Lace, frills and beading are checked before cleaning and finished by hand."), ("Straps & Ties", "Straps and ties are pressed flat and kept untangled.")],
     "faq": ("Can you clean delicate or embellished tops?", "Yes. Delicate and embellished tops are inspected first, drycleaned gently and finished by hand around any lace, beads or sequins.")},
    {"slug": "dress", "profile": "everyday", "noun": "dresses", "plural": "Dresses", "iron": "iron-dress",
     "seo": "Dress Dry Cleaning",
     "best_for": ["Party, cocktail and evening dresses", "Silk, satin and chiffon dresses", "Dresses with lining, pleats or embellishment", "Dresses with food, drink or makeup marks"],
     "details": [("Pleats & Gathers", "Pleats are set by hand and gathers steamed so the skirt falls properly."), ("Linings", "Linings are cleaned with the dress and pressed so they never hang below the hem."), ("Zips & Fastenings", "Concealed zips, hooks and buttons are checked and pressed around.")],
     "faq": ("Can you dryclean a dress with sequins or beading?", "Yes. Embellished dresses are checked before cleaning, drycleaned gently and finished from the reverse so beads and sequins are not crushed or loosened.")},
    {"slug": "palazzo", "profile": "everyday", "noun": "palazzos", "plural": "Palazzos",
     "seo": "Palazzo Dry Cleaning",
     "best_for": ["Rayon, georgette and silk palazzos", "Pleated and flared palazzos", "Palazzos worn with kurtas", "Fabrics that shrink or twist at home"],
     "details": [("Flare & Fall", "The legs are steamed so the flare falls evenly."), ("Pleats", "Pleats are set by hand along their original folds."), ("Waistband", "Elastic and drawstring waistbands are pressed flat without stretching.")],
     "faq": ("Will my palazzo shrink?", "No. Rayon and georgette palazzos shrink easily in a hot home wash; a professional dryclean avoids water and heat, so the length and fit stay the same.")},

    # Tailored
    {"slug": "coat", "profile": "tailored", "noun": "coat", "plural": "Coats", "iron": "iron-coat",
     "seo": "Coat Dry Cleaning",
     "best_for": ["Blazers and sports coats", "Wool and tweed coats", "Coats with food or rain marks", "Coats that have lost their shape"],
     "faq": ("Should a blazer be drycleaned or can I wash it?", "A blazer or coat should be drycleaned. The canvas and interfacing inside shrink at a different rate from the outer fabric in water, which leaves bubbles and a distorted shape.")},
    {"slug": "men-suit-2pcs", "profile": "tailored", "noun": "suit", "plural": "Two-Piece Suits",
     "seo": "Suit Dry Cleaning", "h1": "Professional Dryclean Care for Your Two-Piece Suit",
     "best_for": ["Business and wedding suits", "Wool, linen and blended suits", "Suits after a function or a long week", "Suits with spills or collar marks"],
     "faq": ("Are the jacket and trousers cleaned together?", "Yes. Both pieces of a suit are drycleaned together so the colour stays matched, then the jacket is shaped and the trousers creased separately.")},
    {"slug": "men-suit-3pcs", "profile": "tailored", "noun": "suit", "plural": "Three-Piece Suits",
     "seo": "Three-Piece Suit Dry Cleaning", "h1": "Professional Dryclean Care for Your Three-Piece Suit",
     "best_for": ["Wedding and occasion three-piece suits", "Wool and blended suits with waistcoats", "Suits worn to long events", "Suits going into storage"],
     "details": [("Waistcoat", "The waistcoat's back panel and buckle are checked, and its points pressed sharp."), ("Buttons & Linings", "Horn and metal buttons are checked and linings are smoothed so they never pull."), ("Trouser Creases", "Creases are set along the original line, with the waistband and seat pressed separately.")],
     "faq": ("Is the waistcoat included?", "Yes. The Men Suit 3 Pcs price covers the jacket, waistcoat and trousers, all drycleaned together so the colour stays matched.")},
    {"slug": "long-coat", "profile": "tailored", "noun": "long coat", "plural": "Long Coats",
     "seo": "Long Coat Dry Cleaning",
     "best_for": ["Wool and cashmere overcoats", "Trench coats", "Winter coats before or after the season", "Coats with collar or cuff grime"],
     "details": [("Collar & Cuffs", "Collars and cuffs are pre-treated for grime and pressed into shape."), ("Belt & Buttons", "Belts, buckles and buttons are checked and cleaned alongside the coat."), ("Length & Hem", "The full length is steamed so the coat hangs straight to the hem.")],
     "faq": ("When should I get my winter coat drycleaned?", "Before you store it at the end of winter. Dirt and body oils left in the wool over summer attract moths and set in, so a clean coat stores much better.")},
    {"slug": "jacket", "profile": "tailored", "noun": "jacket", "plural": "Jackets",
     "seo": "Jacket Dry Cleaning",
     "best_for": ["Casual and bomber jackets", "Nehru and bandhgala jackets", "Padded and quilted jackets", "Jackets with collar or cuff grime"],
     "details": [("Padding & Quilting", "Padded and quilted jackets are cleaned so the fill stays even."), ("Zips & Hardware", "Zips, poppers and toggles are checked and cleaned."), ("Collar & Cuffs", "Collar and cuff grime is pre-treated before the dryclean.")],
     "faq": ("Can you clean a padded or puffer jacket?", "Yes. Padded jackets are cleaned and dried so the fill does not clump, then finished with light steam. We check the care label first and tell you if a different method suits it better.")},

    # Ethnic
    {"slug": "sherwani", "profile": "ethnic", "noun": "sherwani", "plural": "Sherwanis",
     "seo": "Sherwani Dry Cleaning",
     "best_for": ["Wedding and reception sherwanis", "Silk, brocade and velvet sherwanis", "Sherwanis with hand embroidery", "Sherwanis going back into storage"],
     "details": [("Embroidery & Buttons", "Hand embroidery and decorative buttons are checked before cleaning and finished from the reverse."), ("Collar", "The band collar is shaped so it stands properly."), ("Length & Fall", "The full length is steamed so the sherwani hangs straight.")],
     "faq": ("Can you clean a heavily embroidered wedding sherwani?", "Yes. Heavy work is inspected first, drycleaned gently and finished from the reverse. Loose buttons or threads are flagged to you before we start.")},
    {"slug": "kurta", "profile": "ethnic", "noun": "kurta", "plural": "Kurtas",
     "seo": "Kurta Dry Cleaning",
     "best_for": ["Cotton, linen and silk kurtas", "Office and festive kurtas", "Kurtas with sweat or food marks", "Kurtas that fade in a home wash"],
     "details": [("Collar & Placket", "The collar and button placket are pressed flat and straight."), ("Side Slits & Hem", "Side slits and the hem are pressed straight so the kurta falls evenly."), ("Colour", "Dyed fabrics are checked for bleeding before cleaning.")],
     "faq": ("Should a cotton kurta be drycleaned?", "A plain cotton kurta can be laundered, but a dryclean keeps colour and shape better — especially for dyed, printed or silk-blend kurtas that fade or shrink in water.")},
    {"slug": "kurta-fancy", "profile": "ethnic", "noun": "kurta", "plural": "Designer Kurtas",
     "seo": "Designer Kurta Dry Cleaning", "h1": "Professional Dryclean Care for Your Designer Kurta",
     "best_for": ["Festive and designer kurtas", "Kurtas with embroidery or sequins", "Silk and chanderi kurtas", "Kurtas worn to weddings and functions"],
     "faq": ("What counts as a 'fancy' kurta?", "Any kurta with embroidery, sequins, mirror work, silk or a designer finish. These need gentler handling than an everyday cotton kurta, which is why they have their own rate.")},
    {"slug": "kurta-heavy", "profile": "ethnic", "noun": "kurta", "plural": "Heavy Kurtas",
     "seo": "Heavy Kurta Dry Cleaning", "h1": "Professional Dryclean Care for Your Heavy Work Kurta",
     "best_for": ["Heavily embroidered kurtas", "Kurtas with zardozi or stone work", "Velvet and brocade kurtas", "Groom and wedding-party kurtas"],
     "faq": ("Why is heavy work priced differently?", "Heavy zardozi, stone and bead work takes longer to inspect, clean around and finish by hand, and needs more care to avoid loosening the work.")},
    {"slug": "salwar", "profile": "ethnic", "noun": "salwar", "plural": "Salwars", "iron": "iron-salwar",
     "seo": "Salwar Dry Cleaning",
     "best_for": ["Silk and cotton-silk salwars", "Salwars from a matching suit set", "Salwars with sweat or food marks", "Fabrics that fade or shrink at home"],
     "details": [("Pleats & Gathers", "Gathers at the waist are steamed so they fall evenly."), ("Ankle Cuffs", "Cuffs and hems are pressed straight."), ("Matching Set", "Cleaned the same way as its kurta so the colours stay matched.")],
     "faq": ("Should I send the full suit together?", "Yes — sending the kurta, salwar and dupatta together means they are all cleaned the same way and the colours stay matched.")},
    {"slug": "saree", "profile": "ethnic", "noun": "saree", "plural": "Sarees", "iron": "iron-saree",
     "seo": "Saree Dry Cleaning",
     "best_for": ["Silk, Banarasi and Kanjeevaram sarees", "Georgette, chiffon and crepe sarees", "Sarees with zari borders or embroidery", "Sarees worn to weddings and functions"],
     "details": [("Pallu & Border", "The pallu and border are pressed straight and the zari protected."), ("Silk Sheen", "Silk is handled so it keeps its natural lustre without water marks."), ("Fold & Storage", "Folded with tissue along soft lines so it stores without hard creases.")],
     "faq": ("Is it safe to dryclean a silk saree?", "Yes — for silk, especially Banarasi and Kanjeevaram with zari, a professional dryclean is the safest way to clean it. Water can make silk dyes run and tarnish zari.")},
    {"slug": "lehenga", "profile": "ethnic", "noun": "lehenga", "plural": "Lehengas", "iron": "iron-lehenga",
     "seo": "Lehenga Dry Cleaning",
     "best_for": ["Bridal and wedding lehengas", "Lehengas with heavy embroidery", "Net, silk and velvet lehengas", "Lehengas going into storage"],
     "details": [("Can-Can & Layers", "Can-can and lining layers are checked and shaped so the flare returns."), ("Heavy Work", "Zardozi, stones and sequins are finished from the reverse, never pressed flat."), ("Choli & Dupatta", "Choli and dupatta can be cleaned together so the set stays matched.")],
     "faq": ("Can you clean a bridal lehenga?", "Yes. Bridal lehengas are inspected piece by piece, drycleaned gently and finished by hand. Loose stones or threads are flagged to you before cleaning, and the lehenga is returned folded with tissue for storage.")},
    {"slug": "dupatta", "profile": "ethnic", "noun": "dupatta", "plural": "Dupattas",
     "seo": "Dupatta Dry Cleaning",
     "best_for": ["Silk, chiffon and georgette dupattas", "Dupattas with borders or embroidery", "Dupattas with makeup marks", "Dupattas from a suit set"],
     "details": [("Borders & Lace", "Borders and lace edges are pressed straight."), ("Light Fabrics", "Chiffon and net are handled gently so they do not snag or stretch."), ("Makeup Marks", "Foundation and kajal marks along the edge are pre-treated.")],
     "faq": ("Can makeup marks on a dupatta be removed?", "Makeup is pre-treated before the dryclean. Fresh foundation and lipstick usually lift well; marks left for a long time may lighten rather than disappear completely.")},
    {"slug": "blouse", "profile": "ethnic", "noun": "blouse", "plural": "Blouses", "iron": "iron-blouse",
     "img": "images/pricing/saree.png", "seo": "Blouse Dry Cleaning",
     "best_for": ["Saree and lehenga blouses", "Silk and brocade blouses", "Blouses with embroidery or mirror work", "Blouses with sweat marks"],
     "details": [("Shape & Darts", "Darts and padding are shaped so the blouse keeps its fit."), ("Hooks & Tie-Backs", "Hooks, buttons and tie-backs are checked and pressed around."), ("Sweat Marks", "Underarm areas are pre-treated before the dryclean.")],
     "faq": ("Should the blouse be cleaned with its saree?", "Yes, ideally. Cleaning the blouse and saree together keeps the colours matched.")},

    # Knitwear
    {"slug": "sweater", "profile": "knit", "noun": "sweater", "plural": "Sweaters",
     "seo": "Sweater Dry Cleaning",
     "best_for": ["Wool, cashmere and merino sweaters", "Hand-knitted sweaters", "Sweaters going into or out of storage", "Sweaters with food or makeup marks"],
     "faq": ("Will my sweater shrink?", "No. Sweaters shrink from hot water and tumble drying. A professional dryclean uses neither, and each sweater is blocked back to its size.")},
    {"slug": "cardigan", "profile": "knit", "noun": "cardigan", "plural": "Cardigans",
     "seo": "Cardigan Dry Cleaning",
     "best_for": ["Wool and cashmere cardigans", "Cardigans with buttons or trims", "Knitwear worn over office clothes", "Pieces going into storage"],
     "details": [("Button Bands", "Button bands are shaped so they lie flat and straight."), ("Buttons", "Buttons are checked and cleaned around."), ("Cuffs & Hem", "Ribbing is blocked back so it does not flare.")],
     "faq": ("Can you clean a cashmere cardigan?", "Yes. Cashmere is drycleaned gently, blocked to size and finished with light steam so it stays soft.")},
    {"slug": "sweatshirt", "profile": "knit", "noun": "sweatshirt", "plural": "Sweatshirts",
     "seo": "Sweatshirt Dry Cleaning",
     "best_for": ["Fleece and cotton sweatshirts", "Hoodies and printed sweatshirts", "Heavy pieces that take days to dry at home", "Sweatshirts with food or sweat marks"],
     "details": [("Fleece Inside", "Fleece lining is lifted, not flattened."), ("Prints", "Printed areas are never pressed directly."), ("Hood & Cuffs", "Hoods, cuffs and waistbands are shaped so they hold their grip.")],
     "faq": ("Will the fleece stay soft?", "Yes. The fleece is not tumble-dried hot, so it keeps its soft, brushed feel.")},
    {"slug": "shawl", "profile": "knit", "noun": "shawl", "plural": "Shawls",
     "seo": "Shawl Dry Cleaning",
     "best_for": ["Pashmina and wool shawls", "Embroidered and Kashmiri shawls", "Shawls going into storage", "Shawls with makeup or food marks"],
     "details": [("Fine Wool", "Pashmina and fine wool are handled gently to avoid pulls and felting."), ("Embroidery & Fringes", "Embroidery is protected and fringes combed out straight."), ("Storage", "Folded with tissue so it stores without creases or moth-attracting dirt.")],
     "faq": ("Can you clean a pashmina shawl?", "Yes. Pashmina is drycleaned gently, never scrubbed, and finished with light steam. Fringes are combed straight before it is folded for storage.")},

    # Leather
    {"slug": "leather-jacket", "profile": "leather", "noun": "leather jacket", "plural": "Leather Jackets",
     "seo": "Leather Jacket Cleaning", "h1": "Professional Leather Care for Your Leather Jacket",
     "best_for": ["Biker and bomber leather jackets", "Nappa and lambskin jackets", "Jackets with collar or cuff grime", "Jackets coming out of storage"],
     "faq": ("Can a leather jacket be drycleaned?", "Not with ordinary clothes. Leather goes through a separate specialist process with pH-balanced leather products and conditioning, because standard dryclean solvents and heat dry it out and crack it.")},
    {"slug": "handbag-leather", "profile": "leather", "noun": "leather handbag", "plural": "Leather Handbags",
     "seo": "Leather Handbag Cleaning", "h1": "Professional Leather Care for Your Handbag", "turnaround": "3–5 days",
     "category": "Bag Care",
     "best_for": ["Everyday leather handbags and totes", "Bags with handle and edge grime", "Light-coloured leather with dye transfer", "Bags coming out of storage"],
     "details": [("Handles & Edges", "Handles and edges take the most handling marks and are cleaned carefully."), ("Lining", "The lining is vacuumed and freshened."), ("Hardware", "Clasps, zips and feet are cleaned and checked.")],
     "faq": ("How long does handbag cleaning take?", "Leather handbags take 3 to 5 days, because the leather is cleaned, conditioned and left to settle before it is finished.")},

    # Home
    {"slug": "curtain", "profile": "home", "noun": "curtains", "plural": "Curtains", "parent": "curtains-cleaning",
     "seo": "Curtain Dry Cleaning",
     "best_for": ["Living and bedroom curtains", "Lined and blackout curtains", "Sheers and voiles", "Curtains that have not been cleaned in a year or more"],
     "details": [("Linings & Blackout", "Lined and blackout panels are dryclean or wet-cleaned depending on the backing, so it does not crack or peel."), ("Hooks & Eyelets", "Hooks are removed and eyelets checked before cleaning."), ("Length", "Panels are finished to hang straight to their full length.")],
     "faq": ("Do you take the curtains down and put them back up?", "Yes. Curtain cleaning includes free de-installation and re-installation — we take the curtains down and rehang them at no extra charge. Pricing is per panel of about 3.5 ft.")},
    {"slug": "single-blanket", "profile": "home", "noun": "blanket", "plural": "Single Blankets & Quilts",
     "seo": "Blanket Dry Cleaning", "h1": "Professional Dryclean Care for Your Single Blanket or Quilt",
     "best_for": ["Single wool and fleece blankets", "Single razais and quilts", "Blankets going into or out of storage", "Children's blankets"],
     "faq": ("When should blankets be cleaned?", "Before you put them away in spring and, ideally, before you bring them out in winter. Storing a blanket dirty traps sweat and dust that attract moths and mustiness.")},
    {"slug": "double-blanket", "profile": "home", "noun": "blanket", "plural": "Double Blankets & Quilts",
     "seo": "Double Blanket Dry Cleaning", "h1": "Professional Dryclean Care for Your Double Blanket or Quilt",
     "best_for": ["Double wool and mink blankets", "Double razais and quilts", "Heavy blankets that will not fit a home machine", "Seasonal cleaning before storage"],
     "faq": ("Can you clean a heavy razai?", "Yes. Heavy razais and quilts are cleaned on machines with the capacity to handle them and dried completely through the filling, which is almost impossible at home.")},
    {"slug": "comforter-double", "profile": "home", "noun": "comforter", "plural": "Double Comforters",
     "seo": "Comforter Dry Cleaning",
     "best_for": ["Double-bed comforters and duvets", "Microfibre and down-filled comforters", "Comforters used through a season", "Comforters that smell musty"],
     "details": [("Filling", "Filling is handled so it does not clump, then fluffed as it dries."), ("Drying", "Dried completely through the centre, where home drying always fails."), ("Covers & Piping", "Covers, piping and stitching are checked before cleaning.")],
     "faq": ("Will the filling clump?", "No. Comforters are dried slowly and completely with the filling fluffed as it dries, so it stays even.")},
    {"slug": "bed-spread-double", "profile": "home", "noun": "bedspread", "plural": "Double Bedspreads",
     "seo": "Bedspread Dry Cleaning",
     "best_for": ["Double bedspreads and bed covers", "Embroidered and quilted bedspreads", "Heavy cotton and silk bedspreads", "Bedspreads before guests or festivals"],
     "details": [("Embroidery & Quilting", "Embroidery and quilting stitches are protected during cleaning."), ("Colour", "Printed and dyed bedspreads are checked for bleeding before cleaning."), ("Size", "Cleaned on machines with room for a full double bedspread.")],
     "faq": ("Can you clean an embroidered or silk bedspread?", "Yes. Embroidered and silk bedspreads are drycleaned so the colours and work are protected, then finished and folded.")},
    {"slug": "single-bed-sheet", "profile": "home", "noun": "bed sheet", "plural": "Single Bed Sheets", "iron": "iron-single-bedsheet",
     "parent": "linen-cleaning", "seo": "Bed Sheet Dry Cleaning", "turnaround": T_DRYCLEAN,
     "best_for": ["Cotton and satin single bed sheets", "Printed and embroidered sheets", "Sheets with stains or yellowing", "Sheets for guest rooms"],
     "details": [("Fabric", "Cotton, satin and linen sheets are each cleaned at the right setting."), ("Crisp Finish", "Pressed flat and crisp, not just folded."), ("Folding", "Folded neatly and packed so it goes straight into the cupboard.")],
     "faq": ("Can I get bed sheets only ironed?", "Yes. If your sheets are already clean, choose Steam Press for a crisp, flat finish.")},
    {"slug": "double-bed-sheet", "profile": "home", "noun": "bed sheet", "plural": "Double Bed Sheets", "iron": "iron-double-bedsheet",
     "parent": "linen-cleaning", "seo": "Double Bed Sheet Dry Cleaning", "turnaround": T_DRYCLEAN,
     "best_for": ["Cotton, satin and linen double sheets", "Printed and embroidered sheets", "Sheets with stains or yellowing", "Sheets that need a hotel-crisp finish"],
     "details": [("Fabric", "Cotton, satin and linen sheets are each cleaned at the right setting."), ("Crisp Finish", "Pressed flat and crisp across the full width."), ("Folding", "Folded neatly and packed for the cupboard.")],
     "faq": ("Can I get bed sheets only ironed?", "Yes. If your sheets are already clean, choose Steam Press for a crisp, flat finish.")},

    # Carpet
    {"slug": "carpet", "profile": "carpet", "noun": "carpet", "plural": "Carpets & Rugs",
     "seo": "Carpet Cleaning", "h1": "Professional Carpet Cleaning, Collected From Your Door",
     "best_for": ["Wool, silk and synthetic rugs", "Living-room and bedroom carpets", "Carpets with spills or pet stains", "Rugs that smell dusty or damp"],
     "faq": ("Do I need to measure my carpet before booking?", "It helps. Tell us the approximate size when you book and we will give you an estimate; the carpet is measured again at pickup and the final price confirmed before cleaning.")},

    # Footwear
    {"slug": "sports-shoes", "profile": "footwear", "noun": "sports shoes", "plural": "Sports Shoes",
     "seo": "Sports Shoe Cleaning", "h1": "Professional Shoe Care for Your Sports Shoes",
     "best_for": ["Running and training shoes", "Mesh and knit uppers", "Muddy or dusty outdoor shoes", "Shoes with odour"],
     "faq": ("Can you clean running shoes with mesh uppers?", "Yes. Mesh and knit uppers are cleaned by hand with soft brushes so the weave does not fray, and dried at room temperature so the sole glue stays intact.")},
    {"slug": "sneakers", "profile": "footwear", "noun": "sneakers", "plural": "Sneakers",
     "seo": "Sneaker Cleaning", "h1": "Professional Shoe Care for Your Sneakers",
     "best_for": ["White and light-coloured sneakers", "Canvas, leather and suede sneakers", "Sneakers with yellowed soles", "Collector and premium pairs"],
     "faq": ("Can you whiten yellowed sneaker soles?", "Soles and midsoles are scrubbed to lift grime, which brightens them noticeably. Yellowing caused by rubber oxidising with age can lighten but may not return to factory white.")},
    {"slug": "leather-shoes", "profile": "footwear", "noun": "leather shoes", "plural": "Leather Shoes",
     "seo": "Leather Shoe Cleaning", "h1": "Professional Shoe Care for Your Leather Shoes",
     "best_for": ["Formal Oxfords, Derbies and loafers", "Leather office shoes", "Shoes with salt or water marks", "Pairs that have gone dull and dry"],
     "details": [("Leather Uppers", "Cleaned with leather-safe products, then conditioned so they do not crack."), ("Welt & Edges", "Welts and edges are cleaned and dressed."), ("Polish", "Finished with a polish that matches the leather.")],
     "faq": ("Do you polish leather shoes?", "Yes. After cleaning and conditioning, leather shoes are finished with a polish suited to their colour.")},
    {"slug": "suede-leather-shoes", "profile": "footwear", "noun": "suede shoes", "plural": "Suede Shoes",
     "seo": "Suede Shoe Cleaning", "h1": "Professional Shoe Care for Your Suede Shoes",
     "best_for": ["Suede loafers, boots and sneakers", "Nubuck shoes", "Suede with water marks or flattened nap", "Light suede that has gone grey"],
     "details": [("Nap", "The suede nap is brushed and lifted, not soaked flat."), ("Water Marks", "Water rings are blended out across the whole panel."), ("Colour", "Colour is refreshed where the suede has gone patchy.")],
     "faq": ("Can suede be cleaned without damaging it?", "Yes, with the right method. Suede is dry-brushed and cleaned with suede-specific products, never soaked, and the nap is lifted as it dries.")},
    {"slug": "sneaker-ankle", "profile": "footwear", "noun": "high-top sneakers", "plural": "Ankle Sneakers",
     "seo": "High-Top Sneaker Cleaning", "h1": "Professional Shoe Care for Your High-Top Sneakers",
     "best_for": ["High-top and ankle sneakers", "Basketball and skate shoes", "Canvas and leather high-tops", "Pairs with collar and lining grime"],
     "details": [("Collar & Lining", "The padded collar and inner lining are cleaned, where high-tops collect the most grime."), ("Uppers", "Leather, canvas and suede panels are each cleaned with their own product."), ("Soles", "Soles and midsoles are scrubbed back towards their original colour.")],
     "faq": ("Why do high-tops cost more than regular sneakers?", "High-tops have more upper, a padded collar and more lining to clean, so each pair takes longer by hand.")},
    {"slug": "boots-mid-length", "profile": "footwear", "noun": "boots", "plural": "Boots",
     "seo": "Boot Cleaning", "h1": "Professional Shoe Care for Your Boots",
     "best_for": ["Leather and suede ankle and mid-length boots", "Chelsea and chukka boots", "Boots with salt or water marks", "Winter boots before storage"],
     "details": [("Shaft", "The boot shaft is cleaned and supported so it dries without creasing."), ("Leather or Suede", "Cleaned and conditioned or brushed according to the material."), ("Zips & Elastic", "Side zips and elastic gussets are cleaned and checked.")],
     "faq": ("Can you clean suede boots?", "Yes. Suede boots are dry-brushed, cleaned with suede-specific products and the nap lifted as they dry. Leather boots are cleaned and conditioned.")},

    # Laundry
    {"slug": "wash-and-fold", "profile": "laundry", "noun": "laundry", "plural": "Wash & Fold",
     "seo": "Wash and Fold Laundry", "h1": "Wash & Fold Laundry, Done Properly",
     "svc_name": "Wash & Fold",
     "svc_long_desc": "Everyday laundry sorted by colour and fabric, washed on commercial machines with eco-friendly detergents, dried completely and folded. Priced per kilogram.",
     "includes": ["Sorted by colour & fabric", "Pocket check", "Commercial machine wash", "Eco-friendly detergent", "Complete drying", "Neatly folded & packed"],
     "best_for": ["Everyday clothes, T-shirts and loungewear", "Towels and bed linen", "Gym and sports clothes", "Children's clothes"],
     "faq": ("Is my laundry washed with other people's?", "No. Every customer's laundry is washed in its own load and never mixed with another order.")},
    {"slug": "wash-and-steam-iron", "profile": "laundry", "noun": "laundry", "plural": "Wash & Steam Iron",
     "seo": "Wash and Iron Laundry", "h1": "Wash & Steam Iron Laundry, Ready to Wear",
     "svc_name": "Wash & Steam Iron",
     "svc_long_desc": "Your everyday clothes washed on commercial machines with eco-friendly detergents, dried completely and then steam-ironed, so they come back ready to wear rather than folded.",
     "includes": ["Sorted by colour & fabric", "Pocket check", "Commercial machine wash", "Eco-friendly detergent", "Professional steam ironing", "Folded or hung for delivery"],
     "best_for": ["Office shirts and trousers", "Cotton kurtas and dresses", "Everyday clothes you want ready to wear", "Busy weeks with no time to iron"],
     "faq": ("What is the difference from wash and fold?", "Wash & Fold is washed, dried and folded. Wash & Steam Iron adds professional steam ironing, so clothes come back pressed and ready to wear.")},
    {"slug": "premium-laundry", "profile": "laundry", "noun": "laundry", "plural": "Premium Laundry",
     "seo": "Premium Laundry Service", "h1": "Premium Laundry for Clothes That Deserve More",
     "svc_name": "Premium Laundry",
     "svc_long_desc": "For better clothes that can be washed but should not go through an ordinary cycle: washed gently in small loads by fabric, dried at low heat and steam-finished by hand.",
     "includes": ["Sorted by fabric & care label", "Small, gentle loads", "Premium eco-friendly detergent", "Low-heat drying", "Hand steam finishing", "Hung or folded with care"],
     "best_for": ["Premium cotton and linen shirts", "Branded casual wear", "Delicate but washable fabrics", "Clothes you want to last longer"],
     "faq": ("When should I choose premium laundry over dryclean?", "Premium Laundry suits good-quality washable clothes. Anything labelled dry clean only, or made of silk, wool suiting or heavy embellishment, should be drycleaned instead.")},
    {"slug": "woollen-laundry", "profile": "laundry", "noun": "woollens", "plural": "Woollen Laundry",
     "seo": "Woollen Laundry Service", "h1": "Woollen Laundry for Everyday Winter Wear",
     "svc_name": "Woollen Laundry",
     "svc_long_desc": "Everyday woollens washed on a wool-safe cycle with wool-friendly detergent, dried flat so they keep their size, and folded. For daily-wear sweaters, caps and scarves.",
     "includes": ["Care-label check", "Wool-safe wash cycle", "Wool-friendly detergent", "Dried flat, not tumbled", "Reshaped by hand", "Folded & packed"],
     "best_for": ["Daily-wear sweaters and pullovers", "School and office woollens", "Woollen caps, scarves and gloves", "Winter wear washed often"],
     "faq": ("Will my woollens shrink?", "Woollens are washed on a wool-safe cycle and dried flat, never tumbled, which is what shrinks wool at home. Delicate cashmere and pashmina should be drycleaned instead.")},
    {"slug": "woollen-laundry-iron", "profile": "laundry", "noun": "woollens", "plural": "Woollen Laundry & Iron",
     "seo": "Woollen Wash and Iron", "h1": "Woollen Laundry & Iron for Everyday Winter Wear",
     "svc_name": "Woollen Laundry & Iron",
     "svc_long_desc": "Everyday woollens washed on a wool-safe cycle, dried flat so they keep their size, then finished with light steam so they come back smooth and ready to wear.",
     "includes": ["Care-label check", "Wool-safe wash cycle", "Wool-friendly detergent", "Dried flat, not tumbled", "Light steam finishing", "Folded & packed"],
     "best_for": ["Woollen uniforms and school sweaters", "Office cardigans and pullovers", "Woollen trousers", "Winter wear you want ready to wear"],
     "faq": ("What does the iron add?", "After washing and flat drying, woollens are finished with light steam to smooth them without flattening the knit.")},
]


# ---------------------------------------------------------------------------

def pairs(items, a, b):
    return [{a: x, b: y} for x, y in items]


def build_product(p: dict, price_index: dict, services_by_slug: dict) -> dict:
    prof = PROFILES[p["profile"]]
    item = price_index[p["slug"]]
    name = item["name"]
    plural = p["plural"]
    many = p.get("many") or plural.lower().replace("t-shirts", "T-shirts")
    p = {**p, "name": name, "many": many}
    noun = p["noun"]
    plural = p["plural"]
    care = prof.get("care", "dryclean care")
    img = p.get("img") or item.get("img")
    webp = img.rsplit(".", 1)[0] + ".webp"
    parent = services_by_slug.get(p.get("parent") or prof["parent"])

    # Services
    if p["profile"] == "laundry":
        svc = {
            "id": "laundry",
            "slug": p["slug"],
            "name": p["svc_name"],
            "short": p["svc_name"],
            "tagline": prof["svc_tagline"],
            "shortDescription": p["svc_long_desc"].split(". ")[0] + ".",
            "longDescription": p["svc_long_desc"],
            "bestFor": p["best_for"],
            "includes": p["includes"],
            "turnaround": prof["turnaround"],
        }
        services = [svc]
    else:
        services = [dryclean_service(p, prof)]
        if p.get("iron"):
            services.append(steam_service(p))

    eyebrow = prof.get("eyebrow", "Professional Dryclean Care")
    h1 = p.get("h1") or f"Professional Dryclean Care for Your {plural}"
    seo = p["seo"]
    first_turn = services[0]["turnaround"]
    if len(services) > 1:
        turnaround_note = f"Dryclean {first_turn.replace(' hours', ' hrs')} · Steam press 24 hrs"
    else:
        turnaround_note = f"Ready in {first_turn.replace(' hours', ' hrs')}"

    subtitle = {
        "leather": f"Your {noun} cleaned and conditioned by hand at Wash4You, in a specialist process kept separate from the dryclean load. Collected free from your doorstep across Gurugram & Delhi NCR.",
        "carpet": "Rugs and carpets collected from your door, dusted, deep-cleaned with extraction methods and dried completely at Wash4You. Priced per square foot, across Gurugram & Delhi NCR.",
        "footwear": f"Your {noun} cleaned by hand at Wash4You's Gurugram stores — uppers by material, soles, laces and insoles included. Free doorstep pickup and delivery.",
        "laundry": (p.get("svc_long_desc", "").split(". ")[0] + ". Free doorstep pickup and delivery across Gurugram & Delhi NCR."),
    }.get(p["profile"], f"Your {noun} drycleaned on commercial machines, steam-finished by hand and returned pressed and covered by Wash4You. Collected free from your doorstep across Gurugram & Delhi NCR.")

    care_word = {"leather": "leather cleaning", "carpet": "carpet cleaning", "footwear": "shoe cleaning", "laundry": "laundry"}.get(p["profile"], "dry cleaning")
    desc = f"Professional {seo.lower()} in Gurgaon & Delhi NCR by Wash4You. Stain treatment, expert finishing and free doorstep pickup & delivery."
    if len(desc) > 158:
        desc = f"{seo} in Gurgaon & Delhi NCR by Wash4You, with stain treatment and free doorstep pickup & delivery."

    out: dict = {
        "_generated": "tools/gen-product-pages.py — edit the generator (or delete this key to hand-maintain the file)",
        "name": name,
        "slug": p["slug"],
        "noun": noun,
        "seo": seo,
        "care": care,
        "category": p.get("category") or prof["category"],
        "eyebrow": eyebrow,
        "h1": h1,
        "subtitle": subtitle,
        "heroImage": webp,
        "heroImageFallback": img,
        "heroImageAlt": f"{name} — {care_word} by Wash4You",
        "turnaroundNote": turnaround_note,
        "badge": "Free Doorstep Pickup & Delivery",
        "meta": {
            "title": f"{seo} Service in Gurgaon | Wash4You",
            "description": desc,
            "og_title": f"{seo} with Free Pickup | Wash4You",
            "og_description": subtitle,
        },
        "services": services,
    }
    if prof.get("studio_label"):
        out["studioLabel"] = prof["studio_label"]
    if care != "dryclean care":
        out["tag"] = {
            "title": care.replace(" care", "").title() + " Care Tag",
            "line": "Tagged at your door · Returned clean & packed",
        }
    if prof.get("studio"):
        s = prof["studio"]
        out["studio"] = {
            "eyebrow": s["eyebrow"], "title": s["title"], "subtitle": s["subtitle"],
            "points": pairs(s["points"], "title", "desc"),
        }
    if len(services) > 1:
        out["serviceComparison"] = compare_block(p, prof)

    why = prof["why"]
    why_title = {
        "leather": f"Why Professional Leather Care for Your {plural}?",
        "carpet": "Why Professional Carpet Cleaning?",
        "footwear": f"Why Professional Shoe Care for Your {plural}?",
        "laundry": "Why Professional Laundry Care?",
    }.get(p["profile"], f"Why Professional Dryclean Care for {plural}?")
    out["whyProfessional"] = {
        "eyebrow": why["eyebrow"], "title": why_title, "subtitle": why["subtitle"],
        "points": pairs(why["points"], "title", "desc"),
    }

    if prof.get("stains"):
        before = {"footwear": "Cleaning", "carpet": "Deep Clean", "leather": "Cleaning"}.get(p["profile"], "Dryclean")
        out["stainTreatment"] = {
            "eyebrow": "Targeted Treatment",
            "title": f"Tough Stains? We Treat Them Before the {before}.",
            "subtitle": f"These are the marks we see most often on {many}. Each one is assessed and pre-treated before the main clean.",
            "categories": pairs(prof["stains"], "name", "detail"),
            "disclaimer": DISCLAIMER,
        }
    if prof.get("details"):
        details = list(p.get("details") or prof["details"]) + [
            d for d in prof["details"] if d not in (p.get("details") or [])
        ]
        details = (details + [
            ("Care Label", "The manufacturer's care label is read before anything else and followed."),
            ("Final Inspection", "Checked under light for cleanliness and finish before packing."),
            ("Packing", "Packed to arrive clean, crease-free and ready to use."),
        ])[:6]
        out["detailCare"] = {
            "eyebrow": "Craftsmanship",
            "title": "Every Detail Matters",
            "subtitle": f"Here is how the Wash4You studio treats the parts of your {noun} that matter most:",
            "details": pairs(details, "title", "desc"),
        }
    if prof.get("before_after"):
        out["beforeAfter"] = {
            "eyebrow": "Visual Results",
            "title": "See the Difference",
            "subtitle": f"How Wash4You's professional {care} resolves common problems:",
            "examples": [
                {"title": t, "problem": a, "treatment": b, "result": c}
                for t, a, b, c in prof["before_after"]
            ],
        }
        if prof.get("ba_photos"):
            out["beforeAfter"]["photos"] = prof["ba_photos"]

    if prof.get("process"):
        out["careProcess"] = {
            "eyebrow": "Our Process",
            "title": f"The 8-Step Wash4You {care.replace(' care', '').title()} Process",
            "subtitle": "From your doorstep, through the Wash4You studio, and back:",
            "steps": [{"step": f"{i:02d}", "title": t, "desc": d} for i, (t, d) in enumerate(prof["process"], 1)],
        }

    out["relatedServices"] = [s for s in prof["related"] if s != p["slug"]][:6]
    out["relatedTitle"] = {
        "footwear": "More From the Wash4You Shoe Studio",
        "laundry": "More From Wash4You",
    }.get(p["profile"], "More From the Wash4You Dryclean Studio")

    # FAQs: price, time, item-specific. Shared ones come from _shared.json.
    if len(services) > 1:
        price_a = f"{name} Dryclean & Press starts from {{price1}} per piece and Steam Press from {{price2}} per piece."
        time_a = f"Steam Press is usually delivered within 24 hours, and Dryclean & Press within {first_turn}."
    elif p["profile"] == "carpet":
        price_a = "Carpet cleaning starts from {price1} per square foot."
        time_a = f"Carpet cleaning takes about {first_turn}, including complete drying."
    elif p["profile"] == "laundry":
        price_a = f"{p['svc_name']} starts from {{price1}}{' per kg' if p['slug'] == 'wash-and-fold' else ' per piece'}."
        time_a = f"{p['svc_name']} is usually delivered within {first_turn}."
    else:
        unit = item.get("unit") or ("per pair" if p["profile"] == "footwear" else "per piece")
        price_a = f"{services[0]['name']} for {many} starts from {{price1}} {unit}."
        time_a = f"{services[0]['name']} for {many} usually takes {first_turn}."
    seo_q = seo.lower().replace("t-shirt", "T-shirt")
    faqs = [
        {"q": f"How much does {seo_q} cost at Wash4You?",
         "a": price_a + " Prices are exclusive of 18% GST, and pickup and delivery are free."},
        {"q": f"How long does {seo_q} take?", "a": time_a},
    ]
    if len(services) > 1:
        faqs.append({"q": "Should I choose dryclean or steam press?",
                     "a": "Choose Steam Press when the piece is already clean and just needs the creases out. Choose Dryclean & Press when it has been worn, has stains or smells, or needs a proper hygienic clean."})
    q, a = p["faq"]
    faqs.append({"q": q, "a": a})
    if prof.get("stains"):
        faqs.append({"q": f"Can you remove stains from {many}?",
                     "a": "Visible stains are identified and pre-treated before the main clean. Results depend on the type and age of the stain, the fabric and any earlier home treatment, so complete removal cannot be guaranteed for every mark."})
    out["faqs"] = faqs

    fc_title = {
        "leather": f"Your {name}, Cared For by Wash4You.",
        "footwear": f"Your {plural}, Cleaned by Hand at Wash4You.",
        "carpet": "Your Carpet, Deep-Cleaned by Wash4You.",
        "laundry": "Your Laundry, Done by Wash4You.",
    }.get(p["profile"], f"Your {plural}, Drycleaned by Wash4You.")
    out["finalCta"] = {"title": fc_title}

    photos = dict(prof.get("photos") or {})
    if prof.get("banner"):
        photos["banner"] = prof["banner"]
    if photos:
        out["photos"] = photos
    if parent:
        out["parentService"] = {"slug": parent["slug"], "name": parent["name"]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slugs", nargs="*", help="only these products")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    pricing = json.loads((DATA / "pricing.json").read_text(encoding="utf-8"))
    price_index = {i["slug"]: i for c in pricing["categories"] for i in c["items"] if i.get("slug")}
    services = json.loads((DATA / "services.json").read_text(encoding="utf-8"))
    services_by_slug = {s["slug"]: s for s in services["services"]}

    wanted = set(args.slugs)
    written = skipped = 0
    for p in PRODUCTS:
        if wanted and p["slug"] not in wanted:
            continue
        if p["slug"] in HAND_WRITTEN and not (args.force and p["slug"] in wanted):
            continue
        if p["slug"] not in price_index:
            print(f"!! {p['slug']} is not in pricing.json", file=sys.stderr)
            return 1
        path = OUT / f"{p['slug']}.json"
        if path.exists() and not args.force:
            skipped += 1
            continue
        data = build_product(p, price_index, services_by_slug)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1

    covered = {p["slug"] for p in PRODUCTS} | HAND_WRITTEN
    missing = [s for c in pricing["categories"] if c["title"] != "Steam Iron"
               for s in (i["slug"] for i in c["items"]) if s not in covered]
    print(f"wrote {written}, skipped {skipped} existing (use --force to overwrite)")
    if missing:
        print("price-list items with no product page:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
