# Build042

Build042 makes Git for Windows directory-deletion retry prompts noninteractive. During branch switches and other lifecycle Git operations, the script supplies `n` automatically when Windows or OneDrive keeps a directory locked. The prompt remains visible in the execution log, but it no longer blocks the build. Required Git operations still fail closed if the command does not succeed after the existing transient retry.
