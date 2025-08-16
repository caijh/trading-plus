from indicator.adl import ADL
from indicator.adx import ADX
from indicator.ar import AR
from indicator.aroon import AROON
from indicator.chaikin import Chaikin
from indicator.cmf import CMF
from indicator.kvo import KVO
from indicator.macd_confirm import MACD
from indicator.mfi import MFI
from indicator.obv import OBV
from indicator.rsi_confirm import RSI

volume_registry = {
    'SMA': {
        1: [ADX(1), OBV(1), CMF(1), AROON(1), MACD(1)],
        -1: [ADX(-1), OBV(-1), CMF(-1), AROON(-1), MACD(-1)]
    },
    'MACD': {
        1: [RSI(1), OBV(1), ADL(1), Chaikin(1), KVO(1)],
        -1: [RSI(-1), OBV(-1), ADL(-1), Chaikin(-1), KVO(-1)]
    },
    'SAR': {
        1: [ADX(1), MFI(1), OBV(1), AROON(1)],
        -1: [ADX(-1), MFI(-1), OBV(1), AROON(-1)]
    },
    'BIAS': {
        1: [ADX(1), CMF(1), MFI(1)],
        -1: [ADX(-1), CMF(1), MFI(-1)]
    },
    'KDJ': {
        1: [ADX(1), MFI(1), AR(1)],
        -1: [ADX(-1), MFI(-1), AR(-1)]
    },
    'RSI': {
        1: [ADX(1), MFI(1), OBV(1)],
        -1: [ADX(-1), MFI(-1), OBV(-1)]
    },
    'WR': {
        1: [ADX(1), CMF(1), OBV(1), KVO(1)],
        -1: [ADX(-1), CMF(-1), OBV(-1), KVO(-1)]
    },
}
