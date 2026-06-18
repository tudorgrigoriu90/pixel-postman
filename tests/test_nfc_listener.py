from src.nfc_listener import NFCListener


def test_fires_once_per_presentation():
    listener = NFCListener(on_scan=lambda uid: None)

    # Tag placed and held for several poll cycles -> fires exactly once.
    assert listener._decide("04AABB") == "04AABB"
    assert listener._decide("04AABB") is None
    assert listener._decide("04AABB") is None


def test_refires_after_removal():
    listener = NFCListener(on_scan=lambda uid: None)
    assert listener._decide("04AABB") == "04AABB"
    assert listener._decide(None) is None       # lifted off the reader
    assert listener._decide("04AABB") == "04AABB"  # placed back -> fires again


def test_different_tag_fires_immediately():
    listener = NFCListener(on_scan=lambda uid: None)
    assert listener._decide("04AABB") == "04AABB"
    assert listener._decide("04CCDD") == "04CCDD"  # swapped postcard
