  

# Burning Man Global Spread: Historical Data Archaeology Dataset

## Research deliverables

I assembled a first normalized, machine-readable research dataset rather than just a source list. It currently contains **91 event entities and 205 edition/year observations**, covering the original Burning Man, early North American offshoots, major international burns, and a broad discovery layer of smaller or less-documented events. The edition table explicitly distinguishes attendance from tickets sold, capacity, approximate scale, cancellation, virtual editions, current-catalogue snapshots, and unresolved records.

|Artifact|Contents|
|---|---|
|[Complete ZIP](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|All files together|
|[events.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|91 normalized event entities, aliases, first-year evidence, type, official-status research classification, geography, approximate scale, provenance|
|[editions.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|205 event-year observations, location, coordinate fields, precision, population, metric, status, source, confidence, notes|
|[observations.csv](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Conflicts and ambiguities that must survive reconciliation rather than being overwritten|
|[burning_man_spread_dataset.json](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Combined JSON bundle|
|[README.md](https://connector-id-dfbccc248e43b6fe7d187129e21b5ec8.web-sandbox.oaiusercontent.com/?app=skybridge&locale=en-US&deviceType=desktop&unsafeSkipTargetOriginCheck=true&backgroundMode=transparent)|Schema semantics and cautions|

This should be treated as a **research seed rather than a finished canonical database**. In particular, I did not turn "no record found" into zero, did not infer an annual event between two known editions, and did not label a 2026 calendar listing as a completed event without post-event evidence. Burning Wiki itself describes its world list as a best-effort community compilation and says its official-event marker can be incomplete, so I used it mainly for discovery rather than as sole proof.

The resulting model is deliberately observation-oriented. For example, a row can say "1,835 tickets sold, 1,651 actually on site" rather than collapsing both into a single "size" value. Kiwiburn's own 2024 report provides exactly that distinction, while Element 11's 2016 AfterBurn separately reports 1,353 paid tickets, 1,406 allocated tickets, and 1,273 people captured through the gate.

## Historical spine and first propagation

The core timeline is unusually well documented. Burning Man began on Baker Beach in 1986 with 35 people, then grew to 80 in 1987, 200 in 1988, and 300 in 1989. The 1990 transition needs special handling: Burning Man's official timeline gives a headline population of 350, while the same historical account describes roughly 90 participants at the first Black Rock Desert burning. I preserved this as a conflict instead of selecting one number invisibly.

The official population series then gives 250 in 1991, 600 in 1992, 1,000 in 1993, 2,000 in 1994, 4,000 in 1995, 8,000 in 1996, 10,000 in 1997, 15,000 in 1998, and 23,000 in 1999. It reaches 25,400 in 2000 and 25,659 in 2001, then climbs into the 70,000-plus range in the late 2010s and 2020s. Official figures give 78,850 for 2019, 75,069 for 2022, 74,126 for 2023, 69,141 for 2024, and 72,181 for 2025. The official physical Black Rock City event did not take place in 2020 or 2021, so those years are encoded as `cancelled` with null population, not population `0`.

The first clearly documented official regional offshoot is **Burning Man Texas in June 1998**, with about 30 people; the event took the name **Burning Flipside** in 1999. Burning Man's own Regional Network history identifies that Texas event as the first official Regional Event.

A second east-coast lineage arose almost simultaneously. Playa del Fuego's organizers trace their history to about 20 people meeting at Assateague Island on August 1, 1998. The historical secondary record preserves subsequent Assateague gatherings of roughly 30 that autumn, about 30 and then about 60 in 1999, and 70-plus at the spring 2000 gathering that is generally treated as the first "Playa del Fuego" proper. The event moved off Assateague as it grew, first to Delaware in 2001 and eventually to Tamaqua, Pennsylvania in 2018. Because the detailed early attendance table is secondary rather than an organizer archive, I tagged those rows medium confidence.

Utah provides another useful example of why precursor semantics matter. Element 11's own history calls an eight-person Stansbury Island gathering in 1998 a precursor, while the first Utah Regional Burn, then called **Synorgy**, took place in 1999 with roughly 70 people. The name changed to **Element 11** in 2006, when attendance was around 500. The organizer's historical timeline gives about 1,200 in 2013-14, 1,300 in 2015, 1,400 in 2016, 1,200 in 2017, 1,300 in 2018, and 1,400 in 2019. For 2016, the detailed AfterBurn refines the approximate headline to 1,273 people captured through the gate, demonstrating why the raw metric should be retained.

These early records change the visual story somewhat: there is not one single "first spark" after Nevada. By 1998, distinct regional experiments were appearing in Texas, on the Atlantic coast, and in Utah, with different degrees of formal recognition and different relationships to Burning Man. The dataset therefore encodes them separately rather than forcing an unsupported parent-child graph.

## International spread and recovered attendance series

Burning Man's official Regional Network history identifies **Kiwiburn in New Zealand in 2004 as the first Regional event outside North America**. Kiwiburn's own account says the first event occurred as part of the Visionz festival in early 2004, with the following two South Island stand-alone burns drawing approximately 200 people; the wording is ambiguous enough that I have not treated "200" as a precise independent gate count for each year. The project moved to the North Island in 2007.

Kiwiburn has one of the best early retrospective series I found. Its 2013 AfterBurn gives attendance of **145, 182, 250, 450, 530, 536, and 754** for 2007 through 2013 respectively; the 2013 total consists of 732 paying participants and 22 children. Its official Burning Man regional page says Kiwiburn grew from fewer than 100 participants in its first year to more than 2,300 in 2023, and confirms that no Kiwiburn took place in 2019 or 2022.

**Nowhere** is the key early European burn. Burning Man's Spain page says it was founded in 2004 and is held in the Monegros Desert in Aragón. More importantly, the official 2023 Nowhere census contains a retrospective population series: 35 in 2004, 68 in 2005, 134 in 2006, 240 in 2007, 320 in 2008, 515 in 2009, 590 in 2010, 627 in 2011, 1,004 in 2012, 1,199 in 2013, 1,368 in 2014, 1,500 in 2015, 1,939 in 2016, 2,600 in 2017, 3,664 in 2018, 3,554 in 2019, 3,151 in 2022, and 2,670 in 2023. The same report says 2,980 tickets were sold in 2023 with a 9% no-show rate.

**AfrikaBurn** has an unusually useful organizer-maintained event archive. It records approximately 1,000 participants in 2007, 1,200 in 2008, 1,600 in 2009, 2,200 in 2010, 4,000 in 2011, 5,700 in 2012, 7,000 in 2013, 9,000 in 2014, 9,800 in 2015, 11,800 in 2016, 13,000 in 2017, 11,000 in 2018, 11,500 in 2019, 6,500 in 2022, 9,000 in 2023, and 10,000 in 2024; the organizer marks 2020 and 2021 as cancelled. A contemporary South African retrospective instead describes the first edition as roughly 800 people, so both observations are retained in the provenance table, with the organizer archive preferred for the canonical series.

**Midburn's** documented lineage begins before the event itself. Its organizers say the Israeli community was established in 2011; **Mama Burn** at HaBonim Beach in April 2012 drew roughly 600 people, followed by **Octoburn** later that year at roughly 1,600. The community was formally recognized in 2013, and the first Midburn in 2014 had about 3,000 participants. By 2018 the event was around 12,000. I model Mama Burn and Octoburn as `precursor_gathering` and `precursor_burn`, not as retroactively renamed Midburn editions.

**The Borderland** in Sweden is another instructive scale trajectory. Its own community history states that it began in 2011 with 46 participants and now welcomes more than 5,000 annually. A current community catalogue gives a smaller approximate figure for the event, so I have not treated "5,000" as a verified 2026 gate count.

**Burning Seed** in Australia also has a precursor/main-event distinction. Organizer material lists a 2009 Bellingen "Seed" gathering, followed by the first official themed regional event in 2010, whose capacity was capped at 500. By 2019, organizers reported more than 4,500 tickets sold. The proposed 2022 return was deliberately limited to around 1,500 tickets. The organization's 2026 retrospective explicitly refers to the cancellation of Burning Seed 2025 and describes a smaller Pilot Burn in Capertee Valley in May 2026, with a full-scale Burning Seed return targeted for 2027; I therefore do not silently merge the pilot into the ordinary annual series.

## Global catalogue coverage

The broad catalogue now reaches beyond the large, familiar burns. The current research seed includes North American events such as Firefly, Apogaea, Transformus, SOAK, Myschievia, Alchemy, Resonance, WickerMan, Gateway Burn, Frostburn, Lakes of Fire, unSCruz, BeQuinox, Saguaro Man, YOUtopia, Ignite, POrtal Burn, Critical Northwest, What If/Burn in the Forest, Freezer Burn Alberta, OtherWorld, and SideBurn/Hyperborea. Their dates and approximate current scale mostly come from the community catalogue and therefore remain medium-confidence discovery records until individual organizer archives are checked.

European coverage in the seed includes Nowhere, The Borderland, Swiss Winter Burn, Burning Sand, RoBurn, Čarodění, Degošie Jāņi, Vienna Burning Ball, Burning Nest, Where the Sheep Sleep, Pyraegea, Schönburn, MicroBurn, Juhé Burn, Hamburn, Sunraiz, Amber Burn, Nordic Burn, Magic Forest, Somewhere and Re-Burn, in addition to urban or decomposition-style records that can be filtered separately. Again, these are not asserted to be equivalently "official": the dataset includes an `official_status` and `event_type` precisely so a visualization can show only recognized regionals, all self-described burns, or a broader cultural ecosystem.

Other regions represented include AfrikaBurn and Wildeb​​urn in South Africa and NamBurn in Namibia; Kiwiburn in New Zealand and Burning Seed, Blazing Swan, Modifyre, Underland and other Australian events; Burning Japan, Dragon Burn and Lantern/Turtle Burn in Asia; and Fuego Austral, Chupacabra del Fuego, Tropical Burn and Hombre en Llamas in Latin America. These long-tail rows are intentionally sparse when the source only supports first year, location or approximate size.

The official network itself is now large enough that completeness is a moving target. Burning Man currently describes a network spanning dozens of countries and says organizers run more than 80 unique official Regional Events annually; it reports more than 100,000 participants across Regional Events in 2024. Burning Man's 2025 history describes more than 90 official Regional Events, ranging from AfrikaBurn at around 10,500 people to tiny events with fewer than 25.

That broad contemporary catalogue is useful for discovery but not sufficient for the animation by itself. A current row saying an event is "since 2014" and "about 1,000" cannot establish which intervening years happened, whether the event moved, or whether 1,000 means attendance, ticket cap or a rounded community estimate. This is why current-catalogue entries in `editions.csv` are marked `catalogue_snapshot` rather than `held`.

## Data quality, conflicts and naming archaeology

The biggest methodological result from this pass is that **"population" is not one variable**. Sources variously report gate capture, tickets sold, allocations, capacity, organizer estimates, census participants and rounded current scale. Burning Flipside, for example, reported 3,193 tickets sold but 2,852 people through the gate in 2015; in 2017 it reported 3,017 tickets sold and 2,870 used, and in 2018 2,710 sold and 2,627 used. Its official Burning Man regional page gives 2,490 tickets sold for 2024. These should remain separate metrics even if the map later collapses them to a single visual radius.

Relocations also need edition-level geography. Playa del Fuego moved from Assateague Island to Delaware and later to Pennsylvania; its current organizer page publishes the present Coal Creek Ranch coordinates as approximately **40.777480, -76.02282**. Kiwiburn moved from the South Island to the North Island and today publishes a Hunterville venue address. A single event-level latitude/longitude would therefore produce visibly incorrect history.

Likewise, a "first year" can mean at least three things: a loose community gathering, the first burn under a precursor name, or the first edition under the current brand. Element 11 can reasonably be described as beginning with an eight-person 1998 gathering, with the first Synorgy regional burn in 1999, or with the Element 11 name in 2006. Burning Flipside has Burning Man Texas in 1998 and the Flipside name in 1999. Burning Seed has a 2009 precursor and a 2010 first official themed event. The dataset keeps these distinctions instead of choosing one silently.

The user's remembered **"Wikiburn" remains unresolved**. Exact-name searches did not surface a credible Burning Man-related event under that name; search results instead produced irrelevant uses of the term and Kiwiburn results. There is therefore no basis to identify "Wikiburn" with Kiwiburn or any other burn. It is preserved in `observations.csv` as an unresolved possible alias, misspelling or defunct event for later archive/mail-list archaeology.

One useful warning about official status also emerged from Kiwiburn's own 2013 AfterBurn: although the event was deeply embedded in the network, the report says it had temporarily lacked formal official regional status because of insurance requirements and regained it before that year's event. "Official" is thus potentially an edition- or period-specific property rather than a timeless Boolean attached to an event.

## Coverage assessment and unresolved gaps

Coverage is strongest for **Burning Man itself, Nowhere and AfrikaBurn**, where long organizer-backed population series are available. It is also strong for the early history of Burning Flipside, Element 11/Synorgy and Playa del Fuego/Assateague because contemporary or organizer histories preserve key transitions. Kiwiburn has excellent data for 2007-2013 plus several recent years, while Midburn and Burning Seed have strong origin stories but still need year-by-year extraction from annual transparency/AfterBurn materials.

The weakest part remains the long tail: smaller European burns, decompressions, discontinued North American burns, Asian events, Latin American events, and the many cases for which the only currently indexed evidence is an event catalogue or a present-day web page. The current official Regional Network is much larger than the subset for which historical attendance has been reconstructed, so the map would presently be globally broad but uneven in historical depth.

The 2026 layer is especially conservative. The current date is November 26, 2026, but an announced event with dates earlier in 2026 is not automatically evidence that the event actually took place. For example, the official calendar listed Midburn for November 2-7, 2026, and Playa del Fuego listed May 21-25, 2026, but without a post-event count I leave attendance blank rather than carrying forward an earlier size.

The main unresolved data jobs are historical annual attendance for the dozens of long-tail events; precise venue changes; periods of official recognition; discontinued-event end dates; older European burner calendars and mailing-list archives; local-language records; and reconciliation of community-list values against organizer reports. Burning Wiki itself points to several older community-maintained datasets, including the Burns Around the World material, as sources it has used to reconstruct obscure burns, which makes those older sheets particularly valuable for the next archaeology pass.

## Developer handoff

The current files are already shaped for implementation. `events.csv` should remain the entity table; `editions.csv` should drive the time animation; `observations.csv` should remain untouched as the audit trail for conflicts. For production, I would add a separate `sources` table and a separate `locations` table rather than embedding normalized source and geocode data directly in canonical editions.

The key semantics are already encoded: null means unknown, not zero; `cancelled` is separate from attendance; `virtual`, `pilot_burn`, `catalogue_snapshot`, and `scheduled_or_unverified` are distinct statuses; `population_metric` records what the number actually measures; `location_precision` prevents a region centroid from masquerading as a venue coordinate; and aliases/precursors are retained without inventing genealogical links.

A representative production row should look conceptually like this:

csv

Copy

```csv
event_id,year,location,population,population_metric,status,confidence
kiwiburn,2024,"136 Cooks Rd, Hunterville",1651,"gate/on-site count",held,high
kiwiburn,2024,"136 Cooks Rd, Hunterville",1835,"tickets sold",held,high
burning_seed,2010,"Bellingen, NSW",500,"capacity",held,high
burning_man,2020,"Black Rock Desert, Nevada",,"not applicable",cancelled,high
```

That distinction is source-grounded: Kiwiburn reported both 1,835 tickets sold and 1,651 people on site in 2024, Burning Seed describes 500 as a cap rather than an attendance count, and the official Black Rock City event was cancelled in 2020 rather than attended by zero people.

The current dataset is therefore sufficient to start the mapping/animation code without first solving every archival gap: it already contains a defensible historical spine, several complete or near-complete regional growth curves, a 91-event global discovery catalogue, explicit uncertainty, and source-level provenance. The remaining work is mainly enrichment and reconciliation rather than redesigning the data model.