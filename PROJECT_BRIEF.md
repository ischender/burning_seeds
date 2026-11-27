# Burning Seeds

Build a reproducible historical dataset for mapping Burning Man and related
events over time. See docs/burner-seed-handoff.md for the recovered research and
the primary-source queue.

- `events.csv` identifies events. Record parent IDs only for documented lineage.
- `editions.csv` records event-year status, dates, location, and population
  evidence. Locations belong to editions because venues change, and each fix
  records its precision. Unknown dates stay blank, and month-only dates stay
  `YYYY-MM`.
- `observations.csv` preserves source claims and conflicting measurements.
  Attendance, ticket counts, capacities, and estimates are separate metrics.

Keep unknown and cancelled population blank. Treat catalogue entries as discovery
evidence and avoid filling gaps between documented editions. Prefer organizer
archives, censuses, and annual reports when reconciling observations.

## Future idea: key people

Founders, lead organizers, and other documented figures could be mapped
alongside editions. This is not implemented yet. A coherent design would add a
`people.csv` table (`person_id`, `name`, `notes`) and a `roles.csv` link table
(`person_id`, `event_id`, `year_start`, `year_end`, `role`, `source_url`,
`confidence`). Roles would follow the same evidence rules as lineage: each one
needs a source, and names alone never imply ties between events. Record only
public roles stated by the organizers or the press, and do not collect personal
contact details.
