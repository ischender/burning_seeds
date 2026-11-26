# Burning Seeds

Build a reproducible historical dataset for mapping Burning Man and related
events over time. See burner-seed-handoff.md for the recovered research and
the primary-source queue.

- `events.csv` identifies events. Record parent IDs only for documented lineage.
- `editions.csv` records event-year status, location, and population evidence.
  Locations belong to editions because venues change.
- `observations.csv` preserves source claims and conflicting measurements.
  Attendance, ticket counts, capacities, and estimates are separate metrics.

Keep unknown and cancelled population blank. Treat catalogue entries as discovery
evidence and avoid filling gaps between documented editions. Prefer organizer
archives, censuses, and annual reports when reconciling observations.
