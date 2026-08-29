# NRHIS Sprint 2 Build092 Release Notes

Build092 prepares NRHIS for the full 2007-present USGS archive. It adds the two Rincon Bayou stations omitted from the initial six-station plan, removes repeated full-history identity rescans during chunked backfill, and preserves exact upstream USGS response bytes so chunk receipt SHA-256 values verify the archived evidence itself. Differing rerun responses are retained under hash-suffixed filenames instead of overwriting prior raw evidence.
