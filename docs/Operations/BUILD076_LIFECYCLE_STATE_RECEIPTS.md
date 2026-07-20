# Build076 Lifecycle State Receipts

Build076 writes `lifecycle-state.json` under the build evidence directory at every major release phase. The receipt records build number, phase, status, detail, pull-request URL, base branch, and UTC update time. The resume helper reads and reports the prior phase before delegating to the finish lifecycle.
