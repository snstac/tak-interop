# TAK Interop

`snstac-tak-interop` is the small, domain-neutral interoperability package used
by DTED.org, Cambot, and FireCOP. It owns deterministic TAK Mission Package
construction, ATAK handoff URIs, KML NetworkLinks, QR rendering, product
catalog and asset contracts, and artifact validation. Product contracts carry
canonical UI links and fire/disaster/USAR domains; vector assets have stable
live, historical, and tombstone identities. Version 1.2 also packages the
shared Cambot camera-profile browser component used by both Cambot and
FireCOP, including its pinned HLS.js runtime.

It deliberately does not own source adapters, authentication policy, storage,
or domain-specific Cursor on Target serialization.

The service ownership and federation rules are documented in
[ARCHITECTURE.md](ARCHITECTURE.md). The package's stable discovery contract is
served by each application at `/.well-known/tak-products.json` and
`/api/v1/products`.

```bash
python -m pip install -e '.[test]'
pytest
tak-validate package.zip
```

Web applications can mount `takinterop.web_assets_path()` at a static URL and
load `camera-profile.css`, `vendor/hls.min.js`, then `camera-profile.js`.

Licensed under Apache-2.0.
