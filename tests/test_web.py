from takinterop import web_assets_path


def test_shared_camera_profile_assets_are_packaged() -> None:
    root = web_assets_path()
    script = (root / "camera-profile.js").read_text(encoding="utf-8")
    styles = (root / "camera-profile.css").read_text(encoding="utf-8")

    assert "window.TakCameraProfile" in script
    assert "createExport" in script
    assert ".tak-camera-profile" in styles
