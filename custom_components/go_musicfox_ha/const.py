"""Constants for the Go Musicfox HA integration."""

DOMAIN = "go_musicfox"

PLAY_MODES = ["ordered", "list_loop", "single_loop", "list_random", "inf_random", "intelligent"]

PLAY_MODE_CODE_MAP = {
    1: "list_loop",
    2: "ordered",
    3: "single_loop",
    4: "list_random",
    5: "inf_random",
    6: "intelligent",
}
