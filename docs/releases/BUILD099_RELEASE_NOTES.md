# NRHIS Sprint 2 Build099 Release Notes

Build099 reconciles the Build097 and Build098 interval counts and turns the 2017-2018 Rincon findings into a compact evidence timeline. It distinguishes sampled negative-value runs from piecewise-linear integrated negative-flow intervals, identifies exact-zero bridges that merge otherwise separate sampled runs, reports any unintegrated observation-only runs, and verifies the interval-count accounting identity.

It also extracts the exact reverse-flow interval ending at the 2017 material discharge outage, stage coverage through that outage, the first reverse interval after discharge resumes, and the May 2018 terminal discharge discontinuation with continuing stage monitoring. Outputs are SHA-256 bound to the finalized local archive and query index, with zero USGS requests.
