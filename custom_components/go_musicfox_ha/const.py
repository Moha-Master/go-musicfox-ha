"""Constants for the Go Musicfox HA integration."""

DOMAIN = "go_musicfox_ha"

PLAY_MODES = ["ordered", "list_loop", "single_loop", "list_random", "inf_random", "intelligent"]

PLAY_MODE_MAP = {
    "ordered": "顺序播放",
    "list_loop": "列表循环",
    "single_loop": "单曲循环",
    "list_random": "列表随机",
    "inf_random": "无限随机",
    "intelligent": "心动模式",
}

PLAY_MODE_CODE_MAP = {
    1: "list_loop",
    2: "ordered",
    3: "single_loop",
    4: "list_random",
    5: "inf_random",
    6: "intelligent",
}