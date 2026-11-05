import numpy as np
OLD=[0,3.8,7.0,9.1,12.5,15.2,18.1,21.9,24.0,26.3,30.5,34.1,35.2,37.6,39.5]
NEW=[0,3.99,7.17,9.21,13.22,16.13,18.89,22.04,23.81,26.02,30.93,35.26,36.15,38.86,39.6]
W=lambda t: float(np.interp(t,OLD,NEW)); Winv=lambda t: float(np.interp(t,NEW,OLD))
