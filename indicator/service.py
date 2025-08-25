from indicator.adoc import ADOSC
from indicator.adx import ADX
from indicator.ar import AR
from indicator.aroon import AROON
from indicator.chaikin import Chaikin
from indicator.cmf import CMF
from indicator.confirm.macd import MACD
from indicator.confirm.rsi import RSI
from indicator.kvo import KVO
from indicator.mfi import MFI
from indicator.nvi import NVI
from indicator.obv import OBV
from indicator.pvi import PVI
from indicator.vpt import VPT


def get_bullish_all_volume_patterns():
    return [
        ADX(1),
        ADOSC(1),
        AR(1),
        AROON(1),
        Chaikin(1),
        CMF(1),
        KVO(1),
        MFI(1),
        NVI(1),
        OBV(1),
        PVI(1),
        RSI(1),
        MACD(1),
        VPT(1)
    ]

def get_bearish_all_volume_patterns():
    return [
        ADX(-1),
        ADOSC(-1),
        AR(-1),
        AROON(-1),
        Chaikin(-1),
        CMF(-1),
        KVO(-1),
        MFI(-1),
        NVI(-1),
        OBV(-1),
        PVI(-1),
        RSI(-1),
        MACD(-1),
        VPT(-1)
    ]

volume_registry = {
    'SMA': {
        1: [OBV(1)],
        -1: [OBV(-1)]
    },
    'MACD': {
        1: [Chaikin(1)],
        -1: [Chaikin(-1)]
    },
    'SAR': {
        1: [NVI(1), OBV(1)],
        -1: [NVI(-1), OBV(-1)]
    },
    'BIAS': {
        1: [NVI(1)],
        -1: [NVI(-1)]
    },
    'KDJ': {
        1: [CMF(1)],
        -1: [CMF(-1)]
    },
    'RSI': {
        1: [AROON(1)],
        -1: [AROON(-1)]
    },
    'WR': {
        1: [MACD(1, mode='reversal')],
        -1: [MACD(-1, mode='reversal')]
    },
}
