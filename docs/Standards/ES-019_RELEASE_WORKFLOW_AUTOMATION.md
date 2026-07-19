# ES-019 Release Workflow Automation

## Purpose

ES-019 defines the automated NRHIS build, validation, pull-request, tagging, and
pre-release publication workflow.

## Automated stages

- repository validation;
- feature-branch publication;
- pull-request creation when GitHub CLI is available;
- post-merge synchronization;
- full release-gate validation;
- installer-artifact cleanup;
- annotated tag creation and verification;
- tag publication;
- GitHub pre-release publication when GitHub CLI is authenticated.

## Manual release gate

Pull-request merging remains manual. Automation must not invoke `gh pr merge` or
otherwise bypass GitHub branch protections and required checks.

## Failure behavior

Every command must stop on a nonzero exit code. Tagging and publication occur
only after the test, lint, coverage, legacy-preservation, whitespace, and clean
working-tree gates pass.
