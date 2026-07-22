# Service boundaries

The shared package defines wire contracts and deterministic TAK packaging; it
does not turn the participating services into one deployment.

| Owner | Responsibilities | Consumers |
| --- | --- | --- |
| Cambot | Camera collection, normalized camera identity, signed media capabilities, camera CoT and camera mission packages | FireCOP and direct clients |
| FireCOP | Protected incident COP, non-camera source normalization, operator subscriptions, advisory analysis | FireCOP operators |
| layers.firecop.us | Anonymous approved wildfire products, open GIS formats, TAK packages, Sentinel tile cache | TAK and GIS clients; FireCOP handoff |
| DTED.org | Elevation acquisition, quality gates, streaming endpoints and DTED client preferences | TAK elevation clients |
| tak-interop | Product discovery schema, Mission Package construction, NetworkLinks, TAK URIs, QR helpers and validation | All services |

Every participating service exposes `GET /.well-known/tak-products.json` and
`GET /api/v1/products`. Product identifiers are stable within the owning
service. Artifact URLs are absolute and carry media types, attribution, terms,
access policy, freshness, bounds, and supported time windows when applicable.

Federation is one-way at runtime: FireCOP consumes Cambot camera APIs and links
to public layer artifacts; Cambot and the public layers service do not call
back into FireCOP. DTED remains an independent elevation service. This avoids
circular availability dependencies and keeps source-specific credentials with
the service that owns each integration.

Public redistribution is fail-closed. A FireCOP source must have an explicit
public-distribution flag, an allowlist of output formats, a review date, and a
review basis before the public layers process will emit it. Missing metadata
removes the affected product from discovery and blocks direct artifact output.
