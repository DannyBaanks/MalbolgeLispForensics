# Publication redaction

Absolute workstation paths in curated text logs are replaced with neutral tokens
(such as `<LAB>`) before publication. The substitution changes only local path
strings; execution results, outputs, step counts, errors, and other measured data
are left unchanged. Hashes in `evidence/hashes/evidence.sha256` are hashes of the
published, redacted artifacts.
