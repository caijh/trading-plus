from indicator.aroon import AROON
from indicator.cmf import CMF
from indicator.nvi import NVI
from indicator.obv import OBV
from indicator.pvi import PVI

volume_registry = {
    'SMA': {
        1: [
            PVI(1)
        ],
        -1: [
            PVI(-1)
        ],
    },
    'MACD': {
        1: [
            NVI(1),
        ],
        -1: [
            NVI(-1),
        ]
    },
    'SAR': {
        1: [
            NVI(1),
        ],
        -1: [
            NVI(-1),
        ]
    },
    'BIAS': {
        1: [
            NVI(1),
        ],
        -1: [
            NVI(-1),
        ]
    },
    'KDJ': {
        1: [
            AROON(1),
            CMF(1),
        ],
        -1: [
            AROON(-1),
            CMF(-1),
        ]
    },
    'RSI': {
        1: [
            NVI(1),
        ],
        -1: [
            NVI(-1),
        ]
    },
    'WR': {
        1: [
            CMF(1),
            NVI(1),
            OBV(1),
        ],
        -1: [
            CMF(-1),
            NVI(-1),
            OBV(-1),
        ]
    },
}
