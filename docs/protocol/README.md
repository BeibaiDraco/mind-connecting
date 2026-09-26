# Protocols and freeze manifests

Each confirmatory stage was run under a protocol frozen before its data were collected. Freezing wrote a manifest, `FREEZE_protocol_<version>.txt`, listing the SHA256 of the protocol document, the configurations, the generators and the source files, together with the git commit, and created the tag `protocol-<version>`.

| Version | Protocol | Manifest | Tag |
|---|---|---|---|
| v1 | `EXPERIMENT_DESIGN.md` (hidden-state study) | `FREEZE_protocol_v1.txt` | `protocol-v1` |
| v2 | `PROTOCOL_V2.md` (memory link, first confirmatory sample) | `FREEZE_protocol_v2.txt` | `protocol-v2` |
| v3 | `PROTOCOL_V3.md` (main sample and two-way pilot) | `FREEZE_protocol_v3.txt` | `protocol-v3` |

## Verifying a freeze

The manifests describe the files as they were at the freeze, so they are verified against the tagged commit, not against the current files. The public repository starts from a single commit made on 2026-09-25; the development history before it, including the freeze commits and the tags above, is kept as a private archive (a git bundle held by the PI) and can be shared on request. In a clone of the archive:

```bash
git checkout protocol-v2
python scripts/freeze_protocol.py --verify --version v2
```

Against the current files the check is expected to fail, for two reasons. The source code kept evolving after each freeze (later protocols added new interfaces), and the protocol documents themselves were written in Chinese and translated into English on 2026-09-25 for the public release. The translation changed the language only, not the content, but it changes the files' hashes. The originals, with the hashes recorded in the manifests, are the versions at the tags in the archive.
