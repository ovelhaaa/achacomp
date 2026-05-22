from component_radar.normalizer import is_component_match, normalize_component_token


def test_normalization_variants_lm308():
    assert normalize_component_token("LM308") == "LM308"
    assert normalize_component_token("LM 308") == "LM308"
    assert normalize_component_token("lm308n") == "LM308"
    assert normalize_component_token("LM308AN") == "LM308"


def test_false_positive_2sk30_vs_2sk301():
    assert not is_component_match("2SK30", "Transistor 2SK301 TO-92")


def test_true_positive_with_suffix():
    assert is_component_match("LM308", "Opamp LM308N DIP8")
