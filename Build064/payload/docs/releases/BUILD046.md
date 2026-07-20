# NRHIS Sprint 2 Build047

Build047 extends the one-step lifecycle with automatic CI repair guidance. When required checks block a merge, the lifecycle captures failed-step logs, identifies failing pytest node IDs when possible, and writes a ready-to-run local reproduction script beside the existing diagnostic evidence.
