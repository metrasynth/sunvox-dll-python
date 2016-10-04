import sunvox


def test_init_deinit():
    flags = (
        sunvox.SV_INIT_FLAG.ONE_THREAD |
        sunvox.SV_INIT_FLAG.USER_AUDIO_CALLBACK
    )
    sunvox.init(None, 44100, 2, flags)
    sunvox.deinit()
