import sunvox.api


def test_init_deinit():
    flags = sunvox.api.INIT_FLAG.ONE_THREAD | sunvox.api.INIT_FLAG.USER_AUDIO_CALLBACK
    sunvox.api.init(None, 44100, 2, flags)
    sunvox.api.deinit()
