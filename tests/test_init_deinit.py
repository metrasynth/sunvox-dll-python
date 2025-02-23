import sunvox.api


def test_init_deinit():
    # given: the user wants to initialize the SunVox library

    # and: the user doesn't want to load a custom configuration
    config = None

    # and: the user wants a sample rate of 44100
    freq = 44100

    # and: the user wants 2 audio channels
    channels = 2

    # and: they want it to run in one thread
    flags = 0
    flags |= sunvox.api.INIT_FLAG.ONE_THREAD

    # and: they want to use a custom audio callback
    flags |= sunvox.api.INIT_FLAG.USER_AUDIO_CALLBACK

    # when: the library is initialized
    version = sunvox.api.init(config, freq, channels, flags)

    # and: the library is deinitialized
    deinit_response = sunvox.api.deinit()

    # then: the version reported is 2.1.2
    assert version == 0x020102

    # and: the deinitialization was successful
    assert deinit_response == 0
