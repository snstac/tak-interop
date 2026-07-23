(() => {
  "use strict";

  function createCameraProfile(options = {}) {
    if (!window.L) throw new Error("TakCameraProfile requires Leaflet");
    if (typeof options.loadCamera !== "function") throw new Error("loadCamera callback is required");

    const scopes = options.scopes?.length
      ? options.scopes
      : [{ id: "camera", label: "Just this camera" }];
    const state = {
      camera: null,
      context: null,
      envelope: null,
      generation: 0,
      hls: null,
      map: null,
      spatialLayer: null,
      takUri: "",
    };

    const dialog = document.createElement("dialog");
    dialog.className = "tak-camera-profile";
    dialog.setAttribute("aria-labelledby", "tak-camera-profile-title");
    dialog.innerHTML = `
      <div class="tak-camera-profile-shell">
        <button class="tak-camera-profile-close" type="button" aria-label="Close camera details">
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg>
        </button>
        <div class="tak-camera-profile-visuals">
          <div class="tak-camera-feed-frame">
            <img class="tak-camera-image" alt="">
            <video class="tak-camera-video" autoplay muted playsinline controls hidden></video>
            <div class="tak-camera-feed-placeholder" hidden>Live media unavailable in cached fallback</div>
            <div class="tak-camera-feed-overlay">
              <span class="tak-camera-feed-badge">Loading</span>
              <span class="tak-camera-feed-time" hidden>DEMO FEED</span>
            </div>
            <div class="tak-camera-reticle" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
          </div>
          <div class="tak-camera-profile-map" role="img" aria-label="Camera spatial preview map"></div>
        </div>
        <div class="tak-camera-profile-content">
          <div class="tak-camera-profile-warning" role="status" hidden></div>
          <p class="tak-camera-eyebrow"><span></span><b class="tak-camera-source">Camera source</b></p>
          <h2 id="tak-camera-profile-title">Loading camera…</h2>
          <p class="tak-camera-place"></p>
          <dl class="tak-camera-facts">
            <div><dt>Direction</dt><dd data-fact="direction">—</dd></div>
            <div><dt>Media</dt><dd data-fact="media">—</dd></div>
            <div><dt>Coordinates</dt><dd data-fact="coordinates">—</dd></div>
            <div><dt>Last update</dt><dd data-fact="updated">—</dd></div>
            <div><dt>Point of view</dt><dd data-fact="pov">—</dd></div>
            <div><dt>Field of view</dt><dd data-fact="fov">—</dd></div>
            <div><dt>Viewshed</dt><dd data-fact="viewshed">—</dd></div>
            <div><dt>SPI</dt><dd data-fact="spi">—</dd></div>
          </dl>
          <div class="tak-camera-actions">
            <button class="tak-camera-button tak-camera-primary tak-camera-copy-profile" type="button">Copy profile link</button>
            <a class="tak-camera-button tak-camera-secondary tak-camera-source-link" href="#" target="_blank" rel="noreferrer">Source site <span aria-hidden="true">↗</span></a>
          </div>
          <section class="tak-camera-profile-tak" aria-labelledby="tak-camera-profile-tak-title">
            <p class="tak-camera-section-label" id="tak-camera-profile-tak-title">Install in TAK</p>
            <fieldset class="tak-camera-profile-scopes">
              <legend class="tak-camera-sr-only">Choose camera package scope</legend>
              ${scopes.map((scope, index) => `<label><input type="radio" name="tak-camera-profile-scope" value="${escapeAttribute(scope.id)}" ${index === 0 ? "checked" : ""}> ${escapeText(scope.label)}</label>`).join("")}
            </fieldset>
            <p class="tak-camera-export-count"><strong>1</strong> camera selected</p>
            <p class="tak-camera-export-warning" hidden>Large packages can slow ATAK. Continue only if the receiving device can handle this many markers.</p>
            <div class="tak-camera-profile-qr" aria-label="TAK import QR code">Preparing QR…</div>
            <p class="tak-camera-expiry">Creating TAK link…</p>
            <div class="tak-camera-actions">
              <a class="tak-camera-button tak-camera-primary tak-camera-download">Download package</a>
              <button class="tak-camera-button tak-camera-secondary tak-camera-copy-tak" type="button" disabled>Copy TAK link</button>
            </div>
          </section>
          <p class="tak-camera-attribution"></p>
        </div>
      </div>`;
    document.body.append(dialog);

    const elements = {
      close: dialog.querySelector(".tak-camera-profile-close"),
      image: dialog.querySelector(".tak-camera-image"),
      video: dialog.querySelector(".tak-camera-video"),
      placeholder: dialog.querySelector(".tak-camera-feed-placeholder"),
      badge: dialog.querySelector(".tak-camera-feed-badge"),
      time: dialog.querySelector(".tak-camera-feed-time"),
      warning: dialog.querySelector(".tak-camera-profile-warning"),
      source: dialog.querySelector(".tak-camera-source"),
      title: dialog.querySelector("h2"),
      place: dialog.querySelector(".tak-camera-place"),
      sourceLink: dialog.querySelector(".tak-camera-source-link"),
      attribution: dialog.querySelector(".tak-camera-attribution"),
      scopes: [...dialog.querySelectorAll('input[name="tak-camera-profile-scope"]')],
      count: dialog.querySelector(".tak-camera-export-count strong"),
      exportWarning: dialog.querySelector(".tak-camera-export-warning"),
      qr: dialog.querySelector(".tak-camera-profile-qr"),
      expiry: dialog.querySelector(".tak-camera-expiry"),
      download: dialog.querySelector(".tak-camera-download"),
      copyTak: dialog.querySelector(".tak-camera-copy-tak"),
      copyProfile: dialog.querySelector(".tak-camera-copy-profile"),
    };

    function escapeText(value) {
      return String(value ?? "").replace(/[&<>]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[char]);
    }

    function escapeAttribute(value) {
      return escapeText(value).replace(/"/g, "&quot;");
    }

    function finiteNumber(value) {
      if (value === null || value === undefined || value === "") return null;
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }

    function statusClass(status) {
      return ["online", "degraded", "offline"].includes(status) ? status : "degraded";
    }

    function spatialFact(value, suffix = "") {
      const number = finiteNumber(value);
      return number === null ? null : `${number.toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
    }

    function destination(latitude, longitude, bearing, distanceMeters) {
      const radius = 6371008.8;
      const angular = distanceMeters / radius;
      const startLat = latitude * Math.PI / 180;
      const startLon = longitude * Math.PI / 180;
      const heading = bearing * Math.PI / 180;
      const endLat = Math.asin(
        Math.sin(startLat) * Math.cos(angular)
        + Math.cos(startLat) * Math.sin(angular) * Math.cos(heading),
      );
      const endLon = startLon + Math.atan2(
        Math.sin(heading) * Math.sin(angular) * Math.cos(startLat),
        Math.cos(angular) - Math.sin(startLat) * Math.sin(endLat),
      );
      return [endLat * 180 / Math.PI, endLon * 180 / Math.PI];
    }

    function fovPolygon(camera, azimuth, fov, range) {
      const points = [[camera.latitude, camera.longitude]];
      const segments = Math.max(8, Math.ceil(fov / 5));
      for (let index = 0; index <= segments; index += 1) {
        points.push(destination(camera.latitude, camera.longitude, azimuth - fov / 2 + fov * index / segments, range));
      }
      points.push([camera.latitude, camera.longitude]);
      return points;
    }

    function bearingIcon(azimuth) {
      return L.divIcon({
        className: "tak-camera-bearing-marker",
        html: `<span class="tak-camera-bearing-arrow" style="transform:rotate(${Number(azimuth)}deg)"></span>`,
        iconSize: [24, 52], iconAnchor: [12, 45],
      });
    }

    function ensureMap() {
      if (state.map) return;
      state.map = L.map(dialog.querySelector(".tak-camera-profile-map"), {
        zoomControl: true, attributionControl: false, dragging: true, scrollWheelZoom: false,
      }).setView([38.2, -119.6], 5);
      L.tileLayer(options.tileUrl || "https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, attribution: "OpenStreetMap",
      }).addTo(state.map);
      state.spatialLayer = L.featureGroup().addTo(state.map);
    }

    function renderSpatial(camera) {
      ensureMap();
      const layer = state.spatialLayer;
      layer.clearLayers();
      const spatial = camera.spatial || {};
      const location = [camera.latitude, camera.longitude];
      L.circleMarker(location, {
        radius: 7, color: "#fff", weight: 2, fillColor: "#35c47c", fillOpacity: 1,
      }).bindTooltip(camera.name).addTo(layer);
      if (spatial.viewshed) {
        L.geoJSON(spatial.viewshed, {
          style: { color: "#f2c94c", weight: 2, opacity: 0.9, fillColor: "#f2c94c", fillOpacity: 0.16 },
        }).bindTooltip("Authoritative viewshed").addTo(layer);
      }
      const azimuth = finiteNumber(spatial.azimuth_degrees);
      if (azimuth !== null) L.marker(location, { icon: bearingIcon(azimuth), interactive: false }).addTo(layer);
      const fov = finiteNumber(spatial.field_of_view_degrees);
      const range = finiteNumber(spatial.range_meters);
      if (azimuth !== null && fov !== null && range !== null && fov > 0 && range > 0) {
        L.polygon(fovPolygon(camera, azimuth, fov, range), {
          color: "#54c7ec", weight: 2, fillColor: "#54c7ec", fillOpacity: 0.18,
        }).bindTooltip("Authoritative field of view").addTo(layer);
      }
      const spi = spatial.spi;
      if (spi && finiteNumber(spi.latitude) !== null && finiteNumber(spi.longitude) !== null) {
        const spiLocation = [Number(spi.latitude), Number(spi.longitude)];
        L.polyline([location, spiLocation], { color: "#e24c4c", dashArray: "5 5", weight: 2 }).addTo(layer);
        L.marker(spiLocation, {
          icon: L.divIcon({ className: "tak-camera-bearing-marker", html: '<span class="tak-camera-spi-marker"></span>', iconSize: [17, 17], iconAnchor: [8, 8] }),
          title: spi.name || "Sensor point of interest",
        }).addTo(layer);
      }
      window.setTimeout(() => {
        state.map.invalidateSize();
        const bounds = layer.getBounds();
        if (bounds.isValid() && bounds.getNorthEast().distanceTo(bounds.getSouthWest()) > 20) {
          state.map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15 });
        } else {
          state.map.setView(location, 14);
        }
      }, 40);
    }

    function stopVideo() {
      if (state.hls) { state.hls.destroy(); state.hls = null; }
      elements.video.pause();
      elements.video.onplaying = null;
      elements.video.onerror = null;
      elements.video.removeAttribute("src");
      elements.video.load();
      elements.video.hidden = true;
      elements.image.hidden = false;
    }

    function startVideo(camera) {
      stopVideo();
      const url = camera.playback_url;
      if (!url || !url.toLowerCase().includes(".m3u8")) return;
      const showVideo = () => {
        if (state.camera?.id !== camera.id) return;
        elements.image.hidden = true;
        elements.video.hidden = false;
        elements.video.play().catch(() => {});
      };
      const fallback = () => {
        if (state.camera?.id !== camera.id) return;
        elements.video.hidden = true;
        elements.image.hidden = false;
      };
      elements.video.onplaying = showVideo;
      elements.video.onerror = fallback;
      if (elements.video.canPlayType("application/vnd.apple.mpegurl")) {
        elements.video.src = url;
        elements.video.load();
        elements.video.play().catch(fallback);
      } else if (window.Hls?.isSupported()) {
        const hls = new window.Hls({ liveSyncDurationCount: 2 });
        state.hls = hls;
        hls.on(window.Hls.Events.ERROR, (_event, data) => {
          if (data.fatal) { hls.destroy(); if (state.hls === hls) state.hls = null; fallback(); }
        });
        hls.loadSource(url);
        hls.attachMedia(elements.video);
      }
    }

    function fact(name, value) {
      dialog.querySelector(`[data-fact="${name}"]`).textContent = value;
    }

    function renderCamera(envelope) {
      const camera = envelope.camera;
      const source = camera.source || {};
      const spatial = camera.spatial || {};
      const cached = envelope.state === "cached";
      state.camera = camera;
      state.envelope = envelope;
      elements.warning.hidden = !cached && !envelope.warning;
      elements.warning.textContent = envelope.warning || "";
      stopVideo();
      elements.placeholder.hidden = !cached;
      elements.image.hidden = cached;
      elements.image.src = cached ? "" : (camera.preview_url || camera.image_url || "");
      elements.image.alt = `${camera.name} camera view`;
      if (!cached) startVideo(camera);
      elements.badge.textContent = cached ? "Cached fallback" : (camera.is_demo ? `${camera.status} · demo` : camera.status);
      elements.badge.className = `tak-camera-feed-badge ${cached ? "cached" : statusClass(camera.status)}`;
      elements.time.hidden = !camera.is_demo;
      elements.source.textContent = source.name || camera.source_id || "Camera source";
      elements.title.textContent = camera.name;
      elements.place.textContent = [camera.route, camera.municipality, camera.county, camera.region].filter(Boolean).join(" · ");
      fact("direction", camera.direction || "Not provided");
      fact("media", cached ? "Unavailable while Cambot is offline" : (camera.media_type || "unknown").toUpperCase());
      fact("coordinates", `${Number(camera.latitude).toFixed(4)}, ${Number(camera.longitude).toFixed(4)}`);
      fact("updated", camera.updated_at ? new Date(camera.updated_at).toLocaleString() : (camera.is_demo ? "Demo data" : "Live source; image timestamp not provided"));
      const pov = [spatialFact(spatial.azimuth_degrees, "° bearing"), spatialFact(spatial.tilt_degrees, "° tilt"), spatialFact(spatial.zoom_scale, "× zoom scale")].filter(Boolean);
      fact("pov", pov.length ? pov.join(" · ") : "Not available from source");
      const fov = spatialFact(spatial.field_of_view_degrees, "°");
      const range = spatialFact(spatial.range_meters, " m");
      fact("fov", fov ? `${fov}${range ? ` · ${range}` : ""}` : "Not available from source");
      fact("viewshed", spatial.viewshed ? `Available${spatial.observed_at ? ` · ${new Date(spatial.observed_at).toLocaleString()}` : ""}` : "Not available from source");
      fact("spi", spatial.spi ? `${Number(spatial.spi.latitude).toFixed(5)}, ${Number(spatial.spi.longitude).toFixed(5)}` : "Not available from source");
      elements.sourceLink.href = camera.source_url || source.homepage || camera.canonical_url || "#";
      elements.attribution.textContent = source.attribution || camera.attribution || "";
      elements.scopes[0].checked = true;
      renderSpatial(camera);
      if (cached) disableExport("Live TAK export is unavailable while Cambot is offline.");
      else updateExport();
    }

    function disableExport(message) {
      state.generation += 1;
      state.takUri = "";
      elements.qr.replaceChildren(message);
      elements.expiry.textContent = message;
      elements.download.removeAttribute("href");
      elements.download.setAttribute("aria-disabled", "true");
      elements.copyTak.disabled = true;
    }

    function normalizeAction(payload) {
      return {
        count: Number(payload.count ?? 1),
        downloadUrl: payload.downloadUrl || payload.download_url || payload.mission_package_url || "",
        takUri: payload.takUri || payload.tak_uri || payload.atak_import_uri || "",
        qrUrl: payload.qrUrl || payload.qr_url || payload.qr_svg_url || payload.qr_png_url || "",
        expiresAt: payload.expiresAt ?? payload.expires_at ?? null,
      };
    }

    async function updateExport() {
      if (!state.camera || state.envelope?.state === "cached") return;
      const generation = ++state.generation;
      const scope = elements.scopes.find((input) => input.checked)?.value || scopes[0].id;
      elements.qr.replaceChildren("Preparing QR…");
      elements.expiry.textContent = "Creating TAK link…";
      elements.download.removeAttribute("href");
      elements.download.removeAttribute("aria-disabled");
      elements.copyTak.disabled = true;
      try {
        const action = normalizeAction(await options.createExport({ camera: state.camera, scope, context: state.context }));
        if (generation !== state.generation) return;
        elements.count.textContent = action.count.toLocaleString();
        elements.exportWarning.hidden = action.count <= 1000;
        if (action.count < 1 || action.count > 5000 || !action.downloadUrl) {
          throw new Error(action.count > 5000 ? "Narrow this result set below 5,000 cameras" : "A TAK package cannot be created for this scope.");
        }
        state.takUri = action.takUri;
        elements.download.href = action.downloadUrl;
        elements.copyTak.disabled = !action.takUri;
        let expiry = action.expiresAt;
        if (typeof expiry === "number" && expiry < 100000000000) expiry *= 1000;
        elements.expiry.textContent = expiry
          ? `Scan with ATAK or download directly. Link expires ${new Date(expiry).toLocaleString()}.`
          : "Scan with ATAK or download directly.";
        elements.qr.replaceChildren();
        if (action.qrUrl) {
          const image = document.createElement("img");
          image.src = action.qrUrl;
          image.alt = `TAK import QR for ${state.camera.name}`;
          elements.qr.append(image);
        } else if (window.QRCode && action.takUri) {
          new window.QRCode(elements.qr, { text: action.takUri, width: 160, height: 160, correctLevel: window.QRCode.CorrectLevel.M });
        } else {
          elements.qr.textContent = "QR unavailable; use the download button.";
        }
      } catch (error) {
        if (generation !== state.generation) return;
        elements.count.textContent = "—";
        elements.qr.textContent = "TAK QR unavailable";
        elements.expiry.textContent = error.message || "Unable to create TAK export.";
      }
    }

    async function load(id, context = null) {
      state.context = context;
      const generation = ++state.generation;
      if (!dialog.open) dialog.showModal();
      elements.title.textContent = "Loading camera…";
      elements.warning.hidden = true;
      try {
        const result = await options.loadCamera(id, context);
        if (generation !== state.generation) return;
        const envelope = result?.camera ? result : { state: "live", camera: result };
        if (!envelope.camera) throw new Error("Camera details unavailable");
        renderCamera(envelope);
        options.onOpen?.({ camera: envelope.camera, envelope, context });
      } catch (error) {
        if (generation !== state.generation) return;
        close(false);
        options.onError?.(error);
      }
    }

    function close(notify = true) {
      state.generation += 1;
      stopVideo();
      if (dialog.open) dialog.close();
      const previous = { camera: state.camera, envelope: state.envelope, context: state.context };
      state.camera = null;
      state.envelope = null;
      state.context = null;
      state.takUri = "";
      state.spatialLayer?.clearLayers();
      if (notify) options.onClose?.(previous);
    }

    elements.close.addEventListener("click", () => close());
    dialog.addEventListener("cancel", (event) => { event.preventDefault(); close(); });
    dialog.addEventListener("click", (event) => { if (event.target === dialog) close(); });
    elements.scopes.forEach((input) => input.addEventListener("change", updateExport));
    elements.copyProfile.addEventListener("click", async () => {
      const url = state.camera?.canonical_url || window.location.href;
      try { await navigator.clipboard.writeText(url); options.toast?.("Camera profile link copied"); }
      catch (_error) { options.toast?.("Copy unavailable; open the authoritative profile instead"); }
    });
    elements.copyTak.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(state.takUri); options.toast?.("TAK import link copied"); }
      catch (_error) { options.toast?.("Copy unavailable; scan the QR code instead"); }
    });

    return { load, close, dialog, currentCamera: () => state.camera };
  }

  window.TakCameraProfile = Object.freeze({ create: createCameraProfile });
})();
