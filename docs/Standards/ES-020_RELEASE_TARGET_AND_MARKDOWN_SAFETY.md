# ES-020 Release Target and Markdown Safety

## Purpose

ES-020 prevents pull requests from opening against the wrong base branch and
preserves Markdown formatting during manual GitHub release publication.

## Pull-request safety

The GitHub compare URL must be constructed from an explicitly supplied base
branch and head branch. Repository identification must support SSH and HTTPS
GitHub remotes without truncating the repository slug.

## Release-note safety

Manual publication must copy the complete release-note file using raw text so
Markdown headings, lists, inline code, and paragraph spacing are preserved.

## Manual merge gate

Pull-request merging remains manual and must occur only after the displayed base
branch, commit count, file count, and required checks are verified.
