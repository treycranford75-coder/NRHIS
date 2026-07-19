# ES-024 Handoff Lifecycle and Clipboard Safety

## Purpose

ES-024 keeps operator handoff files outside the Git repository and ensures manual
release notes are copied after the browser opens.

## Handoff storage

Operator handoff files are stored under the user's local application-data
directory:

`%LOCALAPPDATA%\NRHIS\handoff`

This prevents generated handoff files from making the repository working tree
unclean.

## Clipboard sequencing

For manual GitHub release publication, the browser opens first. Release notes are
then copied to the clipboard after a short delay. This reduces the risk that a
browser or screenshot action replaces the intended Markdown clipboard content.
