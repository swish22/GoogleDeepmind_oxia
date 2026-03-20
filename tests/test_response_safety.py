from chat.response_safety import ensure_three_suggestions


def test_ensure_three_suggestions_pads_and_trims():
    padded = ensure_three_suggestions([], "glucose")
    assert len(padded) == 3

    one = ensure_three_suggestions(["What next?"], "glucose")
    assert len(one) == 3
    assert one[0] == "What next?"

    many = ensure_three_suggestions(["a", "b", "c", "d", "e"], "glucose")
    assert many == ["a", "b", "c"]

