import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KITTY = ROOT / "home/private_dot_config/kitty/kitty.conf"
HERDR = ROOT / "home/private_dot_config/herdr/config.toml"


def chord(binding):
    *mods, key = binding.lower().split("+")
    return "+".join(sorted(mods) + [key])


def kitty_passes_to_herdr():
    return {
        chord(m.group(1))
        for m in re.finditer(r"^map --when-focus-on title:\^herdr: (\S+)$", KITTY.read_text(), re.M)
    }


def herdr_direct_bindings():
    keys = tomllib.loads(HERDR.read_text())["keys"]
    chords = {chord(command["key"]) for command in keys["command"]}
    for action, value in keys.items():
        if action == "command":
            continue
        for binding in [value] if isinstance(value, str) else value:
            if binding.startswith("prefix+"):
                continue
            if binding.endswith("1..9"):
                chords |= {chord(binding.replace("1..9", str(n))) for n in range(1, 10)}
            else:
                chords.add(chord(binding))
    return chords


def test_kitty_passes_exactly_the_keys_herdr_binds_directly():
    assert kitty_passes_to_herdr() == herdr_direct_bindings()
