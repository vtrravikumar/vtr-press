from renderer.document_assets import DocumentAssets


def test_resolve_stages_existing_relative_asset(tmp_path):
    manuscript = tmp_path / "docs" / "engineering" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    asset = tmp_path / "assets" / "images" / "architecture.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"PNG DATA")

    staging = tmp_path / "generated" / "assets" / "TestDocument"

    with DocumentAssets(
        manuscript,
        staging_root=staging,
    ) as assets:
        resolved = assets.resolve("../../assets/images/architecture.png")

        assert resolved is not None
        assert resolved.source_path == asset.resolve()
        assert resolved.staged_path.exists()
        assert resolved.staged_path.read_bytes() == b"PNG DATA"
        assert resolved.epub_href == "images/architecture.png"
        assert resolved.media_type == "image/png"
        assert assets.missing == []


def test_missing_asset_does_not_raise(tmp_path):
    manuscript = tmp_path / "docs" / "engineering" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    staging = tmp_path / "generated" / "assets" / "TestDocument"

    with DocumentAssets(
        manuscript,
        staging_root=staging,
    ) as assets:
        resolved = assets.resolve("../../assets/images/missing.png")

        assert resolved is None
        assert assets.missing == ["../../assets/images/missing.png"]
        assert assets.resolved == ()


def test_absolute_asset_path_is_rejected(tmp_path):
    manuscript = tmp_path / "docs" / "engineering" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    asset = tmp_path / "outside.png"
    asset.write_bytes(b"outside")

    staging = tmp_path / "generated" / "assets" / "TestDocument"

    with DocumentAssets(
        manuscript,
        staging_root=staging,
    ) as assets:
        resolved = assets.resolve(str(asset))

        assert resolved is None
        assert assets.missing == [str(asset)]


def test_repeated_reference_is_resolved_once(tmp_path):
    manuscript = tmp_path / "docs" / "engineering" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    asset = tmp_path / "assets" / "architecture.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"PNG DATA")

    source = "../../assets/architecture.png"
    staging = tmp_path / "generated" / "assets" / "TestDocument"

    with DocumentAssets(
        manuscript,
        staging_root=staging,
    ) as assets:
        first = assets.resolve(source)
        second = assets.resolve(source)

        assert first is second
        assert len(assets.resolved) == 1
        assert assets.missing == []


def test_staging_directory_is_preserved(tmp_path):
    manuscript = tmp_path / "docs" / "engineering" / "EngineeringDesign.md"
    manuscript.parent.mkdir(parents=True)

    asset = tmp_path / "assets" / "architecture.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"PNG DATA")

    staging = tmp_path / "generated" / "assets" / "TestDocument"

    with DocumentAssets(
        manuscript,
        staging_root=staging,
    ) as assets:
        resolved = assets.resolve("../../assets/architecture.png")

        assert resolved is not None
        assert resolved.staged_path.exists()
        staged_path = resolved.staged_path

    assert staging.exists()
    assert staged_path.exists()
    assert staged_path.read_bytes() == b"PNG DATA"