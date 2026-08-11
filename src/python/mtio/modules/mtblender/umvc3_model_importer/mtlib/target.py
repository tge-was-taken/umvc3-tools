from dataclasses import dataclass


@dataclass
class TargetInfo:
    name: str
    description: str
    platform: str
    endian: str
    pathLength: int
    useTriStrips: bool
    vertexFlags_IASkinTB1wt: int
    vertexFlags_IASkinTB2wt: int
    vertexFlags_IASkinTB4wt: int
    BM_HQ_BC7: bool
    useUninitializedPadding: bool
    textureType: int

supported = [
    TargetInfo(name='mvc3-pc', 
               description='Ultimate Marvel vs Capcom 3 (PC)', 
               platform='pc', 
               endian='little', 
               pathLength=64, 
               useTriStrips=False,
               vertexFlags_IASkinTB1wt=0x09,
               vertexFlags_IASkinTB2wt=0x11,
               vertexFlags_IASkinTB4wt=0x19,
               BM_HQ_BC7=False,
               useUninitializedPadding=False,
               textureType=0xA09D),
    
    TargetInfo(name='aa-pc', 
               description='The Great Ace Attorney Chronicles (PC)', 
               platform='pc', 
               endian='little', 
               pathLength=128, 
               useTriStrips=True,
               vertexFlags_IASkinTB1wt=0x11,
               vertexFlags_IASkinTB2wt=0x21,
               vertexFlags_IASkinTB4wt=0x41,
               BM_HQ_BC7=True,
               useUninitializedPadding=True,
               textureType=0x90A3),
]
supportedDict = dict()
for target in supported:
    supportedDict[target.name] = target

current: TargetInfo = supported[0]

def setTarget(name):
    global current
    current = supportedDict[name]
