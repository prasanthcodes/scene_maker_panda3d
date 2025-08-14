#inverse tonemapping
import math
import numpy as np

def inverse_tonemapping(color2):
    a = 1.7 * color2-0.5
    b = 1.402 * color2 * color2 - 0.212 * color2 + 0.25
    out=(a + np.sqrt(b)) / (12.4 * (1.0 - color2))
    return out

def filmic_tone_map(color):
    """
    Applies filmic tone mapping to an RGB color vector.
    
    Parameters:
        color (numpy.ndarray): Input RGB color as a 3-component array (HDR values).
    
    Returns:
        numpy.ndarray: Tone-mapped RGB color as a 3-component array.
    """
    import numpy as np
    
    # Ensure input is a numpy array
    color = np.array(color, dtype=np.float32)
    
    # Constants for the filmic tone mapping
    a = 6.2
    b = 0.5
    c = 1.7
    d = 0.06
    
    # Compute numerator: color * (6.2 * color + 0.5)
    numerator = color * (a * color + b)
    
    # Compute denominator: color * (6.2 * color + 1.7) + 0.06
    denominator = color * (a * color + c) + d
    
    # Apply tone mapping per channel
    return numerator / denominator
    
w=0.996
q=inverse_tonemapping(np.array([w,w,w]))
print(q)
z=255
print(filmic_tone_map([z,z,z]))


