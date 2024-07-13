#!/usr/bin/env python3

import argparse
from typing import List
from enum import Enum


class Qt_KeyboardModifier(Enum):
    # enum Qt::KeyboardModifier
    # https://doc.qt.io/qt-6/qt.html#KeyboardModifier-enum
    # This enum describes the modifier keys.
    """
    Note:
    On macOS, the ControlModifier value corresponds to the 
    Command keys on the keyboard, and the MetaModifier value 
    corresponds to the Control keys. The KeypadModifier 
    value will also be set when an arrow key is pressed as 
    the arrow keys are considered part of the keypad.
    """

    """
    Note:
    On Windows Keyboards, Qt::MetaModifier and Qt::Key_Meta 
    are mapped to the Windows key.
    """

    """
    The KeyboardModifiers type is a typedef for QFlags<KeyboardModifier>.
    It stores an OR combination of KeyboardModifier values.
    """

    # Constant                  # Value
    NoModifier                  = 0x00000000

    ShiftModifier               = 0x02000000
    ControlModifier             = 0x04000000
    AltModifier                 = 0x08000000

    MetaModifier                = 0x10000000
    KeypadModifier              = 0x20000000
    GroupSwitchModifier         = 0x40000000



class Qt_Key(Enum):
    # enum Qt::Key
    # https://doc.qt.io/qt-6/qt.html#Key-enum
    # The key names used by Qt.
    # Constant                  # Value             # Description
    Key_Escape                  = 0x01000000
    Key_Tab                     = 0x01000001
    Key_Backtab                 = 0x01000002
    Key_Backspace               = 0x01000003
    Key_Return                  = 0x01000004
    Key_Enter                   = 0x01000005        # Typically located on the keypad.
    Key_Insert                  = 0x01000006
    Key_Delete                  = 0x01000007
    Key_Pause                   = 0x01000008        # The Pause/Break key (Note: Not related to pausing media)
    Key_Print                   = 0x01000009
    Key_SysReq                  = 0x0100000a
    Key_Clear                   = 0x0100000b        # Corresponds to the Clear key on selected Apple keyboard models. On other systems it is commonly mapped to the numeric keypad key 5, when Num Lock is off.
    Key_Home                    = 0x01000010
    Key_End                     = 0x01000011
    Key_Left                    = 0x01000012
    Key_Up                      = 0x01000013
    Key_Right                   = 0x01000014
    Key_Down                    = 0x01000015
    Key_PageUp                  = 0x01000016
    Key_PageDown                = 0x01000017
    Key_Shift                   = 0x01000020
    Key_Control                 = 0x01000021        # On macOS, this corresponds to the Command keys.
    Key_Meta                    = 0x01000022        # On macOS, this corresponds to the Control keys. On Windows keyboards, this key is mapped to the Windows key.
    Key_Alt                     = 0x01000023
    Key_AltGr                   = 0x01001103        # On Windows, when the KeyDown event for this key is sent, the Ctrl+Alt modifiers are also set.
    Key_CapsLock                = 0x01000024
    Key_NumLock                 = 0x01000025
    Key_ScrollLock              = 0x01000026
    Key_F1                      = 0x01000030
    Key_F2                      = 0x01000031
    Key_F3                      = 0x01000032
    Key_F4                      = 0x01000033
    Key_F5                      = 0x01000034
    Key_F6                      = 0x01000035
    Key_F7                      = 0x01000036
    Key_F8                      = 0x01000037
    Key_F9                      = 0x01000038
    Key_F10                     = 0x01000039
    Key_F11                     = 0x0100003a
    Key_F12                     = 0x0100003b
    Key_F13                     = 0x0100003c
    Key_F14                     = 0x0100003d
    Key_F15                     = 0x0100003e
    Key_F16                     = 0x0100003f
    Key_F17                     = 0x01000040
    Key_F18                     = 0x01000041
    Key_F19                     = 0x01000042
    Key_F20                     = 0x01000043
    Key_F21                     = 0x01000044
    Key_F22                     = 0x01000045
    Key_F23                     = 0x01000046
    Key_F24                     = 0x01000047
    Key_F25                     = 0x01000048
    Key_F26                     = 0x01000049
    Key_F27                     = 0x0100004a
    Key_F28                     = 0x0100004b
    Key_F29                     = 0x0100004c
    Key_F30                     = 0x0100004d
    Key_F31                     = 0x0100004e
    Key_F32                     = 0x0100004f
    Key_F33                     = 0x01000050
    Key_F34                     = 0x01000051
    Key_F35                     = 0x01000052
    Key_Super_L                 = 0x01000053
    Key_Super_R                 = 0x01000054
    Key_Menu                    = 0x01000055
    Key_Hyper_L                 = 0x01000056
    Key_Hyper_R                 = 0x01000057
    Key_Help                    = 0x01000058
    Key_Direction_L             = 0x01000059
    Key_Direction_R             = 0x01000060
    Key_Space                   = 0x20
    # Key_Any                     = Key_Space
    Key_Exclam                  = 0x21
    Key_QuoteDbl                = 0x22
    Key_NumberSign              = 0x23
    Key_Dollar                  = 0x24
    Key_Percent                 = 0x25
    Key_Ampersand               = 0x26
    Key_Apostrophe              = 0x27
    Key_ParenLeft               = 0x28
    Key_ParenRight              = 0x29
    Key_Asterisk                = 0x2a
    Key_Plus                    = 0x2b
    Key_Comma                   = 0x2c
    Key_Minus                   = 0x2d
    Key_Period                  = 0x2e
    Key_Slash                   = 0x2f
    Key_0                       = 0x30
    Key_1                       = 0x31
    Key_2                       = 0x32
    Key_3                       = 0x33
    Key_4                       = 0x34
    Key_5                       = 0x35
    Key_6                       = 0x36
    Key_7                       = 0x37
    Key_8                       = 0x38
    Key_9                       = 0x39
    Key_Colon                   = 0x3a
    Key_Semicolon               = 0x3b
    Key_Less                    = 0x3c
    Key_Equal                   = 0x3d
    Key_Greater                 = 0x3e
    Key_Question                = 0x3f
    Key_At                      = 0x40
    Key_A                       = 0x41
    Key_B                       = 0x42
    Key_C                       = 0x43
    Key_D                       = 0x44
    Key_E                       = 0x45
    Key_F                       = 0x46
    Key_G                       = 0x47
    Key_H                       = 0x48
    Key_I                       = 0x49
    Key_J                       = 0x4a
    Key_K                       = 0x4b
    Key_L                       = 0x4c
    Key_M                       = 0x4d
    Key_N                       = 0x4e
    Key_O                       = 0x4f
    Key_P                       = 0x50
    Key_Q                       = 0x51
    Key_R                       = 0x52
    Key_S                       = 0x53
    Key_T                       = 0x54
    Key_U                       = 0x55
    Key_V                       = 0x56
    Key_W                       = 0x57
    Key_X                       = 0x58
    Key_Y                       = 0x59
    Key_Z                       = 0x5a
    Key_BracketLeft             = 0x5b
    Key_Backslash               = 0x5c
    Key_BracketRight            = 0x5d
    Key_AsciiCircum             = 0x5e
    Key_Underscore              = 0x5f
    Key_QuoteLeft               = 0x60              # This is what other key lists might call Key_Grave
    Key_BraceLeft               = 0x7b
    Key_Bar                     = 0x7c
    Key_BraceRight              = 0x7d
    Key_AsciiTilde              = 0x7e
    Key_nobreakspace            = 0x0a0
    Key_exclamdown              = 0x0a1
    Key_cent                    = 0x0a2
    Key_sterling                = 0x0a3
    Key_currency                = 0x0a4
    Key_yen                     = 0x0a5
    Key_brokenbar               = 0x0a6
    Key_section                 = 0x0a7
    Key_diaeresis               = 0x0a8
    Key_copyright               = 0x0a9
    Key_ordfeminine             = 0x0aa
    Key_guillemotleft           = 0x0ab
    Key_notsign                 = 0x0ac
    Key_hyphen                  = 0x0ad
    Key_registered              = 0x0ae
    Key_macron                  = 0x0af
    Key_degree                  = 0x0b0
    Key_plusminus               = 0x0b1
    Key_twosuperior             = 0x0b2
    Key_threesuperior           = 0x0b3
    Key_acute                   = 0x0b4
    Key_micro                   = 0x0b5             # (since Qt 6.7)
    # Key_mu                      = Key_micro         # Deprecated alias for Key_micro
    Key_paragraph               = 0x0b6
    Key_periodcentered          = 0x0b7
    Key_cedilla                 = 0x0b8
    Key_onesuperior             = 0x0b9
    Key_masculine               = 0x0ba
    Key_guillemotright          = 0x0bb
    Key_onequarter              = 0x0bc
    Key_onehalf                 = 0x0bd
    Key_threequarters           = 0x0be
    Key_questiondown            = 0x0bf
    Key_Agrave                  = 0x0c0
    Key_Aacute                  = 0x0c1
    Key_Acircumflex             = 0x0c2
    Key_Atilde                  = 0x0c3
    Key_Adiaeresis              = 0x0c4
    Key_Aring                   = 0x0c5
    Key_AE                      = 0x0c6
    Key_Ccedilla                = 0x0c7
    Key_Egrave                  = 0x0c8
    Key_Eacute                  = 0x0c9
    Key_Ecircumflex             = 0x0ca
    Key_Ediaeresis              = 0x0cb
    Key_Igrave                  = 0x0cc
    Key_Iacute                  = 0x0cd
    Key_Icircumflex             = 0x0ce
    Key_Idiaeresis              = 0x0cf
    Key_ETH                     = 0x0d0
    Key_Ntilde                  = 0x0d1
    Key_Ograve                  = 0x0d2
    Key_Oacute                  = 0x0d3
    Key_Ocircumflex             = 0x0d4
    Key_Otilde                  = 0x0d5
    Key_Odiaeresis              = 0x0d6
    Key_multiply                = 0x0d7
    Key_Ooblique                = 0x0d8
    Key_Ugrave                  = 0x0d9
    Key_Uacute                  = 0x0da
    Key_Ucircumflex             = 0x0db
    Key_Udiaeresis              = 0x0dc
    Key_Yacute                  = 0x0dd
    Key_THORN                   = 0x0de
    Key_ssharp                  = 0x0df
    Key_division                = 0x0f7
    Key_ydiaeresis              = 0x0ff
    Key_Multi_key               = 0x01001120
    Key_Codeinput               = 0x01001137
    Key_SingleCandidate         = 0x0100113c
    Key_MultipleCandidate       = 0x0100113d
    Key_PreviousCandidate       = 0x0100113e
    Key_Mode_switch             = 0x0100117e
    Key_Kanji                   = 0x01001121
    Key_Muhenkan                = 0x01001122
    Key_Henkan                  = 0x01001123
    Key_Romaji                  = 0x01001124
    Key_Hiragana                = 0x01001125
    Key_Katakana                = 0x01001126
    Key_Hiragana_Katakana       = 0x01001127
    Key_Zenkaku                 = 0x01001128
    Key_Hankaku                 = 0x01001129
    Key_Zenkaku_Hankaku         = 0x0100112a
    Key_Touroku                 = 0x0100112b
    Key_Massyo                  = 0x0100112c
    Key_Kana_Lock               = 0x0100112d
    Key_Kana_Shift              = 0x0100112e
    Key_Eisu_Shift              = 0x0100112f
    Key_Eisu_toggle             = 0x01001130
    Key_Hangul                  = 0x01001131
    Key_Hangul_Start            = 0x01001132
    Key_Hangul_End              = 0x01001133
    Key_Hangul_Hanja            = 0x01001134
    Key_Hangul_Jamo             = 0x01001135
    Key_Hangul_Romaja           = 0x01001136
    Key_Hangul_Jeonja           = 0x01001138
    Key_Hangul_Banja            = 0x01001139
    Key_Hangul_PreHanja         = 0x0100113a
    Key_Hangul_PostHanja        = 0x0100113b
    Key_Hangul_Special          = 0x0100113f
    Key_Dead_Grave              = 0x01001250
    Key_Dead_Acute              = 0x01001251
    Key_Dead_Circumflex         = 0x01001252
    Key_Dead_Tilde              = 0x01001253
    Key_Dead_Macron             = 0x01001254
    Key_Dead_Breve              = 0x01001255
    Key_Dead_Abovedot           = 0x01001256
    Key_Dead_Diaeresis          = 0x01001257
    Key_Dead_Abovering          = 0x01001258
    Key_Dead_Doubleacute        = 0x01001259
    Key_Dead_Caron              = 0x0100125a
    Key_Dead_Cedilla            = 0x0100125b
    Key_Dead_Ogonek             = 0x0100125c
    Key_Dead_Iota               = 0x0100125d
    Key_Dead_Voiced_Sound       = 0x0100125e
    Key_Dead_Semivoiced_Sound   = 0x0100125f
    Key_Dead_Belowdot           = 0x01001260
    Key_Dead_Hook               = 0x01001261
    Key_Dead_Horn               = 0x01001262
    Key_Dead_Stroke             = 0x01001263
    Key_Dead_Abovecomma         = 0x01001264
    Key_Dead_Abovereversedcomma = 0x01001265
    Key_Dead_Doublegrave        = 0x01001266
    Key_Dead_Belowring          = 0x01001267
    Key_Dead_Belowmacron        = 0x01001268
    Key_Dead_Belowcircumflex    = 0x01001269
    Key_Dead_Belowtilde         = 0x0100126a
    Key_Dead_Belowbreve         = 0x0100126b
    Key_Dead_Belowdiaeresis     = 0x0100126c
    Key_Dead_Invertedbreve      = 0x0100126d
    Key_Dead_Belowcomma         = 0x0100126e
    Key_Dead_Currency           = 0x0100126f
    Key_Dead_a                  = 0x01001280
    Key_Dead_A                  = 0x01001281
    Key_Dead_e                  = 0x01001282
    Key_Dead_E                  = 0x01001283
    Key_Dead_i                  = 0x01001284
    Key_Dead_I                  = 0x01001285
    Key_Dead_o                  = 0x01001286
    Key_Dead_O                  = 0x01001287
    Key_Dead_u                  = 0x01001288
    Key_Dead_U                  = 0x01001289
    Key_Dead_Small_Schwa        = 0x0100128a
    Key_Dead_Capital_Schwa      = 0x0100128b
    Key_Dead_Greek              = 0x0100128c
    Key_Dead_Lowline            = 0x01001290
    Key_Dead_Aboveverticalline  = 0x01001291
    Key_Dead_Belowverticalline  = 0x01001292
    Key_Dead_Longsolidusoverlay = 0x01001293
    Key_Back                    = 0x01000061
    Key_Forward                 = 0x01000062
    Key_Stop                    = 0x01000063
    Key_Refresh                 = 0x01000064
    Key_VolumeDown              = 0x01000070
    Key_VolumeMute              = 0x01000071
    Key_VolumeUp                = 0x01000072
    Key_BassBoost               = 0x01000073
    Key_BassUp                  = 0x01000074
    Key_BassDown                = 0x01000075
    Key_TrebleUp                = 0x01000076
    Key_TrebleDown              = 0x01000077
    Key_MediaPlay               = 0x01000080        # A key setting the state of the media player to play
    Key_MediaStop               = 0x01000081        # A key setting the state of the media player to stop
    Key_MediaPrevious           = 0x01000082
    Key_MediaNext               = 0x01000083
    Key_MediaRecord             = 0x01000084
    Key_MediaPause              = 0x01000085        # A key setting the state of the media player to pause (Note: not the pause/break key)
    Key_MediaTogglePlayPause    = 0x01000086        # A key to toggle the play/pause state in the media player (rather than setting an absolute state)
    Key_HomePage                = 0x01000090
    Key_Favorites               = 0x01000091
    Key_Search                  = 0x01000092
    Key_Standby                 = 0x01000093
    Key_OpenUrl                 = 0x01000094
    Key_LaunchMail              = 0x010000a0
    Key_LaunchMedia             = 0x010000a1
    Key_Launch0                 = 0x010000a2
    Key_Launch1                 = 0x010000a3
    Key_Launch2                 = 0x010000a4
    Key_Launch3                 = 0x010000a5
    Key_Launch4                 = 0x010000a6
    Key_Launch5                 = 0x010000a7
    Key_Launch6                 = 0x010000a8
    Key_Launch7                 = 0x010000a9
    Key_Launch8                 = 0x010000aa
    Key_Launch9                 = 0x010000ab
    Key_LaunchA                 = 0x010000ac
    Key_LaunchB                 = 0x010000ad
    Key_LaunchC                 = 0x010000ae
    Key_LaunchD                 = 0x010000af
    Key_LaunchE                 = 0x010000b0
    Key_LaunchF                 = 0x010000b1
    Key_LaunchG                 = 0x0100010e
    Key_LaunchH                 = 0x0100010f
    Key_MonBrightnessUp         = 0x010000b2
    Key_MonBrightnessDown       = 0x010000b3
    Key_KeyboardLightOnOff      = 0x010000b4
    Key_KeyboardBrightnessUp    = 0x010000b5
    Key_KeyboardBrightnessDown  = 0x010000b6
    Key_PowerOff                = 0x010000b7
    Key_WakeUp                  = 0x010000b8
    Key_Eject                   = 0x010000b9
    Key_ScreenSaver             = 0x010000ba
    Key_WWW                     = 0x010000bb
    Key_Memo                    = 0x010000bc
    Key_LightBulb               = 0x010000bd
    Key_Shop                    = 0x010000be
    Key_History                 = 0x010000bf
    Key_AddFavorite             = 0x010000c0
    Key_HotLinks                = 0x010000c1
    Key_BrightnessAdjust        = 0x010000c2
    Key_Finance                 = 0x010000c3
    Key_Community               = 0x010000c4
    Key_AudioRewind             = 0x010000c5
    Key_BackForward             = 0x010000c6
    Key_ApplicationLeft         = 0x010000c7
    Key_ApplicationRight        = 0x010000c8
    Key_Book                    = 0x010000c9
    Key_CD                      = 0x010000ca
    Key_Calculator              = 0x010000cb
    Key_ToDoList                = 0x010000cc
    Key_ClearGrab               = 0x010000cd
    Key_Close                   = 0x010000ce
    Key_Copy                    = 0x010000cf
    Key_Cut                     = 0x010000d0
    Key_Display                 = 0x010000d1
    Key_DOS                     = 0x010000d2
    Key_Documents               = 0x010000d3
    Key_Excel                   = 0x010000d4
    Key_Explorer                = 0x010000d5
    Key_Game                    = 0x010000d6
    Key_Go                      = 0x010000d7
    Key_iTouch                  = 0x010000d8
    Key_LogOff                  = 0x010000d9
    Key_Market                  = 0x010000da
    Key_Meeting                 = 0x010000db
    Key_MenuKB                  = 0x010000dc
    Key_MenuPB                  = 0x010000dd
    Key_MySites                 = 0x010000de
    Key_News                    = 0x010000df
    Key_OfficeHome              = 0x010000e0
    Key_Option                  = 0x010000e1
    Key_Paste                   = 0x010000e2
    Key_Phone                   = 0x010000e3
    Key_Calendar                = 0x010000e4
    Key_Reply                   = 0x010000e5
    Key_Reload                  = 0x010000e6
    Key_RotateWindows           = 0x010000e7
    Key_RotationPB              = 0x010000e8
    Key_RotationKB              = 0x010000e9
    Key_Save                    = 0x010000ea
    Key_Send                    = 0x010000eb
    Key_Spell                   = 0x010000ec
    Key_SplitScreen             = 0x010000ed
    Key_Support                 = 0x010000ee
    Key_TaskPane                = 0x010000ef
    Key_Terminal                = 0x010000f0
    Key_Tools                   = 0x010000f1
    Key_Travel                  = 0x010000f2
    Key_Video                   = 0x010000f3
    Key_Word                    = 0x010000f4
    Key_Xfer                    = 0x010000f5
    Key_ZoomIn                  = 0x010000f6
    Key_ZoomOut                 = 0x010000f7
    Key_Away                    = 0x010000f8
    Key_Messenger               = 0x010000f9
    Key_WebCam                  = 0x010000fa
    Key_MailForward             = 0x010000fb
    Key_Pictures                = 0x010000fc
    Key_Music                   = 0x010000fd
    Key_Battery                 = 0x010000fe
    Key_Bluetooth               = 0x010000ff
    Key_WLAN                    = 0x01000100
    Key_UWB                     = 0x01000101
    Key_AudioForward            = 0x01000102
    Key_AudioRepeat             = 0x01000103
    Key_AudioRandomPlay         = 0x01000104
    Key_Subtitle                = 0x01000105
    Key_AudioCycleTrack         = 0x01000106
    Key_Time                    = 0x01000107
    Key_Hibernate               = 0x01000108
    Key_View                    = 0x01000109
    Key_TopMenu                 = 0x0100010a
    Key_PowerDown               = 0x0100010b
    Key_Suspend                 = 0x0100010c
    Key_ContrastAdjust          = 0x0100010d
    Key_TouchpadToggle          = 0x01000110
    Key_TouchpadOn              = 0x01000111
    Key_TouchpadOff             = 0x01000112
    Key_MicMute                 = 0x01000113
    Key_Red                     = 0x01000114
    Key_Green                   = 0x01000115
    Key_Yellow                  = 0x01000116
    Key_Blue                    = 0x01000117
    Key_ChannelUp               = 0x01000118
    Key_ChannelDown             = 0x01000119
    Key_Guide                   = 0x0100011a
    Key_Info                    = 0x0100011b
    Key_Settings                = 0x0100011c
    Key_MicVolumeUp             = 0x0100011d
    Key_MicVolumeDown           = 0x0100011e
    Key_New                     = 0x01000120
    Key_Open                    = 0x01000121
    Key_Find                    = 0x01000122
    Key_Undo                    = 0x01000123
    Key_Redo                    = 0x01000124
    Key_MediaLast               = 0x0100ffff
    Key_unknown                 = 0x01ffffff
    Key_Call                    = 0x01100004        # A key to answer or initiate a call (see Qt::Key_ToggleCallHangup for a key to toggle current call state)
    Key_Camera                  = 0x01100020        # A key to activate the camera shutter. On Windows Runtime, the environment variable QT_QPA_ENABLE_CAMERA_KEYS must be set to receive the event.
    Key_CameraFocus             = 0x01100021        # A key to focus the camera. On Windows Runtime, the environment variable QT_QPA_ENABLE_CAMERA_KEYS must be set to receive the event.
    Key_Context1                = 0x01100000
    Key_Context2                = 0x01100001
    Key_Context3                = 0x01100002
    Key_Context4                = 0x01100003
    Key_Flip                    = 0x01100006
    Key_Hangup                  = 0x01100005        # A key to end an ongoing call (see Qt::Key_ToggleCallHangup for a key to toggle current call state)
    Key_No                      = 0x01010002
    Key_Select                  = 0x01010000
    Key_Yes                     = 0x01010001
    Key_ToggleCallHangup        = 0x01100007        # A key to toggle the current call state (ie. either answer, or hangup) depending on current call state
    Key_VoiceDial               = 0x01100008
    Key_LastNumberRedial        = 0x01100009
    Key_Execute                 = 0x01020003
    Key_Printer                 = 0x01020002
    Key_Play                    = 0x01020005
    Key_Sleep                   = 0x01020004
    Key_Zoom                    = 0x01020006
    Key_Exit                    = 0x0102000a
    Key_Cancel                  = 0x01020001


"""
Special Multi-Modifier-Only shortcuts note:

A modifier-only shortcut using multiple modifiers will produce different
encoded integers depending on the order in which the modifier keys are
presented to the converter. This is because the first modifier(s) will be
converted as a "modifier", while the last will converted as a "key". (All
the modifiers also appear in the Qt::Key enum list.)

Fortunately, this doesn't matter. Plasma/KWin appears to internally
translate the integers into something that will allow the shortcut to
be triggered regardless of the order in which the multi-modifier-only
keys in a modifier-only shortcut are pressed. Smart.

But the results from the converter may seem somewhat arbitrary, depending
on the order in which the modifiers are provided in the argument string.

Example of this phenomenon:

Meta+Ctrl = 285212705 (Plasma internal order, Ctrl gets its "key" value)
Ctrl+Meta = 83886114 (Meta gets its "key" value instead, different result)

Handling logic for this special case was added (pre-sorting if all keys
given in string argument are in the modifiers list). This should cause
the same integer to come out regardless of the original order:

Meta+Ctrl = 285212705
Ctrl+Meta = 285212705 (got pre-sorted to Meta+Ctrl)

Notes on some Qt key naming quirks: 

Other sources call the key the Tilde is on the "Grave" key, while Qt::Key
has several "grave" keys, but the key that correlates to "Grave" is actually
the "Key_QuoteLeft" key. I'm including a way to use "Grave" as part of the
input combo string, which will then be matched with "Key_QuoteLeft" on both
input and output. It shows a note about the conversion in the terminal. 

The Plasma Shortcuts settings dialog displays characters for keys like 
Grave/QuoteLeft "`" or Tilde "~" instead of the key name. So the actual name
of the key may not be well-known. I'm not sure I want to process those 
characters directly as arguments. That would be a lot of work with filtering.

Qt:Key puts the string "Ascii" in front of what are commonly known as just
"Tilde" and "Circum" in other sources. I'm including some translation
logic that will add the "Ascii" when necessary for matching, and remove it
for the "normalized" shortcut combo displayed on output. 

The "Control" key is allowed to be entered in the shortcut string as
"Ctrl", which is quite common in other shortcut representations. The full
name of the key will be displayed to make it obvious that "Ctrl" is not
the name of the key in Qt::Key. 

The Plasma Shortcuts settings dialog also displays "Control" as "Ctrl",
for the sake of brevity, I assume. So it is not unusual to show the final 
combo with "Ctrl" instead of "Control". 

Usability enhancements:

Handles string input in the terminal command line with or without quotes, 
as long as it is a single, unbroken string. 

Delimiter for key string can be either plus "+" or minus/dash "-". Will be
internally converted into a plus "+" for consistency. 

If key name capitalization doesn't match, a search function will suggest
alternatives based on the substring match. 


"""


# 'Ctrl' is not in the modifiers list, but 'Ctrl' is translated to 'Control'
# internally, and should sort like 'Control' in the preferred order. 
preferred_mod_order = ['Meta', 'Ctrl', 'Control', 'Alt', 'Shift', 'Keypad']


def is_integer(s: str):
    return s.lstrip('-').isdigit()


def capitalize_first_letter(input_string: str):
    parts = input_string.split('+')  # Adjust the delimiter based on your input structure, e.g., '+', '-', etc.
    formatted_parts = [part[0].upper() + part[1:] if len(part) > 1 else part.upper() for part in parts]
    return '+'.join(formatted_parts)


def reorder_keys(input_keys, preferred_order):
    # Create a dictionary that maps each key to its index in the preferred order
    order_index = {key: index for index, key in enumerate(preferred_order)}

    # Sort the input keys based on their index in the preferred order
    # If a key is not found in the dictionary, it's assigned a default index that places it at the end
    sorted_keys = sorted(input_keys, key=lambda x: order_index.get(x, len(preferred_order)))

    return sorted_keys


def parse_modifiers(modifiers):
    results = []
    individual_values = {}
    for modifier in Qt_KeyboardModifier:
        if modifiers & modifier.value:
            mod_name = modifier.name.replace('Modifier', '')
            results.append(mod_name)
            individual_values[mod_name] = hex(modifier.value)
    return results, individual_values


def parse_key(key_code):
    for key in Qt_Key:
        if key_code == key.value:
            return key.name.replace('Key_', '')
    return "No Match to Key"


def find_similar_key_names(substring: str):
    substring = substring.lower()  # Convert substring to lowercase for case insensitive comparison
    matching_keys = [
        key.name.replace('Key_', '') for key in Qt_Key 
        if substring in key.name.lower()
    ]
    return matching_keys


def encode_string_of_keys_to_int(key_name: str, modifier_names: List[str] = []):

    # Make sure everything is capitalized for proper matching in enums
    # key_name = format_input(key_name)       # There are key names that aren't capitalized!
    modifier_names = [capitalize_first_letter(mod_name) for mod_name in modifier_names]

    # Let 'AsciiTilde' and 'AsciiCircum' be matched without 
    # having to literally put 'Ascii' in input string
    if key_name in ['Tilde', 'Circum']:
        key_name = 'Ascii' + key_name

    # There's no basic Key_Grave, it's Key_QuoteLeft, so translate when user inputs 'Grave'.
    # There are several other "grave" keys that might not make this the best solution.
    if key_name == 'Grave':
        key_name = 'QuoteLeft'

    # If 'Ctrl' is being considered a key (multi-mod-only last key, or by itself)
    # then we need to make sure to convert it to 'Control' to match the key name.
    if key_name == 'Ctrl':
        key_name = 'Control'

    # Match literal key names in enum without making user enter 'Key_'
    if not key_name.startswith('Key_'):
        key_name = 'Key_' + key_name

    try:
        key_value = Qt_Key[key_name].value
    except KeyError:
        similar_keys = find_similar_key_names(key_name.replace('Key_', ''))
        if similar_keys:
            return None, (f"No exact match found for '{key_name.replace('Key_', '')}'. "
                            "Did you mean: " + ', '.join(similar_keys) )
        else:
            return None, f"No matching or similar keys found for '{key_name.replace('Key_', '')}'"

    modifier_value = 0
    for mod_name in modifier_names:

        # Revert 'Ctrl' back to 'Control' if key is being considered a modifier
        if mod_name == 'Ctrl':
            mod_name = 'Control'

        if not mod_name.endswith('Modifier'):
            mod_name = mod_name + 'Modifier'    # Add 'Modifier' suffix for internal matching

        try:
            modifier_value |= Qt_KeyboardModifier[mod_name].value
        except KeyError:
            print()
            print(f"ERROR (KeyError): Wrong order? Modifier keys must come first.")
            return None, f"ERROR: No match on modifier name(s): {modifier_names}"

    return key_value | modifier_value, None     # Always return a tuple


def main():

    parser = argparse.ArgumentParser(
        description=('Convert between integers and shortcut key names for Plasma/Qt/gdbus.')
    )

    parser.add_argument(
        'input',
        type=str,
        help='The integer (to decode) or key/modifier names (to encode)'
    )

    args = parser.parse_args()

    input_str: str = args.input.strip()

    # Strip out integer from gdbus a(ai) output from org.kde.KGlobalAccel.shortcutKeys method
    # This will only work for a "conventional" shortcut (not a sequence of shortcuts)
    a_ai_arg_prefix = '(['
    a_ai_arg_suffix = ', 0, 0, 0],)'

    if input_str.startswith(a_ai_arg_prefix) and input_str.endswith(a_ai_arg_suffix):
        input_str = input_str.replace(a_ai_arg_prefix, '').replace(a_ai_arg_suffix, '')
        print()
        print(f'Integer extracted from a(ai) input argument: {input_str}')
    elif input_str.startswith(a_ai_arg_prefix) and not input_str.endswith(a_ai_arg_suffix):
        print()
        print("ERROR: Script cannot (yet) process integer arrays with more than one shortcut:")
        print(f"\t'{input_str}'")
        print("       Try converting the integers separately.")
        print()
        return


#####################################################################################################
##########################  IF INPUT IS AN INTEGER, NOT A STRING ARGUMENT  ##########################
#####################################################################################################

    if is_integer(input_str):  # Check if the input string represents an integer
        input_value = int(input_str)

        # int: 33554431
        MAX_KEY_VALUE_HX                    = 0x01FFFFFF
        # int: 4261412864
        MAX_MODIFIER_MASK_HX                = 0xFE000000
        # int: 4294967295
        MAX_MODS_AND_KEY_VALUE_HX           = 0xFFFFFFFF

        if input_value < 32:                # Minimum integer value of any single key
            print()
            print(f"ERROR: Integer values below 32 are control codes. Nothing to convert.")
            print()
            return
        elif input_value > MAX_MODS_AND_KEY_VALUE_HX:
            print()
            print("ERROR: Integer value too large for any combination of modifiers + key. Typo?")
            print()
            return

        key_code = input_value & MAX_KEY_VALUE_HX
        modifiers_int = input_value & MAX_MODIFIER_MASK_HX

        if key_code > MAX_KEY_VALUE_HX:
            print(f"\nERROR: Key code part of integer exceeds maximum value ({MAX_KEY_VALUE_HX}).\n")
            return

        print()
        print(f'Converting integer to its component key(s)...')

        key_name = parse_key(key_code)
        modifier_names, individual_modifier_values = parse_modifiers(modifiers_int)

        # Make sure everything is capitalized for proper display on output
        # key_name = format_input(key_name)   # There are key names that aren't capitalized!

        modifier_names = [capitalize_first_letter(mod_name) for mod_name in modifier_names]

        if modifier_names:
            modifier_output = ", ".join(mod_name + 'Modifier' for mod_name in modifier_names)
        else:
            modifier_output = "None"

        print()
        print(f"Integer argument given:     {input_value}")
        print()
        print(f"Extracted Mod(s) int:       {modifiers_int}")

        for mod, value in individual_modifier_values.items():
            print(f"{mod + ' hex value:':>23}       {value}")

        print(f"    Full Mod Name(s):       {modifier_output}")
        print()
        print(f"Extracted Key int value:    {key_code}")
        print(f"  Extracted Key hex value:    {hex(key_code)}")
        print(f"          Full Key Name:    {'Key_' + key_name}")
        print()

        # Constructing shortcut combo
        modifier_names = [
            'Ctrl' if 'Control' in mod_name else mod_name 
            for mod_name in modifier_names
        ]
        # Put combo modifiers for display in same order as Plasma Shortcuts settings dialog
        modifier_names = reorder_keys(modifier_names, preferred_mod_order)
        key_name = 'Ctrl' if key_name == 'Control' else key_name
        shortcut_combo = '+'.join(modifier_names + [key_name.replace('Ascii', '')])

        print(f"Normalized Shortcut Combo:  '{shortcut_combo}'")
        print()

#####################################################################################################
##############################  IF INPUT IS A STRING, NOT AN INTEGER  ###############################
#####################################################################################################

    else:
        # Treat as string of key/modifier names
        print()
        print(f'Converting string of keys to integer...')

        if '-' in input_str:
            input_str = input_str.replace('-', '+')

        parts = input_str.split('+')

        # Special case handling: All elements in parts list are modifier keys.
        # Capitalize in temporary list, check for all being in `preferred_order` list,
        # sort parts list by `preferred_order`, update parts list from new list.
        temp_parts = [capitalize_first_letter(part) for part in parts]
        if all(key in preferred_mod_order for key in temp_parts) and len(parts) > 1:
            print()
            print("Detected special case: Multi-mod-only shortcut string.")
            print('One mod will be treated as non-mod "key" for integer value.')
            print("Pre-sorting for consistent integer conversion result...")
            parts = reorder_keys(parts, preferred_mod_order)

        key_name = parts[-1]  # Last part is the key

        # If 'Key_' is actually given on input we need to strip it off for now. 
        if key_name.startswith('Key_'):
            key_name = key_name.replace('Key_', '')

        # Correct the key name from 'Ctrl' to Qt::Key name 'Control'
        if key_name == 'Ctrl':
            key_name = 'Control'
        modifier_names = parts[:-1]  # All other parts are modifiers

        # Make sure everything is capitalized for proper matching and display on output
        # key_name = format_input(key_name)       # There are key names that aren't capitalized!
        modifier_names = [capitalize_first_letter(mod_name) for mod_name in modifier_names]

        # Now that keys are capitalized: If 'Menu' found, 'Shift' should be removed?
        # (Shift gets ignored in Plasma Shortcuts settings when Menu is used as part of shortcut.)
        # TODO: Check that this removal of Shift results in the same integer that shortcut creates.
        if key_name == 'Menu' and 'Shift' in modifier_names:
            modifier_names = [mod_name for mod_name in modifier_names if mod_name != 'Shift']

        encoded_integer, message = encode_string_of_keys_to_int(key_name, modifier_names)

        if message:
            print()
            print(message)
            print()
        else:
            # Add the 'Ascii' prefix when necessary
            if key_name in ['Tilde', 'Circum']:
                print()
                print(f"NOTE: Converting '{key_name}' to Qt::Key name '{'Ascii' + key_name}'")
                key_name = 'Ascii' + key_name

            # There's no basic Key_Grave, it's Key_QuoteLeft, so translate when user inputs 'Grave'.
            # There are several other "grave" keys that might not make this the best solution.
            if key_name == 'Grave':
                key_name = 'QuoteLeft'
                print()
                print(f"NOTE: Converting input 'Grave' to Qt:Key name 'QuoteLeft'...")

            # Convert input 'Ctrl' to proper Qt::Key name 'Control' for display on output
            if key_name == 'Ctrl':
                key_name = 'Control'
                print()
                print(f"NOTE: Converting input 'Ctrl' to Qt::Key name 'Control'...")

            # Add the 'Key_' prefix
            key_name = 'Key_' + key_name

            # Convert 'Ctrl' from input to Qt::KeyboardModifier name 'Control'.
            # For "Full Key Name:" display.
            modifier_names = [
                'Control' if mod_name == 'Ctrl' else mod_name
                for mod_name in modifier_names
            ]

            if modifier_names:
                modifier_output = ", ".join(mod_name + 'Modifier' for mod_name in modifier_names)
            else:
                modifier_output = "None"

            print()
            print(f"String argument given:  {input_str}")
            print()
            print(f"Full Mod Name(s):       {modifier_output}")
            print(f"Full Key Name:          {key_name}")
            print()
            print(f"Encoded to Integer:     {encoded_integer}")
            print()
            # Sample a(ai) argument to give to gdbus call to setShortcutKeys: "([16777250, 0, 0, 0],)"
            print(f'Gdbus a(ai) argument syntax: "([{encoded_integer}, 0, 0, 0],)"')
            print()


if __name__ == "__main__":
    main()
