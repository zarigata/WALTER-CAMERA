import json


def test_message_examples():
    slider = {"type": "slider", "id": "effect.intensity", "value": 0.7}
    trigger = {"type": "trigger", "action": "record"}
    params = {"type": "params", "data": {"effect.intensity": 0.7}}
    # Validate presence of keys
    assert slider["type"] == "slider" and "id" in slider and "value" in slider
    assert trigger["type"] == "trigger" and "action" in trigger
    assert params["type"] == "params" and "data" in params
