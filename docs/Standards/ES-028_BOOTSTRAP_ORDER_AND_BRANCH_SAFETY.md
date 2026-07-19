# ES-028 Bootstrap Order and Branch Safety

## Purpose

ES-028 ensures each one-step build installs its required bootstrap helpers before
those helpers are called and ensures the feature branch exists before any build
commit is created.

## Required sequence

1. Extract the one-step package.
2. Install bootstrap helpers from the payload.
3. Synchronize the base branch without pruning.
4. Create or switch to the feature branch.
5. Install the remaining payload.
6. Run validation.
7. Stage, verify, commit, and push.

## Branch safeguard

A build commit must never be created while `develop` is checked out. The
feature branch is created directly from the synchronized base branch before
payload installation and validation continue.
