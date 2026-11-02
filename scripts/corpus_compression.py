"""Preserve the published gzip byte format across Python default/header changes."""
import gzip


def canonical_gzip(data):
    # Corpus 0.2/0.3 was published at level9, mtime0, with OS marker3 (Unix).
    # Python3.13+ emits marker255; Python3.15+ changes the default level.
    # The marker is format metadata, not a property of the scientific content.
    payload = gzip.compress(data, compresslevel=9, mtime=0)
    return payload[:9] + b'\x03' + payload[10:]
