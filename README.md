# TAK Interop

`snstac-tak-interop` is the small, domain-neutral interoperability package used
by DTED.org, Cambot, and FireCOP. It owns deterministic TAK Mission Package
construction, ATAK handoff URIs, KML NetworkLinks, QR rendering, product
catalog contracts, and artifact validation.

It deliberately does not own source adapters, authentication policy, storage,
or domain-specific Cursor on Target serialization.

```bash
python -m pip install -e '.[test]'
pytest
tak-validate package.zip
```

Licensed under Apache-2.0.
