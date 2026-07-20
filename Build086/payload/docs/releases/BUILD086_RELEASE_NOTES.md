# NRHIS Sprint 2 Build086 Release Notes

Build086 prevents premature release-lifecycle failures when GitHub Actions has not yet registered checks for a newly created pull request. The lifecycle now waits and retries before deciding that CI is unavailable, while genuine test or lint failures continue to block merge.
